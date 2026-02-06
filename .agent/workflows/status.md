---
description: Exibir status do agente e do projeto. Acompanhamento de progresso e quadro de status.
---

# /status - Mostrar Status

$ARGUMENTS

---

## Tarefa

Mostrar o status atual do projeto e dos agentes.

### O Que Ele Exibe

1. **Informações do Projeto**
   - Nome e caminho do projeto
   - Tech stack
   - Funcionalidades atuais

2. **Quadro de Status dos Agentes**
   - Quais agentes estão rodando
   - Quais tarefas estão concluídas
   - Trabalho pendente

3. **Estatísticas de Arquivos**
   - Contagem de arquivos criados
   - Contagem de arquivos modificados

4. **Status do Preview**
   - O servidor está rodando
   - URL
   - Health check (verificação de saúde)

---

## Exemplo de Saída

```
=== Status do Projeto ===

📁 Projeto: meu-ecommerce
📂 Caminho: C:/projetos/meu-ecommerce
🏷️ Tipo: nextjs-ecommerce
📊 Status: ativo

🔧 Tech Stack:
   Framework: next.js
   Banco de Dados: postgresql
   Auth: clerk
   Pagamento: stripe

✅ Recursos (5):
   • listagem-de-produtos
   • carrinho
   • checkout
   • auth-de-usuario
   • historico-de-pedidos

⏳ Pendente (2):
   • painel-admin
   • notificacoes-email

📄 Arquivos: 73 criados, 12 modificados

=== Status dos Agentes ===

✅ database-architect → Concluído
✅ backend-specialist → Concluído
🔄 frontend-specialist → Componentes do Dashboard (60%)
⏳ test-engineer → Aguardando

=== Preview ===

🌐 URL: http://localhost:3000
💚 Saúde: OK
```

---

## Técnico

O status usa estes scripts:
- `session_manager.py status`
- `auto_preview.py status`
