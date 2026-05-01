from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass
class Servico:
    id: UUID
    nome: str
    descricao: str
    preco_base: Decimal
    tempo_estimado_minutos: int
