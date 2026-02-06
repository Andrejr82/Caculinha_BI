# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Agent Solution BI** is a conversational Business Intelligence platform for Lojas Caçula retail chain. It combines Google Gemini (or Groq) LLM with DuckDB high-performance data processing to transform 1M+ sales/inventory records into actionable insights through natural language queries.

**Core Value**: Users ask questions like "Which products are out of stock but available in the warehouse?" and receive instant charts and analysis without needing SQL or BI expertise.

## ⚠️ Critical Notices for Developers

### Before Making Changes
1. **Read `docs/AVALIACAO_ARQUITETURAL_SAAS.md`** - Comprehensive architecture analysis identifying all bottlenecks, security issues, and SaaS gaps
2. **Check "Known Limitations & Technical Debt" section below** - Critical constraints that affect development
3. **Current Architecture:** Single-tenant (NOT multi-tenant SaaS ready)

### Security Warnings
- 🔴 **Admin bypass exists** in `dependencies.py:43-50` - Do NOT rely on this for production
- 🔴 **Tokens stored in sessionStorage** - XSS vulnerable, migrate to HTTP-only cookies
- 🔴 **No token revocation** - Logged out users can use tokens until expiry
- 🟡 **Token in URL** for SSE streaming - Exposed in browser history/logs

### Scalability Warnings
- 🔴 **DuckDB Pool: 4 connections** - System breaks with >4 concurrent users
- 🔴 **Session files (JSON)** - Cannot run multiple instances (no horizontal scaling)
- 🟡 **No code splitting** - 5 MB frontend bundle slows initial load

### Data Warnings
- 🔴 **Parquet files hardcoded** - Paths resolved with fallback logic across 3 locations
- 🔴 **No tenant isolation** - All data shared (blocker for multi-tenant SaaS)
- 🟡 **No schema versioning** - Breaking changes possible

## Key Architecture Decisions

### Data Layer: Hybrid Architecture with DuckDB (Dec 2025 Migration)
- **Primary**: DuckDB 1.1+ for columnar analytics on Parquet files (3.3x faster, 76% less memory than previous Polars/Dask stack)
- **Fallback**: SQL Server optional (disabled by default via `USE_SQL_SERVER=false` to prevent connection timeouts)
- **File**: `backend/app/infrastructure/data/hybrid_adapter.py` - Auto-fallback logic
- **Critical**: Always use DuckDB adapter methods, NOT direct SQL or Pandas operations for data queries

### AI Agent: Gemini Native Function Calling
- **LLM Provider**: Supports Google Gemini (default) or Groq (configured via `LLM_PROVIDER` in `.env`)
- **Architecture**: ReAct pattern with tool calling (NOT legacy code generation)
- **Main Agent**: `backend/app/core/agents/caculinha_bi_agent.py` (1600+ lines)
  - Uses Gemini's native function calling API
  - Tools are LangChain BaseTool instances converted to Gemini Function Declarations
  - Supports streaming responses via SSE (Server-Sent Events)
  - Includes RAG (Retrieval Augmented Generation) for query examples

**Critical Rules for Agent**:
1. **Chart Generation**: Uses `gerar_grafico_universal_v2` tool (NOT code generation) - filters applied via tool parameters
2. **Analysis vs Charts**: System detects keywords to decide between textual analysis (críticas/relatórios) vs visualizations (gráficos)
3. **Max Turns**: 20 iterations (increased from 10 for complex analyses)
4. **Fallback**: If LLM ignores chart request, synthetic tool call is injected automatically

### Frontend: SolidJS Reactive Framework
- **Framework**: SolidJS 1.8+ (chosen for native reactivity and performance over React)
- **State**: @tanstack/solid-query for server state, signals for local state
- **Charts**: Plotly.js for all visualizations
- **Markdown**: marked + github-markdown-css for rich text rendering

## Development Commands

