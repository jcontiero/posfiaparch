# ADR-003 — Notificações por E-mail via smtplib

**Projeto:** Sistema de Oficina Mecânica — FIAP Pos Tech Fase 1  
**Status:** Aceito  
**Data:** 2026-04  
**Autor:** Jonas Vasconcelos

---

## Contexto

O sistema precisa enviar notificações por e-mail em quatro momentos do ciclo de vida da OS:

1. Diagnóstico concluído → notifica Admin
2. Orçamento gerado → notifica Cliente
3. Todos os serviços concluídos → notifica Admin
4. OS finalizada (controle de qualidade) → notifica Cliente

A escolha da biblioteca de envio impacta a compatibilidade com o ambiente de desenvolvimento (Apple Silicon / ARM64 via Colima) e a complexidade de configuração.

---

## Alternativas consideradas

### SendGrid SDK (`sendgrid`)

**Prós:**
- API de alto nível, bem documentada
- Suporte a templates HTML, rastreamento de abertura, bounce management
- Plano gratuito generoso para MVPs

**Contras:**
- O pacote `sendgrid` depende de `cryptography` que, em algumas versões, inclui extensões nativas compiladas
- Em ambientes ARM64/Colima com imagens Docker não-native, causou `SIGILL` (exit code 132) por instrução ilegal na CPU emulada
- Introduz dependência de serviço externo pago para funcionalidade opcional no MVP

---

### smtplib (stdlib Python)

**Prós:**
- Faz parte da biblioteca padrão do Python — zero dependências extras
- Funciona em qualquer plataforma sem compilação nativa
- Compatível com qualquer provedor SMTP (Gmail, Outlook, SES, Mailgun via SMTP)
- Configuração via variáveis de ambiente já existentes no `.env`

**Contras:**
- API de mais baixo nível — exige composição manual do `MIMEMultipart`
- Sem recursos avançados (tracking, templates gerenciados, bounce handling)
- Adequado para MVP; em produção pode exigir migração para SDK dedicado

---

### Celery + Redis (envio assíncrono)

**Prós:**
- Envio não bloqueia a requisição HTTP
- Retry automático em caso de falha SMTP

**Contras:**
- Adiciona dois serviços à infraestrutura (broker + worker)
- Complexidade desproporcional para o MVP
- Fora do escopo do Tech Challenge

---

## Decisão

**smtplib** da stdlib Python com envio síncrono e falha silenciosa.

### Justificativas

1. **Compatibilidade ARM64/Colima** — a causa raiz do `SIGILL` com SendGrid foi eliminada. O smtplib é código Python puro, sem extensões nativas.

2. **Falha silenciosa intencional** — o bloco `try/except Exception: pass` em `enviar_email()` garante que falhas de e-mail não interrompam o fluxo principal da OS. Notificação é efeito colateral, não parte da transação de negócio.

3. **Configuração simples** — se `SMTP_USER` ou `SMTP_PASSWORD` estiverem vazios, a função retorna imediatamente sem tentar conexão. O sistema funciona sem e-mail configurado (útil em desenvolvimento e testes).

4. **Sem dependências novas** — nenhuma linha adicionada ao `pyproject.toml`.

---

## Eventos que disparam notificações

| Evento | Destinatário | Use Case |
|---|---|---|
| Diagnóstico concluído | Admin | `FinalizarDiagnostico` |
| Orçamento gerado | Cliente | `GerarOrcamento` |
| Orçamento recusado pelo cliente | Admin | `RecusarOrcamento` |
| Todos os serviços concluídos | Admin | `ExecutarServico` |
| OS finalizada — veículo pronto | Cliente | `FinalizarOS` |
| Estoque reposto | Admin | `ReporEstoque` |

---

## Templates HTML externos

Os corpos dos e-mails são mantidos em arquivos `.html` separados em `src/shared/templates/`, sem nenhum HTML inline no código Python. O módulo `notificacoes.py` usa uma função `_render(template, **ctx)` que lê o arquivo e substitui `{{chave}}` pelos valores em tempo de execução.

```
src/shared/templates/
├── base.html                  ← layout, CSS, logo SVG, header e footer
├── diagnostico_concluido.html
├── orcamento_disponivel.html
├── orcamento_recusado.html
├── servicos_concluidos.html
├── veiculo_pronto.html
└── estoque_reposto.html
```

Essa separação permite editar o visual dos e-mails sem tocar no código Python e sem dependência de engine de templates externa (Jinja2, Mako, etc.).

---

## Implementação

```python
# src/shared/notificacoes.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from src.config import configuracoes

def enviar_email(destinatario: str, assunto: str, corpo_html: str) -> None:
    if not configuracoes.smtp_user or not configuracoes.smtp_password or not destinatario:
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = configuracoes.email_remetente
        msg["To"] = destinatario
        msg.attach(MIMEText(corpo_html, "html"))
        with smtplib.SMTP(configuracoes.smtp_host, configuracoes.smtp_port) as server:
            server.starttls()
            server.login(configuracoes.smtp_user, configuracoes.smtp_password)
            server.sendmail(configuracoes.email_remetente, destinatario, msg.as_string())
    except Exception:
        pass  # falha silenciosa — email não bloqueia o fluxo da OS
```

### Variáveis de ambiente necessárias

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu@email.com
SMTP_PASSWORD=senha-de-app-gmail
EMAIL_REMETENTE=noreply@suaoficina.com
EMAIL_ADMIN=admin@suaoficina.com
```

---

## Consequências

### Positivas

- Ambiente Docker ARM64/Colima estável — sem SIGILL
- Zero dependências adicionais
- Sistema funciona em desenvolvimento sem configuração de e-mail
- Compatível com qualquer provedor SMTP

### Negativas

- Envio síncrono bloqueia a thread durante o SMTP handshake (~200ms em média)
- Sem retry automático em caso de falha temporária de rede
- Sem rastreamento de entrega ou bounce

### Evolução futura

Para produção, recomenda-se:
- Mover o envio para uma task assíncrona (Celery + Redis ou similar)
- Substituir smtplib por SDK de provedor transacional (AWS SES, Resend, Postmark)

---

## Referências

- Python docs: `email.mime`, `smtplib` — docs.python.org/3/library/smtplib.html
- Bandit B110 (`try_except_pass`) — aceito como risco calculado: falha de e-mail é intencional

---

**Anterior:** [ADR-002 — Arquitetura](./ADR-002-arquitetura.md)
