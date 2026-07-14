from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from src.shared.dependencias import get_usuario_atual
from src.container import (
    get_cadastrar_servico,
    get_listar_servicos,
    get_buscar_servico,
    get_atualizar_servico,
    get_remover_servico,
)
from src.catalogo.aplicacao.casos_de_uso import (
    CadastrarServico,
    ListarServicos,
    BuscarServico,
    AtualizarServico,
    RemoverServico,
)
from src.catalogo.dominio.excecoes import ServicoNaoEncontradoError
from src.catalogo.apresentacao.schemas import (
    ServicoRequest,
    ServicoAtualizarRequest,
    ServicoResponse,
)

AuthDep = Annotated[dict, Depends(get_usuario_atual)]

router = APIRouter(tags=["Catálogo"])


@router.post("/servicos", response_model=ServicoResponse, status_code=201)
def cadastrar_servico(
    body: ServicoRequest,
    caso_de_uso: Annotated[CadastrarServico, Depends(get_cadastrar_servico)],
    _: AuthDep,
):
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
    caso_de_uso: Annotated[ListarServicos, Depends(get_listar_servicos)],
    _: AuthDep,
    busca: str | None = Query(default=None),
):
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
    caso_de_uso: Annotated[BuscarServico, Depends(get_buscar_servico)],
    _: AuthDep,
):
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
    caso_de_uso: Annotated[AtualizarServico, Depends(get_atualizar_servico)],
    _: AuthDep,
):
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
    caso_de_uso: Annotated[RemoverServico, Depends(get_remover_servico)],
    _: AuthDep,
):
    try:
        caso_de_uso.executar(id)
    except ServicoNaoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
