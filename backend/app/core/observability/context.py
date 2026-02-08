
import contextvars
import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class RequestContext:
    """
    Mantém o contexto da requisição atual para logs e tracing.
    """
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    agent_trace_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

# ContextVar para armazenar o contexto da thread/task atual
_context_var: contextvars.ContextVar[RequestContext] = contextvars.ContextVar(
    "request_context", default=RequestContext()
)

def get_context() -> RequestContext:
    """Retorna o contexto atual. Se não existir, cria um default."""
    try:
        return _context_var.get()
    except LookupError:
        ctx = RequestContext()
        _context_var.set(ctx)
        return ctx

def set_context(context: RequestContext):
    """Define o contexto atual."""
    _context_var.set(context)

def reset_context():
    """Reseta o contexto para um novo vazio."""
    _context_var.set(RequestContext())

def get_request_id() -> str:
    return get_context().request_id

def get_tenant_id() -> Optional[str]:
    return get_context().tenant_id
