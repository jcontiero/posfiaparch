from datetime import datetime, timezone
from unittest.mock import MagicMock
from src.relatorios.aplicacao.casos_de_uso import GerarRelatorioTempoMedioDeServicos
from src.relatorios.aplicacao.dto import RelatorioTempoMedioDto, TempoMedioServicoDto


def test_gerar_relatorio_sem_filtro():
    consulta = MagicMock()
    consulta.tempo_medio_de_servicos.return_value = RelatorioTempoMedioDto(
        periodo_inicio=None,
        periodo_fim=None,
        servicos=[
            TempoMedioServicoDto(
                servico_id="abc",
                nome="Troca de óleo",
                total_execucoes=5,
                tempo_medio_minutos=30.0,
            )
        ],
    )

    resultado = GerarRelatorioTempoMedioDeServicos(consulta).executar(None, None)

    assert len(resultado.servicos) == 1
    assert resultado.servicos[0].nome == "Troca de óleo"
    consulta.tempo_medio_de_servicos.assert_called_once_with(None, None)


def test_gerar_relatorio_com_periodo():
    consulta = MagicMock()
    consulta.tempo_medio_de_servicos.return_value = RelatorioTempoMedioDto(
        periodo_inicio="2024-01-01T00:00:00+00:00",
        periodo_fim="2024-01-31T00:00:00+00:00",
        servicos=[],
    )

    data_inicio = datetime(2024, 1, 1, tzinfo=timezone.utc)
    data_fim = datetime(2024, 1, 31, tzinfo=timezone.utc)

    resultado = GerarRelatorioTempoMedioDeServicos(consulta).executar(
        data_inicio, data_fim
    )

    assert resultado.servicos == []
    consulta.tempo_medio_de_servicos.assert_called_once_with(data_inicio, data_fim)
