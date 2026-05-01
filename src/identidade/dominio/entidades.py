from dataclasses import dataclass
from uuid import UUID
from enum import Enum


class PerfilUsuario(str, Enum):
    ADMIN = "ADMIN"
    MECANICO = "MECANICO"


@dataclass
class Usuario:
    id: UUID
    email: str
    senha_hash: str
    perfil: PerfilUsuario
