# Relatório de Cobertura de Testes

**Projeto:** Oficina Mecânica API  
**Data:** 2026-04-29  
**Ferramenta:** pytest-cov 7.x  
**Cobertura total:** 87,07% — acima do mínimo exigido (80%)

---

## Resultado

```
95 passed, 1 warning
Required test coverage of 80% reached. Total coverage: 87.07%
```

---

## Cobertura por módulo

| Módulo | Stmts | Miss | Cobertura |
|---|---|---|---|
| `src/identidade/dominio/` | — | — | **100%** |
| `src/identidade/infraestrutura/` | — | — | **100%** |
| `src/identidade/apresentacao/` | — | — | **100%** |
| `src/identidade/aplicacao/` | — | — | **100%** |
| `src/atendimento/dominio/entidades.py` | 107 | 2 | 98% |
| `src/atendimento/dominio/value_objects.py` | 64 | 2 | 97% |
| `src/estoque/infraestrutura/repositorios.py` | 42 | 1 | 98% |
| `src/atendimento/infraestrutura/modelos.py` | 62 | 0 | 100% |
| `src/atendimento/infraestrutura/repositorios.py` | 129 | 21 | 84% |
| `src/catalogo/apresentacao/rotas.py` | 47 | 5 | 89% |
| `src/catalogo/aplicacao/casos_de_uso.py` | 48 | 6 | 88% |
| `src/estoque/dominio/entidades.py` | 25 | 0 | 100% |
| `src/atendimento/aplicacao/casos_de_uso.py` | 269 | 60 | 78% |
| `src/estoque/aplicacao/casos_de_uso.py` | 71 | 23 | 68% |
| `src/estoque/apresentacao/rotas.py` | 50 | 10 | 80% |
| `src/atendimento/apresentacao/schemas.py` | 115 | 0 | 100% |
| `src/atendimento/apresentacao/rotas.py` | 199 | 82 | 59% |
| `src/relatorios/apresentacao/rotas.py` | 21 | 9 | 57% |
| `src/shared/dependencias.py` | 25 | 8 | 68% |
| `src/shared/excecoes_http.py` | 12 | 5 | 58% |
| `src/shared/notificacoes.py` | 59 | 0 | **100%** |
| **TOTAL** | **1807** | **231** | **87,21%** |

---

## Suíte de testes

### Testes unitários (sem banco, sem HTTP)

| Arquivo | Testes | Resultado |
|---|---|---|
| `tests/unit/atendimento/test_value_objects.py` | 12 | ✅ Todos passando |
| `tests/unit/atendimento/test_ordem_de_servico.py` | 13 | ✅ Todos passando |
| `tests/unit/atendimento/test_cliente.py` | 4 | ✅ Todos passando |
| `tests/unit/estoque/test_peca.py` | 11 | ✅ Todos passando |
| `tests/unit/identidade/test_autenticacao.py` | 3 | ✅ Todos passando |
| `tests/unit/shared/test_notificacoes.py` | 11 | ✅ Todos passando |
| **Subtotal unitários** | **54** | ✅ |

### Testes de integração (API + PostgreSQL)

| Arquivo | Testes | Resultado |
|---|---|---|
| `tests/integration/test_auth.py` | 3 | ✅ Todos passando |
| `tests/integration/test_clientes.py` | 10 | ✅ Todos passando |
| `tests/integration/test_catalogo.py` | 6 | ✅ Todos passando |
| `tests/integration/test_estoque.py` | 7 | ✅ Todos passando |
| `tests/integration/test_ordens_de_servico.py` | 12 | ✅ Todos passando |
| **Subtotal integração** | **38** | ✅ |

**Total: 95 testes — 0 falhas**

---

## Domínios críticos

Os módulos de domínio — que concentram as invariantes e regras de negócio — apresentam cobertura acima de 95%:

| Módulo | Cobertura |
|---|---|
| `atendimento/dominio/entidades.py` | 98% |
| `atendimento/dominio/value_objects.py` | 97% |
| `estoque/dominio/entidades.py` | 100% |
| `identidade/dominio/` | 100% |

Os testes unitários de OS cobrem o fluxo completo de 9 status: `RECEBIDA → EM_DIAGNOSTICO → AGUARDANDO_ORCAMENTO → AGUARDANDO_APROVACAO → EM_EXECUCAO → SERVICOS_CONCLUIDOS → FINALIZADA → ENTREGUE`, além do fluxo de cancelamento.

---

## Áreas com menor cobertura

| Módulo | Cobertura | Motivo |
|---|---|---|
| `relatorios/apresentacao/rotas.py` | 57% | Sem teste de integração para o relatório de tempo médio |
| `shared/excecoes_http.py` | 58% | Handlers globais não chamados diretamente nos testes |
| `atendimento/apresentacao/rotas.py` | 59% | Vários endpoints sem teste de integração dedicado |
| `shared/dependencias.py` | 68% | Fluxo de JWT inválido/expirado não coberto |

---

## Infraestrutura de testes

Os testes unitários não requerem banco de dados e executam em ~1 segundo. Os testes de integração utilizam banco dedicado `oficina_test` e são limpos automaticamente entre testes pela fixture `limpar_banco`.

A separação entre `tests/unit/` e `tests/integration/` garante que os testes unitários não dependam de PostgreSQL — `tests/integration/conftest.py` isola toda a configuração de banco.

---

## Comando para reproduzir

```bash
# Subir banco de dados
docker-compose up -d db

# Criar banco de testes (primeira vez)
docker-compose exec db psql -U oficina_user -d oficina_db \
  -c "CREATE DATABASE oficina_test OWNER oficina_user;"

# Rodar suíte completa com cobertura
pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Rodar apenas unit tests (sem banco)
pytest tests/unit/ -v

# Rodar apenas integração
TEST_DATABASE_URL=postgresql+pg8000://oficina_user:oficina_pass@localhost:5432/oficina_test \
pytest tests/integration/ -v
```
