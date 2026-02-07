# Segurança e Multi-Tenancy

**Versão:** 2.0  
**Data:** 2026-02-07

---

## 1. Visão Geral

Sistema de segurança em camadas com isolamento por tenant.

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Request ───→ [Rate Limit] ───→ [JWT Auth] ───→ [RBAC]    │
│                                       │           │         │
│                                       ▼           ▼         │
│                               ┌─────────────────────┐       │
│                               │   Tenant Resolver   │       │
│                               │   (from JWT claim)  │       │
│                               └──────────┬──────────┘       │
│                                          │                  │
│                                          ▼                  │
│                               ┌─────────────────────┐       │
│                               │  Row-Level Security │       │
│                               │  (WHERE tenant_id=) │       │
│                               └─────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Autenticação

### JWT Structure
```json
{
  "sub": "user-uuid",
  "tenant_id": "tenant-uuid",
  "email": "user@tenant.com",
  "roles": ["analyst", "admin"],
  "iat": 1707321600,
  "exp": 1707408000
}
```

### Middleware
```python
class JWTMiddleware:
    async def __call__(self, request: Request, call_next):
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(401, "Missing token")
        
        try:
            payload = jwt.decode(token.split()[1], SECRET_KEY)
            request.state.user = payload
            request.state.tenant_id = payload["tenant_id"]
        except JWTError:
            raise HTTPException(401, "Invalid token")
        
        return await call_next(request)
```

---

## 3. Multi-Tenancy

### Tenant Resolver
```python
class TenantResolver:
    """Extrai tenant_id do contexto."""
    
    def resolve(self, request: Request) -> str:
        # 1. JWT claim (preferido)
        if hasattr(request.state, "tenant_id"):
            return request.state.tenant_id
        
        # 2. Header X-Tenant-ID (API keys)
        if "X-Tenant-ID" in request.headers:
            return request.headers["X-Tenant-ID"]
        
        # 3. Subdomain (web)
        host = request.headers.get("Host", "")
        if "." in host:
            return host.split(".")[0]
        
        raise HTTPException(400, "Tenant not resolved")
```

### Row-Level Security
```sql
-- Todas as queries incluem filtro automático
SELECT * FROM conversations 
WHERE tenant_id = :current_tenant_id

-- PostgreSQL RLS Policy
CREATE POLICY tenant_isolation ON conversations
    USING (tenant_id = current_setting('app.tenant_id'));
```

---

## 4. RBAC (Role-Based Access Control)

### Roles
| Role | Permissions |
|------|-------------|
| `viewer` | read:chat, read:insights |
| `analyst` | + write:chat, read:memory |
| `admin` | + write:memory, delete:memory, manage:users |
| `super_admin` | + manage:tenants, manage:billing |

### Permission Check
```python
def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user = request.state.user
            if permission not in get_permissions(user["roles"]):
                raise HTTPException(403, "Permission denied")
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

@router.delete("/memory/{id}")
@require_permission("delete:memory")
async def delete_memory(id: str):
    ...
```

---

## 5. Rate Limiting

```python
class RateLimiter:
    """Rate limit por tenant + endpoint."""
    
    limits = {
        "POST /chat": "60/minute",
        "POST /ingest": "10/minute",
        "GET /memory": "100/minute",
    }
    
    async def check(self, tenant_id: str, endpoint: str) -> bool:
        key = f"rate:{tenant_id}:{endpoint}"
        count = await redis.incr(key)
        
        if count == 1:
            await redis.expire(key, 60)
        
        limit = self._parse_limit(self.limits.get(endpoint, "100/minute"))
        return count <= limit
```

---

## 6. Audit Trail

```python
@dataclass
class AuditLog:
    id: str
    tenant_id: str
    user_id: str
    action: str           # CREATE, READ, UPDATE, DELETE
    resource: str         # conversation, message, document
    resource_id: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    metadata: Dict

# Logging automático
async def audit(action: str, resource: str, resource_id: str):
    log = AuditLog(
        id=str(uuid4()),
        tenant_id=get_current_tenant(),
        user_id=get_current_user(),
        action=action,
        resource=resource,
        resource_id=resource_id,
        timestamp=datetime.utcnow(),
        ip_address=get_client_ip(),
        user_agent=get_user_agent(),
    )
    await audit_repository.save(log)
```

---

## 7. Secrets Management

```python
# .env (development)
JWT_SECRET_KEY=dev-secret-key
GOOGLE_API_KEY=AIza...

# Production: Azure Key Vault / AWS Secrets Manager
class SecretsManager:
    async def get_secret(self, name: str) -> str:
        if os.getenv("ENVIRONMENT") == "production":
            return await azure_keyvault.get_secret(name)
        return os.getenv(name)
```

---

## 8. Security Checklist

- [ ] JWT Middleware implementado
- [ ] Tenant Resolver implementado
- [ ] RBAC implementado
- [ ] Rate Limiting implementado
- [ ] Audit Trail implementado
- [ ] Secrets em Key Vault (produção)
- [ ] HTTPS forçado
- [ ] CORS configurado
- [ ] SQL Injection prevenido
- [ ] XSS prevenido
