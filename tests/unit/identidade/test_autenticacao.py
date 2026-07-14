import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from src.identidade.aplicacao.casos_de_uso import AutenticarUsuario
from src.identidade.dominio.entidades import Usuario, PerfilUsuario
from src.identidade.dominio.excecoes import CredenciaisInvalidasError
from src.identidade.infraestrutura.bcrypt_provider import BcryptHashProvider


def usuario_fake() -> Usuario:
    hash_provider = BcryptHashProvider()
    return Usuario(
        id=uuid4(),
        email="admin@oficina.com",
        senha_hash=hash_provider.hash("senha123"),
        perfil=PerfilUsuario.ADMIN,
    )


def test_autenticar_com_credenciais_validas():
    repo = MagicMock()
    repo.buscar_por_email.return_value = usuario_fake()
    token_provider = MagicMock()
    token_provider.criar.return_value = "token-fake"
    hash_provider = BcryptHashProvider()

    resultado = AutenticarUsuario(repo, token_provider, hash_provider).executar(
        "admin@oficina.com", "senha123"
    )

    assert resultado["token"] == "token-fake"
    assert resultado["usuario"].email == "admin@oficina.com"


def test_autenticar_com_senha_errada():
    repo = MagicMock()
    repo.buscar_por_email.return_value = usuario_fake()
    token_provider = MagicMock()
    hash_provider = BcryptHashProvider()

    with pytest.raises(CredenciaisInvalidasError):
        AutenticarUsuario(repo, token_provider, hash_provider).executar(
            "admin@oficina.com", "senha_errada"
        )


def test_autenticar_usuario_inexistente():
    repo = MagicMock()
    repo.buscar_por_email.return_value = None
    token_provider = MagicMock()
    hash_provider = BcryptHashProvider()

    with pytest.raises(CredenciaisInvalidasError):
        AutenticarUsuario(repo, token_provider, hash_provider).executar(
            "nao@existe.com", "qualquer"
        )
