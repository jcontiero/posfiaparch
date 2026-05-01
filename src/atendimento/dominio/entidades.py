from dataclasses import dataclass, field
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timezone

from src.atendimento.dominio.value_objects import StatusOS, TRANSICOES_VALIDAS, CPF, CNPJ, Placa
from src.atendimento.dominio.excecoes import (
    TransicaoInvalidaError,
    OsSemServicosError,
    ServicosNaoConcluidos,
    ItemNaoEncontradoError,
)


@dataclass
class Cliente:
    id: UUID
    nome: str
    cpf: CPF | None
    cnpj: CNPJ | None
    email: str
    telefone: str

    def __post_init__(self):
        tem_cpf = self.cpf is not None
        tem_cnpj = self.cnpj is not None
        if tem_cpf == tem_cnpj:
            raise ValueError("Cliente deve ter CPF ou CNPJ — nunca ambos ou nenhum")


@dataclass
class Veiculo:
    id: UUID
    cliente_id: UUID
    placa: Placa
    marca: str
    modelo: str
    ano: int
    cor: str = ""


@dataclass
class ItemServico:
    id: UUID
    servico_id: UUID
    descricao: str
    preco_unitario: Decimal
    observacao: str = ""
    concluido: bool = False
    concluido_em: datetime | None = None


@dataclass
class ItemPeca:
    id: UUID
    peca_id: UUID
    descricao: str
    quantidade: int
    preco_unitario: Decimal

    @property
    def preco_total(self) -> Decimal:
        return self.preco_unitario * self.quantidade


@dataclass
class OrdemDeServico:
    id: UUID
    cliente_id: UUID
    veiculo_id: UUID
    descricao_problema: str
    status: StatusOS = StatusOS.RECEBIDA
    valor_orcamento: Decimal | None = None
    criada_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    atualizada_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    itens_servico: list[ItemServico] = field(default_factory=list)
    itens_peca: list[ItemPeca] = field(default_factory=list)

    def iniciar_diagnostico(self) -> None:
        self._transicionar_para(StatusOS.EM_DIAGNOSTICO)

    def finalizar_diagnostico(self) -> None:
        self._transicionar_para(StatusOS.AGUARDANDO_ORCAMENTO)

    def adicionar_servico(
        self,
        servico_id: UUID,
        descricao: str,
        preco_unitario: Decimal,
        observacao: str = "",
    ) -> ItemServico:
        if self.status not in (StatusOS.EM_DIAGNOSTICO, StatusOS.AGUARDANDO_ORCAMENTO):
            raise TransicaoInvalidaError(self.status, StatusOS.EM_DIAGNOSTICO)
        item = ItemServico(
            id=uuid4(),
            servico_id=servico_id,
            descricao=descricao,
            preco_unitario=preco_unitario,
            observacao=observacao,
        )
        self.itens_servico.append(item)
        return item

    def adicionar_peca(
        self,
        peca_id: UUID,
        descricao: str,
        quantidade: int,
        preco_unitario: Decimal,
    ) -> ItemPeca:
        if self.status not in (StatusOS.EM_DIAGNOSTICO, StatusOS.AGUARDANDO_ORCAMENTO):
            raise TransicaoInvalidaError(self.status, StatusOS.AGUARDANDO_ORCAMENTO)
        item = ItemPeca(
            id=uuid4(),
            peca_id=peca_id,
            descricao=descricao,
            quantidade=quantidade,
            preco_unitario=preco_unitario,
        )
        self.itens_peca.append(item)
        return item

    def gerar_orcamento(self) -> None:
        if not self.itens_servico:
            raise OsSemServicosError()
        total = sum(i.preco_unitario for i in self.itens_servico)
        total += sum(i.preco_total for i in self.itens_peca)
        self.valor_orcamento = total
        self._transicionar_para(StatusOS.AGUARDANDO_APROVACAO)

    def aprovar_orcamento(self) -> None:
        self._transicionar_para(StatusOS.EM_EXECUCAO)

    def recusar_orcamento(self) -> None:
        self._transicionar_para(StatusOS.CANCELADA)

    def executar_servico(self, item_id: UUID) -> bool:
        item = next((i for i in self.itens_servico if i.id == item_id), None)
        if not item:
            raise ItemNaoEncontradoError(item_id)
        if self.status != StatusOS.EM_EXECUCAO:
            raise TransicaoInvalidaError(self.status, StatusOS.EM_EXECUCAO)
        item.concluido = True
        item.concluido_em = datetime.now(timezone.utc)
        todos_concluidos = all(i.concluido for i in self.itens_servico)
        if todos_concluidos:
            self._transicionar_para(StatusOS.SERVICOS_CONCLUIDOS)
        return todos_concluidos

    def finalizar(self) -> None:
        self._transicionar_para(StatusOS.FINALIZADA)

    def entregar(self) -> None:
        self._transicionar_para(StatusOS.ENTREGUE)

    def _transicionar_para(self, novo_status: StatusOS) -> None:
        if novo_status not in TRANSICOES_VALIDAS[self.status]:
            raise TransicaoInvalidaError(self.status, novo_status)
        self.status = novo_status
        self.atualizada_em = datetime.now(timezone.utc)
