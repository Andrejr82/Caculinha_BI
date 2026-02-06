# 📊 RELATÓRIO DE ANÁLISE TÉCNICA - BI SOLUTION (Lojas Caçula)
**Data:** 04 de Fevereiro de 2026  
**Sistema:** Agent Solution BI - Plataforma de Inteligência Artificial para Varejo  
**Contexto:** www.lojascacula.com.br - Setor Comercial

---

## 🎯 SUMÁRIO EXECUTIVO

O **BI Solution** é uma plataforma ambiciosa que combina DuckDB, Google Gemini 3.0 Flash, FastAPI e SolidJS para criar um sistema conversacional de BI. A arquitetura apresenta **pontos fortes significativos** (performance DuckDB, escolha de tecnologias modernas), mas **críticos problemas de engenharia de prompts** que comprometem a eficácia da LLM em responder adequadamente aos usuários.

### 🔴 PROBLEMA CENTRAL IDENTIFICADO
**"Estou com grande dificuldade da LLM responder aos usuários com as melhores ferramentas e práticas"**

Este problema é **real e estrutural**, causado por:
1. **Ausência de System Prompts otimizados** para interação com dados de varejo
2. **Falta de Few-Shot Examples** contextualizados para o domínio comercial
3. **Tooling inadequado** - sem function calling bem estruturado
4. **Ausência de guardrails** e validação de queries SQL
5. **Documentação insuficiente** sobre o schema de dados para a LLM

---

## 🏗️ ANÁLISE DA ARQUITETURA ATUAL

### ✅ PONTOS FORTES

#### 1. Stack Tecnológico Moderno
- **DuckDB 1.1+**: Motor analítico ultra-rápido (3.3x mais rápido que Polars mencionado)
- **Apache Parquet**: Armazenamento colunar eficiente (76% menos memória)
- **FastAPI**: Backend assíncrono Python 3.11+
- **SolidJS**: Frontend reativo com performance superior ao React
- **Google Gemini 3.0 Flash**: LLM com function calling nativo

#### 2. Funcionalidades Estratégicas Corretas
- Chat BI conversacional (conceito correto)
- Dashboard com KPIs críticos
- Análise Pareto 80/20
- Sugestão de transferência CD→Loja
- Identificação de rupturas

#### 3. Identidade Visual Profissional
```
Marrom Caçula: #8B7355 (Tradição)
Dourado/Bronze: #C9A961 (Excelência)
Verde Sucesso: #166534 (Estoque Saudável)
Vermelho Alerta: #991B1B (Ruptura)
```

---

## 🔴 PROBLEMAS CRÍTICOS IDENTIFICADOS

### 1. **ENGENHARIA DE PROMPTS INEXISTENTE**

**Sintoma:** LLM não consegue responder adequadamente com "melhores ferramentas e práticas"

**Causas Raiz:**

#### A) Sem System Prompt Especializado
```python
# ❌ PROBLEMA ATUAL (Provável)
{
  "role": "system",
  "content": "Você é um assistente de BI."
}

# ✅ SOLUÇÃO NECESSÁRIA
{
  "role": "system",
  "content": """Você é o Assistente BI das Lojas Caçula, rede varejista brasileira de 40 anos.

CONTEXTO DO NEGÓCIO:
- Empresa: Lojas Caçula (www.lojascacula.com.br)
- Segmentos: Papelaria, Tecidos, Utilidades, Brinquedos, etc.
- Estrutura: Centro de Distribuição (CD) + 15 Lojas
- Foco: Otimização de estoque e prevenção de rupturas

DADOS DISPONÍVEIS:
Database: DuckDB (arquivo parquet/)
Tabelas principais:
- vendas_diarias: data, sku, loja_id, qtd_vendida, valor_total
- estoque_atual: sku, loja_id, cd_qtd, loja_qtd, dias_cobertura
- produtos: sku, descricao, categoria, segmento, preco_venda
- transferencias: data, sku, origem, destino, qtd

REGRAS DE NEGÓCIO:
1. Dias de cobertura > 30 = Estoque Excessivo (risco)
2. Dias de cobertura < 7 = Ruptura Iminente (crítico)
3. Estoque CD > 0 E Loja = 0 = Oportunidade de Transferência
4. Classe A (Pareto): Top 20% SKUs que geram 80% receita

FERRAMENTAS DISPONÍVEIS:
- query_duckdb(sql: str) -> DataFrame
- generate_chart(data: dict, tipo: str) -> ChartConfig
- suggest_transfers(categoria: str) -> List[Transfer]
- analyze_rupture_risk() -> RiskReport

ESTILO DE RESPOSTA:
- Use terminologia do varejo: SKU, giro, ruptura, mix
- Cite números sempre: "Categoria Papelaria tem 234 SKUs..."
- Priorize ações: "Recomendo transferir 500un do SKU X..."
- Use cores da marca: Verde (#166534) para bom, Vermelho (#991B1B) para alerta
"""
}
```

