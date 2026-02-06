# Guia de Otimização para Máquinas com 8GB RAM

## Situação Atual
- **RAM Total**: 8GB
- **WSL2 Configurado**: 4GB (ajustado)
- **Swap WSL**: 2GB (reduzido)

---

## Opções de Execução

### 📦 Opção 1: Docker Light (Moderado - ~1.2GB)
**Vantagens:**
- Ambiente isolado e consistente
- Fácil deploy em produção
- Configuração automatizada

**Desvantagens:**
- Usa ~1.2GB de RAM
- Requer WSL2/Docker Desktop
- Startup mais lento (~30s)

**Como usar:**
```bash
# Windows
start-light.bat

# Ou manualmente
docker-compose -f docker-compose.light.yml up -d
```

**Portas:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

### 💻 Opção 2: Execução Local (Leve - ~500MB) ⭐ RECOMENDADO
**Vantagens:**
- Usa apenas ~500MB de RAM
- Startup rápido (~5s)
- Hot reload no desenvolvimento
- Sem overhead do Docker

**Desvantagens:**
- Requer dependências instaladas localmente
- Python 3.11+ necessário
- Node.js 18+ necessário

**Pré-requisitos:**
```bash
# 1. Instalar Python virtual environment
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 2. Instalar dependências Node.js
cd ../frontend-solid
npm install
```

**Como usar:**
```bash
# Windows
start-local.bat

# Ou manualmente:
# Terminal 1 - Backend
cd backend
.venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend
cd frontend-solid
npm run dev
```

**Portas:**
- Backend: http://localhost:8000
- Frontend: http://localhost:5173 (Vite dev server)
- API Docs: http://localhost:8000/docs

---

## Configurações Aplicadas

### `.wslconfig` Otimizado
```ini
[wsl2]
memory=4GB              # Aumentado de 3GB
processors=2            # Mantido
swap=2GB                # Reduzido de 4GB
localhostForwarding=true
pageReporting=false     # Reduz overhead
kernelCommandLine=cgroup_no_v1=all systemd.unified_cgroup_hierarchy=1
```

**⚠️ Importante:** Após alterar `.wslconfig`, execute:
```bash
wsl --shutdown
```

### `docker-compose.light.yml` Limites
```yaml
backend:
  deploy:
    resources:
      limits:
        memory: 1G      # Limite máximo
      reservations:
        memory: 512M    # Garantido

frontend:
  deploy:
    resources:
      limits:
        memory: 256M
      reservations:
        memory: 128M
```

---

## Comparação de Recursos

| Métrica | Docker Completo | Docker Light | Local |
|---------|----------------|--------------|-------|
| RAM Usada | ~3GB | ~1.2GB | ~500MB |
| Startup | ~60s | ~30s | ~5s |
| Inclui Observability | ✅ | ❌ | ❌ |
| Hot Reload | ❌ | ❌ | ✅ |
| Deploy Pronto | ✅ | ✅ | ❌ |
| **Recomendado 8GB** | ❌ | ⚠️ | ✅ |

---

## Troubleshooting

### Docker consumindo muita RAM?
1. Use apenas `docker-compose.light.yml`
2. Verifique containers rodando: `docker stats`
3. Pare containers não usados: `docker-compose -f docker-compose.light.yml down`

### WSL2 lento após mudanças?
```bash
# Reiniciar WSL
wsl --shutdown

# Verificar distribuição
wsl -l -v
```

### Backend/Frontend não iniciam localmente?
```bash
# Verificar Python
python --version  # Deve ser 3.11+

# Verificar Node.js
node --version    # Deve ser 18+

# Reinstalar dependências
cd backend
pip install -r requirements.txt

cd ../frontend-solid
npm install
```

---

## Monitoramento de Memória

### Windows
```bash
# Ver uso de RAM do WSL
wsl -d Ubuntu --exec free -h

# Task Manager
Ctrl+Shift+Esc -> Performance
```

### Docker
```bash
# Ver uso de containers
docker stats

# Ver logs
docker-compose -f docker-compose.light.yml logs -f
```

---

## Próximos Passos

1. ✅ Configuração WSL otimizada
2. ⬜ Escolher modo de execução (Light Docker vs Local)
3. ⬜ Testar aplicação
4. ⬜ Monitorar uso de RAM

**Recomendação Final:** Para desenvolvimento com 8GB RAM, use **execução local** (`start-local.bat`). Reserve Docker apenas para testes de produção.
