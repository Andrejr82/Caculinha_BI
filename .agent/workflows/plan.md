---
description: Criar plano de projeto usando o agente project-planner. Sem escrita de código - apenas geração do arquivo de plano.
---

# /plan - Modo de Planejamento de Projeto

$ARGUMENTS

---

## 🔴 REGRAS CRÍTICAS

1. **SEM ESCRITA DE CÓDIGO** - Este comando cria apenas o arquivo de plano
2. **Use o agente project-planner** - NÃO use o subagente Plan nativo do Claude Code
3. **Socratic Gate** - Faça perguntas de esclarecimento antes de planejar
4. **Nomeação Dinâmica** - Arquivo de plano nomeado com base na tarefa

---

## Tarefa

Use o agente `project-planner` com este contexto:

```
CONTEXTO:
- Pedido do Usuário: $ARGUMENTS
- Modo: APENAS PLANEJAMENTO (sem código)
- Saída: docs/PLAN-{slug-da-tarefa}.md (nomeação dinâmica)

REGRAS DE NOMEAÇÃO:
1. Extraia 2-3 palavras-chave do pedido
2. Letras minúsculas, separadas por hífen
3. Máximo de 30 caracteres
4. Exemplo: "e-commerce cart" → PLAN-ecommerce-cart.md

REGRAS:
1. Siga o project-planner.md Fase -1 (Context Check)
2. Siga o project-planner.md Fase 0 (Socratic Gate)
3. Crie PLAN-{slug}.md com a quebra de tarefas
4. NÃO escreva nenhum arquivo de código
5. RELATE o nome exato do arquivo criado
```

---

## Saída Esperada

| Entregável | Localização |
|------------|-------------|
| Plano de Projeto | `docs/PLAN-{slug-da-tarefa}.md` |
| Quebra de Tarefas | Dentro do arquivo de plano |
| Atribuições de Agente | Dentro do arquivo de plano |
| Checklist de Verificação | Fase X no arquivo de plano |

---

## Após o Planejamento

Diga ao usuário:
```
[OK] Plano criado: docs/PLAN-{slug}.md

Próximos passos:
- Revise o plano
- Execute /create para iniciar a implementação
- Ou modifique o plano manualmente
```

---

## Exemplos de Nomeação

| Pedido | Arquivo de Plano |
|--------|------------------|
| `/plan site e-commerce com carrinho` | `docs/PLAN-ecommerce-carrinho.md` |
| `/plan app mobile para fitness` | `docs/PLAN-fitness-app.md` |
| `/plan adicionar recurso de modo escuro` | `docs/PLAN-modo-escuro.md` |
| `/plan corrigir bug de autenticação` | `docs/PLAN-auth-fix.md` |
| `/plan dashboard SaaS` | `docs/PLAN-saas-dashboard.md` |

---

## Uso

```
/plan site e-commerce com carrinho
/plan app mobile para monitoramento de fitness
/plan dashboard SaaS com analytics
```