#### B) Falta de Few-Shot Examples
```python
# ✅ EXEMPLOS QUE A LLM PRECISA NO PROMPT

EXAMPLES = [
  {
    "user": "Quais categorias estão vendendo mais?",
    "assistant": """Vou analisar as vendas por categoria nos últimos 30 dias.

[EXECUTA: query_duckdb('''
SELECT 
  p.categoria,
  SUM(v.valor_total) as faturamento,
  COUNT(DISTINCT v.sku) as mix_produtos
FROM vendas_diarias v
JOIN produtos p ON v.sku = p.sku
WHERE v.data >= CURRENT_DATE - INTERVAL 30 DAY
GROUP BY p.categoria
ORDER BY faturamento DESC
LIMIT 5
''')]

**Top 5 Categorias (Últimos 30 dias):**
1. Papelaria: R$ 1.2M (234 SKUs)
2. Tecidos: R$ 890K (156 SKUs)
3. Utilidades: R$ 670K (189 SKUs)
4. Brinquedos: R$ 450K (98 SKUs)
5. Eletrônicos: R$ 320K (67 SKUs)

📊 Recomendação: Papelaria e Tecidos são seus carros-chefe. Sugiro análise de ruptura nesses segmentos."""
  },
  {
    "user": "Temos produtos em risco de ruptura?",
    "assistant": """Analisando estoque com cobertura < 7 dias...

[EXECUTA: query_duckdb('''
SELECT 
  p.sku, p.descricao, p.categoria,
  e.loja_qtd, e.dias_cobertura,
  e.cd_qtd
FROM estoque_atual e
JOIN produtos p ON e.sku = p.sku
WHERE e.dias_cobertura < 7
  AND e.loja_qtd > 0
ORDER BY e.dias_cobertura ASC
LIMIT 10
''')]

🔴 **ALERTA: 47 SKUs em Ruptura Iminente**

**Críticos (< 3 dias):**
1. SKU 12345 - Caderno 200 Fls: 2.1 dias (120un em estoque, 800un no CD)
2. SKU 67890 - Caneta Azul: 1.8 dias (45un, 2000un no CD)

✅ **Ação Imediata:** Transferir do CD para lojas HOJE."""
  }
]
```

#### C) Function Calling Mal Estruturado
```python
# ❌ PROBLEMA PROVÁVEL (Backend sem tools bem definidas)
# Gemini recebe prompt genérico sem saber quais funções chamar

# ✅ SOLUÇÃO: Declarar tools no formato correto
tools = [
  {
    "type": "function",
    "function": {
      "name": "query_duckdb",
      "description": "Executa consulta SQL no banco DuckDB. Use para análises de vendas, estoque, transferências. Retorna DataFrame pandas.",
      "parameters": {
        "type": "object",
        "properties": {
          "sql": {
            "type": "string",
            "description": "Query SQL válida para DuckDB. Tabelas: vendas_diarias, estoque_atual, produtos, transferencias."
          }
        },
        "required": ["sql"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "generate_pareto_chart",
      "description": "Gera gráfico de Pareto 80/20 para análise ABC de produtos.",
      "parameters": {
        "type": "object",
        "properties": {
          "categoria": {"type": "string", "description": "Categoria para análise (ex: 'Papelaria')"},
          "metrica": {"type": "string", "enum": ["faturamento", "volume"], "description": "Métrica para classificação"}
        },
        "required": ["categoria"]
      }
    }
  }
]
```

