from decimal import Decimal
from uuid import uuid4

import pytest

from src.atendimento.aplicacao.casos_de_uso import (
    AbrirOrdemDeServicoUnificada,
    AtualizarStatusViaWebhook,
    ConsultarStatusOrdemDeServico,
    ListarOrdensDeServicoAtivas,
    ProcessarAprovacaoOrcamento,
)
from src.atendimento.dominio.entidades import Cliente, OrdemDeServico, Veiculo
from src.atendimento.dominio.excecoes import (
    OrdemDeServicoNaoEncontradaError,
    TokenDeAprovacaoInvalidoError,
    TransicaoDeStatusInvalidaError,
)
from src.atendimento.dominio.repositorios import (
    ClienteRepositorio,
    VeiculoRepositorio,
    OrdemDeServicoRepositorio,
)
from src.atendimento.dominio.value_objects import (
    CPF,
    Placa,
    StatusOS,
    StatusOSFase2,
)
from src.identidade.aplicacao.ports import ProvedorToken
from src.catalogo.dominio.entidades import Servico
from src.estoque.dominio.entidades import Peca


class RepoFake:
    def __init__(self, entidades=None):
        self._dados = {e.id: e for e in (entidades or [])}

    def _salvar(self, entidade):
        self._dados[entidade.id] = entidade
        return entidade

    def buscar_por_id(self, id):
        return self._dados.get(id)


class ClienteRepoFake(RepoFake, ClienteRepositorio):
    def salvar(self, cliente):
        return self._salvar(cliente)

    def buscar_por_cpf(self, cpf):
        for c in self._dados.values():
            if c.cpf and c.cpf.valor == cpf:
                return c
        return None

    def buscar_por_cnpj(self, cnpj):
        for c in self._dados.values():
            if c.cnpj and c.cnpj.valor == cnpj:
                return c
        return None

    def listar(self, busca=None):
        return list(self._dados.values())

    def remover(self, id):
        self._dados.pop(id, None)


class VeiculoRepoFake(RepoFake, VeiculoRepositorio):
    def __init__(self, entidades=None):
        super().__init__(entidades)
        self._por_placa = {e.placa.valor: e for e in (entidades or [])}

    def salvar(self, veiculo):
        self._por_placa[veiculo.placa.valor] = veiculo
        return self._salvar(veiculo)

    def buscar_por_placa(self, placa):
        return self._por_placa.get(placa)

    def listar(self, cliente_id=None):
        return list(self._dados.values())

    def remover(self, id):
        self._dados.pop(id, None)


class OsRepoFake(RepoFake, OrdemDeServicoRepositorio):
    def salvar(self, os):
        return self._salvar(os)

    def listar(self, status=None, cliente_id=None):
        return list(self._dados.values())

    def buscar_ativa_por_veiculo(self, veiculo_id):
        for os in self._dados.values():
            if os.veiculo_id == veiculo_id and os.status not in (
                StatusOS.FINALIZADA,
                StatusOS.ENTREGUE,
                StatusOS.CANCELADA,
            ):
                return os
        return None

    def existe_os_ativa_por_cliente(self, cliente_id):
        return self.buscar_ativa_por_veiculo(cliente_id) is not None


class ServicoRepoFake(RepoFake):
    pass


class PecaRepoFake(RepoFake):
    pass


class TokenProviderFake(ProvedorToken):
    def __init__(self, valido=True):
        self.valido = valido

    def criar(self, dados, expiracao_horas=None):
        return f"token-{dados['os_id']}"

    def decodificar(self, token):
        if not self.valido:
            raise Exception("token inválido")
        os_id = token.replace("token-", "", 1)
        return {"os_id": os_id}


def _cliente():
    return Cliente(
        id=uuid4(),
        nome="João",
        cpf=CPF("529.982.247-25"),
        cnpj=None,
        email="joao@email.com",
        telefone="11999990000",
    )


def _veiculo(cliente_id=None):
    return Veiculo(
        id=uuid4(),
        cliente_id=cliente_id or uuid4(),
        placa=Placa("ABC1D23"),
        marca="Toyota",
        modelo="Corolla",
        ano=2022,
    )


def _servico():
    return Servico(
        id=uuid4(),
        nome="Troca de óleo",
        descricao="Troca completa",
        preco_base=Decimal("150.00"),
        tempo_estimado_minutos=60,
    )


