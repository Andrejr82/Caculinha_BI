---
name: database-design
description: Princípios de design de banco de dados e tomada de decisão. Design de schema, estratégia de indexação, seleção de ORM, bancos de dados serverless.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Design de Banco de Dados

> **Aprenda a PENSAR, não a copiar padrões SQL.**

## 🎯 Regra de Leitura Seletiva

**Leia APENAS os arquivos relevantes para o pedido!** Verifique o mapa de conteúdo, encontre o que precisa.

| Arquivo | Descrição | Quando Ler |
|---------|-----------|------------|
| `database-selection.md` | PostgreSQL vs Neon vs Turso vs SQLite | Escolhendo banco de dados |
| `orm-selection.md` | Drizzle vs Prisma vs Kysely | Escolhendo ORM |
| `schema-design.md` | Normalização, PKs, relacionamentos | Projetando o schema |
| `indexing.md` | Tipos de índice, índices compostos | Ajuste de performance |
| `optimization.md` | N+1, EXPLAIN ANALYZE | Otimização de queries |
| `migrations.md` | Migrações seguras, bancos serverless | Mudanças de schema |

---

## ⚠️ Princípio Core

- PERGUNTE ao usuário as preferências de banco de dados quando não estiver claro
- Escolha o banco/ORM baseado no CONTEXTO
- Não use PostgreSQL como padrão para tudo

---

## Checklist de Decisão

Antes de projetar o schema:

- [ ] Perguntou ao usuário sobre a preferência de banco de dados?
- [ ] Escolheu o banco para ESTE contexto?
- [ ] Considerou o ambiente de deploy?
- [ ] Planejou a estratégia de índices?
- [ ] Definiu os tipos de relacionamento?

---

## Anti-Padrões

❌ Usar PostgreSQL por padrão para apps simples (SQLite pode bastar)
❌ Pular a criação de índices
❌ Usar SELECT * em produção
❌ Armazenar JSON quando dados estruturados seriam melhores
❌ Ignorar queries N+1
