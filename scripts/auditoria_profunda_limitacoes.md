# Auditoria Profunda: Limitações do Agente BI

## 🎯 Objetivo
Identificar TODAS as limitações que podem restringir o desempenho do agente, incluindo:
- Limites de contexto
- Truncamentos de resposta
- Timeouts
- Restrições de memória
- Filtros de segurança

---

## 🚨 LIMITAÇÕES CRÍTICAS ENCONTRADAS

### 1. **Histórico de Contexto Limitado a 15 Mensagens**

**Arquivo:** `backend/app/core/agents/caculinha_bi_agent.py`

**Linhas:** 512, 916, 923

**Código:**
```python
# Linha 512
recent_history = filtered_history[-15:] if len(filtered_history) > 15 else filtered_history

# Linha 916
recent_history = filtered_history[-15:] if len(filtered_history) > 15 else filtered_history

# Linha 923
if len(filtered_history) > 15:
```

**Impacto:** 🔴 **CRÍTICO**
- Agente "esquece" conversas longas
- Perde contexto após 15 interações
- Dificulta análises complexas que requerem múltiplas iterações

**Recomendação:**
```python
# ANTES
recent_history = filtered_history[-15:]

# DEPOIS
recent_history = filtered_history[-30:]  # Dobrar para 30 mensagens
```

---

### 2. **Respostas de Ferramentas Truncadas em 500 Caracteres**

**Arquivo:** `backend/app/core/agents/caculinha_bi_agent.py`

**Linhas:** 414, 943

**Código:**
```python
# Linha 414
if len(assist_r) > 500:
    # Trunca resposta

# Linha 943
if len(assist_r) > 500: assist_r = assist_r[:500] + "..."
```

**Impacto:** 🔴 **CRÍTICO**
- Respostas de ferramentas são cortadas
- Agente perde informações importantes
- Análises incompletas

**Recomendação:**
```python
# ANTES
if len(assist_r) > 500: assist_r = assist_r[:500] + "..."

# DEPOIS
if len(assist_r) > 2000: assist_r = assist_r[:2000] + "..."  # 4x maior
```

---

### 3. **Lista de Colunas Truncada em 30**

**Arquivo:** `backend/app/core/agents/caculinha_bi_agent.py`

**Linha:** 238

**Código:**
```python
{f"... (+{len(other_cols)-30} colunas adicionais)" if len(other_cols) > 30 else ""}
```

**Impacto:** 🟡 **MÉDIO**
- Agente não vê todas as colunas disponíveis
- Pode não usar colunas relevantes

**Recomendação:**
```python
# ANTES
if len(other_cols) > 30

# DEPOIS
if len(other_cols) > 50  # Mostrar mais colunas
```

---

### 4. **Timeout de Code Interpreter: 10 Segundos**

**Arquivo:** `backend/app/core/tools/code_interpreter.py`

**Linha:** 42

**Código:**
```python
def __init__(self, timeout_seconds: int = 10):
    self.timeout = timeout_seconds
```

**Impacto:** 🟡 **MÉDIO**
- Análises complexas podem falhar por timeout
- Limita capacidade de processamento

**Recomendação:**
```python
# ANTES
timeout_seconds: int = 10

# DEPOIS
timeout_seconds: int = 30  # 3x mais tempo
```

---

### 5. **Max Tokens do Groq: 4096**

**Arquivo:** `backend/app/core/llm_groq_adapter.py`

**Linha:** 67

**Código:**
```python
"max_tokens": 4096,
```

**Impacto:** 🟡 **MÉDIO**
- Respostas longas são cortadas
- Análises detalhadas podem ser incompletas

**Recomendação:**
```python
# ANTES
"max_tokens": 4096

# DEPOIS
"max_tokens": 8192  # Dobrar limite (se modelo suportar)
```

---

### 6. **Truncamento de DataFrame para LLM: 10 Linhas**

**Arquivo:** `backend/app/core/tools/unified_data_tools.py`

**Linha:** 17

**Código:**
```python
def _truncate_df_for_llm(df: pd.DataFrame, max_rows: int = 10) -> Dict[str, Any]:
```

**Impacto:** 🟡 **MÉDIO**
- Agente vê apenas 10 primeiras linhas
- Análises baseadas em amostra pequena

**Recomendação:**
```python
# ANTES
max_rows: int = 10

# DEPOIS
max_rows: int = 50  # 5x mais dados
```

---

### 7. **Amostragem de Gráficos: 2000 Pontos**

**Arquivo:** `backend/app/core/tools/chart_tools.py`

**Linha:** 1633

**Código:**
```python
df_chart = df_chart.sample(2000)
```

**Impacto:** 🟢 **BAIXO**
- Gráficos com muitos pontos são amostrados
- Pode perder padrões em datasets grandes

**Recomendação:**
```python
# ANTES
df_chart.sample(2000)

# DEPOIS
df_chart.sample(5000)  # 2.5x mais pontos
```

---

### 8. **Retry Delay do Gemini: 2 Segundos**

**Arquivo:** `backend/app/core/llm_genai_adapter.py`

**Linha:** 66

**Código:**
```python
self.retry_delay = 2.0
```

