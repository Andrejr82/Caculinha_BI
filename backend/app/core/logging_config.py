"""
Sistema de Logging Centralizado
Configuração completa de logs para o AgentBI Backend
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
import json

from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import structlog


class LogConfig:
    """Configuração centralizada de logging"""

    # Diretórios de logs
    BASE_LOG_DIR = Path("logs")
    APP_LOG_DIR = BASE_LOG_DIR / "app"
    API_LOG_DIR = BASE_LOG_DIR / "api"
    SECURITY_LOG_DIR = BASE_LOG_DIR / "security"
    CHAT_LOG_DIR = BASE_LOG_DIR / "chat"
    ERROR_LOG_DIR = BASE_LOG_DIR / "errors"
    AUDIT_LOG_DIR = BASE_LOG_DIR / "audit"

    # Configurações de rotação
    MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    BACKUP_COUNT = 10

    # Níveis de log por ambiente
    LOG_LEVELS = {
        "development": "DEBUG",
        "staging": "INFO",
        "production": "WARNING"
    }

    @classmethod
    def setup_directories(cls):
        """Cria todos os diretórios de logs necessários"""
        for log_dir in [
            cls.APP_LOG_DIR,
            cls.API_LOG_DIR,
            cls.SECURITY_LOG_DIR,
            cls.CHAT_LOG_DIR,
            cls.ERROR_LOG_DIR,
            cls.AUDIT_LOG_DIR
        ]:
            log_dir.mkdir(parents=True, exist_ok=True)


class JSONFormatter(logging.Formatter):
    """Formatter que gera logs em formato JSON estruturado"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Adiciona informações extras se disponíveis
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "ip_address"):
            log_data["ip_address"] = record.ip_address
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration"):
            log_data["duration"] = record.duration

        # Adiciona exception info se presente
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Adiciona stack info se presente
        if hasattr(record, "stack_info") and record.stack_info:
            log_data["stack_info"] = record.stack_info

        return json.dumps(log_data, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """Formatter com cores para console (development)"""

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def get_file_handler(
    filename: Path,
    level: int = logging.INFO,
    max_bytes: int = LogConfig.MAX_BYTES,
    backup_count: int = LogConfig.BACKUP_COUNT,
    use_json: bool = True
) -> RotatingFileHandler:
    """Cria um handler rotativo para arquivo"""
    handler = RotatingFileHandler(
        filename=filename,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    handler.setLevel(level)

    if use_json:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )

    return handler


def get_timed_file_handler(
    filename: Path,
    level: int = logging.INFO,
    when: str = 'midnight',
    interval: int = 1,
    backup_count: int = 30,
    use_json: bool = True
) -> TimedRotatingFileHandler:
    """Cria um handler com rotação por tempo"""
    handler = TimedRotatingFileHandler(
        filename=filename,
        when=when,
        interval=interval,
        backupCount=backup_count,
        encoding='utf-8'
    )
    handler.setLevel(level)

    if use_json:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )

    return handler


def get_console_handler(level: int = logging.DEBUG, colored: bool = True) -> logging.StreamHandler:
    """Cria um handler para console"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if colored:
        handler.setFormatter(
            ColoredConsoleFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
    else:
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )

    return handler


def setup_logger(
    name: str,
    log_file: Path | None = None,
    level: int = logging.INFO,
    console: bool = True,
    use_json: bool = False
) -> logging.Logger:
    """
    Configura um logger específico

    Args:
        name: Nome do logger
        log_file: Caminho do arquivo de log (opcional)
        level: Nível de log
        console: Se deve mostrar logs no console
        use_json: Se deve usar formato JSON

    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()  # Remove handlers existentes

    # Handler de console
    if console:
        logger.addHandler(get_console_handler(level, colored=True))

    # Handler de arquivo
    if log_file:
        logger.addHandler(get_file_handler(log_file, level, use_json=use_json))

    logger.propagate = False
    return logger