### Package Managers
- **Backend**: pip (Python packages via requirements.txt)
- **Frontend**: pnpm (enforced via engines field in package.json)
- **Root**: npm scripts coordinate both services (automatically uses pnpm for frontend)

### 🚀 Quick Start - Local Development (RECOMMENDED for 8GB RAM)

**For development on machines with 8GB RAM, ALWAYS use local setup (not Docker)**:

```bat
# Windows - One command to start everything
START_LOCAL_DEV.bat

# Starts backend (port 8000) and frontend (port 3000) in separate windows
# Memory usage: ~1.5GB (vs ~6GB with Docker)
```

**First time setup**:
```bash
# Backend dependencies
cd backend
pip install -r requirements.txt
copy .env.example .env
# Edit .env and add GROQ_API_KEY or GEMINI_API_KEY

# Frontend dependencies
cd frontend-solid
pnpm install
```

See `SETUP_LOCAL_8GB.md` for complete local development guide.

### Unified Commands (Repository Root)

The root `package.json` provides convenient scripts that coordinate both backend and frontend:

```bash
# Start both backend and frontend concurrently
npm run dev

# Install all dependencies (backend + frontend)
npm run install

# Clean up ports before starting
npm run clean:ports

# Validate environment setup
npm run validate:env

# Backend-specific commands (from root)
npm run test:backend       # Run pytest tests
npm run lint:backend       # Run ruff linter
npm run format:backend     # Run black formatter
```

### Backend (FastAPI + DuckDB)
```bash
# Navigate to backend directory
cd backend

# Install dependencies (Python 3.11+)
pip install -r requirements.txt

# Run development server (auto-reload enabled)
python main.py
# OR
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_caculinha_bi_agent.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run integration tests only
pytest tests/integration/

# Check DuckDB performance
python scripts/benchmark_duckdb_vs_polars.py
```

### Frontend (SolidJS + Vite)
```bash
# Navigate to frontend directory
cd frontend-solid

# Install dependencies (requires pnpm)
pnpm install

# Run development server (with auto-open browser)
pnpm dev

# Build for production
pnpm build

# Preview production build
pnpm serve

# Run linter
pnpm lint

# Fix linting issues
pnpm lint:fix

# Run tests
pnpm test

# Run tests with UI
pnpm test:ui

# Run tests with coverage
pnpm test:coverage
```

### Docker Compose (ONLY for production or 16GB+ RAM machines)

**⚠️ WARNING**: Docker stack requires **6GB+ RAM**. For development on 8GB machines, use local setup above.

```bash
# Start all services (backend, frontend, observability stack)
# REQUIRES: 16GB RAM minimum for stable operation
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild and restart
docker-compose up -d --build

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Check service health
docker-compose ps
```

**Production deployment**: Use `START_DOCKER_DEFINITIVO.bat` or see `SOLUCAO_DEFINITIVA.md`

**Troubleshooting**: See `DIAGNOSTICO_E_CORRECAO_COMPLETA.md` for Docker issues

## Critical File Locations

### Backend Core
- **Main Entry**: `backend/main.py` - FastAPI app with lifespan events
- **Settings**: `backend/app/config/settings.py` - Pydantic settings (reads `.env`)
- **Main Agent**: `backend/app/core/agents/caculinha_bi_agent.py` - BI chat agent
- **LLM Adapters**:
  - `backend/app/core/llm_gemini_adapter_v2.py` - Gemini integration
  - `backend/app/core/llm_groq_adapter.py` - Groq integration
  - `backend/app/core/llm_factory.py` - Factory pattern for LLM selection
- **Data Adapter**: `backend/app/infrastructure/data/hybrid_adapter.py` - DuckDB + SQL Server fallback

### Tools (Function Calling)
- **Universal Chart**: `backend/app/core/tools/universal_chart_generator.py` - `gerar_grafico_universal_v2`
- **Flexible Query**: `backend/app/core/tools/flexible_query_tool.py` - Generic data queries
- **Business Logic**: `backend/app/core/tools/une_tools.py` - Transfer suggestions, stock calculations
- **Semantic Search**: `backend/app/core/tools/semantic_search_tool.py` - RAG product search

