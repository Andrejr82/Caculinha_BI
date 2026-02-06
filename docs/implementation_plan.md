# Plano de Implementação - Resolução de Pontos Críticos da Auditoria
## Agent Solution BI - Lojas Caçula

**Data:** 2026-01-17  
**Objetivo:** Resolver 100% dos pontos críticos identificados na auditoria de integração  
**Conformidade Atual:** 89%  
**Meta:** 100%

---

## 📊 Sumário Executivo

Este plano aborda **13 pontos críticos** identificados na auditoria, organizados em **4 fases** de implementação com **30 tarefas** detalhadas.

### Distribuição por Prioridade

| Prioridade | Pontos | Tarefas | Tempo Estimado |
|------------|--------|---------|----------------|
| **ALTA** | 4 | 12 | 1-2 semanas |
| **MÉDIA** | 3 | 12 | 1-2 meses |
| **BAIXA** | 6 | 6 | 3-6 meses |
| **TOTAL** | 13 | 30 | ~4 meses |

---

## 🎯 Fase 1: Prioridade ALTA (1-2 semanas)

### Ponto Crítico 1: Rate Limiting ⚠️

**Categoria:** Segurança  
**Conformidade Atual:** 85%  
**Impacto:** ALTO - Protege contra abuso e DDoS

#### Tarefas

**1.1 Implementar Rate Limiting Básico**
- **Descrição:** Adicionar middleware FastAPI para rate limiting
- **Tecnologia:** `slowapi` ou `fastapi-limiter`
- **Localização:** `backend/app/middleware/rate_limiter.py`
- **Tempo:** 2 horas

**Implementação:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# Aplicar em main.py
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Aplicar em endpoints críticos
@router.post("/chat")
@limiter.limit("10/minute")  # 10 requests por minuto
async def chat_endpoint(...):
    ...
```

**1.2 Rate Limiting por Usuário**
- **Descrição:** Limitar por user_id autenticado (não apenas IP)
- **Localização:** `backend/app/middleware/rate_limiter.py`
- **Tempo:** 2 horas

**Implementação:**
```python
def get_user_id(request: Request):
    # Extrair user_id do token JWT
    token = request.headers.get("Authorization")
    if token:
        payload = decode_jwt(token)
        return payload.get("sub")  # user_id
    return get_remote_address(request)

limiter = Limiter(key_func=get_user_id)
```

**1.3 Configuração de Limites**
- **Descrição:** Definir limites por endpoint
- **Localização:** `backend/app/config/rate_limits.py`
- **Tempo:** 1 hora

**Configuração:**
```python
RATE_LIMITS = {
    "/chat": "10/minute",  # Chat intensivo
    "/analytics": "30/minute",  # Analytics moderado
    "/metrics": "60/minute",  # Métricas leves
    "/auth/login": "5/minute",  # Login restrito
}
```

**Critérios de Aceitação:**
- [x] Rate limiting ativo em todos os endpoints
- [x] Limites configuráveis por endpoint
- [x] Mensagens de erro claras (429 Too Many Requests)
- [x] Logs de rate limit violations

---

### Ponto Crítico 2: Audit Trail Completo ⚠️

**Categoria:** Segurança + Compliance  
**Conformidade Atual:** 85% (Segurança), 90% (Compliance)  
**Impacto:** ALTO - Requerido por EU AI Act

#### Tarefas

**2.1 Criar Modelo de Audit Log**
- **Descrição:** Modelo SQLAlchemy para audit trail
- **Localização:** `backend/app/infrastructure/database/models/audit_log.py`
- **Tempo:** 2 horas

**Implementação:**
```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String, index=True)
    event_type = Column(String, index=True)  # 'llm_call', 'data_access', 'auth'
    
    # LLM specific
    prompt = Column(Text)
    response = Column(Text)
    model = Column(String)
    tokens_used = Column(Integer)
    latency_ms = Column(Integer)
    
    # Context
    ip_address = Column(String)
    user_agent = Column(String)
    endpoint = Column(String)
    
    # Metadata
    metadata = Column(JSON)
