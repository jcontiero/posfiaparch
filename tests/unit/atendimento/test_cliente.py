import pytest
from uuid import uuid4
from src.atendimento.dominio.entidades import Cliente
from src.atendimento.dominio.excecoes import DocumentoClienteInvalidoError
from src.atendimento.dominio.value_objects import CPF, CNPJ


def test_cliente_com_cpf():
    cpf = CPF("529.982.247-25")
    c = Cliente(
        id=uuid4(), nome="João", cpf=cpf, cnpj=None, email="j@j.com", telefone="11999"
    )
    assert c.cpf is not None
    assert c.cpf.valor == "52998224725"


def test_cliente_com_cnpj():
    cnpj = CNPJ("11.222.333/0001-81")
    c = Cliente(
        id=uuid4(),
        nome="Empresa",
        cpf=None,
        cnpj=cnpj,
        email="e@e.com",
        telefone="1133",
    )
    assert c.cnpj is not None
    assert c.cnpj.valor == "11222333000181"


def test_cliente_sem_documento_falha():
    with pytest.raises(DocumentoClienteInvalidoError):
        Cliente(
            id=uuid4(),
            nome="João",
            cpf=None,
            cnpj=None,
            email="j@j.com",
            telefone="11999",
        )


def test_cliente_com_ambos_documentos_falha():
    with pytest.raises(DocumentoClienteInvalidoError):
        Cliente(
            id=uuid4(),
            nome="João",
            cpf=CPF("529.982.247-25"),
            cnpj=CNPJ("11.222.333/0001-81"),
            email="j@j.com",
            telefone="11999",
        )
