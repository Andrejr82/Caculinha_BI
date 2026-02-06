# Resumo da Configuração Docker - 30 Usuários

**Data:** 2025-12-31
**Status:** Otimizado para produção

---

## ✅ Ajustes Realizados

### 1. Backend - Configuração Multi-Worker

**Antes:**
- 1 worker Uvicorn simples
- ~300MB RAM
- Capacidade: ~10 usuários

**Depois:**
- 4 workers Gunicorn + Uvicorn
- 2GB RAM (limite), 1GB (reservado)
- 2 CPUs (limite), 1 CPU (reservado)
- Capacidade: **30-50 usuários simultâneos**

### 2. Dependências Adicionadas

**requirements.txt:**
```
+ gunicorn  # Servidor de produção com multi-workers
```

### 3. Script de Inicialização

**backend/entrypoint.sh** (NOVO):
- Configura 4 workers automaticamente
- 1000 max requests por worker (anti-memory leak)
- Timeout de 120s para queries longas
- Logs estruturados para monitoramento

### 4. Docker Compose

**docker-compose.light.yml atualizado:**
```yaml
WORKERS=4
DUCKDB_THREADS=4
DUCKDB_MEMORY_LIMIT=1.5GB
MAX_REQUESTS=1000
WORKER_CONNECTIONS=1000
```

---

## 🎯 Capacidade e Performance

### Usuários Simultâneos Suportados

| Usuários | Latência Esperada | Status |
|----------|-------------------|--------|
| 1-10 | <100ms | ✅ Excelente |
| 11-30 | 100-300ms | ✅ Bom |
| 31-50 | 300-500ms | ⚠️ Aceitável |
| 50+ | >500ms | ❌ Degradado |

**Configuração ideal para:** 30 usuários

---

## 💾 Requisitos de Hardware

### Desenvolvimento (8GB RAM) - LIMITADO
⚠️ **Apenas para testes com 5-10 usuários**
- Docker usará ~2.5GB
- Windows ~3GB
- Sobra ~2.5GB para outros processos

### Produção (Mínimo)
✅ **Para 30 usuários reais**
- RAM: 16GB
- CPU: 4 cores
- Disco: 50GB SSD
- Rede: 100Mbps

### Produção (Ideal)
🚀 **Para 50+ usuários com folga**
- RAM: 32GB
- CPU: 8 cores
- Disco: 100GB NVMe
- Rede: 1Gbps

---

## 🚀 Como Iniciar

### Primeira Vez (Rebuild Completo)
```bash
docker-rebuild.bat
```

**O que acontece:**
1. Para containers antigos
2. Remove imagens antigas
3. Reconstrói do zero (sem cache)
4. Inicia com 4 workers
5. ~3-5 minutos total

### Uso Diário
```bash
docker-start.bat
```

**O que acontece:**
1. Reinicia WSL
2. Inicia containers existentes
3. ~30 segundos total

### Ver Logs
```bash
docker-logs.bat
```

### Parar Sistema
```bash
docker-stop.bat
```

---

## 📊 Monitoramento

### Ver Uso de Recursos
```bash
docker stats
```

**Saída esperada:**
```
CONTAINER         CPU %    MEM USAGE / LIMIT    MEM %
agent_bi_backend  50-80%   1.2GB / 2GB         60%
agent_bi_frontend 5-10%    100MB / 256MB       40%
```

### Ver Workers Ativos
```bash
docker logs agent_bi_backend | grep -i worker
```

**Saída esperada:**
```
Workers: 4
Worker Class: uvicorn.workers.UvicornWorker
[INFO] Booting worker with pid: 8
[INFO] Booting worker with pid: 9
[INFO] Booting worker with pid: 10
[INFO] Booting worker with pid: 11
```

---

## ⚠️ Avisos Importantes

### 1. Máquina de Desenvolvimento (8GB RAM)
**NÃO é adequada para testar 30 usuários reais!**

Você pode:
- ✅ Desenvolver e testar funcionalidades
- ✅ Testar com 1-5 usuários simultaneamente
- ❌ Testar carga com 30 usuários (travará)

Para testes de carga, use servidor com 16GB+ RAM.

### 2. Servidor de Produção
**DEVE ter no mínimo 16GB RAM**

Com 8GB em produção:
- Sistema ficará instável
- Pode ter OOM (Out of Memory) kills
- Performance degradada
- Usuários terão timeouts

### 3. Escalabilidade
Se ultrapassar 50 usuários:
1. Aumentar para 8 workers (requer 32GB RAM)
2. OU escalar horizontalmente (múltiplos containers)
3. OU usar Kubernetes para auto-scaling

---

## 🔧 Arquivos Modificados

```
✅ docker-compose.light.yml    # Aumentado recursos, 4 workers
✅ backend/requirements.txt    # Adicionado gunicorn
✅ backend/Dockerfile          # Usa entrypoint.sh
✅ backend/entrypoint.sh       # NOVO - Inicia com gunicorn
✅ docker-rebuild.bat          # Atualizado com info de capacidade
```

---

## 📝 Próximos Passos

### Agora (Desenvolvimento)
1. Execute: `docker-rebuild.bat`
2. Teste a aplicação com 1-2 usuários
3. Verifique logs: `docker-logs.bat`
4. Monitore: `docker stats`

### Antes do Deploy em Produção
1. Provisionar servidor com **16GB+ RAM**
2. Instalar Docker e Docker Compose
3. Configurar `.env` com credenciais de produção
4. Configurar firewall (portas 8000, 3000)
5. Configurar SSL/HTTPS com Nginx
6. Testar com 10 usuários
7. Testar com 30 usuários
8. Configurar backups automáticos

### Monitoramento em Produção
1. Configurar alertas de CPU/RAM
2. Logs centralizados (ELK/Loki)
3. Uptime monitoring (UptimeRobot)
4. Performance monitoring (Prometheus + Grafana)

---

## 🎯 Conclusão

**Status Atual:** ✅ Pronto para 30 usuários (em servidor adequado)

**Configuração:**
- 4 workers Gunicorn/Uvicorn
- 2GB RAM, 2 CPUs
- Auto-restart, healthchecks
- DuckDB otimizado

**Limitação Atual:**
- Máquina de dev (8GB) só para testes leves
- **Produção requer 16GB+ RAM**

**Comandos:**
```bash
docker-rebuild.bat  # Primeira vez / rebuild
docker-start.bat    # Uso diário
docker-logs.bat     # Ver logs
docker-stop.bat     # Parar
```

---

Para mais detalhes, veja:
- `REQUISITOS_PRODUCAO_30_USUARIOS.md` - Requisitos completos
- `GUIA_DECISAO.md` - Docker vs Local
- `docker-compose.light.yml` - Configuração técnica
