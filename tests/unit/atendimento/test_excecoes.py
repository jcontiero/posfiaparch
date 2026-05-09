import pytest

from src.atendimento.dominio.value_objects import StatusOS
from src.atendimento.dominio.excecoes import (
    ServicosNaoConcluidos,
    ClienteNaoEncontradoError,
    VeiculoNaoEncontradoError,
    VeiculoComOsAtivaError,
    ClienteComOsAtivaError,
    DocumentoDuplicadoError,
    PlacaDuplicadaError,
    ItemNaoEncontradoError,
)


class TestExcecoesAtendimento:
    def test_servicos_nao_concluidos(self):
        erro = ServicosNaoConcluidos(3)
        assert "3" in str(erro)

    def test_cliente_nao_encontrado(self):
        erro = ClienteNaoEncontradoError("123.456.789-00")
        assert "123.456.789-00" in str(erro)

    def test_veiculo_nao_encontrado(self):
        erro = VeiculoNaoEncontradoError("ABC1234")
        assert "ABC1234" in str(erro)

    def test_veiculo_com_os_ativa(self):
        erro = VeiculoComOsAtivaError("ABC1234")
        assert "ABC1234" in str(erro)

    def test_cliente_com_os_ativa(self):
        erro = ClienteComOsAtivaError()
        assert "ativas" in str(erro).lower()

    def test_documento_duplicado(self):
        erro = DocumentoDuplicadoError("529.982.247-25")
        assert "529.982.247-25" in str(erro)

    def test_placa_duplicada(self):
        erro = PlacaDuplicadaError("BRA2E19")
        assert "BRA2E19" in str(erro)

    def test_item_nao_encontrado(self):
        from uuid import uuid4
        id_ = uuid4()
        erro = ItemNaoEncontradoError(id_)
        assert str(id_) in str(erro)

    def test_todas_sao_exceptions(self):
        assert issubclass(ServicosNaoConcluidos, Exception)
        assert issubclass(ClienteNaoEncontradoError, Exception)
        assert issubclass(VeiculoNaoEncontradoError, Exception)
        assert issubclass(VeiculoComOsAtivaError, Exception)
        assert issubclass(ClienteComOsAtivaError, Exception)
        assert issubclass(DocumentoDuplicadoError, Exception)
        assert issubclass(PlacaDuplicadaError, Exception)
        assert issubclass(ItemNaoEncontradoError, Exception)
