from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from src.shared.dependencias import get_usuario_atual, require_admin, require_mecanico
from src.container import (
    get_cadastrar_cliente,
    get_listar_clientes,
    get_buscar_cliente,
    get_atualizar_cliente,
    get_remover_cliente,
    get_cadastrar_veiculo,
    get_listar_veiculos,
    get_buscar_veiculo,
    get_atualizar_veiculo,
    get_remover_veiculo,
    get_buscar_ordem_de_servico,
    get_iniciar_diagnostico,
    get_finalizar_diagnostico,
    get_adicionar_servico,
    get_adicionar_peca,
    get_gerar_orcamento,
    get_aprovar_orcamento,
    get_recusar_orcamento,
    get_executar_servico,
    get_finalizar_os,
    get_entregar_veiculo,
    get_abrir_ordem_de_servico_unificada,
    get_consultar_status_ordem_de_servico,
    get_processar_aprovacao_orcamento,
    get_listar_ordens_de_servico_ativas,
    get_atualizar_status_via_webhook,
)
from src.estoque.dominio.excecoes import (
    EstoqueInsuficienteError,
    PecaNaoEncontradaError,
)
from src.catalogo.dominio.excecoes import ServicoNaoEncontradoError
from src.atendimento.aplicacao.casos_de_uso import (
    CadastrarCliente,
    ListarClientes,
    BuscarCliente,
    AtualizarCliente,
    RemoverCliente,
    CadastrarVeiculo,
    ListarVeiculos,
    BuscarVeiculo,
    AtualizarVeiculo,
    RemoverVeiculo,
    BuscarOrdemDeServico,
    IniciarDiagnostico,
    FinalizarDiagnostico,
    AdicionarServico,
    AdicionarPeca,
    GerarOrcamento,
    AprovarOrcamento,
    RecusarOrcamento,
    ExecutarServico,
    FinalizarOS,
    EntregarVeiculo,
    AbrirOrdemDeServicoUnificada,
    ConsultarStatusOrdemDeServico,
    ProcessarAprovacaoOrcamento,
    ListarOrdensDeServicoAtivas,
    AtualizarStatusViaWebhook,
)
from src.atendimento.dominio.excecoes import (
    ClienteNaoEncontradoError,
    VeiculoNaoEncontradoError,
    VeiculoComOsAtivaError,
    ClienteComOsAtivaError,
    DocumentoDuplicadoError,
    PlacaDuplicadaError,
    TransicaoInvalidaError,
    TransicaoDeStatusInvalidaError,
    OsSemServicosError,
    ItemNaoEncontradoError,
    OrdemDeServicoNaoEncontradaError,
    TokenDeAprovacaoInvalidoError,
    TokenDeAprovacaoExpiradoError,
)
from src.atendimento.apresentacao.schemas import (
    CadastrarClienteRequest,
    AtualizarClienteRequest,
    ClienteResponse,
    CadastrarVeiculoRequest,
    AtualizarVeiculoRequest,
    VeiculoResponse,
    AbrirOsRequest,
    FinalizarDiagnosticoRequest,
    AdicionarServicoRequest,
    AdicionarPecaRequest,
    RecusarOrcamentoRequest,
    OsResponse,
    AcompanharOsResponse,
    ItensOsResponse,
    StatusOsResponse,
    AprovacaoOrcamentoRequest,
    ListarOsFase2Response,
    WebhookAtualizarStatusRequest,
)
from src.atendimento.dominio.value_objects import (
    para_status_interno,
)

AuthDep = Annotated[dict, Depends(get_usuario_atual)]
AdminDep = Annotated[dict, Depends(require_admin)]
MecanicoDep = Annotated[dict, Depends(require_mecanico)]

router = APIRouter(tags=["Atendimento"])


# -- Clientes ------------------------------------------------------------------


@router.post("/clientes", response_model=ClienteResponse, status_code=201)
def cadastrar_cliente(
    body: CadastrarClienteRequest,
    caso_de_uso: Annotated[CadastrarCliente, Depends(get_cadastrar_cliente)],
    _: MecanicoDep,
):
    try:
        cliente = caso_de_uso.executar(**body.model_dump())
        return ClienteResponse.from_domain(cliente)
    except (ValueError, DocumentoDuplicadoError) as e:
        raise HTTPException(409 if "cadastrado" in str(e) else 400, str(e))


@router.get("/clientes", response_model=list[ClienteResponse])
def listar_clientes(
    caso_de_uso: Annotated[ListarClientes, Depends(get_listar_clientes)],
    _: MecanicoDep,
    busca: str | None = None,
):
    clientes = caso_de_uso.executar(busca)
    return [ClienteResponse.from_domain(c) for c in clientes]