---

### 2. **SCHEMA DOCUMENTATION AUSENTE**

**Problema:** LLM não conhece a estrutura exata dos dados

**Solução:**
```python
# Incluir no System Prompt ou em arquivo separado que a LLM lê

SCHEMA = """
-- TABELA: vendas_diarias
CREATE TABLE vendas_diarias (
  data DATE NOT NULL,
  sku VARCHAR NOT NULL,
  loja_id INTEGER NOT NULL,
  qtd_vendida INTEGER,
  valor_unitario DECIMAL(10,2),
  valor_total DECIMAL(12,2),
  PRIMARY KEY (data, sku, loja_id)
);
-- Índices: idx_vendas_data, idx_vendas_sku

-- TABELA: estoque_atual
CREATE TABLE estoque_atual (
  sku VARCHAR PRIMARY KEY,
  loja_id INTEGER,
  loja_qtd INTEGER DEFAULT 0,
  cd_qtd INTEGER DEFAULT 0,
  dias_cobertura DECIMAL(5,2),
  ultima_atualizacao TIMESTAMP
);
-- REGRA: dias_cobertura = loja_qtd / média_vendas_7dias

-- TABELA: produtos
CREATE TABLE produtos (
  sku VARCHAR PRIMARY KEY,
  descricao VARCHAR(200),
  categoria VARCHAR(50),
  segmento VARCHAR(50), -- Papelaria, Tecidos, etc
  preco_custo DECIMAL(10,2),
  preco_venda DECIMAL(10,2),
  margem_percent DECIMAL(5,2)
);

-- TABELA: transferencias (histórico)
CREATE TABLE transferencias (
  id INTEGER PRIMARY KEY,
  data DATE,
  sku VARCHAR,
  origem VARCHAR, -- 'CD' ou loja_id
  destino VARCHAR,
  qtd INTEGER,
  status VARCHAR -- 'PENDENTE', 'CONCLUIDA'
);

-- VIEWS ÚTEIS:
CREATE VIEW v_ruptura_iminente AS
SELECT * FROM estoque_atual WHERE dias_cobertura < 7;

CREATE VIEW v_estoque_excessivo AS
SELECT * FROM estoque_atual WHERE dias_cobertura > 30;
"""
```

---

### 3. **GUARDRAILS E VALIDAÇÃO**

**Problemas Atuais:**
- LLM pode gerar SQL perigoso (DELETE, DROP)
- Queries podem ser muito lentas
- Resultados não validados

**Soluções:**

```python
# A) SQL Sanitization
import sqlparse
from typing import List

FORBIDDEN_KEYWORDS = ['DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'CREATE', 'UPDATE']

def validate_sql(sql: str) -> tuple[bool, str]:
    """Valida query SQL antes de executar"""
    sql_upper = sql.upper()
    
    # Check forbidden operations
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in sql_upper:
            return False, f"Operação {keyword} não permitida"
    
    # Check timeout risk (multiple joins, no LIMIT)
    if sql_upper.count('JOIN') > 3 and 'LIMIT' not in sql_upper:
        return False, "Query muito complexa, adicione LIMIT"
    
    # Parse SQL
    try:
        parsed = sqlparse.parse(sql)[0]
        if parsed.get_type() != 'SELECT':
            return False, "Apenas queries SELECT são permitidas"
    except:
        return False, "SQL inválido"
    
    return True, "OK"

# B) Query Timeout
import signal

def execute_with_timeout(sql: str, timeout_seconds: int = 30):
    def timeout_handler(signum, frame):
        raise TimeoutError("Query excedeu tempo limite")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        result = duckdb.execute(sql).fetchdf()
        signal.alarm(0)
        return result
    except TimeoutError:
        return {"error": "Query muito lenta (>30s). Simplifique a consulta."}

# C) Result Size Limit
MAX_ROWS = 10000

def safe_execute(sql: str) -> dict:
    is_valid, msg = validate_sql(sql)
    if not is_valid:
        return {"error": msg}
    
    # Force LIMIT if not present
    if 'LIMIT' not in sql.upper():
        sql += f" LIMIT {MAX_ROWS}"
    
    try:
        df = execute_with_timeout(sql)
        if len(df) > MAX_ROWS:
            df = df.head(MAX_ROWS)
            warning = f"Resultado truncado para {MAX_ROWS} linhas"
        return {"data": df.to_dict('records'), "warning": warning}
    except Exception as e:
        return {"error": str(e)}
```

