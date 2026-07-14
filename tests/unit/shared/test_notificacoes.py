from unittest.mock import patch
from src.config import Configuracoes
from src.shared.infraestrutura.notificador_smtp import SmtpNotificador


def _config() -> Configuracoes:
    return Configuracoes(
        database_url="postgresql+pg8000://user:pass@localhost/db",
        secret_key="chave-secreta-teste-32-chars-ok",
        smtp_user="",
        smtp_password="",
        email_admin="",
        email_remetente="noreply@oficina.com",
    )


class TestRender:
    def test_substitui_placeholder_simples(self):
        notificador = SmtpNotificador(_config())
        html = notificador._render(
            "veiculo_pronto.html", nome="Jonas", placa="ABC1D23", valor_total="350.00"
        )
        assert "Jonas" in html
        assert "ABC1D23" in html
        assert "350.00" in html

    def test_placeholder_ausente_permanece_no_output(self):
        notificador = SmtpNotificador(_config())
        html = notificador._render(
            "veiculo_pronto.html", nome="Jonas", placa="ABC1D23", valor_total="0.00"
        )
        assert "{{" not in html

    def test_base_envolve_corpo(self):
        notificador = SmtpNotificador(_config())
        html = notificador._render(
            "base.html", titulo="T", subtitulo="S", corpo="<p>CONTEUDO</p>"
        )
        assert "CONTEUDO" in html
        assert "AutoTech" in html


class TestEnviarEmail:
    def test_nao_envia_sem_smtp_user(self):
        notificador = SmtpNotificador(_config())
        with patch("smtplib.SMTP") as mock_smtp:
            notificador._enviar_email("dest@email.com", "Assunto", "<p>corpo</p>")
            mock_smtp.assert_not_called()

    def test_nao_envia_sem_destinatario(self):
        cfg = _config()
        cfg.smtp_user = "user@gmail.com"
        cfg.smtp_password = "senha"
        notificador = SmtpNotificador(cfg)
        with patch("smtplib.SMTP") as mock_smtp:
            notificador._enviar_email("", "Assunto", "<p>corpo</p>")
            mock_smtp.assert_not_called()

    def test_falha_smtp_e_silenciosa(self):
        cfg = _config()
        cfg.smtp_user = "user@gmail.com"
        cfg.smtp_password = "senha"
        notificador = SmtpNotificador(cfg)
        with patch("smtplib.SMTP", side_effect=ConnectionRefusedError("refused")):
            notificador._enviar_email("dest@email.com", "Assunto", "<p>corpo</p>")


class TestNotificacoes:
    def _notificador(self):
        return SmtpNotificador(_config())

    def test_diagnostico_concluido_renderiza_sem_smtp(self):
        notificador = self._notificador()
        notificador.notificar_admin_diagnostico_concluido(
            os_id="abc123",
            placa="ABC1D23",
            cliente_nome="João Silva",
            descricao_problema="Barulho no motor",
        )

    def test_diagnostico_concluido_com_laudo_aparece_no_email(self):
        notificador = self._notificador()
        with patch.object(notificador, "_enviar_email") as mock_send:
            notificador.notificar_admin_diagnostico_concluido(
                os_id="abc123",
                placa="ABC1D23",
                cliente_nome="João Silva",
                descricao_problema="Barulho no motor",
                laudo_diagnostico="Rolamento dianteiro danificado. Troca necessária.",
            )
            html = mock_send.call_args[1]["corpo_html"]
            assert "Rolamento dianteiro danificado" in html
            assert "Laudo do mecânico" in html

    def test_diagnostico_concluido_sem_laudo_omite_bloco(self):
        notificador = self._notificador()
        with patch.object(notificador, "_enviar_email") as mock_send:
            notificador.notificar_admin_diagnostico_concluido(
                os_id="abc123",
                placa="ABC1D23",
                cliente_nome="João Silva",
                descricao_problema="Barulho no motor",
            )
            html = mock_send.call_args[1]["corpo_html"]
            assert "Laudo do mecânico" not in html

    def test_orcamento_com_servicos_e_pecas(self):
        notificador = self._notificador()
        with patch.object(notificador, "_enviar_email") as mock_send:
            notificador.notificar_cliente_orcamento_disponivel(
                email="cliente@email.com",
                nome="João Silva",
                placa="ABC1D23",
                os_id="abc123",
                valor="235.00",
                itens_servico=[
                    {"descricao": "Troca de óleo", "preco_unitario": "150.00"}
                ],
                itens_peca=[
                    {
                        "descricao": "Filtro de óleo",
                        "quantidade": 1,
                        "preco_unitario": "85.00",
                        "preco_total": "85.00",
                    }
                ],
            )
            html = mock_send.call_args[1]["corpo_html"]
            assert "Troca de óleo" in html
            assert "Filtro de óleo" in html
            assert "235.00" in html

    def test_orcamento_sem_pecas_omite_tabela_pecas(self):
        notificador = self._notificador()
        with patch.object(notificador, "_enviar_email") as mock_send:
            notificador.notificar_cliente_orcamento_disponivel(
                email="cliente@email.com",
                nome="Maria",
                placa="XYZ9999",
                os_id="def456",
                valor="150.00",
                itens_servico=[{"descricao": "Revisão", "preco_unitario": "150.00"}],
                itens_peca=[],
            )
            html = mock_send.call_args[1]["corpo_html"]
            assert "Peças e insumos" not in html

    def test_servicos_concluidos_renderiza(self):
        notificador = self._notificador()
        notificador.notificar_admin_servicos_concluidos(
            os_id="abc123",
            placa="ABC1D23",
            cliente_nome="João",
            itens_servico=[
                {"descricao": "Troca de óleo", "concluido_em": "28/04/2026 14:00"}
            ],
        )

    def test_veiculo_pronto_renderiza(self):
        notificador = self._notificador()
        notificador.notificar_cliente_veiculo_pronto(
            email="cliente@email.com",
            nome="Maria",
            placa="XYZ9999",
            valor_total="350.00",
        )
