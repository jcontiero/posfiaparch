from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.shared.dependencias import get_db, get_usuario_atual, require_admin, require_mecanico
from src.atendimento.infraestrutura.repositorios import (
    ClienteRepositorioImpl, VeiculoRepositorioImpl, OrdemDeServicoRepositorioImpl,
)
from src.estoque.infraestrutura.repositorios import PecaRepositorioImpl
from src.estoque.dominio.excecoes import EstoqueInsuficienteError, PecaNaoEncontradaError
from src.catalogo.infraestrutura.repositorios import ServicoRepositorioImpl
from src.catalogo.dominio.excecoes import ServicoNaoEncontradoError
from src.atendimento.aplicacao.casos_de_uso import (
    CadastrarCliente, ListarClientes, BuscarCliente, AtualizarCliente, RemoverCliente,
    CadastrarVeiculo, ListarVeiculos, BuscarVeiculo, AtualizarVeiculo, RemoverVeiculo,
    AbrirOrdemDeServico, ListarOrdensDeServico, BuscarOrdemDeServico,
    IniciarDiagnostico, FinalizarDiagnostico, AdicionarServico, AdicionarPeca, GerarOrcamento,
    AprovarOrcamento, RecusarOrcamento, ExecutarServico, FinalizarOS, EntregarVeiculo,
)
from src.atendimento.dominio.excecoes import (
    ClienteNaoEncontradoError, VeiculoNaoEncontradoError, VeiculoComOsAtivaError,
    ClienteComOsAtivaError, DocumentoDuplicadoError, PlacaDuplicadaError,
    TransicaoInvalidaError, OsSemServicosError, ItemNaoEncontradoError,
)
from src.atendimento.apresentacao.schemas import (
    CadastrarClienteRequest, AtualizarClienteRequest, ClienteResponse,
    CadastrarVeiculoRequest, AtualizarVeiculoRequest, VeiculoResponse,
    AbrirOsRequest, AdicionarServicoRequest, AdicionarPecaRequest,
    RecusarOrcamentoRequest, OsResponse, AcompanharOsResponse, ItensOsResponse,
)
from src.atendimento.dominio.value_objects import StatusOS

DBDep = Annotated[Session, Depends(get_db)]
AuthDep = Annotated[dict, Depends(get_usuario_atual)]
AdminDep = Annotated[dict, Depends(require_admin)]
MecanicoDep = Annotated[dict, Depends(require_mecanico)]

router = APIRouter(tags=["Atendimento"])


def _repos(db: DBDep):
    return (ClienteRepositorioImpl(db), VeiculoRepositorioImpl(db),
            OrdemDeServicoRepositorioImpl(db))


# ── Clientes ──────────────────────────────────────────────────────────────────

@router.post("/clientes", response_model=ClienteResponse, status_code=201)
def cadastrar_cliente(body: CadastrarClienteRequest, db: DBDep, _: AuthDep):
    try:
        cliente = CadastrarCliente(ClienteRepositorioImpl(db)).executar(**body.model_dump())
        return ClienteResponse.from_domain(cliente)
    except (ValueError, DocumentoDuplicadoError) as e:
        raise HTTPException(409 if "cadastrado" in str(e) else 400, str(e))


@router.get("/clientes", response_model=list[ClienteResponse])
def listar_clientes(busca: str | None = None, db: DBDep = None, _: AuthDep = None):
    clientes = ListarClientes(ClienteRepositorioImpl(db)).executar(busca)
    return [ClienteResponse.from_domain(c) for c in clientes]


@router.get("/clientes/{id}", response_model=ClienteResponse)
def buscar_cliente(id: UUID, db: DBDep, _: AuthDep):
    try:
        return ClienteResponse.from_domain(BuscarCliente(ClienteRepositorioImpl(db)).executar(id))
    except ClienteNaoEncontradoError as e:
        raise HTTPException(404, str(e))


@router.put("/clientes/{id}", response_model=ClienteResponse)
def atualizar_cliente(id: UUID, body: AtualizarClienteRequest, db: DBDep, _: AuthDep):
    try:
        cliente = AtualizarCliente(ClienteRepositorioImpl(db)).executar(
            id, **body.model_dump(exclude_none=True))
        return ClienteResponse.from_domain(cliente)
    except ClienteNaoEncontradoError as e:
        raise HTTPException(404, str(e))


@router.delete("/clientes/{id}", status_code=204)
def remover_cliente(id: UUID, db: DBDep, _: AuthDep):
    try:
        RemoverCliente(ClienteRepositorioImpl(db), OrdemDeServicoRepositorioImpl(db)).executar(id)
    except ClienteNaoEncontradoError as e:
        raise HTTPException(404, str(e))
    except ClienteComOsAtivaError as e:
        raise HTTPException(422, str(e))


