def _cadastrar_servico(client, headers, nome="Troca de óleo"):
    return client.post("/servicos", json={
        "nome": nome,
        "descricao": "Troca de óleo do motor",
        "preco_base": "150.00",
        "tempo_estimado_minutos": 60,
    }, headers=headers).json()


def test_cadastrar_servico(client, headers_admin):
    resposta = client.post("/servicos", json={
        "nome": "Troca de óleo",
        "descricao": "Troca de óleo do motor",
        "preco_base": "150.00",
        "tempo_estimado_minutos": 60,
    }, headers=headers_admin)

    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["nome"] == "Troca de óleo"
    assert dados["preco_base"] == "150.00"


def test_listar_servicos(client, headers_admin):
    _cadastrar_servico(client, headers_admin, "Troca de óleo")
    _cadastrar_servico(client, headers_admin, "Alinhamento")

    resposta = client.get("/servicos", headers=headers_admin)
    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_filtrar_servicos_por_nome(client, headers_admin):
    _cadastrar_servico(client, headers_admin, "Troca de óleo")
    _cadastrar_servico(client, headers_admin, "Alinhamento")

    resposta = client.get("/servicos?busca=óleo", headers=headers_admin)
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["nome"] == "Troca de óleo"


def test_atualizar_servico(client, headers_admin):
    servico = _cadastrar_servico(client, headers_admin)
    resposta = client.put(f"/servicos/{servico['id']}",
                          json={"preco_base": "180.00"}, headers=headers_admin)
    assert resposta.status_code == 200
    assert resposta.json()["preco_base"] == "180.00"


def test_buscar_servico_inexistente(client, headers_admin):
    from uuid import uuid4
    resposta = client.get(f"/servicos/{uuid4()}", headers=headers_admin)
    assert resposta.status_code == 404


def test_remover_servico(client, headers_admin):
    servico = _cadastrar_servico(client, headers_admin)
    resposta = client.delete(f"/servicos/{servico['id']}", headers=headers_admin)
    assert resposta.status_code == 204
