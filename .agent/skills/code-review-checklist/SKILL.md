---
name: code-review-checklist
description: Diretrizes de revisão de código cobrindo qualidade de código, segurança e melhores práticas.
allowed-tools: Read, Glob, Grep
---

# Checklist de Revisão de Código

## Checklist de Revisão Rápida

### Correção (Correctness)
- [ ] O código faz o que é suposto fazer?
- [ ] Casos de borda (edge cases) tratados?
- [ ] Tratamento de erros implementado?
- [ ] Sem bugs óbvios?

### Segurança
- [ ] Entrada validada e sanitizada?
- [ ] Sem vulnerabilidades de injeção SQL/NoSQL?
- [ ] Sem vulnerabilidades XSS ou CSRF?
- [ ] Sem segredos (secrets) ou credenciais sensíveis no código?
- [ ] **Específico de IA:** Proteção contra Prompt Injection (se aplicável)?
- [ ] **Específico de IA:** Saídas são sanitizadas antes de serem usadas em sinks críticos?

### Performance
- [ ] Sem queries N+1?
- [ ] Sem loops desnecessários?
- [ ] Caching apropriado?
- [ ] Impacto no tamanho do bundle considerado?

### Qualidade do Código
- [ ] Nomenclatura clara?
- [ ] DRY - sem código duplicado?
- [ ] Princípios SOLID seguidos?
- [ ] Nível de abstração apropriado?

### Testes
- [ ] Testes unitários para o código novo?
- [ ] Casos de borda testados?
- [ ] Testes legíveis e fáceis de manter?

### Documentação
- [ ] Lógica complexa comentada?
- [ ] APIs públicas documentadas?
- [ ] README atualizado se necessário?

## Padrões de Revisão de IA & LLM (2025)

### Lógica & Alucinações
- [ ] **Chain of Thought:** A lógica segue um caminho verificável?
- [ ] **Casos de Borda:** A IA considerou estados vazios, timeouts e falhas parciais?
- [ ] **Estado Externo:** O código está fazendo suposições seguras sobre sistemas de arquivos ou redes?

### Revisão de Engenharia de Prompt
```markdown
// ❌ Prompt vago no código
const response = await ai.generate(userInput);

// ✅ Prompt estruturado e seguro
const response = await ai.generate({
  system: "Você é um parser especializado...",
  input: sanitize(userInput),
  schema: ResponseSchema
});
```

## Anti-Padrões para Sinalizar

```typescript
// ❌ Números mágicos
if (status === 3) { ... }

// ✅ Constantes nomeadas
if (status === Status.ACTIVE) { ... }

// ❌ Aninhamento profundo (Deep nesting)
if (a) { if (b) { if (c) { ... } } }

// ✅ Retornos antecipados (Early returns)
if (!a) return;
if (!b) return;
if (!c) return;
// executa o trabalho

// ❌ Funções longas (100+ linhas)
// ✅ Funções pequenas e focadas

// ❌ tipo any
const data: any = ...

// ✅ Tipagem adequada
const data: UserData = ...
```

## Guia de Comentários de Revisão

```
// Problemas bloqueantes usam 🔴
🔴 BLOQUEANTE: Vulnerabilidade de injeção SQL aqui

// Sugestões importantes usam 🟡
🟡 SUGESTÃO: Considere usar useMemo para melhoria de performance

// Ajustes menores (nits) usam 🟢
🟢 AJUSTE: Prefira const em vez de let para variáveis imutáveis

// Perguntas usam ❓
❓ PERGUNTA: O que acontece se o usuário for nulo aqui?
```
