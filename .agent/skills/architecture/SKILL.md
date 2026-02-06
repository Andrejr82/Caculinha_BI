---
name: architecture
description: Framework de tomada de decisão arquitetural. Análise de requisitos, avaliação de trade-offs, documentação ADR. Use ao tomar decisões de arquitetura ou analisar o design do sistema.
allowed-tools: Read, Glob, Grep
---

# Framework de Decisão de Arquitetura

> "Requisitos direcionam a arquitetura. Trade-offs informam decisões. ADRs capturam a lógica."

## 🎯 Regra de Leitura Seletiva

**Leia APENAS os arquivos relevantes para o pedido!** Verifique o mapa de conteúdo, encontre o que precisa.

| Arquivo | Descrição | Quando Ler |
|---------|-----------|------------|
| `context-discovery.md` | Perguntas a fazer, classificação do projeto | Iniciando design de arquitetura |
| `trade-off-analysis.md` | Templates de ADR, framework de trade-off | Documentando decisões |
| `pattern-selection.md` | Árvores de decisão, anti-padrões | Escolhendo padrões |
| `examples.md` | Exemplos MVP, SaaS, Enterprise | Implementações de referência |
| `patterns-reference.md` | Busca rápida por padrões | Comparação de padrões |

---

## 🔗 Skills Relacionadas

| Skill | Use Para |
|-------|----------|
| `@[skills/database-design]` | Design de schema de banco de dados |
| `@[skills/api-patterns]` | Padrões de design de API |
| `@[skills/deployment-procedures]` | Arquitetura de deploy |

---

## Princípio Core

**"Simplicidade é a sofisticação máxima."**

- Comece simples
- Adicione complexidade APENAS quando provado necessário
- Você sempre pode adicionar padrões depois
- Remover complexidade é MUITO mais difícil do que adicioná-la

---

## Checklist de Validação

Antes de finalizar a arquitetura:

- [ ] Requisitos claramente compreendidos
- [ ] Restrições identificadas
- [ ] Cada decisão tem análise de trade-off
- [ ] Alternativas mais simples consideradas
- [ ] ADRs escritos para decisões significativas
- [ ] Expertise do time combina com os padrões escolhidos
