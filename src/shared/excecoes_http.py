from fastapi import Request
from fastapi.responses import JSONResponse


def erro(status: int, mensagem: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"erro": mensagem})


async def handler_nao_encontrado(request: Request, exc: Exception) -> JSONResponse:
    return erro(404, str(exc))


async def handler_conflito(request: Request, exc: Exception) -> JSONResponse:
    return erro(409, str(exc))


async def handler_regra_negocio(request: Request, exc: Exception) -> JSONResponse:
    return erro(422, str(exc))


async def handler_credenciais_invalidas(request: Request, exc: Exception) -> JSONResponse:
    return erro(401, str(exc))
