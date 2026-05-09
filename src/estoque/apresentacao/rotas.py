from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.shared.dependencias import get_db, get_usuario_atual
from src.estoque.aplicacao.casos_de_uso import (
    CadastrarPeca, ListarPecas, BuscarPeca, AtualizarPeca, ReporEstoque, RemoverPeca,
)
from src.estoque.infraestrutura.repositorios import PecaRepositorioImpl
from src.estoque.dominio.excecoes import (
    PecaNaoEncontradaError, EstoqueInsuficienteError, CodigoPecaDuplicadoError,
)
from src.estoque.apresentacao.schemas import (
    CadastrarPecaRequest, AtualizarPecaRequest, ReporEstoqueRequest, PecaResponse,
)

DBDep = Annotated[Session, Depends(get_db)]
AuthDep = Annotated[dict, Depends(get_usuario_atual)]

router = APIRouter(prefix="/pecas", tags=["Estoque"])


def _repo(db: DBDep) -> PecaRepositorioImpl:
    return PecaRepositorioImpl(db)


RepoDep = Annotated[PecaRepositorioImpl, Depends(_repo)]


@router.post("", response_model=PecaResponse, status_code=201, summary="Cadastrar Peca")
def cadastrar(body: CadastrarPecaRequest, repo: RepoDep, _: AuthDep):
    try:
        peca = CadastrarPeca(repo).executar(**body.model_dump())
        return PecaResponse.from_domain(peca)
    except CodigoPecaDuplicadoError as e:
        raise HTTPException(409, str(e))


@router.get("", response_model=list[PecaResponse], summary="Listar Pecas")
def listar(busca: str | None = None, alerta_estoque_baixo: bool = False,
           repo: RepoDep = None, _: AuthDep = None):
    pecas = ListarPecas(repo).executar(busca, alerta_estoque_baixo)
    return [PecaResponse.from_domain(p) for p in pecas]


@router.get("/codigo/{codigo}", response_model=PecaResponse, summary="Buscar Peca por Codigo")
def buscar_por_codigo(codigo: str, repo: RepoDep, _: AuthDep):
    peca = repo.buscar_por_codigo(codigo)
    if not peca:
        raise HTTPException(404, f"Peça com código '{codigo}' não encontrada")
    return PecaResponse.from_domain(peca)


@router.get("/{id}", response_model=PecaResponse, summary="Buscar Peca")
def buscar(id: UUID, repo: RepoDep, _: AuthDep):
    try:
        return PecaResponse.from_domain(BuscarPeca(repo).executar(id))
    except PecaNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.put("/{id}", response_model=PecaResponse, summary="Atualizar Peca")
def atualizar(id: UUID, body: AtualizarPecaRequest, repo: RepoDep, _: AuthDep):
    try:
        peca = AtualizarPeca(repo).executar(id, **body.model_dump(exclude_none=True))
        return PecaResponse.from_domain(peca)
    except PecaNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.delete("/{id}", status_code=204, summary="Remover Peca")
def remover(id: UUID, repo: RepoDep, _: AuthDep):
    try:
        RemoverPeca(repo).executar(id)
    except PecaNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.post("/{id}/repor-estoque", response_model=PecaResponse, summary="Repor Estoque")
def repor_estoque(id: UUID, body: ReporEstoqueRequest, repo: RepoDep, _: AuthDep):
    try:
        peca = ReporEstoque(repo).executar(id, body.quantidade)
        return PecaResponse.from_domain(peca)
    except PecaNaoEncontradaError as e:
        raise HTTPException(404, str(e))
    except (EstoqueInsuficienteError, ValueError) as e:
        raise HTTPException(422, str(e))
