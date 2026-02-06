# 🚀 Agent BI Solution - Quick Start

## Início Rápido

```bash
# 1. Instalar dependências
npm install

# 2. Iniciar sistema
npm run dev
```

✅ Backend: http://localhost:8000
✅ Frontend: http://localhost:3000
✅ API Docs: http://localhost:8000/docs

---

## 📦 Comandos Principais

```bash
npm run dev              # Inicia tudo
npm run dev:backend      # Apenas backend
npm run dev:frontend     # Apenas frontend
npm run clean:ports      # Limpa portas 8000 e 3000
```

---

## ⚙️ Configuração Inicial

### 1. Configure o Gemini API Key

Edite `backend/.env`:
```bash
GEMINI_API_KEY="sua_chave_api_gemini_aqui"
```

**Obtenha sua chave:** https://makersuite.google.com/app/apikey

### 2. Verifique a configuração

```bash
npm run validate:env
```

---

## 🏥 Health Checks

```bash
# Health check simples
curl http://localhost:8000/health

# Health check completo
curl http://localhost:8000/api/v1/health

# Liveness probe (Kubernetes)
curl http://localhost:8000/api/v1/health/live

# Readiness probe (Kubernetes)
curl http://localhost:8000/api/v1/health/ready
```

---

## 🛠️ Troubleshooting

### Porta ocupada
```bash
npm run clean:ports
```

### Backend não inicia
```bash
# Verifique logs
npm run dev:backend

# Instale dependências faltantes
cd backend
.venv\Scripts\pip.exe install -r requirements.txt
```

### Frontend não inicia
```bash
# Instale dependências
cd frontend-solid
pnpm install
```

---

## 📚 Documentação Completa

Veja [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) para:
- Guia detalhado de migração
- Todas as mudanças implementadas
- Comparativo antes vs depois
- Troubleshooting avançado
- Próximos passos recomendados

---

## 🎯 Stack Tecnológica

- **Backend:** FastAPI + Python 3.11+
- **Frontend:** SolidJS + Vite
- **Database:** Parquet (fallback: SQL Server)
- **LLM:** Gemini 3.0 Flash (`gemini-3-flash-preview`)
- **Package Manager:** npm + pnpm

---

## ✅ Checklist Pré-Desenvolvimento

- [ ] `npm install` executado
- [ ] `.env` configurado com `GEMINI_API_KEY`
- [ ] `npm run dev` funcionando
- [ ] Backend respondendo em http://localhost:8000/health
- [ ] Frontend acessível em http://localhost:3000

---

**Versão:** 1.0.0
**Data:** 2025-12-13