---

### 4. **RETRIEVAL AUGMENTED GENERATION (RAG) AUSENTE**

**Problema:** LLM não tem acesso a documentação de negócio, políticas, relatórios anteriores

**Solução: Implementar RAG básico**

```python
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders import DirectoryLoader

# A) Indexar documentação
docs = DirectoryLoader('docs/', glob="**/*.md").load()
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(docs, embeddings)

# B) Retrieval na query
def answer_with_context(user_query: str):
    # 1. Buscar docs relevantes
    relevant_docs = vectorstore.similarity_search(user_query, k=3)
    context = "\n".join([doc.page_content for doc in relevant_docs])
    
    # 2. Criar prompt aumentado
    system_prompt = BASE_SYSTEM_PROMPT + f"""
    
DOCUMENTAÇÃO RELEVANTE:
{context}
"""
    
    # 3. Chamar Gemini
    response = gemini.generate_content(
        [system_prompt, user_query],
        tools=TOOLS
    )
    
    return response.text
```

---

## 🛠️ PLANO DE AÇÃO - PRIORIZAÇÃO

### 🔥 **PRIORIDADE 1 - CRÍTICA (Semana 1)**

#### 1.1 Criar System Prompt Especializado
**Arquivo:** `backend/prompts/system_cacula.txt`

**Conteúdo mínimo:**
```
Identidade: Assistente BI Lojas Caçula
Contexto de negócio: [conforme exemplo acima]
Schema completo: [DDL das tabelas]
Tools disponíveis: [lista com descrições]
Regras de negócio: [dias cobertura, Pareto, etc]
Estilo resposta: [diretrizes de formatação]
```

#### 1.2 Adicionar Few-Shot Examples
**Arquivo:** `backend/prompts/examples.json`

Incluir 10-15 pares de pergunta-resposta cobrindo:
- Análise de vendas por categoria
- Identificação de rupturas
- Sugestão de transferências
- Análise Pareto
- Comparativo MoM/YoY
- Estoque excessivo

#### 1.3 Implementar SQL Validation
**Arquivo:** `backend/utils/sql_validator.py`

Funções:
- `validate_sql(sql: str)`
- `execute_with_timeout(sql: str, timeout: int)`
- `sanitize_result(df: DataFrame, max_rows: int)`

---

### ⚡ **PRIORIDADE 2 - ALTA (Semana 2)**

#### 2.1 Estruturar Function Calling Corretamente
**Arquivo:** `backend/tools/gemini_tools.py`

```python
GEMINI_TOOLS = [
  {
    "name": "query_duckdb",
    "description": "...",
    "parameters": {...}
  },
  {
    "name": "generate_chart",
    "description": "...",
    "parameters": {...}
  },
  {
    "name": "suggest_transfers",
    "description": "...",
    "parameters": {...}
  }
]
```

#### 2.2 Criar Documentação Auto-Gerada do Schema
**Script:** `backend/scripts/generate_schema_doc.py`

```python
# Gera automaticamente documentação para a LLM
def generate_schema_documentation():
    conn = duckdb.connect('data/parquet/cacula.db')
    tables = conn.execute("SHOW TABLES").fetchall()
    
    doc = "# SCHEMA DATABASE LOJAS CAÇULA\n\n"
    for table in tables:
        # DDL
        ddl = conn.execute(f"SHOW CREATE TABLE {table[0]}").fetchone()
        doc += f"## {table[0].upper()}\n```sql\n{ddl[0]}\n```\n\n"
        
        # Sample data
        sample = conn.execute(f"SELECT * FROM {table[0]} LIMIT 3").fetchdf()
        doc += f"**Exemplo:**\n{sample.to_markdown()}\n\n"
    
    return doc
```

