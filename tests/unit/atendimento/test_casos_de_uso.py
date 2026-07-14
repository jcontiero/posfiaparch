from decimal import Decimal
from uuid import uuid4

import pytest

from src.atendimento.aplicacao.casos_de_uso import (
    AdicionarPeca,
    AdicionarServico,
    AprovarOrcamento,
    AtualizarCliente,
    AtualizarVeiculo,
    BuscarCliente,
    BuscarVeiculo,
    CadastrarCliente,
    CadastrarVeiculo,
    EntregarVeiculo,
    ExecutarServico,
    FinalizarOS,
    FinalizarDiagnostico,
    GerarOrcamento,
    IniciarDiagnostico,
    ListarClientes,
    ListarVeiculos,
    RecusarOrcamento,
    RemoverCliente,
    RemoverVeiculo,
)
from src.atendimento.dominio.entidades import Cliente, OrdemDeServico, Veiculo
from src.atendimento.dominio.excecoes import (
    ClienteNaoEncontradoError,
    DocumentoDuplicadoError,
    OrdemDeServicoNaoEncontradaError,
    PlacaDuplicadaError,
    VeiculoNaoEncontradoError,
    VeiculoComOsAtivaError,
    ClienteComOsAtivaError,
)
from src.atendimento.dominio.repositorios import (
    ClienteRepositorio,
    VeiculoRepositorio,
    OrdemDeServicoRepositorio,
)
from src.atendimento.dominio.value_objects import CPF, Placa, StatusOS
from src.atendimento.aplicacao.ports import Notificador
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

    def listar(self, *args, **kwargs):
        return list(self._dados.values())

    def remover(self, id):
        self._dados.pop(id, None)


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


class VeiculoRepoFake(RepoFake, VeiculoRepositorio):
    def __init__(self, entidades=None):
        super().__init__(entidades)
        self._por_placa = {e.placa.valor: e for e in (entidades or [])}

    def salvar(self, veiculo):
        self._por_placa[veiculo.placa.valor] = veiculo
        return self._salvar(veiculo)

    def buscar_por_placa(self, placa):
        return self._por_placa.get(placa)


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
        for os in self._dados.values():
            if os.cliente_id == cliente_id and os.status not in (
                StatusOS.FINALIZADA,
                StatusOS.ENTREGUE,
                StatusOS.CANCELADA,
            ):
                return True
        return False


class ServicoRepoFake(RepoFake):
    def salvar(self, entidade):
        return self._salvar(entidade)


class PecaRepoFake(RepoFake):
    def salvar(self, entidade):
        return self._salvar(entidade)


class NotificadorFake(Notificador):
    def __init__(self):
        self.chamadas = []

    def notificar_admin_diagnostico_concluido(self, *args, **kwargs):
        self.chamadas.append(("diagnostico_concluido", args, kwargs))

    def notificar_cliente_orcamento_disponivel(self, *args, **kwargs):
        self.chamadas.append(("orcamento_disponivel", args, kwargs))

    def notificar_admin_orcamento_recusado(self, *args, **kwargs):
        self.chamadas.append(("orcamento_recusado", args, kwargs))

    def notificar_admin_servicos_concluidos(self, *args, **kwargs):
        self.chamadas.append(("servicos_concluidos", args, kwargs))

    def notificar_cliente_veiculo_pronto(self, *args, **kwargs):
        self.chamadas.append(("veiculo_pronto", args, kwargs))


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


def _os_com_servico(cliente_id=None, veiculo_id=None):
    os = OrdemDeServico(
        id=uuid4(),
        cliente_id=cliente_id or uuid4(),
        veiculo_id=veiculo_id or uuid4(),
        descricao_problema="X",
    )
    os.iniciar_diagnostico()
    os.adicionar_servico(uuid4(), "Troca de óleo", Decimal("150.00"))
    os.finalizar_diagnostico()
    os.gerar_orcamento()
    return os