### Frontend Core
- **Chat Page**: `frontend-solid/src/pages/Chat.tsx` - Main conversational interface
- **Plotly Charts**: `frontend-solid/src/components/PlotlyChart.tsx` - Chart rendering
- **Auth Store**: `frontend-solid/src/store/auth.ts` - JWT authentication state

### Configuration
- **Backend ENV**: `backend/.env` (create from `backend/.env.example`)
- **Docker Compose**: `docker-compose.yml` (full stack) or `docker-compose.light.yml` (minimal)
- **Prometheus**: `config/prometheus/prometheus.yml`

### Documentation
- **Index**: `docs/INDEX.md` - Documentation navigation
- **Migration**: `docs/migration/` - DuckDB migration reports (Dec 2025)
- **Guides**: `docs/guides/` - Operational guides
- **PRD**: `docs/PRD.md` - Product requirements
- **GEMINI.md**: Root-level Gemini AI assistant instructions (alternative to CLAUDE.md)
- **Architecture Analysis**: `docs/AVALIACAO_ARQUITETURAL_SAAS.md` - Deep architecture assessment for SaaS evolution (Jan 2026)

## Data Schema (Parquet/DuckDB)

Main dataset: `data/parquet/admmat.parquet` (1M+ rows)

**Key Columns**:
- `PRODUTO` (int) - Product SKU code
- `NOME` (str) - Product name
- `UNE` (int) - Store/warehouse ID
- `NOMESEGMENTO` (str) - Segment (e.g., "TECIDOS", "ARMARINHO")
- `NOMECATEGORIA` (str) - Category
- `NOMEFABRICANTE` (str) - Manufacturer
- `VENDA_30DD` (float) - Sales last 30 days
- `ESTOQUE_UNE` (float) - Store stock
- `ESTOQUE_CD` (float) - Warehouse stock
- `PRECO_VENDA` (float) - Sale price
- `PRECO_CUSTO` (float) - Cost price

**Allowed Stores (UNEs)**: See `backend/app/config/settings.py` ALLOWED_UNES list (36 stores)

## Authentication & Authorization

- **Method**: JWT tokens (HS256 algorithm)
- **User Storage**: Parquet file `backend/app/data/users.parquet`
- **Role-Based Access**:
  - `admin` - Access to all segments
  - `analyst` - Restricted to specific segments via `allowed_segments` array
- **Token Expiry**: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Tool Scoping**: Tools are filtered based on user role (`backend/app/core/utils/tool_scoping.py`)

**Default Credentials**:
- Admin: `admin` / `admin`
- Analyst: `hugo.mendes` / `123456`

## Environment Variables (.env)

**Required**:
```bash
SECRET_KEY=<32+ character random string>
GEMINI_API_KEY=<your-google-api-key>  # OR GROQ_API_KEY
LLM_PROVIDER=groq  # or "google"
```

**Important Flags**:
```bash
USE_SQL_SERVER=false  # Keep false to avoid connection timeouts
FALLBACK_TO_PARQUET=true  # Enable automatic fallback to Parquet
DEBUG=true  # Enable debug mode in development
ENVIRONMENT=development  # or "staging" / "production"
```

See `backend/.env.example` for full list.

## Testing Strategy

### Backend Tests
- **Unit Tests**: `backend/tests/unit/` - Test individual components
- **Integration Tests**: `backend/tests/integration/` - Test API endpoints
- **Performance Tests**: `backend/tests/test_performance_v2.py`, `backend/tests/test_extreme_performance.py`

**Key Test Files**:
- `tests/unit/test_caculinha_bi_agent.py` - Agent behavior
- `tests/integration/test_chat_endpoint.py` - Chat API
- `tests/integration/test_auth.py` - Authentication
- `tests/test_tool_modernization.py` - Tool system

