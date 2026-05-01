from typing import Annotated
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.shared.dependencias import get_db, get_usuario_atual
from src.relatorios.apresentacao.schemas import RelatorioTempoMedioResponse, TempoMedioServicoResponse
from src.atendimento.infraestrutura.modelos import ItemServicoModel, OrdemDeServicoModel
from src.catalogo.infraestrutura.modelos import ServicoModel
from src.atendimento.dominio.value_objects import StatusOS

DBDep = Annotated[Session, Depends(get_db)]
AuthDep = Annotated[dict, Depends(get_usuario_atual)]

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


@router.get("/tempo-medio-servicos", response_model=RelatorioTempoMedioResponse)
def tempo_medio_servicos(
    data_inicio: str | None = None,
    data_fim: str | None = None,
    db: DBDep = None,
    _: AuthDep = None,
):
    query = (
        db.query(
            ItemServicoModel.servico_id,
            ItemServicoModel.descricao.label("nome"),
            func.count(ItemServicoModel.id).label("total"),
            func.avg(
                func.extract("epoch",
                             ItemServicoModel.concluido_em - OrdemDeServicoModel.criada_em) / 60
            ).label("media_minutos"),
        )
        .join(OrdemDeServicoModel, ItemServicoModel.os_id == OrdemDeServicoModel.id)
        .filter(ItemServicoModel.concluido == True)  # noqa: E712
        .filter(OrdemDeServicoModel.status.in_([StatusOS.FINALIZADA, StatusOS.ENTREGUE]))
        .group_by(ItemServicoModel.servico_id, ItemServicoModel.descricao)
    )

    if data_inicio:
        dt_inicio = datetime.fromisoformat(data_inicio).replace(tzinfo=timezone.utc)
        query = query.filter(OrdemDeServicoModel.criada_em >= dt_inicio)
    if data_fim:
        dt_fim = (datetime.fromisoformat(data_fim) + timedelta(days=1)).replace(tzinfo=timezone.utc)
        query = query.filter(OrdemDeServicoModel.criada_em < dt_fim)

    resultados = query.all()

    return RelatorioTempoMedioResponse(
        periodo_inicio=data_inicio,
        periodo_fim=data_fim,
        servicos=[
            TempoMedioServicoResponse(
                servico_id=str(r.servico_id),
                nome=r.nome,
                total_execucoes=r.total,
                tempo_medio_minutos=round(float(r.media_minutos or 0), 1),
            )
            for r in resultados
        ],
    )
