import uuid
from sqlalchemy import Column, String, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from src.shared.banco import Base
from src.identidade.dominio.entidades import PerfilUsuario


class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    senha_hash = Column(String, nullable=False)
    perfil = Column(SAEnum(PerfilUsuario, name="perfil_usuario"), nullable=False)