def configure_structlog(environment: str = "development"):
    """
    Configura structlog para logging estruturado

    Args:
        environment: Ambiente de execução (development, staging, production)
    """
    processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Em desenvolvimento, usa console renderer colorido
    # Em produção, usa JSON renderer
    if environment == "development":
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def setup_application_logging(environment: str = "development"):
    """
    Configura todo o sistema de logging da aplicação

    Args:
        environment: Ambiente de execução
    """
    # Cria diretórios
    LogConfig.setup_directories()

    # Configura structlog
    configure_structlog(environment)

    # Nível base de log baseado no ambiente
    base_level = getattr(logging, LogConfig.LOG_LEVELS.get(environment, "INFO"))

    # Logger principal da aplicação
    app_logger = setup_logger(
        "agentbi",
        log_file=LogConfig.APP_LOG_DIR / "app.log",
        level=base_level,
        console=True,
        use_json=(environment != "development")
    )

    # Logger de API
    api_logger = setup_logger(
        "agentbi.api",
        log_file=LogConfig.API_LOG_DIR / "api.log",
        level=logging.INFO,
        console=(environment == "development"),
        use_json=(environment != "development")
    )

    # Logger de segurança
    security_logger = setup_logger(
        "agentbi.security",
        log_file=LogConfig.SECURITY_LOG_DIR / "security.log",
        level=logging.INFO,
        console=True,
        use_json=True  # Sempre JSON para análise de segurança
    )

    # Logger de chat/conversas
    chat_logger = setup_logger(
        "agentbi.chat",
        log_file=LogConfig.CHAT_LOG_DIR / "chat.log",
        level=logging.INFO,
        console=(environment == "development"),
        use_json=True
    )

    # Logger de erros (todos os erros vão aqui também)
    error_logger = setup_logger(
        "agentbi.errors",
        log_file=LogConfig.ERROR_LOG_DIR / "errors.log",
        level=logging.ERROR,
        console=True,
        use_json=True
    )

    # Logger de auditoria
    audit_logger = setup_logger(
        "agentbi.audit",
        log_file=LogConfig.AUDIT_LOG_DIR / "audit.log",
        level=logging.INFO,
        console=False,
        use_json=True  # Sempre JSON para análise de auditoria
    )

    # Configura handler de erros global para capturar tudo
    root_logger = logging.getLogger()
    root_logger.setLevel(base_level)

    # Remove handlers padrão
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
    
    root_logger.handlers.clear()

    # Adiciona handlers
    if environment == "development":
        root_logger.addHandler(get_console_handler(base_level, colored=True))

    # Adiciona handler de arquivo para erros críticos
    root_logger.addHandler(
        get_file_handler(
            LogConfig.ERROR_LOG_DIR / "critical.log",
            level=logging.ERROR,
            use_json=True
        )
    )

    return {
        "app": app_logger,
        "api": api_logger,
        "security": security_logger,
        "chat": chat_logger,
        "errors": error_logger,
        "audit": audit_logger,
    }


# Funções auxiliares para logging específico

def log_api_request(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    user_id: str | None = None,
    ip_address: str | None = None,
    request_id: str | None = None,
    **kwargs
):
    """Log de requisição API"""
    extra = {
        "method": method,
        "endpoint": endpoint,
        "user_id": user_id,
        "ip_address": ip_address,
        "request_id": request_id,
        **kwargs
    }
    logger.info(f"API Request: {method} {endpoint}", extra=extra)


def log_api_response(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    status_code: int,
    duration: float,
    user_id: str | None = None,
    request_id: str | None = None,
    **kwargs
):
    """Log de resposta API"""
    extra = {
        "method": method,
        "endpoint": endpoint,
        "status_code": status_code,
        "duration": duration,
        "user_id": user_id,
        "request_id": request_id,
        **kwargs
    }

    if status_code >= 500:
        logger.error(f"API Response: {method} {endpoint} - {status_code}", extra=extra)
    elif status_code >= 400:
        logger.warning(f"API Response: {method} {endpoint} - {status_code}", extra=extra)
    else:
        logger.info(f"API Response: {method} {endpoint} - {status_code}", extra=extra)


def log_security_event(
    logger: logging.Logger,
    event_type: str,
    user_id: str | None = None,
    ip_address: str | None = None,
    details: dict[str, Any] | None = None,
    success: bool = True
):
    """Log de evento de segurança"""
    extra = {
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": ip_address,
        "success": success,
        "details": details or {}
    }

    if success:
        logger.info(f"Security Event: {event_type}", extra=extra)
    else:
        logger.warning(f"Security Event Failed: {event_type}", extra=extra)


def log_audit_event(
    logger: logging.Logger,
    action: str,
    user_id: str,
    resource: str,
    resource_id: str | None = None,
    changes: dict[str, Any] | None = None,
    ip_address: str | None = None
):
    """Log de evento de auditoria"""
    extra = {
        "action": action,
        "user_id": user_id,
        "resource": resource,
        "resource_id": resource_id,
        "changes": changes or {},
        "ip_address": ip_address
    }
    logger.info(f"Audit: {action} on {resource}", extra=extra)


def log_chat_interaction(
    logger: logging.Logger,
    user_id: str,
    message: str,
    response: str | None = None,
    tokens_used: int | None = None,
    duration: float | None = None,
    model: str | None = None
):
    """Log de interação de chat"""
    extra = {
        "user_id": user_id,
        "message_preview": message[:100] + "..." if len(message) > 100 else message,
        "response_preview": (response[:100] + "..." if response and len(response) > 100 else response) if response else None,
        "tokens_used": tokens_used,
        "duration": duration,
        "model": model
    }
    logger.info(f"Chat interaction from user {user_id}", extra=extra)
