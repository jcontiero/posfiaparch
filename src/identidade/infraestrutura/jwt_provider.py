from datetime import datetime, timedelta, timezone
import jwt

from src.config import Configuracoes
from src.identidade.aplicacao.ports import ProvedorToken


class JwtTokenProvider(ProvedorToken):
    def __init__(self, configuracoes: Configuracoes):
        self.config = configuracoes

    def criar(self, dados: dict, expiracao_horas: int | None = None) -> str:
        payload = dados.copy()
        horas = (
            expiracao_horas
            if expiracao_horas is not None
            else self.config.token_expire_horas
        )
        expiracao = datetime.now(timezone.utc) + timedelta(hours=horas)
        payload["exp"] = expiracao
        return jwt.encode(
            payload, self.config.secret_key, algorithm=self.config.algorithm
        )

    def decodificar(self, token: str) -> dict:
        return jwt.decode(
            token, self.config.secret_key, algorithms=[self.config.algorithm]
        )
