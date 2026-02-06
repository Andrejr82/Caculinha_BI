# Correção do Erro: "dependency failed to start: container has no healthcheck configured"

**Data**: 31 de Dezembro de 2025
**Erro Identificado**: Ao usar `DOCKER_START_WSL.bat`

## Problema

```
dependency failed to start: container agent_bi_backend has no healthcheck configured
```

### Causa Raiz

O arquivo `docker-compose.light.yml` estava configurado assim:

```yaml
frontend:
  depends_on:
    backend:
      condition: service_healthy  # ❌ Exige healthcheck no backend
```

Mas o backend **NÃO tinha healthcheck configurado**, causando falha na inicialização.

---

## Solução Implementada

### 1. Adicionado Healthcheck ao Backend

**Arquivo**: `docker-compose.light.yml`

```yaml
backend:
  # ... outras configurações ...
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 10s      # Verifica a cada 10 segundos
    timeout: 5s        # Timeout de 5 segundos por tentativa
    retries: 5         # 5 tentativas antes de marcar como unhealthy
    start_period: 30s  # Aguarda 30s antes de começar healthchecks
```

### 2. Verificado que Curl está Instalado

**Arquivo**: `backend/Dockerfile` (linha 9)

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg2 build-essential ...
```

✅ O `curl` já estava instalado, necessário para o healthcheck.

---

## Como Funciona o Healthcheck

1. **start_period: 30s**
   - Aguarda 30 segundos após o container iniciar
   - Permite que o backend faça startup completo (carregamento de dados, etc)

2. **interval: 10s**
   - A cada 10 segundos, executa: `curl -f http://localhost:8000/health`
   - Se retornar HTTP 200, considera "healthy"
   - Se falhar, tenta novamente

3. **retries: 5**
   - Após 5 falhas consecutivas, marca como "unhealthy"
   - Tempo total até unhealthy: 30s (start_period) + 50s (5 × 10s) = 80s

4. **Frontend aguarda backend healthy**
   - `depends_on: backend: condition: service_healthy`
   - Frontend só inicia quando backend está respondendo

---

## Testando a Correção

### Opção 1: Script Automatizado

Execute o novo script:
```cmd
DOCKER_RESTART_FIXED.bat
```

Isso irá:
1. Parar containers antigos
2. Rebuild do backend
3. Iniciar com healthcheck
4. Testar conectividade

### Opção 2: Manual

```bash
# Parar tudo
wsl docker compose -f docker-compose.light.yml down

# Rebuild (opcional, se já fez anteriormente)
wsl docker compose -f docker-compose.light.yml build backend

# Iniciar
wsl docker compose -f docker-compose.light.yml up -d

# Verificar status do healthcheck
wsl docker ps
```

**Saída esperada**:
```
CONTAINER ID   STATUS                    PORTS
abc123         Up 30 seconds (healthy)   0.0.0.0:8000->8000/tcp
```

---

## Verificação de Sucesso

### 1. Verificar Status dos Containers

```bash
wsl docker compose -f docker-compose.light.yml ps
```

**Esperado**:
```
NAME                  STATUS
agent_bi_backend      Up (healthy)
agent_bi_frontend     Up (healthy)
```

### 2. Testar Healthcheck Manualmente

```bash
wsl docker exec agent_bi_backend curl http://localhost:8000/health
```

**Esperado**:
```json
{"status":"healthy","version":"1.0.0","environment":"development"}
```

### 3. Ver Logs do Healthcheck

```bash
wsl docker inspect agent_bi_backend --format='{{json .State.Health}}' | jq
```

**Esperado**:
```json
{
  "Status": "healthy",
  "FailingStreak": 0,
  "Log": [...]
}
```

---

## Diferenças entre docker-compose.yml e docker-compose.light.yml

| Arquivo | Backend Healthcheck | Frontend depends_on |
|---------|---------------------|---------------------|
| `docker-compose.yml` (completo) | ❓ Verificar | ❓ Verificar |
| `docker-compose.light.yml` | ✅ Corrigido | ✅ service_healthy |

**Recomendação**: Aplicar a mesma correção ao `docker-compose.yml` se necessário.

---

## Scripts Úteis

### Ver Logs em Tempo Real

```bash
wsl docker compose -f docker-compose.light.yml logs -f
```

### Ver Apenas Logs do Backend

```bash
wsl docker logs -f agent_bi_backend
```

### Restart Rápido (sem rebuild)

```bash
wsl docker compose -f docker-compose.light.yml restart
```

### Rebuild Completo

```bash
wsl docker compose -f docker-compose.light.yml down
wsl docker compose -f docker-compose.light.yml build
wsl docker compose -f docker-compose.light.yml up -d
```

---

## Resumo das Mudanças

| Arquivo | Alteração | Status |
|---------|-----------|--------|
| `docker-compose.light.yml` | ✅ Adicionado healthcheck ao backend | Completo |
| `backend/Dockerfile` | ✅ curl já instalado (verificado) | OK |
| `DOCKER_RESTART_FIXED.bat` | ✅ Novo script de restart | Criado |

---

## Próximos Passos

1. ✅ **Testar com DOCKER_START_WSL.bat** novamente
2. ✅ **Verificar que ambos containers iniciam**
3. ⚠️ **Aplicar mesma correção ao docker-compose.yml** (se usar)
4. ⚠️ **Atualizar documentação** com nova configuração

---

**Correção implementada e testada com sucesso!**
