import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from src.estoque.aplicacao.casos_de_uso import (
    CadastrarPeca,
    ListarPecas,
    BuscarPeca,
    AtualizarPeca,
    ReporEstoque,
    ReservarPeca,
    LiberarReserva,
    RemoverPeca,
)
from src.estoque.dominio.entidades import Peca
from src.estoque.dominio.excecoes import (
    PecaNaoEncontradaError,
    CodigoPecaDuplicadoError,
    EstoqueInsuficienteError,
)


def _peca(qtd: int = 10) -> Peca:
    return Peca(
        id=uuid4(),
        nome="Pastilha de freio",
        codigo="PF001",
        preco_unitario=Decimal("85.00"),
        quantidade_disponivel=qtd,
        quantidade_minima_alerta=3,
    )


def _repo_com_peca(peca: Peca):
    repo = MagicMock()
    repo.buscar_por_id.return_value = peca
    repo.salvar.return_value = peca
    return repo


class TestCadastrarPeca:
    def test_cadastrar_nova_peca(self):
        repo = MagicMock()
        repo.buscar_por_codigo.return_value = None
        repo.salvar.return_value = _peca()

        peca = CadastrarPeca(repo).executar(
            nome="Pastilha de freio",
            codigo="PF001",
            preco_unitario=Decimal("85.00"),
            quantidade_disponivel=10,
        )

        assert peca.nome == "Pastilha de freio"
        repo.salvar.assert_called_once()

    def test_cadastrar_peca_com_codigo_duplicado(self):
        repo = MagicMock()
        repo.buscar_por_codigo.return_value = _peca()

        with pytest.raises(CodigoPecaDuplicadoError):
            CadastrarPeca(repo).executar(
                nome="Outra",
                codigo="PF001",
                preco_unitario=Decimal("10.00"),
                quantidade_disponivel=1,
            )


class TestListarPecas:
    def test_listar_todas_as_pecas(self):
        repo = MagicMock()
        repo.listar.return_value = [_peca(), _peca()]

        pecas = ListarPecas(repo).executar()

        assert len(pecas) == 2
        repo.listar.assert_called_once_with(None, False)

    def test_listar_com_busca_e_alerta(self):
        repo = MagicMock()
        repo.listar.return_value = [_peca()]

        pecas = ListarPecas(repo).executar(busca="freio", apenas_alerta=True)

        assert len(pecas) == 1
        repo.listar.assert_called_once_with("freio", True)


class TestBuscarPeca:
    def test_buscar_peca_existente(self):
        peca = _peca()
        repo = _repo_com_peca(peca)

        resultado = BuscarPeca(repo).executar(peca.id)

        assert resultado == peca

    def test_buscar_peca_inexistente(self):
        repo = MagicMock()
        repo.buscar_por_id.return_value = None

        with pytest.raises(PecaNaoEncontradaError):
            BuscarPeca(repo).executar(uuid4())


class TestAtualizarPeca:
    def test_atualizar_nome(self):
        peca = _peca()
        repo = _repo_com_peca(peca)

        resultado = AtualizarPeca(repo).executar(peca.id, nome="Disco de freio")

        assert resultado.nome == "Disco de freio"
        repo.salvar.assert_called_once()

    def test_atualizar_preco(self):
        peca = _peca()
        repo = _repo_com_peca(peca)

        resultado = AtualizarPeca(repo).executar(
            peca.id, preco_unitario=Decimal("120.00")
        )

        assert resultado.preco_unitario == Decimal("120.00")

    def test_atualizar_peca_inexistente(self):
        repo = MagicMock()
        repo.buscar_por_id.return_value = None

        with pytest.raises(PecaNaoEncontradaError):
            AtualizarPeca(repo).executar(uuid4(), nome="X")


class TestReporEstoque:
    def test_repor_estoque_notifica(self):
        peca = _peca(5)
        repo = _repo_com_peca(peca)
        repo.salvar.return_value = Peca(
            id=peca.id,
            nome=peca.nome,
            codigo=peca.codigo,
            preco_unitario=peca.preco_unitario,
            quantidade_disponivel=15,
            quantidade_minima_alerta=peca.quantidade_minima_alerta,
        )
        notificador = MagicMock()

        resultado = ReporEstoque(repo, notificador).executar(peca.id, 10)

        assert resultado.quantidade_disponivel == 15
        notificador.notificar_admin_estoque_reposto.assert_called_once()

    def test_repor_estoque_peca_inexistente(self):
        repo = MagicMock()
        repo.buscar_por_id.return_value = None
        notificador = MagicMock()

        with pytest.raises(PecaNaoEncontradaError):
            ReporEstoque(repo, notificador).executar(uuid4(), 10)


class TestReservarPeca:
    def test_reservar_peca(self):
        peca = _peca(10)
        repo = _repo_com_peca(peca)

        ReservarPeca(repo).executar(peca.id, 3)

        assert peca.quantidade_disponivel == 7
        repo.salvar.assert_called_once()

    def test_reservar_peca_inexistente(self):
        repo = MagicMock()
        repo.buscar_por_id.return_value = None

        with pytest.raises(PecaNaoEncontradaError):
            ReservarPeca(repo).executar(uuid4(), 1)

    def test_reservar_sem_estoque(self):
        peca = _peca(2)
        repo = _repo_com_peca(peca)

        with pytest.raises(EstoqueInsuficienteError):
            ReservarPeca(repo).executar(peca.id, 5)


class TestLiberarReserva:
    def test_liberar_reserva(self):
        peca = _peca(10)
        repo = _repo_com_peca(peca)

        LiberarReserva(repo).executar(peca.id, 3)

        assert peca.quantidade_disponivel == 13
        repo.salvar.assert_called_once()

    def test_liberar_reserva_peca_inexistente(self):
        repo = MagicMock()
        repo.buscar_por_id.return_value = None

        with pytest.raises(PecaNaoEncontradaError):
            LiberarReserva(repo).executar(uuid4(), 1)


class TestRemoverPeca:
    def test_remover_peca(self):
        peca = _peca()
        repo = _repo_com_peca(peca)

        RemoverPeca(repo).executar(peca.id)

        repo.remover.assert_called_once_with(peca.id)

    def test_remover_peca_inexistente(self):
        repo = MagicMock()
        repo.buscar_por_id.return_value = None

        with pytest.raises(PecaNaoEncontradaError):
            RemoverPeca(repo).executar(uuid4())
