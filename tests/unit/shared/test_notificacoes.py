from unittest.mock import patch, MagicMock
from src.shared.notificacoes import (
    _render,
    enviar_email,
    notificar_admin_diagnostico_concluido,
    notificar_cliente_orcamento_disponivel,
    notificar_admin_servicos_concluidos,
    notificar_cliente_veiculo_pronto,
)


class TestRender:
    def test_substitui_placeholder_simples(self):
        html = _render("veiculo_pronto.html", nome="Jonas", placa="ABC1D23", valor_total="350.00")
        assert "Jonas" in html
        assert "ABC1D23" in html
        assert "350.00" in html

    def test_placeholder_ausente_permanece_no_output(self):
        html = _render("veiculo_pronto.html", nome="Jonas", placa="ABC1D23", valor_total="0.00")
        assert "{{" not in html

    def test_base_envolve_corpo(self):
        html = _render("base.html", titulo="T", subtitulo="S", corpo="<p>CONTEUDO</p>")
        assert "CONTEUDO" in html
        assert "AutoTech" in html


class TestEnviarEmail:
    def test_nao_envia_sem_smtp_user(self):
        with patch("src.shared.notificacoes.configuracoes") as mock_cfg:
            mock_cfg.smtp_user = ""
            mock_cfg.smtp_password = "senha"
            with patch("smtplib.SMTP") as mock_smtp:
                enviar_email("dest@email.com", "Assunto", "<p>corpo</p>")
                mock_smtp.assert_not_called()

    def test_nao_envia_sem_destinatario(self):
        with patch("src.shared.notificacoes.configuracoes") as mock_cfg:
            mock_cfg.smtp_user = "user@gmail.com"
            mock_cfg.smtp_password = "senha"
            with patch("smtplib.SMTP") as mock_smtp:
                enviar_email("", "Assunto", "<p>corpo</p>")
                mock_smtp.assert_not_called()

    def test_falha_smtp_e_silenciosa(self):
        with patch("src.shared.notificacoes.configuracoes") as mock_cfg:
            mock_cfg.smtp_user = "user@gmail.com"
            mock_cfg.smtp_password = "senha"
            mock_cfg.smtp_host = "smtp.gmail.com"
            mock_cfg.smtp_port = 587
            mock_cfg.email_remetente = "noreply@oficina.com"
            with patch("smtplib.SMTP", side_effect=ConnectionRefusedError("refused")):
                enviar_email("dest@email.com", "Assunto", "<p>corpo</p>")


class TestNotificacoes:
    def _mock_cfg(self, mock_cfg):
        mock_cfg.smtp_user = ""
        mock_cfg.smtp_password = ""
        mock_cfg.email_admin = ""
        mock_cfg.email_remetente = "noreply@oficina.com"
        mock_cfg.smtp_host = "smtp.gmail.com"
        mock_cfg.smtp_port = 587

    def test_diagnostico_concluido_renderiza_sem_smtp(self):
        with patch("src.shared.notificacoes.configuracoes") as mock_cfg:
            self._mock_cfg(mock_cfg)
            notificar_admin_diagnostico_concluido(
                os_id="abc123",
                placa="ABC1D23",
                cliente_nome="João Silva",
                descricao_problema="Barulho no motor",
            )

    def test_orcamento_com_servicos_e_pecas(self):
        with patch("src.shared.notificacoes.configuracoes") as mock_cfg:
            self._mock_cfg(mock_cfg)
            with patch("src.shared.notificacoes.enviar_email") as mock_send:
                notificar_cliente_orcamento_disponivel(
                    email="cliente@email.com",
                    nome="João Silva",
                    placa="ABC1D23",
                    os_id="abc123",
                    valor="235.00",
                    itens_servico=[{"descricao": "Troca de óleo", "preco_unitario": "150.00"}],
                    itens_peca=[{
                        "descricao": "Filtro de óleo", "quantidade": 1,
                        "preco_unitario": "85.00", "preco_total": "85.00",
                    }],
                )
                html = mock_send.call_args[1]["corpo_html"]
                assert "Troca de óleo" in html
                assert "Filtro de óleo" in html
                assert "235.00" in html

    def test_orcamento_sem_pecas_omite_tabela_pecas(self):
        with patch("src.shared.notificacoes.configuracoes") as mock_cfg:
            self._mock_cfg(mock_cfg)
            with patch("src.shared.notificacoes.enviar_email") as mock_send:
                notificar_cliente_orcamento_disponivel(
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
        with patch("src.shared.notificacoes.configuracoes") as mock_cfg:
            self._mock_cfg(mock_cfg)
            notificar_admin_servicos_concluidos(
                os_id="abc123",
                placa="ABC1D23",
                cliente_nome="João",
                itens_servico=[{"descricao": "Troca de óleo", "concluido_em": "28/04/2026 14:00"}],
            )

    def test_veiculo_pronto_renderiza(self):
        with patch("src.shared.notificacoes.configuracoes") as mock_cfg:
            self._mock_cfg(mock_cfg)
            notificar_cliente_veiculo_pronto(
                email="cliente@email.com",
                nome="Maria",
                placa="XYZ9999",
                valor_total="350.00",
            )
