import httpx

base_url = "http://localhost:8000"


def test():
    with httpx.Client(base_url=base_url) as client:
        # 1. Login
        response = client.post(
            "/auth/login",
            data={"username": "admin@oficina.com", "password": "senha123"},
        )
        if response.status_code != 200:
            print(f"Login failed: {response.status_code} {response.text}")
            return
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login OK")

        # 2. Criar cliente
        cliente_data = {
            "nome": "João E2E",
            "cpf": "12345678909",
            "email": "joao@e2e.com",
            "telefone": "11999999999",
        }
        r = client.post("/atendimento/clientes", json=cliente_data, headers=headers)
        if r.status_code not in (200, 201):
            print(f"Erro cliente: {r.status_code} {r.text}")
            return
        cliente_id = r.json()["id"]
        print("Cliente OK")

        # 3. Criar veiculo
        veiculo_data = {
            "cliente_id": cliente_id,
            "placa": "ABC1234",
            "marca": "Toyota",
            "modelo": "Corolla",
            "ano": 2020,
            "cor": "Preto",
        }
        r = client.post("/atendimento/veiculos", json=veiculo_data, headers=headers)
        if r.status_code not in (200, 201):
            print(f"Erro veiculo: {r.status_code} {r.text}")
            return
        veiculo_id = r.json()["id"]
        print("Veiculo OK")

        # 4. Criar OS
        os_data = {
            "cliente_id": cliente_id,
            "veiculo_id": veiculo_id,
            "descricao_problema": "Barulho no freio",
        }
        r = client.post("/atendimento/ordens-de-servico", json=os_data, headers=headers)
        if r.status_code not in (200, 201):
            print(f"Erro OS: {r.status_code} {r.text}")
            return
        os_id = r.json()["id"]
        print(f"OS OK: {os_id}")

        # 5. Listar OS
        r = client.get("/atendimento/ordens-de-servico", headers=headers)
        print("Listagem OS OK. Count:", len(r.json()))


if __name__ == "__main__":
    test()
