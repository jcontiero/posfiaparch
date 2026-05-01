from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    senha: str


class UsuarioResponse(BaseModel):
    id: str
    email: str
    perfil: str


class TokenResponse(BaseModel):
    token: str
    usuario: UsuarioResponse
