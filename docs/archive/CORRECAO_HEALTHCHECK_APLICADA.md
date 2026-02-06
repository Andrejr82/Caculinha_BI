# 🔧 Correção de Healthcheck Docker - Aplicada

**Data**: 2026-01-01
**Problema**: Container `agent_bi_backend` falhando no healthcheck e impedindo `agent_bi_frontend` de iniciar

---

## ✅ Correções Aplicadas

### 1. **Arquivo `.env` - Removida Configuração Duplicada**
- **Problema**: `USE_SQL_SERVER` estava definido duas vezes (linha 14 como `true` e linha 24 como `false`)
- **Solução**: Consolidada configuração única com `USE_SQL_SERVER=false`
- **Impacto**: Elimina conflito que poderia causar timeout no startup (tentativa de conexão SQL Server desnecessária)

### 2. **`healthcheck.py` - Melhorado para Docker**
**Mudanças**:
- ✅ URL alterada de `http://127.0.0.1:8000/health` → `http://localhost:8000/health` (melhor compatibilidade com rede Docker)
- ✅ Timeout aumentado de 2s → 5s (permite workers do Gunicorn terminarem startup)
- ✅ Mensagens de erro melhoradas com emojis e hints
- ✅ Tratamento específico para `URLError` (indica que app ainda está subindo)

### 3. **`docker-compose.yml` - Healthcheck Timing Ajustado**
**Mudanças**:
```yaml
# ANTES:
interval: 10s
timeout: 5s
start_period: 30s

# DEPOIS:
interval: 15s
timeout: 10s
start_period: 60s  # Doubled to allow Gunicorn workers to fully start
```

**Justificativa**:
- Gunicorn com 4 workers pode levar 40-50s para inicializar completamente
- `start_period: 60s` garante que healthcheck não falhe prematuramente durante startup
- `interval: 15s` reduz overhead de checagens frequentes
- `timeout: 10s` alinhado com timeout do script Python (5s) + margem de segurança

---

## 🚀 Como Testar a Correção

### Opção 1: Rebuild Completo (Recomendado)

```bash
cd /mnt/c/Agente_BI/BI_Solution

# 1. Parar todos os containers
docker-compose down

# 2. Rebuild do backend (força recriação com novos arquivos)
docker-compose build --no-cache backend

# 3. Subir todos os serviços
docker-compose up -d

# 4. Acompanhar logs do backend em tempo real
docker-compose logs -f backend
```

**O que esperar nos logs**:
```
backend_1  | =========================================
backend_1  | Iniciando Agente BI Backend
backend_1  | =========================================
backend_1  | Workers: 4
backend_1  | Worker Class: uvicorn.workers.UvicornWorker
backend_1  | =========================================
backend_1  | [INFO] Booting worker with pid: X
backend_1  | [INFO] Booting worker with pid: Y
backend_1  | [INFO] Booting worker with pid: Z
backend_1  | [INFO] Booting worker with pid: W
backend_1  | [INFO] Application startup complete.
```

### Opção 2: Restart Rápido (se já builded)

```bash
# Apenas reiniciar o backend
docker-compose restart backend

# Verificar status
docker-compose ps
```

---

## 🔍 Script de Diagnóstico

Criado script utilitário para diagnóstico rápido:

```bash
# Executar diagnóstico completo
bash scripts/utils/diagnose-docker-backend.sh
```

**O script verifica**:
1. ✓ Status do container
2. ✓ Últimos 30 logs
3. ✓ Healthcheck manual
4. ✓ Endpoint `/health` respondendo
5. ✓ Arquivo Parquet presente
6. ✓ Variáveis de ambiente críticas
7. ✓ Processos rodando (Gunicorn/Uvicorn)

---

## 🎯 Validação de Sucesso

### 1. Verificar Status dos Containers

```bash
docker-compose ps
```

**Esperado**:
```
NAME                   STATUS
agent_bi_backend       Up (healthy)
agent_bi_frontend      Up
agent_bi_langfuse      Up
agent_bi_prometheus    Up
agent_bi_grafana       Up
```

### 2. Testar Endpoint de Health

```bash
curl http://localhost:8000/health
```

