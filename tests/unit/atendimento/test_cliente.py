import pytest
from uuid import uuid4
from src.atendimento.dominio.entidades import Cliente


def test_cliente_com_cpf():
    c = Cliente(id=uuid4(), nome="João", cpf="12345678901",
                cnpj=None, email="j@j.com", telefone="11999")
    assert c.cpf == "12345678901"


def test_cliente_com_cnpj():
    c = Cliente(id=uuid4(), nome="Empresa", cpf=None,
                cnpj="12345678000195", email="e@e.com", telefone="1133")
    assert c.cnpj == "12345678000195"


def test_cliente_sem_documento_falha():
    with pytest.raises(ValueError, match="CPF ou CNPJ"):
        Cliente(id=uuid4(), nome="João", cpf=None,
                cnpj=None, email="j@j.com", telefone="11999")


def test_cliente_com_ambos_documentos_falha():
    with pytest.raises(ValueError, match="CPF ou CNPJ"):
        Cliente(id=uuid4(), nome="João", cpf="12345678901",
                cnpj="12345678000195", email="j@j.com", telefone="11999")
