from typing import Annotated
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from src.shared.dependencias import get_usuario_atual
from src.container import get_gerar_relatorio_tempo_medio
from src.relatorios.aplicacao.casos_de_uso import GerarRelatorioTempoMedioDeServicos
from src.relatorios.apresentacao.schemas import (
    RelatorioTempoMedioResponse,
    TempoMedioServicoResponse,
)

AuthDep = Annotated[dict, Depends(get_usuario_atual)]

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


@router.get("/tempo-medio-servicos", response_model=RelatorioTempoMedioResponse)
def tempo_medio_servicos(
    caso_de_uso: Annotated[
        GerarRelatorioTempoMedioDeServicos, Depends(get_gerar_relatorio_tempo_medio)
    ],
    _: AuthDep,
    data_inicio: str | None = None,
    data_fim: str | None = None,
):
    dt_inicio = None
    dt_fim = None
    if data_inicio:
        dt_inicio = datetime.fromisoformat(data_inicio).replace(tzinfo=timezone.utc)
    if data_fim:
        dt_fim = datetime.fromisoformat(data_fim).replace(tzinfo=timezone.utc)

    resultado = caso_de_uso.executar(dt_inicio, dt_fim)

    return RelatorioTempoMedioResponse(
        periodo_inicio=data_inicio,
        periodo_fim=data_fim,
        servicos=[
            TempoMedioServicoResponse(
                servico_id=s.servico_id,
                nome=s.nome,
                total_execucoes=s.total_execucoes,
                tempo_medio_minutos=s.tempo_medio_minutos,
            )
            for s in resultado.servicos
        ],
    )
