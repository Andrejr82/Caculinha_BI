---
name: documentation-templates
description: Templates de documentação e diretrizes de estrutura. README, docs de API, comentários de código e documentação amigável para IA.
allowed-tools: Read, Glob, Grep
---

# Templates de Documentação

> Templates e diretrizes de estrutura para tipos comuns de documentação.

---

## 1. Estrutura do README

### Seções Essenciais (Ordem de Prioridade)

| Seção | Propósito |
|-------|-----------|
| **Título + Descrição Curta** | O que é isso? |
| **Início Rápido (Quick Start)** | Rodando em < 5 min |
| **Recursos (Features)** | O que posso fazer? |
| **Configuração** | Como customizar |
| **Referência de API** | Link para docs detalhados |
| **Contribuição** | Como ajudar |
| **Licença** | Aspectos legais |

### Template de README

```markdown
# Nome do Projeto

Descrição breve de uma linha.

## Início Rápido

[Passos mínimos para executar]

## Recursos

- Recurso 1
- Recurso 2

## Configuração

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| PORT | Porta do servidor | 3000 |

## Documentação

- [Referência de API](./docs/api.md)
- [Arquitetura](./docs/architecture.md)

## Licença

MIT
```

---

## 2. Estrutura de Documentação de API

### Template por Endpoint

```markdown
## GET /usuarios/:id

Busca um usuário pelo ID.

**Parâmetros:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| id | string | Sim | ID do Usuário |

**Resposta:**
- 200: Objeto do usuário
- 404: Usuário não encontrado

**Exemplo:**
[Exemplo de requisição e resposta]
```

---

## 3. Diretrizes de Comentários de Código

### Template JSDoc/TSDoc

```typescript
/**
 * Descrição breve do que a função faz.
 * 
 * @param nomeParam - Descrição do parâmetro
 * @returns Descrição do valor de retorno
 * @throws TipoErro - Quando este erro ocorre
 * 
 * @example
 * const resultado = nomeFuncao(entrada);
 */
```

### Quando Comentar

| ✅ Comente | ❌ Não Comente |
|-----------|----------------|
| O porquê (lógica de negócio) | O quê (óbvio) |
| Algoritmos complexos | Cada linha |
| Comportamento não óbvio | Código autoexplicativo |
| Contratos de API | Detalhes de implementação |

---

## 4. Template de Changelog (Mantenha um Changelog)

```markdown
# Changelog

## [Não lançado]
### Adicionado
- Novo recurso

## [1.0.0] - 2025-01-01
### Adicionado
- Lançamento inicial
### Alterado
- Dependência atualizada
### Corrigido
- Correção de bug
```

---

## 5. Registro de Decisão Arquitetural (ADR)

```markdown
# ADR-001: [Título]

## Status
Aceito / Obsoleto / Substituído

## Contexto
Por que estamos tomando esta decisão?

## Decisão
O que decidimos?

## Consequências
Quais são os trade-offs (prós e contras)?
```

---

## 6. Documentação Amigável para IA (2025)

### Template llms.txt

Para crawlers e agentes de IA:

```markdown
# Nome do Projeto
> Objetivo de uma linha.

## Arquivos Core
- [src/index.ts]: Entrada principal
- [src/api/]: Rotas da API
- [docs/]: Documentação

## Conceitos Chave
- Conceito 1: Explicação breve
- Concept 2: Explicação breve
```

### Documentação Pronta para MCP

Para indexação RAG:
- Hierarquia clara de H1-H3
- Exemplos JSON/YAML para estruturas de dados
- Diagramas Mermaid para fluxos
- Seções autocontidas

---

## 7. Princípios de Estrutura

| Princípio | Por que |
|-----------|---------|
| **Escaneável** | Cabeçalhos, listas, tabelas |
| **Exemplos primeiro** | Mostre, não apenas diga |
| **Detalhamento progressivo** | Simples → Complexo |
| **Atualizado** | Desatualizado = enganoso |

---

> **Lembre-se:** Templates são pontos de partida. Adapte-os às necessidades do seu projeto.
