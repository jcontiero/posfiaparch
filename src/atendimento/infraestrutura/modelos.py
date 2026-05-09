import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy import TypeDecorator
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.shared.banco import Base
from src.atendimento.dominio.value_objects import StatusOS, CPF, CNPJ, Placa


class CPFType(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.valor if isinstance(value, CPF) else value

    def process_result_value(self, value, dialect):
        return CPF(value) if value else None


class CNPJType(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.valor if isinstance(value, CNPJ) else value

    def process_result_value(self, value, dialect):
        return CNPJ(value) if value else None


class PlacaType(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.valor if isinstance(value, Placa) else value

    def process_result_value(self, value, dialect):
        return Placa(value) if value else None


class ClienteModel(Base):
    __tablename__ = "clientes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String, nullable=False)
    cpf = Column(CPFType(11), unique=True, nullable=True, index=True)
    cnpj = Column(CNPJType(14), unique=True, nullable=True, index=True)
    email = Column(String, nullable=False)
    telefone = Column(String, nullable=False)

    veiculos = relationship("VeiculoModel", back_populates="cliente")
    ordens_de_servico = relationship("OrdemDeServicoModel", back_populates="cliente")


class VeiculoModel(Base):
    __tablename__ = "veiculos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    placa = Column(PlacaType(8), unique=True, nullable=False, index=True)
    marca = Column(String, nullable=False)
    modelo = Column(String, nullable=False)
    ano = Column(Integer, nullable=False)
    cor = Column(String, nullable=True)

    cliente = relationship("ClienteModel", back_populates="veiculos")
    ordens_de_servico = relationship("OrdemDeServicoModel", back_populates="veiculo")


class OrdemDeServicoModel(Base):
    __tablename__ = "ordens_de_servico"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    veiculo_id = Column(UUID(as_uuid=True), ForeignKey("veiculos.id"), nullable=False)
    descricao_problema = Column(String, nullable=False)
    laudo_diagnostico = Column(String, nullable=True)
    status = Column(SAEnum(StatusOS, name="status_os", native_enum=False), nullable=False, default=StatusOS.RECEBIDA)
    valor_orcamento = Column(Numeric(10, 2), nullable=True)
    criada_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    atualizada_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    cliente = relationship("ClienteModel", back_populates="ordens_de_servico")
    veiculo = relationship("VeiculoModel", back_populates="ordens_de_servico")
    itens_servico = relationship("ItemServicoModel", back_populates="ordem_de_servico",
                                 cascade="all, delete-orphan")
    itens_peca = relationship("ItemPecaModel", back_populates="ordem_de_servico",
                              cascade="all, delete-orphan")


class ItemServicoModel(Base):
    __tablename__ = "itens_servico"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    os_id = Column(UUID(as_uuid=True), ForeignKey("ordens_de_servico.id"), nullable=False)
    servico_id = Column(UUID(as_uuid=True), nullable=False)
    descricao = Column(String, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    observacao = Column(String, nullable=True, default="")
    concluido = Column(Boolean, default=False)
    concluido_em = Column(DateTime(timezone=True), nullable=True)

    ordem_de_servico = relationship("OrdemDeServicoModel", back_populates="itens_servico")


class ItemPecaModel(Base):
    __tablename__ = "itens_peca"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    os_id = Column(UUID(as_uuid=True), ForeignKey("ordens_de_servico.id"), nullable=False)
    peca_id = Column(UUID(as_uuid=True), nullable=False)
    descricao = Column(String, nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)

    ordem_de_servico = relationship("OrdemDeServicoModel", back_populates="itens_peca")