class TestClientes:
    def test_cadastrar_cliente(self):
        caso = CadastrarCliente(ClienteRepoFake())
        cliente = caso.executar(
            nome="João",
            email="joao@email.com",
            telefone="11999990000",
            cpf="529.982.247-25",
        )
        assert cliente.nome == "João"
        assert cliente.cpf is not None
        assert cliente.cpf.valor == "52998224725"

    def test_cadastrar_cliente_cnpj(self):
        caso = CadastrarCliente(ClienteRepoFake())
        cliente = caso.executar(
            nome="Empresa",
            email="emp@emp.com",
            telefone="11999990000",
            cnpj="11.222.333/0001-81",
        )
        assert cliente.cnpj is not None
        assert cliente.cnpj.valor == "11222333000181"

    def test_cadastrar_cliente_documento_duplicado(self):
        repo = ClienteRepoFake([_cliente()])
        caso = CadastrarCliente(repo)
        with pytest.raises(DocumentoDuplicadoError):
            caso.executar(
                nome="João 2",
                email="j2@j.com",
                telefone="11999990001",
                cpf="529.982.247-25",
            )

    def test_listar_clientes(self):
        repo = ClienteRepoFake([_cliente()])
        caso = ListarClientes(repo)
        assert len(caso.executar()) == 1

    def test_buscar_cliente(self):
        cliente = _cliente()
        caso = BuscarCliente(ClienteRepoFake([cliente]))
        assert caso.executar(cliente.id).id == cliente.id

    def test_buscar_cliente_nao_encontrado(self):
        with pytest.raises(ClienteNaoEncontradoError):
            BuscarCliente(ClienteRepoFake()).executar(uuid4())

    def test_atualizar_cliente(self):
        cliente = _cliente()
        caso = AtualizarCliente(ClienteRepoFake([cliente]))
        atualizado = caso.executar(cliente.id, nome="João Silva")
        assert atualizado.nome == "João Silva"

    def test_atualizar_cliente_nao_encontrado(self):
        with pytest.raises(ClienteNaoEncontradoError):
            AtualizarCliente(ClienteRepoFake()).executar(uuid4(), nome="X")

    def test_remover_cliente_com_os_ativa(self):
        cliente = _cliente()
        os = OrdemDeServico(
            id=uuid4(),
            cliente_id=cliente.id,
            veiculo_id=uuid4(),
            descricao_problema="X",
        )
        with pytest.raises(ClienteComOsAtivaError):
            RemoverCliente(ClienteRepoFake([cliente]), OsRepoFake([os])).executar(
                cliente.id
            )


class TestVeiculos:
    def test_cadastrar_veiculo(self):
        cliente = _cliente()
        caso = CadastrarVeiculo(VeiculoRepoFake(), ClienteRepoFake([cliente]))
        veiculo = caso.executar(
            cliente_id=cliente.id,
            placa="ABC1D23",
            marca="Toyota",
            modelo="Corolla",
            ano=2022,
        )
        assert veiculo.placa.valor == "ABC1D23"

    def test_cadastrar_veiculo_cliente_nao_encontrado(self):
        caso = CadastrarVeiculo(VeiculoRepoFake(), ClienteRepoFake())
        with pytest.raises(ClienteNaoEncontradoError):
            caso.executar(uuid4(), "ABC1D23", "Toyota", "Corolla", 2022)

    def test_cadastrar_veiculo_placa_duplicada(self):
        cliente = _cliente()
        veiculo = _veiculo(cliente.id)
        caso = CadastrarVeiculo(VeiculoRepoFake([veiculo]), ClienteRepoFake([cliente]))
        with pytest.raises(PlacaDuplicadaError):
            caso.executar(cliente.id, "ABC1D23", "Honda", "Civic", 2021)

    def test_listar_veiculos(self):
        caso = ListarVeiculos(VeiculoRepoFake([_veiculo()]))
        assert len(caso.executar()) == 1

    def test_buscar_veiculo(self):
        veiculo = _veiculo()
        caso = BuscarVeiculo(VeiculoRepoFake([veiculo]))
        assert caso.executar(veiculo.id).id == veiculo.id

    def test_buscar_veiculo_nao_encontrado(self):
        with pytest.raises(VeiculoNaoEncontradoError):
            BuscarVeiculo(VeiculoRepoFake()).executar(uuid4())

    def test_atualizar_veiculo(self):
        veiculo = _veiculo()
        caso = AtualizarVeiculo(VeiculoRepoFake([veiculo]))
        atualizado = caso.executar(veiculo.id, cor="Prata")
        assert atualizado.cor == "Prata"

    def test_remover_veiculo_com_os_ativa(self):
        veiculo = _veiculo()
        os = OrdemDeServico(
            id=uuid4(),
            cliente_id=uuid4(),
            veiculo_id=veiculo.id,
            descricao_problema="X",
        )
        with pytest.raises(VeiculoComOsAtivaError):
            RemoverVeiculo(VeiculoRepoFake([veiculo]), OsRepoFake([os])).executar(
                veiculo.id
            )


