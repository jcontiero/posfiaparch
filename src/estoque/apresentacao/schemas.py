from decimal import Decimal
from pydantic import BaseModel


class CadastrarPecaRequest(BaseModel):
    nome: str
    codigo: str
    preco_unitario: Decimal
    quantidade_disponivel: int
    quantidade_minima_alerta: int = 5


class AtualizarPecaRequest(BaseModel):
    nome: str | None = None
    preco_unitario: Decimal | None = None
    quantidade_minima_alerta: int | None = None


class ReporEstoqueRequest(BaseModel):
    quantidade: int


class PecaResponse(BaseModel):
    id: str
    nome: str
    codigo: str
    preco_unitario: str
    quantidade_disponivel: int
    quantidade_minima_alerta: int
    alerta_estoque_baixo: bool

    @classmethod
    def from_domain(cls, peca) -> "PecaResponse":
        return cls(
            id=str(peca.id),
            nome=peca.nome,
            codigo=peca.codigo,
            preco_unitario=str(peca.preco_unitario),
            quantidade_disponivel=peca.quantidade_disponivel,
            quantidade_minima_alerta=peca.quantidade_minima_alerta,
            alerta_estoque_baixo=peca.alerta_estoque_baixo,
        )
