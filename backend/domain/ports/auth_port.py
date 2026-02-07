"""
Port: AuthPort

Interface abstrata para autenticação e autorização.
Implementada por: SupabaseAdapter, JWTAdapter

Uso:
    from backend.domain.ports import AuthPort
    
    class SupabaseAdapter(AuthPort):
        async def authenticate(self, token):
            ...

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class UserInfo:
    """
    Informações do usuário autenticado.
    
    Attributes:
        id: ID do usuário
        email: Email do usuário
        tenant_id: ID do tenant
        roles: Lista de papéis
        metadata: Metadados adicionais
    """
    
    id: str
    email: str
    tenant_id: str
    roles: List[str]
    metadata: Dict[str, Any]
    
    @property
    def is_admin(self) -> bool:
        """Verifica se o usuário é admin."""
        return "admin" in self.roles


class AuthPort(ABC):
    """
    Interface abstrata para autenticação e autorização.
    
    Esta é a porta para verificação de identidade e permissões.
    Implementações concretas em infrastructure/adapters/auth/
    
    Example:
        >>> class SupabaseAdapter(AuthPort):
        ...     async def authenticate(self, token):
        ...         # Validar token com Supabase
        ...         pass
    """
    
    @abstractmethod
    async def authenticate(self, token: str) -> Optional[UserInfo]:
        """
        Autentica um token e retorna informações do usuário.
        
        Args:
            token: Token de autenticação (JWT, API Key, etc.)
        
        Returns:
            UserInfo se autenticado, None se inválido
        """
        pass
    
    @abstractmethod
    async def authorize(
        self,
        user: UserInfo,
        resource: str,
        action: str,
    ) -> bool:
        """
        Verifica se o usuário tem permissão para uma ação.
        
        Args:
            user: Informações do usuário
            resource: Recurso sendo acessado
            action: Ação sendo executada (read, write, delete)
        
        Returns:
            True se autorizado
        """
        pass
    
    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[UserInfo]:
        """
        Obtém informações de usuário por ID.
        
        Args:
            user_id: ID do usuário
        
        Returns:
            UserInfo ou None
        """
        pass
    
    @abstractmethod
    async def validate_tenant_access(
        self,
        user: UserInfo,
        tenant_id: str,
    ) -> bool:
        """
        Valida se o usuário tem acesso a um tenant.
        
        Args:
            user: Informações do usuário
            tenant_id: ID do tenant
        
        Returns:
            True se tem acesso
        """
        pass
    
    @abstractmethod
    async def refresh_token(self, token: str) -> Optional[str]:
        """
        Renova um token de autenticação.
        
        Args:
            token: Token atual
        
        Returns:
            Novo token ou None se não puder renovar
        """
        pass
