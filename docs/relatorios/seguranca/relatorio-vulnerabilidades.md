# Relatório de Análise de Vulnerabilidades

**Projeto:** Oficina Mecânica API  
**Data do scan:** 2026-04-29  
**Ferramenta:** Bandit 1.9.x (análise estática de segurança para Python)  
**Escopo:** `src/` — 2.402 linhas de código

---

## 1. Resultado do Scan Automatizado

```
bandit -r src/ -f txt

Run started: 2026-04-30
Total lines of code: 2402
Total lines skipped (#nosec): 0

Total issues (by severity):
    High:    0
    Medium:  0
    Low:     1

Files skipped: 0
```

**1 issue de baixa severidade identificado** — detalhe na seção 2.7.

---

## 2. Análise Manual de Segurança

O scan automatizado cobre falhas de código conhecidas (injeção, uso de funções inseguras, configurações perigosas). A análise manual complementa com avaliação de design e configuração.

---

### 2.1 Autenticação e Autorização

**Status: Implementado corretamente**

| Controle | Implementação | Avaliação |
|---|---|---|
| Hash de senhas | `bcrypt` direto (sem passlib) — ARM64-safe | Seguro — bcrypt é resistente a ataques de força bruta |
| Tokens JWT | `PyJWT`, assinado com `HS256`, expiração em 8h | Adequado para MVP |
| Proteção de rotas | `HTTPBearer` via `Depends(get_usuario_atual)` | Correto — token ausente retorna 401 |
| Controle por perfil | `require_admin` e `require_mecanico` via `Depends` | Correto — ADMIN e MECÂNICO têm permissões distintas |
| Rotas públicas | 4 rotas explicitamente isentas de JWT | Correto — princípio de menor privilégio |
| Dados sensíveis na rota pública | `/acompanhar` não expõe CPF, CNPJ, e-mail | Correto |

**Risco residual (baixo):** o algoritmo `HS256` usa chave simétrica — a mesma chave assina e verifica o token. Para produção, recomenda-se migrar para `RS256` (assimétrico).

---

### 2.2 Injeção de SQL

**Status: Protegido**

O projeto utiliza SQLAlchemy ORM para todas as operações de banco de dados. Queries parametrizadas são geradas automaticamente — não há concatenação manual de strings SQL em nenhum ponto do código.

O único ponto de atenção é o relatório de tempo médio, que usa `func.extract` e `func.avg` — ambos são métodos nativos do SQLAlchemy, sem SQL raw.

---

### 2.3 Validação de Dados de Entrada

**Status: Implementado**

| Campo | Validação |
|---|---|
| CPF | Algoritmo de dígito verificador (módulo 11) no Value Object `CPF` |
| CNPJ | Algoritmo de dígito verificador no Value Object `CNPJ` |
| Placa | Regex que aceita apenas formatos antigo e Mercosul |
| Campos obrigatórios | Pydantic aplica validação automática em todos os schemas |
| Valores monetários | `Decimal` — sem risco de ponto flutuante |

---

### 2.4 Exposição de Informações Sensíveis

**Status: Adequado para MVP**

| Item | Status |
|---|---|
| `.env` no `.gitignore` | Sim — credenciais não são versionadas |
| `SECRET_KEY` em variável de ambiente | Sim — não hardcoded |
| Stack traces na API | FastAPI retorna mensagens de erro sem expor stack traces em produção |
| Senha do usuário | Nunca retornada em nenhum endpoint |
| Credenciais SMTP | Em variáveis de ambiente; se não configuradas, notificações são silenciosas |

**Risco residual (médio):** mensagens de erro de domínio (`TransicaoInvalidaError`, etc.) são retornadas ao cliente com detalhes internos. Em produção, recomenda-se mapear para mensagens genéricas para contextos externos.

---

### 2.5 OWASP Top 10 — Avaliação