@router.get("/clientes/{id}", response_model=ClienteResponse)
def buscar_cliente(
    id: UUID,
    caso_de_uso: Annotated[BuscarCliente, Depends(get_buscar_cliente)],
    _: MecanicoDep,
):
    try:
        return ClienteResponse.from_domain(caso_de_uso.executar(id))
    except ClienteNaoEncontradoError as e:
        raise HTTPException(404, str(e))


@router.put("/clientes/{id}", response_model=ClienteResponse)
def atualizar_cliente(
    id: UUID,
    body: AtualizarClienteRequest,
    caso_de_uso: Annotated[AtualizarCliente, Depends(get_atualizar_cliente)],
    _: MecanicoDep,
):
    try:
        cliente = caso_de_uso.executar(id=id, **body.model_dump(exclude_none=True))
        return ClienteResponse.from_domain(cliente)
    except ClienteNaoEncontradoError as e:
        raise HTTPException(404, str(e))


@router.delete("/clientes/{id}", status_code=204)
def remover_cliente(
    id: UUID,
    caso_de_uso: Annotated[RemoverCliente, Depends(get_remover_cliente)],
    _: AdminDep,
):
    try:
        caso_de_uso.executar(id)
    except ClienteNaoEncontradoError as e:
        raise HTTPException(404, str(e))
    except ClienteComOsAtivaError as e:
        raise HTTPException(422, str(e))


# -- Veículos ------------------------------------------------------------------


@router.post("/veiculos", response_model=VeiculoResponse, status_code=201)
def cadastrar_veiculo(
    body: CadastrarVeiculoRequest,
    caso_de_uso: Annotated[CadastrarVeiculo, Depends(get_cadastrar_veiculo)],
    _: MecanicoDep,
):
    try:
        veiculo = caso_de_uso.executar(
            cliente_id=UUID(body.cliente_id),
            placa=body.placa,
            marca=body.marca,
            modelo=body.modelo,
            ano=body.ano,
            cor=body.cor,
        )
        return VeiculoResponse.from_domain(veiculo)
    except ClienteNaoEncontradoError as e:
        raise HTTPException(404, str(e))
    except (PlacaDuplicadaError, ValueError) as e:
        raise HTTPException(409 if "cadastrada" in str(e) else 400, str(e))


@router.get("/veiculos", response_model=list[VeiculoResponse])
def listar_veiculos(
    caso_de_uso: Annotated[ListarVeiculos, Depends(get_listar_veiculos)],
    _: MecanicoDep,
    cliente_id: UUID | None = None,
):
    veiculos = caso_de_uso.executar(cliente_id)
    return [VeiculoResponse.from_domain(v) for v in veiculos]


@router.get("/veiculos/{id}", response_model=VeiculoResponse)
def buscar_veiculo(
    id: UUID,
    caso_de_uso: Annotated[BuscarVeiculo, Depends(get_buscar_veiculo)],
    _: MecanicoDep,
):
    try:
        return VeiculoResponse.from_domain(caso_de_uso.executar(id))
    except VeiculoNaoEncontradoError as e:
        raise HTTPException(404, str(e))


@router.put("/veiculos/{id}", response_model=VeiculoResponse)
def atualizar_veiculo(
    id: UUID,
    body: AtualizarVeiculoRequest,
    caso_de_uso: Annotated[AtualizarVeiculo, Depends(get_atualizar_veiculo)],
    _: MecanicoDep,
):
    try:
        v = caso_de_uso.executar(id=id, **body.model_dump(exclude_none=True))
        return VeiculoResponse.from_domain(v)
    except VeiculoNaoEncontradoError as e:
        raise HTTPException(404, str(e))


@router.delete("/veiculos/{id}", status_code=204)
def remover_veiculo(
    id: UUID,
    caso_de_uso: Annotated[RemoverVeiculo, Depends(get_remover_veiculo)],
    _: AdminDep,
):
    try:
        caso_de_uso.executar(id)
    except VeiculoNaoEncontradoError as e:
        raise HTTPException(404, str(e))
    except VeiculoComOsAtivaError as e:
        raise HTTPException(422, str(e))


# -- Ordens de Serviço ---------------------------------------------------------


@router.post("/ordens-de-servico", response_model=OsResponse, status_code=201)
def abrir_os_unificado(
    body: AbrirOsRequest,
    caso_de_uso: Annotated[
        AbrirOrdemDeServicoUnificada, Depends(get_abrir_ordem_de_servico_unificada)
    ],
    _: AdminDep,
):
    try:
        os = caso_de_uso.executar(
            cliente_dados=body.cliente.model_dump(),
            veiculo_dados=body.veiculo.model_dump(),
            servicos=[s.model_dump() for s in body.servicos],
            pecas=[p.model_dump() for p in body.pecas],
        )
        return OsResponse.from_domain(os)
    except (ClienteNaoEncontradoError, VeiculoNaoEncontradoError) as e:
        raise HTTPException(404, str(e))
    except (
        VeiculoComOsAtivaError,
        OsSemServicosError,
        ValueError,
    ) as e:
        raise HTTPException(422, str(e))


