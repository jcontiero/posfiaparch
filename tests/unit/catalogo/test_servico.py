from decimal import Decimal
from uuid import uuid4

import pytest

from src.catalogo.dominio.entidades import Servico
from src.catalogo.dominio.excecoes import ServicoNaoEncontradoError, ServicoEmUsoError


class TestServicoEntidade:
    def test_criar_servico(self):
        s = Servico(
            id=uuid4(),
            nome="Troca de óleo",
            descricao="Troca de óleo do motor",
            preco_base=Decimal("150.00"),
            tempo_estimado_minutos=60,
        )
        assert s.nome == "Troca de óleo"
        assert s.preco_base == Decimal("150.00")
        assert s.tempo_estimado_minutos == 60

    def test_igualdade_por_id(self):
        id_ = uuid4()
        s1 = Servico(id=id_, nome="A", descricao="", preco_base=Decimal("1"), tempo_estimado_minutos=10)
        s2 = Servico(id=id_, nome="B", descricao="", preco_base=Decimal("2"), tempo_estimado_minutos=20)
        assert s1.id == s2.id

    def test_ids_distintos_sao_diferentes(self):
        s1 = Servico(id=uuid4(), nome="A", descricao="", preco_base=Decimal("1"), tempo_estimado_minutos=10)
        s2 = Servico(id=uuid4(), nome="A", descricao="", preco_base=Decimal("1"), tempo_estimado_minutos=10)
        assert s1.id != s2.id


class TestCatalogoExcecoes:
    def test_servico_nao_encontrado_mensagem(self):
        erro = ServicoNaoEncontradoError()
        assert "não encontrado" in str(erro).lower()

    def test_servico_em_uso_mensagem(self):
        erro = ServicoEmUsoError()
        assert "uso" in str(erro).lower()

    def test_servico_nao_encontrado_e_exception(self):
        with pytest.raises(ServicoNaoEncontradoError):
            raise ServicoNaoEncontradoError()

    def test_servico_em_uso_e_exception(self):
        with pytest.raises(ServicoEmUsoError):
            raise ServicoEmUsoError()
