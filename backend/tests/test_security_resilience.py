"""
Testes de Regressão - Novas Features de Segurança e Resiliência

Testa todas as implementações do roadmap:
- Rate limiting
- Input validation
- Audit log
- Circuit breaker
- Background tasks

Baseado nas recomendações do Code Archaeologist.
"""

import pytest
import asyncio
from datetime import datetime
from app.middleware.rate_limit import limiter, get_rate_limit
from app.schemas.validation import ChatRequest, ChartRequest, EOQRequest
from app.services.audit_log import get_audit_logger, AuditAction
from app.infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitState
from app.services.background_tasks import get_task_manager, TaskStatus


class TestRateLimiting:
    """Testes para rate limiting."""
    
    def test_rate_limit_configuration(self):
        """Testa configuração de rate limits."""
        assert get_rate_limit("auth") == "10/minute"
        assert get_rate_limit("chat") == "100/minute"
        assert get_rate_limit("read") == "500/minute"
        assert get_rate_limit("write") == "100/minute"
        assert get_rate_limit("admin") == "50/minute"
    
    def test_limiter_instance(self):
        """Testa que limiter é singleton."""
        limiter1 = limiter
        limiter2 = limiter
        assert limiter1 is limiter2


class TestInputValidation:
    """Testes para validação de input."""
    
    def test_chat_request_valid(self):
        """Testa validação de ChatRequest válido."""
        request = ChatRequest(
            message="Quais são as vendas?",
            session_id="session_123"
        )
        assert request.message == "Quais são as vendas?"
        assert request.session_id == "session_123"
    
    def test_chat_request_invalid_message(self):
        """Testa rejeição de mensagem com caracteres de controle."""
        with pytest.raises(ValueError):
            ChatRequest(
                message="Test\x00message",  # Null byte
                session_id="session_123"
            )
    
    def test_chat_request_too_long(self):
        """Testa rejeição de mensagem muito longa."""
        with pytest.raises(ValueError):
            ChatRequest(
                message="x" * 10001,  # Excede max_length
                session_id="session_123"
            )
    
    def test_chart_request_valid(self):
        """Testa validação de ChartRequest válido."""
        request = ChartRequest(
            descricao="vendas por segmento",
            filtro_une="1685",
            tipo_grafico="bar",
            limite=10
        )
        assert request.descricao == "vendas por segmento"
        assert request.tipo_grafico == "bar"
    
    def test_chart_request_invalid_tipo(self):
        """Testa rejeição de tipo de gráfico inválido."""
        with pytest.raises(ValueError):
            ChartRequest(
                descricao="test",
                tipo_grafico="invalid_type"
            )
    
    def test_chart_request_sql_injection_prevention(self):
        """Testa prevenção de SQL injection em filtros."""
        with pytest.raises(ValueError):
            ChartRequest(
                descricao="test",
                filtro_segmento="'; DROP TABLE users; --"
            )
    
    def test_eoq_request_valid(self):
        """Testa validação de EOQRequest válido."""
        request = EOQRequest(
            produto_id="59294",
            demanda_anual=1000,
            custo_pedido=100.0,
            custo_armazenagem=0.2
        )
        assert request.produto_id == "59294"
        assert request.demanda_anual == 1000


class TestAuditLog:
    """Testes para audit log."""
    
    def test_audit_logger_singleton(self):
        """Testa que audit logger é singleton."""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()
        assert logger1 is logger2
    
    def test_log_action(self):
        """Testa logging de ação."""
        audit = get_audit_logger()
        
        # Não deve lançar exceção
        audit.log_action(
            action=AuditAction.LOGIN,
            user_id="test_user",
            username="testuser",
            ip_address="127.0.0.1",
            success=True
        )
    
    def test_log_login_helper(self):
        """Testa helper de login."""
        audit = get_audit_logger()
        
        # Login bem-sucedido
        audit.log_login(
            username="admin",
            user_id="123",
            ip_address="192.168.1.1",
            success=True
        )
        
        # Login falho
        audit.log_login(
            username="hacker",
            user_id="",
            ip_address="1.2.3.4",
            success=False,
            error="Invalid credentials"
        )


class TestCircuitBreaker:
    """Testes para circuit breaker."""
    
    def test_circuit_breaker_initial_state(self):
        """Testa estado inicial do circuit breaker."""
        breaker = CircuitBreaker(failure_threshold=3)
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    def test_circuit_breaker_opens_after_failures(self):
        """Testa que circuit abre após threshold de falhas."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        def failing_func():
            raise Exception("Test failure")
        
        # 3 falhas devem abrir o circuit
        for _ in range(3):
            try:
                breaker.call(failing_func)
            except Exception:
                pass
        
        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3
    
    def test_circuit_breaker_rejects_when_open(self):
        """Testa que circuit rejeita quando aberto."""
        breaker = CircuitBreaker(failure_threshold=1)
        
        def failing_func():
            raise Exception("Test failure")
        
        # Abrir circuit
        try:
            breaker.call(failing_func)
        except Exception:
            pass
        
        # Deve rejeitar próxima chamada
        from app.infrastructure.resilience.circuit_breaker import CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(failing_func)
    
    def test_circuit_breaker_stats(self):
        """Testa estatísticas do circuit breaker."""
        breaker = CircuitBreaker()
        stats = breaker.get_stats()
        
        assert "state" in stats
        assert "total_calls" in stats
        assert "success_rate" in stats


class TestBackgroundTasks:
    """Testes para background tasks."""
    
    @pytest.mark.asyncio
    async def test_task_manager_singleton(self):
        """Testa que task manager é singleton."""
        manager1 = get_task_manager()
        manager2 = get_task_manager()
        assert manager1 is manager2
    
    @pytest.mark.asyncio
    async def test_add_task(self):
        """Testa adição de tarefa."""
        manager = get_task_manager()
        
        async def dummy_task():
            await asyncio.sleep(0.1)
            return "completed"
        
        task_id = await manager.add_task(dummy_task, name="Test Task")
        
        assert task_id is not None
        task = manager.get_task(task_id)
        assert task is not None
        assert task.name == "Test Task"
    
    @pytest.mark.asyncio
    async def test_task_completion(self):
        """Testa conclusão de tarefa."""
        manager = get_task_manager()
        
        async def quick_task():
            return "done"
        
        task_id = await manager.add_task(quick_task)
        await manager.wait_for_task(task_id, timeout=1.0)
        
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "done"
    
    @pytest.mark.asyncio
    async def test_task_failure(self):
        """Testa falha de tarefa."""
        manager = get_task_manager()
        
        async def failing_task():
            raise ValueError("Test error")
        
        task_id = await manager.add_task(failing_task)
        await manager.wait_for_task(task_id, timeout=1.0)
        
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.FAILED
        assert "Test error" in task.error


# Testes de integração
class TestIntegration:
    """Testes de integração entre componentes."""
    
    @pytest.mark.asyncio
    async def test_audit_log_with_background_task(self):
        """Testa audit log em background task."""
        audit = get_audit_logger()
        manager = get_task_manager()
        
        async def audited_task():
            audit.log_action(
                action=AuditAction.DATA_READ,
                user_id="test",
                username="testuser"
            )
            return "logged"
        
        task_id = await manager.add_task(audited_task)
        await manager.wait_for_task(task_id, timeout=1.0)
        
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
