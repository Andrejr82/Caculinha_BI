# Agent Solution BI - Lojas Caçula (Edição Context7)

Este arquivo `GEMINI.md` fornece contexto essencial para o projeto "Agent Solution BI", uma plataforma de Business Intelligence de alto desempenho integrada com IA Generativa (Google Gemini).

## 🌍 Visão Geral do Projeto

**Agent Solution BI** é uma plataforma de decisão estratégica projetada para a gestão de varejo (Lojas Caçula). Ela transforma milhões de registros de vendas e estoque em planos de ação imediatos usando uma arquitetura híbrida de IA Generativa e processamento de dados colunar.

### Tecnologias Chave
*   **IA/LLM:** Google Gemini 2.5 Pro (Primário - Raciocínio STEM nível PhD), Llama-3 (Secundário/Groq).
*   **Backend:** Python 3.11+, FastAPI.
*   **Motor de Dados:** DuckDB 1.1+ (SQL Analítico), Polars (DataFrames), Apache Parquet (Armazenamento).
*   **Frontend:** SolidJS (UI Reativa), Tailwind CSS.
*   **Arquitetura:** Híbrida (SQL Server + Fallback Parquet), RAG (Retrieval-Augmented Generation).
*   **Analytics:** SciPy (Análise Estatística), Scikit-learn (Machine Learning).

### Recursos Principais
*   **BI Conversacional:** Consultas em linguagem natural ("Como estão as vendas na loja 1685?").
*   **Context7 Ultimate:** Framework avançado de prompt do sistema para narrativa de dados natural (sem saída JSON bruta).
*   **Agente de Dados Autoconsciente:** Injeção dinâmica de esquema permitindo que o LLM inspecione colunas disponíveis em tempo de execução.
*   **Gráficos Universais:** Ferramenta `gerar_grafico_universal_v2` para visualização sob demanda.
*   **Analytics STEM (NOVO 24/01/2026):** Análise estatística avançada (regressão, detecção de anomalias, correlação).
*   **Otimização Multi-Restrição (NOVO 24/01/2026):** EOQ com restrições de orçamento, espaço e nível de serviço.

## 📂 Estrutura de Diretórios

```text
C:\Agente_BI\BI_Solution\
├── backend/                  # Backend Python FastAPI
│   ├── app/
│   │   ├── api/              # Endpoints da API (v1)
│   │   ├── core/             # Lógica Principal (Agentes, Ferramentas, Config)
│   │   │   ├── agents/       # Agentes de IA (CaculinhaBIAgent, MasterPrompt)
│   │   │   └── tools/        # Ferramentas de BI (Gráficos, Consulta de Dados)
│   │   └── services/         # Serviços de Negócio
│   ├── data/                 # Armazenamento de Dados (Parquet, Cache)
│   ├── main.py               # Ponto de Entrada da Aplicação
│   └── .env                  # Variáveis de Ambiente (Chaves API, Config)
├── frontend-solid/           # Frontend SolidJS
│   ├── src/                  # Código Fonte
│   ├── package.json          # Dependências
│   └── vite.config.ts        # Configuração de Build
├── docs/                     # Documentação do Projeto
├── scripts/                  # Scripts Utilitários
├── START_LOCAL_DEV.bat       # Script de Inicialização Local Windows
└── README.md                 # Visão Geral do Projeto
```

## 🚀 Compilação e Execução

### Pré-requisitos
*   Python 3.11+
*   Node.js 18+
*   Chave de API Google Gemini (configurada em `backend/.env`)

### Desenvolvimento Local (Windows)
A maneira recomendada de iniciar o projeto sem Docker é usando o script em lote:

```bat
START_LOCAL_DEV.bat
```

**Início Manual:**

1.  **Backend:**
    ```bash
    cd backend
    # Garanta que o venv esteja ativo se usado
    python main.py
    ```
    *Roda em:* `http://localhost:8000` (Docs: `/docs`)

2.  **Frontend:**
    ```bash
    cd frontend-solid
    npm install  # Apenas na primeira vez
    npm run dev
    ```
    *Roda em:* `http://localhost:3000`

## 🛠️ Convenções de Desenvolvimento

