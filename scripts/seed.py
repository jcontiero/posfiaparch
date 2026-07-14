import os
from src.container import Container
from src.identidade.aplicacao.casos_de_uso import CriarUsuario
from src.identidade.dominio.entidades import PerfilUsuario
from src.identidade.infraestrutura.repositorios import UsuarioRepositorioImpl

email = os.getenv("ADMIN_EMAIL", "admin@oficina.com")
senha = os.getenv("ADMIN_SENHA", "senha123")

container = Container()
db = container.SessionLocal()
repo = UsuarioRepositorioImpl(db)

try:
    if not repo.buscar_por_email(email):
        CriarUsuario(repo, container.hash_provider).executar(
            email, senha, PerfilUsuario.ADMIN
        )
        print(f"Admin criado: {email}")
    else:
        print(f"Admin já existe: {email}")
    db.commit()
except Exception as erro:
    db.rollback()
    print(f"Erro ao criar admin: {erro}")
    raise
finally:
    db.close()
