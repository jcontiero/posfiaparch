from abc import ABC, abstractmethod
from uuid import UUID
from src.catalogo.dominio.entidades import Servico


class ServicoRepositorio(ABC):  # pragma: no cover

    @abstractmethod
    def salvar(self, servico: Servico) -> Servico:
        pass

    @abstractmethod
    def listar(self, busca: str | None = None) -> list[Servico]:
        pass

    @abstractmethod
    def buscar_por_id(self, id: UUID) -> Servico | None:
        pass

    @abstractmethod
    def atualizar(self, servico: Servico) -> Servico:
        pass

    @abstractmethod
    def remover(self, id: UUID) -> None:
        pass
