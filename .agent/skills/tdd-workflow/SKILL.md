---
name: tdd-workflow
description: Princípios do fluxo de desenvolvimento orientado a testes (TDD). Ciclo RED-GREEN-REFACTOR.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Fluxo de TDD

> Escreva os testes primeiro, o código depois.

---

## 1. O Ciclo de TDD

```
🔴 RED → Escreva um teste que falha
    ↓
🟢 GREEN → Escreva o código mínimo para passar
    ↓
🔵 REFACTOR → Melhore a qualidade do código
    ↓
   Repita...
```

---

## 2. As Três Leis do TDD

1. Escreva código de produção apenas para fazer um teste falhar passar
2. Escreva apenas o teste suficiente para demonstrar a falha
3. Escreva apenas o código suficiente para fazer o teste passar

---

## 3. Princípios da Fase RED

### O que escrever

| Foco | Exemplo |
|------|---------|
| Comportamento | "deve somar dois números" |
| Casos de borda | "deve lidar com entrada vazia" |
| Estados de erro | "deve lançar erro para dados inválidos" |

### Regras da Fase RED

- O teste deve falhar primeiro
- O nome do teste descreve o comportamento esperado
- Uma asserção por teste (idealmente)

---

## 4. Princípios da Fase GREEN

### Código Mínimo

| Princípio | Significado |
|-----------|-------------|
| **YAGNI** | Você não vai precisar disso (You Aren't Gonna Need It) |
| **A coisa mais simples**| Escreva o mínimo para passar |
| **Sem otimização** | Apenas faça funcionar |

### Regras da Fase GREEN

- Não escreva código desnecessário
- Não otimize ainda
- Passe no teste, nada mais

---

## 5. Princípios da Fase REFACTOR

### O que melhorar

| Área | Ação |
|------|------|
| Duplicação | Extrair código comum |
| Nomenclatura | Tornar a intenção clara |
| Estrutura | Melhorar a organização |
| Complexidade | Simplificar a lógica |

### Regras da Fase REFACTOR

- Todos os testes devem permanecer verdes
- Mudanças incrementais pequenas
- Commit após cada refatoração

---

## 6. Padrão AAA

Cada teste segue:

| Passo | Propósito |
|-------|-----------|
| **Arrange** (Preparar) | Configurar os dados do teste |
| **Act** (Agir) | Executar o código sob teste |
| **Assert** (Verificar) | Verificar o resultado esperado |

---

## 7. Quando usar TDD

| Cenário | Valor do TDD |
|---------|--------------|
| Novo recurso | Alto |
| Correção de bug | Alto (escreva o teste primeiro) |
| Lógica complexa | Alto |
| Exploratório | Baixo (faça um spike, depois TDD) |
| Layout de UI | Baixo |

---

## 8. Priorização de Testes

| Prioridade | Tipo de Teste |
|------------|---------------|
| 1 | Caminho feliz (Happy path) |
| 2 | Casos de erro |
| 3 | Casos de borda |
| 4 | Performance |

---

## 9. Anti-Padrões

| ❌ Não faça | ✅ Faça |
|-------------|---------|
| Pular a fase RED | Assista ao teste falhar primeiro |
| Escrever testes depois | Escrever testes antes |
| Super-dimensionar o início | Mantenha simples |
| Múltiplas asserções | Um comportamento por teste |
| Testar implementação | Testar comportamento |

---

## 10. TDD Aumentado por IA

### Padrão Multi-Agente

| Agente | Papel |
|--------|-------|
| Agente A | Escrever testes que falham (RED) |
| Agente B | Implementar para passar (GREEN) |
| Agente C | Otimizar (REFACTOR) |

---

> **Lembre-se:** O teste é a especificação. Se você não consegue escrever um teste, você não entende o requisito.
