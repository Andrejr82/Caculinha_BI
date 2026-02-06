---
description: Iniciar, parar e checar status do servidor de preview. Gerenciamento do servidor de desenvolvimento local.
---

# /preview - Gerenciamento de Preview

$ARGUMENTS

---

## Tarefa

Gerenciar o servidor de preview: iniciar, parar, checar status.

### Comandos

```
/preview           - Mostrar status atual
/preview start     - Iniciar servidor
/preview stop      - Parar servidor
/preview restart   - Reiniciar
/preview check     - Verificação de saúde (health check)
```

---

## Exemplos de Uso

### Iniciar Servidor
```
/preview start

Resposta:
🚀 Iniciando preview...
   Porta: 3000
   Tipo: Next.js

✅ Preview pronto!
   URL: http://localhost:3000
```

### Checagem de Status
```
/preview

Resposta:
=== Status do Preview ===

🌐 URL: http://localhost:3000
📁 Projeto: C:/projetos/meu-app
🏷️ Tipo: nextjs
💚 Saúde: OK
```

### Conflito de Porta
```
/preview start

Resposta:
⚠️ A porta 3000 está em uso.

Opções:
1. Iniciar na porta 3001
2. Fechar app na 3000
3. Especificar porta diferente

Qual delas? (padrão: 1)
```

---

## Técnico

O preview automático usa o script `auto_preview.py`:

```bash
python .agent/scripts/auto_preview.py start [caminho] [porta]
python .agent/scripts/auto_preview.py stop
python .agent/scripts/auto_preview.py status
```