@router.get("/ordens-de-servico", response_model=list[ListarOsFase2Response])
def listar_os_fase2(
    caso_de_uso: Annotated[
        ListarOrdensDeServicoAtivas, Depends(get_listar_ordens_de_servico_ativas)
    ],
    _: AuthDep,
):
    ordens = caso_de_uso.executar()
    return [ListarOsFase2Response.from_domain(o) for o in ordens]


@router.get("/ordens-de-servico/{id}", response_model=OsResponse)
def buscar_os(
    id: UUID,
    caso_de_uso: Annotated[BuscarOrdemDeServico, Depends(get_buscar_ordem_de_servico)],
    _: AuthDep,
):
    try:
        return OsResponse.from_domain(caso_de_uso.executar(id))
    except OrdemDeServicoNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.get("/ordens-de-servico/{id}/status", response_model=StatusOsResponse)
def consultar_status_os(
    id: UUID,
    caso_de_uso: Annotated[
        ConsultarStatusOrdemDeServico, Depends(get_consultar_status_ordem_de_servico)
    ],
):
    try:
        os, status = caso_de_uso.executar(id)
        return StatusOsResponse(id=str(os.id), status=status)
    except OrdemDeServicoNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/aprovacao", response_model=OsResponse)
def aprovar_os_fase2(
    id: UUID,
    body: AprovacaoOrcamentoRequest,
    caso_de_uso: Annotated[
        ProcessarAprovacaoOrcamento, Depends(get_processar_aprovacao_orcamento)
    ],
):
    try:
        os = caso_de_uso.executar(id, body.aprovado, body.motivo)
        return OsResponse.from_domain(os)
    except (
        TransicaoInvalidaError,
        TransicaoDeStatusInvalidaError,
        OsSemServicosError,
    ) as e:
        raise HTTPException(422, str(e))
    except OrdemDeServicoNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.post("/webhooks/os/{id}/atualizar-status", response_model=OsResponse)
def atualizar_status_via_webhook(
    id: UUID,
    body: WebhookAtualizarStatusRequest,
    caso_de_uso: Annotated[
        AtualizarStatusViaWebhook, Depends(get_atualizar_status_via_webhook)
    ],
):
    try:
        novo_status = para_status_interno(body.status)
        os = caso_de_uso.executar(id, body.token, novo_status)
        return OsResponse.from_domain(os)
    except (KeyError, ValueError):
        raise HTTPException(400, f"Status inválido: {body.status}")
    except (
        TransicaoInvalidaError,
        TransicaoDeStatusInvalidaError,
    ) as e:
        raise HTTPException(422, str(e))
    except (
        TokenDeAprovacaoInvalidoError,
        TokenDeAprovacaoExpiradoError,
    ) as e:
        raise HTTPException(401, str(e))
    except OrdemDeServicoNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.get("/ordens-de-servico/{id}/itens", response_model=ItensOsResponse)
def listar_itens_os(
    id: UUID,
    caso_buscar: Annotated[BuscarOrdemDeServico, Depends(get_buscar_ordem_de_servico)],
    _: MecanicoDep,
    pendentes: bool = False,
):
    try:
        os = caso_buscar.executar(id)
        return ItensOsResponse.from_domain(os, apenas_pendentes=pendentes)
    except OrdemDeServicoNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.get("/ordens-de-servico/{id}/acompanhar", response_model=AcompanharOsResponse)
def acompanhar_os(
    id: UUID,
    caso_de_uso: Annotated[BuscarOrdemDeServico, Depends(get_buscar_ordem_de_servico)],
):
    try:
        os = caso_de_uso.executar(id)
        return AcompanharOsResponse.from_domain(os)
    except OrdemDeServicoNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/iniciar-diagnostico", response_model=OsResponse)
def iniciar_diagnostico(
    id: UUID,
    caso_de_uso: Annotated[IniciarDiagnostico, Depends(get_iniciar_diagnostico)],
    _: MecanicoDep,
):
    try:
        return OsResponse.from_domain(caso_de_uso.executar(id))
    except TransicaoInvalidaError as e:
        raise HTTPException(422, str(e))
    except OrdemDeServicoNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/finalizar-diagnostico", response_model=OsResponse)
