# Guia de Implementação de Infraestrutura - Fase 4

## Objetivo
Otimizar o sistema BI_Solution para suportar 30+ usuários simultâneos com alta performance.

---

## 4.1. Migração para DuckDB Servidor

### Pré-requisitos
- DuckDB 1.1+
- Python 3.11+

### Passos de Implementação

#### 1. Instalar DuckDB em Modo Servidor

```bash
# Instalar DuckDB CLI
pip install duckdb --upgrade

# Ou baixar binário
# https://duckdb.org/docs/installation/
```

#### 2. Configurar Modo Servidor

**Arquivo:** `backend/app/infrastructure/data/duckdb_server.py` (CRIAR)

```python
import duckdb
from contextlib import contextmanager

class DuckDBServer:
    def __init__(self, db_path: str, max_connections: int = 50):
        self.db_path = db_path
        self.max_connections = max_connections
        self._connection_pool = []
    
    @contextmanager
    def get_connection(self):
        """Connection pooling"""
        if self._connection_pool:
            conn = self._connection_pool.pop()
        else:
            conn = duckdb.connect(self.db_path, read_only=True)
        
        try:
            yield conn
        finally:
            if len(self._connection_pool) < self.max_connections:
                self._connection_pool.append(conn)
            else:
                conn.close()
```

#### 3. Atualizar DataSourceManager

**Arquivo:** `backend/app/core/data_source_manager.py`

```python
# Substituir conexão direta por pool
from app.infrastructure.data.duckdb_server import DuckDBServer

class DataSourceManager:
    def __init__(self):
        self.duckdb_server = DuckDBServer(
            db_path="data/admmat.parquet",
            max_connections=50
        )
    
    def execute_query(self, query: str):
        with self.duckdb_server.get_connection() as conn:
            return conn.execute(query).df()
```

#### 4. Testar com 30 Usuários

```bash
# Usar Locust para teste de carga
pip install locust

# Criar arquivo de teste
# tests/load/test_30_users.py
```

**Status:** ✅ Documentado (implementação manual necessária)

---

## 4.2. Implementar Cache Redis

### Pré-requisitos
- Redis 7.0+
- redis-py

### Passos de Implementação

#### 1. Instalar Redis

**Windows:**
```bash
# Usar WSL ou Docker
docker run -d -p 6379:6379 redis:7-alpine
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

#### 2. Configurar Redis Cache

**Arquivo:** `backend/app/infrastructure/cache/redis_cache.py` (CRIAR)

```python
import redis
import json
import hashlib
from typing import Any, Optional

class RedisCache:
    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )
    
    def get(self, key: str) -> Optional[Any]:
        """Obter valor do cache"""
        value = self.client.get(key)
        if value:
            return json.loads(value)
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Armazenar no cache (TTL em segundos)"""
        self.client.setex(
            key,
            ttl,
            json.dumps(value)
        )
    
    def invalidate(self, pattern: str):
        """Invalidar cache por padrão"""
        for key in self.client.scan_iter(pattern):
            self.client.delete(key)
    
    @staticmethod
    def generate_key(query: str, params: dict) -> str:
        """Gerar chave única para query"""
        content = f"{query}:{json.dumps(params, sort_keys=True)}"
        return f"query:{hashlib.md5(content.encode()).hexdigest()}"
```

#### 3. Integrar no DataSourceManager

```python
class DataSourceManager:
    def __init__(self):
        self.cache = RedisCache()
    
    def execute_query(self, query: str, use_cache=True):
        if use_cache:
            cache_key = RedisCache.generate_key(query, {})
            cached = self.cache.get(cache_key)
            if cached:
                return pd.DataFrame(cached)
        
        # Executar query
        result = self._execute_duckdb(query)
        
        if use_cache:
            self.cache.set(cache_key, result.to_dict('records'), ttl=3600)
        
        return result
```

#### 4. Queries a Cachear

- Top produtos (TTL: 1 hora)
- Métricas de dashboard (TTL: 5 minutos)
- Previsões (TTL: 1 hora)
- Dados de fornecedores (TTL: 6 horas)

**Status:** ✅ Documentado (implementação manual necessária)

---

## 4.3. Rate Limiting e Monitoramento

### Rate Limiting

**Arquivo:** `backend/app/middleware/rate_limiter.py` (CRIAR)

```python
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Aplicar no main.py
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Decorar endpoints
@app.get("/api/v1/chat")
@limiter.limit("100/minute")
async def chat_endpoint(request: Request):
    ...
```

### Monitoramento com Prometheus

#### 1. Instalar Prometheus Client

```bash
pip install prometheus-client
```

#### 2. Configurar Métricas

**Arquivo:** `backend/app/monitoring/metrics.py` (CRIAR)

```python
from prometheus_client import Counter, Histogram, Gauge

# Contadores
requests_total = Counter(
    'http_requests_total',
    'Total de requisições HTTP',
    ['method', 'endpoint', 'status']
)

# Histogramas (latência)
request_duration = Histogram(
    'http_request_duration_seconds',
    'Duração das requisições',
    ['endpoint']
)

# Gauges (valores atuais)
active_users = Gauge(
    'active_users',
    'Usuários ativos'
)

llm_tokens_used = Counter(
    'llm_tokens_total',
    'Tokens usados pela LLM',
    ['model']
)
```

#### 3. Expor Métricas

```python
from prometheus_client import make_asgi_app

# Adicionar no main.py
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

#### 4. Configurar Grafana

**Dashboard JSON:** `docs/grafana_dashboard.json`

```json
{
  "dashboard": {
    "title": "BI Solution Metrics",
    "panels": [
      {
        "title": "Requests per Second",
        "targets": [{
          "expr": "rate(http_requests_total[1m])"
        }]
      },
      {
        "title": "Response Time (p95)",
        "targets": [{
          "expr": "histogram_quantile(0.95, http_request_duration_seconds)"
        }]
      }
    ]
  }
}
```

**Status:** ✅ Documentado (implementação manual necessária)

---

## Checklist de Implementação

### 4.1. DuckDB Servidor
- [ ] Criar `duckdb_server.py`
- [ ] Implementar connection pooling
- [ ] Atualizar `DataSourceManager`
- [ ] Executar testes de carga (Locust)
- [ ] Validar performance (30+ usuários)

### 4.2. Redis Cache
- [ ] Instalar Redis (Docker/WSL)
- [ ] Criar `redis_cache.py`
- [ ] Integrar no `DataSourceManager`
- [ ] Configurar TTLs por tipo de query
- [ ] Medir redução de latência

### 4.3. Monitoramento
- [ ] Instalar prometheus-client
- [ ] Criar `metrics.py`
- [ ] Expor endpoint `/metrics`
- [ ] Configurar Grafana
- [ ] Criar alertas (latência >2s, erro rate >5%)

---

## Métricas de Sucesso

- **Latência p95:** < 2 segundos
- **Throughput:** > 100 req/s
- **Cache Hit Rate:** > 60%
- **Uptime:** > 99.5%
- **Usuários Simultâneos:** 30+ sem degradação

---

## Comandos Úteis

```bash
# Testar Redis
redis-cli ping

# Monitorar Redis
redis-cli monitor

# Ver métricas Prometheus
curl http://localhost:8000/metrics

# Teste de carga
locust -f tests/load/test_30_users.py --host=http://localhost:8000
```

---

**Nota:** Esta fase requer implementação manual pois envolve infraestrutura externa (Redis, Prometheus). Os guias acima fornecem todos os passos necessários.
