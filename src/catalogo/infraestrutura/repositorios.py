from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from src.catalogo.dominio.entidades import Servico
from src.catalogo.dominio.repositorios import ServicoRepositorio
from src.catalogo.infraestrutura.modelos import ServicoModel


class ServicoRepositorioImpl(ServicoRepositorio):
    def __init__(self, db: Session):
        self.db = db

    def salvar(self, servico: Servico) -> Servico:
        modelo = ServicoModel(
            id=servico.id,
            nome=servico.nome,
            descricao=servico.descricao,
            preco_base=servico.preco_base,
            tempo_estimado_minutos=servico.tempo_estimado_minutos,
        )
        self.db.add(modelo)
        self.db.commit()
        return servico

    def listar(self, busca: str | None = None) -> list[Servico]:
        query = self.db.query(ServicoModel)
        if busca:
            query = query.filter(ServicoModel.nome.ilike(f"%{busca}%"))
        return [self._para_entidade(m) for m in query.all()]

    def buscar_por_id(self, id: UUID) -> Servico | None:
        modelo = self.db.query(ServicoModel).filter(ServicoModel.id == id).first()
        if not modelo:
            return None
        return self._para_entidade(modelo)

    def atualizar(self, servico: Servico) -> Servico:
        modelo = (
            self.db.query(ServicoModel).filter(ServicoModel.id == servico.id).first()
        )
        if not modelo:
            return servico
        modelo.nome = servico.nome
        modelo.descricao = servico.descricao
        modelo.preco_base = servico.preco_base
        modelo.tempo_estimado_minutos = servico.tempo_estimado_minutos
        self.db.commit()
        return servico

    def remover(self, id: UUID) -> None:
        modelo = self.db.query(ServicoModel).filter(ServicoModel.id == id).first()
        if not modelo:
            return
        self.db.delete(modelo)
        self.db.commit()

    def _para_entidade(self, modelo: ServicoModel) -> Servico:
        return Servico(
            id=modelo.id,
            nome=modelo.nome,
            descricao=modelo.descricao,
            preco_base=Decimal(str(modelo.preco_base)),
            tempo_estimado_minutos=modelo.tempo_estimado_minutos,
        )
