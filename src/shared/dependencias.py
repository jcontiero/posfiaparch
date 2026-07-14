from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import PyJWTError

from src.container import get_token_provider
from src.identidade.aplicacao.ports import ProvedorToken

security = HTTPBearer()


def get_usuario_atual(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_provider: ProvedorToken = Depends(get_token_provider),
) -> dict:
    try:
        return token_provider.decodificar(credentials.credentials)
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


def require_admin(payload: dict = Depends(get_usuario_atual)) -> dict:
    if payload.get("perfil") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso restrito ao perfil ADMIN")
    return payload


def require_mecanico(payload: dict = Depends(get_usuario_atual)) -> dict:
    if payload.get("perfil") not in ("ADMIN", "MECANICO"):
        raise HTTPException(
            status_code=403, detail="Acesso restrito ao perfil MECANICO ou ADMIN"
        )
    return payload
