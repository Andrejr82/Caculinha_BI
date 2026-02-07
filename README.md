# Caculinha BI Agent Platform v2.0

> **Plataforma de Business Intelligence Conversacional com Agentes de IA**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Visão Geral

Plataforma de BI que permite consultas em **linguagem natural** sobre dados de varejo, utilizando **8 agentes especializados** orquestrados por IA (Google Gemini).

```
"Como estão as vendas da loja 1685 este mês?"
     ↓
[OrchestratorAgent] → [SQLAgent] → DuckDB → [InsightAgent]
     ↓
"As vendas da loja 1685 totalizaram R$ 125.430,00 este mês, 
um crescimento de 12% comparado ao mesmo período do ano anterior..."
```

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (SolidJS)                   │
└────────────────────────┬────────────────────────────────┘
                         │ REST/SSE
┌────────────────────────▼────────────────────────────────┐
│                     API Layer (FastAPI)                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ /auth    │ │ /chat    │ │ /agents  │ │ /metrics │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
├─────────────────────────────────────────────────────────┤
│                   Middleware Layer                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
│  │ Auth/JWT │ │ Tenant   │ │RateLimit │                 │
│  └──────────┘ └──────────┘ └──────────┘                 │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│               Application Layer (Agents)                │
│  ┌────────────────────────────────────────────┐         │
│  │            OrchestratorAgent               │         │
│  └──────────────────┬─────────────────────────┘         │
│         ┌───────────┼───────────┬───────────┐           │
│    ┌────▼────┐ ┌────▼────┐ ┌────▼────┐ ┌────▼────┐      │
│    │SQLAgent │ │Insight  │ │Forecast │ │Metadata │      │
│    └─────────┘ │Agent    │ │Agent    │ │Agent    │      │
│                └─────────┘ └─────────┘ └─────────┘      │
│    ┌─────────┐ ┌─────────┐ ┌─────────┐                  │
│    │Tenant   │ │Security │ │Monitor  │                  │
│    │Agent    │ │Agent    │ │Agent    │                  │
│    └─────────┘ └─────────┘ └─────────┘                  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Infrastructure Layer                        │
│    ┌─────────────────┐    ┌─────────────────┐           │
│    │  GeminiAdapter  │    │  DuckDBAdapter  │           │
│    │  (LLM Port)     │    │  (Data Port)    │           │
│    └────────┬────────┘    └────────┬────────┘           │
│             │                      │                     │
│    ┌────────▼────────┐    ┌────────▼────────┐           │
│    │  Google Gemini  │    │  Parquet Files  │           │
│    └─────────────────┘    └─────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Pré-requisitos

- Python 3.11+
- Google Gemini API Key

### Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-repo/caculinha-bi.git
cd caculinha-bi

# Crie um virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instale dependências
pip install -r backend/requirements.txt

# Configure variáveis de ambiente
cp backend/.env.example backend/.env
# Edite backend/.env e adicione sua GEMINI_API_KEY
```

### Execução

```bash
# Desenvolvimento
cd backend
python main.py

# Ou com uvicorn
uvicorn backend.main:app --reload --port 8000
```

### Docker

```bash
# Build
docker build -t caculinha-bi:latest .

# Run
docker run -p 8000:8000 --env-file backend/.env caculinha-bi:latest

# Ou com docker-compose
docker-compose up -d
```

## 📚 API Endpoints

### Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v2/auth/login` | Login (retorna JWT) |
| GET | `/api/v2/auth/me` | Perfil do usuário |
| POST | `/api/v2/auth/refresh` | Renovar token |

### Chat

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v2/chat` | Chat síncrono |
| POST | `/api/v2/chat/stream` | Chat com SSE |

### Agentes

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v2/agents` | Lista agentes |
| GET | `/api/v2/agents/{name}` | Detalhes do agente |

### Métricas

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v2/metrics` | Métricas da aplicação |
| GET | `/api/v2/metrics/usage` | Uso do tenant |
| GET | `/api/v2/metrics/invoice` | Gerar fatura |

## 🤖 Agentes

| Agente | Função |
|--------|--------|
| **OrchestratorAgent** | Coordena agentes e roteia requisições |
| **SQLAgent** | Executa queries SQL via DuckDB |
| **InsightAgent** | Gera narrativas e insights |
| **ForecastAgent** | Previsões e tendências |
| **MetadataAgent** | Schema e dicionário de dados |
| **TenantAgent** | Multi-tenancy e isolamento |
| **SecurityAgent** | Validação de acesso e auditoria |
| **MonitoringAgent** | Saúde do sistema e alertas |

## 💼 Planos

| Plano | Requests/Hora | Tokens | Features |
|-------|---------------|--------|----------|
| **Free** | 100 | 4K | chat, basic_insights |
| **Pro** | 1.000 | 8K | + sql, forecasts |
| **Enterprise** | 10.000 | 32K | + custom_agents, api |

## 🧪 Testes

```bash
# Todos os testes
pytest .agent/tests/ -v

# Por fase
pytest .agent/tests/test_fase5_api_async.py -v   # API
pytest .agent/tests/test_fase6_saas.py -v        # Auth/SaaS
pytest .agent/tests/test_fase7_observability.py -v # Métricas
```

## 📁 Estrutura do Projeto

```
backend/
├── main.py                 # Entrypoint
├── domain/                 # Entidades e Ports
│   ├── entities/           # Modelos de domínio
│   ├── value_objects/      # Value Objects
│   └── ports/              # Interfaces
├── application/            # Casos de uso e Agentes
│   └── agents/             # 8 Agentes especializados
├── infrastructure/         # Adapters
│   └── adapters/
│       ├── llm/            # GeminiAdapter
│       └── data/           # DuckDBAdapter
├── api/                    # Camada de API
│   ├── middleware/         # Auth, Tenant, RateLimit
│   └── v2/endpoints/       # Routers
└── services/               # Serviços de infraestrutura
    ├── metrics.py          # Observabilidade
    ├── billing.py          # Billing
    └── logging_config.py   # Logs
```

## 🔐 Segurança

- JWT para autenticação
- Rate limiting por plano
- Isolamento de dados por tenant
- Logs estruturados para auditoria

## 📊 Observabilidade

- **Métricas**: Contadores, gauges, histogramas
- **Logs**: Structlog JSON
- **Health Checks**: `/ping`, `/api/v2/health`

## 📝 Licença

MIT License - Veja [LICENSE](LICENSE)

---

**Desenvolvido com ❤️ para Lojas Caçula**