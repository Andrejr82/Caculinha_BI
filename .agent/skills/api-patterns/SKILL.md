---
name: api-patterns
description: Princípios de design de API e tomada de decisão. Seleção entre REST vs GraphQL vs tRPC, formatos de resposta, versionamento, paginação.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Padrões de API

# Agente de Padrões de API

> Princípios de design de API e tomada de decisão para 2025.
> **Aprenda a PENSAR, não a copiar padrões fixos.**

## 🎯 Regra de Leitura Seletiva

**Leia APENAS os arquivos relevantes para o pedido!** Verifique o mapa de conteúdo, encontre o que precisa.

---

## 📑 Mapa de Conteúdo

| Arquivo | Descrição | Quando Ler |
|---------|-----------|------------|
| `api-style.md` | Árvore de decisão: REST vs GraphQL vs tRPC | Escolhendo tipo de API |
| `rest.md` | Nomenclatura de recursos, métodos HTTP, status codes | Projetando API REST |
| `response.md` | Padrão envelope, formato de erro, paginação | Estrutura de resposta |
| `graphql.md` | Design de schema, quando usar, segurança | Considerando GraphQL |
| `trpc.md` | Monorepo TypeScript, segurança de tipos | Projetos TS fullstack |
| `versioning.md` | Versionamento por URI/Header/Query | Planejando evolução da API |
| `auth.md` | JWT, OAuth, Passkey, API Keys | Seleção de padrão de auth |
| `rate-limiting.md` | Token bucket, sliding window | Proteção de API |
| `documentation.md` | Melhores práticas de OpenAPI/Swagger | Documentação |
| `security-testing.md` | OWASP API Top 10, testes de auth/authz | Auditorias de segurança |

---

## 🔗 Skills Relacionadas

| Necessidade | Skill |
|-------------|-------|
| Implementação de API | `@[skills/backend-development]` |
| Estrutura de dados | `@[skills/database-design]` |
| Detalhes de segurança | `@[skills/security-hardening]` |

---

## ✅ Checklist de Decisão

Antes de projetar uma API:

- [ ] **Perguntou ao usuário sobre os consumidores da API?**
- [ ] **Escolheu o estilo de API para ESTE contexto?** (REST/GraphQL/tRPC)
- [ ] **Definiu um formato de resposta consistente?**
- [ ] **Planejou a estratégia de versionamento?**
- [ ] **Considerou necessidades de autenticação?**
- [ ] **Planejou rate limiting?**
- [ ] **Abordagem de documentação definida?**

---

## ❌ Anti-Padrões

**NÃO FAÇA:**
- Usar REST como padrão para tudo
- Usar verbos em endpoints REST (/obterUsuarios)
- Retornar formatos de resposta inconsistentes
- Expor erros internos para os clientes
- Pular rate limiting

**FAÇA:**
- Escolha o estilo de API baseado no contexto
- Pergunte sobre os requisitos do cliente
- Documente detalhadamente
- Use status codes apropriados

---

## Script

| Script | Propósito | Comando |
|--------|-----------|---------|
| `scripts/api_validator.py` | Validação de endpoints de API | `python scripts/api_validator.py <caminho_projeto>` |
