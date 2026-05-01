import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from src.identidade.aplicacao.casos_de_uso import AutenticarUsuario
from src.identidade.dominio.entidades import Usuario, PerfilUsuario
from src.identidade.dominio.excecoes import CredenciaisInvalidasError
from src.shared.seguranca import hash_senha


def usuario_fake() -> Usuario:
    return Usuario(
        id=uuid4(),
        email="admin@oficina.com",
        senha_hash=hash_senha("senha123"),
        perfil=PerfilUsuario.ADMIN,
    )


def test_autenticar_com_credenciais_validas():
    repo = MagicMock()
    repo.buscar_por_email.return_value = usuario_fake()

    resultado = AutenticarUsuario(repo).executar("admin@oficina.com", "senha123")

    assert "token" in resultado
    assert resultado["usuario"].email == "admin@oficina.com"


def test_autenticar_com_senha_errada():
    repo = MagicMock()
    repo.buscar_por_email.return_value = usuario_fake()

    with pytest.raises(CredenciaisInvalidasError):
        AutenticarUsuario(repo).executar("admin@oficina.com", "senha_errada")


def test_autenticar_usuario_inexistente():
    repo = MagicMock()
    repo.buscar_por_email.return_value = None

    with pytest.raises(CredenciaisInvalidasError):
        AutenticarUsuario(repo).executar("nao@existe.com", "qualquer")