def _peca():
    return Peca(
        id=uuid4(),
        nome="Filtro",
        codigo="F-001",
        preco_unitario=Decimal("30.00"),
        quantidade_disponivel=10,
        quantidade_minima_alerta=2,
    )


class TestAbrirOrdemDeServicoUnificada:
    def test_cria_cliente_veiculo_os_e_adiciona_itens(self):
        servico = _servico()
        caso = AbrirOrdemDeServicoUnificada(
            OsRepoFake(),
            ClienteRepoFake(),
            VeiculoRepoFake(),
            ServicoRepoFake([servico]),
            PecaRepoFake(),
        )

        os = caso.executar(
            cliente_dados={
                "nome": "João",
                "email": "joao@email.com",
                "telefone": "11999990000",
                "cpf": "529.982.247-25",
            },
            veiculo_dados={
                "placa": "ABC1D23",
                "marca": "Toyota",
                "modelo": "Corolla",
                "ano": 2022,
                "descricao_problema": "Barulho",
            },
            servicos=[{"servico_id": str(servico.id)}],
        )

        assert os.status == StatusOS.AGUARDANDO_APROVACAO
        assert os.valor_orcamento == Decimal("150.00")
        assert len(os.itens_servico) == 1

    def test_reutiliza_cliente_e_veiculo_existentes(self):
        cliente = _cliente()
        veiculo = _veiculo(cliente.id)
        servico = _servico()
        caso = AbrirOrdemDeServicoUnificada(
            OsRepoFake(),
            ClienteRepoFake([cliente]),
            VeiculoRepoFake([veiculo]),
            ServicoRepoFake([servico]),
            PecaRepoFake(),
        )

        os = caso.executar(
            cliente_dados={
                "nome": cliente.nome,
                "email": cliente.email,
                "telefone": cliente.telefone,
                "cpf": "529.982.247-25",
            },
            veiculo_dados={
                "placa": "ABC1D23",
                "marca": veiculo.marca,
                "modelo": veiculo.modelo,
                "ano": veiculo.ano,
                "descricao_problema": "Barulho",
            },
            servicos=[{"servico_id": str(servico.id)}],
        )

        assert os.cliente_id == cliente.id
        assert os.veiculo_id == veiculo.id

    def test_falha_sem_servicos(self):
        caso = AbrirOrdemDeServicoUnificada(
            OsRepoFake(),
            ClienteRepoFake(),
            VeiculoRepoFake(),
            ServicoRepoFake(),
            PecaRepoFake(),
        )
        with pytest.raises(Exception):
            caso.executar(
                cliente_dados={
                    "nome": "João",
                    "email": "joao@email.com",
                    "telefone": "11999990000",
                    "cpf": "529.982.247-25",
                },
                veiculo_dados={
                    "placa": "ABC1D23",
                    "marca": "Toyota",
                    "modelo": "Corolla",
                    "ano": 2022,
                },
                servicos=[],
            )


class TestConsultarStatusOrdemDeServico:
    def test_retorna_status_fase2(self):
        os = OrdemDeServico(
            id=uuid4(), cliente_id=uuid4(), veiculo_id=uuid4(), descricao_problema="X"
        )
        os.iniciar_diagnostico()
        repo = OsRepoFake([os])
        caso = ConsultarStatusOrdemDeServico(repo)

        os_retornada, status = caso.executar(os.id)
        assert os_retornada.id == os.id
        assert status == StatusOSFase2.DIAGNOSTICO.value

    def test_falha_se_os_nao_encontrada(self):
        caso = ConsultarStatusOrdemDeServico(OsRepoFake())
        with pytest.raises(OrdemDeServicoNaoEncontradaError):
            caso.executar(uuid4())


class TestProcessarAprovacaoOrcamento:
    def test_aprovacao_transiciona_para_execucao(self):
        os = OrdemDeServico(
            id=uuid4(), cliente_id=uuid4(), veiculo_id=uuid4(), descricao_problema="X"
        )
        os.iniciar_diagnostico()
        os.adicionar_servico(uuid4(), "Troca de óleo", Decimal("150.00"))
        os.finalizar_diagnostico()
        os.gerar_orcamento()

        caso = ProcessarAprovacaoOrcamento(OsRepoFake([os]))
        resultado = caso.executar(os.id, aprovado=True)
        assert resultado.status == StatusOS.EM_EXECUCAO

    def test_recusa_transiciona_para_diagnostico(self):
        os = OrdemDeServico(
            id=uuid4(), cliente_id=uuid4(), veiculo_id=uuid4(), descricao_problema="X"
        )
        os.iniciar_diagnostico()
        os.adicionar_servico(uuid4(), "Troca de óleo", Decimal("150.00"))
        os.finalizar_diagnostico()
        os.gerar_orcamento()

        caso = ProcessarAprovacaoOrcamento(OsRepoFake([os]))
        resultado = caso.executar(os.id, aprovado=False)
        assert resultado.status == StatusOS.EM_DIAGNOSTICO

    def test_falha_se_os_nao_encontrada(self):
        caso = ProcessarAprovacaoOrcamento(OsRepoFake())
        with pytest.raises(OrdemDeServicoNaoEncontradaError):
            caso.executar(uuid4(), aprovado=True)


