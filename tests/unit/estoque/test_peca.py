import pytest
from uuid import uuid4
from decimal import Decimal
from src.estoque.dominio.entidades import Peca
from src.estoque.dominio.excecoes import (
    EstoqueInsuficienteError,
    ReposicaoInvalidaError,
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


class TestReserva:
    def test_reservar_quantidade_disponivel(self):
        peca = _peca(10)
        peca.reservar(4)
        assert peca.quantidade_disponivel == 6

    def test_reservar_toda_a_quantidade(self):
        peca = _peca(5)
        peca.reservar(5)
        assert peca.quantidade_disponivel == 0

    def test_reservar_mais_do_que_disponivel(self):
        peca = _peca(2)
        with pytest.raises(EstoqueInsuficienteError):
            peca.reservar(5)

    def test_mensagem_erro_estoque_insuficiente(self):
        peca = _peca(2)
        with pytest.raises(EstoqueInsuficienteError, match="Pastilha de freio"):
            peca.reservar(5)


class TestReposicao:
    def test_repor_aumenta_quantidade(self):
        peca = _peca(5)
        peca.repor(10)
        assert peca.quantidade_disponivel == 15

    def test_repor_zero_falha(self):
        with pytest.raises(ReposicaoInvalidaError):
            _peca().repor(0)

    def test_repor_negativo_falha(self):
        with pytest.raises(ReposicaoInvalidaError):
            _peca().repor(-1)


class TestLiberacaoReserva:
    def test_liberar_reserva_restaura_estoque(self):
        peca = _peca(10)
        peca.reservar(3)
        peca.liberar_reserva(3)
        assert peca.quantidade_disponivel == 10


class TestAlerta:
    def test_alerta_quando_quantidade_igual_ao_minimo(self):
        assert _peca(qtd=3).alerta_estoque_baixo is True

    def test_alerta_quando_quantidade_abaixo_do_minimo(self):
        assert _peca(qtd=1).alerta_estoque_baixo is True

    def test_sem_alerta_quando_acima_do_minimo(self):
        assert _peca(qtd=10).alerta_estoque_baixo is False
