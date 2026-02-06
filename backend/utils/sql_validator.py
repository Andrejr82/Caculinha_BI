"""
SQL Validator - Validação de segurança para queries SQL
FIX 2026-02-04: Novo módulo para prevenir SQL injection e queries perigosas

Funcionalidades:
- Bloqueia operações perigosas (DELETE, DROP, etc)
- Limita JOINs (máx 3)
- Adiciona LIMIT automático se ausente
- Valida sintaxe SQL com sqlparse
"""

import re
import logging
from typing import Tuple, List

try:
    import sqlparse
    SQLPARSE_AVAILABLE = True
except ImportError:
    SQLPARSE_AVAILABLE = False

logger = logging.getLogger(__name__)


class SQLValidationError(Exception):
    """Exceção customizada para erros de validação SQL"""
    pass


class SQLValidator:
    """Valida queries SQL antes de execução"""
    
    # Operações proibidas
    FORBIDDEN_KEYWORDS = [
        'DELETE', 'DROP', 'TRUNCATE', 'ALTER', 
        'CREATE', 'UPDATE', 'INSERT', 'GRANT',
        'REVOKE', 'EXEC', 'EXECUTE', 'PRAGMA'
    ]
    
    # Máximos permitidos
    MAX_JOINS = 3
    MAX_SUBQUERIES = 2
    DEFAULT_LIMIT = 500
    
    def __init__(self):
        self.validation_errors: List[str] = []
    
    def validate(self, sql: str) -> Tuple[bool, str]:
        """
        Valida query SQL
        
        Args:
            sql: String SQL para validar
            
        Returns:
            (is_valid, error_message)
        """
        self.validation_errors = []
        
        if not sql or not sql.strip():
            return False, "Query SQL vazia"
        
        try:
            # 1. Check forbidden keywords
            if not self._check_forbidden_keywords(sql):
                return False, self.validation_errors[0]
            
            # 2. Parse SQL (se sqlparse disponível)
            if SQLPARSE_AVAILABLE:
                parsed = self._parse_sql(sql)
                if not parsed:
                    return False, "SQL inválido ou malformado"
                
                # 3. Check statement type
                if not self._check_statement_type(parsed):
                    return False, self.validation_errors[0]
            
            # 4. Check joins count
            if not self._check_joins_count(sql):
                return False, self.validation_errors[0]
            
            # 5. Check dangerous patterns
            if not self._check_dangerous_patterns(sql):
                return False, self.validation_errors[0]
            
            return True, "OK"
            
        except Exception as e:
            logger.error(f"Erro na validação SQL: {e}")
            return False, f"Erro na validação: {str(e)}"
    
    def _check_forbidden_keywords(self, sql: str) -> bool:
        """Verifica presença de keywords proibidas"""
        sql_upper = sql.upper()
        
        for keyword in self.FORBIDDEN_KEYWORDS:
            # Procura palavra completa (não substring)
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_upper):
                self.validation_errors.append(
                    f"Operação '{keyword}' não permitida. "
                    f"Apenas consultas SELECT são aceitas."
                )
                return False
        
        return True
    
    def _parse_sql(self, sql: str):
        """Parse SQL usando sqlparse"""
        if not SQLPARSE_AVAILABLE:
            return None
            
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return None
            return parsed[0]
        except Exception:
            return None
    
    def _check_statement_type(self, statement) -> bool:
        """Verifica se é SELECT statement"""
        if not SQLPARSE_AVAILABLE or statement is None:
            return True  # Skip check se sqlparse não disponível
            
        stmt_type = statement.get_type()
        
        if stmt_type and stmt_type != 'SELECT':
            self.validation_errors.append(
                f"Tipo de statement '{stmt_type}' não permitido. "
                f"Apenas SELECT é aceito."
            )
            return False
        
        return True
    
    def _check_joins_count(self, sql: str) -> bool:
        """Verifica número de JOINs"""
        join_count = sql.upper().count(' JOIN ')
        
        if join_count > self.MAX_JOINS:
            self.validation_errors.append(
                f"Query muito complexa: {join_count} JOINs encontrados. "
                f"Máximo permitido: {self.MAX_JOINS}. "
                f"Considere usar views ou simplificar a consulta."
            )
            return False
        
        return True
    
    def _check_dangerous_patterns(self, sql: str) -> bool:
        """Verifica padrões perigosos"""
        dangerous_patterns = [
            (r'--', 'Comentários SQL (--) não são permitidos'),
            (r'/\*', 'Comentários em bloco (/* */) não são permitidos'),
            (r';.*\w', 'Múltiplos statements não são permitidos'),
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, sql):
                self.validation_errors.append(message)
                return False
        
        return True
    
    def add_limit_if_missing(self, sql: str) -> str:
        """Adiciona LIMIT se ausente"""
        if 'LIMIT' not in sql.upper():
            sql = sql.rstrip(';').rstrip()
            sql += f" LIMIT {self.DEFAULT_LIMIT}"
            logger.info(f"LIMIT {self.DEFAULT_LIMIT} adicionado automaticamente à query")
        
        return sql
    
    def get_validation_errors(self) -> List[str]:
        """Retorna lista de erros de validação"""
        return self.validation_errors


# Instância singleton
_validator = SQLValidator()


def validate_sql(sql: str) -> Tuple[bool, str]:
    """
    Função helper para validação rápida
    
    Usage:
        is_valid, error = validate_sql("SELECT * FROM vendas")
        if not is_valid:
            raise SQLValidationError(error)
    """
    return _validator.validate(sql)


def safe_add_limit(sql: str) -> str:
    """Adiciona LIMIT se ausente"""
    return _validator.add_limit_if_missing(sql)


def sanitize_query(sql: str) -> Tuple[bool, str, str]:
    """
    Valida e sanitiza query SQL
    
    Returns:
        (is_valid, error_or_ok, sanitized_sql)
    """
    is_valid, message = validate_sql(sql)
    if not is_valid:
        return False, message, sql
    
    sanitized = safe_add_limit(sql)
    return True, "OK", sanitized


# Testes se executado diretamente
if __name__ == "__main__":
    # Teste 1: Query válida
    sql1 = "SELECT * FROM vendas_diarias WHERE data >= '2026-01-01' LIMIT 100"
    is_valid, msg = validate_sql(sql1)
    print(f"Query 1: {'✅ VÁLIDA' if is_valid else '❌ INVÁLIDA'} - {msg}")
    
    # Teste 2: Query com DELETE (inválida)
    sql2 = "DELETE FROM vendas_diarias WHERE data < '2025-01-01'"
    is_valid, msg = validate_sql(sql2)
    print(f"Query 2: {'✅ VÁLIDA' if is_valid else '❌ INVÁLIDA'} - {msg}")
    
    # Teste 3: Query sem LIMIT
    sql3 = "SELECT * FROM produtos"
    is_valid, msg = validate_sql(sql3)
    sql3_safe = safe_add_limit(sql3)
    print(f"Query 3: {'✅ VÁLIDA' if is_valid else '❌ INVÁLIDA'}")
    print(f"Query segura: {sql3_safe}")
    
    # Teste 4: Query com muitos JOINs
    sql4 = """
        SELECT * FROM vendas_diarias v
        JOIN produtos p ON v.sku = p.sku
        JOIN estoque_atual e ON p.sku = e.sku
        JOIN transferencias t ON p.sku = t.sku
        JOIN lojas l ON v.loja_id = l.id
    """
    is_valid, msg = validate_sql(sql4)
    print(f"Query 4: {'✅ VÁLIDA' if is_valid else '❌ INVÁLIDA'} - {msg}")
