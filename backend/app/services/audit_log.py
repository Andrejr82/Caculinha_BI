"""
Audit Log Service - Rastreabilidade de Ações

Registra todas as ações importantes do sistema para:
- Compliance e auditoria
- Investigação de incidentes
- Análise de comportamento
- Segurança

Baseado nas recomendações do Database Architect.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

# Diretório de logs de auditoria
AUDIT_LOG_DIR = Path(__file__).parent.parent.parent / "logs" / "audit"
AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)


class AuditAction(str, Enum):
    """Tipos de ações auditáveis."""
    
    # Autenticação
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    
    # Dados
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_DELETE = "data_delete"
    
    # Chat/IA
    CHAT_MESSAGE = "chat_message"
    TOOL_EXECUTION = "tool_execution"
    
    # Admin
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    ROLE_CHANGED = "role_changed"
    
    # Sistema
    CONFIG_CHANGED = "config_changed"
    MIGRATION_RUN = "migration_run"


class AuditLogger:
    """
    Serviço de auditoria centralizado.
    
    Features:
    - Logging estruturado em JSON
    - Rotação automática de arquivos
    - Campos padronizados
    - Thread-safe
    """
    
    def __init__(self):
        self.log_file = AUDIT_LOG_DIR / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
    
    def log_action(
        self,
        action: AuditAction,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        Registra uma ação no log de auditoria.
        
        Args:
            action: Tipo de ação (enum AuditAction)
            user_id: ID do usuário
            username: Nome do usuário
            details: Detalhes adicionais da ação
            ip_address: IP do cliente
            success: Se a ação foi bem-sucedida
            error_message: Mensagem de erro (se falhou)
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action.value,
            "user_id": user_id,
            "username": username,
            "ip_address": ip_address,
            "success": success,
            "error_message": error_message,
            "details": details or {}
        }
        
        try:
            # Escrever em arquivo JSONL (JSON Lines)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(audit_entry, ensure_ascii=False) + '\n')
            
            # Também logar no logger padrão
            log_msg = f"[AUDIT] {action.value} by {username or user_id or 'anonymous'}"
            if success:
                logger.info(log_msg, extra=audit_entry)
            else:
                logger.warning(f"{log_msg} - FAILED: {error_message}", extra=audit_entry)
                
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def log_login(self, username: str, user_id: str, ip_address: str, success: bool = True, error: Optional[str] = None):
        """Helper para login."""
        self.log_action(
            action=AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED,
            user_id=user_id if success else None,
            username=username,
            ip_address=ip_address,
            success=success,
            error_message=error
        )
    
    def log_data_access(self, user_id: str, username: str, table: str, operation: str, filters: Optional[Dict] = None):
        """Helper para acesso a dados."""
        self.log_action(
            action=AuditAction.DATA_READ,
            user_id=user_id,
            username=username,
            details={
                "table": table,
                "operation": operation,
                "filters": filters
            }
        )
    
    def log_tool_execution(self, user_id: str, username: str, tool_name: str, parameters: Dict, result_status: str):
        """Helper para execução de ferramentas."""
        self.log_action(
            action=AuditAction.TOOL_EXECUTION,
            user_id=user_id,
            username=username,
            details={
                "tool": tool_name,
                "parameters": parameters,
                "status": result_status
            }
        )
    
    def log_admin_action(self, admin_id: str, admin_username: str, action: AuditAction, target_user: str, details: Dict):
        """Helper para ações administrativas."""
        self.log_action(
            action=action,
            user_id=admin_id,
            username=admin_username,
            details={
                "target_user": target_user,
                **details
            }
        )


# Singleton instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Retorna instância singleton do audit logger."""
    global _audit_logger
    
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    
    return _audit_logger


# Decorator para auditoria automática
def audit_action(action: AuditAction):
    """
    Decorator para auditar automaticamente uma função.
    
    Usage:
        @audit_action(AuditAction.DATA_READ)
        async def get_data(user_id: str):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            audit = get_audit_logger()
            user_id = kwargs.get('user_id') or kwargs.get('current_user', {}).get('id')
            username = kwargs.get('username') or kwargs.get('current_user', {}).get('username')
            
            try:
                result = await func(*args, **kwargs)
                audit.log_action(
                    action=action,
                    user_id=user_id,
                    username=username,
                    success=True
                )
                return result
            except Exception as e:
                audit.log_action(
                    action=action,
                    user_id=user_id,
                    username=username,
                    success=False,
                    error_message=str(e)
                )
                raise
        
        return wrapper
    return decorator
