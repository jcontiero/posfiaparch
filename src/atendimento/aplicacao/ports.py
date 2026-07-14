from abc import ABC, abstractmethod


class Notificador(ABC):
    @abstractmethod
    def notificar_admin_diagnostico_concluido(
        self,
        os_id: str,
        placa: str,
        cliente_nome: str,
        descricao_problema: str,
        laudo_diagnostico: str | None = None,
    ) -> None: ...

    @abstractmethod
    def notificar_cliente_orcamento_disponivel(
        self,
        email: str,
        nome: str,
        placa: str,
        os_id: str,
        valor: str,
        itens_servico: list[dict],
        itens_peca: list[dict],
    ) -> None: ...

    @abstractmethod
    def notificar_admin_servicos_concluidos(
        self,
        os_id: str,
        placa: str,
        cliente_nome: str,
        itens_servico: list[dict],
    ) -> None: ...

    @abstractmethod
    def notificar_admin_orcamento_recusado(
        self,
        os_id: str,
        placa: str,
        cliente_nome: str,
        valor: str,
        motivo: str,
    ) -> None: ...

    @abstractmethod
    def notificar_cliente_veiculo_pronto(
        self,
        email: str,
        nome: str,
        placa: str,
        valor_total: str,
    ) -> None: ...
