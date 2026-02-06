---
name: app-builder
description: Orquestrador principal de construção de aplicações. Cria aplicações full-stack a partir de pedidos em linguagem natural. Determina o tipo de projeto, seleciona a tech stack, coordena agentes.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# App Builder - Orquestrador de Construção de Aplicações

> Analisa pedidos do usuário, determina a tech stack, planeja a estrutura e coordena os agentes.

## 🎯 Regra de Leitura Seletiva

**Leia APENAS os arquivos relevantes para o pedido!** Verifique o mapa de conteúdo, encontre o que precisa.

| Arquivo | Descrição | Quando Ler |
|---------|-----------|------------|
| `project-detection.md` | Matriz de palavras-chave, detecção de tipo de projeto | Iniciando novo projeto |
| `tech-stack.md` | Stack padrão 2025, alternativas | Escolhendo tecnologias |
| `agent-coordination.md` | Pipeline de agentes, ordem de execução | Coordenando trabalho multi-agente |
| `scaffolding.md` | Estrutura de diretórios, arquivos core | Criando estrutura do projeto |
| `feature-building.md` | Análise de features, tratamento de erro | Adicionando features a projeto existente |
| `templates/SKILL.md` | **Templates de projeto** | Criando a base de um novo projeto |

---

## 📦 Templates (13)

Base de início rápido para novos projetos. **Leia apenas o template correspondente!**

| Template | Tech Stack | Quando Usar |
|----------|------------|-------------|
| [nextjs-fullstack](templates/nextjs-fullstack/TEMPLATE.md) | Next.js + Prisma | App web full-stack |
| [nextjs-saas](templates/nextjs-saas/TEMPLATE.md) | Next.js + Stripe | Produto SaaS |
| [nextjs-static](templates/nextjs-static/TEMPLATE.md) | Next.js + Framer | Landing page |
| [nuxt-app](templates/nuxt-app/TEMPLATE.md) | Nuxt 3 + Pinia | App Vue full-stack |
| [express-api](templates/express-api/TEMPLATE.md) | Express + JWT | API REST |
| [python-fastapi](templates/python-fastapi/TEMPLATE.md) | FastAPI | API Python |
| [react-native-app](templates/react-native-app/TEMPLATE.md) | Expo + Zustand | App Mobile |
| [flutter-app](templates/flutter-app/TEMPLATE.md) | Flutter + Riverpod | Mobile multiplataforma |
| [electron-desktop](templates/electron-desktop/TEMPLATE.md) | Electron + React | App Desktop |
| [chrome-extension](templates/chrome-extension/TEMPLATE.md) | Chrome MV3 | Extensão de navegador |
| [cli-tool](templates/cli-tool/TEMPLATE.md) | Node.js + Commander | Ferramenta CLI |
| [monorepo-turborepo](templates/monorepo-turborepo/TEMPLATE.md) | Turborepo + pnpm | Monorepo |

---

## 🔗 Agentes Relacionados

| Agente | Papel |
|--------|-------|
| `project-planner` | Quebra de tarefas, gráfico de dependência |
| `frontend-specialist` | Componentes de UI, páginas |
| `backend-specialist` | API, lógica de negócio |
| `database-architect` | Schema, migrações |
| `devops-engineer` | Deploy, preview |

---

## Exemplo de Uso

```
Usuário: "Crie um clone do Instagram com compartilhamento de fotos e curtidas"

Processo do App Builder:
1. Tipo de projeto: App de Rede Social
2. Tech stack: Next.js + Prisma + Cloudinary + Clerk
3. Criar plano:
   ├─ Schema do Banco de Dados (usuários, posts, curtidas, seguidores)
   ├─ Rotas de API (12 endpoints)
   ├─ Páginas (feed, perfil, upload)
   └─ Componentes (PostCard, Feed, LikeButton)
4. Coordenar agentes
5. Relatar progresso
6. Iniciar preview
```
