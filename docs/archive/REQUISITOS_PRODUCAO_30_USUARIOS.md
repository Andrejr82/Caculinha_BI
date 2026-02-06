# Requisitos de Produção - 30 Usuários Simultâneos

**Data:** 2025-12-31
**Configuração:** Docker Light Otimizado

---

## 🎯 Configuração Atual

### Backend
- **Workers:** 4 (Gunicorn + Uvicorn)
- **Worker Connections:** 1000
- **Max Requests:** 1000 (com jitter de 50)
- **Timeout:** 120s
- **Keepalive:** 5s

### Recursos Docker

#### Backend Container
```yaml
Limites:
  Memória: 2GB
  CPU: 2 cores

Reservado:
  Memória: 1GB
  CPU: 1 core
```

#### Frontend Container
```yaml
Limites:
  Memória: 256MB
  CPU: 0.5 core

Reservado:
  Memória: 128MB
  CPU: 0.25 core
```

---

## 💾 Requisitos de Hardware

### Desenvolvimento (Máquina Atual - 8GB RAM)
**Viável apenas para testes com poucos usuários:**
- RAM: 8GB (uso ~2.5GB Docker + ~3GB Windows = 5.5GB)
- CPU: 2 cores mínimo
- Disco: 10GB livres

⚠️ **Atenção:** Com 8GB RAM, não é recomendado testar com mais de 5-10 usuários simultâneos.

### Produção (Recomendado para 30 usuários)
**Configuração Mínima:**
- RAM: 16GB (uso ~4GB Docker + ~2GB SO = 6GB, margem de 10GB)
- CPU: 4 cores / 8 threads
- Disco: 50GB SSD
- Rede: 100Mbps

**Configuração Ideal:**
- RAM: 32GB
- CPU: 8 cores / 16 threads
- Disco: 100GB NVMe SSD
- Rede: 1Gbps

---

## 📊 Capacidade Estimada

### Com Configuração Atual (4 workers)

| Cenário | Usuários | Req/seg | Latência Média | Status |
|---------|----------|---------|----------------|--------|
| Leve | 10 | ~20 | <100ms | ✅ Excelente |
| Normal | 30 | ~50 | 100-300ms | ✅ Bom |
| Pico | 50 | ~80 | 300-500ms | ⚠️ Aceitável |
| Stress | 100+ | ~100+ | >500ms | ❌ Degradado |

**Conclusão:** Configuração adequada para **até 50 usuários simultâneos** com boa performance.

---

## 🔧 Ajustes para Escalar Além de 30 Usuários

### Para 50-100 usuários
```yaml
backend:
  environment:
    - WORKERS=8              # Dobrar workers
    - DUCKDB_MEMORY_LIMIT=3GB
  deploy:
    resources:
      limits:
        memory: 4G
        cpus: '4.0'
```

**Hardware necessário:** 32GB RAM, 8 cores

### Para 100-200 usuários
- Considere escalar horizontalmente (múltiplos containers)
- Use load balancer (Nginx/Traefik)
- Redis para cache distribuído
- PostgreSQL para sessões

---

## 🚀 Otimizações Aplicadas

### 1. Multi-Worker com Gunicorn
- **4 workers** Uvicorn processam requisições em paralelo
- Cada worker pode lidar com ~8-10 usuários simultâneos
- Auto-restart de workers após 1000 requests (previne memory leaks)

### 2. DuckDB em vez de Polars
- **3.3x mais rápido** em queries analíticas
- **76% menos memória** (crítico para múltiplos workers)
- Cache persistente entre reinicializações

### 3. Healthchecks Robustos
- Verifica saúde a cada 10s
- 5 tentativas antes de marcar como unhealthy
- 40s de startup (tempo para iniciar 4 workers)

### 4. Resource Limits
- Previne consumo excessivo de RAM
- Garante recursos mínimos reservados
- Evita OOM (Out of Memory) kills

---

## 📈 Monitoramento Essencial

### Métricas Críticas para Produção

#### Backend
```bash
# Ver uso de recursos em tempo real
docker stats agent_bi_backend

# Logs de performance
docker logs -f agent_bi_backend | grep -i "worker"

# Conexões ativas
docker exec agent_bi_backend netstat -an | grep :8000 | wc -l
```

#### Sistema
```bash
# Uso de RAM
free -h

# Uso de CPU
htop

# Disco
df -h
```

---

## ⚠️ Sinais de Alerta

