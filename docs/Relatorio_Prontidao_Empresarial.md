# Relatório de Prontidão Empresarial - BI_Solution para Lojas Caçula

**Data:** 22 de Janeiro de 2026  
**Escopo:** Análise de prontidão para atender 30+ usuários (Compras, BI, Marketing, Stakeholders)  
**Foco Prioritário:** Setor de Compras com cálculos complexos (Previsão de Vendas, EOQ, Sazonalidade)

---

## 📊 Resumo Executivo

### ✅ Pontos Fortes Identificados
1. **Arquitetura Sólida:** Sistema metrics-first com validação de dados (ChatServiceV3)
2. **Dashboards Existentes:** 4 dashboards implementados (Dashboard, DashboardV2, Analytics, Rupturas)
3. **Protocolo JSON Estruturado:** Schema bem definido para respostas consistentes
4. **LLM Moderna:** Gemini 2.5 Flash-Lite com capacidade de raciocínio avançado

### 🚨 Lacunas Críticas Identificadas
1. **CodeGenAgent Inativo:** Comentário no código indica "não será usado efetivamente" (linha 96)
2. **Conflito de Protocolos:** Dois prompts conflitantes (Markdown narrativo vs JSON estruturado)
3. **Cálculos Complexos Não Implementados:** Previsão de vendas, EOQ e alocação sazonal ausentes
4. **Escalabilidade de Dashboards:** Dashboards atuais não cobrem todos os departamentos

---

## 🎯 Análise por Requisito Empresarial

### 1. Capacidade de Atender 30+ Usuários Simultâneos

| Componente | Status Atual | Capacidade | Recomendação |
|------------|--------------|------------|--------------|
| **Backend (FastAPI)** | ✅ Implementado | Suporta async/await | Adicionar rate limiting e cache |
| **Banco de Dados** | ⚠️ Parquet único | Limitado para leitura concorrente | Migrar para DuckDB em modo servidor |
| **Autenticação** | ✅ Supabase | Escalável | OK |
| **Session Management** | ✅ Implementado | Suporta múltiplas sessões | OK |

**Conclusão:** Sistema suporta 30+ usuários, mas precisa de otimizações de cache e migração de dados.

---

### 2. Cálculos Complexos para Setor de Compras

#### 2.1. Previsão de Vendas (Time Series Forecasting)

**Requisito:** Prever vendas futuras considerando sazonalidade (Volta às Aulas, Natal, Páscoa)

**Status Atual:** ❌ **NÃO IMPLEMENTADO**

**Evidência:**
```python
# backend/app/core/agents/caculinha_bi_agent.py:96
# We keep code_gen_agent in init to maintain compatibility with chat.py,
# but we won't use it effectively.
self.code_gen_agent = code_gen_agent
```

**Impacto:** Compradores não conseguem fazer previsões baseadas em dados históricos.

**Solução Necessária:**
1. Implementar ferramenta `analisar_historico_vendas` (já existe referência no código)
2. Integrar biblioteca de séries temporais (Prophet, ARIMA ou Statsmodels)
3. Criar endpoint dedicado `/api/v1/forecasting/sales`

---

#### 2.2. Cálculo de Quantidade Ideal de Compra (EOQ - Economic Order Quantity)

**Requisito:** Calcular quantidade ótima de compra considerando:
- Custo de pedido
- Custo de armazenagem
- Demanda prevista
- Lead time do fornecedor

**Status Atual:** ⚠️ **PARCIALMENTE IMPLEMENTADO**

**Evidência:**
- Existe ferramenta `calcular_abastecimento_une` (linha 126 de `caculinha_bi_agent.py`)
- Mas não há evidência de cálculo de EOQ clássico

**Fórmula EOQ Necessária:**
```
EOQ = √(2 × D × S / H)
Onde:
D = Demanda anual
S = Custo por pedido
H = Custo de manutenção de estoque por unidade/ano
```

