from decimal import Decimal
from pydantic import BaseModel
from src.atendimento.dominio.entidades import Cliente, Veiculo, OrdemDeServico


class CadastrarClienteRequest(BaseModel):
    nome: str
    email: str
    telefone: str
    cpf: str | None = None
    cnpj: str | None = None


class AtualizarClienteRequest(BaseModel):
    nome: str | None = None
    email: str | None = None
    telefone: str | None = None


class ClienteResponse(BaseModel):
    id: str
    nome: str
    cpf: str | None
    cnpj: str | None
    email: str
    telefone: str

    @classmethod
    def from_domain(cls, c: Cliente) -> "ClienteResponse":
        return cls(id=str(c.id), nome=c.nome,
                   cpf=c.cpf.valor if c.cpf else None,
                   cnpj=c.cnpj.valor if c.cnpj else None,
                   email=c.email, telefone=c.telefone)


class CadastrarVeiculoRequest(BaseModel):
    cliente_id: str
    placa: str
    marca: str
    modelo: str
    ano: int
    cor: str = ""


class AtualizarVeiculoRequest(BaseModel):
    marca: str | None = None
    modelo: str | None = None
    ano: int | None = None
    cor: str | None = None


class VeiculoResponse(BaseModel):
    id: str
    cliente_id: str
    placa: str
    marca: str
    modelo: str
    ano: int
    cor: str

    @classmethod
    def from_domain(cls, v: Veiculo) -> "VeiculoResponse":
        return cls(id=str(v.id), cliente_id=str(v.cliente_id), placa=v.placa.valor,
                   marca=v.marca, modelo=v.modelo, ano=v.ano, cor=v.cor)


class AbrirOsRequest(BaseModel):
    cliente_cpf_cnpj: str
    veiculo_placa: str
    descricao_problema: str


class AdicionarServicoRequest(BaseModel):
    servico_id: str
    observacao: str = ""


class AdicionarPecaRequest(BaseModel):
    peca_id: str
    quantidade: int


class FinalizarDiagnosticoRequest(BaseModel):
    laudo_diagnostico: str | None = None


class RecusarOrcamentoRequest(BaseModel):
    motivo: str = ""


class ItemServicoResponse(BaseModel):
    id: str
    servico_id: str
    descricao: str
    preco_unitario: str
    observacao: str
    concluido: bool
    concluido_em: str | None = None


class ItemPecaResponse(BaseModel):
    id: str
    peca_id: str
    descricao: str
    quantidade: int
    preco_unitario: str
    preco_total: str


class OsResponse(BaseModel):
    id: str
    status: str
    cliente_id: str
    veiculo_id: str
    descricao_problema: str
    laudo_diagnostico: str | None
    valor_orcamento: str | None
    itens_servico: list[ItemServicoResponse]
    itens_peca: list[ItemPecaResponse]
    criada_em: str
    atualizada_em: str

    @classmethod
    def from_domain(cls, os: OrdemDeServico) -> "OsResponse":
        return cls(
            id=str(os.id),
            status=os.status.value,
            cliente_id=str(os.cliente_id),
            veiculo_id=str(os.veiculo_id),
            descricao_problema=os.descricao_problema,
            laudo_diagnostico=os.laudo_diagnostico,
            valor_orcamento=str(os.valor_orcamento) if os.valor_orcamento else None,
            itens_servico=[
                ItemServicoResponse(id=str(i.id), servico_id=str(i.servico_id),
                                    descricao=i.descricao, preco_unitario=str(i.preco_unitario),
                                    observacao=i.observacao, concluido=i.concluido,
                                    concluido_em=i.concluido_em.isoformat() if i.concluido_em else None)
                for i in os.itens_servico
            ],
            itens_peca=[
                ItemPecaResponse(id=str(i.id), peca_id=str(i.peca_id),
                                 descricao=i.descricao, quantidade=i.quantidade,
                                 preco_unitario=str(i.preco_unitario),
                                 preco_total=str(i.preco_total))
                for i in os.itens_peca
            ],
            criada_em=os.criada_em.isoformat(),
            atualizada_em=os.atualizada_em.isoformat(),
        )


class ItensOsResponse(BaseModel):
    os_id: str
    status: str
    total: int
    pendentes: int
    concluidos: int
    itens: list[ItemServicoResponse]

    @classmethod
    def from_domain(cls, os: OrdemDeServico, apenas_pendentes: bool = False) -> "ItensOsResponse":
        itens = [
            ItemServicoResponse(
                id=str(i.id), servico_id=str(i.servico_id),
                descricao=i.descricao, preco_unitario=str(i.preco_unitario),
                observacao=i.observacao, concluido=i.concluido,
                concluido_em=i.concluido_em.isoformat() if i.concluido_em else None,
            )
            for i in os.itens_servico
        ]
        concluidos = sum(1 for i in itens if i.concluido)
        if apenas_pendentes:
            itens = [i for i in itens if not i.concluido]
        return cls(
            os_id=str(os.id),
            status=os.status.value,
            total=len(os.itens_servico),
            pendentes=len(os.itens_servico) - concluidos,
            concluidos=concluidos,
            itens=itens,
        )


class AcompanharOsResponse(BaseModel):
    id: str
    status: str
    descricao_problema: str
    valor_orcamento: str | None
    servicos: list[dict]
    atualizada_em: str

    @classmethod
    def from_domain(cls, os: OrdemDeServico) -> "AcompanharOsResponse":
        return cls(
            id=str(os.id),
            status=os.status.value,
            descricao_problema=os.descricao_problema,
            valor_orcamento=str(os.valor_orcamento) if os.valor_orcamento else None,
            servicos=[{"descricao": i.descricao, "concluido": i.concluido}
                      for i in os.itens_servico],
            atualizada_em=os.atualizada_em.isoformat(),
        )
