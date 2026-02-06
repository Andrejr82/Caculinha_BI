---
description: Brainstorming estruturado para projetos e recursos. Explora múltiplas opções antes da implementação.
---

# /brainstorm - Exploração Estruturada de Ideias

$ARGUMENTS

---

## Propósito

Este comando ativa o modo BRAINSTORM para exploração estruturada de ideias. Use quando precisar explorar opções antes de se comprometer com uma implementação.

---

## Comportamento

Quando o `/brainstorm` é acionado:

1. **Entender o objetivo**
   - Qual problema estamos resolvendo?
   - Quem é o usuário?
   - Quais restrições existem?

2. **Gerar opções**
   - Fornecer pelo menos 3 abordagens diferentes
   - Cada uma com prós e contras
   - Considerar soluções não convencionais

3. **Comparar e recomendar**
   - Resumir os trade-offs
   - Dar uma recomendação com justificativa

---

## Formato de Saída

```markdown
## 🧠 Brainstorm: [Tópico]

### Contexto
[Breve declaração do problema]

---

### Opção A: [Nome]
[Descrição]

✅ **Prós:**
- [benefício 1]
- [benefício 2]

❌ **Contras:**
- [desvantagem 1]

📊 **Esforço:** Baixo | Médio | Alto

---

### Opção B: [Nome]
[Descrição]

✅ **Prós:**
- [benefício 1]

❌ **Contras:**
- [desvantagem 1]
- [desvantagem 2]

📊 **Esforço:** Baixo | Médio | Alto

---

### Opção C: [Nome]
[Descrição]

✅ **Prós:**
- [benefício 1]

❌ **Contras:**
- [desvantagem 1]

📊 **Esforço:** Baixo | Médio | Alto

---

## 💡 Recomendação

**Opção [X]** porque [justificativa].

Qual direção você gostaria de explorar?
```

---

## Exemplos

```
/brainstorm sistema de autenticação
/brainstorm gerenciamento de estado para formulário complexo
/brainstorm schema de banco de dados para app social
/brainstorm estratégia de cache
```

---

## Princípios Chave

- **Sem código** - trata-se de ideias, não de implementação
- **Visual quando útil** - use diagramas para arquitetura
- **Trade-offs honestos** - não esconda a complexidade
- **Deferir ao usuário** - apresente opções, deixe-os decidir
