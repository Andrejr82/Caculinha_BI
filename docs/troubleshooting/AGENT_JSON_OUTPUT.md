# Troubleshooting: Agent Returning Raw JSON (Context7 Violation)

## 🚨 Problema Relatado
O Agente de BI ("Caculinha") estava retornando respostas em formato JSON bruto (ex: `{"analise_executiva": ...}`) diretamente na interface de chat, violando o padrão **Context7** que exige respostas narrativas e formatadas em Markdown ("Storytelling").

### Sintoma
O usuário vê um bloco de código JSON na tela em vez de um texto explicativo.
Exemplo:
```json
{
  "analise_executiva": {
    "manchete": "UNE 2599 lidera vendas...",
    "status_geral": "ALTA PERFORMANCE",
    ...
  }
}
```

## 🔍 Causa Raiz
1. **Falha no Safety Net**: O mecanismo de segurança (`Safety Net`) no arquivo `backend/app/core/agents/caculinha_bi_agent.py` que converte esse JSON específico em Markdown estava posicionado **após** o comando `return`, tornando-o inalcançável.
2. **Priorização de Gráficos**: Quando o agente gerava um gráfico (`code_result`), o endpoint de chat (`chat.py`) ignorava o texto explicativo (`text_override`) e gerava um dump JSON do resumo dos dados.

## 🛠️ Solução Aplicada (24/12/2025)

### 1. Correção no Agente (`caculinha_bi_agent.py`)
O bloco de código responsável por detectar e converter o padrão JSON `analise_executiva` foi movido para **antes** do retorno final nos métodos `run` e `run_async`.

**Antes (Errado):**
```python
return {"type": "text", "result": content}
# Safety Net inalcançável...
```

**Depois (Corrigido):**
```python
# Safety Net detecta JSON e converte para Markdown...
content = md_output 
return {"type": "text", "result": content}
```

### 2. Melhoria no Endpoint de Chat (`chat.py`)
O endpoint de streaming foi atualizado para respeitar o campo `text_override` quando o tipo de resposta é `code_result` (Gráfico).
Isso garante que, mesmo quando um gráfico é exibido, a explicação narrativa do agente (Storytelling) seja mostrada em vez de dados técnicos.

## ✅ Validação
- **JSON Puro**: Convertido automaticamente para Markdown com manchete, diagnóstico e recomendações.
- **Gráficos**: Exibidos com o texto explicativo correto (Storytelling) acima ou abaixo do gráfico.
- **Padrão Context7**: Mantido (Sem JSON bruto para o usuário final).

---
**Documento criado em:** 24/12/2025
**Status:** Resolvido
