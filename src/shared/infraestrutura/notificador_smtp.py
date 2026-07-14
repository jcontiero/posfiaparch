import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from src.config import Configuracoes
from src.atendimento.aplicacao.ports import Notificador
from src.estoque.aplicacao.ports import NotificadorEstoque

logger = logging.getLogger(__name__)

_TEMPLATES = Path(__file__).parent.parent / "templates"


class SmtpNotificador(Notificador, NotificadorEstoque):
    def __init__(self, configuracoes: Configuracoes):
        self.config = configuracoes

    def _render(self, template: str, **ctx: str) -> str:
        tpl = (_TEMPLATES / template).read_text(encoding="utf-8")
        for key, value in ctx.items():
            tpl = tpl.replace(f"{{{{{key}}}}}", value)
        return tpl

    def _html(self, titulo: str, subtitulo: str, corpo: str) -> str:
        return self._render(
            "base.html", titulo=titulo, subtitulo=subtitulo, corpo=corpo
        )

    def _enviar_email(self, destinatario: str, assunto: str, corpo_html: str) -> None:
        if (
            not self.config.smtp_user
            or not self.config.smtp_password
            or not destinatario
        ):
            return
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = assunto
            msg["From"] = f"AutoTech Oficina <{self.config.email_remetente}>"
            msg["To"] = destinatario
            msg.attach(MIMEText(corpo_html, "html"))
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_user, self.config.smtp_password)
                server.sendmail(
                    self.config.email_remetente, destinatario, msg.as_string()
                )
        except Exception as e:
            logger.error("Falha ao enviar e-mail para %s: %s", destinatario, e)

    # -- 1. Diagnóstico concluído -> Admin
    def notificar_admin_diagnostico_concluido(
        self,
        os_id: str,
        placa: str,
        cliente_nome: str,
        descricao_problema: str,
        laudo_diagnostico: str | None = None,
    ) -> None:
        bloco_laudo = (
            f"<p><b>Laudo do mecânico:</b></p>"
            f"<p style='white-space:pre-wrap'>{laudo_diagnostico}</p>"
            if laudo_diagnostico
            else ""
        )
        corpo = self._render(
            "diagnostico_concluido.html",
            os_id=os_id,
            os_id_curto=os_id[:8].upper(),
            placa=placa,
            cliente_nome=cliente_nome,
            descricao_problema=descricao_problema,
            bloco_laudo=bloco_laudo,
        )
        self._enviar_email(
            destinatario=self.config.email_admin,
            assunto=f"[AutoTech] Diagnóstico concluído — OS {os_id[:8].upper()}",
            corpo_html=self._html(
                "Diagnóstico Concluído", f"OS {os_id[:8].upper()} · {placa}", corpo
            ),
        )

    # -- 2. Orçamento disponível -> Cliente
    def notificar_cliente_orcamento_disponivel(
        self,
        email: str,
        nome: str,
        placa: str,
        os_id: str,
        valor: str,
        itens_servico: list[dict],
        itens_peca: list[dict],
    ) -> None:
        tabela_servicos = ""
        if itens_servico:
            linhas = "".join(
                f"<tr><td>{i['descricao']}</td>"
                f"<td class='right'>R$ {i['preco_unitario']}</td></tr>"
                for i in itens_servico
            )
            tabela_servicos = (
                "<p class='section-title'>Serviços</p>"
                "<table class='items'>"
                "<thead><tr><th scope='col'>Descrição</th><th scope='col' class='right'>Valor</th></tr></thead>"
                f"<tbody>{linhas}</tbody></table>"
            )

        tabela_pecas = ""
        if itens_peca:
            linhas = "".join(
                f"<tr><td>{i['descricao']}</td>"
                f"<td class='center'>{i['quantidade']}</td>"
                f"<td class='right'>R$ {i['preco_unitario']}</td>"
                f"<td class='right'>R$ {i['preco_total']}</td></tr>"
                for i in itens_peca
            )
            tabela_pecas = (
                "<p class='section-title'>Peças e insumos</p>"
                "<table class='items'>"
                "<thead><tr><th scope='col'>Descrição</th><th scope='col' class='center'>Qtd</th>"
                "<th scope='col' class='right'>Unit.</th><th scope='col' class='right'>Total</th></tr></thead>"
                f"<tbody>{linhas}</tbody></table>"
            )

        colspan = "3" if itens_peca else "1"

        corpo = self._render(
            "orcamento_disponivel.html",
            nome=nome,
            placa=placa,
            os_id=os_id,
            os_id_curto=os_id[:8].upper(),
            valor=valor,
            tabela_servicos=tabela_servicos,
            tabela_pecas=tabela_pecas,
            colspan_total=colspan,
        )
        self._enviar_email(
            destinatario=email,
            assunto=f"[AutoTech] Seu orçamento está pronto — {placa}",
            corpo_html=self._html(
                "Orçamento Disponível", f"Veículo {placa} · R$ {valor}", corpo
            ),
        )

    # -- 3. Serviços concluídos -> Admin
    def notificar_admin_servicos_concluidos(
        self,
        os_id: str,
        placa: str,
        cliente_nome: str,
        itens_servico: list[dict],
    ) -> None:
        tabela_servicos = ""
        if itens_servico:
            linhas = "".join(
                f"<tr><td>{i['descricao']}</td>"
                f"<td class='center' style='color:#43a047'>✔ Concluído</td>"
                f"<td>{i.get('concluido_em', '—')}</td></tr>"
                for i in itens_servico
            )
            tabela_servicos = (
                "<p class='section-title'>Serviços executados</p>"
                "<table class='items'>"
                "<thead><tr><th scope='col'>Serviço</th><th scope='col' class='center'>Status</th>"
                "<th scope='col'>Concluído em</th></tr></thead>"
                f"<tbody>{linhas}</tbody></table>"
            )

        corpo = self._render(
            "servicos_concluidos.html",
            os_id=os_id,
            os_id_curto=os_id[:8].upper(),
            placa=placa,
            cliente_nome=cliente_nome,
            tabela_servicos=tabela_servicos,
        )
        self._enviar_email(
            destinatario=self.config.email_admin,
            assunto=f"[AutoTech] Serviços concluídos — OS {os_id[:8].upper()}",
            corpo_html=self._html(
                "Serviços Concluídos", f"OS {os_id[:8].upper()} · {placa}", corpo
            ),
        )

    # -- 4. Orçamento recusado -> Admin
    def notificar_admin_orcamento_recusado(
        self,
        os_id: str,
        placa: str,
        cliente_nome: str,
        valor: str,
        motivo: str,
    ) -> None:
        corpo = self._render(
            "orcamento_recusado.html",
            os_id=os_id,
            os_id_curto=os_id[:8].upper(),
            placa=placa,
            cliente_nome=cliente_nome,
            valor=valor,
            motivo=motivo or "Não informado",
        )
        self._enviar_email(
            destinatario=self.config.email_admin,
            assunto=f"[AutoTech] Orçamento recusado — OS {os_id[:8].upper()}",
            corpo_html=self._html(
                "Orçamento Recusado", f"OS {os_id[:8].upper()} · {placa}", corpo
            ),
        )

    # -- 5. Estoque reposto -> Admin
    def notificar_admin_estoque_reposto(
        self,
        nome: str,
        codigo: str,
        quantidade_reposta: int,
        quantidade_atual: int,
    ) -> None:
        corpo = self._render(
            "estoque_reposto.html",
            nome=nome,
            codigo=codigo,
            quantidade_reposta=str(quantidade_reposta),
            quantidade_atual=str(quantidade_atual),
        )
        self._enviar_email(
            destinatario=self.config.email_admin,
            assunto=f"[AutoTech] Estoque reposto — {nome}",
            corpo_html=self._html(
                "Estoque Reposto", f"{nome} · {quantidade_atual} un. disponíveis", corpo
            ),
        )

    # -- 6. Veículo pronto -> Cliente
    def notificar_cliente_veiculo_pronto(
        self,
        email: str,
        nome: str,
        placa: str,
        valor_total: str,
    ) -> None:
        corpo = self._render(
            "veiculo_pronto.html",
            nome=nome,
            placa=placa,
            valor_total=valor_total,
        )
        self._enviar_email(
            destinatario=email,
            assunto=f"[AutoTech] Seu veículo está pronto — {placa}",
            corpo_html=self._html(
                "Veículo Pronto", f"Veículo {placa} · R$ {valor_total}", corpo
            ),
        )