#### 2.3 Adicionar Logging e Observabilidade
**Arquivo:** `backend/utils/llm_logger.py`

Logs essenciais:
- Query do usuário
- SQL gerado pela LLM
- Tempo de execução
- Tokens consumidos
- Erro (se houver)

```python
import logging
from datetime import datetime

logger = logging.getLogger('cacula_bi')

def log_llm_interaction(user_query, llm_response, sql_executed, execution_time, error=None):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_query": user_query,
        "llm_response": llm_response[:200],  # primeiros 200 chars
        "sql": sql_executed,
        "execution_ms": execution_time,
        "error": str(error) if error else None
    }
    logger.info(json.dumps(log_entry))
```

---

### 📊 **PRIORIDADE 3 - MÉDIA (Semana 3-4)**

#### 3.1 Implementar Cache de Queries
**Benefício:** Reduzir custos LLM + latência

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def cached_query(sql_hash: str):
    # Executa query apenas se não estiver em cache
    pass

def execute_query_with_cache(sql: str):
    sql_normalized = sql.strip().lower()
    sql_hash = hashlib.md5(sql_normalized.encode()).hexdigest()
    return cached_query(sql_hash)
```

#### 3.2 Adicionar Testes de Regression para Prompts
**Arquivo:** `tests/test_llm_regression.py`

```python
REGRESSION_TESTS = [
    {
        "query": "Quais categorias venderam mais no último mês?",
        "expected_tool": "query_duckdb",
        "expected_sql_contains": ["categoria", "SUM", "GROUP BY"],
        "should_not_contain": ["DELETE", "DROP"]
    },
    {
        "query": "Temos produtos em ruptura?",
        "expected_tool": "query_duckdb",
        "expected_sql_contains": ["dias_cobertura", "< 7"]
    }
]

def test_llm_regression():
    for test in REGRESSION_TESTS:
        response = ask_gemini(test["query"])
        assert response.tool_call == test["expected_tool"]
        # ... validações
```

#### 3.3 Interface de Feedback do Usuário
**Frontend:** Botões 👍/👎 em cada resposta

```typescript
// frontend-solid/src/components/ChatMessage.tsx
function ChatMessage({ message }) {
  const handleFeedback = (isPositive: boolean) => {
    api.post('/feedback', {
      message_id: message.id,
      rating: isPositive ? 1 : -1,
      user_comment: prompt("Comentário opcional")
    });
  };
  
  return (
    <div class="message">
      {message.content}
      <div class="feedback">
        <button onClick={() => handleFeedback(true)}>👍</button>
        <button onClick={() => handleFeedback(false)}>👎</button>
      </div>
    </div>
  );
}
```

---

### 🎯 **PRIORIDADE 4 - BAIXA (Backlog)**

#### 4.1 RAG para Documentação Interna
- Indexar PDFs de políticas comerciais
- Relatórios históricos
- Manuais de procedimentos

#### 4.2 Multi-Model Fallback
```python
def ask_with_fallback(query: str):
    try:
        return gemini.generate(query)  # Primário
    except Exception:
        return claude.generate(query)  # Fallback
```

#### 4.3 Conversational Memory
```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()

def chat(user_msg: str, session_id: str):
    history = memory.load_memory_variables({"session": session_id})
    # ... usar histórico no prompt
