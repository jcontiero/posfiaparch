import pytest


def _payload_abertura_unificada(cliente, veiculo, servico, descricao="Revisão"):
    return {
        "cliente": {
            "nome": cliente["nome"],
            "email": cliente["email"],
            "telefone": cliente["telefone"],
            "cpf": cliente["cpf"],
        },
        "veiculo": {
            "placa": veiculo["placa"],
            "marca": veiculo["marca"],
            "modelo": veiculo["modelo"],
            "ano": veiculo["ano"],
            "descricao_problema": descricao,
        },
        "servicos": [{"servico_id": servico["id"]}],
    }


@pytest.fixture
def setup_base(client, headers_admin):
    """Cria cliente, veículo e serviço — base para os testes de OS."""
    cliente = client.post(
        "/clientes",
        json={
            "nome": "João Silva",
            "email": "joao@email.com",
            "telefone": "11999990000",
            "cpf": "529.982.247-25",
        },
        headers=headers_admin,
    ).json()

    veiculo = client.post(
        "/veiculos",
        json={
            "cliente_id": cliente["id"],
            "placa": "ABC1D23",
            "marca": "Toyota",
            "modelo": "Corolla",
            "ano": 2022,
        },
        headers=headers_admin,
    ).json()

    servico = client.post(
        "/servicos",
        json={
            "nome": "Troca de óleo",
            "descricao": "Troca completa",
            "preco_base": "150.00",
            "tempo_estimado_minutos": 60,
        },
        headers=headers_admin,
    ).json()

    return {"cliente": cliente, "veiculo": veiculo, "servico": servico}


def test_abrir_os_unificada(client, headers_admin, setup_base):
    payload = _payload_abertura_unificada(
        setup_base["cliente"],
        setup_base["veiculo"],
        setup_base["servico"],
        "Barulho no motor",
    )
    resposta = client.post("/ordens-de-servico", json=payload, headers=headers_admin)

    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["status"] == "AGUARDANDO_APROVACAO"
    assert dados["valor_orcamento"] == "150.00"


def test_fluxo_completo_da_os(client, headers_admin, setup_base):
    servico = setup_base["servico"]
    payload = _payload_abertura_unificada(
        setup_base["cliente"], setup_base["veiculo"], servico, "Revisão geral"
    )

    # 1. Abrir OS (já vai para Aguardando Aprovação na abertura unificada)
    os = client.post("/ordens-de-servico", json=payload, headers=headers_admin).json()
    os_id = os["id"]
    assert os["status"] == "AGUARDANDO_APROVACAO"

    # 2. Aprovar orçamento (rota antiga ainda disponível)
    os = client.post(f"/ordens-de-servico/{os_id}/aprovar-orcamento").json()
    assert os["status"] == "EM_EXECUCAO"

    # 3. Executar serviço
    item_id = os["itens_servico"][0]["id"]
    os = client.post(
        f"/ordens-de-servico/{os_id}/executar-servico/{item_id}", headers=headers_admin
    ).json()
    assert os["status"] == "SERVICOS_CONCLUIDOS"

    # 4. Finalizar OS
    os = client.post(
        f"/ordens-de-servico/{os_id}/finalizar", headers=headers_admin
    ).json()
    assert os["status"] == "FINALIZADA"

    # 5. Entregar veículo
    os = client.post(
        f"/ordens-de-servico/{os_id}/entregar", headers=headers_admin
    ).json()
    assert os["status"] == "ENTREGUE"


def test_acompanhar_os_sem_autenticacao(client, headers_admin, setup_base):
    payload = _payload_abertura_unificada(
        setup_base["cliente"], setup_base["veiculo"], setup_base["servico"]
    )
    os = client.post("/ordens-de-servico", json=payload, headers=headers_admin).json()

    # Rota pública — sem token
    resposta = client.get(f"/ordens-de-servico/{os['id']}/acompanhar")
    assert resposta.status_code == 200
    dados = resposta.json()
    # Dados sensíveis não devem aparecer
    assert "cpf" not in dados
    assert "cnpj" not in dados
    assert "email" not in dados


def test_consultar_status_os(client, headers_admin, setup_base):
    payload = _payload_abertura_unificada(
        setup_base["cliente"], setup_base["veiculo"], setup_base["servico"]
    )
    os = client.post("/ordens-de-servico", json=payload, headers=headers_admin).json()

    resposta = client.get(f"/ordens-de-servico/{os['id']}/status")
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["id"] == os["id"]
    assert dados["status"] == "Aguardando Aprovação"


def test_aprovacao_os_fase2(client, headers_admin, setup_base):
    payload = _payload_abertura_unificada(
        setup_base["cliente"], setup_base["veiculo"], setup_base["servico"]
    )
    os = client.post("/ordens-de-servico", json=payload, headers=headers_admin).json()
    os_id = os["id"]

    resposta = client.post(
        f"/ordens-de-servico/{os_id}/aprovacao",
        json={"aprovado": True},
    )
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "EM_EXECUCAO"


