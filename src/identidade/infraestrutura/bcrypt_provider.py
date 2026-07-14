import bcrypt

from src.identidade.aplicacao.ports import ProvedorHashSenha


class BcryptHashProvider(ProvedorHashSenha):
    def hash(self, senha: str) -> str:
        return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

    def verificar(self, senha: str, hash: str) -> bool:
        return bcrypt.checkpw(senha.encode(), hash.encode())
