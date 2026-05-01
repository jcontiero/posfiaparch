def _cadastrar_peca(client, headers, codigo="P001", qtd=20):
    return client.post("/pecas", json={
        "nome": "Pastilha de freio",
        "codigo": codigo,
        "preco_unitario": "85.00",
        "quantidade_disponivel": qtd,
        "quantidade_minima_alerta": 5,
    }, headers=headers).json()


def test_cadastrar_peca(client, headers_admin):
    resposta = client.post("/pecas", json={
        "nome": "Pastilha de freio",
        "codigo": "PF001",
        "preco_unitario": "85.00",
        "quantidade_disponivel": 20,
        "quantidade_minima_alerta": 5,
    }, headers=headers_admin)

    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["nome"] == "Pastilha de freio"
    assert dados["quantidade_disponivel"] == 20
    assert dados["alerta_estoque_baixo"] is False


def test_codigo_duplicado_retorna_409(client, headers_admin):
    _cadastrar_peca(client, headers_admin)
    resposta = client.post("/pecas", json={
        "nome": "Outra peça", "codigo": "P001",
        "preco_unitario": "10.00", "quantidade_disponivel": 5,
    }, headers=headers_admin)
    assert resposta.status_code == 409


def test_repor_estoque(client, headers_admin):
    peca = _cadastrar_peca(client, headers_admin, qtd=10)
    resposta = client.post(f"/pecas/{peca['id']}/repor-estoque",
                           json={"quantidade": 5}, headers=headers_admin)
    assert resposta.status_code == 200
    assert resposta.json()["quantidade_disponivel"] == 15


def test_repor_quantidade_invalida(client, headers_admin):
    peca = _cadastrar_peca(client, headers_admin)
    resposta = client.post(f"/pecas/{peca['id']}/repor-estoque",
                           json={"quantidade": 0}, headers=headers_admin)
    assert resposta.status_code == 422


def test_alerta_estoque_baixo(client, headers_admin):
    peca = _cadastrar_peca(client, headers_admin, qtd=3)
    resposta = client.get(f"/pecas/{peca['id']}", headers=headers_admin)
    assert resposta.json()["alerta_estoque_baixo"] is True


def test_filtrar_por_alerta(client, headers_admin):
    _cadastrar_peca(client, headers_admin, codigo="P001", qtd=2)
    _cadastrar_peca(client, headers_admin, codigo="P002", qtd=20)

    resposta = client.get("/pecas?alerta_estoque_baixo=true", headers=headers_admin)
    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_remover_peca(client, headers_admin):
    peca = _cadastrar_peca(client, headers_admin)
    resposta = client.delete(f"/pecas/{peca['id']}", headers=headers_admin)
    assert resposta.status_code == 204
