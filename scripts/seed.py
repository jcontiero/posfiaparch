import os
from src.shared.banco import SessionLocal
from src.identidade.aplicacao.casos_de_uso import CriarUsuario
from src.identidade.dominio.entidades import PerfilUsuario
from src.identidade.infraestrutura.repositorios import UsuarioRepositorioImpl

email = os.getenv("ADMIN_EMAIL", "admin@oficina.com")
senha = os.getenv("ADMIN_SENHA", "senha123")

db = SessionLocal()
repo = UsuarioRepositorioImpl(db)

if not repo.buscar_por_email(email):
    CriarUsuario(repo).executar(email, senha, PerfilUsuario.ADMIN)
    print(f"Admin criado: {email}")
else:
    print(f"Admin já existe: {email}")
