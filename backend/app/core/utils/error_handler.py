"""
Error Handler - Gerenciamento centralizado de erros.

Este módulo fornece tratamento robusto e centralizado de erros
para o sistema Agent Solution BI.

Funcionalidades:
- Captura de exceções específicas (ParquetFileError, etc)
- Logging estruturado com contexto completo
- Mensagens user-friendly
- Rastreamento de erros recorrentes

Autor: Code Agent
Data: 2025-10-17
"""

import logging
import traceback
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from pathlib import Path
from functools import wraps
import json

logger = logging.getLogger(__name__)

# Diretório para logs de erro
ERROR_LOG_DIR = Path("data/learning")
ERROR_LOG_DIR.mkdir(parents=True, exist_ok=True)


class APIError(Exception):
    """Exceção customizada para erros da API"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ErrorContext:
    """
    Contexto de erro com informações detalhadas.
    """

    def __init__(
        self,
        error: Exception,
        context: Dict[str, Any],
        user_message: Optional[str] = None
    ):
        """
        Inicializa contexto de erro.

        Args:
            error: Exceção capturada
            context: Dicionário com contexto (função, parâmetros, etc)
            user_message: Mensagem personalizada para o usuário
        """
        self.error = error
        self.error_type = type(error).__name__
        self.error_message = str(error)
        self.context = context
        self.user_message = user_message or self._generate_user_message()
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()

    def _generate_user_message(self) -> str:
        """
        Gera mensagem amigável baseada no tipo de erro.

        Returns:
            Mensagem formatada para o usuário
        """
        error_messages = {
            'FileNotFoundError': 'Arquivo de dados não encontrado. Verifique se os dados foram carregados.',
            'PermissionError': 'Sem permissão para acessar o arquivo. Verifique as permissões do sistema.',
            'KeyError': 'Campo não encontrado nos dados. Verifique os parâmetros da consulta.',
            'ValueError': 'Valor inválido encontrado. Verifique os dados de entrada.',
            'TypeError': 'Tipo de dado incompatível na operação.',
            'ParserError': 'Erro ao ler arquivo de dados. O arquivo pode estar corrompido.',
            'MemoryError': 'Memória insuficiente. Tente reduzir o volume de dados consultado.',
            'TimeoutError': 'A operação demorou muito tempo. Tente usar filtros mais específicos.',
            'ConnectionError': 'Erro de conexão. Verifique a conectividade de rede.',
            'OSError': 'Erro de sistema operacional ao acessar arquivos.',
        }

        base_message = error_messages.get(
            self.error_type,
            'Ocorreu um erro ao processar sua solicitação.'
        )

        return f"{base_message}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Converte contexto para dicionário.

        Returns:
            Dict com informações do erro
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'error_type': self.error_type,
            'error_message': self.error_message,
            'user_message': self.user_message,
            'context': self.context,
            'traceback': self.traceback
        }

    def log(self, level: int = logging.ERROR):
        """
        Registra erro no log.

        Args:
            level: Nível de log (logging.ERROR, logging.WARNING, etc)
        """
        logger.log(
            level,
            f"Erro {self.error_type}: {self.error_message}\n"
            f"Contexto: {json.dumps(self.context, indent=2)}\n"
            f"Traceback: {self.traceback}"
        )

    def save_to_file(self):
        """
        Salva erro em arquivo para análise posterior.
        """
        try:
            today = datetime.now().strftime('%Y%m%d')
            error_file = ERROR_LOG_DIR / f"error_log_{today}.jsonl"

            with open(error_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(self.to_dict(), ensure_ascii=False) + '\n')

            logger.debug(f"Erro salvo em {error_file}")

        except Exception as e:
            logger.warning(f"Erro ao salvar log de erro: {e}")


class ErrorHandler:
    """
    Gerenciador centralizado de erros.
    """

    def __init__(self):
        """Inicializa o gerenciador de erros."""
        self.error_counts = {}
        self.last_errors = []
        self.max_last_errors = 100

    def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        user_message: Optional[str] = None,
        log_level: int = logging.ERROR,
        save_to_file: bool = True
    ) -> ErrorContext:
        """
        Trata um erro de forma centralizada.

        Args:
            error: Exceção capturada
            context: Contexto da operação
            user_message: Mensagem personalizada para usuário
            log_level: Nível de log
            save_to_file: Se deve salvar em arquivo

        Returns:
            ErrorContext com informações do erro
        """
        # Criar contexto de erro
        error_ctx = ErrorContext(error, context, user_message)

        # Registrar no log
        error_ctx.log(log_level)

        # Salvar em arquivo se necessário
        if save_to_file:
            error_ctx.save_to_file()

        # Atualizar contadores
        error_type = error_ctx.error_type
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        # Manter histórico de erros recentes
        self.last_errors.append(error_ctx)
        if len(self.last_errors) > self.max_last_errors:
            self.last_errors.pop(0)

        return error_ctx

    def get_error_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas de erros.

        Returns:
            Dict com contadores e informações de erros
        """
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_counts': self.error_counts,
            'recent_errors_count': len(self.last_errors),
            'most_common_error': max(self.error_counts.items(), key=lambda x: x[1])[0] if self.error_counts else None
        }

    def clear_stats(self):
        """Limpa estatísticas de erro."""
        self.error_counts.clear()
        self.last_errors.clear()
        logger.info("Estatísticas de erro limpas")