class TestListarOrdensDeServicoAtivas:
    def test_ordena_por_prioridade_e_oculta_finalizadas(self):
        os_execucao = OrdemDeServico(
            id=uuid4(), cliente_id=uuid4(), veiculo_id=uuid4(), descricao_problema="E"
        )
        os_execucao.iniciar_diagnostico()
        os_execucao.adicionar_servico(uuid4(), "S", Decimal("10.00"))
        os_execucao.finalizar_diagnostico()
        os_execucao.gerar_orcamento()
        os_execucao.aprovar_orcamento()

        os_recebida = OrdemDeServico(
            id=uuid4(), cliente_id=uuid4(), veiculo_id=uuid4(), descricao_problema="R"
        )

        os_finalizada = OrdemDeServico(
            id=uuid4(), cliente_id=uuid4(), veiculo_id=uuid4(), descricao_problema="F"
        )
        os_finalizada.iniciar_diagnostico()
        item = os_finalizada.adicionar_servico(uuid4(), "S", Decimal("10.00"))
        os_finalizada.finalizar_diagnostico()
        os_finalizada.gerar_orcamento()
        os_finalizada.aprovar_orcamento()
        os_finalizada.executar_servico(item.id)
        os_finalizada.finalizar()

        repo = OsRepoFake([os_recebida, os_execucao, os_finalizada])
        caso = ListarOrdensDeServicoAtivas(repo)
        resultado = caso.executar()

        assert len(resultado) == 2
        assert resultado[0].id == os_execucao.id
        assert resultado[1].id == os_recebida.id


class TestAtualizarStatusViaWebhook:
    def test_atualiza_status_com_token_valido(self):
        os = OrdemDeServico(
            id=uuid4(), cliente_id=uuid4(), veiculo_id=uuid4(), descricao_problema="X"
        )
        os.iniciar_diagnostico()
        os.adicionar_servico(uuid4(), "S", Decimal("10.00"))
        os.finalizar_diagnostico()
        os.gerar_orcamento()

        caso = AtualizarStatusViaWebhook(
            OsRepoFake([os]), TokenProviderFake(valido=True)
        )
        resultado = caso.executar(os.id, f"token-{os.id}", StatusOS.EM_EXECUCAO)
        assert resultado.status == StatusOS.EM_EXECUCAO

    def test_falha_com_token_invalido(self):
        os = OrdemDeServico(
            id=uuid4(), cliente_id=uuid4(), veiculo_id=uuid4(), descricao_problema="X"
        )
        caso = AtualizarStatusViaWebhook(
            OsRepoFake([os]), TokenProviderFake(valido=False)
        )
        with pytest.raises(TokenDeAprovacaoInvalidoError):
            caso.executar(os.id, "token-invalido", StatusOS.EM_EXECUCAO)

    def test_falha_com_token_de_outra_os(self):
        os = OrdemDeServico(
            id=uuid4(), cliente_id=uuid4(), veiculo_id=uuid4(), descricao_problema="X"
        )
        caso = AtualizarStatusViaWebhook(
            OsRepoFake([os]), TokenProviderFake(valido=True)
        )
        with pytest.raises(TokenDeAprovacaoInvalidoError):
            caso.executar(os.id, f"token-{uuid4()}", StatusOS.EM_EXECUCAO)

    def test_falha_se_transicao_invalida(self):
        os = OrdemDeServico(
            id=uuid4(), cliente_id=uuid4(), veiculo_id=uuid4(), descricao_problema="X"
        )
        caso = AtualizarStatusViaWebhook(
            OsRepoFake([os]), TokenProviderFake(valido=True)
        )
        with pytest.raises(TransicaoDeStatusInvalidaError):
            caso.executar(os.id, f"token-{os.id}", StatusOS.ENTREGUE)
