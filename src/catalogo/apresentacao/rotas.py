from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.shared.dependencias import get_db, get_usuario_atual
from src.catalogo.aplicacao.casos_de_uso import (
    CadastrarServico,
    ListarServicos,
    BuscarServico,
    AtualizarServico,
    RemoverServico,
)
from src.catalogo.infraestrutura.repositorios import ServicoRepositorioImpl
from src.catalogo.dominio.excecoes import ServicoNaoEncontradoError
from src.catalogo.apresentacao.schemas import (
    ServicoRequest,
    ServicoAtualizarRequest,
    ServicoResponse,
)

DBDep = Annotated[Session, Depends(get_db)]
AuthDep = Annotated[dict, Depends(get_usuario_atual)]

router = APIRouter(tags=["Catálogo"])


@router.post("/servicos", response_model=ServicoResponse, status_code=201)
def cadastrar_servico(
    body: ServicoRequest,
    db: DBDep,
    _: AuthDep,
):
    repo = ServicoRepositorioImpl(db)
    caso_de_uso = CadastrarServico(repo)
    servico = caso_de_uso.executar(
        nome=body.nome,
        descricao=body.descricao,
        preco_base=body.preco_base,
        tempo_estimado_minutos=body.tempo_estimado_minutos,
    )
    return ServicoResponse(
        id=servico.id,
        nome=servico.nome,
        descricao=servico.descricao,
        preco_base=servico.preco_base,
        tempo_estimado_minutos=servico.tempo_estimado_minutos,
    )


@router.get("/servicos", response_model=list[ServicoResponse])
def listar_servicos(
    busca: str | None = Query(default=None),
    db: DBDep = None,
    _: AuthDep = None,
):
    repo = ServicoRepositorioImpl(db)
    caso_de_uso = ListarServicos(repo)
    servicos = caso_de_uso.executar(busca)
    return [
        ServicoResponse(
            id=s.id,
            nome=s.nome,
            descricao=s.descricao,
            preco_base=s.preco_base,
            tempo_estimado_minutos=s.tempo_estimado_minutos,
        )
        for s in servicos
    ]


@router.get("/servicos/{id}", response_model=ServicoResponse)
def buscar_servico(
    id: UUID,
    db: DBDep,
    _: AuthDep,
):
    repo = ServicoRepositorioImpl(db)
    caso_de_uso = BuscarServico(repo)
    try:
        servico = caso_de_uso.executar(id)
        return ServicoResponse(
            id=servico.id,
            nome=servico.nome,
            descricao=servico.descricao,
            preco_base=servico.preco_base,
            tempo_estimado_minutos=servico.tempo_estimado_minutos,
        )
    except ServicoNaoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/servicos/{id}", response_model=ServicoResponse)
def atualizar_servico(
    id: UUID,
    body: ServicoAtualizarRequest,
    db: DBDep,
    _: AuthDep,
):
    repo = ServicoRepositorioImpl(db)
    caso_de_uso = AtualizarServico(repo)
    try:
        servico = caso_de_uso.executar(
            id=id,
            nome=body.nome,
            descricao=body.descricao,
            preco_base=body.preco_base,
            tempo_estimado_minutos=body.tempo_estimado_minutos,
        )
        return ServicoResponse(
            id=servico.id,
            nome=servico.nome,
            descricao=servico.descricao,
            preco_base=servico.preco_base,
            tempo_estimado_minutos=servico.tempo_estimado_minutos,
        )
    except ServicoNaoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/servicos/{id}", status_code=204)
def remover_servico(
    id: UUID,
    db: DBDep,
    _: AuthDep,
):
    repo = ServicoRepositorioImpl(db)
    caso_de_uso = RemoverServico(repo)
    try:
        caso_de_uso.executar(id)
    except ServicoNaoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