# ── Veículos ──────────────────────────────────────────────────────────────────

@router.post("/veiculos", response_model=VeiculoResponse, status_code=201)
def cadastrar_veiculo(body: CadastrarVeiculoRequest, db: DBDep, _: AuthDep):
    try:
        veiculo = CadastrarVeiculo(VeiculoRepositorioImpl(db),
                                   ClienteRepositorioImpl(db)).executar(
            cliente_id=UUID(body.cliente_id), placa=body.placa, marca=body.marca,
            modelo=body.modelo, ano=body.ano, cor=body.cor)
        return VeiculoResponse.from_domain(veiculo)
    except ClienteNaoEncontradoError as e:
        raise HTTPException(404, str(e))
    except (PlacaDuplicadaError, ValueError) as e:
        raise HTTPException(409 if "cadastrada" in str(e) else 400, str(e))


@router.get("/veiculos", response_model=list[VeiculoResponse])
def listar_veiculos(cliente_id: UUID | None = None, db: DBDep = None, _: AuthDep = None):
    veiculos = ListarVeiculos(VeiculoRepositorioImpl(db)).executar(cliente_id)
    return [VeiculoResponse.from_domain(v) for v in veiculos]


@router.get("/veiculos/{id}", response_model=VeiculoResponse)
def buscar_veiculo(id: UUID, db: DBDep, _: AuthDep):
    try:
        return VeiculoResponse.from_domain(BuscarVeiculo(VeiculoRepositorioImpl(db)).executar(id))
    except VeiculoNaoEncontradoError as e:
        raise HTTPException(404, str(e))


@router.put("/veiculos/{id}", response_model=VeiculoResponse)
def atualizar_veiculo(id: UUID, body: AtualizarVeiculoRequest, db: DBDep, _: AuthDep):
    try:
        v = AtualizarVeiculo(VeiculoRepositorioImpl(db)).executar(
            id, **body.model_dump(exclude_none=True))
        return VeiculoResponse.from_domain(v)
    except VeiculoNaoEncontradoError as e:
        raise HTTPException(404, str(e))


@router.delete("/veiculos/{id}", status_code=204)
def remover_veiculo(id: UUID, db: DBDep, _: AuthDep):
    try:
        RemoverVeiculo(VeiculoRepositorioImpl(db), OrdemDeServicoRepositorioImpl(db)).executar(id)
    except VeiculoNaoEncontradoError as e:
        raise HTTPException(404, str(e))
    except VeiculoComOsAtivaError as e:
        raise HTTPException(422, str(e))


# ── Ordens de Serviço ─────────────────────────────────────────────────────────

@router.post("/ordens-de-servico", response_model=OsResponse, status_code=201)
def abrir_os(body: AbrirOsRequest, db: DBDep, _: AdminDep):
    try:
        os = AbrirOrdemDeServico(OrdemDeServicoRepositorioImpl(db),
                                 ClienteRepositorioImpl(db),
                                 VeiculoRepositorioImpl(db)).executar(
            body.cliente_cpf_cnpj, body.veiculo_placa, body.descricao_problema)
        return OsResponse.from_domain(os)
    except (ClienteNaoEncontradoError, VeiculoNaoEncontradoError) as e:
        raise HTTPException(404, str(e))
    except (VeiculoComOsAtivaError, ValueError) as e:
        raise HTTPException(422, str(e))


@router.get("/ordens-de-servico", response_model=list[OsResponse])
def listar_os(status: StatusOS | None = None, cliente_id: UUID | None = None,
              db: DBDep = None, _: AuthDep = None):
    ordens = ListarOrdensDeServico(OrdemDeServicoRepositorioImpl(db)).executar(status, cliente_id)
    return [OsResponse.from_domain(o) for o in ordens]


@router.get("/ordens-de-servico/{id}", response_model=OsResponse)
def buscar_os(id: UUID, db: DBDep, _: AuthDep):
    try:
        return OsResponse.from_domain(
            BuscarOrdemDeServico(OrdemDeServicoRepositorioImpl(db)).executar(id))
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/ordens-de-servico/{id}/itens", response_model=ItensOsResponse)
def listar_itens_os(id: UUID, pendentes: bool = False, db: DBDep = None, _: MecanicoDep = None):
    try:
        os = BuscarOrdemDeServico(OrdemDeServicoRepositorioImpl(db)).executar(id)
        return ItensOsResponse.from_domain(os, apenas_pendentes=pendentes)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/ordens-de-servico/{id}/acompanhar", response_model=AcompanharOsResponse)
