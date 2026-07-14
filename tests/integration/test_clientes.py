def test_cadastrar_cliente_pf(client, headers_admin):
    resposta = client.post(
        "/clientes",
        json={
            "nome": "João Silva",
            "email": "joao@email.com",
            "telefone": "(11) 99999-0000",
            "cpf": "529.982.247-25",
        },
        headers=headers_admin,
    )

    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["nome"] == "João Silva"
    assert dados["cpf"] == "52998224725"
    assert dados["cnpj"] is None


def test_cadastrar_cliente_pj(client, headers_admin):
    resposta = client.post(
        "/clientes",
        json={
            "nome": "Empresa XYZ",
            "email": "contato@xyz.com",
            "telefone": "(11) 3000-0000",
            "cnpj": "11.222.333/0001-81",
        },
        headers=headers_admin,
    )

    assert resposta.status_code == 201
    assert resposta.json()["cnpj"] == "11222333000181"


def test_cadastrar_cliente_cpf_invalido(client, headers_admin):
    resposta = client.post(
        "/clientes",
        json={
            "nome": "João",
            "email": "j@j.com",
            "telefone": "11",
            "cpf": "111.111.111-11",
        },
        headers=headers_admin,
    )

    assert resposta.status_code in (400, 422)


def test_cpf_duplicado_retorna_409(client, headers_admin):
    dados = {
        "nome": "João",
        "email": "j@j.com",
        "telefone": "11",
        "cpf": "529.982.247-25",
    }
    client.post("/clientes", json=dados, headers=headers_admin)
    resposta = client.post("/clientes", json=dados, headers=headers_admin)
    assert resposta.status_code == 409


def test_listar_clientes(client, headers_admin):
    client.post(
        "/clientes",
        json={
            "nome": "Maria",
            "email": "m@m.com",
            "telefone": "11",
            "cpf": "529.982.247-25",
        },
        headers=headers_admin,
    )
    resposta = client.get("/clientes", headers=headers_admin)
    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_buscar_cliente_por_id(client, headers_admin):
    criado = client.post(
        "/clientes",
        json={
            "nome": "Maria",
            "email": "m@m.com",
            "telefone": "11",
            "cpf": "529.982.247-25",
        },
        headers=headers_admin,
    ).json()

    resposta = client.get(f"/clientes/{criado['id']}", headers=headers_admin)
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Maria"


def test_buscar_cliente_inexistente(client, headers_admin):
    from uuid import uuid4

    resposta = client.get(f"/clientes/{uuid4()}", headers=headers_admin)
    assert resposta.status_code == 404


def test_atualizar_cliente(client, headers_admin):
    criado = client.post(
        "/clientes",
        json={
            "nome": "Maria",
            "email": "m@m.com",
            "telefone": "11",
            "cpf": "529.982.247-25",
        },
        headers=headers_admin,
    ).json()

    resposta = client.put(
        f"/clientes/{criado['id']}", json={"nome": "Maria Silva"}, headers=headers_admin
    )
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Maria Silva"


def test_remover_cliente(client, headers_admin):
    criado = client.post(
        "/clientes",
        json={
            "nome": "Maria",
            "email": "m@m.com",
            "telefone": "11",
            "cpf": "529.982.247-25",
        },
        headers=headers_admin,
    ).json()

    resposta = client.delete(f"/clientes/{criado['id']}", headers=headers_admin)
    assert resposta.status_code == 204


def test_rota_exige_autenticacao(client):
    resposta = client.get("/clientes")
    assert resposta.status_code in (401, 403)
