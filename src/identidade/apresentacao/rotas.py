from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from src.container import get_autenticar_usuario
from src.identidade.aplicacao.casos_de_uso import AutenticarUsuario
from src.identidade.dominio.excecoes import CredenciaisInvalidasError
from src.identidade.apresentacao.schemas import (
    LoginRequest,
    TokenResponse,
    UsuarioResponse,
)

router = APIRouter(tags=["Autenticação"])


@router.post("/auth/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    caso_de_uso: Annotated[AutenticarUsuario, Depends(get_autenticar_usuario)],
):
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
