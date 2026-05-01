import uuid
from sqlalchemy import Column, String, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from src.shared.banco import Base


class PecaModel(Base):
    __tablename__ = "pecas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String, nullable=False)
    codigo = Column(String, unique=True, nullable=False, index=True)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    quantidade_disponivel = Column(Integer, nullable=False, default=0)
    quantidade_minima_alerta = Column(Integer, nullable=False, default=5)
