from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from src.shared.dependencias import get_usuario_atual
from src.container import (
    get_cadastrar_peca,
    get_listar_pecas,
    get_buscar_peca,
    get_atualizar_peca,
    get_repor_estoque,
    get_remover_peca,
)
from src.estoque.aplicacao.casos_de_uso import (
    CadastrarPeca,
    ListarPecas,
    BuscarPeca,
    AtualizarPeca,
    ReporEstoque,
    RemoverPeca,
)
from src.estoque.dominio.excecoes import (
    PecaNaoEncontradaError,
    EstoqueInsuficienteError,
    CodigoPecaDuplicadoError,
)
from src.estoque.apresentacao.schemas import (
    CadastrarPecaRequest,
    AtualizarPecaRequest,
    ReporEstoqueRequest,
    PecaResponse,
)

AuthDep = Annotated[dict, Depends(get_usuario_atual)]

router = APIRouter(prefix="/pecas", tags=["Estoque"])


@router.post("", response_model=PecaResponse, status_code=201, summary="Cadastrar Peca")
def cadastrar(
    body: CadastrarPecaRequest,
    caso_de_uso: Annotated[CadastrarPeca, Depends(get_cadastrar_peca)],
    _: AuthDep,
):
    try:
        peca = caso_de_uso.executar(**body.model_dump())
        return PecaResponse.from_domain(peca)
    except CodigoPecaDuplicadoError as e:
        raise HTTPException(409, str(e))


@router.get("", response_model=list[PecaResponse], summary="Listar Pecas")
def listar(
    caso_de_uso: Annotated[ListarPecas, Depends(get_listar_pecas)],
    _: AuthDep,
    busca: str | None = None,
    alerta_estoque_baixo: bool = False,
):
    pecas = caso_de_uso.executar(busca, alerta_estoque_baixo)
    return [PecaResponse.from_domain(p) for p in pecas]


@router.get(
    "/codigo/{codigo}", response_model=PecaResponse, summary="Buscar Peca por Codigo"
)
def buscar_por_codigo(
    codigo: str,
    caso_de_uso: Annotated[BuscarPeca, Depends(get_buscar_peca)],
    _: AuthDep,
):
    peca = caso_de_uso.repo.buscar_por_codigo(codigo)
    if not peca:
        raise HTTPException(404, f"Peça com código '{codigo}' não encontrada")
    return PecaResponse.from_domain(peca)


@router.get("/{id}", response_model=PecaResponse, summary="Buscar Peca")
def buscar(
    id: UUID,
    caso_de_uso: Annotated[BuscarPeca, Depends(get_buscar_peca)],
    _: AuthDep,
):
    try:
        return PecaResponse.from_domain(caso_de_uso.executar(id))
    except PecaNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.put("/{id}", response_model=PecaResponse, summary="Atualizar Peca")
def atualizar(
    id: UUID,
    body: AtualizarPecaRequest,
    caso_de_uso: Annotated[AtualizarPeca, Depends(get_atualizar_peca)],
    _: AuthDep,
):
    try:
        peca = caso_de_uso.executar(id=id, **body.model_dump(exclude_none=True))
        return PecaResponse.from_domain(peca)
    except PecaNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.delete("/{id}", status_code=204, summary="Remover Peca")
def remover(
    id: UUID,
    caso_de_uso: Annotated[RemoverPeca, Depends(get_remover_peca)],
    _: AuthDep,
):
    try:
        caso_de_uso.executar(id)
    except PecaNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.post(
    "/{id}/repor-estoque", response_model=PecaResponse, summary="Repor Estoque"
)
def repor_estoque(
    id: UUID,
    body: ReporEstoqueRequest,
    caso_de_uso: Annotated[ReporEstoque, Depends(get_repor_estoque)],
    _: AuthDep,
):
    try:
        peca = caso_de_uso.executar(id, body.quantidade)
        return PecaResponse.from_domain(peca)
    except PecaNaoEncontradaError as e:
        raise HTTPException(404, str(e))
    except (EstoqueInsuficienteError, ValueError) as e:
        raise HTTPException(422, str(e))
