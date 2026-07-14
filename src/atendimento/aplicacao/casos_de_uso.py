import re
from uuid import uuid4, UUID

from src.atendimento.dominio.entidades import Cliente, Veiculo, OrdemDeServico
from src.atendimento.dominio.repositorios import (
    ClienteRepositorio,
    VeiculoRepositorio,
    OrdemDeServicoRepositorio,
)
from src.atendimento.dominio.value_objects import CPF, CNPJ, Placa, StatusOS
from src.atendimento.dominio.excecoes import (
    ClienteNaoEncontradoError,
    VeiculoNaoEncontradoError,
    VeiculoComOsAtivaError,
    ClienteComOsAtivaError,
    DocumentoDuplicadoError,
    PlacaDuplicadaError,
    OrdemDeServicoNaoEncontradaError,
)
from src.atendimento.aplicacao.ports import Notificador
from src.identidade.aplicacao.ports import ProvedorToken

# -- Clientes ------------------------------------------------------------------


class CadastrarCliente:
    def __init__(self, repo: ClienteRepositorio):
        self.repo = repo

    def executar(
        self,
        nome: str,
        email: str,
        telefone: str,
        cpf: str | None = None,
        cnpj: str | None = None,
    ) -> Cliente:
        cpf_vo = CPF(cpf) if cpf else None
        cnpj_vo = CNPJ(cnpj) if cnpj else None

        if cpf_vo and self.repo.buscar_por_cpf(cpf_vo.valor):
            raise DocumentoDuplicadoError(cpf_vo.valor)
        if cnpj_vo and self.repo.buscar_por_cnpj(cnpj_vo.valor):
            raise DocumentoDuplicadoError(cnpj_vo.valor)

        cliente = Cliente(
            id=uuid4(),
            nome=nome,
            cpf=cpf_vo,
            cnpj=cnpj_vo,
            email=email,
            telefone=telefone,
        )
        return self.repo.salvar(cliente)


class ListarClientes:
    def __init__(self, repo: ClienteRepositorio):
        self.repo = repo

    def executar(self, busca: str | None = None) -> list[Cliente]:
        return self.repo.listar(busca)


class BuscarCliente:
    def __init__(self, repo: ClienteRepositorio):
        self.repo = repo

    def executar(self, id: UUID) -> Cliente:
        cliente = self.repo.buscar_por_id(id)
        if not cliente:
            raise ClienteNaoEncontradoError(str(id))
        return cliente


class AtualizarCliente:
    def __init__(self, repo: ClienteRepositorio):
        self.repo = repo

    def executar(
        self,
        id: UUID,
        nome: str | None = None,
        email: str | None = None,
        telefone: str | None = None,
    ) -> Cliente:
        cliente = self.repo.buscar_por_id(id)
        if not cliente:
            raise ClienteNaoEncontradoError(str(id))
        if nome is not None:
            cliente.nome = nome
        if email is not None:
            cliente.email = email
        if telefone is not None:
            cliente.telefone = telefone
        return self.repo.salvar(cliente)


class RemoverCliente:
    def __init__(self, repo: ClienteRepositorio, os_repo: OrdemDeServicoRepositorio):
        self.repo = repo
        self.os_repo = os_repo

    def executar(self, id: UUID) -> None:
        cliente = self.repo.buscar_por_id(id)
        if not cliente:
            raise ClienteNaoEncontradoError(str(id))
        if self.os_repo.existe_os_ativa_por_cliente(id):
            raise ClienteComOsAtivaError()
        self.repo.remover(id)


# -- Veículos ------------------------------------------------------------------


class CadastrarVeiculo:
    def __init__(self, repo: VeiculoRepositorio, cliente_repo: ClienteRepositorio):
        self.repo = repo
        self.cliente_repo = cliente_repo

    def executar(
        self,
        cliente_id: UUID,
        placa: str,
        marca: str,
        modelo: str,
        ano: int,
        cor: str = "",
    ) -> Veiculo:
        if not self.cliente_repo.buscar_por_id(cliente_id):
            raise ClienteNaoEncontradoError(str(cliente_id))
        placa_vo = Placa(placa)
        if self.repo.buscar_por_placa(placa_vo.valor):
            raise PlacaDuplicadaError(placa_vo.valor)
        veiculo = Veiculo(
            id=uuid4(),
            cliente_id=cliente_id,
            placa=placa_vo,
            marca=marca,
            modelo=modelo,
            ano=ano,
            cor=cor,
        )
        return self.repo.salvar(veiculo)


