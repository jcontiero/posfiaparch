from abc import ABC, abstractmethod
from uuid import UUID
from src.estoque.dominio.entidades import Peca


class PecaRepositorio(ABC):

    @abstractmethod
    def salvar(self, peca: Peca) -> Peca: pass

    @abstractmethod
    def buscar_por_id(self, id: UUID) -> Peca | None: pass

    @abstractmethod
    def buscar_por_codigo(self, codigo: str) -> Peca | None: pass

    @abstractmethod
    def listar(self, busca: str | None = None, apenas_alerta: bool = False) -> list[Peca]: pass

    @abstractmethod
    def remover(self, id: UUID) -> None: pass
