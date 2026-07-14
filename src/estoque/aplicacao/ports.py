from abc import ABC, abstractmethod


class NotificadorEstoque(ABC):
    @abstractmethod
    def notificar_admin_estoque_reposto(
        self,
        nome: str,
        codigo: str,
        quantidade_reposta: int,
        quantidade_atual: int,
    ) -> None: ...
