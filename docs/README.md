# Documentação — Oficina Mecânica API

Documentação técnica do Tech Challenge — Pos Tech Arquitetura de Software (FIAP, Fase 2).

---

## Evolução para a Fase 2
Esta documentação reflete o estado do sistema após as refatorações arquiteturais da Fase 2, que incluíram:
- **Clean Architecture / Hexagonal**: Separação rigorosa de domínio e infraestrutura.
- **Orquestração e IaC**: Manifestos Kubernetes e scripts Terraform (`/k8s` e `/infra`).
- **CI/CD**: Pipeline automatizado no GitHub Actions.
- **APIs Expandidas**: Abertura de OS, consulta e aprovação externa.

---

## Estrutura

```
docs/
├── README.md                         Este arquivo
├── modelagem/
│   ├── context-map.excalidraw        Mapa de contextos delimitados
│   ├── domain-model.excalidraw       Modelo de domínio (entidades e agregados)
│   └── event-storming.excalidraw     Event storming do fluxo de OS
├── adr/
│   ├── ADR-001-banco-de-dados.md     Justificativa da escolha do PostgreSQL
│   ├── ADR-002-arquitetura.md        Justificativa da arquitetura em camadas + DDD
│   └── ADR-003-notificacoes.md       Justificativa da estratégia de notificações
└── relatorios/
    ├── relatorio-cobertura-testes.md   Cobertura de testes (mín. 80%)
    └── seguranca/
        ├── relatorio-vulnerabilidades.md   Análise de segurança (Bandit + manual)
        └── relatorio-zap.pdf               Relatório OWASP ZAP
```

---

## Linguagem Ubíqua

Vocabulário compartilhado entre especialistas de domínio e desenvolvedores. Os mesmos termos aparecem na conversa, no código, no banco de dados, nas URLs e nos logs. Nunca traduzir.

### Glossário

| Termo | Definição | Nunca usar |
|---|---|---|
| `Cliente` | Pessoa física (CPF) ou jurídica (CNPJ) que traz o veículo para a oficina | `User`, `Owner`, `Customer` |
| `Veiculo` | Automóvel pertencente a um Cliente, identificado pela placa | `Car`, `Auto`, `Vehicle` |
| `OrdemDeServico` | Documento central do ciclo de atendimento — da recepção à entrega | `ServiceRequest`, `Ticket`, `Job` |
| `Servico` | Trabalho técnico do catálogo (ex.: "Troca de óleo") | `Task`, `Activity`, `Work` |
| `ItemServico` | Cópia congelada de um Serviço dentro de uma OS, com preço e flag de conclusão | `ServiceItem`, `Task` |
| `Peca` | Componente físico do estoque utilizado durante a execução | `Item`, `Product`, `Part` |
| `ItemPeca` | Registro de Peça adicionada à OS com quantidade e preço congelados | `PartItem` |
| `Diagnostico` | Fase de análise do Veículo pelo mecânico | `Analysis`, `Inspection` |
| `Orcamento` | Valor total calculado automaticamente e enviado ao Cliente para aprovação | `Budget`, `Quote`, `Estimate` |
| `Aprovacao` | Ato pelo qual o Cliente aceita o Orçamento, autorizando a execução | `Confirmation`, `Authorization` |
| `Estoque` | Controle de quantidade disponível de cada Peça | `Inventory`, `Warehouse`, `Stock` |

### Regras de domínio dos termos principais

**Cliente**
- Pessoa física → identificada por CPF; pessoa jurídica → identificada por CNPJ
- Nunca ambos, nunca nenhum

**Veiculo**
- Placa é imutável após o cadastro
- Pertence a exatamente um Cliente
- Só pode ter uma OS ativa por vez

**OrdemDeServico**
- Abreviação aceita em variáveis locais: `os`; classes sempre por extenso: `OrdemDeServico`
- Serviços e Peças só são adicionáveis em `EM_DIAGNOSTICO` ou `AGUARDANDO_ORCAMENTO`
- Preço congelado no momento da adição (nunca editável depois)
- Reserva de estoque ocorre na aprovação do orçamento, não na adição da peça

---

### Ciclo de vida da Ordem de Serviço

```
RECEBIDA
  → EM_DIAGNOSTICO
    → AGUARDANDO_ORCAMENTO
      → AGUARDANDO_APROVACAO ──→ CANCELADA
        → EM_EXECUCAO
          → SERVICOS_CONCLUIDOS
            → FINALIZADA
              → ENTREGUE
```

| Status | Significado |
|---|---|
| `RECEBIDA` | Veículo entrou na oficina. OS aberta. Aguardando Diagnóstico. |
| `EM_DIAGNOSTICO` | Mecânico analisando. Serviços e Peças podem ser adicionados. |
| `AGUARDANDO_ORCAMENTO` | Diagnóstico concluído. Orçamento em elaboração pelo Admin. |
| `AGUARDANDO_APROVACAO` | Orçamento enviado. Aguardando resposta do Cliente. |
| `EM_EXECUCAO` | Cliente aprovou. Mecânicos executando os Serviços. |
| `SERVICOS_CONCLUIDOS` | Todos os Serviços concluídos. Aguardando finalização pelo Admin. |
| `FINALIZADA` | OS finalizada. Veículo pronto para retirada. |
| `ENTREGUE` | Veículo retirado. Ciclo encerrado. |
| `CANCELADA` | OS cancelada antes de FINALIZADA. |

### Transições válidas

| De | Para | Ação |
|---|---|---|
| `RECEBIDA` | `EM_DIAGNOSTICO` | `iniciar_diagnostico()` — MECANICO |
| `EM_DIAGNOSTICO` | `AGUARDANDO_ORCAMENTO` | `finalizar_diagnostico()` — MECANICO |
| `AGUARDANDO_ORCAMENTO` | `AGUARDANDO_APROVACAO` | `gerar_orcamento()` — ADMIN |
| `AGUARDANDO_APROVACAO` | `EM_EXECUCAO` | `aprovar_orcamento()` — público |
| `AGUARDANDO_APROVACAO` | `CANCELADA` | `recusar_orcamento()` — público |
| `EM_EXECUCAO` | `SERVICOS_CONCLUIDOS` | `executar_servico()` — MECANICO (automático no último) |
| `SERVICOS_CONCLUIDOS` | `FINALIZADA` | `finalizar_os()` — ADMIN (manual) |
| `FINALIZADA` | `ENTREGUE` | `entregar_veiculo()` — ADMIN |
| `RECEBIDA` | `CANCELADA` | `cancelar()` |
| `EM_DIAGNOSTICO` | `CANCELADA` | `cancelar()` |

---

### Mapa de relacionamentos

```
+----------+       1..*      +----------+
| Cliente  |---------------->| Veiculo  |
+----------+                 +----------+
                                  |
                                  | 0..*
                                  v
                          +-----------------+
                          | OrdemDeServico  |
                          +-----------------+
                               |        |
                          1..* |        | 0..*
                               v        v
                       +----------+  +----------+
                       |ItemServ. |  |ItemPeca  |
                       +----------+  +----------+
                            |              |
                            | N:1          | N:1
                            v              v
                       +----------+  +----------+
                       | Servico  |  |   Peca   |
                       |(Catalogo)|  | (Estoque)|
                       +----------+  +----------+
```

---

## ADRs

Registram decisões arquiteturais significativas com contexto, alternativas avaliadas e justificativas. Devem ser lidos antes de qualquer refatoração da stack.

## Relatórios

Entregáveis obrigatórios conforme o enunciado do Tech Challenge. Incluem análise de vulnerabilidades e resultado da cobertura de testes automatizados.