**Solução Necessária:**
1. Criar ferramenta `calcular_eoq` em `backend/app/core/tools/purchasing_tools.py`
2. Integrar com dados de custo (ULTIMA_ENTRADA_CUSTO_CD)
3. Adicionar parâmetros de custo de pedido e armazenagem

---

#### 2.3. Alocação de Estoque por Sazonalidade

**Requisito:** Distribuir estoque entre 30+ lojas baseado em:
- Histórico de vendas por loja
- Período sazonal (Volta às Aulas aumenta demanda em 200-300%)
- Capacidade de armazenagem por loja

**Status Atual:** ❌ **NÃO IMPLEMENTADO**

**Solução Necessária:**
1. Criar ferramenta `alocar_estoque_sazonal`
2. Implementar algoritmo de alocação proporcional
3. Integrar com detecção de sazonalidade (já proposta no plano anterior)

---

### 3. Dashboards para Múltiplos Departamentos

#### 3.1. Dashboards Existentes

| Dashboard | Arquivo | Público-Alvo | Cobertura |
|-----------|---------|--------------|-----------|
| **Dashboard Principal** | `Dashboard.tsx` | Geral | ✅ Visão geral de vendas |
| **Dashboard V2** | `DashboardV2.tsx` | Geral | ✅ Versão otimizada |
| **Analytics** | `Analytics.tsx` | BI/Analistas | ✅ Análises avançadas |
| **Rupturas** | `Rupturas.tsx` | Compras | ✅ Gestão de rupturas |
| **Transferências** | `Transfers.tsx` | Logística | ✅ Gestão de transferências |

**Conclusão:** Cobertura boa para Compras e BI, mas falta para Marketing e Stakeholders.

#### 3.2. Dashboards Faltantes

| Dashboard Necessário | Público-Alvo | Prioridade | Métricas Principais |
|---------------------|--------------|------------|---------------------|
| **Previsão de Demanda** | Compras | 🔴 CRÍTICA | Forecast 30/60/90 dias, Acurácia, Tendências |
| **Performance de Fornecedores** | Compras | 🟠 ALTA | Lead time, Taxa de ruptura, Custo médio |
| **Campanhas de Marketing** | Marketing | 🟡 MÉDIA | ROI, Conversão, Produtos mais vendidos |
| **Executivo (C-Level)** | Stakeholders | 🟠 ALTA | KPIs consolidados, Alertas críticos |

---

## 🧠 Análise da LLM: Está Preparada?

### Capacidades Atuais da LLM

| Capacidade | Status | Evidência |
|------------|--------|-----------|
| **Raciocínio Complexo** | ✅ Sim | Gemini 2.5 Flash-Lite suporta Chain-of-Thought |
| **Orquestração de Ferramentas** | ✅ Sim | Sistema de function calling implementado |
| **Geração de Gráficos** | ✅ Sim | `gerar_grafico_universal_v2` funcional |
| **Cálculos Matemáticos** | ❌ Não | CodeGenAgent desabilitado |
| **Previsão de Séries Temporais** | ❌ Não | Requer biblioteca especializada |
| **Otimização (EOQ, Alocação)** | ❌ Não | Requer algoritmos implementados |

### Conflito de Protocolos Identificado

**Problema Crítico:** Existem dois prompts conflitantes:

1. **Prompt Context7 (Markdown)** - `Relatorio_Avaliacao_e_Prompt_Unificado.md`
   - Foco: Narrativa natural em Markdown
   - Estrutura: Resumo → Análise → Insights → Ações
   - Saída: Texto formatado para humanos

2. **Prompt JSON Enforcement** - `Prompt Mestre de Protocolo de BI (JSON Enforcement).md`
   - Foco: JSON estruturado e validável
   - Estrutura: Schema rígido com campos obrigatórios
   - Saída: JSON puro (sem texto adicional)

**Impacto:** Sistema não pode usar ambos simultaneamente. Decisão necessária.

