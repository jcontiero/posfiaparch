# ADR-001 — Escolha do Banco de Dados

**Projeto:** Sistema de Oficina Mecânica — FIAP Pos Tech Fase 1
**Status:** Aceito
**Data:** 2026-04
**Autor:** Jonas Vasconcelos

---

## Contexto

O sistema de oficina mecânica gerencia dados com as seguintes características:

- **Dados relacionais**: Clientes têm Veículos. Veículos têm Ordens de Serviço. OSs têm Serviços e Peças. As relações são explícitas e com cardinalidade definida.
- **Requisito de integridade**: Uma peça reservada em uma OS não pode ser reservada além do estoque disponível. Isso exige controle transacional (ACID) para evitar race conditions.
- **Consultas analíticas**: O módulo de relatórios precisa de queries com `JOIN`, `GROUP BY`, `AVG` e filtros por período — padrão SQL.
- **Consistência de dados**: O histórico de OSs é imutável depois de `ENTREGUE`. Alterações em registros financeiros (orçamentos) requerem garantia de durabilidade.

---

## Alternativas consideradas

### PostgreSQL 16

**Prós:**
- ACID completo com suporte a transações aninhadas (savepoints)
- Suporte nativo a UUID, JSONB, arrays, enums customizados
- Suporte a `CHECK CONSTRAINTS` para reforçar regras de domínio no banco
- Open source, sem licença, bem suportado na AWS/GCP/Azure

**Contras:**
- Necessita de instância dedicada (não é embedded)
- Configuração inicial mais complexa que SQLite

---

### MySQL 8 / MariaDB

**Prós:**
- Amplamente adotado, boa documentação
- Performance comparável ao PostgreSQL para workloads simples

**Contras:**
- Suporte a tipos avançados (UUID nativo, enums flexíveis) inferior ao PostgreSQL
- Comportamento padrão de `NULL` e charset histórico causam surpresas

---

### MongoDB

**Prós:**
- Schema flexível — útil quando o modelo muda frequentemente
- Bom para documentos aninhados

**Contras:**
- O modelo de dados do projeto é fortemente relacional — MongoDB forçaria desnormalização artificial
- Transações multi-documento são suportadas mas com overhead significativo e sintaxe complexa
- Não é relacional — dificulta as queries analíticas do módulo de relatórios

---

### SQLite

**Prós:**
- Zero configuração, embedded, ideal para testes
- Excelente para desenvolvimento local rápido

**Contras:**
- Sem suporte a concorrência de escritas (lock de arquivo)
- Não é adequado para produção com múltiplos workers
- Tipos nativos (UUID, ENUM) não suportados — geraria incompatibilidade com PostgreSQL em testes

---

## Decisão

**PostgreSQL 16** com driver `pg8000` e ORM `SQLAlchemy 2.0` (modo síncrono).

### Justificativas objetivas

1. **ACID garante as invariantes de estoque** — A regra "quantidade disponível nunca negativa" precisa de transações para resistir a requisições concorrentes. O PostgreSQL oferece `SELECT FOR UPDATE` e isolamento `SERIALIZABLE` sem configuração adicional.

2. **UUID nativo reduz código** — UUID como tipo nativo evita conversão manual. O enum `StatusOS` é armazenado como `VARCHAR` com `native_enum=False` para evitar problemas de `ALTER TYPE` ao adicionar novos valores — a integridade é garantida pelo domínio, não pelo banco.

3. **TypeDecorators para VOs** — `CPF`, `CNPJ` e `Placa` são armazenados como `VARCHAR` no banco, mas as entidades de domínio carregam os tipos VO diretamente (`Cliente.cpf: CPF | None`). `CPFType`, `CNPJType` e `PlacaType` em `modelos.py` convertem automaticamente VO↔string no `process_bind_param` / `process_result_value`, sem expor a string ao domínio.

3. **pg8000 — driver puro Python** — Compatível com ARM64 (Apple Silicon / Colima) sem dependências nativas. A escolha pelo driver síncrono simplifica o código para o escopo do MVP.

4. **SQLAlchemy 2.0** — ORM maduro, documentado e compatível com `pg8000`. `Base.metadata.create_all()` no startup da aplicação cria as tabelas automaticamente — sem Alembic, suficiente para o MVP.

---

## Consequências

### Positivas

- Banco de dados confiável e performático para o modelo relacional do sistema
- Suporte a tipos avançados reduz validações redundantes no código
- Docker facilita reprodução do ambiente completo
- PostgreSQL de teste (banco separado `oficina_test`) garante testes realistas

### Negativas

- Docker obrigatório para desenvolvimento local (ou instalação nativa do PostgreSQL)
- `pg8000` é mais lento que `psycopg2` — aceitável para MVP, considerar troca em produção

---

## Configuração de referência

### docker-compose.yml (fragmento)

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: oficina_user
      POSTGRES_PASSWORD: oficina_pass
      POSTGRES_DB: oficina_db
    ports:
      - "5432:5432"
```

### .env

```bash
DATABASE_URL=postgresql+pg8000://oficina_user:oficina_pass@localhost:5432/oficina_db
TEST_DATABASE_URL=postgresql+pg8000://oficina_user:oficina_pass@localhost:5432/oficina_test
```

### src/shared/banco.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from src.config import configuracoes

engine = create_engine(configuracoes.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass
```

---

## Referências

- PostgreSQL 16 Documentation: postgresql.org/docs/16/
- pg8000: github.com/tlocke/pg8000
- SQLAlchemy 2.0: docs.sqlalchemy.org/en/20/

---

**Próximo:** [ADR-002 — Arquitetura](./ADR-002-arquitetura.md)
