import pytest


@pytest.fixture
def setup_base(client, headers_admin):
    """Cria cliente, veículo e serviço — base para os testes de OS."""
    cliente = client.post("/clientes", json={
        "nome": "João Silva", "email": "joao@email.com",
        "telefone": "11999990000", "cpf": "529.982.247-25",
    }, headers=headers_admin).json()

    veiculo = client.post("/veiculos", json={
        "cliente_id": cliente["id"], "placa": "ABC1D23",
        "marca": "Toyota", "modelo": "Corolla", "ano": 2022,
    }, headers=headers_admin).json()

    servico = client.post("/servicos", json={
        "nome": "Troca de óleo", "descricao": "Troca completa",
        "preco_base": "150.00", "tempo_estimado_minutos": 60,
    }, headers=headers_admin).json()

    return {"cliente": cliente, "veiculo": veiculo, "servico": servico}


def test_abrir_os(client, headers_admin, setup_base):
    resposta = client.post("/ordens-de-servico", json={
        "cliente_cpf_cnpj": "529.982.247-25",
        "veiculo_placa": "ABC1D23",
        "descricao_problema": "Barulho no motor",
    }, headers=headers_admin)

    assert resposta.status_code == 201
    assert resposta.json()["status"] == "RECEBIDA"


def test_fluxo_completo_da_os(client, headers_admin, setup_base):
    servico = setup_base["servico"]

    # 1. Abrir OS
    os = client.post("/ordens-de-servico", json={
        "cliente_cpf_cnpj": "529.982.247-25",
        "veiculo_placa": "ABC1D23",
        "descricao_problema": "Revisão geral",
    }, headers=headers_admin).json()
    os_id = os["id"]

    # 2. Iniciar diagnóstico
    os = client.post(f"/ordens-de-servico/{os_id}/iniciar-diagnostico",
                     headers=headers_admin).json()
    assert os["status"] == "EM_DIAGNOSTICO"

    # 3. Adicionar serviço
    os = client.post(f"/ordens-de-servico/{os_id}/adicionar-servico", json={
        "servico_id": servico["id"],
    }, headers=headers_admin).json()
    assert len(os["itens_servico"]) == 1
    assert os["itens_servico"][0]["descricao"] == "Troca de óleo"
    assert os["itens_servico"][0]["preco_unitario"] == "150.00"
    item_id = os["itens_servico"][0]["id"]

    # 4. Finalizar diagnóstico
    os = client.post(f"/ordens-de-servico/{os_id}/finalizar-diagnostico",
                     headers=headers_admin).json()
    assert os["status"] == "AGUARDANDO_ORCAMENTO"

    # 5. Gerar orçamento
    os = client.post(f"/ordens-de-servico/{os_id}/gerar-orcamento",
                     headers=headers_admin).json()
    assert os["status"] == "AGUARDANDO_APROVACAO"
    assert os["valor_orcamento"] == "150.00"

    # 6. Aprovar orçamento (sem autenticação — rota pública)
    os = client.post(f"/ordens-de-servico/{os_id}/aprovar-orcamento").json()
    assert os["status"] == "EM_EXECUCAO"

    # 7. Executar serviço
    os = client.post(f"/ordens-de-servico/{os_id}/executar-servico/{item_id}",
                     headers=headers_admin).json()
    assert os["status"] == "SERVICOS_CONCLUIDOS"

    # 8. Finalizar OS (controle de qualidade)
    os = client.post(f"/ordens-de-servico/{os_id}/finalizar",
                     headers=headers_admin).json()
    assert os["status"] == "FINALIZADA"

    # 9. Entregar veículo
    os = client.post(f"/ordens-de-servico/{os_id}/entregar",
                     headers=headers_admin).json()
    assert os["status"] == "ENTREGUE"


def test_acompanhar_os_sem_autenticacao(client, headers_admin, setup_base):
    os = client.post("/ordens-de-servico", json={
        "cliente_cpf_cnpj": "529.982.247-25",
        "veiculo_placa": "ABC1D23",
        "descricao_problema": "Revisão",
    }, headers=headers_admin).json()

    # Rota pública — sem token
    resposta = client.get(f"/ordens-de-servico/{os['id']}/acompanhar")
    assert resposta.status_code == 200
    dados = resposta.json()
    # Dados sensíveis não devem aparecer
    assert "cpf" not in dados
    assert "cnpj" not in dados
    assert "email" not in dados


def test_transicao_invalida_retorna_422(client, headers_admin, setup_base):
    os = client.post("/ordens-de-servico", json={
        "cliente_cpf_cnpj": "529.982.247-25",
        "veiculo_placa": "ABC1D23",
        "descricao_problema": "Revisão",
    }, headers=headers_admin).json()

    # Tenta aprovar orçamento sem ter gerado (status RECEBIDA)
    resposta = client.post(f"/ordens-de-servico/{os['id']}/aprovar-orcamento")
    assert resposta.status_code == 422