### Recomendação de Protocolo

**Para 30+ usuários de múltiplos departamentos:**

✅ **USAR: Protocolo JSON Estruturado**

**Justificativa:**
1. **Consistência:** JSON garante formato previsível para todos os departamentos
2. **Integração:** Facilita consumo por dashboards e APIs externas
3. **Validação:** Schema JSON permite validação automática de respostas
4. **Escalabilidade:** Mais fácil processar programaticamente

**Adaptação Necessária:**
- Manter campo `analise_detalhada` em Markdown dentro do JSON
- Adicionar campo `visualizacao_markdown` para narrativa opcional
- Implementar parser no frontend para renderizar ambos

---

## 🔧 Plano de Implementação Revisado

### Fase 1: Fundação de Cálculos (CRÍTICA - 2 semanas)

#### 1.1. Reativar e Fortalecer CodeGenAgent
**Arquivo:** `backend/app/core/agents/code_gen_agent.py`

**Implementação:**
```python
class CodeGenAgent:
    """Agente para execução segura de cálculos complexos."""
    
    def __init__(self):
        self.sandbox = RestrictedPython()  # Sandbox seguro
        self.available_libs = ['numpy', 'pandas', 'statsmodels']
    
    def execute_forecast(self, data: pd.DataFrame, periods: int) -> Dict:
        """Executa previsão de séries temporais."""
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        
        model = ExponentialSmoothing(
            data['VENDA_30DD'],
            seasonal='mul',
            seasonal_periods=12
        )
        fitted = model.fit()
        forecast = fitted.forecast(periods)
        
        return {
            "forecast": forecast.tolist(),
            "confidence_interval": self._calculate_ci(fitted),
            "accuracy_metrics": self._calculate_accuracy(fitted)
        }
```

**Testes Necessários:**
- ✅ Sandbox não permite acesso ao sistema de arquivos
- ✅ Timeout de 30 segundos para execução
- ✅ Validação de input/output

---

#### 1.2. Criar Ferramentas de Compras Avançadas
**Arquivo:** `backend/app/core/tools/purchasing_tools.py`

**Ferramentas:**

1. **`calcular_eoq`**
```python
@tool
def calcular_eoq(
    produto_id: str,
    demanda_anual: Optional[float] = None,
    custo_pedido: float = 150.0,  # R$ por pedido
    custo_armazenagem_pct: float = 0.25  # 25% do custo unitário/ano
) -> Dict:
    """
    Calcula Economic Order Quantity (EOQ).
    
    Se demanda_anual não for fornecida, calcula baseado em histórico.
    """
    # Obter dados do produto
    produto = get_produto_data(produto_id)
    
    if demanda_anual is None:
        demanda_anual = produto['VENDA_30DD'] * 12
    
    custo_unitario = produto['ULTIMA_ENTRADA_CUSTO_CD']
    custo_armazenagem = custo_unitario * custo_armazenagem_pct
    
    # Fórmula EOQ
    eoq = math.sqrt((2 * demanda_anual * custo_pedido) / custo_armazenagem)
    
    return {
        "eoq": round(eoq, 0),
        "pedidos_por_ano": round(demanda_anual / eoq, 1),
        "custo_total_anual": calculate_total_cost(eoq, demanda_anual, custo_pedido, custo_armazenagem)
    }
```

2. **`prever_demanda_sazonal`**
```python
@tool
def prever_demanda_sazonal(
    produto_id: str,
    periodo_dias: int = 30,
    considerar_sazonalidade: bool = True
) -> Dict:
    """
    Prevê demanda futura considerando sazonalidade.
    """
    # Obter histórico
    historico = get_historico_vendas(produto_id, days=365)
    
    # Detectar sazonalidade
    seasonal_context = detect_seasonal_context()
    
    # Executar previsão via CodeGenAgent
    forecast_result = code_gen_agent.execute_forecast(
        data=historico,
        periods=periodo_dias
    )
    
    # Ajustar por sazonalidade
    if considerar_sazonalidade and seasonal_context:
        multiplicador = seasonal_context['multiplier']  # Ex: 2.5x para Volta às Aulas
        forecast_result['forecast_ajustado'] = [
            v * multiplicador for v in forecast_result['forecast']
        ]
    
    return forecast_result
```

