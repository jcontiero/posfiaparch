from src.estoque.dominio.excecoes import (
    EstoqueInsuficienteError,
    PecaNaoEncontradaError,
    CodigoPecaDuplicadoError,
)


class TestExcecoesEstoque:
    def test_estoque_insuficiente_mensagem(self):
        erro = EstoqueInsuficienteError("Pastilha de freio", 10, 3)
        assert "Pastilha de freio" in str(erro)
        assert "10" in str(erro)
        assert "3" in str(erro)

    def test_peca_nao_encontrada(self):
        from uuid import uuid4

        id_ = uuid4()
        erro = PecaNaoEncontradaError(id_)
        assert str(id_) in str(erro)

    def test_codigo_duplicado(self):
        erro = CodigoPecaDuplicadoError("PF-001")
        assert "PF-001" in str(erro)

    def test_todas_sao_exceptions(self):
        assert issubclass(EstoqueInsuficienteError, Exception)
        assert issubclass(PecaNaoEncontradaError, Exception)
        assert issubclass(CodigoPecaDuplicadoError, Exception)
