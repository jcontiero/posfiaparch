import uuid
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.banco import Base


class PecaModel(Base):
    __tablename__ = "pecas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String, nullable=False)
    codigo: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantidade_disponivel: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    quantidade_minima_alerta: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5
    )
