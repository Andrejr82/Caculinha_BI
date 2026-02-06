"""
Background Tasks Service - Processamento Assíncrono

Gerencia tarefas em background para:
- Operações pesadas
- Processamento batch
- Jobs agendados
- Limpeza de dados

Baseado nas recomendações do Backend Specialist.
"""

import asyncio
import logging
from typing import Callable, Any, Optional, Dict
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from uuid import uuid4

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Status de uma tarefa em background."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackgroundTask:
    """Representa uma tarefa em background."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    progress: int = 0  # 0-100
    
    def mark_running(self):
        """Marca tarefa como em execução."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
    
    def mark_completed(self, result: Any = None):
        """Marca tarefa como completa."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
        self.progress = 100
    
    def mark_failed(self, error: str):
        """Marca tarefa como falha."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
    
    def update_progress(self, progress: int):
        """Atualiza progresso da tarefa."""
        self.progress = min(100, max(0, progress))


class BackgroundTaskManager:
    """
    Gerenciador de tarefas em background.
    
    Features:
    - Execução assíncrona
    - Rastreamento de status
    - Progresso em tempo real
    - Cancelamento de tarefas
    """
    
    def __init__(self):
        self.tasks: Dict[str, BackgroundTask] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
    
    async def add_task(
        self,
        func: Callable,
        *args,
        name: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Adiciona uma tarefa para execução em background.
        
        Args:
            func: Função async a ser executada
            *args, **kwargs: Argumentos da função
            name: Nome descritivo da tarefa
            
        Returns:
            ID da tarefa
        """
        task = BackgroundTask(name=name or func.__name__)
        self.tasks[task.id] = task
        
        # Criar task asyncio
        asyncio_task = asyncio.create_task(
            self._execute_task(task, func, *args, **kwargs)
        )
        self._running_tasks[task.id] = asyncio_task
        
        logger.info(f"Background task created: {task.name} ({task.id})")
        return task.id
    
    async def _execute_task(
        self,
        task: BackgroundTask,
        func: Callable,
        *args,
        **kwargs
    ):
        """Executa uma tarefa em background."""
        task.mark_running()
        logger.info(f"Starting background task: {task.name}")
        
        try:
            # Executar função
            result = await func(*args, **kwargs)
            
            # Marcar como completa
            task.mark_completed(result)
            logger.info(f"Background task completed: {task.name}")
            
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            logger.warning(f"Background task cancelled: {task.name}")
            
        except Exception as e:
            task.mark_failed(str(e))
            logger.error(f"Background task failed: {task.name} - {e}", exc_info=True)
            
        finally:
            # Remover da lista de running
            if task.id in self._running_tasks:
                del self._running_tasks[task.id]
    
    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """Retorna informações de uma tarefa."""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, BackgroundTask]:
        """Retorna todas as tarefas."""
        return self.tasks.copy()
    
    def get_running_tasks(self) -> Dict[str, BackgroundTask]:
        """Retorna tarefas em execução."""
        return {
            task_id: task
            for task_id, task in self.tasks.items()
            if task.status == TaskStatus.RUNNING
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancela uma tarefa em execução.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            True se cancelada, False se não estava rodando
        """
        if task_id not in self._running_tasks:
            return False
        
        asyncio_task = self._running_tasks[task_id]
        asyncio_task.cancel()
        
        logger.info(f"Cancelled background task: {task_id}")
        return True
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None):
        """
        Aguarda conclusão de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            timeout: Timeout em segundos
        """
        if task_id not in self._running_tasks:
            return
        
        asyncio_task = self._running_tasks[task_id]
        
        try:
            await asyncio.wait_for(asyncio_task, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for task: {task_id}")
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """
        Remove tarefas antigas do histórico.
        
        Args:
            max_age_hours: Idade máxima em horas
        """
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        
        to_remove = [
            task_id
            for task_id, task in self.tasks.items()
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
            and task.completed_at
            and task.completed_at.timestamp() < cutoff
        ]
        
        for task_id in to_remove:
            del self.tasks[task_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old background tasks")


# Singleton instance
_task_manager: Optional[BackgroundTaskManager] = None


def get_task_manager() -> BackgroundTaskManager:
    """Retorna instância singleton do task manager."""
    global _task_manager
    
    if _task_manager is None:
        _task_manager = BackgroundTaskManager()
    
    return _task_manager


# Helper para FastAPI BackgroundTasks integration
async def add_background_task(func: Callable, *args, name: Optional[str] = None, **kwargs) -> str:
    """
    Helper para adicionar tarefa em background.
    
    Usage:
        task_id = await add_background_task(heavy_processing, data=data)
    """
    manager = get_task_manager()
    return await manager.add_task(func, *args, name=name, **kwargs)
