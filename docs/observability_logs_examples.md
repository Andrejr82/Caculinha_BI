# Exemplos de Logs JSON (Observabilidade)

Este documento demonstra o formato de saída dos logs estruturados implementados na Fase 2.

## 1. Requisição Iniciada (Start)

Emitido pelo `ObservabilityMiddleware` assim que a requisição chega.

```json
{
  "timestamp": "2026-02-07T18:45:00.123Z",
  "level": "INFO",
  "service": "caculinha-bi",
  "message": "http_request_started",
  "request_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "tenant_id": null,
  "component": "backend.core.observability.middleware",
  "method": "POST",
  "path": "/api/v2/chat",
  "user_agent": "Mozilla/5.0..."
}
```
*Nota: `tenant_id` é null no início pois a autenticação ainda não ocorreu.*

## 2. Requisição Finalizada com Sucesso (Success)

Emitido após o processamento, com duração e status code.

```json
{
  "timestamp": "2026-02-07T18:45:02.456Z",
  "level": "INFO",
  "service": "caculinha-bi",
  "message": "http_request_finished",
  "request_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "tenant_id": "loja-1685",
  "component": "backend.core.observability.middleware",
  "method": "POST",
  "path": "/api/v2/chat",
  "status_code": 200,
  "duration_s": 2.333,
  "tenant_id": "loja-1685"
}
```
*Nota: `tenant_id` agora está preenchido, propagado pelo `TenantMiddleware`.*

## 3. Requisição com Erro (Error)

Emitido se uma exceção não tratada ocorrer.

```json
{
  "timestamp": "2026-02-07T18:46:00.999Z",
  "level": "ERROR",
  "service": "caculinha-bi",
  "message": "http_request_failed",
  "request_id": "f9e8d7c6-b5a4-3210-9876-543210fedcba",
  "tenant_id": "loja-123",
  "component": "backend.core.observability.middleware",
  "method": "GET",
  "path": "/api/v2/metrics",
  "error": "Database connection timeout",
  "duration_s": 5.001,
  "exception": "Traceback (most recent call last):\n  File \"...\"",
  "stack_info": "..."
}
```

## 4. Log de Aplicação (Dentro de um Serviço)

Exemplo de log emitido manualmente pelo `logger.info()` dentro da lógica de negócio.

```json
{
  "timestamp": "2026-02-07T18:45:01.000Z",
  "level": "INFO",
  "service": "caculinha-bi",
  "message": "Searching vector database",
  "request_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "tenant_id": "loja-1685",
  "component": "backend.services.rag_service",
  "query": "qual o faturamento?",
  "top_k": 5
}
```