def acompanhar_os(id: UUID, db: DBDep):
    try:
        os = BuscarOrdemDeServico(OrdemDeServicoRepositorioImpl(db)).executar(id)
        return AcompanharOsResponse.from_domain(os)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/iniciar-diagnostico", response_model=OsResponse)
def iniciar_diagnostico(id: UUID, db: DBDep, _: MecanicoDep):
    try:
        return OsResponse.from_domain(
            IniciarDiagnostico(OrdemDeServicoRepositorioImpl(db)).executar(id))
    except TransicaoInvalidaError as e:
        raise HTTPException(422, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/finalizar-diagnostico", response_model=OsResponse)
def finalizar_diagnostico(id: UUID, db: DBDep, _: MecanicoDep):
    try:
        return OsResponse.from_domain(
            FinalizarDiagnostico(OrdemDeServicoRepositorioImpl(db),
                                 VeiculoRepositorioImpl(db),
                                 ClienteRepositorioImpl(db)).executar(id))
    except TransicaoInvalidaError as e:
        raise HTTPException(422, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/adicionar-servico", response_model=OsResponse)
def adicionar_servico(id: UUID, body: AdicionarServicoRequest, db: DBDep, _: AdminDep):
    try:
        os = AdicionarServico(OrdemDeServicoRepositorioImpl(db),
                              ServicoRepositorioImpl(db)).executar(
            id, UUID(body.servico_id), body.observacao)
        return OsResponse.from_domain(os)
    except ServicoNaoEncontradoError as e:
        raise HTTPException(404, str(e))
    except TransicaoInvalidaError as e:
        raise HTTPException(422, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/adicionar-peca", response_model=OsResponse)
def adicionar_peca(id: UUID, body: AdicionarPecaRequest, db: DBDep, _: AdminDep):
    try:
        os = AdicionarPeca(OrdemDeServicoRepositorioImpl(db), PecaRepositorioImpl(db)).executar(
            id, UUID(body.peca_id), body.quantidade)
        return OsResponse.from_domain(os)
    except TransicaoInvalidaError as e:
        raise HTTPException(422, str(e))
    except EstoqueInsuficienteError as e:
        raise HTTPException(422, str(e))
    except PecaNaoEncontradaError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/gerar-orcamento", response_model=OsResponse)
def gerar_orcamento(id: UUID, db: DBDep, _: AdminDep):
    try:
        return OsResponse.from_domain(
            GerarOrcamento(OrdemDeServicoRepositorioImpl(db),
                           ClienteRepositorioImpl(db),
                           VeiculoRepositorioImpl(db)).executar(id))
    except (TransicaoInvalidaError, OsSemServicosError) as e:
        raise HTTPException(422, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/aprovar-orcamento", response_model=OsResponse)
def aprovar_orcamento(id: UUID, db: DBDep):
    try:
        return OsResponse.from_domain(
            AprovarOrcamento(OrdemDeServicoRepositorioImpl(db),
                             PecaRepositorioImpl(db)).executar(id))
    except EstoqueInsuficienteError as e:
        raise HTTPException(422, str(e))
    except TransicaoInvalidaError as e:
        raise HTTPException(422, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/recusar-orcamento", response_model=OsResponse)
def recusar_orcamento(id: UUID, body: RecusarOrcamentoRequest, db: DBDep):
    try:
        return OsResponse.from_domain(
            RecusarOrcamento(OrdemDeServicoRepositorioImpl(db),
                             ClienteRepositorioImpl(db),
                             VeiculoRepositorioImpl(db)).executar(id, body.motivo))
    except TransicaoInvalidaError as e:
        raise HTTPException(422, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/executar-servico/{item_id}", response_model=OsResponse)
def executar_servico(id: UUID, item_id: UUID, db: DBDep, _: MecanicoDep):
    try:
        return OsResponse.from_domain(
            ExecutarServico(OrdemDeServicoRepositorioImpl(db),
                            VeiculoRepositorioImpl(db)).executar(id, item_id))
    except (TransicaoInvalidaError, ItemNaoEncontradoError) as e:
        raise HTTPException(422, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/finalizar", response_model=OsResponse)
def finalizar_os(id: UUID, db: DBDep, _: AdminDep):
    try:
        return OsResponse.from_domain(
            FinalizarOS(OrdemDeServicoRepositorioImpl(db),
                        ClienteRepositorioImpl(db),
                        VeiculoRepositorioImpl(db)).executar(id))
    except TransicaoInvalidaError as e:
        raise HTTPException(422, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/entregar", response_model=OsResponse)
def entregar_veiculo(id: UUID, db: DBDep, _: AdminDep):
    try:
        return OsResponse.from_domain(
            EntregarVeiculo(OrdemDeServicoRepositorioImpl(db)).executar(id))
    except TransicaoInvalidaError as e:
        raise HTTPException(422, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))