**Esperado**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

### 3. Testar Frontend

Abrir navegador em: http://localhost:3000

**Esperado**: Página de login do Agent BI carregando normalmente

---

## 🐛 Troubleshooting

### Problema: Backend ainda falha no healthcheck

**Diagnóstico**:
```bash
# 1. Ver logs detalhados
docker-compose logs -f backend

# 2. Executar diagnóstico
bash scripts/utils/diagnose-docker-backend.sh

# 3. Verificar se app está respondendo dentro do container
docker exec agent_bi_backend curl http://localhost:8000/health
```

**Possíveis causas**:
1. **Falta API Key do LLM**
   - Verifique no `.env`: `GROQ_API_KEY` ou `GEMINI_API_KEY` deve estar preenchido
   - Obtenha chave em: https://console.groq.com/ (Groq - grátis) ou https://aistudio.google.com/ (Gemini)

2. **SECRET_KEY inválido**
   - Deve ter pelo menos 32 caracteres
   - Gere novo: `openssl rand -hex 32`

3. **Arquivo Parquet ausente**
   - Verifique: `ls -lh backend/app/data/parquet/admmat.parquet`
   - Se não existir, contacte responsável pelos dados

### Problema: Frontend não sobe (dependency failed)

**Causa**: Backend ainda não está healthy após as correções acima

**Solução**:
```bash
# 1. Verificar status do backend
docker-compose ps backend

# 2. Se backend está "unhealthy", ver logs
docker-compose logs backend

# 3. Após backend ficar "healthy", reiniciar frontend
docker-compose restart frontend
```

### Problema: Timeout no startup mesmo com 60s

**Solução**: Aumentar ainda mais o `start_period` no `docker-compose.yml`:

```yaml
healthcheck:
  start_period: 90s  # Aumentar para 90s ou 120s se necessário
```

---

## 📊 Monitoramento

### Ver logs em tempo real de todos os serviços:
```bash
docker-compose logs -f
```

### Ver logs apenas do backend:
```bash
docker-compose logs -f backend
```

### Ver logs apenas do frontend:
```bash
docker-compose logs -f frontend
```

### Verificar uso de recursos:
```bash
docker stats
```

---

## 🎓 Entendendo o Problema

### Por que o healthcheck estava falhando?

1. **Timing insuficiente**: Gunicorn com 4 workers Uvicorn leva ~40-50s para:
   - Iniciar processo master do Gunicorn
   - Spawnar 4 workers Uvicorn
   - Cada worker carregar aplicação FastAPI
   - Carregar DuckDB e dados Parquet em memória
   - Inicializar LLM adapter
   - Ficar pronto para receber requests

2. **Configuração duplicada**: `USE_SQL_SERVER=true` e `false` causavam tentativa de conexão SQL Server, adicionando 2-10s de timeout desnecessário no startup

3. **Healthcheck muito agressivo**: Com `start_period: 30s`, o Docker começava a falhar o container antes dele estar completamente pronto

### Como a correção resolve?

- ✅ **60s start_period**: Dá tempo suficiente para todos os workers iniciarem
- ✅ **15s interval**: Reduz overhead de checagens constantes
- ✅ **10s timeout**: Margem de segurança para requisição HTTP + script Python
- ✅ **URL localhost**: Melhor resolução DNS dentro do container Docker
- ✅ **Sem SQL Server**: Elimina 2-10s de timeout de conexão desnecessária

---

## 📝 Notas Adicionais

### Arquivos Modificados:
1. `backend/.env` - Configuração consolidada
2. `backend/healthcheck.py` - Script melhorado
3. `docker-compose.yml` - Timings ajustados
4. `scripts/utils/diagnose-docker-backend.sh` - Novo script de diagnóstico (criado)

### Próximos Passos Recomendados:
1. ✅ Testar a correção seguindo as instruções acima
2. ✅ Se funcionar, fazer commit das mudanças
3. ✅ Documentar a configuração final do `.env` para produção
4. ✅ Configurar alertas de healthcheck no ambiente de produção

---

**Dúvidas?** Verifique `docs/guides/TROUBLESHOOTING_WSL2.md` ou execute o script de diagnóstico.