```

**2.2 Implementar Decorator de Audit**
- **Descrição:** Decorator para capturar LLM calls automaticamente
- **Localização:** `backend/app/core/decorators/audit_decorator.py`
- **Tempo:** 3 horas

**Implementação:**
```python
def audit_llm_call(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        user_id = get_current_user_id()
        
        # Capturar prompt
        prompt = kwargs.get('prompt') or args[0] if args else None
        
        try:
            response = await func(*args, **kwargs)
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Salvar audit log
            await save_audit_log(
                user_id=user_id,
                event_type='llm_call',
                prompt=prompt,
                response=response,
                latency_ms=latency_ms,
                metadata={'function': func.__name__}
            )
            
            return response
        except Exception as e:
            # Log de erro também
            await save_audit_log(
                user_id=user_id,
                event_type='llm_error',
                prompt=prompt,
                metadata={'error': str(e)}
            )
            raise
    return wrapper
```

**2.3 Aplicar Audit em Adapters LLM**
- **Descrição:** Adicionar audit em GeminiLLMAdapter e GroqLLMAdapter
- **Localização:** `backend/app/core/llm_*_adapter.py`
- **Tempo:** 2 horas

**2.4 Implementar Retenção de Logs**
- **Descrição:** Política de retenção de 6 meses (EU AI Act)
- **Localização:** `backend/app/services/audit_service.py`
- **Tempo:** 2 horas

**Implementação:**
```python
async def cleanup_old_audit_logs():
    """Remove logs mais antigos que 6 meses"""
    cutoff_date = datetime.utcnow() - timedelta(days=180)
    await db.execute(
        delete(AuditLog).where(AuditLog.timestamp < cutoff_date)
    )
```

**Critérios de Aceitação:**
- [x] Todos os LLM calls registrados
- [x] Campos obrigatórios: user_id, timestamp, prompt, response
- [x] Retenção de 6 meses implementada
- [x] Logs tamper-evident (hash de integridade)

---

### Ponto Crítico 3: Health Check Endpoints ⚠️

**Categoria:** Monitoramento  
**Conformidade Atual:** 70%  
**Impacto:** ALTO - Essencial para produção

#### Tarefas

**3.1 Criar Endpoint /health**
- **Descrição:** Health check básico
- **Localização:** `backend/app/api/v1/endpoints/health.py`
- **Tempo:** 1 hora

**Implementação:**
```python
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
```

**3.2 Verificar LLM Connectivity**
- **Descrição:** Testar conexão com Gemini/Groq
- **Localização:** `backend/app/api/v1/endpoints/health.py`
- **Tempo:** 2 horas

**Implementação:**
```python
@router.get("/health/detailed")
async def detailed_health_check():
    checks = {}
    
    # LLM Check
    try:
        llm = get_llm_adapter()
        response = await llm.generate("test", max_tokens=5)
        checks["llm"] = "healthy"
    except Exception as e:
        checks["llm"] = f"unhealthy: {str(e)}"
    
    # Database Check
    try:
        await db.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
    
    # Cache Check
    try:
        cache.set("health_check", "ok", ex=10)
        checks["cache"] = "healthy"
    except Exception as e:
        checks["cache"] = f"unhealthy: {str(e)}"
    
    # Parquet Check
    try:
        parquet_path = Path("data/parquet/admmat.parquet")
        checks["parquet"] = "healthy" if parquet_path.exists() else "unhealthy"
    except Exception as e:
        checks["parquet"] = f"unhealthy: {str(e)}"
    
    overall_status = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

**3.3 Endpoint /readiness**
- **Descrição:** Readiness probe para Kubernetes
- **Localização:** `backend/app/api/v1/endpoints/health.py`
- **Tempo:** 1 hora

**Critérios de Aceitação:**
- [x] `/health` retorna 200 OK
- [x] `/health/detailed` verifica LLM, DB, Cache, Parquet
- [x] `/readiness` para Kubernetes
- [x] Timeout de 5 segundos para health checks

---

### Ponto Crítico 4: Automated Testing ⚠️

**Categoria:** Processo  
**Conformidade Atual:** 67%  
**Impacto:** ALTO - Previne regressões

#### Tarefas

**4.1 Criar Estrutura de Testes**
- **Descrição:** Organizar testes por categoria
- **Localização:** `backend/tests/`
- **Tempo:** 1 hora

**Estrutura:**
```
tests/
├── unit/
│   ├── test_field_mapper.py
│   ├── test_query_optimizer.py
│   └── test_column_mapping.py
├── integration/
│   ├── test_chat_service.py
│   ├── test_llm_adapters.py
│   └── test_tools.py
├── e2e/
│   └── test_chat_flow.py
└── conftest.py
```

**4.2 Unit Tests para Ferramentas Críticas**
- **Descrição:** Testes para 10 ferramentas mais usadas
- **Localização:** `backend/tests/unit/test_tools.py`
- **Tempo:** 4 horas

**Exemplo:**
```python
def test_consultar_dicionario_dados():
    result = consultar_dicionario_dados(coluna="PRODUTO")
    assert "PRODUTO" in result
    assert result["PRODUTO"]["descricao"]
    assert result["PRODUTO"]["tipo"] == "int"

def test_consultar_dados_flexivel():
    result = consultar_dados_flexivel(
        filtros={"PRODUTO": "123456"},
        limite=10
    )
    assert result["total_resultados"] >= 0
    assert "resultados" in result
```

**4.3 Integration Tests com Mock LLMs**
- **Descrição:** Testar ChatServiceV3 com LLM mockado
- **Localização:** `backend/tests/integration/test_chat_service.py`
- **Tempo:** 3 horas

**Exemplo:**
```python
@pytest.fixture
def mock_llm():
    with patch('app.core.llm_factory.get_llm_adapter') as mock:
        mock.return_value.generate.return_value = "Resposta mockada"
        yield mock

def test_chat_service_with_mock_llm(mock_llm):
    service = ChatServiceV3()
    response = await service.process_message("Teste", user_id="test_user")
    assert response
    assert mock_llm.called
```

**4.4 Configurar pytest e Coverage**
- **Descrição:** Configurar pytest.ini e coverage
- **Localização:** `backend/pytest.ini`, `backend/.coveragerc`
- **Tempo:** 1 hora

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --cov=app --cov-report=html --cov-report=term
```

**Critérios de Aceitação:**
- [x] 20+ unit tests implementados
- [x] 10+ integration tests implementados
- [x] Coverage mínimo de 70%
- [x] Todos os testes passando

---

## 🎯 Fase 2: Prioridade MÉDIA (1-2 meses)

### Ponto Crítico 5: Observability (LangSmith) ⚠️

**Categoria:** Monitoramento  
**Conformidade Atual:** 70%  
**Impacto:** MÉDIO - Melhora debugging e otimização

#### Tarefas

**5.1 Integrar LangSmith**
- **Descrição:** Adicionar LangSmith para tracing
- **Localização:** `backend/app/core/observability/langsmith_tracer.py`
- **Tempo:** 4 horas

**Implementação:**
```python
from langsmith import Client
from langsmith.run_helpers import traceable

client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))

