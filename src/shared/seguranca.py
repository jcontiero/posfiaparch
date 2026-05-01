from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from src.config import configuracoes


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def verificar_senha(senha: str, hash: str) -> bool:
    return bcrypt.checkpw(senha.encode(), hash.encode())


def criar_token(dados: dict) -> str:
    payload = dados.copy()
    expiracao = datetime.now(timezone.utc) + timedelta(hours=configuracoes.token_expire_horas)
    payload["exp"] = expiracao
    return jwt.encode(payload, configuracoes.secret_key, algorithm=configuracoes.algorithm)


def decodificar_token(token: str) -> dict:
    return jwt.decode(token, configuracoes.secret_key, algorithms=[configuracoes.algorithm])
