---
name: plan-writing
description: Planejamento estruturado de tarefas com detalhamento claro, dependências e critérios de verificação. Use ao implementar recursos, refatorar ou em qualquer trabalho de múltiplas etapas.
allowed-tools: Read, Glob, Grep
---

# Escrita de Planos

> Fonte: obra/superpowers

## Visão Geral
Esta skill fornece um framework para dividir o trabalho em tarefas claras e acionáveis com critérios de verificação.

## Princípios de Detalhamento de Tarefas

### 1. Tarefas Pequenas e Focadas
- Cada tarefa deve levar de 2 a 5 minutos
- Um resultado claro por tarefa
- Verificável de forma independente

### 2. Verificação Clara
- Como você sabe que está concluído?
- O que você pode checar/testar?
- Qual é a saída esperada?

### 3. Ordenação Lógica
- Dependências identificadas
- Trabalho paralelo onde possível
- Caminho crítico destacado
- **Fase X: Verificação é sempre a ÚLTIMA**

### 4. Nomenclatura Dinâmica na Raiz do Projeto
- Arquivos de plano são salvos como `{task-slug}.md` na RAIZ DO PROJETO
- Nome derivado da tarefa (ex: "add auth" → `auth-feature.md`)
- **NUNCA** dentro de `.claude/`, `docs/` ou pastas temporárias

## Princípios de Planejamento (NÃO Templates!)

> 🔴 **SEM templates fixos. Cada plano é ÚNICO para a tarefa.**

### Princípio 1: Mantenha CURTO

| ❌ Errado | ✅ Certo |
|-----------|----------|
| 50 tarefas com sub-sub-tarefas | Máximo de 5-10 tarefas claras |
| Cada micro-passo listado | Apenas itens acionáveis |
| Descrições verbosas | Uma linha por tarefa |

> **Regra:** Se o plano for maior que 1 página, está muito longo. Simplifique.

---

### Princípio 2: Seja ESPECÍFICO, Não Genérico

| ❌ Errado | ✅ Certo |
|-----------|----------|
| "Configurar projeto" | "Executar `npx create-next-app`" |
| "Adicionar autenticação"| "Instalar next-auth, criar `/api/auth/[...nextauth].ts`" |
| "Estilizar a UI" | "Adicionar classes Tailwind ao `Header.tsx`" |

> **Regra:** Cada tarefa deve ter um resultado claro e verificável.

---

### Princípio 3: Conteúdo Dinâmico Baseado no Tipo de Projeto

**Para NOVO PROJETO:**
- Qual stack tecnológica? (decida primeiro)
- Qual o MVP? (recursos mínimos)
- Qual a estrutura de arquivos?

**Para ADIÇÃO DE RECURSOS:**
- Quais arquivos serão afetados?
- Quais dependências são necessárias?
- Como verificar se funciona?

**Para CORREÇÃO DE BUG:**
- Qual a causa raiz?
- Qual arquivo/linha mudar?
- Como testar a correção?

---

### Princípio 4: Scripts São Específicos do Projeto

> 🔴 **NÃO copie e cole comandos de script. Escolha com base no tipo de projeto.**

| Tipo de Projeto | Scripts Relevantes |
|-----------------|--------------------|
| Frontend/React | `ux_audit.py`, `accessibility_checker.py` |
| Backend/API | `api_validator.py`, `security_scan.py` |
| Mobile | `mobile_audit.py` |
| Banco de Dados | `schema_validator.py` |
| Full-stack | Mistura dos itens acima baseada no que foi alterado |

**Errado:** Adicionar todos os scripts em todos os planos
**Certo:** Apenas scripts relevantes para ESTA tarefa

---

### Princípio 5: Verificação é Simples

| ❌ Errado | ✅ Certo |
|-----------|----------|
| "Verificar se o componente funciona" | "Rodar `npm run dev`, clicar no botão, ver o toast" |
| "Testar a API" | "curl localhost:3000/api/users retorna 200" |
| "Checar estilos" | "Abrir navegador, verificar o toggle do modo escuro" |

---

## Estrutura do Plano (Flexível, Não Fixa!)

```markdown
# [Nome da Tarefa]

## Objetivo
Uma frase: O que estamos construindo/corrigindo?

## Tarefas
- [ ] Tarefa 1: [Ação específica] → Verificar: [Como checar]
- [ ] Tarefa 2: [Ação específica] → Verificar: [Como checar]
- [ ] Tarefa 3: [Ação específica] → Verificar: [Como checar]

## Concluído Quando
- [ ] [Principal critério de sucesso]
```

> **É só isso.** Sem fases, sem subseções a menos que seja realmente necessário.
> Mantenha o mínimo. Adicione complexidade apenas quando exigido.

---

## Melhores Práticas (Referência Rápida)

1. **Comece com o objetivo** - O que estamos construindo/corrigindo?
2. **Máximo de 10 tarefas** - Se houver mais, divida em múltiplos planos
3. **Cada tarefa verificável** - Critério de "concluído" claro
4. **Específico do projeto** - Nada de templates de copiar e colar
5. **Atualize conforme avança** - Marque com `[x]` quando concluir

---

## Quando Usar

- Novo projeto do zero
- Adição de um recurso
- Correção de um bug (se for complexo)
- Refatoração de múltiplos arquivos
