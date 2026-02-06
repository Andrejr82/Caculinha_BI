# 📊 Agent BI Solution - Resumo Executivo

**Sistema**: Plataforma de Business Intelligence Conversacional
**Cliente**: Lojas Caçula (rede de varejo)
**Status**: ✅ Funcional | 🔧 Em desenvolvimento

---

## 🎯 O QUE É

Chat inteligente que responde perguntas de negócio em **linguagem natural** e gera **gráficos automáticos**.

**Exemplo de uso**:
- Usuário pergunta: *"Quais produtos estão em ruptura?"*
- Sistema responde: Lista produtos + gráfico interativo

**Tecnologias**:
- **Backend**: Python + FastAPI + DuckDB + Gemini/Groq AI
- **Frontend**: SolidJS + Plotly.js
- **Dados**: 1M+ registros em Parquet (~60MB)

---

## ⚡ QUICK START

### Opção 1: Desenvolvimento Local (8GB RAM) ⭐ RECOMENDADO

```bat
START_LOCAL_DEV.bat
```

**Requisitos**:
- Python 3.11+
- Node.js 18+
- 8GB RAM
- API Key Groq (grátis) ou Gemini

**Tempo**: 5 min primeira vez, 15s próximas vezes

**Documentação**: `SETUP_LOCAL_8GB.md`

### Opção 2: Docker (Produção - 16GB+ RAM)

```bat
START_DOCKER_DEFINITIVO.bat
```

**Requisitos**:
- Docker Desktop
- 16GB RAM mínimo
- 10GB espaço em disco

**Tempo**: 6-9 min build completo

**Documentação**: `SOLUCAO_DEFINITIVA.md`

---

## 📁 ESTRUTURA DO PROJETO

```
BI_Solution/
├── backend/              # API FastAPI + Agente IA
│   ├── app/
│   │   ├── api/         # Endpoints REST
│   │   ├── core/        # Agente BI + Tools + LLM
│   │   ├── data/        # Dados Parquet + Cache
│   │   └── config/      # Settings
│   ├── main.py          # Entry point
│   └── requirements.txt
│
├── frontend-solid/      # UI SolidJS
│   ├── src/
│   │   ├── pages/       # Chat, Analytics, etc
│   │   ├── components/  # Componentes reutilizáveis
│   │   └── store/       # State management
│   └── package.json
│
├── docs/                # Documentação
│   ├── INDEX.md         # Índice da documentação
│   ├── PRD.md           # Product Requirements
│   ├── migration/       # Migração DuckDB (Dez 2025)
│   └── guides/          # Guias operacionais
│
├── scripts/             # Scripts utilitários
│   └── utils/           # Diagnóstico, rebuild, etc
│
├── config/              # Configurações Docker/Prometheus
├── data/                # Dados e cache (não versionado)
└── tests/               # Testes automatizados
```

---

## 🔧 DESENVOLVIMENTO DIÁRIO

### Iniciar Trabalho

```bash
# Local (8GB RAM)
START_LOCAL_DEV.bat

# Acesse: http://localhost:3000
# Login: admin / admin
```

### Fazer Mudanças

**Backend** (Python):
- Edite arquivos em `backend/app/`
- Salvamento automático recarrega servidor (hot reload)
- Logs aparecem na janela do terminal

**Frontend** (TypeScript/SolidJS):
- Edite arquivos em `frontend-solid/src/`
- Vite atualiza browser automaticamente
- Erros aparecem no console do browser (F12)

### Testar

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend-solid
npm test
```

---

## 📊 SPECS TÉCNICAS

### Performance
- **Query Response**: < 3s (p95)
- **Chart Generation**: < 5s (p95)
- **Concurrent Users**: 30 usuários (produção)
- **Data Volume**: 1M+ registros (60MB Parquet)

### Migração DuckDB (Dezembro 2025)
- ✅ **3.3x mais rápido** que Polars/Dask
- ✅ **76% menos memória** (1.7GB → 400MB)
- ✅ **75% menos dependências** (4 engines → 1)

Ver: `docs/migration/RESUMO_EXECUTIVO_MIGRACAO.md`

### LLM Providers Suportados
- **Groq** (llama-3.3-70b) - Grátis, rápido
- **Google Gemini** (gemini-2.5-flash-lite) - Alternativa

---

## 🚀 DEPLOY PRODUÇÃO (30 USUÁRIOS)

### Requisitos Mínimos

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| RAM | 16GB | 32GB |
| CPU | 4 vCPUs | 8 vCPUs |
| Disco | 50GB SSD | 100GB SSD |
| Rede | 100 Mbps | 1 Gbps |

### Opções de Hosting

**Cloud (Recomendado)**:
- DigitalOcean Droplet 16GB - $84/mês
- AWS Lightsail 16GB - ~$80/mês
- Contabo VPS 16GB - €10/mês

**On-Premise**:
- Servidor dedicado 32GB RAM
- Custo: ~R$ 3.000-5.000 (one-time)
- Requer energia + internet dedicada

### Deploy Steps

```bash
# 1. Clonar repositório no servidor
git clone <repo-url>
cd BI_Solution

# 2. Configurar .env
cp backend/.env.example backend/.env
# Editar .env com chaves de produção

