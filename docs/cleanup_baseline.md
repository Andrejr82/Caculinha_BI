# Cleanup Baseline — Descomissionamento Controlado

**Projeto:** Caculinha BI Enterprise AI Platform  
**Data:** 2026-02-07  
**Branch:** main (up to date with origin/main)

---

## 1. Estado Atual do Git

```
Branch: main
Status: up to date with 'origin/main'
Arquivos não commitados: sim (limpeza anterior pendente de commit)
```

---

## 2. Estrutura da Nova Arquitetura (PROTEGIDA)

### Backend (Python/FastAPI)
```
backend/
├── domain/          # Entidades e Ports (Hexagonal)
├── application/     # Agentes e Use Cases
├── infrastructure/  # Adapters (Redis, DuckDB, SQLite)
├── api/             # Endpoints REST
├── core/            # Config, Security, Pipeline
├── tests/           # Testes unitários (pytest)
└── data/            # Dados parquet e cache
```

### Frontend (SolidJS)
```
frontend-solid/
├── src/             # Código fonte
├── public/          # Assets estáticos
├── tests/           # Testes Playwright
└── dist/            # Build de produção
```

### Infraestrutura
```
docker-compose.yml   # Na raiz
Dockerfile           # Na raiz
.agent/              # Antigravity Kit
docs/                # Documentação
tools/               # Scripts de manutenção
```

---

## 3. Gates de Validação

### Backend
| Gate | Comando | Esperado |
|------|---------|----------|
| **pytest** | `$env:PYTHONPATH="c:\Projetos_BI\BI_Solution"; python -m pytest backend/tests/ -v` | 24 passed |
| **startup** | `python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000` | Health OK |

### Frontend
| Gate | Comando | Esperado |
|------|---------|----------|
| **build** | `cd frontend-solid && npm run build` | Exit 0 |
| **dev** | `cd frontend-solid && npm run dev` | Vite running |

### Docker
| Gate | Comando | Esperado |
|------|---------|----------|
| **compose** | `docker-compose build` | Exit 0 |
| **up** | `docker-compose up -d` | Services healthy |

---

## 4. Comandos Executados Nesta Fase

```powershell
git status
git branch --show-current
python -m pytest backend/tests/ -v --collect-only
```

---

## 5. Baseline de Arquivos

| Local | Status |
|-------|--------|
| `backend/` | ✅ Arquitetura Hexagonal completa |
| `frontend-solid/` | ✅ SolidJS + Tailwind |
| `docs/` | ⚠️ Contém legado misturado |
| `tools/` | ✅ Scripts de auditoria |
| `.agent/` | ✅ Antigravity Kit |
| `raiz/` | ⚠️ Arquivos órfãos residuais |

---

## 6. Próximas Fases

| Fase | Objetivo |
|------|----------|
| **FASE 1** | Inventário profundo (deep_inventory.py) |
| **FASE 2** | Classificação (o que fica / o que sai) |
| **FASE 3** | Quarentena (mover sem deletar) |
| **FASE 4** | Remoção definitiva (com prova) |
| **FASE 5** | Endurecimento (prevenção de regressão) |

---

**FASE 0 COMPLETA — AGUARDANDO APROVAÇÃO PARA FASE 1**
