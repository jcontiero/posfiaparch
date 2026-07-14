from dataclasses import dataclass


@dataclass
class TempoMedioServicoDto:
    servico_id: str
    nome: str
    total_execucoes: int
    tempo_medio_minutos: float


@dataclass
class RelatorioTempoMedioDto:
    periodo_inicio: str | None
    periodo_fim: str | None
    servicos: list[TempoMedioServicoDto]