def test_recusar_orcamento(client, headers_admin, setup_base):
    servico = setup_base["servico"]
    os = client.post("/ordens-de-servico", json={
        "cliente_cpf_cnpj": "529.982.247-25",
        "veiculo_placa": "ABC1D23",
        "descricao_problema": "Revisão",
    }, headers=headers_admin).json()

    client.post(f"/ordens-de-servico/{os['id']}/iniciar-diagnostico", headers=headers_admin)
    client.post(f"/ordens-de-servico/{os['id']}/adicionar-servico", json={
        "servico_id": servico["id"],
    }, headers=headers_admin)
    client.post(f"/ordens-de-servico/{os['id']}/finalizar-diagnostico", headers=headers_admin)
    client.post(f"/ordens-de-servico/{os['id']}/gerar-orcamento", headers=headers_admin)

    resposta = client.post(f"/ordens-de-servico/{os['id']}/recusar-orcamento",
                           json={"motivo": "Valor alto"})
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "CANCELADA"


def test_adicionar_peca_nao_reserva_estoque(client, headers_admin, setup_base):
    """Adicionar peça à OS não deve alterar o estoque — reserva só na aprovação."""
    peca = client.post("/pecas", json={
        "nome": "Filtro de óleo", "codigo": "FO-001",
        "preco_unitario": "45.00", "quantidade_disponivel": 10,
        "quantidade_minima_alerta": 2,
    }, headers=headers_admin).json()

    os = client.post("/ordens-de-servico", json={
        "cliente_cpf_cnpj": "529.982.247-25",
        "veiculo_placa": "ABC1D23",
        "descricao_problema": "Troca de óleo",
    }, headers=headers_admin).json()

    client.post(f"/ordens-de-servico/{os['id']}/iniciar-diagnostico", headers=headers_admin)
    client.post(f"/ordens-de-servico/{os['id']}/adicionar-peca", json={
        "peca_id": peca["id"], "quantidade": 3,
    }, headers=headers_admin)

    estoque_apos_add = client.get(f"/pecas/{peca['id']}", headers=headers_admin).json()
    assert estoque_apos_add["quantidade_disponivel"] == 10


def test_aprovar_orcamento_reserva_estoque(client, headers_admin, setup_base):
    """Aprovação do orçamento deve reservar as peças (reduzir estoque)."""
    servico = setup_base["servico"]
    peca = client.post("/pecas", json={
        "nome": "Filtro de óleo", "codigo": "FO-002",
        "preco_unitario": "45.00", "quantidade_disponivel": 10,
        "quantidade_minima_alerta": 2,
    }, headers=headers_admin).json()

    os = client.post("/ordens-de-servico", json={
        "cliente_cpf_cnpj": "529.982.247-25",
        "veiculo_placa": "ABC1D23",
        "descricao_problema": "Troca de óleo",
    }, headers=headers_admin).json()
    os_id = os["id"]

    client.post(f"/ordens-de-servico/{os_id}/iniciar-diagnostico", headers=headers_admin)
    client.post(f"/ordens-de-servico/{os_id}/adicionar-servico", json={
        "servico_id": servico["id"],
    }, headers=headers_admin)
    client.post(f"/ordens-de-servico/{os_id}/adicionar-peca", json={
        "peca_id": peca["id"], "quantidade": 3,
    }, headers=headers_admin)
    client.post(f"/ordens-de-servico/{os_id}/finalizar-diagnostico", headers=headers_admin)
    client.post(f"/ordens-de-servico/{os_id}/gerar-orcamento", headers=headers_admin)
    client.post(f"/ordens-de-servico/{os_id}/aprovar-orcamento")

    estoque_apos_aprovacao = client.get(f"/pecas/{peca['id']}", headers=headers_admin).json()
    assert estoque_apos_aprovacao["quantidade_disponivel"] == 7


def test_aprovar_orcamento_sem_estoque_retorna_422(client, headers_admin, setup_base):
    """Aprovação deve falhar com 422 se estoque insuficiente para alguma peça."""
    servico = setup_base["servico"]
    peca = client.post("/pecas", json={
        "nome": "Filtro de óleo", "codigo": "FO-003",
        "preco_unitario": "45.00", "quantidade_disponivel": 1,
        "quantidade_minima_alerta": 1,
    }, headers=headers_admin).json()

    os = client.post("/ordens-de-servico", json={
        "cliente_cpf_cnpj": "529.982.247-25",
        "veiculo_placa": "ABC1D23",
        "descricao_problema": "Troca de óleo",
    }, headers=headers_admin).json()
    os_id = os["id"]

    client.post(f"/ordens-de-servico/{os_id}/iniciar-diagnostico", headers=headers_admin)
    client.post(f"/ordens-de-servico/{os_id}/adicionar-servico", json={
        "servico_id": servico["id"],
    }, headers=headers_admin)
    client.post(f"/ordens-de-servico/{os_id}/adicionar-peca", json={
        "peca_id": peca["id"], "quantidade": 5,
    }, headers=headers_admin)
    client.post(f"/ordens-de-servico/{os_id}/finalizar-diagnostico", headers=headers_admin)
    client.post(f"/ordens-de-servico/{os_id}/gerar-orcamento", headers=headers_admin)

    resposta = client.post(f"/ordens-de-servico/{os_id}/aprovar-orcamento")
    assert resposta.status_code == 422