def finalizar_diagnostico(
    id: UUID,
    caso_de_uso: Annotated[FinalizarDiagnostico, Depends(get_finalizar_diagnostico)],
    _: MecanicoDep,
    body: FinalizarDiagnosticoRequest | None = None,
):
    try:
        laudo = body.laudo_diagnostico if body else None
        return OsResponse.from_domain(caso_de_uso.executar(id, laudo))
    except TransicaoInvalidaError as e:
        raise HTTPException(422, str(e))
    except OrdemDeServicoNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/adicionar-servico", response_model=OsResponse)
def adicionar_servico(
    id: UUID,
    body: AdicionarServicoRequest,
    caso_de_uso: Annotated[AdicionarServico, Depends(get_adicionar_servico)],
    _: AdminDep,
):
    try:
        os = caso_de_uso.executar(id, UUID(body.servico_id), body.observacao)
        return OsResponse.from_domain(os)
    except ServicoNaoEncontradoError as e:
        raise HTTPException(404, str(e))
    except TransicaoInvalidaError as e:
        raise HTTPException(422, str(e))
    except OrdemDeServicoNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/adicionar-peca", response_model=OsResponse)
def adicionar_peca(
    id: UUID,
    body: AdicionarPecaRequest,
    caso_de_uso: Annotated[AdicionarPeca, Depends(get_adicionar_peca)],
    _: AdminDep,
):
    try:
        os = caso_de_uso.executar(id, UUID(body.peca_id), body.quantidade)
        return OsResponse.from_domain(os)
    except TransicaoInvalidaError as e:
        raise HTTPException(422, str(e))
    except EstoqueInsuficienteError as e:
        raise HTTPException(422, str(e))
    except PecaNaoEncontradaError as e:
        raise HTTPException(404, str(e))
    except OrdemDeServicoNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/gerar-orcamento", response_model=OsResponse)
def gerar_orcamento(
    id: UUID,
    caso_de_uso: Annotated[GerarOrcamento, Depends(get_gerar_orcamento)],
    _: AdminDep,
):
    try:
        return OsResponse.from_domain(caso_de_uso.executar(id))
    except (TransicaoInvalidaError, OsSemServicosError) as e:
        raise HTTPException(422, str(e))
    except OrdemDeServicoNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/aprovar-orcamento", response_model=OsResponse)
def aprovar_orcamento(
    id: UUID,
    caso_de_uso: Annotated[AprovarOrcamento, Depends(get_aprovar_orcamento)],
):
    try:
        return OsResponse.from_domain(caso_de_uso.executar(id))
    except EstoqueInsuficienteError as e:
        raise HTTPException(422, str(e))
    except TransicaoInvalidaError as e:
        raise HTTPException(422, str(e))
    except OrdemDeServicoNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/recusar-orcamento", response_model=OsResponse)
def recusar_orcamento(
    id: UUID,
    body: RecusarOrcamentoRequest,
    caso_de_uso: Annotated[RecusarOrcamento, Depends(get_recusar_orcamento)],
):
    try:
        return OsResponse.from_domain(caso_de_uso.executar(id, body.motivo))
    except TransicaoInvalidaError as e:
        raise HTTPException(422, str(e))
    except OrdemDeServicoNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.post(
    "/ordens-de-servico/{id}/executar-servico/{item_id}", response_model=OsResponse
)
def executar_servico(
    id: UUID,
    item_id: UUID,
    caso_de_uso: Annotated[ExecutarServico, Depends(get_executar_servico)],
    _: MecanicoDep,
):
    try:
        return OsResponse.from_domain(caso_de_uso.executar(id, item_id))
    except (TransicaoInvalidaError, ItemNaoEncontradoError) as e:
        raise HTTPException(422, str(e))
    except OrdemDeServicoNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/finalizar", response_model=OsResponse)
def finalizar_os(
    id: UUID,
    caso_de_uso: Annotated[FinalizarOS, Depends(get_finalizar_os)],
    _: AdminDep,
):
    try:
        return OsResponse.from_domain(caso_de_uso.executar(id))
    except TransicaoInvalidaError as e:
        raise HTTPException(422, str(e))
    except OrdemDeServicoNaoEncontradaError as e:
        raise HTTPException(404, str(e))


@router.post("/ordens-de-servico/{id}/entregar", response_model=OsResponse)
def entregar_veiculo(
    id: UUID,
    caso_de_uso: Annotated[EntregarVeiculo, Depends(get_entregar_veiculo)],
    _: AdminDep,
):
    try:
        return OsResponse.from_domain(caso_de_uso.executar(id))
    except TransicaoInvalidaError as e:
        raise HTTPException(422, str(e))
    except OrdemDeServicoNaoEncontradaError as e:
        raise HTTPException(404, str(e))
