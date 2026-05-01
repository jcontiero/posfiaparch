from abc import ABC, abstractmethod
from src.identidade.dominio.entidades import Usuario


class UsuarioRepositorio(ABC):

    @abstractmethod
    def buscar_por_email(self, email: str) -> Usuario | None:
        pass

    @abstractmethod
    def salvar(self, usuario: Usuario) -> Usuario:
        pass
