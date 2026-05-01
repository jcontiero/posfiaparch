from sqlalchemy.orm import Session
from src.identidade.dominio.entidades import Usuario
from src.identidade.dominio.repositorios import UsuarioRepositorio
from src.identidade.infraestrutura.modelos import UsuarioModel


class UsuarioRepositorioImpl(UsuarioRepositorio):
    def __init__(self, db: Session):
        self.db = db

    def buscar_por_email(self, email: str) -> Usuario | None:
        modelo = self.db.query(UsuarioModel).filter(UsuarioModel.email == email).first()
        if not modelo:
            return None
        return self._para_entidade(modelo)

    def salvar(self, usuario: Usuario) -> Usuario:
        modelo = UsuarioModel(
            id=usuario.id,
            email=usuario.email,
            senha_hash=usuario.senha_hash,
            perfil=usuario.perfil,
        )
        self.db.add(modelo)
        self.db.commit()
        return usuario

    def _para_entidade(self, modelo: UsuarioModel) -> Usuario:
        return Usuario(
            id=modelo.id,
            email=modelo.email,
            senha_hash=modelo.senha_hash,
            perfil=modelo.perfil,
        )
