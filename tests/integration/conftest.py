import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import Configuracoes
from src.main import criar_app
from src.shared.banco import Base
from src.identidade.infraestrutura.bcrypt_provider import BcryptHashProvider

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+pg8000://oficina_user:oficina_pass@localhost:5432/oficina_test",
)

engine_teste = create_engine(TEST_DATABASE_URL)
SessionTeste = sessionmaker(autocommit=False, autoflush=False, bind=engine_teste)


def _config_teste() -> Configuracoes:
    return Configuracoes(
        database_url=TEST_DATABASE_URL,
        secret_key="test-secret-key-32-chars-length",
    )


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine_teste)
    yield
    Base.metadata.drop_all(bind=engine_teste)


@pytest.fixture
def db():
    sessao = SessionTeste()
    try:
        yield sessao
    finally:
        sessao.close()


@pytest.fixture(autouse=True)
def limpar_banco(db):
    yield
    for tabela in reversed(Base.metadata.sorted_tables):
        db.execute(tabela.delete())
    db.commit()


@pytest.fixture
def app_test():
    return criar_app(_config_teste())


@pytest.fixture
def client(app_test, db):
    container = app_test.state.container

    def override_get_db():
        yield db

    original_get_db = container.get_db
    container.get_db = override_get_db
    yield TestClient(app_test)
    container.get_db = original_get_db


@pytest.fixture
def token_admin(client, db):
    from src.identidade.aplicacao.casos_de_uso import CriarUsuario
    from src.identidade.dominio.entidades import PerfilUsuario
    from src.identidade.infraestrutura.repositorios import UsuarioRepositorioImpl

    hash_provider = BcryptHashProvider()
    CriarUsuario(UsuarioRepositorioImpl(db), hash_provider).executar(
        email="admin@oficina.com", senha="senha123", perfil=PerfilUsuario.ADMIN
    )
    resposta = client.post(
        "/auth/login", json={"email": "admin@oficina.com", "senha": "senha123"}
    )
    return resposta.json()["token"]


@pytest.fixture
def headers_admin(token_admin):
    return {"Authorization": f"Bearer {token_admin}"}
