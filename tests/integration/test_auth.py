from src.identidade.aplicacao.casos_de_uso import CriarUsuario
from src.identidade.dominio.entidades import PerfilUsuario
from src.identidade.infraestrutura.repositorios import UsuarioRepositorioImpl
from src.identidade.infraestrutura.bcrypt_provider import BcryptHashProvider


def test_login_com_sucesso(client, db):
    hash_provider = BcryptHashProvider()
    CriarUsuario(UsuarioRepositorioImpl(db), hash_provider).executar(
        email="admin@oficina.com",
        senha="senha123",
        perfil=PerfilUsuario.ADMIN,
    )

    resposta = client.post(
        "/auth/login",
        json={
            "email": "admin@oficina.com",
            "senha": "senha123",
        },
    )

    assert resposta.status_code == 200
    assert "token" in resposta.json()


def test_login_com_senha_errada(client, db):
    hash_provider = BcryptHashProvider()
    CriarUsuario(UsuarioRepositorioImpl(db), hash_provider).executar(
        email="admin@oficina.com",
        senha="senha123",
        perfil=PerfilUsuario.ADMIN,
    )

    resposta = client.post(
        "/auth/login",
        json={
            "email": "admin@oficina.com",
            "senha": "errada",
        },
    )

    assert resposta.status_code == 401


def test_login_usuario_inexistente(client):
    resposta = client.post(
        "/auth/login",
        json={
            "email": "nao@existe.com",
            "senha": "qualquer",
        },
    )

    assert resposta.status_code == 401