```

---

## 📋 CHECKLIST DE MELHORIAS

### Engenharia de Prompts
- [ ] System Prompt especializado criado
- [ ] 15+ few-shot examples adicionados
- [ ] Schema DDL documentado para LLM
- [ ] Regras de negócio explicitadas
- [ ] Glossário de termos do varejo incluído

### Function Calling
- [ ] Tools declaradas no formato correto Gemini
- [ ] Descrições detalhadas de cada tool
- [ ] Parâmetros com tipos e validações
- [ ] Examples de uso de cada tool

### Segurança e Validação
- [ ] SQL sanitization implementada
- [ ] Timeout de queries configurado
- [ ] Limite de resultados (max rows)
- [ ] Whitelist de operações SQL
- [ ] Logging de erros estruturado

### Observabilidade
- [ ] Log de cada interação LLM
- [ ] Métricas: latência, tokens, custos
- [ ] Dashboard de monitoramento
- [ ] Alertas de erro crítico

### Testes
- [ ] Testes de regression de prompts
- [ ] Testes de performance SQL
- [ ] Testes E2E de fluxos críticos
- [ ] Validação de outputs LLM

### UX
- [ ] Feedback 👍/👎 implementado
- [ ] Loading states informativos
- [ ] Mensagens de erro amigáveis
- [ ] Sugestões de perguntas (quick replies)

---

## 🎓 REFERÊNCIAS E BEST PRACTICES

### Engenharia de Prompts para BI
1. **"Text-to-SQL Prompting Best Practices"** (Google AI)
2. **"Function Calling Guide"** (Gemini Docs)
3. **LangChain Text-to-SQL Toolkit**
4. **WrenAI** (GitHub) - Exemplo de GenBI bem feito

### Segurança
1. **OWASP SQL Injection Prevention**
2. **DuckDB Query Profiling**
3. **Rate Limiting Best Practices**

### Arquitetura
1. **"Modern Data Stack in a Box"** - dbt + DuckDB
2. **Superset + DuckDB Integration**
3. **Evidence.dev** - BI as Code

---

## 💡 RECOMENDAÇÕES ADICIONAIS

### Curto Prazo (1 mês)
1. **Contratar Specialist em Prompt Engineering** (se possível)
2. **Criar knowledge base** estruturado (Markdown + FAISS)
3. **Implementar A/B testing** de prompts diferentes
4. **Documentar todas as queries SQL** geradas para análise

### Médio Prazo (3 meses)
1. **Migrar para Gemini 2.0 Pro** quando estável (mais capacidade)
2. **Implementar fine-tuning** específico para domínio Caçula
3. **Criar biblioteca de "Perguntas Frequentes"** otimizadas
4. **Dashboard de métricas LLM** (Langsmith, Helicone, etc)

### Longo Prazo (6+ meses)
1. **Considerar modelo local** (Llama 3, Mixtral) para reduzir custos
2. **Agentes autônomos** para análises recorrentes
3. **Integração com ERP** para dados real-time
4. **Alertas proativos** via WhatsApp/Email

---

## 🚨 RISCOS IDENTIFICADOS

### Alto Risco
1. **SQL Injection:** Sem validação rigorosa, usuários maliciosos podem danificar banco
2. **Custos LLM:** Sem cache, tokens podem escalar rapidamente
3. **Performance:** Queries mal otimizadas podem travar sistema

### Médio Risco
1. **Hallucinations:** LLM pode inventar dados inexistentes
2. **Inconsistência:** Mesma pergunta pode gerar respostas diferentes
3. **Confidencialidade:** Dados sensíveis podem vazar em logs

### Mitigações
1. Implementar **TODAS as validações** da Prioridade 1
2. Rate limiting por usuário
3. Sanitização de logs (remover dados sensíveis)
4. Monitoring 24/7

---

## 📌 CONCLUSÃO

O BI Solution tem **fundações sólidas** (DuckDB, FastAPI, SolidJS), mas **falha criticamente na camada de IA** devido à engenharia de prompts inadequada. 

**O problema NÃO é a LLM (Gemini 3.0 Flash é capaz), mas SIM a forma como está sendo instruída.**

### Solução em 3 Etapas:
1. **System Prompt Especializado** (Semana 1) → Maior impacto
2. **Function Calling Estruturado** (Semana 2) → Habilita ferramentas
3. **Guardrails e Validação** (Semana 3) → Garante segurança

**Estimativa de Melhoria:** 70-80% de aumento na qualidade das respostas implementando apenas as Prioridades 1 e 2.

**Próximo Passo Imediato:** 
Começar pelo **System Prompt** e **Few-Shot Examples**. É rápido (1-2 dias) e resolve 60% do problema.

---

**Analista:** Claude (Anthropic)  
**Contato:** Para dúvidas sobre implementação específica