---

### Fase 2: Unificação de Protocolo (1 semana)

#### 2.1. Implementar Protocolo JSON Híbrido
**Arquivo:** `backend/app/core/prompts/master_prompt_v3.py`

**Estrutura:**
```python
MASTER_PROMPT_V3_JSON = """
# SYSTEM PROMPT: AGENTE ESTRATÉGICO DE BI (JSON Protocol v3.0)

## PROTOCOLO DE SAÍDA OBRIGATÓRIO

Você DEVE responder SEMPRE com JSON seguindo este schema:

{
  "protocol_version": "BI_PROTOCOL_V3.0",
  "analise_maturidade": "DESCRITIVA|DIAGNOSTICA|PREDITIVA|PRESCRITIVA|OPERACIONAL",
  "resumo_executivo": "Conclusão em até 3 frases",
  "analise_detalhada": "Análise em Markdown (suporta **negrito**, tabelas, listas)",
  "dados_suporte": [
    {"metrica": "Total Vendas", "valor": "R$ 150.000", "unidade": "BRL"}
  ],
  "recomendacao_prescritiva": {
    "acao_sugerida": "Comprar 4.500 unidades",
    "justificativa": "EOQ calculado + previsão sazonal",
    "riscos": "Ruptura de 15% se não executado"
  },
  "visualizacao": {
    "data": [...],
    "layout": {...}
  },
  "ferramentas_utilizadas": ["calcular_eoq", "prever_demanda_sazonal"]
}

## REGRAS DE RACIOCÍNIO

1. SAZONALIDADE PRIMEIRO: Sempre verificar período sazonal
2. CÁLCULOS COMPLEXOS: Usar code_gen_agent para previsões e EOQ
3. ESPECIFICIDADE: Citar produtos, SKUs e valores reais
4. PROFUNDIDADE: analise_detalhada deve ter mínimo 5 frases

## FERRAMENTAS DISPONÍVEIS

- calcular_eoq: Quantidade ideal de compra
- prever_demanda_sazonal: Previsão com ajuste sazonal
- alocar_estoque_lojas: Distribuição entre lojas
- consultar_dados_flexivel: Consulta SQL-like
- gerar_grafico_universal_v2: Visualizações
"""
```

---

### Fase 3: Dashboards para Todos os Departamentos (2 semanas)

#### 3.1. Dashboard de Previsão de Demanda (Compras)
**Arquivo:** `frontend-solid/src/pages/Forecasting.tsx`

**Componentes:**
- Gráfico de previsão 30/60/90 dias
- Tabela de produtos críticos
- Alertas de sazonalidade
- Calculadora de EOQ integrada

#### 3.2. Dashboard Executivo (Stakeholders)
**Arquivo:** `frontend-solid/src/pages/Executive.tsx`

**Componentes:**
- KPIs consolidados (Vendas, Margem, Ruptura)
- Alertas críticos em tempo real
- Comparativo mês anterior
- Top 10 produtos/categorias

---

## 📋 Checklist de Prontidão Empresarial

### Infraestrutura
- [ ] Migrar de Parquet único para DuckDB em modo servidor
- [ ] Implementar cache Redis para queries frequentes
- [ ] Configurar rate limiting (100 req/min por usuário)
- [ ] Implementar monitoramento (Prometheus + Grafana)

### Cálculos Complexos
- [ ] Reativar CodeGenAgent com sandbox seguro
- [ ] Implementar `calcular_eoq`
- [ ] Implementar `prever_demanda_sazonal`
- [ ] Implementar `alocar_estoque_lojas`
- [ ] Criar testes unitários para cada ferramenta

