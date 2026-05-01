import uuid
from sqlalchemy import Column, String, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from src.shared.banco import Base


class ServicoModel(Base):
    __tablename__ = "servicos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String, nullable=False, index=True)
    descricao = Column(String, nullable=False)
    preco_base = Column(Numeric(10, 2), nullable=False)
    tempo_estimado_minutos = Column(Integer, nullable=False)
