from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

from src.shared.banco import SessionLocal
from src.shared.seguranca import hash_senha
from src.identidade.infraestrutura.modelos import UsuarioModel
from src.identidade.dominio.entidades import PerfilUsuario
from src.atendimento.infraestrutura.modelos import (
    ClienteModel, VeiculoModel, OrdemDeServicoModel, ItemServicoModel, ItemPecaModel,
)
from src.catalogo.infraestrutura.modelos import ServicoModel
from src.estoque.infraestrutura.modelos import PecaModel
from src.atendimento.dominio.value_objects import StatusOS


def ha(dias: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=dias)


def criar_mock():
    db = SessionLocal()
    try:
        if db.query(ClienteModel).count() > 0:
            print("Mock já existe — pulando")
            return

        # ── Usuários ──────────────────────────────────────────────────────────
        db.add(UsuarioModel(
            id=uuid4(), email="mecanico@oficina.com",
            senha_hash=hash_senha("senha123"), perfil=PerfilUsuario.MECANICO,
        ))

        # ── Catálogo de serviços ──────────────────────────────────────────────
        s_oleo = ServicoModel(id=uuid4(), nome="Troca de oleo", descricao="Troca de oleo do motor com filtro", preco_base=Decimal("150.00"), tempo_estimado_minutos=60)
        s_alin = ServicoModel(id=uuid4(), nome="Alinhamento e balanceamento", descricao="Alinhamento das rodas e balanceamento", preco_base=Decimal("120.00"), tempo_estimado_minutos=45)
        s_freo = ServicoModel(id=uuid4(), nome="Revisao de freios", descricao="Inspecao completa do sistema de freios", preco_base=Decimal("250.00"), tempo_estimado_minutos=90)
        s_diag = ServicoModel(id=uuid4(), nome="Diagnostico eletronico", descricao="Leitura de codigos de erro via scanner", preco_base=Decimal("200.00"), tempo_estimado_minutos=30)
        s_filt = ServicoModel(id=uuid4(), nome="Troca de filtros", descricao="Troca de filtro de ar e combustivel", preco_base=Decimal("90.00"), tempo_estimado_minutos=30)
        s_pneu = ServicoModel(id=uuid4(), nome="Troca de pneu", descricao="Troca e calibragem de pneu", preco_base=Decimal("80.00"), tempo_estimado_minutos=20)
        s_susp = ServicoModel(id=uuid4(), nome="Revisao de suspensao", descricao="Verificacao completa da suspensao", preco_base=Decimal("180.00"), tempo_estimado_minutos=60)
        s_elet = ServicoModel(id=uuid4(), nome="Revisao eletrica", descricao="Verificacao do sistema eletrico", preco_base=Decimal("160.00"), tempo_estimado_minutos=45)
        for s in [s_oleo, s_alin, s_freo, s_diag, s_filt, s_pneu, s_susp, s_elet]:
            db.add(s)

        # ── Estoque ───────────────────────────────────────────────────────────
        p_oleo  = PecaModel(id=uuid4(), nome="Oleo 5W30 (1L)", codigo="OL-5W30-001", preco_unitario=Decimal("35.00"), quantidade_disponivel=50, quantidade_minima_alerta=10)
        p_foleo = PecaModel(id=uuid4(), nome="Filtro de oleo", codigo="FO-001", preco_unitario=Decimal("25.00"), quantidade_disponivel=30, quantidade_minima_alerta=5)
        p_past  = PecaModel(id=uuid4(), nome="Pastilha de freio dianteira", codigo="PF-DIANT-001", preco_unitario=Decimal("85.00"), quantidade_disponivel=20, quantidade_minima_alerta=4)
        p_disco = PecaModel(id=uuid4(), nome="Disco de freio dianteiro", codigo="DF-DIANT-001", preco_unitario=Decimal("180.00"), quantidade_disponivel=8, quantidade_minima_alerta=2)
        p_pneu  = PecaModel(id=uuid4(), nome="Pneu 195/65R15", codigo="PN-195-001", preco_unitario=Decimal("320.00"), quantidade_disponivel=12, quantidade_minima_alerta=3)
        p_far   = PecaModel(id=uuid4(), nome="Filtro de ar", codigo="FA-001", preco_unitario=Decimal("40.00"), quantidade_disponivel=4, quantidade_minima_alerta=5)
        p_vela  = PecaModel(id=uuid4(), nome="Vela de ignicao", codigo="VI-001", preco_unitario=Decimal("22.00"), quantidade_disponivel=16, quantidade_minima_alerta=4)
        p_corr  = PecaModel(id=uuid4(), nome="Correia dentada", codigo="CD-001", preco_unitario=Decimal("95.00"), quantidade_disponivel=6, quantidade_minima_alerta=2)
        for p in [p_oleo, p_foleo, p_past, p_disco, p_pneu, p_far, p_vela, p_corr]:
            db.add(p)

        # ── Clientes ──────────────────────────────────────────────────────────
        c1 = ClienteModel(id=uuid4(), nome="Joao Silva", cpf="52998224725", cnpj=None, email="joao@email.com", telefone="11999990000")
        c2 = ClienteModel(id=uuid4(), nome="Maria Santos", cpf="21932463007", cnpj=None, email="maria@email.com", telefone="11988880000")
        c3 = ClienteModel(id=uuid4(), nome="Transportes ABC Ltda.", cpf=None, cnpj="11222333000181", email="frota@abc.com", telefone="1130001234")
        c4 = ClienteModel(id=uuid4(), nome="Carlos Ferreira", cpf="87748241079", cnpj=None, email="carlos@email.com", telefone="11977770000")
        c5 = ClienteModel(id=uuid4(), nome="Ana Lima", cpf="34644762060", cnpj=None, email="ana@email.com", telefone="11966660000")
        for c in [c1, c2, c3, c4, c5]:
            db.add(c)

        # ── Veículos ──────────────────────────────────────────────────────────
        v1  = VeiculoModel(id=uuid4(), cliente_id=c1.id, placa="ABC1D23", marca="Toyota",     modelo="Corolla",  ano=2022, cor="Prata")
        v2  = VeiculoModel(id=uuid4(), cliente_id=c1.id, placa="DEF4G56", marca="Honda",      modelo="Civic",    ano=2020, cor="Branco")
        v3  = VeiculoModel(id=uuid4(), cliente_id=c2.id, placa="GHI7J89", marca="Volkswagen", modelo="Gol",      ano=2019, cor="Vermelho")
        v4  = VeiculoModel(id=uuid4(), cliente_id=c3.id, placa="JKL0M12", marca="Ford",       modelo="Transit",  ano=2021, cor="Prata")
        v5  = VeiculoModel(id=uuid4(), cliente_id=c3.id, placa="MNO3P45", marca="Fiat",       modelo="Ducato",   ano=2020, cor="Branco")
        v6  = VeiculoModel(id=uuid4(), cliente_id=c4.id, placa="PQR6S78", marca="Chevrolet",  modelo="Onix",     ano=2023, cor="Preto")
        v7  = VeiculoModel(id=uuid4(), cliente_id=c4.id, placa="TUV9W01", marca="Hyundai",    modelo="HB20",     ano=2021, cor="Azul")
        v8  = VeiculoModel(id=uuid4(), cliente_id=c5.id, placa="XYZ2A34", marca="Renault",    modelo="Kwid",     ano=2022, cor="Laranja")
        for v in [v1, v2, v3, v4, v5, v6, v7, v8]:
            db.add(v)

        db.flush()

        def nova_os(cliente, veiculo, problema, status, orcamento, criada, atualizada):
            m = OrdemDeServicoModel(
                id=uuid4(), cliente_id=cliente.id, veiculo_id=veiculo.id,
                descricao_problema=problema, status=status,
                valor_orcamento=orcamento, criada_em=criada, atualizada_em=atualizada,
            )
            db.add(m)
            return m

        def item_s(os_m, servico, descricao, preco, concluido, concluido_em=None):
            db.add(ItemServicoModel(
                id=uuid4(), os_id=os_m.id, servico_id=servico.id,
                descricao=descricao, preco_unitario=preco,
                concluido=concluido, concluido_em=concluido_em,
            ))

        def item_p(os_m, peca, descricao, qtd, preco):
            db.add(ItemPecaModel(
                id=uuid4(), os_id=os_m.id, peca_id=peca.id,
                descricao=descricao, quantidade=qtd, preco_unitario=preco,
            ))

        # ── ENTREGUE (10 OS — histórico completo) ────────────────────────────

        o1 = nova_os(c1, v1, "Revisao periodica — troca de oleo", StatusOS.ENTREGUE, Decimal("325.00"), ha(120), ha(118))
        item_s(o1, s_oleo, "Troca de oleo", Decimal("150.00"), True, ha(119))
        item_p(o1, p_oleo, "Oleo 5W30 (4L)", 4, Decimal("35.00"))
        item_p(o1, p_foleo, "Filtro de oleo", 1, Decimal("25.00"))

        o2 = nova_os(c1, v2, "Luz de avaria acesa no painel", StatusOS.ENTREGUE, Decimal("330.00"), ha(105), ha(103))
        item_s(o2, s_diag, "Diagnostico eletronico", Decimal("200.00"), True, ha(104))
        item_s(o2, s_filt, "Troca de filtros", Decimal("90.00"), True, ha(104))
        item_p(o2, p_far, "Filtro de ar", 1, Decimal("40.00"))

        o3 = nova_os(c2, v3, "Barulho ao frear e pedal mole", StatusOS.ENTREGUE, Decimal("590.00"), ha(90), ha(87))
        item_s(o3, s_freo, "Revisao de freios", Decimal("250.00"), True, ha(88))
        item_p(o3, p_past, "Pastilha de freio dianteira", 2, Decimal("85.00"))
        item_p(o3, p_disco, "Disco de freio dianteiro", 1, Decimal("180.00"))

        o4 = nova_os(c3, v4, "Volante puxando para o lado", StatusOS.ENTREGUE, Decimal("120.00"), ha(75), ha(74))
        item_s(o4, s_alin, "Alinhamento e balanceamento", Decimal("120.00"), True, ha(74))

        o5 = nova_os(c1, v1, "Pneu furado e desgaste irregular", StatusOS.ENTREGUE, Decimal("520.00"), ha(60), ha(59))
        item_s(o5, s_pneu, "Troca de pneu", Decimal("80.00"), True, ha(59))
        item_s(o5, s_alin, "Alinhamento e balanceamento", Decimal("120.00"), True, ha(59))
        item_p(o5, p_pneu, "Pneu 195/65R15", 1, Decimal("320.00"))

        o6 = nova_os(c3, v5, "Revisao de 60.000 km", StatusOS.ENTREGUE, Decimal("545.00"), ha(45), ha(43))
        item_s(o6, s_oleo, "Troca de oleo", Decimal("150.00"), True, ha(44))
        item_s(o6, s_filt, "Troca de filtros", Decimal("90.00"), True, ha(44))
        item_p(o6, p_oleo, "Oleo 5W30 (5L)", 5, Decimal("35.00"))
        item_p(o6, p_foleo, "Filtro de oleo", 1, Decimal("25.00"))
        item_p(o6, p_far, "Filtro de ar", 1, Decimal("40.00"))

        o7 = nova_os(c4, v6, "Velas falhando e consumo alto", StatusOS.ENTREGUE, Decimal("278.00"), ha(30), ha(28))
        item_s(o7, s_diag, "Diagnostico eletronico", Decimal("200.00"), True, ha(29))
        item_p(o7, p_vela, "Vela de ignicao", 4, Decimal("22.00"))
        item_p(o7, p_far, "Filtro de ar", 1, Decimal("40.00"))

        o8 = nova_os(c5, v8, "Revisao anual", StatusOS.ENTREGUE, Decimal("270.00"), ha(20), ha(18))
        item_s(o8, s_oleo, "Troca de oleo", Decimal("150.00"), True, ha(19))
        item_s(o8, s_alin, "Alinhamento e balanceamento", Decimal("120.00"), True, ha(19))

        o9 = nova_os(c2, v3, "Correia dentada — risco de ruptura", StatusOS.ENTREGUE, Decimal("435.00"), ha(15), ha(13))
        item_s(o9, s_diag, "Diagnostico eletronico", Decimal("200.00"), True, ha(14))
        item_s(o9, s_susp, "Revisao de suspensao", Decimal("180.00"), True, ha(14))
        item_p(o9, p_corr, "Correia dentada", 1, Decimal("95.00"))

        o10 = nova_os(c4, v7, "Barulho na suspensao dianteira", StatusOS.ENTREGUE, Decimal("300.00"), ha(8), ha(6))
        item_s(o10, s_susp, "Revisao de suspensao", Decimal("180.00"), True, ha(7))
        item_s(o10, s_alin, "Alinhamento e balanceamento", Decimal("120.00"), True, ha(7))

        # ── FINALIZADA (3 OS) ─────────────────────────────────────────────────

        o11 = nova_os(c1, v2, "Troca de oleo de rotina", StatusOS.FINALIZADA, Decimal("185.00"), ha(5), ha(3))
        item_s(o11, s_oleo, "Troca de oleo", Decimal("150.00"), True, ha(3))
        item_p(o11, p_foleo, "Filtro de oleo", 1, Decimal("25.00"))

        o12 = nova_os(c3, v4, "Revisao sistema de freios", StatusOS.FINALIZADA, Decimal("335.00"), ha(4), ha(2))
        item_s(o12, s_freo, "Revisao de freios", Decimal("250.00"), True, ha(2))
        item_p(o12, p_past, "Pastilha de freio dianteira", 1, Decimal("85.00"))

        o13 = nova_os(c5, v8, "Diagnostico — carro falhando", StatusOS.FINALIZADA, Decimal("360.00"), ha(3), ha(1))
        item_s(o13, s_diag, "Diagnostico eletronico", Decimal("200.00"), True, ha(1))
        item_s(o13, s_elet, "Revisao eletrica", Decimal("160.00"), True, ha(1))

        # ── SERVICOS_CONCLUIDOS (2 OS) ────────────────────────────────────────

        o14 = nova_os(c2, v3, "Todos servicos prontos aguardando vistoria", StatusOS.SERVICOS_CONCLUIDOS, Decimal("370.00"), ha(2), ha(0))
        item_s(o14, s_freo, "Revisao de freios", Decimal("250.00"), True, ha(1))
        item_s(o14, s_alin, "Alinhamento e balanceamento", Decimal("120.00"), True, ha(0))

        o15 = nova_os(c4, v6, "Revisao completa 100k km", StatusOS.SERVICOS_CONCLUIDOS, Decimal("610.00"), ha(3), ha(0))
        item_s(o15, s_oleo, "Troca de oleo", Decimal("150.00"), True, ha(1))
        item_s(o15, s_filt, "Troca de filtros", Decimal("90.00"), True, ha(1))
        item_s(o15, s_susp, "Revisao de suspensao", Decimal("180.00"), True, ha(0))
        item_p(o15, p_oleo, "Oleo 5W30 (4L)", 4, Decimal("35.00"))
        item_p(o15, p_foleo, "Filtro de oleo", 1, Decimal("25.00"))
        item_p(o15, p_far, "Filtro de ar", 1, Decimal("40.00"))

        # ── EM_EXECUCAO (3 OS) ────────────────────────────────────────────────

        o16 = nova_os(c3, v5, "Barulho na suspensao traseira", StatusOS.EM_EXECUCAO, Decimal("300.00"), ha(2), ha(1))
        item_s(o16, s_susp, "Revisao de suspensao", Decimal("180.00"), True, ha(1))
        item_s(o16, s_alin, "Alinhamento e balanceamento", Decimal("120.00"), False, None)

        o17 = nova_os(c1, v1, "Revisao pre-viagem longa", StatusOS.EM_EXECUCAO, Decimal("420.00"), ha(1), ha(0))
        item_s(o17, s_oleo, "Troca de oleo", Decimal("150.00"), True, ha(0))
        item_s(o17, s_pneu, "Troca de pneu", Decimal("80.00"), False, None)
        item_s(o17, s_alin, "Alinhamento e balanceamento", Decimal("120.00"), False, None)
        item_p(o17, p_oleo, "Oleo 5W30 (4L)", 4, Decimal("35.00"))

        o18 = nova_os(c5, v8, "Sistema de freios com folga", StatusOS.EM_EXECUCAO, Decimal("250.00"), ha(1), ha(0))
        item_s(o18, s_freo, "Revisao de freios", Decimal("250.00"), False, None)

        # ── AGUARDANDO_APROVACAO (3 OS) ───────────────────────────────────────

        o19 = nova_os(c2, v3, "Ar condicionado nao gela", StatusOS.AGUARDANDO_APROVACAO, Decimal("200.00"), ha(2), ha(1))
        item_s(o19, s_diag, "Diagnostico eletronico", Decimal("200.00"), False)

        o20 = nova_os(c4, v7, "Carro perdendo potencia", StatusOS.AGUARDANDO_APROVACAO, Decimal("350.00"), ha(3), ha(1))
        item_s(o20, s_diag, "Diagnostico eletronico", Decimal("200.00"), False)
        item_s(o20, s_filt, "Troca de filtros", Decimal("90.00"), False)
        item_p(o20, p_far, "Filtro de ar", 1, Decimal("40.00"))

        o21 = nova_os(c1, v2, "Luz do motor acesa", StatusOS.AGUARDANDO_APROVACAO, Decimal("488.00"), ha(1), ha(0))
        item_s(o21, s_diag, "Diagnostico eletronico", Decimal("200.00"), False)
        item_s(o21, s_elet, "Revisao eletrica", Decimal("160.00"), False)
        item_p(o21, p_vela, "Vela de ignicao", 4, Decimal("22.00"))

        # ── AGUARDANDO_ORCAMENTO (3 OS) ───────────────────────────────────────

        o22 = nova_os(c3, v4, "Motor aquecendo demais", StatusOS.AGUARDANDO_ORCAMENTO, None, ha(1), ha(0))

        o23 = nova_os(c5, v8, "Fumaca branca ao ligar", StatusOS.AGUARDANDO_ORCAMENTO, None, ha(2), ha(1))

        o24 = nova_os(c2, v3, "Freio de mao nao segura", StatusOS.AGUARDANDO_ORCAMENTO, None, ha(1), ha(0))

        # ── EM_DIAGNOSTICO (2 OS) ─────────────────────────────────────────────

        o25 = nova_os(c4, v6, "Barulho ao acelerar", StatusOS.EM_DIAGNOSTICO, None, ha(0), ha(0))

        o26 = nova_os(c1, v1, "Volante vibrando em alta velocidade", StatusOS.EM_DIAGNOSTICO, None, ha(1), ha(0))

        # ── RECEBIDA (2 OS) ───────────────────────────────────────────────────

        o27 = nova_os(c3, v5, "Revisao periodica 80k km", StatusOS.RECEBIDA, None, ha(0), ha(0))

        o28 = nova_os(c5, v8, "Carro trepidando ao frear", StatusOS.RECEBIDA, None, ha(0), ha(0))

        # ── CANCELADA (4 OS) ─────────────────────────────────────────────────

        o29 = nova_os(c1, v2, "Diagnostico — cliente recusou orcamento alto", StatusOS.CANCELADA, Decimal("200.00"), ha(50), ha(48))
        item_s(o29, s_diag, "Diagnostico eletronico", Decimal("200.00"), False)

        o30 = nova_os(c2, v3, "Revisao completa — orcamento recusado", StatusOS.CANCELADA, Decimal("890.00"), ha(35), ha(33))
        item_s(o30, s_freo, "Revisao de freios", Decimal("250.00"), False)
        item_s(o30, s_susp, "Revisao de suspensao", Decimal("180.00"), False)
        item_s(o30, s_alin, "Alinhamento e balanceamento", Decimal("120.00"), False)
        item_p(o30, p_past, "Pastilha de freio dianteira", 2, Decimal("85.00"))
        item_p(o30, p_corr, "Correia dentada", 1, Decimal("95.00"))

        o31 = nova_os(c4, v7, "Troca de correia — cancelado por preco", StatusOS.CANCELADA, Decimal("455.00"), ha(20), ha(19))
        item_s(o31, s_diag, "Diagnostico eletronico", Decimal("200.00"), False)
        item_s(o31, s_susp, "Revisao de suspensao", Decimal("180.00"), False)
        item_p(o31, p_corr, "Correia dentada", 1, Decimal("95.00"))

        o32 = nova_os(c5, v8, "Revisao — cliente desistiu", StatusOS.CANCELADA, Decimal("270.00"), ha(10), ha(9))
        item_s(o32, s_oleo, "Troca de oleo", Decimal("150.00"), False)
        item_s(o32, s_filt, "Troca de filtros", Decimal("90.00"), False)

        db.commit()

        total = 32
        contagem = {
            "ENTREGUE": 10, "FINALIZADA": 3, "SERVICOS_CONCLUIDOS": 2,
            "EM_EXECUCAO": 3, "AGUARDANDO_APROVACAO": 3, "AGUARDANDO_ORCAMENTO": 3,
            "EM_DIAGNOSTICO": 2, "RECEBIDA": 2, "CANCELADA": 4,
        }
        print(f"Mock criado: 5 clientes | 8 veiculos | 8 servicos | 8 pecas | {total} OS")
        print("  " + " | ".join(f"{v} {k}" for k, v in contagem.items()))

    except Exception as e:
        db.rollback()
        print(f"Erro no mock: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    criar_mock()