class TestOrdensDeServico:
    def test_iniciar_diagnostico(self):
        os = OrdemDeServico(
            id=uuid4(), cliente_id=uuid4(), veiculo_id=uuid4(), descricao_problema="X"
        )
        caso = IniciarDiagnostico(OsRepoFake([os]))
        resultado = caso.executar(os.id)
        assert resultado.status == StatusOS.EM_DIAGNOSTICO

    def test_iniciar_diagnostico_os_nao_encontrada(self):
        with pytest.raises(OrdemDeServicoNaoEncontradaError):
            IniciarDiagnostico(OsRepoFake()).executar(uuid4())

    def test_finalizar_diagnostico(self):
        os = OrdemDeServico(
            id=uuid4(), cliente_id=uuid4(), veiculo_id=uuid4(), descricao_problema="X"
        )
        os.iniciar_diagnostico()
        cliente = _cliente()
        veiculo = _veiculo()
        notificador = NotificadorFake()
        caso = FinalizarDiagnostico(
            OsRepoFake([os]),
            VeiculoRepoFake([veiculo]),
            ClienteRepoFake([cliente]),
            notificador,
        )
        resultado = caso.executar(os.id, "Laudo")
        assert resultado.status == StatusOS.AGUARDANDO_ORCAMENTO
        assert resultado.laudo_diagnostico == "Laudo"
        assert len(notificador.chamadas) == 1

    def test_adicionar_servico(self):
        os = OrdemDeServico(
            id=uuid4(), cliente_id=uuid4(), veiculo_id=uuid4(), descricao_problema="X"
        )
        os.iniciar_diagnostico()
        servico = _servico()
        caso = AdicionarServico(OsRepoFake([os]), ServicoRepoFake([servico]))
        resultado = caso.executar(os.id, servico.id)
        assert len(resultado.itens_servico) == 1

    def test_adicionar_peca(self):
        os = OrdemDeServico(
            id=uuid4(), cliente_id=uuid4(), veiculo_id=uuid4(), descricao_problema="X"
        )
        os.iniciar_diagnostico()
        peca = _peca()
        caso = AdicionarPeca(OsRepoFake([os]), PecaRepoFake([peca]))
        resultado = caso.executar(os.id, peca.id, 3)
        assert len(resultado.itens_peca) == 1

    def test_gerar_orcamento(self):
        cliente = _cliente()
        veiculo = _veiculo(cliente.id)
        os = OrdemDeServico(
            id=uuid4(),
            cliente_id=cliente.id,
            veiculo_id=veiculo.id,
            descricao_problema="X",
        )
        os.iniciar_diagnostico()
        os.adicionar_servico(uuid4(), "S", Decimal("100.00"))
        os.adicionar_peca(uuid4(), "P", 2, Decimal("25.00"))
        os.finalizar_diagnostico()
        notificador = NotificadorFake()
        caso = GerarOrcamento(
            OsRepoFake([os]),
            ClienteRepoFake([cliente]),
            VeiculoRepoFake([veiculo]),
            notificador,
        )
        resultado = caso.executar(os.id)
        assert resultado.status == StatusOS.AGUARDANDO_APROVACAO
        assert resultado.valor_orcamento == Decimal("150.00")
        assert len(notificador.chamadas) == 1

    def test_aprovar_orcamento(self):
        os = _os_com_servico()
        caso = AprovarOrcamento(OsRepoFake([os]))
        resultado = caso.executar(os.id)
        assert resultado.status == StatusOS.EM_EXECUCAO

    def test_aprovar_orcamento_reserva_pecas(self):
        os = OrdemDeServico(
            id=uuid4(), cliente_id=uuid4(), veiculo_id=uuid4(), descricao_problema="X"
        )
        os.iniciar_diagnostico()
        peca = _peca()
        os.adicionar_servico(uuid4(), "S", Decimal("50.00"))
        os.adicionar_peca(peca.id, peca.nome, 3, peca.preco_unitario)
        os.finalizar_diagnostico()
        os.gerar_orcamento()
        peca_repo = PecaRepoFake([peca])
        caso = AprovarOrcamento(OsRepoFake([os]), peca_repo)
        caso.executar(os.id)
        assert peca.quantidade_disponivel == 7

    def test_recusar_orcamento(self):
        cliente = _cliente()
        veiculo = _veiculo(cliente.id)
        os = _os_com_servico(cliente.id, veiculo.id)
        notificador = NotificadorFake()
        caso = RecusarOrcamento(
            OsRepoFake([os]),
            ClienteRepoFake([cliente]),
            VeiculoRepoFake([veiculo]),
            notificador,
        )
        resultado = caso.executar(os.id, "Valor alto")
        assert resultado.status == StatusOS.EM_DIAGNOSTICO
        assert len(notificador.chamadas) == 1

    def test_executar_servico(self):
        os = _os_com_servico()
        os.aprovar_orcamento()
        item_id = os.itens_servico[0].id
        notificador = NotificadorFake()
        caso = ExecutarServico(
            OsRepoFake([os]), VeiculoRepoFake([_veiculo()]), notificador
        )
        resultado = caso.executar(os.id, item_id)
        assert resultado.status == StatusOS.SERVICOS_CONCLUIDOS

    def test_finalizar_os(self):
        cliente = _cliente()
        veiculo = _veiculo(cliente.id)
        os = _os_com_servico(cliente.id, veiculo.id)
        os.aprovar_orcamento()
        os.executar_servico(os.itens_servico[0].id)
        notificador = NotificadorFake()
        caso = FinalizarOS(
            OsRepoFake([os]),
            ClienteRepoFake([cliente]),
            VeiculoRepoFake([veiculo]),
            notificador,
        )
        resultado = caso.executar(os.id)
        assert resultado.status == StatusOS.FINALIZADA
        assert len(notificador.chamadas) == 1

    def test_entregar_veiculo(self):
        os = _os_com_servico()
        os.aprovar_orcamento()
        os.executar_servico(os.itens_servico[0].id)
        os.finalizar()
        caso = EntregarVeiculo(OsRepoFake([os]))
        resultado = caso.executar(os.id)
        assert resultado.status == StatusOS.ENTREGUE