| # | Categoria | Status | Observação |
|---|---|---|---|
| A01 | Broken Access Control | Mitigado | JWT + controle por perfil (ADMIN/MECANICO) em todas as rotas protegidas |
| A02 | Cryptographic Failures | Mitigado | bcrypt para senhas; JWT com chave de ambiente |
| A03 | Injection | Mitigado | SQLAlchemy ORM — sem SQL raw |
| A04 | Insecure Design | Mitigado | Regras de negócio encapsuladas nos aggregates |
| A05 | Security Misconfiguration | Parcial | CORS não configurado (ver item 2.6) |
| A06 | Vulnerable Components | Não avaliado | Verificar periodicamente com `pip audit` |
| A07 | Auth Failures | Mitigado | bcrypt + JWT com expiração |
| A08 | Software Integrity Failures | Fora do escopo | Sem pipeline CI/CD no MVP |
| A09 | Logging Failures | Parcial | Sem log estruturado de eventos de segurança |
| A10 | SSRF | Mitigado | Notificações via `smtplib` stdlib — sem URLs dinâmicas de usuário |

---

### 2.6 Vulnerabilidades Identificadas na Análise Manual

#### VUL-001 — CORS não configurado
**Severidade:** Média  
**Descrição:** O FastAPI não tem política CORS definida. Qualquer origem pode fazer requisições à API a partir de um browser.  
**Recomendação:**
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["https://seu-dominio.com"],
                   allow_methods=["*"], allow_headers=["*"])
```

#### VUL-002 — Ausência de rate limiting
**Severidade:** Média  
**Descrição:** Não há limite de requisições por IP ou usuário. Endpoints de autenticação (`POST /auth/login`) estão vulneráveis a ataques de força bruta.  
**Recomendação:** Adicionar `slowapi` ou middleware de rate limiting em produção. Para MVP, mitigado pelo contexto interno (não é uma API pública).

#### VUL-003 — Secret Key sem validação de força
**Severidade:** Baixa  
**Descrição:** A `SECRET_KEY` é lida do `.env` sem verificação de comprimento mínimo. Uma chave fraca compromete todos os tokens JWT.  
**Recomendação:** Adicionar validação no `config.py`:
```python
@field_validator("secret_key")
def validar_secret_key(cls, v):
    if len(v) < 32:
        raise ValueError("SECRET_KEY deve ter ao menos 32 caracteres")
    return v
```

#### VUL-004 — Ausência de headers de segurança HTTP
**Severidade:** Baixa  
**Descrição:** A API não define headers como `X-Content-Type-Options`, `X-Frame-Options` ou `Strict-Transport-Security`.  
**Recomendação:** Adicionar middleware de headers de segurança (`secure` library) em produção.

---

### 2.7 Achado do Scan Automatizado (Bandit)

#### B110 — try/except/pass em `src/shared/notificacoes.py:20`
**Severidade Bandit:** Low  
**Confiança:** High  
**CWE:** CWE-703  
**Descrição:** O bloco `except Exception: pass` na função `enviar_email` suprime silenciosamente todas as exceções de envio SMTP.  
**Justificativa:** Comportamento intencional — falha de e-mail não deve interromper o fluxo principal da OS. O sistema de notificações é um efeito colateral opcional; a resiliência do workflow de atendimento tem prioridade.  
**Ação:** Aceito como risco calculado (`#nosec B110` pode ser adicionado para suprimir o aviso em futuras versões se necessário).

---

## 3. Resumo Executivo

| Severidade | Quantidade | Status |
|---|---|---|
| Alta | 0 | — |
| Média | 2 | VUL-001 (CORS), VUL-002 (rate limiting) |
| Baixa | 3 | VUL-003 (secret key), VUL-004 (HTTP headers), B110 (try/except/pass intencional) |

O código não apresenta vulnerabilidades de alta severidade. As vulnerabilidades identificadas são comuns em MVPs e mitigáveis antes de um deploy em produção. Os controles críticos — autenticação, hash de senhas, prevenção de SQL injection e validação de dados sensíveis — estão corretamente implementados.

---

## 4. Comandos para reproduzir o scan

```bash
# Instalar bandit
pip install bandit

# Rodar scan completo
bandit -r src/ -f txt

# Exportar relatório em JSON
bandit -r src/ -f json -o relatorio-bandit.json

# Verificar dependências com vulnerabilidades conhecidas
pip audit
```