### Frontend Tests
- **Framework**: Vitest + @solidjs/testing-library
- **Location**: `frontend-solid/src/**/*.test.tsx` (convention)
- **Run**: `pnpm test` or `pnpm test:ui` (from frontend-solid directory)

## Common Patterns

### Adding a New Tool (Function)
1. Create tool in `backend/app/core/tools/` as LangChain BaseTool
2. Add tool to `all_bi_tools` list in `caculinha_bi_agent.py`
3. Update `SYSTEM_PROMPT` in same file to document the new tool
4. Add tests in `tests/unit/test_une_tools.py`

### Modifying Chart Generation
- **Primary File**: `backend/app/core/tools/universal_chart_generator.py`
- **Function**: `gerar_grafico_universal_v2` (supports auto type detection)
- **Filters**: `filtro_une`, `filtro_segmento`, `filtro_categoria`, `filtro_produto`
- **Output**: Returns Plotly JSON spec via `fig.to_json()`

### Adding New Frontend Page
1. Create component in `frontend-solid/src/pages/`
2. Add route in `frontend-solid/src/App.tsx` (SolidJS Router)
3. Update navigation in layout component

### Debugging Agent Behavior
- **Enable Logging**: Set `LOG_LEVEL=DEBUG` in `.env`
- **Check Logs**: `backend/logs/` directory (structured JSON logs)
- **Agent Traces**: Look for `[GRAPH PRIORITY]`, `[ANALYSIS MODE]`, `[FALLBACK]` log markers
- **Tool Execution**: Search logs for `"Agent calling tool:"`

## Performance Considerations

### DuckDB Best Practices
- Use `.filter()` instead of `.where()` for better performance
- Avoid `SELECT *` - specify columns explicitly
- Use `LIMIT` for large result sets
- Leverage DuckDB's parallel execution (automatic)

### Frontend Optimization
- Charts are memoized - avoid recreating PlotlyChart component unnecessarily
- Use SolidJS `createMemo` for expensive computations
- Lazy load pages with dynamic imports if needed

### API Response Times
- **Target**: < 3 seconds for p95 queries
- **Chart Generation**: < 5 seconds for p95
- **Monitoring**: Prometheus metrics at `http://localhost:9090`

## Observability Stack

**Services** (all via Docker Compose):
- **LangFuse** (port 3001) - LLM trace monitoring
- **Prometheus** (port 9090) - Metrics collection
- **Grafana** (port 3002) - Dashboards

**Access**:
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- LangFuse: http://localhost:3001
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3002

## Deployment Notes

### Production Checklist
1. Change `SECRET_KEY` to secure random value (32+ chars)
2. Set `DEBUG=false` and `ENVIRONMENT=production`
3. Configure proper CORS origins in `BACKEND_CORS_ORIGINS`
4. Update LangFuse secrets (`NEXTAUTH_SECRET`, `SALT`) in docker-compose.yml
5. Use production-grade database (not SQLite) if needed
6. Set up SSL/TLS certificates
7. Configure firewall rules for ports 8000, 3000

### Docker Production Build
```bash
# Build optimized images
docker-compose -f docker-compose.yml build --no-cache

# Run in production mode
docker-compose -f docker-compose.yml up -d
```

## Troubleshooting

### Backend won't start
- Check `backend/.env` exists and has valid `SECRET_KEY`
- Verify Parquet file exists at `data/parquet/admmat.parquet`
- Check logs: `docker-compose logs backend`

### Agent not generating charts
- Verify LLM API key is set (`GEMINI_API_KEY` or `GROQ_API_KEY`)
- Check agent logs for `[FALLBACK]` markers - indicates LLM ignored tool call
- Review `SYSTEM_PROMPT` in `caculinha_bi_agent.py` for chart generation rules

### DuckDB errors
- Check file path in settings: `PARQUET_FILE_PATH`
- Verify Parquet schema with: `python backend/scripts/inspect_parquet.py`
- DuckDB version must be >= 1.1.0

