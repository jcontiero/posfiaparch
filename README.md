# Oficina Mecânica API

[![Quality gate](https://sonarcloud.io/api/project_badges/quality_gate?project=jcontiero_posfiaparch_fase01&token=b4911515593a102dd125f01015779211089bbd21)](https://sonarcloud.io/summary/new_code?id=jcontiero_posfiaparch_fase01)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=jcontiero_posfiaparch_fase01&metric=coverage&token=b4911515593a102dd125f01015779211089bbd21)](https://sonarcloud.io/summary/new_code?id=jcontiero_posfiaparch_fase01)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=jcontiero_posfiaparch_fase01&metric=vulnerabilities&token=b4911515593a102dd125f01015779211089bbd21)](https://sonarcloud.io/summary/new_code?id=jcontiero_posfiaparch_fase01)

Sistema Integrado de Atendimento e Execução de Serviços — MVP back-end desenvolvido como Tech Challenge da Pós Tech em Arquitetura de Software (FIAP, Fase 1).

## Sobre o projeto

API RESTful para gerenciamento de uma oficina mecânica, cobrindo o ciclo completo de Ordens de Serviço: abertura, diagnóstico, orçamento, execução e entrega. Desenvolvido com **Python + FastAPI + PostgreSQL**, aplicando **Domain-Driven Design (DDD)** e arquitetura em camadas.

## Requisitos

- Docker e Docker Compose
- Python 3.12+ (apenas para desenvolvimento local sem Docker)

## Como executar

### Com Docker (recomendado)

```bash
# 1. Clone o repositório
git clone git@github.com:jcontiero/posfiaparch.git
cd posfiaparch

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env e defina uma SECRET_KEY segura

# 3. Suba o ambiente completo
docker-compose up --build
```

A API estará disponível em `http://localhost:8000`.  
Documentação interativa (Swagger): `http://localhost:8000/docs`

### Desenvolvimento local (sem Docker)

```bash
# Instale as dependências
pip install uv
uv pip install -e ".[dev]"

# Suba apenas o banco de dados
docker-compose up db

# Configure o .env
cp .env.example .env

# Inicie a API (tabelas criadas automaticamente no startup)
uvicorn src.main:app --reload
```

## Variáveis de ambiente

| Variável | Descrição | Exemplo |
|---|---|---|
| `DATABASE_URL` | URL de conexão PostgreSQL (driver pg8000) | `postgresql+pg8000://user:pass@localhost:5432/oficina_db` |
| `SECRET_KEY` | Chave para assinatura JWT | string aleatória longa |
| `ALGORITHM` | Algoritmo JWT | `HS256` |
| `TOKEN_EXPIRE_HORAS` | Expiração do token em horas | `8` |
| `SMTP_HOST` | Servidor SMTP para notificações | `smtp.gmail.com` |
| `SMTP_PORT` | Porta SMTP | `587` |
| `SMTP_USER` | Usuário SMTP (e-mail da conta) | `seu@email.com` |
| `SMTP_PASSWORD` | Senha de app SMTP | senha gerada na conta |
| `EMAIL_REMETENTE` | E-mail de origem das notificações | `noreply@suaoficina.com` |
| `EMAIL_ADMIN` | E-mail do Atendente/Admin para notificações | `admin@suaoficina.com` |


---

## Testes

```bash
# Suba o banco de teste
docker-compose up db -d

# Crie o banco de teste (primeira vez)
docker exec -it <container_db> psql -U oficina_user -c "CREATE DATABASE oficina_test;"

# Execute os testes com cobertura
pytest --cov=src --cov-report=term-missing

# Apenas testes unitários (sem banco)
pytest tests/unit/
```

Cobertura mínima: **80%** nos domínios críticos.

## Arquitetura

Monolito com **Layered Architecture + DDD**, organizado em 5 módulos:

```
src/
├── identidade/     # Autenticação JWT
├── atendimento/    # Clientes, Veículos e Ordens de Serviço
├── catalogo/       # Catálogo de Serviços
├── estoque/        # Peças e Insumos
└── relatorios/     # Tempo médio de execução
```

Cada módulo segue: `dominio/` → `aplicacao/` → `infraestrutura/` → `apresentacao/`.

## Endpoints principais

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| POST | `/auth/login` | Não | Autenticar usuário |
| POST | `/clientes` | ADMIN | Cadastrar cliente |
| POST | `/veiculos` | ADMIN | Cadastrar veículo |
| POST | `/ordens-de-servico` | ADMIN | Abrir OS |
| POST | `/ordens-de-servico/{id}/iniciar-diagnostico` | MECANICO | Iniciar diagnóstico |
| POST | `/ordens-de-servico/{id}/finalizar-diagnostico` | MECANICO | Finalizar diagnóstico → notifica Admin |
| POST | `/ordens-de-servico/{id}/adicionar-servico` | ADMIN | Adicionar serviço à OS |
| POST | `/ordens-de-servico/{id}/adicionar-peca` | ADMIN | Adicionar peça à OS (reserva estoque) |
| POST | `/ordens-de-servico/{id}/gerar-orcamento` | ADMIN | Gerar orçamento → notifica Cliente |
| GET | `/ordens-de-servico/{id}/acompanhar` | **Não** | Acompanhamento público |
| POST | `/ordens-de-servico/{id}/aprovar-orcamento` | **Não** | Aprovar orçamento |
| POST | `/ordens-de-servico/{id}/recusar-orcamento` | **Não** | Recusar orçamento (libera estoque) |
| GET | `/ordens-de-servico/{id}/itens` | MECANICO | ML: listar itens de serviço da OS (pendentes ou todos) |
| POST | `/ordens-de-servico/{id}/executar-servico/{item_id}` | MECANICO | Executar serviço |
| POST | `/ordens-de-servico/{id}/finalizar` | ADMIN | Finalizar OS (controle de qualidade) → notifica Cliente |
| POST | `/ordens-de-servico/{id}/entregar` | ADMIN | Entregar veículo |
| POST | `/pecas/{id}/repor-estoque` | ADMIN | Repor estoque |
| GET | `/relatorios/tempo-medio-servicos` | ADMIN | Tempo médio por serviço |

Documentação completa dos 38 endpoints disponível no Swagger em `/docs`.

> **Controle de estoque integrado:** peças são adicionadas ao orçamento sem verificar estoque. A reserva ocorre na **aprovação do orçamento** — se o estoque for insuficiente, a aprovação retorna 422. Alertas de estoque abaixo do mínimo são notificados ao Admin após a reserva.

> **Notificações por e-mail (smtplib):** disparadas automaticamente pelos use cases. Se `SMTP_USER` não estiver configurado, ignoradas silenciosamente.
>
> | Evento | Destinatário |
> |---|---|
> | Diagnóstico concluído | Admin |
> | Orçamento gerado | Cliente |
> | Orçamento recusado pelo cliente | Admin |
> | Todos os serviços concluídos | Admin |
> | OS finalizada — veículo pronto | Cliente |
> | Estoque reposto | Admin |

### Ciclo de vida da OS

```
RECEBIDA
  → EM_DIAGNOSTICO
    → AGUARDANDO_ORCAMENTO
      → AGUARDANDO_APROVACAO ──→ CANCELADA (orçamento recusado)
        → EM_EXECUCAO
          → SERVICOS_CONCLUIDOS
            → FINALIZADA
              → ENTREGUE
```

### Perfis de acesso

| Perfil | Permissões |
|---|---|
| `ADMIN` | Tudo — inclui ações de Atendente/Admin |
| `MECANICO` | Iniciar diagnóstico, finalizar diagnóstico, executar serviço |

## Stack tecnológica

| Componente | Tecnologia |
|---|---|
| Framework | FastAPI 0.115 |
| Banco de dados | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 |
| Migrations | SQLAlchemy `create_all()` no startup — `TypeDecorator` para VOs CPF/CNPJ/Placa |
| Autenticação | JWT (PyJWT + bcrypt) |
| Notificações | smtplib — stdlib Python |
| Testes | pytest + pytest-cov |
| Container | Docker + Docker Compose |
