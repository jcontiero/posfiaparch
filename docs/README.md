# Documentação — Oficina Mecânica API

Documentação técnica do Tech Challenge — Pos Tech Arquitetura de Software (FIAP, Fase 1).

---

## Estrutura

```
docs/
├── adr/                          # Architecture Decision Records
│   ├── ADR-001-banco-de-dados.md     Justificativa da escolha do PostgreSQL
│   └── ADR-002-arquitetura.md        Justificativa da arquitetura em camadas + DDD
│
└── relatorios/                   # Relatórios obrigatórios da entrega
    ├── relatorio-vulnerabilidades.md   Análise de segurança (Bandit + manual)
    └── relatorio-cobertura-testes.md   Cobertura de testes (85.23% — mín. 80%)
```

---

## ADRs

Registram as decisões arquiteturais significativas com contexto, alternativas avaliadas e justificativas. Devem ser lidos antes de qualquer refatoração da stack.

## Relatórios

Entregáveis obrigatórios conforme o enunciado do Tech Challenge. Incluem análise de vulnerabilidades do código e resultado da cobertura de testes automatizados.