class ListarVeiculos:
    def __init__(self, repo: VeiculoRepositorio):
        self.repo = repo

    def executar(self, cliente_id: UUID | None = None) -> list[Veiculo]:
        return self.repo.listar(cliente_id)


class BuscarVeiculo:
    def __init__(self, repo: VeiculoRepositorio):
        self.repo = repo

    def executar(self, id: UUID) -> Veiculo:
        veiculo = self.repo.buscar_por_id(id)
        if not veiculo:
            raise VeiculoNaoEncontradoError(str(id))
        return veiculo


class AtualizarVeiculo:
    def __init__(self, repo: VeiculoRepositorio):
        self.repo = repo

    def executar(
        self,
        id: UUID,
        marca: str | None = None,
        modelo: str | None = None,
        ano: int | None = None,
        cor: str | None = None,
    ) -> Veiculo:
        veiculo = self.repo.buscar_por_id(id)
        if not veiculo:
            raise VeiculoNaoEncontradoError(str(id))
        if marca is not None:
            veiculo.marca = marca
        if modelo is not None:
            veiculo.modelo = modelo
        if ano is not None:
            veiculo.ano = ano
        if cor is not None:
            veiculo.cor = cor
        return self.repo.salvar(veiculo)


class RemoverVeiculo:
    def __init__(self, repo: VeiculoRepositorio, os_repo: OrdemDeServicoRepositorio):
        self.repo = repo
        self.os_repo = os_repo

    def executar(self, id: UUID) -> None:
        veiculo = self.repo.buscar_por_id(id)
        if not veiculo:
            raise VeiculoNaoEncontradoError(str(id))
        if self.os_repo.buscar_ativa_por_veiculo(id):
            raise VeiculoComOsAtivaError(veiculo.placa.valor)
        self.repo.remover(id)


# -- Ordens de Serviço ---------------------------------------------------------


class AbrirOrdemDeServico:
    def __init__(
        self,
        os_repo: OrdemDeServicoRepositorio,
        cliente_repo: ClienteRepositorio,
        veiculo_repo: VeiculoRepositorio,
    ):
        self.os_repo = os_repo
        self.cliente_repo = cliente_repo
        self.veiculo_repo = veiculo_repo

    def executar(
        self, cliente_cpf_cnpj: str, veiculo_placa: str, descricao_problema: str
    ) -> OrdemDeServico:
        documento = re.sub(r"\D", "", cliente_cpf_cnpj)

        cliente = self.cliente_repo.buscar_por_cpf(
            documento
        ) or self.cliente_repo.buscar_por_cnpj(documento)
        if not cliente:
            raise ClienteNaoEncontradoError(cliente_cpf_cnpj)

        placa = Placa(veiculo_placa).valor
        veiculo = self.veiculo_repo.buscar_por_placa(placa)
        if not veiculo:
            raise VeiculoNaoEncontradoError(placa)

        if self.os_repo.buscar_ativa_por_veiculo(veiculo.id):
            raise VeiculoComOsAtivaError(placa)

        os = OrdemDeServico(
            id=uuid4(),
            cliente_id=cliente.id,
            veiculo_id=veiculo.id,
            descricao_problema=descricao_problema,
        )
        return self.os_repo.salvar(os)


class ListarOrdensDeServico:
    def __init__(self, repo: OrdemDeServicoRepositorio):
        self.repo = repo

    def executar(
        self, status: StatusOS | None = None, cliente_id: UUID | None = None
    ) -> list[OrdemDeServico]:
        return self.repo.listar(status, cliente_id)


class BuscarOrdemDeServico:
    def __init__(self, repo: OrdemDeServicoRepositorio):
        self.repo = repo

    def executar(self, id: UUID) -> OrdemDeServico:
        os = self.repo.buscar_por_id(id)
        if not os:
            raise OrdemDeServicoNaoEncontradaError(str(id))
        return os


