"""
Input Validation Schemas - Pydantic Models

Valida todos os inputs de API para prevenir:
- Payloads maliciosos
- Dados inválidos
- Ataques de injeção
- Buffer overflows

Baseado nas recomendações do Backend Specialist.
"""

from pydantic import BaseModel, Field, validator, constr
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Schema para requisições de chat."""
    
    message: constr(min_length=1, max_length=10000) = Field(
        ...,
        description="Mensagem do usuário",
        example="Quais são as vendas da loja 1685?"
    )
    
    session_id: constr(min_length=1, max_length=100) = Field(
        ...,
        description="ID da sessão",
        example="session_123"
    )
    
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Contexto adicional"
    )
    
    @validator('message')
    def validate_message(cls, v):
        """Valida que a mensagem não contém caracteres suspeitos."""
        # Remover caracteres de controle
        if any(ord(c) < 32 and c not in '\n\r\t' for c in v):
            raise ValueError('Message contains invalid control characters')
        return v.strip()
    
    @validator('session_id')
    def validate_session_id(cls, v):
        """Valida formato do session_id."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Invalid session_id format')
        return v


class ChartRequest(BaseModel):
    """Schema para requisições de gráficos."""
    
    descricao: constr(min_length=1, max_length=500) = Field(
        ...,
        description="Descrição do gráfico",
        example="vendas por segmento"
    )
    
    filtro_une: Optional[str] = Field(
        default=None,
        description="Filtro de UNE (loja)",
        example="1685"
    )
    
    filtro_segmento: Optional[constr(max_length=100)] = Field(
        default=None,
        description="Filtro de segmento"
    )
    
    filtro_categoria: Optional[constr(max_length=100)] = Field(
        default=None,
        description="Filtro de categoria"
    )
    
    tipo_grafico: constr(regex=r'^(bar|pie|line|auto)$') = Field(
        default="auto",
        description="Tipo de gráfico"
    )
    
    limite: Optional[int] = Field(
        default=10,
        ge=1,
        le=100,
        description="Limite de itens"
    )
    
    @validator('filtro_segmento', 'filtro_categoria')
    def validate_filters(cls, v):
        """Valida que filtros não contêm SQL injection."""
        if v is None:
            return v
        
        # Remover caracteres perigosos
        dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'sp_', 'DROP', 'DELETE', 'INSERT', 'UPDATE']
        v_upper = v.upper()
        
        for char in dangerous_chars:
            if char in v_upper:
                raise ValueError(f'Filter contains dangerous pattern: {char}')
        
        return v.strip()


class EOQRequest(BaseModel):
    """Schema para cálculo de EOQ."""
    
    produto_id: constr(min_length=1, max_length=50) = Field(
        ...,
        description="ID do produto",
        example="59294"
    )
    
    demanda_anual: Optional[int] = Field(
        default=None,
        ge=0,
        le=10000000,
        description="Demanda anual estimada"
    )
    
    custo_pedido: Optional[float] = Field(
        default=100.0,
        ge=0,
        le=100000,
        description="Custo por pedido"
    )
    
    custo_armazenagem: Optional[float] = Field(
        default=0.2,
        ge=0,
        le=1,
        description="Custo de armazenagem (% do valor)"
    )
    
    @validator('produto_id')
    def validate_produto_id(cls, v):
        """Valida formato do produto_id."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Invalid produto_id format')
        return v


class ForecastRequest(BaseModel):
    """Schema para previsão de demanda."""
    
    produto_id: constr(min_length=1, max_length=50) = Field(
        ...,
        description="ID do produto"
    )
    
    periodos: int = Field(
        default=30,
        ge=7,
        le=365,
        description="Número de dias para prever"
    )
    
    metodo: constr(regex=r'^(holt-winters|arima|prophet|auto)$') = Field(
        default="auto",
        description="Método de previsão"
    )


class UserLoginRequest(BaseModel):
    """Schema para login de usuário."""
    
    username: constr(min_length=3, max_length=50) = Field(
        ...,
        description="Nome de usuário"
    )
    
    password: constr(min_length=6, max_length=100) = Field(
        ...,
        description="Senha"
    )
    
    @validator('username')
    def validate_username(cls, v):
        """Valida formato do username."""
        if not v.replace('_', '').replace('.', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, _, ., -')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        """Valida força da senha."""
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


class FilterRequest(BaseModel):
    """Schema genérico para filtros."""
    
    une: Optional[List[int]] = Field(
        default=None,
        description="Lista de UNEs"
    )
    
    segmento: Optional[List[str]] = Field(
        default=None,
        description="Lista de segmentos"
    )
    
    categoria: Optional[List[str]] = Field(
        default=None,
        description="Lista de categorias"
    )
    
    data_inicio: Optional[datetime] = Field(
        default=None,
        description="Data de início"
    )
    
    data_fim: Optional[datetime] = Field(
        default=None,
        description="Data de fim"
    )
    
    @validator('une')
    def validate_une_list(cls, v):
        """Valida lista de UNEs."""
        if v and len(v) > 100:
            raise ValueError('Maximum 100 UNEs allowed')
        return v
    
    @validator('segmento', 'categoria')
    def validate_string_lists(cls, v):
        """Valida listas de strings."""
        if v and len(v) > 50:
            raise ValueError('Maximum 50 items allowed')
        
        # Validar cada item
        for item in v or []:
            if len(item) > 100:
                raise ValueError('Item too long (max 100 chars)')
            if not all(c.isalnum() or c.isspace() or c in '-_' for c in item):
                raise ValueError(f'Invalid characters in: {item}')
        
        return v


class PaginationParams(BaseModel):
    """Schema para paginação."""
    
    page: int = Field(
        default=1,
        ge=1,
        le=1000,
        description="Número da página"
    )
    
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Itens por página"
    )
    
    @property
    def offset(self) -> int:
        """Calcula offset para query."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Retorna limit para query."""
        return self.page_size
