import pytest
from src.atendimento.dominio.value_objects import CPF, CNPJ, Placa


class TestCPF:
    def test_cpf_valido(self):
        cpf = CPF("529.982.247-25")
        assert cpf.valor == "52998224725"

    def test_cpf_sem_formatacao(self):
        cpf = CPF("52998224725")
        assert cpf.valor == "52998224725"

    def test_cpf_digitos_iguais_invalido(self):
        with pytest.raises(ValueError):
            CPF("111.111.111-11")

    def test_cpf_digito_verificador_invalido(self):
        with pytest.raises(ValueError):
            CPF("123.456.789-00")

    def test_cpf_muito_curto(self):
        with pytest.raises(ValueError):
            CPF("123.456")


class TestCNPJ:
    def test_cnpj_valido(self):
        cnpj = CNPJ("11.222.333/0001-81")
        assert cnpj.valor == "11222333000181"

    def test_cnpj_sem_formatacao(self):
        cnpj = CNPJ("11222333000181")
        assert cnpj.valor == "11222333000181"

    def test_cnpj_digitos_iguais_invalido(self):
        with pytest.raises(ValueError):
            CNPJ("11.111.111/1111-11")

    def test_cnpj_digito_verificador_invalido(self):
        with pytest.raises(ValueError):
            CNPJ("12.345.678/0001-00")


class TestPlaca:
    def test_placa_mercosul_valida(self):
        assert Placa("ABC1D23").valor == "ABC1D23"

    def test_placa_antiga_valida(self):
        assert Placa("ABC1234").valor == "ABC1234"

    def test_placa_lowercase_aceita(self):
        assert Placa("abc1234").valor == "ABC1234"

    def test_placa_formato_invalido(self):
        with pytest.raises(ValueError):
            Placa("ABCD123")

    def test_placa_muito_curta(self):
        with pytest.raises(ValueError):
            Placa("AB123")
