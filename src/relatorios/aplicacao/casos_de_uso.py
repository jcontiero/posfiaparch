from datetime import datetime

from src.relatorios.aplicacao.ports import ConsultaRelatorios
from src.relatorios.aplicacao.dto import RelatorioTempoMedioDto


class GerarRelatorioTempoMedioDeServicos:
    def __init__(self, consulta: ConsultaRelatorios):
        self.consulta = consulta

    def executar(
        self,
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> RelatorioTempoMedioDto:
        return self.consulta.tempo_medio_de_servicos(data_inicio, data_fim)
