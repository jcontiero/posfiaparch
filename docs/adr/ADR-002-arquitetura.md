# ADR-002 — Escolha da Arquitetura

**Projeto:** Sistema de Oficina Mecânica — FIAP Pos Tech Fase 1
**Status:** Aceito
**Data:** 2026-04
**Autor:** Jonas Vasconcelos

---

## Contexto

O enunciado do Tech Challenge especifica:

> "Back-end monolítico. Como será um MVP, é possível criar um Monolito utilizando a arquitetura em camadas."

O requisito define tanto o estilo arquitetural (monolito em camadas) quanto a abordagem de modelagem (DDD). O que está em aberto é **como implementar** o monolito em camadas seguindo DDD dentro do prazo.

---

## Alternativas consideradas

### Layered Architecture clássica (Evans 2003)

Quatro camadas fixas: Presentation → Application → Domain → Infrastructure.

**Prós:**
- Corresponde diretamente ao requisito do enunciado
- Simples de entender e implementar
- Sem necessidade de frameworks especializados

**Contras:**
- A camada de domínio pode acidentalmente depender de infraestrutura se não houver disciplina

---

### Hexagonal Architecture (Ports & Adapters — Cockburn 2005)

O domínio fica no centro. Toda comunicação com o exterior passa por interfaces (ports) e implementações (adapters).

**Prós:**
- Domínio completamente isolado por design
- Testabilidade máxima

**Contras:**
- Não é o requisito do enunciado
- Mais abstrações — complexidade desnecessária para o escopo do MVP

---

### Clean Architecture (Martin 2017)

Variante da hexagonal com quatro anéis concêntricos e Dependency Rule rígida.

**Prós:**
- Muito bem documentada e testada em projetos grandes

**Contras:**
- Não é o requisito do enunciado
- Overhead de DTOs entre camadas excessivo para um MVP

---

## Decisão

**"Layered Architecture with DDD flavour"** — arquitetura em camadas conforme Evans (2003), com:

1. Quatro camadas: `dominio`, `aplicacao`, `infraestrutura`, `apresentacao`
2. Regras de dependência explícitas (ver tabela abaixo)
3. Bounded Contexts como módulos Python em `src/`
4. Aggregates protegendo invariantes de domínio
5. Value Objects imutáveis para conceitos sem identidade

---

## Estrutura de camadas no código

```
src/{modulo}/
├── dominio/          ← Entidades, Aggregates, Value Objects, Domain Exceptions
├── aplicacao/        ← Use Cases (orquestram domínio, sem regras de negócio)
├── infraestrutura/   ← SQLAlchemy models + repositórios concretos
└── apresentacao/     ← FastAPI routers + Pydantic schemas
```

---

## Regras de dependência entre camadas

| Camada | Pode importar | Nunca importa |
|---|---|---|
| `dominio/` | Stdlib Python (`dataclasses`, `enum`, `uuid`, `datetime`) | FastAPI, SQLAlchemy, Pydantic |
| `aplicacao/` | `dominio/` do mesmo módulo, interfaces de repositório | FastAPI, SQLAlchemy |
| `infraestrutura/` | `dominio/` (para implementar interfaces), SQLAlchemy | FastAPI, Use Cases |
| `apresentacao/` | `aplicacao/` (Use Cases), Pydantic, FastAPI | SQLAlchemy, `dominio/` direto |

**Regra transversal:** Um módulo nunca importa classes internas de outro módulo. A comunicação entre bounded contexts ocorre via injeção de repositórios nos use cases.

---

## Fluxo de uma requisição HTTP

Exemplo: `POST /ordens-de-servico/{id}/adicionar-peca`

```
1. HTTP Request chega ao FastAPI router (apresentacao/)
2. Pydantic valida o body → AdicionarPecaRequest
3. Depends(get_usuario_atual) decodifica JWT → verifica perfil
4. Router instancia AdicionarPeca (aplicacao/) injetando
   OrdemDeServicoRepositorioImpl + PecaRepositorioImpl
5. Use Case busca a OS e a Peça via repositórios
6. Peca.reservar(quantidade) → aggregate valida invariante
   (se estoque insuficiente → EstoqueInsuficienteError → HTTP 422)
7. Use Case adiciona ItemPeca à OS e persiste ambos
8. Router serializa aggregate → OsResponse (Pydantic)
9. FastAPI retorna HTTP 200 com JSON
```

---

## Stack tecnológica

| Componente | Tecnologia | Papel |
|---|---|---|
| Linguagem | Python 3.12 | Runtime |
| Framework web | FastAPI 0.115 | HTTP, validação, Swagger automático |
| Validação | Pydantic 2 | Schemas de entrada/saída |
| ORM | SQLAlchemy 2.0 (sync) | Mapeamento objeto-relacional |
| Banco de dados | PostgreSQL 16 | Persistência |
| Driver | pg8000 | Conexão puro-Python com PostgreSQL (ARM64) |
| Autenticação | PyJWT 2.8 | JWT encode/decode |
| Hash de senha | bcrypt 4.0 | Hash seguro de senhas |
| Notificações | smtplib (stdlib) | E-mails transacionais — sem dependências externas |
| Servidor | uvicorn 0.30 | WSGI server |
| Contêiner | Docker + Compose | Ambiente reproduzível |
| Testes | pytest + pytest-cov | Framework de testes (cobertura mín. 80%) |

---

## Consequências

### Positivas

- **Alinhamento com o enunciado**: A escolha atende literalmente ao requisito do PDF.
- **Separação de responsabilidades verificável**: A estrutura de pastas torna visível qualquer violação das regras de dependência.
- **Testabilidade do domínio**: Como `dominio/` não depende de nada externo, testes unitários são pytest puro sem mocks de banco ou HTTP.

### Negativas

- **Verbosidade**: A separação aggregate ↔ model introduz código adicional comparado a um CRUD simples.
- **Disciplina necessária**: Python não impõe barreiras de import — a regra "domínio não importa SQLAlchemy" é por convenção, não técnica.

---

## Referências

- Evans, Eric. *Domain-Driven Design: Tackling Complexity in the Heart of Software*. Addison-Wesley, 2003.
- Martin, Robert C. *Clean Architecture*. Prentice Hall, 2017.
- Cockburn, Alistair. *Hexagonal Architecture*. 2005.

---

**Anterior:** [ADR-001 — Banco de Dados](./ADR-001-banco-de-dados.md)  
**Próximo:** [ADR-003 — Notificações via smtplib](./ADR-003-notificacoes.md)  