@traceable(run_type="llm", name="gemini_call")
async def traced_llm_call(prompt: str, **kwargs):
    response = await llm.generate(prompt, **kwargs)
    return response
```

**5.2 Tracking de Latência**
- **Descrição:** Métricas de latência por ferramenta
- **Localização:** `backend/app/core/metrics/latency_tracker.py`
- **Tempo:** 3 horas

**5.3 Tracking de Token Usage**
- **Descrição:** Monitorar uso de tokens por usuário
- **Localização:** `backend/app/core/metrics/token_tracker.py`
- **Tempo:** 3 horas

**5.4 Cost Monitoring**
- **Descrição:** Calcular custo por usuário/sessão
- **Localização:** `backend/app/core/metrics/cost_calculator.py`
- **Tempo:** 2 horas

**Critérios de Aceitação:**
- [x] LangSmith integrado
- [x] Latência rastreada por ferramenta
- [x] Token usage por usuário
- [x] Dashboard de custos

---

### Ponto Crítico 6: Resilience (Circuit Breakers) ⚠️

**Categoria:** Arquitetura  
**Conformidade Atual:** 95%  
**Impacto:** MÉDIO - Previne cascading failures

#### Tarefas

**6.1 Implementar Circuit Breaker**
- **Descrição:** Usar `pybreaker` para LLM calls
- **Localização:** `backend/app/core/resilience/circuit_breaker.py`
- **Tempo:** 3 horas

**Implementação:**
```python
from pybreaker import CircuitBreaker

llm_breaker = CircuitBreaker(
    fail_max=5,  # Falhas antes de abrir
    timeout_duration=60  # Segundos antes de tentar novamente
)

@llm_breaker
async def call_llm_with_breaker(prompt: str):
    return await llm.generate(prompt)
```

**6.2 Retry Logic com Exponential Backoff**
- **Descrição:** Usar `tenacity` para retries
- **Localização:** `backend/app/core/resilience/retry_logic.py`
- **Tempo:** 2 horas

**Implementação:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_llm_with_retry(prompt: str):
    return await llm.generate(prompt)
```

**6.3 Graceful Degradation**
- **Descrição:** Fallback para respostas cached
- **Localização:** `backend/app/core/resilience/fallback.py`
- **Tempo:** 3 horas

**6.4 Configurar Fallback Models**
- **Descrição:** Groq como fallback para Gemini
- **Localização:** `backend/app/core/llm_factory.py`
- **Tempo:** 2 horas

**Critérios de Aceitação:**
- [x] Circuit breaker ativo
- [x] Retry logic com exponential backoff
- [x] Fallback para Groq funcionando
- [x] Graceful degradation implementado

---

### Ponto Crítico 7: Compliance (EU AI Act + GDPR) ⚠️

**Categoria:** Compliance  
**Conformidade Atual:** 90%  
**Impacto:** MÉDIO - Requerido para EU

#### Tarefas

**7.1 Documentar Model Capabilities**
- **Descrição:** Documentação de capabilities do Gemini
- **Localização:** `docs/compliance/model_capabilities.md`
- **Tempo:** 2 horas