def test_recusa_os_fase2_volta_para_diagnostico(client, headers_admin, setup_base):
    payload = _payload_abertura_unificada(
        setup_base["cliente"], setup_base["veiculo"], setup_base["servico"]
    )
    os = client.post("/ordens-de-servico", json=payload, headers=headers_admin).json()
    os_id = os["id"]

    resposta = client.post(
        f"/ordens-de-servico/{os_id}/aprovacao",
        json={"aprovado": False, "motivo": "Valor alto"},
    )
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "EM_DIAGNOSTICO"


def test_listagem_ordenada_oculta_finalizadas(client, headers_admin, setup_base):
    payload = _payload_abertura_unificada(
        setup_base["cliente"], setup_base["veiculo"], setup_base["servico"]
    )
    os1 = client.post("/ordens-de-servico", json=payload, headers=headers_admin).json()

    # Cria uma segunda OS em outro veículo, aprova, executa e finaliza
    outro_veiculo = client.post(
        "/veiculos",
        json={
            "cliente_id": setup_base["cliente"]["id"],
            "placa": "XYZ9K87",
            "marca": "Honda",
            "modelo": "Civic",
            "ano": 2021,
        },
        headers=headers_admin,
    ).json()
    payload2 = _payload_abertura_unificada(
        setup_base["cliente"], outro_veiculo, setup_base["servico"]
    )
    os2 = client.post("/ordens-de-servico", json=payload2, headers=headers_admin).json()
    client.post(f"/ordens-de-servico/{os2['id']}/aprovacao", json={"aprovado": True})
    item_id = os2["itens_servico"][0]["id"]
    client.post(
        f"/ordens-de-servico/{os2['id']}/executar-servico/{item_id}",
        headers=headers_admin,
    )
    client.post(f"/ordens-de-servico/{os2['id']}/finalizar", headers=headers_admin)

    resposta = client.get("/ordens-de-servico", headers=headers_admin)
    assert resposta.status_code == 200
    dados = resposta.json()
    ids = [o["id"] for o in dados]
    assert os1["id"] in ids
    assert os2["id"] not in ids


def test_webhook_atualizar_status(client, headers_admin, setup_base, app_test):
    payload = _payload_abertura_unificada(
        setup_base["cliente"], setup_base["veiculo"], setup_base["servico"]
    )
    os = client.post("/ordens-de-servico", json=payload, headers=headers_admin).json()
    os_id = os["id"]

    token = app_test.state.container.token_provider.criar(
        {"os_id": os_id}, expiracao_horas=1
    )

    resposta = client.post(
        f"/webhooks/os/{os_id}/atualizar-status",
        json={"status": "EXECUCAO", "token": token},
    )
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "EM_EXECUCAO"


def test_webhook_token_invalido_retorna_401(client, headers_admin, setup_base):
    payload = _payload_abertura_unificada(
        setup_base["cliente"], setup_base["veiculo"], setup_base["servico"]
    )
    os = client.post("/ordens-de-servico", json=payload, headers=headers_admin).json()

    resposta = client.post(
        f"/webhooks/os/{os['id']}/atualizar-status",
        json={"status": "EXECUCAO", "token": "token-invalido"},
    )
    assert resposta.status_code == 401


def test_transicao_invalida_retorna_422(client, headers_admin, setup_base):
    payload = _payload_abertura_unificada(
        setup_base["cliente"], setup_base["veiculo"], setup_base["servico"]
    )
    os = client.post("/ordens-de-servico", json=payload, headers=headers_admin).json()

    # Tenta entregar direto sem passar por execução/finalização
    resposta = client.post(
        f"/ordens-de-servico/{os['id']}/entregar", headers=headers_admin
    )
    assert resposta.status_code == 422


def test_adicionar_peca_nao_reserva_estoque(client, headers_admin, setup_base):
    """Adicionar peça à OS não deve alterar o estoque — reserva só na aprovação."""
    peca = client.post(
        "/pecas",
        json={
            "nome": "Filtro de óleo",
            "codigo": "FO-001",
            "preco_unitario": "45.00",
            "quantidade_disponivel": 10,
            "quantidade_minima_alerta": 2,
        },
        headers=headers_admin,
    ).json()

    payload = _payload_abertura_unificada(
        setup_base["cliente"],
        setup_base["veiculo"],
        setup_base["servico"],
        "Troca de óleo",
    )
    payload["pecas"] = [{"peca_id": peca["id"], "quantidade": 3}]
    os = client.post("/ordens-de-servico", json=payload, headers=headers_admin).json()
    assert os["status"] == "AGUARDANDO_APROVACAO"

    estoque_apos_add = client.get(f"/pecas/{peca['id']}", headers=headers_admin).json()
    assert estoque_apos_add["quantidade_disponivel"] == 10


