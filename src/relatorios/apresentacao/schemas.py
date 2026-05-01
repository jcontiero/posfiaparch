from pydantic import BaseModel


class TempoMedioServicoResponse(BaseModel):
    servico_id: str
    nome: str
    total_execucoes: int
    tempo_medio_minutos: float


class RelatorioTempoMedioResponse(BaseModel):
    periodo_inicio: str | None
    periodo_fim: str | None
    servicos: list[TempoMedioServicoResponse]