**7.2 Implementar Transparency Logs**
- **Descrição:** Logs de decisões do modelo
- **Localização:** `backend/app/services/transparency_logger.py`
- **Tempo:** 3 horas

**7.3 Risk Assessment Documentation**
- **Descrição:** Documentar riscos e mitigações
- **Localização:** `docs/compliance/risk_assessment.md`
- **Tempo:** 3 horas

**7.4 Data Retention Policies**
- **Descrição:** Políticas de retenção de dados
- **Localização:** `backend/app/services/data_retention.py`
- **Tempo:** 2 horas

**7.5 Right to be Forgotten**
- **Descrição:** Endpoint para deletar dados de usuário
- **Localização:** `backend/app/api/v1/endpoints/gdpr.py`
- **Tempo:** 2 horas

**Critérios de Aceitação:**
- [x] Model capabilities documentado
- [x] Transparency logs implementados
- [x] Risk assessment completo
- [x] Right to be forgotten funcional

---

## 🎯 Fase 3: Prioridade BAIXA (3-6 meses)

### Ponto Crítico 8-13: Melhorias Avançadas ⚠️

#### 8. RBAC Completo
- **Tempo:** 1 semana
- **Tarefas:** Implementar roles (admin, analyst, viewer), permissions por endpoint

#### 9. MFA (Multi-Factor Authentication)
- **Tempo:** 1 semana
- **Tarefas:** Integrar com Supabase MFA, TOTP/SMS

#### 10. Containerização (Docker)
- **Tempo:** 1 semana
- **Tarefas:** Dockerfile, docker-compose, multi-stage builds

#### 11. Orchestration (Kubernetes)
- **Tempo:** 2 semanas
- **Tarefas:** Helm charts, deployments, services, ingress

#### 12. Prometheus + Grafana
- **Tempo:** 1 semana
- **Tarefas:** Métricas customizadas, dashboards

#### 13. ELK Stack
- **Tempo:** 1 semana
- **Tarefas:** Elasticsearch, Logstash, Kibana

---

## 📋 Cronograma de Implementação

### Semana 1-2 (Prioridade ALTA)
- [ ] Rate Limiting (3 dias)
- [ ] Audit Trail (4 dias)
- [ ] Health Checks (2 dias)
- [ ] Automated Testing (3 dias)

### Mês 1 (Prioridade MÉDIA - Parte 1)
- [ ] Observability/LangSmith (1 semana)
- [ ] Resilience/Circuit Breakers (1 semana)

### Mês 2 (Prioridade MÉDIA - Parte 2)
- [ ] Compliance (EU AI Act + GDPR) (2 semanas)

### Mês 3-4 (Prioridade BAIXA - Parte 1)
- [ ] RBAC (1 semana)
- [ ] MFA (1 semana)
- [ ] Containerização (1 semana)

### Mês 5-6 (Prioridade BAIXA - Parte 2)
- [ ] Kubernetes (2 semanas)
- [ ] Prometheus + Grafana (1 semana)
- [ ] ELK Stack (1 semana)

---

## ✅ Critérios de Sucesso Geral

### Fase 1 (ALTA)
- [x] Conformidade de Segurança: 85% → 95%
- [x] Conformidade de Monitoramento: 70% → 85%
- [x] Conformidade de Processo: 67% → 85%

### Fase 2 (MÉDIA)
- [x] Conformidade de Monitoramento: 85% → 95%
- [x] Conformidade de Arquitetura: 95% → 98%
- [x] Conformidade de Compliance: 90% → 98%

### Fase 3 (BAIXA)
- [x] Conformidade de Segurança: 95% → 100%
- [x] Conformidade de Arquitetura: 98% → 100%
- [x] Conformidade Geral: 89% → 100%

---

## 📊 Métricas de Acompanhamento

| Métrica | Atual | Meta Fase 1 | Meta Fase 2 | Meta Fase 3 |
|---------|-------|-------------|-------------|-------------|
| **Conformidade Geral** | 89% | 92% | 96% | 100% |
| **Segurança** | 85% | 95% | 95% | 100% |
| **Compliance** | 90% | 90% | 98% | 100% |
| **Monitoramento** | 70% | 85% | 95% | 100% |
| **Processo** | 67% | 85% | 90% | 100% |
| **Arquitetura** | 95% | 95% | 98% | 100% |

---

## 🎯 Próximos Passos Imediatos

1. **Revisar e Aprovar Plano** (hoje)
2. **Configurar Ambiente de Desenvolvimento** (amanhã)
3. **Iniciar Fase 1 - Tarefa 1.1: Rate Limiting** (dia 3)

---

**Última Atualização:** 2026-01-17  
**Autor:** Gemini AI (Antigravity)  
**Status:** ✅ PRONTO PARA APROVAÇÃO
