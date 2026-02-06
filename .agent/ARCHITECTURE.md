# Arquitetura do Antigravity Kit

> Toolkit Abrangente de Expansão de Capacidades de Agentes de IA

---

## 📋 Visão Geral

O Antigravity Kit é um sistema modular consistindo em:

- **19 Agentes Especialistas** - Personas de IA baseadas em funções
- **36 Skills (Habilidades)** - Módulos de conhecimento específicos de domínio
- **11 Workflows** - Procedimentos de comandos "slash" (barra)

---

## 🏗️ Estrutura de Diretórios

```plaintext
.agent/
├── ARCHITECTURE.md          # Este arquivo
├── agents/                  # 19 Agentes Especialistas
├── skills/                  # 36 Skills
├── workflows/               # 11 Comandos Slash
├── rules/                   # Regras Globais
└── scripts/                 # Scripts de Validação Mestres
```

---

## 🤖 Agentes (19)

Personas de IA especialistas para diferentes domínios.

| Agente | Foco | Skills Utilizadas |
| ------ | ---- | ----------------- |
| `orchestrator` | Coordenação multi-agente | parallel-agents, behavioral-modes |
| `project-planner` | Descoberta, planejamento de tarefas | brainstorming, plan-writing, architecture |
| `frontend-specialist` | Web UI/UX | frontend-design, react-patterns, tailwind-patterns |
| `backend-specialist` | API, lógica de negócio | api-patterns, nodejs-best-practices, database-design |
| `database-architect` | Schema, SQL | database-design, prisma-expert |
| `mobile-developer` | iOS, Android, RN | mobile-design |
| `game-developer` | Lógica de jogo, mecânicas | game-development |
| `devops-engineer` | CI/CD, Docker | deployment-procedures, docker-expert |
| `security-auditor` | Conformidade de segurança | vulnerability-scanner, red-team-tactics |
| `penetration-tester` | Segurança ofensiva | red-team-tactics |
| `test-engineer` | Estratégias de teste | testing-patterns, tdd-workflow, webapp-testing |
| `debugger` | Análise de causa raiz | systematic-debugging |
| `performance-optimizer` | Velocidade, Web Vitals | performance-profiling |
| `seo-specialist` | Ranking, visibilidade | seo-fundamentals, geo-fundamentals |
| `documentation-writer` | Manuais, docs | documentation-templates |
| `product-manager` | Requisitos, user stories | plan-writing, brainstorming |
| `qa-automation-engineer` | Testes E2E, pipelines de CI | webapp-testing, testing-patterns |
| `code-archaeologist` | Código legado, refatoração | clean-code, code-review-checklist |
| `explorer-agent` | Análise da base de código | - |

---

## 🧩 Skills (36)

Domínios de conhecimento modulares que os agentes podem carregar sob demanda, com base no contexto da tarefa.

### Frontend & UI

| Skill | Descrição |
| ----- | --------- |
| `react-patterns` | React hooks, estado, performance |
| `nextjs-best-practices` | App Router, Server Components |
| `tailwind-patterns` | Utilitários Tailwind CSS v4 |
| `frontend-design` | Padrões de UI/UX, sistemas de design |
| `ui-ux-pro-max` | 50 estilos, 21 paletas, 50 fontes |

### Backend & API

| Skill | Descrição |
| ----- | --------- |
| `api-patterns` | REST, GraphQL, tRPC |
| `nestjs-expert` | Módulos NestJS, DI, decoradores |
| `nodejs-best-practices` | Node.js async, módulos |
| `python-patterns` | Padrões Python, FastAPI |

### Banco de Dados

| Skill | Descrição |
| ----- | --------- |
| `database-design` | Design de schema, otimização |
| `prisma-expert` | ORM Prisma, migrações |

### TypeScript/JavaScript

| Skill | Descrição |
| ----- | --------- |
| `typescript-expert` | Programação em nível de tipo, performance |

### Nuvem & Infraestrutura

| Skill | Descrição |
| ----- | --------- |
| `docker-expert` | Conteinerização, Compose |
| `deployment-procedures` | CI/CD, workflows de deploy |
| `server-management` | Gerenciamento de infraestrutura |

### Testes & Qualidade

| Skill | Descrição |
| ----- | --------- |
| `testing-patterns` | Jest, Vitest, estratégias |
| `webapp-testing` | E2E, Playwright |
| `tdd-workflow` | Desenvolvimento orientado a testes (TDD) |
| `code-review-checklist` | Padrões de revisão de código |
| `lint-and-validate` | Linting, validação |

### Segurança

| Skill | Descrição |
| ----- | --------- |
| `vulnerability-scanner` | Auditoria de segurança, OWASP |
| `red-team-tactics` | Segurança ofensiva |

### Arquitetura & Planejamento

| Skill | Descrição |
| ----- | --------- |
| `app-builder` | Estruturação de app full-stack |
| `architecture` | Padrões de design de sistema |
| `plan-writing` | Planejamento de tarefas, quebra de tarefas |
| `brainstorming` | Questionamento socrático |

