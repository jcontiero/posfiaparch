import pytest
from uuid import uuid4
from decimal import Decimal
from src.atendimento.dominio.entidades import OrdemDeServico
from src.atendimento.dominio.value_objects import StatusOS
from src.atendimento.dominio.excecoes import (
    TransicaoInvalidaError, OsSemServicosError, ItemNaoEncontradoError,
)


def _os() -> OrdemDeServico:
    return OrdemDeServico(
        id=uuid4(), cliente_id=uuid4(), veiculo_id=uuid4(),
        descricao_problema="Barulho no motor",
    )


def _os_pronta_para_orcamento() -> tuple[OrdemDeServico, object]:
    """OS em AGUARDANDO_ORCAMENTO com um serviço adicionado."""
    os = _os()
    os.iniciar_diagnostico()
    item = os.adicionar_servico(uuid4(), "Troca de óleo", Decimal("150.00"))
    os.finalizar_diagnostico()
    return os, item


class TestTransicoesDeStatus:
    def test_status_inicial_e_recebida(self):
        assert _os().status == StatusOS.RECEBIDA

    def test_iniciar_diagnostico(self):
        os = _os()
        os.iniciar_diagnostico()
        assert os.status == StatusOS.EM_DIAGNOSTICO

    def test_finalizar_diagnostico(self):
        os = _os()
        os.iniciar_diagnostico()
        os.finalizar_diagnostico()
        assert os.status == StatusOS.AGUARDANDO_ORCAMENTO

    def test_transicao_invalida_pula_etapa(self):
        os = _os()
        with pytest.raises(TransicaoInvalidaError):
            os.aprovar_orcamento()

    def test_transicao_retroativa_invalida(self):
        os = _os()
        os.iniciar_diagnostico()
        with pytest.raises(TransicaoInvalidaError):
            os.iniciar_diagnostico()

    def test_cancelar_apos_orcamento(self):
        os, _ = _os_pronta_para_orcamento()
        os.gerar_orcamento()
        os.recusar_orcamento()
        assert os.status == StatusOS.CANCELADA

    def test_entregar_apos_finalizada(self):
        os, item = _os_pronta_para_orcamento()
        os.gerar_orcamento()
        os.aprovar_orcamento()
        os.executar_servico(item.id)
        os.finalizar()
        os.entregar()
        assert os.status == StatusOS.ENTREGUE


class TestOrcamento:
    def test_gerar_sem_servicos_falha(self):
        os = _os()
        os.iniciar_diagnostico()
        os.finalizar_diagnostico()
        with pytest.raises(OsSemServicosError):
            os.gerar_orcamento()

    def test_valor_orcamento_soma_servicos_e_pecas(self):
        os = _os()
        os.iniciar_diagnostico()
        os.adicionar_servico(uuid4(), "Troca de óleo", Decimal("150.00"))
        os.adicionar_peca(uuid4(), "Filtro", 2, Decimal("30.00"))
        os.finalizar_diagnostico()
        os.gerar_orcamento()
        assert os.valor_orcamento == Decimal("210.00")

    def test_nao_adiciona_servico_apos_orcamento(self):
        os, _ = _os_pronta_para_orcamento()
        os.gerar_orcamento()
        with pytest.raises(TransicaoInvalidaError):
            os.adicionar_servico(uuid4(), "Alinhamento", Decimal("80.00"))


class TestExecucao:
    def test_transiciona_para_servicos_concluidos_quando_todos_done(self):
        os, item = _os_pronta_para_orcamento()
        os.gerar_orcamento()
        os.aprovar_orcamento()
        concluiu_tudo = os.executar_servico(item.id)
        assert concluiu_tudo is True
        assert os.status == StatusOS.SERVICOS_CONCLUIDOS

    def test_finalizar_apos_servicos_concluidos(self):
        os, item = _os_pronta_para_orcamento()
        os.gerar_orcamento()
        os.aprovar_orcamento()
        os.executar_servico(item.id)
        os.finalizar()
        assert os.status == StatusOS.FINALIZADA

    def test_nao_finaliza_com_servicos_pendentes(self):
        os = _os()
        os.iniciar_diagnostico()
        item1 = os.adicionar_servico(uuid4(), "Troca de óleo", Decimal("150.00"))
        os.adicionar_servico(uuid4(), "Alinhamento", Decimal("80.00"))
        os.finalizar_diagnostico()
        os.gerar_orcamento()
        os.aprovar_orcamento()
        concluiu_tudo = os.executar_servico(item1.id)
        assert concluiu_tudo is False
        assert os.status == StatusOS.EM_EXECUCAO

    def test_executar_item_inexistente(self):
        os, _ = _os_pronta_para_orcamento()
        os.gerar_orcamento()
        os.aprovar_orcamento()
        with pytest.raises(ItemNaoEncontradoError):
            os.executar_servico(uuid4())
