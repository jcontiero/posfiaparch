from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jwt.exceptions import PyJWTError
from src.shared.banco import SessionLocal
from src.shared.seguranca import decodificar_token

security = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_usuario_atual(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    try:
        return decodificar_token(credentials.credentials)
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


def require_admin(payload: dict = Depends(get_usuario_atual)) -> dict:
    if payload.get("perfil") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso restrito ao perfil ADMIN")
    return payload


def require_mecanico(payload: dict = Depends(get_usuario_atual)) -> dict:
    if payload.get("perfil") not in ("ADMIN", "MECANICO"):
        raise HTTPException(status_code=403, detail="Acesso restrito ao perfil MECANICO ou ADMIN")
    return payload
