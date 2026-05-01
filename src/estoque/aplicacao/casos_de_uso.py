from uuid import uuid4, UUID
from decimal import Decimal
from src.estoque.dominio.entidades import Peca
from src.estoque.dominio.repositorios import PecaRepositorio
from src.estoque.dominio.excecoes import PecaNaoEncontradaError, CodigoPecaDuplicadoError


class CadastrarPeca:
    def __init__(self, repo: PecaRepositorio):
        self.repo = repo

    def executar(self, nome: str, codigo: str, preco_unitario: Decimal,
                 quantidade_disponivel: int, quantidade_minima_alerta: int = 5) -> Peca:
        if self.repo.buscar_por_codigo(codigo):
            raise CodigoPecaDuplicadoError(codigo)
        peca = Peca(id=uuid4(), nome=nome, codigo=codigo, preco_unitario=preco_unitario,
                    quantidade_disponivel=quantidade_disponivel,
                    quantidade_minima_alerta=quantidade_minima_alerta)
        return self.repo.salvar(peca)


class ListarPecas:
    def __init__(self, repo: PecaRepositorio):
        self.repo = repo

    def executar(self, busca: str | None = None, apenas_alerta: bool = False) -> list[Peca]:
        return self.repo.listar(busca, apenas_alerta)


class BuscarPeca:
    def __init__(self, repo: PecaRepositorio):
        self.repo = repo

    def executar(self, id: UUID) -> Peca:
        peca = self.repo.buscar_por_id(id)
        if not peca:
            raise PecaNaoEncontradaError(id)
        return peca


class AtualizarPeca:
    def __init__(self, repo: PecaRepositorio):
        self.repo = repo

    def executar(self, id: UUID, **campos) -> Peca:
        peca = self.repo.buscar_por_id(id)
        if not peca:
            raise PecaNaoEncontradaError(id)
        for campo, valor in campos.items():
            if valor is not None:
                setattr(peca, campo, valor)
        return self.repo.salvar(peca)


class ReporEstoque:
    def __init__(self, repo: PecaRepositorio):
        self.repo = repo

    def executar(self, id: UUID, quantidade: int) -> Peca:
        from src.shared.notificacoes import notificar_admin_estoque_reposto
        peca = self.repo.buscar_por_id(id)
        if not peca:
            raise PecaNaoEncontradaError(id)
        peca.repor(quantidade)
        resultado = self.repo.salvar(peca)
        notificar_admin_estoque_reposto(
            nome=peca.nome,
            codigo=peca.codigo,
            quantidade_reposta=quantidade,
            quantidade_atual=resultado.quantidade_disponivel,
        )
        return resultado


class ReservarPeca:
    def __init__(self, repo: PecaRepositorio):
        self.repo = repo

    def executar(self, id: UUID, quantidade: int) -> Peca:
        peca = self.repo.buscar_por_id(id)
        if not peca:
            raise PecaNaoEncontradaError(id)
        peca.reservar(quantidade)
        return self.repo.salvar(peca)


class LiberarReserva:
    def __init__(self, repo: PecaRepositorio):
        self.repo = repo

    def executar(self, id: UUID, quantidade: int) -> Peca:
        peca = self.repo.buscar_por_id(id)
        if not peca:
            raise PecaNaoEncontradaError(id)
        peca.liberar_reserva(quantidade)
        return self.repo.salvar(peca)


class RemoverPeca:
    def __init__(self, repo: PecaRepositorio):
        self.repo = repo

    def executar(self, id: UUID) -> None:
        if not self.repo.buscar_por_id(id):
            raise PecaNaoEncontradaError(id)
        self.repo.remover(id)
