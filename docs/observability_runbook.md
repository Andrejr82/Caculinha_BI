# Runbook de Observabilidade - Caculinha BI

Este guia fornece instruções para operação, monitoramento e resolução de problemas da stack de observabilidade.

## 1. Verificação de Saúde (Health Check)

### Logs
Verifique se os logs estão em formato JSON e contêm `request_id`:
```bash
docker logs caculinha-backend | grep "request_id"
```

### Métricas
Acesse o endpoint de métricas: `http://localhost:8000/api/v1/metrics`. Procure por:
- `caculinha_http_requests_total`
- `caculinha_http_request_duration_seconds`

### Prometheus
Acesse o console do Prometheus: `http://localhost:9090`.
- Vá em **Status > Targets** e verifique se o target `caculinha-bi` está `UP`.

---

## 2. Troubleshooting Comum

### Problema: Logs não são JSON
- **Causa:** Variável `LOG_FORMAT` não está como `json` no `.env`.
- **Solução:** Verifique `backend/.env` e garanta `LOG_FORMAT=json`.

### Problema: Métricas não aparecem no Prometheus
- **Causa:** O Prometheus não consegue resolver o host `backend`.
- **Solução:** Verifique se ambos estão na mesma rede Docker (`caculinha-network`).

### Problema: Erro de Import no Backend
- **Causa:** Módulo de observabilidade não está no PYTHONPATH.
- **Solução:** Garanta que os arquivos estão em `backend/app/core/observability` e são importados via `backend.app.core...`.

---

## 3. Adicionando Novas Métricas

Para adicionar uma métrica customizada:
1. Defina o objeto (Counter/Histogram) em `backend/app/core/observability/metrics.py`.
2. Importe e incremente no código:
```python
from backend.app.core.observability.metrics import MY_METRIC
MY_METRIC.labels(label1="val1").inc()
```

---

## 4. Segurança e Redaction

O sistema mascara automaticamente campos como `password`, `token`, etc.
Para adicionar novos campos, atualize a constante `SENSITIVE_KEYS` em `backend/app/core/observability/logging.py`.