### WSL2/Docker issues on Windows
- See `docs/guides/TROUBLESHOOTING_WSL2.md`
- Ensure WSL2 integration is enabled in Docker Desktop
- Check port forwarding with `netstat -ano | findstr :8000`

## Recent Major Changes (Dec 2025)

1. **DuckDB Migration** - Replaced Polars/Dask/Pandas engines with DuckDB
   - 3.3x faster queries, 76% less memory
   - See `docs/migration/RESUMO_EXECUTIVO_MIGRACAO.md`

2. **Multi-LLM Support** - Added Groq provider alongside Gemini
   - Factory pattern in `llm_factory.py`
   - Switch via `LLM_PROVIDER` env var

3. **Enhanced Agent System** - Improved chart generation reliability
   - Automatic fallback if LLM ignores chart requests
   - Differentiation between textual analysis vs visualizations
   - Max turns increased to 20 for complex analyses

4. **Documentation Reorganization** - Cleaned up root directory
   - Moved all docs to `docs/` with proper structure
   - Created `docs/INDEX.md` for navigation
   - Archived legacy documentation

## Migration from Other Platforms

### From Polars/Pandas/Dask
All data operations now use DuckDB. Legacy adapters are commented out in `requirements.txt`.

**Instead of**:
```python
df = pl.read_parquet("data.parquet").filter(pl.col("UNE") == 1685)
```

**Use**:
```python
result = await data_adapter.execute_query(
    query_filters={"UNE": 1685},
    columns=["PRODUTO", "NOME", "VENDA_30DD"]
)
```

### From Code Generation to Function Calling
Legacy `CodeGenAgent` still exists but is deprecated. Modern flow uses native function calling:
- Agent decides which tool to call based on user query
- Gemini API handles function calling natively
- No Python code generation involved

## Known Limitations & Technical Debt

### Critical Constraints (Must Know Before Coding)

#### DuckDB Connection Pool
- **Limit:** 4 in-memory connections (hardcoded)
- **Impact:** System queues/timeouts with >4 concurrent users
- **Location:** `backend/app/infrastructure/data/duckdb_enhanced_adapter.py:94-96`
- **Workaround:** Increase pool to 16+ for production, use file-based DuckDB instead of `:memory:`

#### Session Storage
- **Current:** JSON files in `data/sessions/` (not distributed)
- **Impact:** Cannot scale horizontally (multi-instance breaks sessions)
- **Location:** `backend/app/core/session_manager.py`
- **Migration Path:** Redis required for production/SaaS

