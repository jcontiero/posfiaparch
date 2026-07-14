from abc import ABC, abstractmethod
from uuid import UUID
from src.atendimento.dominio.entidades import Cliente, Veiculo, OrdemDeServico
from src.atendimento.dominio.value_objects import StatusOS


class ClienteRepositorio(ABC):  # pragma: no cover

    @abstractmethod
    def salvar(self, cliente: Cliente) -> Cliente:
        pass

    @abstractmethod
    def buscar_por_id(self, id: UUID) -> Cliente | None:
        pass

    @abstractmethod
    def buscar_por_cpf(self, cpf: str) -> Cliente | None:
        pass

    @abstractmethod
    def buscar_por_cnpj(self, cnpj: str) -> Cliente | None:
        pass

    @abstractmethod
    def listar(self, busca: str | None = None) -> list[Cliente]:
        pass

    @abstractmethod
    def remover(self, id: UUID) -> None:
        pass


class VeiculoRepositorio(ABC):  # pragma: no cover

    @abstractmethod
    def salvar(self, veiculo: Veiculo) -> Veiculo:
        pass

    @abstractmethod
    def buscar_por_id(self, id: UUID) -> Veiculo | None:
        pass

    @abstractmethod
    def buscar_por_placa(self, placa: str) -> Veiculo | None:
        pass

    @abstractmethod
    def listar(self, cliente_id: UUID | None = None) -> list[Veiculo]:
        pass

    @abstractmethod
    def remover(self, id: UUID) -> None:
        pass


class OrdemDeServicoRepositorio(ABC):  # pragma: no cover

    @abstractmethod
    def salvar(self, os: OrdemDeServico) -> OrdemDeServico:
        pass

    @abstractmethod
    def buscar_por_id(self, id: UUID) -> OrdemDeServico | None:
        pass

    @abstractmethod
    def listar(
        self,
        status: StatusOS | None = None,
        cliente_id: UUID | None = None,
    ) -> list[OrdemDeServico]:
        pass

    @abstractmethod
    def buscar_ativa_por_veiculo(self, veiculo_id: UUID) -> OrdemDeServico | None:
        pass

    @abstractmethod
    def existe_os_ativa_por_cliente(self, cliente_id: UUID) -> bool:
        pass