def test_aprovar_orcamento_reserva_estoque(client, headers_admin, setup_base):
    """Aprovação do orçamento deve reservar as peças (reduzir estoque)."""
    peca = client.post(
        "/pecas",
        json={
            "nome": "Filtro de óleo",
            "codigo": "FO-002",
            "preco_unitario": "45.00",
            "quantidade_disponivel": 10,
            "quantidade_minima_alerta": 2,
        },
        headers=headers_admin,
    ).json()

    payload = _payload_abertura_unificada(
        setup_base["cliente"],
        setup_base["veiculo"],
        setup_base["servico"],
        "Troca de óleo",
    )
    payload["pecas"] = [{"peca_id": peca["id"], "quantidade": 3}]
    os = client.post("/ordens-de-servico", json=payload, headers=headers_admin).json()
    os_id = os["id"]

    client.post(f"/ordens-de-servico/{os_id}/aprovar-orcamento")

    estoque_apos_aprovacao = client.get(
        f"/pecas/{peca['id']}", headers=headers_admin
    ).json()
    assert estoque_apos_aprovacao["quantidade_disponivel"] == 7


def test_aprovar_orcamento_sem_estoque_retorna_422(client, headers_admin, setup_base):
    """Aprovação deve falhar com 422 se estoque insuficiente para alguma peça."""
    peca = client.post(
        "/pecas",
        json={
            "nome": "Filtro de óleo",
            "codigo": "FO-003",
            "preco_unitario": "45.00",
            "quantidade_disponivel": 1,
            "quantidade_minima_alerta": 1,
        },
        headers=headers_admin,
    ).json()

    payload = _payload_abertura_unificada(
        setup_base["cliente"],
        setup_base["veiculo"],
        setup_base["servico"],
        "Troca de óleo",
    )
    payload["pecas"] = [{"peca_id": peca["id"], "quantidade": 5}]
    os = client.post("/ordens-de-servico", json=payload, headers=headers_admin).json()
    os_id = os["id"]

    resposta = client.post(f"/ordens-de-servico/{os_id}/aprovar-orcamento")
    assert resposta.status_code == 422


def test_veiculo_com_os_ativa_nao_abre_nova(client, headers_admin, setup_base):
    payload = _payload_abertura_unificada(
        setup_base["cliente"], setup_base["veiculo"], setup_base["servico"]
    )
    client.post("/ordens-de-servico", json=payload, headers=headers_admin)
    resposta = client.post("/ordens-de-servico", json=payload, headers=headers_admin)
    assert resposta.status_code == 422


def test_listar_itens_os(client, headers_admin, setup_base):
    payload = _payload_abertura_unificada(
        setup_base["cliente"], setup_base["veiculo"], setup_base["servico"]
    )
    os = client.post("/ordens-de-servico", json=payload, headers=headers_admin).json()

    resposta = client.get(f"/ordens-de-servico/{os['id']}/itens", headers=headers_admin)
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["pendentes"] == 1
    assert dados["concluidos"] == 0
    assert len(dados["itens"]) == 1
    assert dados["itens"][0]["concluido"] is False


def test_listar_itens_os_apenas_pendentes(client, headers_admin, setup_base):
    payload = _payload_abertura_unificada(
        setup_base["cliente"], setup_base["veiculo"], setup_base["servico"]
    )
    os = client.post("/ordens-de-servico", json=payload, headers=headers_admin).json()
    os_id = os["id"]
    item_id = os["itens_servico"][0]["id"]

    client.post(f"/ordens-de-servico/{os_id}/aprovar-orcamento")
    client.post(
        f"/ordens-de-servico/{os_id}/executar-servico/{item_id}", headers=headers_admin
    )

    resposta = client.get(
        f"/ordens-de-servico/{os_id}/itens?pendentes=true", headers=headers_admin
    )
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["pendentes"] == 0
    assert dados["concluidos"] == 1
    assert len(dados["itens"]) == 0


def test_gerar_orcamento_sem_servicos_retorna_422(client, headers_admin, setup_base):
    payload = {
        "cliente": {
            "nome": setup_base["cliente"]["nome"],
            "email": setup_base["cliente"]["email"],
            "telefone": setup_base["cliente"]["telefone"],
            "cpf": setup_base["cliente"]["cpf"],
        },
        "veiculo": {
            "placa": "OUT0K99",
            "marca": "Honda",
            "modelo": "Civic",
            "ano": 2021,
            "descricao_problema": "Revisão",
        },
        "servicos": [],
    }
    resposta = client.post("/ordens-de-servico", json=payload, headers=headers_admin)
    assert resposta.status_code == 422