# Instância global
_error_handler = ErrorHandler()


def handle_error(
    error: Exception,
    context: Dict[str, Any],
    user_message: Optional[str] = None
) -> ErrorContext:
    """
    Função auxiliar para tratamento de erro.

    Args:
        error: Exceção
        context: Contexto
        user_message: Mensagem para usuário

    Returns:
        ErrorContext
    """
    return _error_handler.handle_error(error, context, user_message)


def get_error_stats() -> Dict[str, Any]:
    """Retorna estatísticas de erros."""
    return _error_handler.get_error_stats()


def error_handler_decorator(
    context_func: Optional[Callable] = None,
    user_message: Optional[str] = None,
    return_on_error: Any = None
):
    """
    Decorador para tratamento automático de erros.

    Args:
        context_func: Função que retorna contexto (recebe args, kwargs)
        user_message: Mensagem personalizada para usuário
        return_on_error: Valor a retornar em caso de erro

    Example:
        @error_handler_decorator(
            context_func=lambda *args, **kwargs: {'function': 'my_func', 'args': args},
            return_on_error={'success': False, 'data': []}
        )
        def my_function(param1, param2):
            # código que pode gerar erro
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                # Gerar contexto
                if context_func:
                    context = context_func(*args, **kwargs)
                else:
                    context = {
                        'function': func.__name__,
                        'args': str(args)[:200],  # Limitar tamanho
                        'kwargs': str(kwargs)[:200]
                    }

                # Tratar erro
                error_ctx = _error_handler.handle_error(e, context, user_message)

                # Retornar valor padrão ou re-raise
                if return_on_error is not None:
                    # Se return_on_error for um dict, adicionar mensagem de erro
                    if isinstance(return_on_error, dict):
                        result = return_on_error.copy()
                        result['error'] = error_ctx.user_message
                        result['error_type'] = error_ctx.error_type
                        return result
                    else:
                        return return_on_error
                else:
                    raise

        return wrapper
    return decorator


def create_error_response(
    error: Exception,
    context: Dict[str, Any],
    include_details: bool = False
) -> Dict[str, Any]:
    """
    Cria resposta padronizada de erro.

    Args:
        error: Exceção capturada
        context: Contexto da operação
        include_details: Se deve incluir detalhes técnicos

    Returns:
        Dict com resposta de erro formatada
    """
    error_ctx = _error_handler.handle_error(error, context)

    response = {
        'success': False,
        'data': [],
        'count': 0,
        'message': error_ctx.user_message,
        'error_type': error_ctx.error_type,
        'timestamp': error_ctx.timestamp.isoformat()
    }

    if include_details:
        response['error_details'] = {
            'error_message': error_ctx.error_message,
            'context': error_ctx.context
        }

    return response


# Mapeamento de exceções específicas do Parquet
class ParquetErrorHandler:
    """
    Handler específico para erros relacionados a arquivos Parquet.
    """

    @staticmethod
    def handle_parquet_error(error: Exception, file_path: str) -> Dict[str, Any]:
        """
        Trata erros específicos de Parquet.

        Args:
            error: Exceção
            file_path: Caminho do arquivo Parquet

        Returns:
            Dict com resposta de erro
        """
        context = {
            'operation': 'parquet_read',
            'file_path': file_path,
            'file_exists': Path(file_path).exists()
        }

        # Mensagens específicas para erros Parquet
        parquet_messages = {
            'ArrowInvalid': 'Arquivo Parquet inválido ou corrompido.',
            'ArrowIOError': 'Erro de I/O ao ler arquivo Parquet.',
            'OSError': f'Não foi possível acessar o arquivo: {file_path}',
        }

        error_type = type(error).__name__
        user_message = parquet_messages.get(error_type)

        return create_error_response(error, context, include_details=False)


if __name__ == "__main__":
    # Teste básico do error handler
    logging.basicConfig(level=logging.INFO)

    # Teste 1: Erro simples
    try:
        raise ValueError("Teste de erro")
    except Exception as e:
        error_ctx = handle_error(
            e,
            context={'function': 'test', 'param': 'value'}
        )
        print(f"\nMensagem para usuário: {error_ctx.user_message}")

    # Teste 2: Estatísticas
    stats = get_error_stats()
    print(f"\nEstatísticas: {stats}")

    # Teste 3: Decorador
    @error_handler_decorator(
        context_func=lambda x: {'param': x},
        return_on_error={'success': False, 'data': []}
    )
    def test_function(param):
        if param == 'error':
            raise KeyError("Campo não encontrado")
        return {'success': True, 'data': [param]}

    result = test_function('error')
    print(f"\nResultado com erro: {result}")

    result = test_function('ok')
    print(f"Resultado sem erro: {result}")
