from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.relatorios.aplicacao.ports import ConsultaRelatorios
from src.relatorios.aplicacao.dto import RelatorioTempoMedioDto, TempoMedioServicoDto
from src.atendimento.infraestrutura.modelos import ItemServicoModel, OrdemDeServicoModel
from src.atendimento.dominio.value_objects import StatusOS


class RelatorioConsultaImpl(ConsultaRelatorios):
    def __init__(self, db: Session):
        self.db = db

    def tempo_medio_de_servicos(
        self,
        data_inicio: datetime | None,
        data_fim: datetime | None,
    ) -> RelatorioTempoMedioDto:
        query = (
            self.db.query(
                ItemServicoModel.servico_id,
                ItemServicoModel.descricao.label("nome"),
                func.count(ItemServicoModel.id).label("total"),
                func.avg(
                    func.extract(
                        "epoch",
                        ItemServicoModel.concluido_em - OrdemDeServicoModel.criada_em,
                    )
                    / 60
                ).label("media_minutos"),
            )
            .join(OrdemDeServicoModel, ItemServicoModel.os_id == OrdemDeServicoModel.id)
            .filter(ItemServicoModel.concluido == True)  # noqa: E712
            .filter(
                OrdemDeServicoModel.status.in_([StatusOS.FINALIZADA, StatusOS.ENTREGUE])
            )
            .group_by(ItemServicoModel.servico_id, ItemServicoModel.descricao)
        )

        if data_inicio:
            query = query.filter(OrdemDeServicoModel.criada_em >= data_inicio)
        if data_fim:
            query = query.filter(OrdemDeServicoModel.criada_em < data_fim)

        resultados = query.all()

        return RelatorioTempoMedioDto(
            periodo_inicio=data_inicio.isoformat() if data_inicio else None,
            periodo_fim=data_fim.isoformat() if data_fim else None,
            servicos=[
                TempoMedioServicoDto(
                    servico_id=str(r.servico_id),
                    nome=r.nome,
                    total_execucoes=r.total,
                    tempo_medio_minutos=round(float(r.media_minutos or 0), 1),
                )
                for r in resultados
            ],
        )