class IniciarDiagnostico:
    def __init__(self, repo: OrdemDeServicoRepositorio):
        self.repo = repo

    def executar(self, os_id: UUID) -> OrdemDeServico:
        os = self._buscar(os_id)
        os.iniciar_diagnostico()
        return self.repo.salvar(os)

    def _buscar(self, os_id: UUID) -> OrdemDeServico:
        os = self.repo.buscar_por_id(os_id)
        if not os:
            raise OrdemDeServicoNaoEncontradaError(str(os_id))
        return os


class FinalizarDiagnostico:
    def __init__(
        self,
        repo: OrdemDeServicoRepositorio,
        veiculo_repo: VeiculoRepositorio,
        cliente_repo: ClienteRepositorio,
        notificador: Notificador,
    ):
        self.repo = repo
        self.veiculo_repo = veiculo_repo
        self.cliente_repo = cliente_repo
        self.notificador = notificador

    def executar(
        self, os_id: UUID, laudo_diagnostico: str | None = None
    ) -> OrdemDeServico:
        os = self.repo.buscar_por_id(os_id)
        if not os:
            raise OrdemDeServicoNaoEncontradaError(str(os_id))
        os.laudo_diagnostico = laudo_diagnostico
        os.finalizar_diagnostico()
        resultado = self.repo.salvar(os)
        veiculo = self.veiculo_repo.buscar_por_id(os.veiculo_id)
        cliente = self.cliente_repo.buscar_por_id(os.cliente_id)
        placa = veiculo.placa.valor if veiculo else str(os.veiculo_id)
        cliente_nome = cliente.nome if cliente else "—"
        self.notificador.notificar_admin_diagnostico_concluido(
            str(os_id), placa, cliente_nome, os.descricao_problema, laudo_diagnostico
        )
        return resultado


class AdicionarServico:
    def __init__(self, repo: OrdemDeServicoRepositorio, servico_repo):
        self.repo = repo
        self.servico_repo = servico_repo

    def executar(
        self, os_id: UUID, servico_id: UUID, observacao: str = ""
    ) -> OrdemDeServico:
        from src.catalogo.dominio.excecoes import ServicoNaoEncontradoError

        os = self.repo.buscar_por_id(os_id)
        if not os:
            raise OrdemDeServicoNaoEncontradaError(str(os_id))
        servico = self.servico_repo.buscar_por_id(servico_id)
        if not servico:
            raise ServicoNaoEncontradoError()
        os.adicionar_servico(servico_id, servico.nome, servico.preco_base, observacao)
        return self.repo.salvar(os)


class AdicionarPeca:
    def __init__(self, repo: OrdemDeServicoRepositorio, peca_repo):
        self.repo = repo
        self.peca_repo = peca_repo

    def executar(self, os_id: UUID, peca_id: UUID, quantidade: int) -> OrdemDeServico:
        from src.estoque.dominio.excecoes import PecaNaoEncontradaError

        os = self.repo.buscar_por_id(os_id)
        if not os:
            raise OrdemDeServicoNaoEncontradaError(str(os_id))
        peca = self.peca_repo.buscar_por_id(peca_id)
        if not peca:
            raise PecaNaoEncontradaError(peca_id)
        os.adicionar_peca(peca_id, peca.nome, quantidade, peca.preco_unitario)
        return self.repo.salvar(os)


class GerarOrcamento:
    def __init__(
        self,
        repo: OrdemDeServicoRepositorio,
        cliente_repo: ClienteRepositorio,
        veiculo_repo: VeiculoRepositorio,
        notificador: Notificador,
    ):
        self.repo = repo
        self.cliente_repo = cliente_repo
        self.veiculo_repo = veiculo_repo
        self.notificador = notificador

    def executar(self, os_id: UUID) -> OrdemDeServico:
        os = self.repo.buscar_por_id(os_id)
        if not os:
            raise OrdemDeServicoNaoEncontradaError(str(os_id))
        os.gerar_orcamento()
        resultado = self.repo.salvar(os)
        cliente = self.cliente_repo.buscar_por_id(os.cliente_id)
        veiculo = self.veiculo_repo.buscar_por_id(os.veiculo_id)
        if cliente and veiculo:
            self.notificador.notificar_cliente_orcamento_disponivel(
                email=cliente.email,
                nome=cliente.nome,
                placa=veiculo.placa.valor,
                os_id=str(os_id),
                valor=str(resultado.valor_orcamento),
                itens_servico=[
                    {"descricao": i.descricao, "preco_unitario": str(i.preco_unitario)}
                    for i in resultado.itens_servico
                ],
                itens_peca=[
                    {
                        "descricao": i.descricao,
                        "quantidade": i.quantidade,
                        "preco_unitario": str(i.preco_unitario),
                        "preco_total": str(i.preco_total),
                    }
                    for i in resultado.itens_peca
                ],
            )
        return resultado


