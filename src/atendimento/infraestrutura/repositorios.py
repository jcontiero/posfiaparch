from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from src.atendimento.dominio.entidades import Cliente, Veiculo, OrdemDeServico, ItemServico, ItemPeca
from src.atendimento.dominio.repositorios import ClienteRepositorio, VeiculoRepositorio, OrdemDeServicoRepositorio
from src.atendimento.dominio.value_objects import StatusOS
from src.atendimento.infraestrutura.modelos import (
    ClienteModel, VeiculoModel, OrdemDeServicoModel, ItemServicoModel, ItemPecaModel,
)

STATUS_ATIVOS = [
    StatusOS.RECEBIDA, StatusOS.EM_DIAGNOSTICO, StatusOS.AGUARDANDO_APROVACAO,
    StatusOS.EM_EXECUCAO, StatusOS.FINALIZADA,
]


class ClienteRepositorioImpl(ClienteRepositorio):
    def __init__(self, db: Session):
        self.db = db

    def salvar(self, cliente: Cliente) -> Cliente:
        modelo = self.db.get(ClienteModel, cliente.id)
        if modelo:
            modelo.nome = cliente.nome
            modelo.email = cliente.email
            modelo.telefone = cliente.telefone
        else:
            modelo = ClienteModel(**self._para_dict(cliente))
            self.db.add(modelo)
        self.db.commit()
        return cliente

    def buscar_por_id(self, id: UUID) -> Cliente | None:
        m = self.db.get(ClienteModel, id)
        return self._para_entidade(m) if m else None

    def buscar_por_cpf(self, cpf: str) -> Cliente | None:
        m = self.db.query(ClienteModel).filter(ClienteModel.cpf == cpf).first()
        return self._para_entidade(m) if m else None

    def buscar_por_cnpj(self, cnpj: str) -> Cliente | None:
        m = self.db.query(ClienteModel).filter(ClienteModel.cnpj == cnpj).first()
        return self._para_entidade(m) if m else None

    def listar(self, busca: str | None = None) -> list[Cliente]:
        q = self.db.query(ClienteModel)
        if busca:
            q = q.filter(ClienteModel.nome.ilike(f"%{busca}%"))
        return [self._para_entidade(m) for m in q.all()]

    def remover(self, id: UUID) -> None:
        m = self.db.get(ClienteModel, id)
        if m:
            self.db.delete(m)
            self.db.commit()

    def _para_dict(self, c: Cliente) -> dict:
        return dict(id=c.id, nome=c.nome, cpf=c.cpf, cnpj=c.cnpj, email=c.email, telefone=c.telefone)

    def _para_entidade(self, m: ClienteModel) -> Cliente:
        return Cliente(id=m.id, nome=m.nome, cpf=m.cpf, cnpj=m.cnpj, email=m.email, telefone=m.telefone)


class VeiculoRepositorioImpl(VeiculoRepositorio):
    def __init__(self, db: Session):
        self.db = db

    def salvar(self, veiculo: Veiculo) -> Veiculo:
        m = self.db.get(VeiculoModel, veiculo.id)
        if m:
            m.marca = veiculo.marca; m.modelo = veiculo.modelo
            m.ano = veiculo.ano; m.cor = veiculo.cor
        else:
            m = VeiculoModel(id=veiculo.id, cliente_id=veiculo.cliente_id,
                             placa=veiculo.placa, marca=veiculo.marca,
                             modelo=veiculo.modelo, ano=veiculo.ano, cor=veiculo.cor)
            self.db.add(m)
        self.db.commit()
        return veiculo

    def buscar_por_id(self, id: UUID) -> Veiculo | None:
        m = self.db.get(VeiculoModel, id)
        return self._para_entidade(m) if m else None

    def buscar_por_placa(self, placa: str) -> Veiculo | None:
        m = self.db.query(VeiculoModel).filter(VeiculoModel.placa == placa).first()
        return self._para_entidade(m) if m else None

    def listar(self, cliente_id: UUID | None = None) -> list[Veiculo]:
        q = self.db.query(VeiculoModel)
        if cliente_id:
            q = q.filter(VeiculoModel.cliente_id == cliente_id)
        return [self._para_entidade(m) for m in q.all()]

    def remover(self, id: UUID) -> None:
        m = self.db.get(VeiculoModel, id)
        if m:
            self.db.delete(m); self.db.commit()

    def _para_entidade(self, m: VeiculoModel) -> Veiculo:
        return Veiculo(id=m.id, cliente_id=m.cliente_id, placa=m.placa,
                       marca=m.marca, modelo=m.modelo, ano=m.ano, cor=m.cor or "")