# 3. Subir com Docker
docker-compose up -d

# 4. Verificar saúde
docker-compose ps
curl http://localhost:8000/health
```

Ver checklist completo em: `SOLUCAO_DEFINITIVA.md`

---

## 📚 DOCUMENTAÇÃO

### Para Desenvolvedores
- **`CLAUDE.md`** - Guia completo para Claude Code
- **`SETUP_LOCAL_8GB.md`** - Setup local sem Docker
- **`docs/INDEX.md`** - Índice da documentação

### Para Deploy
- **`SOLUCAO_DEFINITIVA.md`** - Deploy com Docker
- **`DIAGNOSTICO_E_CORRECAO_COMPLETA.md`** - Troubleshooting
- **`docker-compose.yml`** - Configuração dos serviços

### Arquitetura
- **`docs/PRD.md`** - Product Requirements Document
- **`docs/migration/`** - Migração DuckDB (Dez 2025)
- **`backend/app/core/agents/caculinha_bi_agent.py`** - Agente principal

---

## 🐛 PROBLEMAS COMUNS

### Backend não inicia

**Erro**: `GROQ_API_KEY is required`

**Solução**:
1. Obter chave grátis: https://console.groq.com/
2. Adicionar em `backend/.env`:
   ```env
   GROQ_API_KEY=gsk_sua_chave_aqui
   LLM_PROVIDER=groq
   ```

### Docker consome muita RAM

**Sintoma**: Sistema fica lento, 100% RAM usado

**Solução**: Usar desenvolvimento local (sem Docker)
```bat
docker-compose down
START_LOCAL_DEV.bat
```

Ver: `SETUP_LOCAL_8GB.md`

### Frontend não conecta ao backend

**Verificar**:
1. Backend rodando? → `curl http://localhost:8000/health`
2. CORS correto? → Verificar `BACKEND_CORS_ORIGINS` no `.env`

### Chart não gera

**Verificar logs do backend**:
```bash
docker-compose logs backend | grep ERROR
# OU (local)
# Ver janela do terminal backend
```

**Causas comuns**:
- API key inválida ou expirada
- Dados Parquet corrompidos
- Timeout do LLM (aumentar tempo em settings)

---

## 📞 SUPORTE

### Logs

**Local**:
- Backend: Janela do terminal
- Frontend: Browser DevTools (F12)

**Docker**:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Diagnóstico

```bash
# Local
cd backend
python test_startup.py

# Docker
bash scripts/utils/diagnose-docker-backend.sh
```

### Stack Completa

**Backend** (Porta 8000):
- FastAPI + Uvicorn
- DuckDB (dados)
- Gemini/Groq (LLM)
- LangChain (agent framework)

**Frontend** (Porta 3000):
- SolidJS (UI framework)
- Plotly.js (gráficos)
- TanStack Query (state)

**Observabilidade** (Docker apenas):
- LangFuse (porta 3001) - Trace LLM
- Prometheus (porta 9090) - Métricas
- Grafana (porta 3002) - Dashboards

---

## 🎯 ROADMAP

### Concluído ✅
- [x] Migração DuckDB (Dez 2025)
- [x] Multi-LLM (Groq + Gemini)
- [x] Setup local para 8GB RAM
- [x] Docker otimizado para produção
- [x] Documentação completa

### Em Progresso 🔧
- [ ] Testes E2E automatizados
- [ ] CI/CD pipeline
- [ ] Monitoring em produção

### Planejado 📅
- [ ] Deploy em cloud provider
- [ ] Autenticação via SSO
- [ ] Mobile app (React Native)
- [ ] Suporte multi-idioma

---

## 📊 MÉTRICAS DO PROJETO

- **Linhas de código**: ~15.000 (backend + frontend)
- **Dependências**: 35 Python + 30 npm
- **Tamanho build**: 2.5GB (Docker) | 500MB (local)
- **Tempo de build**: 6-9 min (Docker) | 3-5 min (local)
- **Cobertura de testes**: ~60% (backend)

---

## 📝 CHANGELOG RECENTE

### 2026-01-01
- ✅ Criado setup local para 8GB RAM
- ✅ Documentação completa de troubleshooting Docker
- ✅ Scripts automatizados de startup
- ✅ Correção de dependências faltantes

### 2025-12-31
- ✅ Migração DuckDB completa (3.3x performance)
- ✅ Limpeza de documentação
- ✅ Reorganização da estrutura de pastas

### 2025-12-28
- ✅ Suporte multi-LLM (Groq + Gemini)
- ✅ Enhanced agent system (20 max turns)
- ✅ Fallback automático para charts

---

## 🔗 LINKS ÚTEIS

- **Groq API** (grátis): https://console.groq.com/
- **Gemini API**: https://aistudio.google.com/
- **Python**: https://www.python.org/downloads/
- **Node.js**: https://nodejs.org/
- **Docker**: https://www.docker.com/products/docker-desktop/

---

**✅ PROJETO PRONTO PARA DESENVOLVIMENTO E DEPLOY**

**Para começar**: Execute `START_LOCAL_DEV.bat` (8GB RAM) ou `START_DOCKER_DEFINITIVO.bat` (16GB+ RAM)

**Dúvidas?** Consulte `CLAUDE.md` ou `docs/INDEX.md`