def test_veiculo_com_os_ativa_nao_abre_nova(client, headers_admin, setup_base):
    dados = {
        "cliente_cpf_cnpj": "529.982.247-25",
        "veiculo_placa": "ABC1D23",
        "descricao_problema": "Revisão",
    }
    client.post("/ordens-de-servico", json=dados, headers=headers_admin)
    resposta = client.post("/ordens-de-servico", json=dados, headers=headers_admin)
    assert resposta.status_code == 422


def test_listar_itens_os(client, headers_admin, setup_base):
    servico = setup_base["servico"]
    os = client.post("/ordens-de-servico", json={
        "cliente_cpf_cnpj": "529.982.247-25",
        "veiculo_placa": "ABC1D23",
        "descricao_problema": "Revisão",
    }, headers=headers_admin).json()

    client.post(f"/ordens-de-servico/{os['id']}/iniciar-diagnostico", headers=headers_admin)
    client.post(f"/ordens-de-servico/{os['id']}/adicionar-servico", json={
        "servico_id": servico["id"],
    }, headers=headers_admin)

    resposta = client.get(f"/ordens-de-servico/{os['id']}/itens", headers=headers_admin)
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["pendentes"] == 1
    assert dados["concluidos"] == 0
    assert len(dados["itens"]) == 1
    assert dados["itens"][0]["concluido"] is False


def test_listar_itens_os_apenas_pendentes(client, headers_admin, setup_base):
    servico = setup_base["servico"]
    os = client.post("/ordens-de-servico", json={
        "cliente_cpf_cnpj": "529.982.247-25",
        "veiculo_placa": "ABC1D23",
        "descricao_problema": "Revisão",
    }, headers=headers_admin).json()
    os_id = os["id"]

    client.post(f"/ordens-de-servico/{os_id}/iniciar-diagnostico", headers=headers_admin)
    item = client.post(f"/ordens-de-servico/{os_id}/adicionar-servico", json={
        "servico_id": servico["id"],
    }, headers=headers_admin).json()
    item_id = item["itens_servico"][0]["id"]

    client.post(f"/ordens-de-servico/{os_id}/adicionar-servico", json={
        "servico_id": servico["id"],
    }, headers=headers_admin)

    client.post(f"/ordens-de-servico/{os_id}/finalizar-diagnostico", headers=headers_admin)
    client.post(f"/ordens-de-servico/{os_id}/gerar-orcamento", headers=headers_admin)
    client.post(f"/ordens-de-servico/{os_id}/aprovar-orcamento")
    client.post(f"/ordens-de-servico/{os_id}/executar-servico/{item_id}", headers=headers_admin)

    resposta = client.get(f"/ordens-de-servico/{os_id}/itens?pendentes=true", headers=headers_admin)
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["total"] == 2
    assert dados["pendentes"] == 1
    assert dados["concluidos"] == 1
    assert len(dados["itens"]) == 1
    assert dados["itens"][0]["concluido"] is False


def test_finalizar_diagnostico_com_laudo(client, headers_admin, setup_base):
    """Laudo informado pelo mecânico deve ser persistido e devolvido na resposta."""
    servico = setup_base["servico"]
    os = client.post("/ordens-de-servico", json={
        "cliente_cpf_cnpj": "529.982.247-25",
        "veiculo_placa": "ABC1D23",
        "descricao_problema": "Barulho ao frear",
    }, headers=headers_admin).json()
    os_id = os["id"]

    client.post(f"/ordens-de-servico/{os_id}/iniciar-diagnostico", headers=headers_admin)
    client.post(f"/ordens-de-servico/{os_id}/adicionar-servico", json={
        "servico_id": servico["id"],
    }, headers=headers_admin)

    laudo = "Rolamento dianteiro esquerdo danificado. Pastilhas de freio com desgaste excessivo."
    resposta = client.post(
        f"/ordens-de-servico/{os_id}/finalizar-diagnostico",
        json={"laudo_diagnostico": laudo},
        headers=headers_admin,
    )
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["status"] == "AGUARDANDO_ORCAMENTO"
    assert dados["laudo_diagnostico"] == laudo

    # Verifica que o laudo persiste ao buscar a OS novamente
    dados_recarregados = client.get(f"/ordens-de-servico/{os_id}", headers=headers_admin).json()
    assert dados_recarregados["laudo_diagnostico"] == laudo


def test_gerar_orcamento_sem_servicos_retorna_422(client, headers_admin, setup_base):
    os = client.post("/ordens-de-servico", json={
        "cliente_cpf_cnpj": "529.982.247-25",
        "veiculo_placa": "ABC1D23",
        "descricao_problema": "Revisão",
    }, headers=headers_admin).json()

    client.post(f"/ordens-de-servico/{os['id']}/iniciar-diagnostico", headers=headers_admin)
    client.post(f"/ordens-de-servico/{os['id']}/finalizar-diagnostico", headers=headers_admin)
    resposta = client.post(f"/ordens-de-servico/{os['id']}/gerar-orcamento", headers=headers_admin)
    assert resposta.status_code == 422
