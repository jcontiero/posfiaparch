from decimal import Decimal
from uuid import UUID, uuid4
from src.catalogo.dominio.entidades import Servico
from src.catalogo.dominio.repositorios import ServicoRepositorio
from src.catalogo.dominio.excecoes import ServicoNaoEncontradoError


class CadastrarServico:
    def __init__(self, repo: ServicoRepositorio):
        self.repo = repo

    def executar(
        self,
        nome: str,
        descricao: str,
        preco_base: Decimal,
        tempo_estimado_minutos: int,
    ) -> Servico:
        servico = Servico(
            id=uuid4(),
            nome=nome,
            descricao=descricao,
            preco_base=preco_base,
            tempo_estimado_minutos=tempo_estimado_minutos,
        )
        return self.repo.salvar(servico)


class ListarServicos:
    def __init__(self, repo: ServicoRepositorio):
        self.repo = repo

    def executar(self, busca: str | None = None) -> list[Servico]:
        return self.repo.listar(busca)


class BuscarServico:
    def __init__(self, repo: ServicoRepositorio):
        self.repo = repo

    def executar(self, id: UUID) -> Servico:
        servico = self.repo.buscar_por_id(id)
        if not servico:
            raise ServicoNaoEncontradoError()
        return servico


class AtualizarServico:
    def __init__(self, repo: ServicoRepositorio):
        self.repo = repo

    def executar(
        self,
        id: UUID,
        nome: str | None = None,
        descricao: str | None = None,
        preco_base: Decimal | None = None,
        tempo_estimado_minutos: int | None = None,
    ) -> Servico:
        servico = self.repo.buscar_por_id(id)
        if not servico:
            raise ServicoNaoEncontradoError()
        if nome is not None:
            servico.nome = nome
        if descricao is not None:
            servico.descricao = descricao
        if preco_base is not None:
            servico.preco_base = preco_base
        if tempo_estimado_minutos is not None:
            servico.tempo_estimado_minutos = tempo_estimado_minutos
        return self.repo.atualizar(servico)


class RemoverServico:
    def __init__(self, repo: ServicoRepositorio):
        self.repo = repo

    def executar(self, id: UUID) -> None:
        servico = self.repo.buscar_por_id(id)
        if not servico:
            raise ServicoNaoEncontradoError()
        self.repo.remover(id)