### Mobile

| Skill | Descrição |
| ----- | --------- |
| `mobile-design` | Padrões de UI/UX mobile |

### Desenvolvimento de Jogos

| Skill | Descrição |
| ----- | --------- |
| `game-development` | Lógica de jogo, mecânicas |

### SEO & Crescimento

| Skill | Descrição |
| ----- | --------- |
| `seo-fundamentals` | SEO, E-E-A-T, Core Web Vitals |
| `geo-fundamentals` | Otimização para GenAI |

### Shell/CLI

| Skill | Descrição |
| ----- | --------- |
| `bash-linux` | Comandos Linux, scripts |
| `powershell-windows` | Windows PowerShell |

### Outros

| Skill | Descrição |
| ----- | --------- |
| `clean-code` | Padrões de codificação (Global) |
| `behavioral-modes` | Personas de agentes |
| `parallel-agents` | Padrões multi-agente |
| `mcp-builder` | Model Context Protocol |
| `documentation-templates` | Formatos de documentação |
| `i18n-localization` | Internacionalização |
| `performance-profiling` | Web Vitals, otimização |
| `systematic-debugging` | Resolução de problemas |

---

## 🔄 Workflows (11)

Procedimentos de comandos slash. Invoque com `/comando`.

| Comando | Descrição |
| ------- | --------- |
| `/brainstorm` | Descoberta socrática |
| `/create` | Criar novos recursos |
| `/debug` | Depurar problemas |
| `/deploy` | Fazer deploy da aplicação |
| `/enhance` | Melhorar código existente |
| `/orchestrate` | Coordenação multi-agente |
| `/plan` | Quebra de tarefas |
| `/preview` | Visualizar mudanças |
| `/status` | Checar status do projeto |
| `/test` | Executar testes |
| `/ui-ux-pro-max` | Design com 50 estilos |

---

## 🎯 Protocolo de Carregamento de Skills

```plaintext
Pedido do Usuário → Correspondência de Descrição da Skill → Carregar SKILL.md
                                             ↓
                                     Ler references/
                                             ↓
                                     Ler scripts/
```

### Estrutura da Skill

```plaintext
nome-da-skill/
├── SKILL.md           # (Obrigatório) Metadados e instruções
├── scripts/           # (Opcional) Scripts Python/Bash
├── references/        # (Opcional) Templates, documentos
└── assets/            # (Opcional) Imagens, logos
```

### Skills Aprimoradas (com scripts/referências)

| Skill | Arquivos | Cobertura |
| ----- | -------- | --------- |
| `typescript-expert` | 5 | Tipos utilitários, tsconfig, cheatsheet |
| `ui-ux-pro-max` | 27 | 50 estilos, 21 paletas, 50 fontes |
| `app-builder` | 20 | Estruturação full-stack |

---

## 🛠️ Scripts (2)

Scripts de validação mestres que orquestram os scripts de nível de skill.

### Scripts Mestres

| Script | Propósito | Quando Usar |
| ------ | --------- | ----------- |
| `checklist.py` | Validação baseada em prioridade (Checagens core) | Desenvolvimento, pre-commit |
| `verify_all.py` | Verificação abrangente (Todas as checagens) | Pré-deploy, lançamentos (releases) |

### Uso

```bash
# Validação rápida durante o desenvolvimento
python .agent/scripts/checklist.py .

# Verificação completa antes do deploy
python .agent/scripts/verify_all.py . --url http://localhost:3000
```

### O Que Eles Verificam

**checklist.py** (Checagens core):

- Segurança (vulnerabilidades, segredos)
- Qualidade de Código (lint, tipos)
- Validação de Schema
- Suíte de Testes
- Auditoria UX
- Verificação de SEO

**verify_all.py** (Suíte completa):

- Tudo no checklist.py MAIS:
- Lighthouse (Core Web Vitals)
- Playwright E2E
- Análise de Bundle
- Auditoria Mobile
- Verificação de i18n

Para detalhes, veja [scripts/README.md](scripts/README.md)

---

## 📊 Estatísticas

| Métrica | Valor |
| ------- | ----- |
| **Total de Agentes** | 19 |
| **Total de Skills** | 36 |
| **Total de Workflows** | 11 |
| **Total de Scripts** | 2 (mestre) + 18 (nível de skill) |
| **Cobertura** | ~90% desenvolvimento web/mobile |

---

## 🔗 Referência Rápida

| Necessidade | Agente | Skills |
| ----------- | ------ | ------ |
| App Web | `frontend-specialist` | react-patterns, nextjs-best-practices |
| API | `backend-specialist` | api-patterns, nodejs-best-practices |
| Mobile | `mobile-developer` | mobile-design |
| Banco de Dados | `database-architect` | database-design, prisma-expert |
| Segurança | `security-auditor` | vulnerability-scanner |
| Testes | `test-engineer` | testing-patterns, webapp-testing |
| Debug | `debugger` | systematic-debugging |
| Plano | `project-planner` | brainstorming, plan-writing |
