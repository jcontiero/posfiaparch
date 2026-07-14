import uuid
from sqlalchemy import String, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.banco import Base
from src.identidade.dominio.entidades import PerfilUsuario


class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String, nullable=False)
    perfil: Mapped[PerfilUsuario] = mapped_column(
        SAEnum(PerfilUsuario, name="perfil_usuario"), nullable=False
    )