#### Authentication Security
- **Issue:** Admin bypass at `dependencies.py:43-50` allows token with `username="admin"` to skip Parquet verification
- **Issue:** No token revocation (logout doesn't invalidate JWT)
- **Issue:** Tokens valid for 30 min with no refresh mechanism
- **Frontend Issue:** Token stored in sessionStorage (XSS vulnerable) + passed in URL for SSE
- **Fix Required:** Migrate to HTTP-only cookies + implement token blacklist in Redis

#### LLM API Calls
- **Issue:** No timeout enforcement (calls can hang indefinitely)
- **Location:** `backend/app/core/agents/caculinha_bi_agent.py`, tool files
- **Risk:** Requests may timeout at uvicorn level (default 120s) causing poor UX
- **Fix:** Add `asyncio.timeout()` wrapper to all LLM calls

#### Frontend Bundle Size
- **Current:** ~5.0 MB uncompressed production build
- **Issue:** No code splitting or lazy loading (all 16 pages in initial bundle)
- **Impact:** Slow First Contentful Paint (~3s on 3G)
- **Location:** `frontend-solid/src/index.tsx` (eager imports)
- **Fix:** Implement `lazy(() => import())` for routes, use plotly.js-basic-dist-min

### Architecture Constraints

#### Single-Tenant Design
- **Current State:** All data shared, no `tenant_id` isolation
- **Impact:** Cannot support multi-tenant SaaS without major refactor
- **Required Changes:** Add tenant_id to User, Session, data queries; implement tenant middleware
- **Files to Modify:** All models, data adapters, API endpoints

#### File-Based Data Storage
- **Parquet Files:** Hardcoded paths with fallback logic (3 possible locations checked)
- **Users:** `backend/app/data/users.parquet` (bcrypt hashed passwords)
- **Main Data:** `data/parquet/admmat.parquet` (1M+ rows)
- **No Versioning:** Schema changes break tools with no migration system
- **No Backup:** Files not replicated or backed up automatically

#### Rate Limiting
- **Current:** IP-based with slowapi (100 req/min global, 5 req/min auth)
- **Issue:** Not per-user or per-tenant (easy to bypass with proxies)
- **Location:** `backend/main.py:124-126`
- **SaaS Requirement:** Implement per-user quota tracking

### Performance Characteristics

**Measured in Production:**
- DuckDB first query: +1-2s (Parquet load + compile)
- Subsequent queries: 200-500ms (cached)
- LLM response (Groq): 1-3s avg
- Chart generation: <1s
- Memory usage: ~1.5GB typical, 4GB max (DuckDB PRAGMA limit)
- Concurrency: 4 concurrent queries max (DuckDB pool), 1000 workers (uvicorn)

## Business Domain Notes

**Lojas Caçula Context**:
- Retail chain specializing in fabrics, sewing supplies, and home decor
- 40 years in business
- 36 stores (UNEs) + 1 distribution center (CD)
- Primary segments: TECIDOS (fabrics), ARMARINHO (sewing supplies), PAPELARIA (stationery)

**Key Metrics**:
- **Ruptura** (Stock-out) - Product available in CD but not in store (high priority issue)
- **Curva ABC** (Pareto) - Class A = top 20% products generating 80% revenue
- **Cobertura** (Coverage) - Days of inventory based on sales velocity
- **MC** (Margem de Contribuição) - Contribution margin

**Critical Business Rules** (`docs/archive/regras_negocio_une.md`):
- ICMS tax varies by UNE
- MC calculation includes freight and taxes
- Transfer suggestions prioritize products with ruptura + CD availability

## SaaS Evolution Roadmap

### Current State: Single-Tenant Production Ready
- ✅ Excellent for single organization deployment
- ✅ Performance: 3.3x faster than previous stack
- ✅ Modern tech stack (FastAPI, SolidJS, DuckDB)
- ❌ NOT ready for multi-tenant SaaS without major refactor

### Critical Blockers for SaaS
1. **Multi-tenancy** - No tenant_id isolation (CRITICAL)
2. **Session storage** - File-based, not distributed (CRITICAL)
3. **Authentication** - Security vulnerabilities, no token revocation (HIGH)
4. **Scalability** - DuckDB pool limited to 4 connections (HIGH)
5. **Infrastructure** - No containerization, no CI/CD (HIGH)

### Recommended Path to SaaS (12 months, ~R$ 1.8M)
See `docs/AVALIACAO_ARQUITETURAL_SAAS.md` for full roadmap.

**Phase 1: MVP SaaS (Months 1-3)**
- Add tenant_id to all models
- Migrate sessions to Redis
- Implement HTTP-only cookies
- Containerization (Docker + K8s)
- Basic billing (Stripe)

**Phase 2: Scale to 100 Clients (Months 4-6)**
- Self-service onboarding
- White-label support
- Multi-region deployment
- LGPD compliance

**Phase 3: Enterprise-Ready (Months 7-12)**
- SOC 2 Type II
- SSO/SAML
- 99.99% SLA
- Advanced RBAC

### Quick Wins (Can Implement Now)
1. Increase DuckDB pool to 16 connections
2. Add asyncio.timeout() to LLM calls
3. Implement code splitting in frontend
4. Add comprehensive logging
5. Remove admin bypass in auth
