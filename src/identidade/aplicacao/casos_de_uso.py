from src.identidade.dominio.entidades import Usuario, PerfilUsuario
from src.identidade.dominio.repositorios import UsuarioRepositorio
from src.identidade.dominio.excecoes import CredenciaisInvalidasError
from src.shared.seguranca import verificar_senha, criar_token, hash_senha
from uuid import uuid4


class AutenticarUsuario:
    def __init__(self, repo: UsuarioRepositorio):
        self.repo = repo

    def executar(self, email: str, senha: str) -> dict:
        usuario = self.repo.buscar_por_email(email)
        if not usuario or not verificar_senha(senha, usuario.senha_hash):
            raise CredenciaisInvalidasError()
        token = criar_token({"sub": str(usuario.id), "perfil": usuario.perfil.value})
        return {"token": token, "usuario": usuario}


class CriarUsuario:
    def __init__(self, repo: UsuarioRepositorio):
        self.repo = repo

    def executar(self, email: str, senha: str, perfil: PerfilUsuario) -> Usuario:
        usuario = Usuario(
            id=uuid4(),
            email=email,
            senha_hash=hash_senha(senha),
            perfil=perfil,
        )
        return self.repo.salvar(usuario)