class AprovarOrcamento:
    def __init__(self, repo: OrdemDeServicoRepositorio, peca_repo=None):
        self.repo = repo
        self.peca_repo = peca_repo

    def executar(self, os_id: UUID) -> OrdemDeServico:
        os = self.repo.buscar_por_id(os_id)
        if not os:
            raise OrdemDeServicoNaoEncontradaError(str(os_id))
        if self.peca_repo:
            for item in os.itens_peca:
                peca = self.peca_repo.buscar_por_id(item.peca_id)
                if peca:
                    peca.reservar(item.quantidade)
                    self.peca_repo.salvar(peca)
        os.aprovar_orcamento()
        return self.repo.salvar(os)


class RecusarOrcamento:
    def __init__(
        self,
        repo: OrdemDeServicoRepositorio,
        cliente_repo: ClienteRepositorio,
        veiculo_repo: VeiculoRepositorio,
        notificador: Notificador,
    ):
        self.repo = repo
        self.cliente_repo = cliente_repo
        self.veiculo_repo = veiculo_repo
        self.notificador = notificador

    def executar(self, os_id: UUID, motivo: str = "") -> OrdemDeServico:
        os = self.repo.buscar_por_id(os_id)
        if not os:
            raise OrdemDeServicoNaoEncontradaError(str(os_id))
        os.recusar_orcamento()
        resultado = self.repo.salvar(os)
        cliente = self.cliente_repo.buscar_por_id(os.cliente_id)
        veiculo = self.veiculo_repo.buscar_por_id(os.veiculo_id)
        if cliente and veiculo:
            self.notificador.notificar_admin_orcamento_recusado(
                os_id=str(os_id),
                placa=veiculo.placa.valor,
                cliente_nome=cliente.nome,
                valor=str(os.valor_orcamento) if os.valor_orcamento else "—",
                motivo=motivo,
            )
        return resultado


class ExecutarServico:
    def __init__(
        self,
        repo: OrdemDeServicoRepositorio,
        veiculo_repo: VeiculoRepositorio,
        notificador: Notificador,
    ):
        self.repo = repo
        self.veiculo_repo = veiculo_repo
        self.notificador = notificador

    def executar(self, os_id: UUID, item_id: UUID) -> OrdemDeServico:
        os = self.repo.buscar_por_id(os_id)
        if not os:
            raise OrdemDeServicoNaoEncontradaError(str(os_id))
        todos = os.executar_servico(item_id)
        resultado = self.repo.salvar(os)
        if todos:
            veiculo = self.veiculo_repo.buscar_por_id(os.veiculo_id)
            placa = veiculo.placa.valor if veiculo else str(os.veiculo_id)
            self.notificador.notificar_admin_servicos_concluidos(
                str(os_id),
                placa,
                "—",
                itens_servico=[
                    {
                        "descricao": i.descricao,
                        "concluido_em": (
                            i.concluido_em.strftime("%d/%m/%Y %H:%M")
                            if i.concluido_em
                            else "—"
                        ),
                    }
                    for i in resultado.itens_servico
                ],
            )
        return resultado


