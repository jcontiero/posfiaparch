from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from src.estoque.dominio.entidades import Peca
from src.estoque.dominio.repositorios import PecaRepositorio
from src.estoque.infraestrutura.modelos import PecaModel


class PecaRepositorioImpl(PecaRepositorio):
    def __init__(self, db: Session):
        self.db = db

    def salvar(self, peca: Peca) -> Peca:
        modelo = self.db.get(PecaModel, peca.id)
        if modelo:
            modelo.nome = peca.nome
            modelo.preco_unitario = peca.preco_unitario
            modelo.quantidade_disponivel = peca.quantidade_disponivel
            modelo.quantidade_minima_alerta = peca.quantidade_minima_alerta
        else:
            modelo = PecaModel(id=peca.id, nome=peca.nome, codigo=peca.codigo,
                               preco_unitario=peca.preco_unitario,
                               quantidade_disponivel=peca.quantidade_disponivel,
                               quantidade_minima_alerta=peca.quantidade_minima_alerta)
            self.db.add(modelo)
        self.db.commit()
        return peca

    def buscar_por_id(self, id: UUID) -> Peca | None:
        modelo = self.db.get(PecaModel, id)
        return self._para_entidade(modelo) if modelo else None

    def buscar_por_codigo(self, codigo: str) -> Peca | None:
        modelo = self.db.query(PecaModel).filter(PecaModel.codigo == codigo).first()
        return self._para_entidade(modelo) if modelo else None

    def listar(self, busca: str | None = None, apenas_alerta: bool = False) -> list[Peca]:
        query = self.db.query(PecaModel)
        if busca:
            query = query.filter(
                PecaModel.nome.ilike(f"%{busca}%") | PecaModel.codigo.ilike(f"%{busca}%")
            )
        modelos = query.all()
        pecas = [self._para_entidade(m) for m in modelos]
        if apenas_alerta:
            pecas = [p for p in pecas if p.alerta_estoque_baixo]
        return pecas

    def remover(self, id: UUID) -> None:
        modelo = self.db.get(PecaModel, id)
        if modelo:
            self.db.delete(modelo)
            self.db.commit()

    def _para_entidade(self, modelo: PecaModel) -> Peca:
        return Peca(
            id=modelo.id,
            nome=modelo.nome,
            codigo=modelo.codigo,
            preco_unitario=Decimal(str(modelo.preco_unitario)),
            quantidade_disponivel=modelo.quantidade_disponivel,
            quantidade_minima_alerta=modelo.quantidade_minima_alerta,
        )