### IA & Engenharia de Prompt
*   **Prompt do Sistema:** Localizado em `backend/app/core/agents/master_prompt.py`. Segue o padrão "Context7 Ultimate".
*   **Regras Context7:**
    1.  **Narrativa Primeiro:** As respostas devem ser texto natural, não despejos de dados brutos.
    2.  **Sem JSON:** Nunca exponha estruturas JSON para o usuário final.
    3.  **Visuais:** Priorize a geração de gráficos (`gerar_grafico_universal_v2`) para solicitações visuais.
    4.  **Autocorreção:** Use `consultar_dicionario_dados` se não tiver certeza sobre o esquema.

### Backend (Python)
*   **Estilo:** Segue PEP 8.
*   **Gerenciamento de Dependências:** `backend/requirements.txt`.
*   **Testes:** `pytest` é usado. Testes principais estão em `backend/tests/` e `backend/verify_gemini_env.py`.

### Frontend (SolidJS)
*   **Gerenciamento de Estado:** Solid Signals e Stores.
*   **Estilização:** Tailwind CSS.

## 🔑 Arquivos de Configuração Chave
*   `backend/.env`: Configuração crítica (Provedor LLM, chaves API, caminhos de banco de dados).
*   `backend/app/core/agents/master_prompt.py`: O "cérebro" do agente (Prompt do Sistema).
*   `backend/app/core/agents/caculinha_bi_agent.py`: Lógica do agente e vinculação de ferramentas.

## 🧮 Ferramentas de Analytics STEM (NOVO 24/01/2026)

### Analytics Avançado (`advanced_analytics_tool.py`)

**1. Análise de Regressão (`analise_regressao_vendas`)**
- Regressão linear e polinomial para análise de tendência
- Métricas de qualidade R²
- Previsão de 30 dias com intervalos de confiança de 95%
- Classificação automática de tendência (crescente/decrescente/estável)

**Exemplo de Consulta:**
```
Analise a tendência de vendas do produto 369947 nos últimos 90 dias usando regressão linear
```

**2. Detecção de Anomalias (`detectar_anomalias_vendas`)**
- Detecção de outliers baseada em Z-score
- Sensibilidade configurável (2.5σ = moderada, 3.0σ = extrema)
- Classificação automática (picos vs quedas de vendas)
- Análise de coeficiente de variação

**Exemplo de Consulta:**
```
Detecte vendas anormais do produto 369947 nos últimos 90 dias
```

**3. Análise de Correlação (`analise_correlacao_produtos`)**
- Matriz de correlação entre produtos
- Identificação de produtos complementares (correlação positiva)
- Identificação de produtos substitutos (correlação negativa)
- Sugestões de estratégia de cross-selling

**Exemplo de Consulta:**
```
Analise a correlação de vendas entre os produtos 369947, 123456 e 789012
```

### Ferramentas de Compras Aprimoradas

**EOQ Multi-Restrição (`calcular_eoq`)**
- Restrições de orçamento (`restricao_orcamento`)
- Restrições de espaço (`restricao_espaco`)
- Consideração de lead time (`lead_time_dias`)
- Otimização de nível de serviço (`nivel_servico`)
- Estoque de segurança probabilístico (baseado em Z-score)

**Exemplo de Consulta:**
```
Calcule o EOQ para produto 369947 considerando orçamento de R$ 5000, 
espaço de 500 unidades, lead time de 15 dias e nível de serviço de 95%
```

## 📝 Contexto Recente & Atualizações
*   **Modelo LLM:** Atualizado para `gemini-2.5-pro` (capacidade estável máxima - raciocínio STEM nível PhD).
*   **Ferramentas STEM:** Adicionadas 3 funções analíticas avançadas (regressão, detecção de anomalias, correlação).
*   **Aprimoramento EOQ:** Otimização multi-restrição com cálculo de estoque de segurança.
*   **Dependências:** Adicionado scipy e scikit-learn para análise estatística.
*   **Autenticação:** Corrigidos problemas de Chave de API no `.env`.
*   **Prompts:** Atualizado `master_prompt.py` para "Context7 Ultimate".
*   **Ferramentas:** Validade conexão com `backend/verify_gemini_env.py`.