**Impacto:** 🟢 **BAIXO**
- Delays podem acumular em múltiplos retries
- Usuário espera mais tempo

**Recomendação:** Manter 2s (adequado para rate limits)

---

### 9. **Timeout de Query Validator: 30 Segundos**

**Arquivo:** `backend/app/core/utils/query_validator.py`

**Linha:** 36

**Código:**
```python
def __init__(self, default_timeout: int = 30):
```

**Impacto:** 🟢 **BAIXO**
- Queries complexas podem falhar
- Proteção contra queries infinitas

**Recomendação:** Manter 30s (segurança)

---

## 📊 Resumo de Limitações

| # | Limitação | Valor Atual | Recomendado | Prioridade | Impacto |
|---|-----------|-------------|-------------|------------|---------|
| 1 | Histórico de contexto | 15 msgs | 30 msgs | 🔴 CRÍTICO | Agente "esquece" conversas |
| 2 | Truncamento de respostas | 500 chars | 2000 chars | 🔴 CRÍTICO | Perde informações |
| 3 | Lista de colunas | 30 colunas | 50 colunas | 🟡 MÉDIO | Não vê todas as colunas |
| 4 | Timeout Code Interpreter | 10s | 30s | 🟡 MÉDIO | Análises complexas falham |
| 5 | Max tokens Groq | 4096 | 8192 | 🟡 MÉDIO | Respostas cortadas |
| 6 | Truncamento DataFrame | 10 linhas | 50 linhas | 🟡 MÉDIO | Amostra pequena |
| 7 | Amostragem gráficos | 2000 pts | 5000 pts | 🟢 BAIXO | Perde padrões |
| 8 | Retry delay Gemini | 2s | 2s | 🟢 BAIXO | OK |
| 9 | Timeout query | 30s | 30s | 🟢 BAIXO | OK (segurança) |

---

## 🎯 Correções Prioritárias

### CRÍTICAS (Implementar Agora)

1. **Aumentar histórico de contexto: 15 → 30**
   - Arquivo: `caculinha_bi_agent.py` linhas 512, 916, 923
   - Impacto: Agente terá memória 2x maior

2. **Aumentar limite de truncamento: 500 → 2000**
   - Arquivo: `caculinha_bi_agent.py` linhas 414, 943
   - Impacto: Respostas completas de ferramentas

### MÉDIAS (Implementar em Seguida)

3. **Aumentar lista de colunas: 30 → 50**
   - Arquivo: `caculinha_bi_agent.py` linha 238

4. **Aumentar timeout Code Interpreter: 10s → 30s**
   - Arquivo: `code_interpreter.py` linha 42

5. **Aumentar truncamento DataFrame: 10 → 50**
   - Arquivo: `unified_data_tools.py` linha 17

6. **Aumentar max_tokens Groq: 4096 → 8192** (se modelo suportar)
   - Arquivo: `llm_groq_adapter.py` linha 67

---

## 🔍 Outras Limitações Encontradas

### Hardcoded Limits (Não Parametrizáveis)

| Arquivo | Linha | Código | Impacto |
|---------|-------|--------|---------|
| `code_gen_agent.py` | 181 | `if len(series) >= 365` | Análise de séries temporais limitada |
| `chart_tools.py` | 1344, 1371, 1396 | `.head(10)` | Top 10 grupos (fixo) |
| `une_tools.py` | 289 | `.head(20)` | Top 20 produtos (fixo) |
| `une_tools.py` | 869 | `.head(5)` | Top 5 origens (fixo) |
| `une_tools.py` | 885 | `.head(3)` | Top 3 destinos (fixo) |
| `une_tools.py` | 1593 | `.nlargest(5)` | Top 5 lojas (fixo) |
| `une_tools.py` | 1611 | `.head(10)` | Top 10 rupturas (fixo) |

**Recomendação:** Transformar em parâmetros quando possível.

---

## 📋 Checklist de Implementação

### Fase 1: CRÍTICAS (Agora)
- [ ] Aumentar histórico de contexto: 15 → 30
- [ ] Aumentar truncamento de respostas: 500 → 2000

### Fase 2: MÉDIAS (Próxima)
- [ ] Aumentar lista de colunas: 30 → 50
- [ ] Aumentar timeout Code Interpreter: 10s → 30s
- [ ] Aumentar truncamento DataFrame: 10 → 50
- [ ] Aumentar max_tokens Groq: 4096 → 8192

### Fase 3: BAIXAS (Futuro)
- [ ] Aumentar amostragem gráficos: 2000 → 5000
- [ ] Parametrizar hardcoded limits

---

## ✅ Conclusão

**Principais Problemas:**
1. 🔴 Histórico de contexto muito curto (15 mensagens)
2. 🔴 Truncamento agressivo de respostas (500 chars)
3. 🟡 Múltiplos limites pequenos acumulados

**Após correções:**
- Agente terá memória 2x maior
- Respostas 4x mais completas
- Análises mais profundas e precisas

**Impacto Esperado:**
- ✅ Conversas longas mantêm contexto
- ✅ Análises complexas não são cortadas
- ✅ Agente vê mais dados e colunas
- ✅ Menos timeouts em processamentos
