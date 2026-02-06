---
description: Comando para criar nova aplicação. Aciona a skill App Builder e inicia diálogo interativo com o usuário.
---

# /create - Criar Aplicação

$ARGUMENTS

---

## Tarefa

Este comando inicia um novo processo de criação de aplicação.

### Passos:

1. **Análise de Pedido**
   - Entender o que o usuário deseja
   - Se faltarem informações, use a skill `conversation-manager` para perguntar

2. **Planejamento do Projeto**
   - Use o agente `project-planner` para a quebra de tarefas
   - Determinar a tech stack
   - Planejar a estrutura de arquivos
   - Criar o arquivo de plano e prosseguir para a construção

3. **Construção da Aplicação (Após Aprovação)**
   - Orquestrar com a skill `app-builder`
   - Coordenar agentes especialistas:
     - `database-architect` → Schema
     - `backend-specialist` → API
     - `frontend-specialist` → UI

4. **Preview**
   - Iniciar com `auto_preview.py` quando concluído
   - Apresentar a URL ao usuário

---

## Exemplos de Uso

```
/create site de blog
/create app de e-commerce com listagem de produtos e carrinho
/create app de tarefas (todo)
/create clone do Instagram
/create sistema de crm com gerenciamento de clientes
```

---

## Antes de Começar

Se o pedido não estiver claro, faça estas perguntas:
- Qual tipo de aplicação?
- Quais são as funcionalidades básicas?
- Quem irá usar?

Use padrões (defaults), adicione detalhes depois.