class OrdemDeServicoRepositorioImpl(OrdemDeServicoRepositorio):
    def __init__(self, db: Session):
        self.db = db

    def salvar(self, os: OrdemDeServico) -> OrdemDeServico:
        m = self.db.get(OrdemDeServicoModel, os.id)
        if m:
            m.status = os.status
            m.valor_orcamento = os.valor_orcamento
            m.laudo_diagnostico = os.laudo_diagnostico
            m.atualizada_em = os.atualizada_em
            self._sincronizar_itens(m, os)
        else:
            m = OrdemDeServicoModel(
                id=os.id, cliente_id=os.cliente_id, veiculo_id=os.veiculo_id,
                descricao_problema=os.descricao_problema, laudo_diagnostico=os.laudo_diagnostico,
                status=os.status, criada_em=os.criada_em, atualizada_em=os.atualizada_em,
            )
            self.db.add(m)
            self.db.flush()
            self._sincronizar_itens(m, os)
        self.db.commit()
        return os

    def buscar_por_id(self, id: UUID) -> OrdemDeServico | None:
        m = self.db.get(OrdemDeServicoModel, id)
        return self._para_entidade(m) if m else None

    def listar(self, status: StatusOS | None = None, cliente_id: UUID | None = None) -> list[OrdemDeServico]:
        q = self.db.query(OrdemDeServicoModel)
        if status:
            q = q.filter(OrdemDeServicoModel.status == status)
        if cliente_id:
            q = q.filter(OrdemDeServicoModel.cliente_id == cliente_id)
        return [self._para_entidade(m) for m in q.all()]

    def buscar_ativa_por_veiculo(self, veiculo_id: UUID) -> OrdemDeServico | None:
        m = (self.db.query(OrdemDeServicoModel)
             .filter(OrdemDeServicoModel.veiculo_id == veiculo_id,
                     OrdemDeServicoModel.status.in_(STATUS_ATIVOS))
             .first())
        return self._para_entidade(m) if m else None

    def existe_os_ativa_por_cliente(self, cliente_id: UUID) -> bool:
        return self.db.query(OrdemDeServicoModel).filter(
            OrdemDeServicoModel.cliente_id == cliente_id,
            OrdemDeServicoModel.status.in_(STATUS_ATIVOS),
        ).first() is not None

    def _sincronizar_itens(self, modelo: OrdemDeServicoModel, os: OrdemDeServico) -> None:
        ids_servico = {i.id for i in os.itens_servico}
        for item_model in list(modelo.itens_servico):
            if item_model.id not in ids_servico:
                self.db.delete(item_model)
        ids_existentes = {i.id for i in modelo.itens_servico}
        for item in os.itens_servico:
            if item.id not in ids_existentes:
                self.db.add(ItemServicoModel(
                    id=item.id, os_id=os.id, servico_id=item.servico_id,
                    descricao=item.descricao, preco_unitario=item.preco_unitario,
                    observacao=item.observacao, concluido=item.concluido,
                    concluido_em=item.concluido_em,
                ))
            else:
                for m in modelo.itens_servico:
                    if m.id == item.id:
                        m.concluido = item.concluido
                        m.concluido_em = item.concluido_em

        ids_peca = {i.id for i in os.itens_peca}
        for item_model in list(modelo.itens_peca):
            if item_model.id not in ids_peca:
                self.db.delete(item_model)
        ids_peca_existentes = {i.id for i in modelo.itens_peca}
        for item in os.itens_peca:
            if item.id not in ids_peca_existentes:
                self.db.add(ItemPecaModel(
                    id=item.id, os_id=os.id, peca_id=item.peca_id,
                    descricao=item.descricao, quantidade=item.quantidade,
                    preco_unitario=item.preco_unitario,
                ))

    def _para_entidade(self, m: OrdemDeServicoModel) -> OrdemDeServico:
        itens_servico = [
            ItemServico(id=i.id, servico_id=i.servico_id, descricao=i.descricao,
                        preco_unitario=Decimal(str(i.preco_unitario)),
                        observacao=i.observacao or "", concluido=i.concluido,
                        concluido_em=i.concluido_em)
            for i in m.itens_servico
        ]
        itens_peca = [
            ItemPeca(id=i.id, peca_id=i.peca_id, descricao=i.descricao,
                     quantidade=i.quantidade, preco_unitario=Decimal(str(i.preco_unitario)))
            for i in m.itens_peca
        ]
        return OrdemDeServico(
            id=m.id, cliente_id=m.cliente_id, veiculo_id=m.veiculo_id,
            descricao_problema=m.descricao_problema, laudo_diagnostico=m.laudo_diagnostico,
            status=m.status,
            valor_orcamento=Decimal(str(m.valor_orcamento)) if m.valor_orcamento else None,
            criada_em=m.criada_em, atualizada_em=m.atualizada_em,
            itens_servico=itens_servico, itens_peca=itens_peca,
        )