class FinalizarOS:
    def __init__(
        self,
        repo: OrdemDeServicoRepositorio,
        cliente_repo: ClienteRepositorio,
        veiculo_repo: VeiculoRepositorio,
        notificador: Notificador,
    ):
        self.repo = repo
        self.cliente_repo = cliente_repo
        self.veiculo_repo = veiculo_repo
        self.notificador = notificador

    def executar(self, os_id: UUID) -> OrdemDeServico:
        os = self.repo.buscar_por_id(os_id)
        if not os:
            raise OrdemDeServicoNaoEncontradaError(str(os_id))
        os.finalizar()
        resultado = self.repo.salvar(os)
        cliente = self.cliente_repo.buscar_por_id(os.cliente_id)
        veiculo = self.veiculo_repo.buscar_por_id(os.veiculo_id)
        if cliente and veiculo:
            self.notificador.notificar_cliente_veiculo_pronto(
                email=cliente.email,
                nome=cliente.nome,
                placa=veiculo.placa.valor,
                valor_total=(
                    str(resultado.valor_orcamento) if resultado.valor_orcamento else "—"
                ),
            )
        return resultado


class EntregarVeiculo:
    def __init__(self, repo: OrdemDeServicoRepositorio):
        self.repo = repo

    def executar(self, os_id: UUID) -> OrdemDeServico:
        os = self.repo.buscar_por_id(os_id)
        if not os:
            raise OrdemDeServicoNaoEncontradaError(str(os_id))
        os.entregar()
        return self.repo.salvar(os)


# -- APIs da Fase 2 ------------------------------------------------------------


class AbrirOrdemDeServicoUnificada:
    def __init__(
        self,
        os_repo: OrdemDeServicoRepositorio,
        cliente_repo: ClienteRepositorio,
        veiculo_repo: VeiculoRepositorio,
        servico_repo,
        peca_repo,
    ):
        self.os_repo = os_repo
        self.cliente_repo = cliente_repo
        self.veiculo_repo = veiculo_repo
        self.servico_repo = servico_repo
        self.peca_repo = peca_repo

    def executar(
        self,
        cliente_dados: dict,
        veiculo_dados: dict,
        servicos: list[dict],
        pecas: list[dict] | None = None,
    ) -> OrdemDeServico:
        from src.catalogo.dominio.excecoes import ServicoNaoEncontradoError
        from src.estoque.dominio.excecoes import PecaNaoEncontradaError

        cliente = self._obter_ou_criar_cliente(cliente_dados)
        veiculo = self._obter_ou_criar_veiculo(veiculo_dados, cliente.id)

        if self.os_repo.buscar_ativa_por_veiculo(veiculo.id):
            raise VeiculoComOsAtivaError(veiculo.placa.valor)

        os = OrdemDeServico(
            id=uuid4(),
            cliente_id=cliente.id,
            veiculo_id=veiculo.id,
            descricao_problema=veiculo_dados.get("descricao_problema", ""),
        )
        os.iniciar_diagnostico()

        for s in servicos:
            servico_id = UUID(s["servico_id"])
            servico = self.servico_repo.buscar_por_id(servico_id)
            if not servico:
                raise ServicoNaoEncontradoError()
            os.adicionar_servico(
                servico_id,
                servico.nome,
                servico.preco_base,
                s.get("observacao", ""),
            )

        for p in pecas or []:
            peca_id = UUID(p["peca_id"])
            quantidade = p["quantidade"]
            peca = self.peca_repo.buscar_por_id(peca_id)
            if not peca:
                raise PecaNaoEncontradaError(peca_id)
            os.adicionar_peca(
                peca_id,
                peca.nome,
                quantidade,
                peca.preco_unitario,
            )

        os.finalizar_diagnostico()
        os.gerar_orcamento()
        return self.os_repo.salvar(os)

    def _obter_ou_criar_cliente(self, dados: dict) -> Cliente:
        cpf = dados.get("cpf")
        cnpj = dados.get("cnpj")
        documento = re.sub(r"\D", "", cpf) if cpf else None
        cliente = None
        if documento:
            cliente = self.cliente_repo.buscar_por_cpf(documento)
        if not cliente and cnpj:
            documento = re.sub(r"\D", "", cnpj)
            cliente = self.cliente_repo.buscar_por_cnpj(documento)
        if cliente:
            return cliente

        cpf_vo = CPF(cpf) if cpf else None
        cnpj_vo = CNPJ(cnpj) if cnpj else None
        if cpf_vo and self.cliente_repo.buscar_por_cpf(cpf_vo.valor):
            raise DocumentoDuplicadoError(cpf_vo.valor)
        if cnpj_vo and self.cliente_repo.buscar_por_cnpj(cnpj_vo.valor):
            raise DocumentoDuplicadoError(cnpj_vo.valor)

        return self.cliente_repo.salvar(
            Cliente(
                id=uuid4(),
                nome=dados["nome"],
                cpf=cpf_vo,
                cnpj=cnpj_vo,
                email=dados["email"],
                telefone=dados["telefone"],
            )
        )

    def _obter_ou_criar_veiculo(self, dados: dict, cliente_id: UUID) -> Veiculo:
        placa = Placa(dados["placa"]).valor
        veiculo = self.veiculo_repo.buscar_por_placa(placa)
        if veiculo:
            return veiculo
        return self.veiculo_repo.salvar(
            Veiculo(
                id=uuid4(),
                cliente_id=cliente_id,
                placa=Placa(placa),
                marca=dados["marca"],
                modelo=dados["modelo"],
                ano=dados["ano"],
                cor=dados.get("cor", ""),
            )
        )


