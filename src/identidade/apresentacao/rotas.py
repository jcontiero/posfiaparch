from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.shared.dependencias import get_db
from src.identidade.aplicacao.casos_de_uso import AutenticarUsuario
from src.identidade.infraestrutura.repositorios import UsuarioRepositorioImpl
from src.identidade.dominio.excecoes import CredenciaisInvalidasError
from src.identidade.apresentacao.schemas import LoginRequest, TokenResponse, UsuarioResponse

DBDep = Annotated[Session, Depends(get_db)]

router = APIRouter(tags=["Autenticação"])


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DBDep):
    repo = UsuarioRepositorioImpl(db)
    caso_de_uso = AutenticarUsuario(repo)
    try:
        resultado = caso_de_uso.executar(body.email, body.senha)
        usuario = resultado["usuario"]
        return TokenResponse(
            token=resultado["token"],
            usuario=UsuarioResponse(
                id=str(usuario.id),
                email=usuario.email,
                perfil=usuario.perfil.value,
            ),
        )
    except CredenciaisInvalidasError as e:
        raise HTTPException(status_code=401, detail=str(e))
