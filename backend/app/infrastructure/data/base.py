"""
Database Adapter Interface
Abstract Base Class for database adapters (Strategy Interface).
Adapted for Async/FastAPI.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

class DatabaseAdapter(ABC):
    """
    Abstract Base Class for database adapters.
    Defines the common contract for all database connectivity.
    """
    @abstractmethod
    async def connect(self) -> None:
        """Establishes a connection to the database."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Closes the database connection."""
        pass

    @abstractmethod
    async def execute_query(self, query: Any) -> Any:
        """Executes a query and returns the results."""
        pass

    @abstractmethod
    async def get_schema(self) -> Any:
        """Returns the database schema information."""
        pass
