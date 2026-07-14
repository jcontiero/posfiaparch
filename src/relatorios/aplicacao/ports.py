from abc import ABC, abstractmethod
from datetime import datetime

from src.relatorios.aplicacao.dto import RelatorioTempoMedioDto


class ConsultaRelatorios(ABC):
    @abstractmethod
    def tempo_medio_de_servicos(
        self,
        data_inicio: datetime | None,
        data_fim: datetime | None,
    ) -> RelatorioTempoMedioDto: ...