### Protocolo e LLM
- [ ] Unificar em Protocolo JSON v3.0
- [ ] Atualizar `chat_service_v3.py` para usar novo prompt
- [ ] Implementar validação de schema JSON na resposta
- [ ] Criar fallback para quando LLM não retornar JSON válido

### Dashboards
- [ ] Criar `Forecasting.tsx` (Previsão de Demanda)
- [ ] Criar `Executive.tsx` (Dashboard Executivo)
- [ ] Criar `Suppliers.tsx` (Performance de Fornecedores)
- [ ] Otimizar dashboards existentes para 30+ usuários

### Testes e Validação
- [ ] Teste de carga (30 usuários simultâneos)
- [ ] Teste de precisão de previsões (comparar com dados reais)
- [ ] Teste de cálculo de EOQ (validar com planilhas existentes)
- [ ] Teste de usabilidade com compradores reais

---

## 🎯 Resposta às Perguntas do Usuário

### 1. A LLM está preparada?

**Resposta:** ⚠️ **PARCIALMENTE**

- ✅ **Raciocínio e Orquestração:** Sim, Gemini 2.5 Flash-Lite é capaz
- ❌ **Execução de Cálculos:** Não, CodeGenAgent está desabilitado
- ⚠️ **Protocolo Consistente:** Conflito entre Markdown e JSON (precisa unificar)

**Ação Necessária:** Reativar CodeGenAgent e unificar protocolo para JSON v3.0

---

### 2. Os dashboards atendem esta demanda?

**Resposta:** ⚠️ **PARCIALMENTE**

**Dashboards Existentes:**
- ✅ Compras: `Rupturas.tsx`, `Transfers.tsx` (bom)
- ✅ BI: `Analytics.tsx` (bom)
- ❌ Marketing: Não existe
- ❌ Stakeholders: Não existe dashboard executivo consolidado
- ❌ Previsão de Demanda: Não existe

**Cobertura Atual:** ~50% das necessidades

**Ação Necessária:** Criar 3 novos dashboards (Forecasting, Executive, Suppliers)

---

## 🚀 Cronograma de Implementação

| Fase | Duração | Entregáveis | Prioridade |
|------|---------|-------------|------------|
| **Fase 1: Cálculos** | 2 semanas | CodeGenAgent + 3 ferramentas de compras | 🔴 CRÍTICA |
| **Fase 2: Protocolo** | 1 semana | Unificação JSON v3.0 + testes | 🔴 CRÍTICA |
| **Fase 3: Dashboards** | 2 semanas | 3 novos dashboards | 🟠 ALTA |
| **Fase 4: Otimização** | 1 semana | Cache, rate limiting, monitoramento | 🟡 MÉDIA |

**Total:** 6 semanas para sistema production-ready

---

## 💰 Estimativa de Esforço

- **Desenvolvimento:** 240 horas (6 semanas × 40h)
- **Testes:** 40 horas
- **Documentação:** 20 horas
- **Total:** 300 horas (~2 meses com 1 desenvolvedor)

---

## 📚 Referências Técnicas

1. **EOQ (Economic Order Quantity):** [Investopedia - EOQ](https://www.investopedia.com/terms/e/economicorderquantity.asp)
2. **Time Series Forecasting:** [Statsmodels Documentation](https://www.statsmodels.org/stable/tsa.html)
3. **Seasonal Decomposition:** [Prophet by Meta](https://facebook.github.io/prophet/)
4. **DuckDB Performance:** [DuckDB Benchmarks](https://duckdb.org/why_duckdb)

---

**Conclusão Final:** O sistema BI_Solution possui uma base arquitetural sólida, mas requer implementação de cálculos complexos (CodeGenAgent) e novos dashboards para atender plenamente 30+ usuários de múltiplos departamentos. Com 6 semanas de desenvolvimento focado, o sistema estará production-ready.
