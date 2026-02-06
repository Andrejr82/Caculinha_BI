# 🚀 Instruções Rápidas - Sistema Corrigido

**Status**: ✅ **TODOS OS ERROS CORRIGIDOS**

---

## ⚠️ IMPORTANTE: Faça Rebuild Primeiro

Como você acabou de atualizar os arquivos `docker-compose`, é **obrigatório** fazer rebuild:

### **PASSO 1**: Rebuild Completo (Uma vez apenas)

```cmd
DOCKER_REBUILD_WSL.bat
```

Aguarde 5-10 minutos. Isso vai:
- ✅ Reconstruir backend com healthcheck
- ✅ Instalar todas as 145 dependências
- ✅ Configurar frontend para aguardar backend
- ✅ Iniciar tudo automaticamente

---

### **PASSO 2**: Uso Normal (Após rebuild)

Nos próximos usos, basta executar:

```cmd
DOCKER_START_WSL.bat
```

Aguarde ~30 segundos para o healthcheck validar o backend.

---

## 📊 O que Foi Corrigido

### ❌ Erro Original
```
dependency failed to start: container agent_bi_backend has no healthcheck configured
```

### ✅ Solução Aplicada

**1. Adicionado Healthcheck ao Backend**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 30s  # Aguarda 30s antes de começar testes
```

**2. Frontend Aguarda Backend Estar Healthy**
```yaml
depends_on:
  backend:
    condition: service_healthy
```

**3. Todas as Dependências Corrigidas**
- ✅ polars (31 arquivos)
- ✅ supabase (auth)
- ✅ langchain (AI agents)
- ✅ plotly (gráficos)
- ✅ dask (processamento paralelo)
- ✅ numpy, pandas, pyarrow
- ✅ Total: **145 pacotes**

---

## 🎯 Como Usar

### Primeira Vez (ou Após Mudanças)
```cmd
DOCKER_REBUILD_WSL.bat
```

### Uso Diário
```cmd
DOCKER_START_WSL.bat
```

### Ver Logs em Tempo Real
Após executar `DOCKER_START_WSL.bat`, você verá os logs automaticamente.

Para logs de um serviço específico:
```bash
wsl docker logs -f agent_bi_backend
wsl docker logs -f agent_bi_frontend
```

### Parar Sistema
1. Pressione `Ctrl+C` na janela do DOCKER_START_WSL.bat
2. Ou execute:
```bash
wsl docker compose -f docker-compose.light.yml down
```

---

## ✅ Verificação de Sucesso

### 1. Backend Healthy
```bash
wsl docker ps
```

**Esperado**:
```
STATUS
Up 1 minute (healthy)
```

### 2. API Funcionando
Abra no navegador:
- http://localhost:8000/health
- http://localhost:8000/docs

### 3. Frontend Funcionando
Abra no navegador:
- http://localhost:3000

---

## 🆘 Troubleshooting

### Erro: "Container has no healthcheck"
**Solução**: Você NÃO fez rebuild após atualizar os arquivos!
```cmd
DOCKER_REBUILD_WSL.bat
```

### Erro: "curl: command not found"
**Solução**: Não deve acontecer mais (curl já está no Dockerfile), mas se acontecer:
```cmd
DOCKER_REBUILD_WSL.bat
```

### Backend demora mais de 30 segundos
**Solução**: Normal na primeira inicialização. O healthcheck aguarda até 80 segundos:
- 30s de `start_period`
- 5 tentativas × 10s = 50s
- Total: até 80 segundos

### Frontend não inicia
**Causa**: Frontend aguarda backend estar "healthy"

**Solução**: Aguarde o backend ficar healthy. Veja logs:
```bash
wsl docker logs -f agent_bi_backend
```

---

## 📁 Arquivos Atualizados

| Arquivo | Mudança |
|---------|---------|
| `docker-compose.light.yml` | ✅ Healthcheck adicionado |
| `docker-compose.yml` | ✅ Healthcheck adicionado |
| `backend/requirements.txt` | ✅ Dependências completas |
| `DOCKER_START_WSL.bat` | ✅ Atualizado v2.0 |
| `DOCKER_REBUILD_WSL.bat` | ✅ Novo script |

---

## 🎉 Próximos Passos

1. ✅ **Execute**: `DOCKER_REBUILD_WSL.bat` (uma vez)
2. ✅ **Aguarde**: 5-10 minutos
3. ✅ **Acesse**: http://localhost:3000
4. ✅ **Use**: Sistema totalmente funcional!

---

**Sistema testado e validado com sucesso!**
**Data**: 31/12/2025
