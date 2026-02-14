"""
Settings Configuration
Pydantic Settings with environment variables
"""

from functools import lru_cache
from typing import Literal
import os

from pydantic import Field, field_validator, model_validator, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    """Application settings"""

    # Calculate absolute path to .env file
    # backend/app/config/settings.py -> backend/.env
    _base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _env_path = os.path.join(_base_dir, ".env")

    model_config = SettingsConfigDict(
        env_file=_env_path,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "Agent BI Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # API
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000"
    )

    # @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    # @classmethod
    # def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
    #     if isinstance(v, str):
    #         return [i.strip() for i in v.split(",")]
    #     return v

    # Database - SQL Server
    # Usando aioodbc para suporte assíncrono com SQLAlchemy
    DATABASE_URL: str = Field(
        default=""
    )
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # Connection string para aioodbc (SQLServerAdapter)
    # Deve corresponder aos mesmos parâmetros do DATABASE_URL
    PYODBC_CONNECTION_STRING: str = Field(
        default=""
    )
    
    # Hybrid Architecture Flags
    USE_SQL_SERVER: bool = False  # Disabled by default to prevent timeouts
    FALLBACK_TO_PARQUET: bool = True
    SQL_SERVER_TIMEOUT: int = 2  # Reduced timeout

    # Redis
    REDIS_URL: RedisDsn = Field(default="redis://localhost:6379/0")
    REDIS_CACHE_TTL: int = 3600  # 1 hour

    # Custom Cache Settings
    CACHE_TTL_MINUTES: int = 360 # 6 hours for LLM responses
    CACHE_MAX_AGE_DAYS: int = 7 # For cache cleaner
    AGENT_GRAPH_CACHE_TTL_MINUTES: int = 360 # 6 hours for agent graph cache
    
    # Cache Directory (Updated to v2 to bypass corruption)
    CACHE_DIR: str = "data/cache_v2"

    # RAG (Retrieval Augmented Generation)
    RAG_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RAG_FAISS_INDEX_PATH: str = "data/rag/faiss_index.bin"

    # Learning System
    LEARNING_FEEDBACK_PATH: str = "data/feedback/"
    LEARNING_EXAMPLES_PATH: str = "data/learning/"
    LEARNING_MAX_EXAMPLES: int = 1000

    # Security
    SECRET_KEY: str = Field(default=None) # Must be set in environment
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_AUTH_PER_MINUTE: int = 5

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["json", "console"] = "json"

    # Sentry
    SENTRY_DSN: str | None = None
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # Prometheus
    METRICS_ENABLED: bool = True

    # AI / LLM - Multi-provider Support
    # FIX 2026-01-09: Groq é o LLM principal (mais rápido, sem rate limit frequente)
    LLM_PROVIDER: Literal["google", "groq", "mock"] = "google"
    PLAYGROUND_MODE: Literal["local_only", "hybrid_optional", "remote_required"] = "local_only"
    PLAYGROUND_CANARY_ENABLED: bool = False
    PLAYGROUND_CANARY_ALLOWED_ROLES: str = "admin"
    PLAYGROUND_CANARY_ALLOWED_USERS: str = ""
    
    # Google Gemini
    GEMINI_API_KEY: str | None = None
    LLM_MODEL_NAME: str = "gemini-2.5-pro"
    
    # Groq
    GROQ_API_KEY: str | None = None
    GROQ_MODEL_NAME: str = "llama-3.3-70b-versatile"
    DEV_FAST_MODE: bool = False
    LLM_MAX_OUTPUT_TOKENS: int = 2048
    LLM_HISTORY_MAX_MESSAGES: int = 15

    # Modelos de Tarefa
    INTENT_CLASSIFICATION_MODEL: str = "gemini-2.5-pro"
    CODE_GENERATION_MODEL: str = "gemini-2.5-pro"

    # Data Sources
    PARQUET_DATA_PATH: str = Field(default="data/parquet/admmat.parquet")
    PARQUET_FILE_PATH: str = Field(default="data/parquet/admmat.parquet")  # Alias for compatibility
    
    # Business Rules
    ALLOWED_UNES: list[int] = Field(default=[
        1, 3, 11, 35, 57, 64, 79, 81, 135, 148, 265, 520, 1685, 1974, 
        2365, 2401, 2475, 2586, 2599, 2720, 2906, 2952, 3038, 3054, 
        3091, 3116, 3281, 3318, 3387, 3404, 3481, 3499, 3577, 3578, 
        5570, 5822
    ])

    # Supabase
    SUPABASE_URL: str = Field(default="")
    SUPABASE_ANON_KEY: str = Field(default="")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="")  # Required for admin operations
    USE_SUPABASE_AUTH: bool = Field(default=True)  # Enabled by default per user request

    @model_validator(mode="after")
    def validate_secret_key(self) -> "Settings":
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return self

    @model_validator(mode="after")
    def resolve_paths(self) -> "Settings":
        """Resolve relative paths to absolute paths based on _base_dir"""
        # [OK] FIX 2026-02-12: Ensure data paths are absolute relative to backend root
        # This prevents issues when starting the app from different CWDs (e.g. root vs backend)
        path_fields = [
            "PARQUET_DATA_PATH", "PARQUET_FILE_PATH", "CACHE_DIR",
            "RAG_FAISS_INDEX_PATH", "LEARNING_FEEDBACK_PATH", "LEARNING_EXAMPLES_PATH"
        ]
        
        for field in path_fields:
            val = getattr(self, field, None)
            if val and isinstance(val, str) and not os.path.isabs(val):
                abs_path = os.path.normpath(os.path.join(self._base_dir, val))
                setattr(self, field, abs_path)
                
        return self

    @model_validator(mode="after")
    def compute_pyodbc_string(self) -> "Settings":
        # OTIMIZAÇÃO: Se DATABASE_URL vazio, desabilitar SQL Server (evita timeout de 10s no login!)
        if not self.DATABASE_URL or self.DATABASE_URL.strip() == "":
            self.USE_SQL_SERVER = False
            self.FALLBACK_TO_PARQUET = True
            return self

        # Força a verificação da variável de ambiente para USE_SQL_SERVER
        if os.environ.get("USE_SQL_SERVER", "false").lower() == "true":
            self.USE_SQL_SERVER = True
        # Se a URL for SQLite, e a variável de ambiente não for true, desabilitar o uso do SQL Server
        elif self.DATABASE_URL and self.DATABASE_URL.startswith("sqlite"):
            self.USE_SQL_SERVER = False
            self.FALLBACK_TO_PARQUET = True
            return self

        # Se PYODBC_CONNECTION_STRING for o default, tentar derivar de DATABASE_URL
        default_pyodbc = Settings.model_fields["PYODBC_CONNECTION_STRING"].default
        if self.PYODBC_CONNECTION_STRING == default_pyodbc and self.DATABASE_URL:
            try:
                url = make_url(str(self.DATABASE_URL))
                # Construir string ODBC
                # DRIVER={driver};SERVER=host;DATABASE=db;UID=user;PWD=pass
                driver = url.query.get("driver", "ODBC Driver 17 for SQL Server")
                trust_cert = url.query.get("TrustServerCertificate", "yes")
                
                # Tratar host e port
                server = url.host
                if url.port:
                    server = f"{server},{url.port}"
                
                conn_str = (
                    f"DRIVER={{{driver}}};"
                    f"SERVER={server};"
                    f"DATABASE={url.database};"
                    f"TrustServerCertificate={trust_cert};"
                )
                
                if url.username:
                    conn_str += f"UID={url.username};PWD={url.password};"
                else:
                    conn_str += "Trusted_Connection=yes;"
                    
                self.PYODBC_CONNECTION_STRING = conn_str
            except Exception:
                # Se falhar, manter o default ou o que foi passado
                pass
        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
try:
    # MANUAL ENV LOADER (Robustness Fix)
    # Pydantic sometimes fails to read .env if shell vars are set or cache is stale
    # This block forces loading from .env if not already set or to override
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _env = os.path.join(_base, ".env")
    if os.path.exists(_env):
        with open(_env, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip()

                    # Remove inline comments while preserving # inside quoted strings.
                    in_single = False
                    in_double = False
                    clean_chars: list[str] = []
                    for ch in v:
                        if ch == "'" and not in_double:
                            in_single = not in_single
                        elif ch == '"' and not in_single:
                            in_double = not in_double
                        elif ch == "#" and not in_single and not in_double:
                            break
                        clean_chars.append(ch)
                    v = "".join(clean_chars).strip()

                    # Remove surrounding matching quotes
                    if len(v) >= 2 and ((v[0] == '"' and v[-1] == '"') or (v[0] == "'" and v[-1] == "'")):
                        v = v[1:-1]
                    
                    # Override or Set
                    # We want to force read from file if pydantic is failing, 
                    # but usually env vars have precedence.
                    # However, since we cleared shell vars, this should fill them.
                    # If we want to strictly follow .env file content:
                    os.environ[k] = v
except Exception as e:
    pass

settings = get_settings()
