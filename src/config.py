from pydantic_settings import BaseSettings


class Configuracoes(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    token_expire_horas: int = 8
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_remetente: str = "noreply@oficina.com"
    email_admin: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


configuracoes = Configuracoes()