class ConsultarStatusOrdemDeServico:
    def __init__(self, repo: OrdemDeServicoRepositorio):
        self.repo = repo

    def executar(self, os_id: UUID) -> tuple[OrdemDeServico, str]:
        os = self.repo.buscar_por_id(os_id)
        if not os:
            raise OrdemDeServicoNaoEncontradaError(str(os_id))
        from src.atendimento.dominio.value_objects import (
            para_status_fase2,
        )

        return os, para_status_fase2(os.status).value


class ProcessarAprovacaoOrcamento:
    def __init__(
        self,
        repo: OrdemDeServicoRepositorio,
        peca_repo=None,
    ):
        self.repo = repo
        self.peca_repo = peca_repo

    def executar(self, os_id: UUID, aprovado: bool, motivo: str = "") -> OrdemDeServico:
        os = self.repo.buscar_por_id(os_id)
        if not os:
            raise OrdemDeServicoNaoEncontradaError(str(os_id))
        if aprovado:
            if self.peca_repo:
                for item in os.itens_peca:
                    peca = self.peca_repo.buscar_por_id(item.peca_id)
                    if peca:
                        peca.reservar(item.quantidade)
                        self.peca_repo.salvar(peca)
            os.aprovar_orcamento()
        else:
            os.recusar_orcamento()
        return self.repo.salvar(os)


class ListarOrdensDeServicoAtivas:
    def __init__(self, repo: OrdemDeServicoRepositorio):
        self.repo = repo

    def executar(self) -> list[OrdemDeServico]:
        from src.atendimento.dominio.value_objects import (
            StatusOSFase2,
            para_status_fase2,
            PRIORIDADE_LISTAGEM_FASE2,
        )

        todas = self.repo.listar()
        ativas = [
            os
            for os in todas
            if para_status_fase2(os.status)
            not in (
                StatusOSFase2.FINALIZADA,
                StatusOSFase2.ENTREGUE,
                StatusOSFase2.CANCELADA,
            )
        ]
        return sorted(
            ativas,
            key=lambda os: (
                PRIORIDADE_LISTAGEM_FASE2[para_status_fase2(os.status)],
                os.criada_em,
            ),
        )


class AtualizarStatusViaWebhook:
    def __init__(
        self,
        repo: OrdemDeServicoRepositorio,
        token_provider: ProvedorToken,
    ):
        self.repo = repo
        self.token_provider = token_provider

    def executar(
        self, os_id: UUID, token: str, novo_status: StatusOS
    ) -> OrdemDeServico:
        from src.atendimento.dominio.excecoes import (
            TokenDeAprovacaoInvalidoError,
        )

        os = self.repo.buscar_por_id(os_id)
        if not os:
            raise OrdemDeServicoNaoEncontradaError(str(os_id))
        try:
            payload = self.token_provider.decodificar(token)
        except Exception:
            raise TokenDeAprovacaoInvalidoError()
        if payload.get("os_id") != str(os_id):
            raise TokenDeAprovacaoInvalidoError()
        os.atualizar_status(novo_status)
        return self.repo.salvar(os)
