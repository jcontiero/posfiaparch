from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel


class ServicoRequest(BaseModel):
    nome: str
    descricao: str
    preco_base: Decimal
    tempo_estimado_minutos: int


class ServicoAtualizarRequest(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    preco_base: Decimal | None = None
    tempo_estimado_minutos: int | None = None


class ServicoResponse(BaseModel):
    id: UUID
    nome: str
    descricao: str
    preco_base: Decimal
    tempo_estimado_minutos: int
