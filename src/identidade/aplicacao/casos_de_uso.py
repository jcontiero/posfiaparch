from uuid import uuid4

from src.identidade.dominio.entidades import Usuario, PerfilUsuario
from src.identidade.dominio.repositorios import UsuarioRepositorio
from src.identidade.dominio.excecoes import CredenciaisInvalidasError
from src.identidade.aplicacao.ports import ProvedorHashSenha, ProvedorToken


class AutenticarUsuario:
    def __init__(
        self,
        repo: UsuarioRepositorio,
        token_provider: ProvedorToken,
        hash_provider: ProvedorHashSenha,
    ):
        self.repo = repo
        self.token_provider = token_provider
        self.hash_provider = hash_provider

    def executar(self, email: str, senha: str) -> dict:
        usuario = self.repo.buscar_por_email(email)
        if not usuario or not self.hash_provider.verificar(senha, usuario.senha_hash):
            raise CredenciaisInvalidasError()
        token = self.token_provider.criar(
            {"sub": str(usuario.id), "perfil": usuario.perfil.value}
        )
        return {"token": token, "usuario": usuario}


class CriarUsuario:
    def __init__(self, repo: UsuarioRepositorio, hash_provider: ProvedorHashSenha):
        self.repo = repo
        self.hash_provider = hash_provider

    def executar(self, email: str, senha: str, perfil: PerfilUsuario) -> Usuario:
        usuario = Usuario(
            id=uuid4(),
            email=email,
            senha_hash=self.hash_provider.hash(senha),
            perfil=perfil,
        )
        return self.repo.salvar(usuario)