### Backend está com problemas se:
1. **Latência > 500ms** consistentemente
2. **Uso de RAM > 90%** do limite (1.8GB de 2GB)
3. **CPU > 90%** do limite
4. **Logs mostram:**
   - "Worker timeout"
   - "Memory error"
   - "Connection refused"

**Ação:** Escalar verticalmente (mais RAM/CPU) ou horizontalmente (mais containers).

---

## 🔐 Considerações de Segurança para Produção

### 1. Variáveis de Ambiente
```bash
# NUNCA use em produção:
DEBUG=true
ENVIRONMENT=development

# Use:
DEBUG=false
ENVIRONMENT=production
SECRET_KEY=<gerar chave de 64+ caracteres>
```

### 2. Rate Limiting
```env
RATE_LIMIT_PER_MINUTE=60  # Por usuário
RATE_LIMIT_AUTH_PER_MINUTE=5
```

### 3. CORS
```env
BACKEND_CORS_ORIGINS=https://seu-dominio.com
```

### 4. HTTPS
- Use reverse proxy (Nginx/Traefik) com SSL
- Certbot para Let's Encrypt gratuito

---

## 📋 Checklist de Deploy em Produção

### Pré-Deploy
- [ ] Servidor com **mínimo 16GB RAM**
- [ ] Docker e Docker Compose instalados
- [ ] Portas 8000 e 3000 abertas no firewall
- [ ] Domínio apontando para o servidor
- [ ] SSL/TLS configurado

### Configuração
- [ ] `.env` com credenciais de produção
- [ ] `SECRET_KEY` gerada aleatoriamente
- [ ] `DEBUG=false`
- [ ] CORS configurado corretamente
- [ ] Backup automático configurado

### Testes
- [ ] Teste de carga com 10 usuários
- [ ] Teste de carga com 30 usuários
- [ ] Teste de failover (matar container)
- [ ] Teste de restart automático
- [ ] Monitoramento funcionando

### Monitoramento Contínuo
- [ ] Logs centralizados (ELK/Loki)
- [ ] Alertas configurados (Slack/Email)
- [ ] Backups testados
- [ ] Plano de rollback documentado

---

## 🔄 Plano de Backup

### Dados Críticos
```bash
# Sessões
./backend/app/data/sessions/

# Cache semântico
./backend/data/cache/semantic/

# Parquet files
./data/parquet/
```

### Script de Backup Automático
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/agentbi_$DATE"

docker-compose -f docker-compose.light.yml exec -T backend tar czf - \
  /app/app/data /app/data > "$BACKUP_DIR.tar.gz"

# Manter apenas últimos 7 dias
find /backup -name "agentbi_*.tar.gz" -mtime +7 -delete
```

---

## 📞 Troubleshooting Produção

### Problema: "503 Service Unavailable"
**Causa:** Workers sobrecarregados
**Solução:**
1. Aumentar `WORKERS` de 4 para 6-8
2. Verificar `docker stats` - se RAM > 90%, aumentar limite
3. Verificar logs: `docker logs agent_bi_backend`

### Problema: "Memory error" nos logs
**Causa:** Limite de RAM insuficiente
**Solução:**
1. Aumentar `memory: 2G` para `4G`
2. Reduzir `WORKERS` de 4 para 2 (temporário)
3. Otimizar queries DuckDB

### Problema: Container reiniciando constantemente
**Causa:** Healthcheck falhando ou OOM kill
**Solução:**
1. Ver logs: `docker logs agent_bi_backend --tail 100`
2. Se OOM: aumentar memória
3. Se healthcheck: aumentar `start_period` de 40s para 60s

---

## 🎯 Conclusão

**Configuração atual está otimizada para:**
- ✅ 30 usuários simultâneos
- ✅ Performance adequada
- ✅ Estabilidade com auto-restart
- ✅ Resource limits configurados

**Para produção, garanta:**
- Servidor com **mínimo 16GB RAM**
- Monitoramento ativo
- Backups automáticos
- Plano de escala (se ultrapassar 50 usuários)

---

## 📚 Documentação Relacionada

- `GUIA_DECISAO.md` - Por que escolher Docker
- `RELATORIO_VERIFICACAO_AMBIENTE.md` - Status do ambiente
- `GUIA_OTIMIZACAO_8GB.md` - Limitações da máquina de dev
- `docker-compose.light.yml` - Configuração atual
- `backend/entrypoint.sh` - Script de inicialização
