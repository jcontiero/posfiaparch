import uuid
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.banco import Base


class ServicoModel(Base):
    __tablename__ = "servicos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String, nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(String, nullable=False)
    preco_base: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tempo_estimado_minutos: Mapped[int] = mapped_column(Integer, nullable=False)
