# Oficina Mecânica API — Fase 2

[![Quality gate](https://sonarcloud.io/api/project_badges/quality_gate?project=jcontiero_posfiaparch_fase01&token=b4911515593a102dd125f01015779211089bbd21)](https://sonarcloud.io/summary/new_code?id=jcontiero_posfiaparch_fase01)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=jcontiero_posfiaparch_fase01&metric=coverage&token=b4911515593a102dd125f01015779211089bbd21)](https://sonarcloud.io/summary/new_code?id=jcontiero_posfiaparch_fase01)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=jcontiero_posfiaparch_fase01&metric=vulnerabilities&token=b4911515593a102dd125f01015779211089bbd21)](https://sonarcloud.io/summary/new_code?id=jcontiero_posfiaparch_fase01)

Sistema Integrado de Atendimento e Execução de Serviços — Tech Challenge da Pós Tech em Arquitetura de Software (FIAP, Fase 2).

---

## 1. Objetivos da Fase 2

A Fase 2 evoluiu o MVP inicial para uma arquitetura escalável, resiliente e automatizada:

- **Clean Architecture / Hexagonal:** separação clara entre domínio, aplicação, infraestrutura e apresentação, com ports/adapters e injeção de dependências.
- **APIs de Ordem de Serviço:** abertura unificada, consulta de status, aprovação externa, listagem ordenada e webhook de atualização por e-mail.
- **Containerização:** Dockerfile multi-stage, usuário não-root, health check e separação de migrations/seeds.
- **Orquestração:** manifestos Kubernetes completos em `/k8s` (Deployment, Service, HPA, ConfigMap, Secret, Job, PVC, Postgres).
- **Infraestrutura como Código:** scripts Terraform modulares em `/infra` provisionando cluster kind, PostgreSQL via Helm e registry local.
- **CI/CD:** pipeline GitHub Actions com lint, testes, cobertura, SonarQube, build/push Docker, Terraform, deploy no Kubernetes e migrations.

---

## 2. Arquitetura

### 2.1 Visão geral

```
┌─────────────────────────────────────────────────────────────┐
│                        GitHub Actions                        │
│  lint → testes → cobertura → build Docker → Terraform → K8s │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Cluster Kubernetes                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  API Pods   │  │  PostgreSQL │  │   Registry Local    │  │
│  │  (HPA)      │  │  (Helm)     │  │   (Docker)          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Estrutura do código

```
src/
├── main.py                 # Ponto de entrada FastAPI
├── container.py            # Container de injeção de dependências
├── config.py               # Configurações via pydantic-settings
├── shared/                 # Utilitários e exceções HTTP genéricas
├── identidade/             # Autenticação JWT
├── atendimento/            # Clientes, Veículos, Ordens de Serviço
├── catalogo/               # Catálogo de Serviços
├── estoque/                # Peças e controle de estoque
└── relatorios/             # Relatórios
    ├── dominio/
    ├── aplicacao/
    ├── infraestrutura/
    └── apresentacao/
```

### 2.3 Camadas (Clean Architecture)

- **Domínio:** entidades, value objects, exceções e regras puras.
- **Aplicação:** casos de uso e ports (interfaces).
- **Infraestrutura:** adapters (SQLAlchemy, JWT, bcrypt, SMTP).
- **Apresentação:** rotas FastAPI + schemas Pydantic.

---

## 3. Stack tecnológica

| Camada | Tecnologia |
|---|---|
| Framework | FastAPI + Uvicorn |
| ORM + migrations | SQLAlchemy 2.0 + Alembic (preparado) |
| Banco de dados | PostgreSQL 16 |
| Testes | pytest, pytest-cov, httpx |
| Lint/Format | ruff, black |
| Container | Docker + Docker Compose |
| Orquestração | Kubernetes |
| IaC | Terraform |
| CI/CD | GitHub Actions |
| Registry | Docker Hub (produção) / registry local (dev) |

---

## 4. Como executar

### 4.1 Pré-requisitos

- Docker e Docker Compose
- Terraform 1.5+
- kubectl
- kind (opcional, para provisionamento via Terraform)

### 4.2 Execução local com Docker Compose

```bash
# 1. Clone o repositório
git clone git@github.com:jcontiero/posfiaparch.git
cd posfiaparch

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env e defina uma SECRET_KEY segura

# 3. Suba o ambiente completo
docker-compose up -d

# 4. Aplique as migrations do Alembic
docker compose --profile tools run migrate

# 5. (Opcional) Popule dados iniciais
docker compose --profile tools run seed
```

A API estará disponível em `http://localhost:8000`.  
Documentação interativa (Swagger): `http://localhost:8000/docs`

### 4.3 Provisionamento com Terraform (cluster kind local)

```bash
cd infra

terraform init
terraform plan -var-file=environments/local.tfvars
terraform apply -var-file=environments/local.tfvars
```

Após o apply, configure o kubectl:

```bash
export KUBECONFIG=$(pwd)/kubeconfig
kubectl cluster-info
```

### 4.4 Deploy no Kubernetes

Com o cluster configurado:

```bash
# Aplique os manifestos
kubectl apply -f k8s/

# Aguarde o rollout
kubectl rollout status deployment/oficina-api -n oficina-api

# Aplique as migrations
kubectl apply -f k8s/job-migrate.yaml
```

Para acessar a API localmente via port-forward:

```bash
kubectl port-forward -n oficina-api svc/oficina-api 8080:80
curl http://localhost:8080/health
```

---

## 5. APIs obrigatórias da Fase 2

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/login` | Autenticar usuário |
| POST | `/ordens-de-servico` | Abertura unificada (cliente, veículo, serviços, peças) |
| GET | `/ordens-de-servico/{id}/status` | Consultar status atual da OS |
| POST | `/ordens-de-servico/{id}/aprovacao` | Aprovar ou recusar orçamento |
| GET | `/ordens-de-servico` | Listagem ordenada das OS ativas |
| POST | `/webhooks/os/{id}/atualizar-status` | Atualização de status via token no link do e-mail |

> Collection completa disponível em: `docs/collection-postman.json`  
> Documentação Swagger disponível em: `http://localhost:8000/docs`

### 5.1 Status da OS

```
RECEBIDA → EM_DIAGNOSTICO → AGUARDANDO_ORCAMENTO → AGUARDANDO_APROVACAO
                                                    → EM_EXECUCAO
                                                      → SERVICOS_CONCLUIDOS
                                                        → FINALIZADA
                                                          → ENTREGUE
```

---

## 6. Testes

```bash
# Suba o banco de dados
docker-compose up db -d

# Crie o banco de testes
docker exec -it <container_db> psql -U oficina_user -c "CREATE DATABASE oficina_test;"

# Execute todos os testes com cobertura
pytest --cov=src --cov-report=term-missing

# Apenas testes unitários
pytest tests/unit/
```

Cobertura mínima: **80%** nas camadas `dominio/` e `aplicacao/`.

---

## 7. CI/CD

A pipeline `Build and Deploy` é executada em pushes para `main`/`tech_challenge` e em pull requests.

Ordem dos jobs:

1. `lint-and-format` — ruff + black
2. `unit-tests`
3. `integration-tests` — com PostgreSQL
4. `coverage-and-sonar` — pytest-cov + SonarQube
5. `docker-build-push` — build e push para Docker Hub
6. `terraform` — plan/apply
7. `deploy-k8s` — `kubectl apply -f k8s/`
8. `migrate` — `kubectl apply -f k8s/job-migrate.yaml`

Configure os secrets em:  
`Settings > Secrets and variables > Actions`

Secrets esperados: `SONAR_TOKEN`, `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `KUBE_CONFIG`.

---

## 8. Entregáveis da Fase 2

- [x] Código refatorado com Clean Architecture/Hexagonal
- [x] APIs de Ordem de Serviço da Fase 2
- [x] Dockerfile e docker-compose revisados
- [x] Manifestos Kubernetes em `/k8s`
- [x] Infraestrutura como Código em `/infra`
- [x] Pipeline CI/CD em `.github/workflows/build.yml`
- [x] README atualizado
- [x] Collection de APIs em `docs/collection-postman.json`
---

## 9. Contato

Projeto desenvolvido por **Jonas Vasconcelos** como Tech Challenge da FIAP Pós Tech em Arquitetura de Software.
