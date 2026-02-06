# 💻 CÓDIGO DE IMPLEMENTAÇÃO - BI SOLUTION

## PARTE 2: FEW-SHOT EXAMPLES (JSON)

### Arquivo: `backend/prompts/few_shot_examples.json`

```json
{
  "examples": [
    {
      "category": "vendas_analise",
      "user": "Quais categorias venderam mais no último mês?",
      "assistant_reasoning": "Usuário quer ranking de categorias por faturamento. Vou consultar vendas_diarias dos últimos 30 dias, fazer JOIN com produtos e agrupar por categoria.",
      "tool_calls": [
        {
          "tool": "query_duckdb",
          "sql": "SELECT p.categoria, SUM(v.valor_total) as faturamento, COUNT(DISTINCT v.sku) as mix_produtos, SUM(v.qtd_vendida) as volume FROM vendas_diarias v JOIN produtos p ON v.sku = p.sku WHERE v.data >= CURRENT_DATE - INTERVAL 30 DAY GROUP BY p.categoria ORDER BY faturamento DESC LIMIT 5"
        }
      ],
      "assistant_response": "Analisando vendas dos últimos 30 dias...\n\n📊 **TOP 5 CATEGORIAS (Últimos 30 dias)**\n\n| Categoria       | Faturamento | Mix SKUs | Volume  |\n|-----------------|-------------|----------|---------|\n| Papelaria       | R$ 1.247.890| 234      | 45.678  |\n| Tecidos         | R$ 892.450  | 156      | 12.345  |\n| Utilidades      | R$ 673.200  | 189      | 23.456  |\n| Brinquedos      | R$ 456.100  | 98       | 8.901   |\n| Eletrônicos     | R$ 321.800  | 67       | 4.567   |\n\n🟡 **INSIGHT:** Papelaria e Tecidos representam 58% do faturamento. Recomendo análise de ruptura prioritária nesses segmentos."
    },
    {
      "category": "ruptura_identificacao",
      "user": "Temos produtos em risco de ruptura?",
      "assistant_reasoning": "Usuário quer identificar produtos com baixa cobertura de estoque. Vou buscar SKUs com dias_cobertura < 7 e priorizar os mais críticos.",
      "tool_calls": [
        {
          "tool": "query_duckdb",
          "sql": "SELECT p.sku, p.descricao, p.categoria, e.loja_id, e.loja_qtd, e.dias_cobertura, e.cd_qtd FROM estoque_atual e JOIN produtos p ON e.sku = p.sku WHERE e.dias_cobertura < 7 AND e.loja_qtd > 0 ORDER BY e.dias_cobertura ASC LIMIT 10"
        }
      ],
      "assistant_response": "🔴 **ALERTA: 47 SKUs em Ruptura Iminente**\n\n**CRÍTICOS (< 3 dias) - AÇÃO IMEDIATA:**\n1. SKU 12345 - Caderno 200 Fls (Loja 5)\n   - Cobertura: 2.1 dias | Estoque: 120un | CD: 800un\n   - 💡 Transferir 280un HOJE\n\n2. SKU 67890 - Caneta Azul (Loja 3)\n   - Cobertura: 1.8 dias | Estoque: 45un | CD: 2.000un\n   - 💡 Transferir 500un HOJE"
    },
    {
      "category": "pareto_analise",
      "user": "Mostre a curva ABC de Papelaria",
      "assistant_reasoning": "Análise Pareto: preciso calcular receita acumulada de cada SKU e classificar em A/B/C. Vou ordenar por faturamento DESC e calcular percentuais.",
      "tool_calls": [
        {
          "tool": "query_duckdb",
          "sql": "WITH receitas AS (SELECT p.sku, p.descricao, SUM(v.valor_total) as receita FROM vendas_diarias v JOIN produtos p ON v.sku = p.sku WHERE p.segmento = 'Papelaria' AND v.data >= CURRENT_DATE - INTERVAL 90 DAY GROUP BY p.sku, p.descricao ORDER BY receita DESC) SELECT sku, descricao, receita, SUM(receita) OVER (ORDER BY receita DESC) / SUM(receita) OVER () as receita_acumulada_pct FROM receitas"
        }
      ],
      "assistant_response": "📈 **ANÁLISE PARETO - PAPELARIA (90 dias)**\n\n**Classe A (Top 20%):**\n- 47 SKUs gerando R$ 998K (80% do faturamento)\n- Principais: Cadernos Universitários, Canetas Gel, Agendas\n\n**Classe B (Próximos 30%):**\n- 70 SKUs gerando R$ 187K (15% do faturamento)\n\n🟡 **RECOMENDAÇÃO:** Garantir ZERO ruptura nos 47 SKUs Classe A"
    },
    {
      "category": "comparativo_temporal",
      "user": "Como foram as vendas de Janeiro comparado com Dezembro?",
      "assistant_reasoning": "Comparativo MoM (Month-over-Month). Vou calcular faturamento de Jan/2026 vs Dez/2025 e mostrar variação percentual.",
      "tool_calls": [
        {
          "tool": "query_duckdb",
          "sql": "WITH vendas_mes AS (SELECT DATE_TRUNC('month', data) as mes, SUM(valor_total) as faturamento FROM vendas_diarias WHERE data >= '2025-12-01' AND data < '2026-02-01' GROUP BY mes) SELECT mes, faturamento, LAG(faturamento) OVER (ORDER BY mes) as mes_anterior, ((faturamento - LAG(faturamento) OVER (ORDER BY mes)) / LAG(faturamento) OVER (ORDER BY mes) * 100) as variacao_pct FROM vendas_mes ORDER BY mes"
        }
      ],
      "assistant_response": "📊 **COMPARATIVO MoM: JAN/2026 vs DEZ/2025**\n\n| Mês     | Faturamento  | Variação  |\n|---------|--------------|----------|\n| Dez/25  | R$ 3.456.780 | -        |\n| Jan/26  | R$ 2.987.123 | -13.6%   |\n\n🔴 **ALERTA:** Queda de 13.6% típica pós-festas. Esperado para Janeiro."
    },
    {
      "category": "estoque_excessivo",
      "user": "Quais produtos estão com estoque parado há muito tempo?",
      "assistant_reasoning": "Estoque excessivo = dias_cobertura > 30. Vou calcular capital imobilizado e priorizar por valor.",
      "tool_calls": [
        {
          "tool": "query_duckdb",
          "sql": "SELECT p.sku, p.descricao, p.categoria, e.loja_qtd, e.dias_cobertura, (e.loja_qtd * p.preco_custo) as capital_imobilizado FROM estoque_atual e JOIN produtos p ON e.sku = p.sku WHERE e.dias_cobertura > 30 ORDER BY capital_imobilizado DESC LIMIT 10"
        }
      ],
      "assistant_response": "⚪ **ESTOQUE EXCESSIVO (> 30 dias)**\n\nTotal Imobilizado: R$ 234.567\n\n**Top 5 SKUs:**\n1. SKU 99999 - Brinquedo Colecionável: R$ 45K (67 dias)\n2. SKU 88888 - Tecido Importado: R$ 38K (52 dias)\n3. SKU 77777 - Eletrônico Descontinuado: R$ 29K (89 dias)\n\n💡 **AÇÃO:** Considerar promoção ou devolução ao fornecedor."
    },
    {
      "category": "transferencia_sugestao",
      "user": "Sugira transferências urgentes para a Loja 5",
      "assistant_reasoning": "Vou buscar SKUs na Loja 5 com cobertura crítica E estoque disponível no CD.",
      "tool_calls": [
        {
          "tool": "suggest_transfers",
          "parameters": {
            "loja_id": 5,
            "min_prioridade": "ALTA"
          }
        }
      ],
      "assistant_response": "🚚 **SUGESTÕES DE TRANSFERÊNCIA - LOJA 5**\n\n**URGENTE (Executar HOJE):**\n1. SKU 12345 - Caderno 200 Fls\n   - Transferir: 280un do CD\n   - Motivo: Cobertura 2.1 dias (CRÍTICO)\n\n2. SKU 67890 - Caneta Azul\n   - Transferir: 500un do CD\n   - Motivo: Cobertura 1.8 dias (CRÍTICO)\n\n✅ Total: 2 transferências salvando R$ 12.5K/semana em vendas perdidas."
    },
    {
      "category": "performance_loja",
      "user": "Qual loja está vendendo menos?",
      "assistant_reasoning": "Ranking de lojas por faturamento nos últimos 30 dias.",
      "tool_calls": [
        {
          "tool": "query_duckdb",
          "sql": "SELECT loja_id, SUM(valor_total) as faturamento, COUNT(DISTINCT sku) as mix_produtos FROM vendas_diarias WHERE data >= CURRENT_DATE - INTERVAL 30 DAY GROUP BY loja_id ORDER BY faturamento ASC LIMIT 5"
        }
      ],
      "assistant_response": "📉 **LOJAS COM MENOR FATURAMENTO (Últimos 30 dias)**\n\n| Loja | Faturamento | Mix SKUs |\n|------|-------------|----------|\n| 12   | R$ 123.456  | 89       |\n| 8    | R$ 145.678  | 102      |\n| 3    | R$ 167.890  | 115      |\n\n🔍 **INVESTIGAR:** Loja 12 com 40% abaixo da média. Possíveis causas: ruptura, localização, mix inadequado."
    },
    {
      "category": "top_produtos",
      "user": "Quais são os 10 produtos mais vendidos?",
      "assistant_reasoning": "Ranking de SKUs por volume de vendas (quantidade).",
      "tool_calls": [
        {
          "tool": "query_duckdb",
          "sql": "SELECT p.sku, p.descricao, p.categoria, SUM(v.qtd_vendida) as qtd_total, SUM(v.valor_total) as receita FROM vendas_diarias v JOIN produtos p ON v.sku = p.sku WHERE v.data >= CURRENT_DATE - INTERVAL 30 DAY GROUP BY p.sku, p.descricao, p.categoria ORDER BY qtd_total DESC LIMIT 10"
        }
      ],
      "assistant_response": "🏆 **TOP 10 PRODUTOS MAIS VENDIDOS (Volume)**\n\n| SKU   | Produto              | Categoria | Qtd    | Receita    |\n|-------|----------------------|-----------|--------|------------|\n| 12345 | Caderno 200 Fls      | Papelaria | 5.678  | R$ 147.2K  |\n| 67890 | Caneta Azul          | Papelaria | 4.901  | R$ 24.5K   |\n| 11111 | Lápis HB             | Papelaria | 4.234  | R$ 8.5K    |\n\n🟢 Papelaria domina: 7 dos 10 top produtos."
    }
  ]
}
```

---

## PARTE 3: SQL VALIDATOR (Python)

### Arquivo: `backend/utils/sql_validator.py`

```python
"""
Validador de SQL para segurança e performance
Previne SQL injection e queries perigosas
"""

import re
import sqlparse
from typing import Tuple, List
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DML


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
    DEFAULT_LIMIT = 10000
    
    def __init__(self):
        self.validation_errors = []
    
    def validate(self, sql: str) -> Tuple[bool, str]:
        """
        Valida query SQL
        
        Args:
            sql: String SQL para validar
            
        Returns:
            (is_valid, error_message)
        """
        self.validation_errors = []
        
        try:
            # 1. Check forbidden keywords
            if not self._check_forbidden_keywords(sql):
                return False, self.validation_errors[0]
            
            # 2. Parse SQL
            parsed = self._parse_sql(sql)
            if not parsed:
                return False, "SQL inválido ou malformado"
            
            # 3. Check statement type
            if not self._check_statement_type(parsed):
                return False, self.validation_errors[0]
            
            # 4. Check joins count
            if not self._check_joins_count(sql):
                return False, self.validation_errors[0]
            
            # 5. Check for LIMIT
            if not self._check_limit(sql):
                return False, self.validation_errors[0]
            
            # 6. Check dangerous patterns
            if not self._check_dangerous_patterns(sql):
                return False, self.validation_errors[0]
            
            return True, "OK"
            
        except Exception as e:
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
    
    def _parse_sql(self, sql: str) -> Statement:
        """Parse SQL usando sqlparse"""
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return None
            return parsed[0]
        except Exception:
            return None
    
    def _check_statement_type(self, statement: Statement) -> bool:
        """Verifica se é SELECT statement"""
        stmt_type = statement.get_type()
        
        if stmt_type != 'SELECT':
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
    
    def _check_limit(self, sql: str) -> bool:
        """Verifica presença de LIMIT ou adiciona warning"""
        if 'LIMIT' not in sql.upper():
            # Não é erro crítico, mas warning
            # A função execute_with_limit vai adicionar LIMIT automaticamente
            pass
        
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
            sql = sql.rstrip(';')  # Remove ; final se existir
            sql += f" LIMIT {self.DEFAULT_LIMIT}"
        
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


# Exemplos de uso
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
```

---

## PARTE 4: QUERY EXECUTOR COM TIMEOUT

### Arquivo: `backend/utils/query_executor.py`

```python
"""
Executor de queries com timeout e cache
"""

import time
import hashlib
import duckdb
import pandas as pd
from typing import Optional, Dict, Any
from functools import lru_cache
from .sql_validator import validate_sql, safe_add_limit, SQLValidationError


class QueryTimeoutError(Exception):
    """Exceção para timeout de query"""
    pass


class QueryExecutor:
    """Executor seguro de queries SQL"""
    
    def __init__(self, db_path: str, timeout_seconds: int = 30):
        self.db_path = db_path
        self.timeout_seconds = timeout_seconds
        self.conn = None
    
    def connect(self):
        """Estabelece conexão com DuckDB"""
        if not self.conn:
            self.conn = duckdb.connect(self.db_path, read_only=True)
    
    def execute(self, sql: str) -> Dict[str, Any]:
        """
        Executa query SQL com validação e timeout
        
        Args:
            sql: Query SQL
            
        Returns:
            dict com 'data', 'rows_count', 'execution_time_ms', 'warnings'
        """
        start_time = time.time()
        
        # 1. Validar SQL
        is_valid, error_msg = validate_sql(sql)
        if not is_valid:
            return {
                'error': error_msg,
                'error_type': 'validation',
                'execution_time_ms': 0
            }
        
        # 2. Adicionar LIMIT se ausente
        sql_safe = safe_add_limit(sql)
        
        # 3. Executar com timeout
        try:
            self.connect()
            
            # Set timeout no DuckDB
            self.conn.execute(f"SET lock_timeout = '{self.timeout_seconds}s'")
            
            # Executar query
            result = self.conn.execute(sql_safe).fetchdf()
            
            execution_time = (time.time() - start_time) * 1000  # ms
            
            # 4. Preparar resposta
            return {
                'data': result.to_dict('records'),
                'rows_count': len(result),
                'execution_time_ms': round(execution_time, 2),
                'warnings': self._generate_warnings(result, sql_safe),
                'sql_executed': sql_safe
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            # Classificar tipo de erro
            error_type = 'unknown'
            if 'timeout' in str(e).lower():
                error_type = 'timeout'
            elif 'syntax' in str(e).lower():
                error_type = 'syntax'
            
            return {
                'error': str(e),
                'error_type': error_type,
                'execution_time_ms': round(execution_time, 2),
                'sql_executed': sql_safe
            }
    
    def execute_with_cache(self, sql: str) -> Dict[str, Any]:
        """
        Executa query com cache
        
        Cache é baseado no hash MD5 do SQL normalizado
        """
        # Normalizar SQL (lowercase, strip)
        sql_normalized = sql.strip().lower()
        sql_hash = hashlib.md5(sql_normalized.encode()).hexdigest()
        
        # Tentar buscar no cache
        cached_result = self._get_from_cache(sql_hash)
        if cached_result:
            cached_result['from_cache'] = True
            return cached_result
        
        # Executar e cachear
        result = self.execute(sql)
        if 'error' not in result:
            self._save_to_cache(sql_hash, result)
        
        result['from_cache'] = False
        return result
    
    @lru_cache(maxsize=100)
    def _get_from_cache(self, sql_hash: str) -> Optional[Dict]:
        """Simula cache (usar Redis em produção)"""
        # Em produção, usar Redis ou Memcached
        return None
    
    def _save_to_cache(self, sql_hash: str, result: Dict):
        """Salva no cache (usar Redis em produção)"""
        # Em produção, implementar com Redis
        pass
    
    def _generate_warnings(self, df: pd.DataFrame, sql: str) -> list:
        """Gera warnings baseado nos resultados"""
        warnings = []
        
        # Warning 1: Resultado muito grande
        if len(df) >= 10000:
            warnings.append(
                "Resultado truncado em 10.000 linhas. "
                "Considere adicionar filtros mais específicos."
            )
        
        # Warning 2: Query lenta
        # (implementar baseado em execution_time)
        
        return warnings
    
    def close(self):
        """Fecha conexão"""
        if self.conn:
            self.conn.close()
            self.conn = None


# Instância global
_executor = None


def get_executor(db_path: str = 'data/parquet/cacula.db') -> QueryExecutor:
    """Factory function para obter executor"""
    global _executor
    if not _executor:
        _executor = QueryExecutor(db_path)
    return _executor


def execute_query(sql: str) -> Dict[str, Any]:
    """Helper function para execução rápida"""
    executor = get_executor()
    return executor.execute(sql)


# Exemplo de uso
if __name__ == "__main__":
    # Query de teste
    sql = """
        SELECT p.categoria, SUM(v.valor_total) as faturamento
        FROM vendas_diarias v
        JOIN produtos p ON v.sku = p.sku
        WHERE v.data >= '2026-01-01'
        GROUP BY p.categoria
        ORDER BY faturamento DESC
    """
    
    result = execute_query(sql)
    
    if 'error' in result:
        print(f"❌ Erro: {result['error']}")
    else:
        print(f"✅ Query executada em {result['execution_time_ms']}ms")
        print(f"📊 {result['rows_count']} linhas retornadas")
        if result['warnings']:
            print(f"⚠️ Warnings: {result['warnings']}")
```

---

## PARTE 5: GEMINI TOOLS CONFIGURATION

### Arquivo: `backend/tools/gemini_tools.py`

```python
"""
Configuração de tools/functions para Gemini Function Calling
"""

GEMINI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_duckdb",
            "description": """
Executa consulta SQL no banco de dados DuckDB das Lojas Caçula.

Use esta função para:
- Análises de vendas por categoria, produto, loja ou período
- Consultas de estoque (quantidade, cobertura, disponibilidade)
- Histórico de transferências entre CD e lojas
- Cálculos de KPIs (faturamento, giro, mix de produtos)

TABELAS DISPONÍVEIS:
- vendas_diarias: Histórico de vendas (data, sku, loja_id, qtd_vendida, valor_total)
- estoque_atual: Posição de estoque (sku, loja_id, loja_qtd, cd_qtd, dias_cobertura)
- produtos: Catálogo (sku, descricao, categoria, segmento, preco_venda)
- transferencias: Movimentações CD↔Lojas

VIEWS ÚTEIS:
- v_ruptura_iminente: Produtos com cobertura < 7 dias
- v_estoque_excessivo: Produtos com cobertura > 30 dias
- v_oportunidade_transferencia: CD tem estoque mas loja não

REGRAS:
- Sempre adicionar LIMIT para queries grandes
- Usar CURRENT_DATE para datas relativas
- Fazer JOIN com produtos para obter descrição/categoria
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "Query SQL válida. Apenas SELECT é permitido. Exemplo: SELECT categoria, SUM(valor_total) as receita FROM vendas_diarias v JOIN produtos p ON v.sku = p.sku WHERE data >= CURRENT_DATE - 30 GROUP BY categoria ORDER BY receita DESC LIMIT 10"
                    }
                },
                "required": ["sql"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_pareto_chart",
            "description": """
Gera gráfico de análise Pareto (Curva ABC) para classificação 80/20.

Use para:
- Identificar os 20% de SKUs que geram 80% da receita
- Priorizar produtos estratégicos (Classe A)
- Avaliar portfólio e descontinuação de produtos

A função retorna classificação automática em:
- Classe A: Top 20% (80% da receita)
- Classe B: Próximos 30% (15% da receita)
- Classe C: Demais 50% (5% da receita)
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "categoria": {
                        "type": "string",
                        "description": "Categoria ou segmento para análise. Exemplos: 'Papelaria', 'Tecidos', 'Brinquedos'. Deixe vazio para análise geral."
                    },
                    "periodo_dias": {
                        "type": "integer",
                        "description": "Período de análise em dias. Padrão: 90 dias.",
                        "default": 90
                    },
                    "metrica": {
                        "type": "string",
                        "enum": ["faturamento", "volume"],
                        "description": "Métrica para classificação: 'faturamento' (R$) ou 'volume' (quantidade)",
                        "default": "faturamento"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_transfers",
            "description": """
Gera sugestões inteligentes de transferência CD → Loja baseado em:
- Produtos com cobertura < 7 dias (risco de ruptura)
- Disponibilidade no CD
- Histórico de vendas
- Classificação ABC (prioriza Classe A e B)

Retorna lista priorizada com:
- SKU e descrição do produto
- Loja destino
- Quantidade sugerida (baseado em 14 dias de cobertura)
- Prioridade (CRÍTICA/ALTA/MÉDIA)
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "loja_id": {
                        "type": "integer",
                        "description": "ID da loja específica (1-15). Deixe vazio para todas as lojas."
                    },
                    "categoria": {
                        "type": "string",
                        "description": "Filtrar por categoria específica. Ex: 'Papelaria'"
                    },
                    "min_prioridade": {
                        "type": "string",
                        "enum": ["CRÍTICA", "ALTA", "MÉDIA"],
                        "description": "Prioridade mínima. Padrão: 'ALTA'",
                        "default": "ALTA"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Máximo de sugestões. Padrão: 20",
                        "default": 20
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_rupture_risk",
            "description": """
Análise completa de risco de ruptura por segmento ou categoria.

Retorna relatório com:
- Total de SKUs em risco (por nível de criticidade)
- Perda estimada de faturamento
- Top 10 produtos mais críticos
- Ações recomendadas prioritárias
- Distribuição por loja

Use quando o usuário perguntar sobre:
- "Risco de ruptura"
- "Produtos em falta"
- "Quais categorias estão críticas"
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "segmento": {
                        "type": "string",
                        "description": "Segmento para análise: 'Papelaria', 'Tecidos', 'Brinquedos', etc. Deixe vazio para análise geral."
                    },
                    "loja_id": {
                        "type": "integer",
                        "description": "Analisar loja específica. Deixe vazio para todas."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_kpis",
            "description": """
Calcula KPIs estratégicos do setor comercial:

- Taxa de Ruptura (%)
- Giro de Estoque
- Cobertura Média (dias)
- Capital Imobilizado (R$)
- Mix de Produtos Ativos
- Faturamento por Segmento

Período padrão: últimos 30 dias
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "periodo_dias": {
                        "type": "integer",
                        "description": "Período para cálculo. Padrão: 30 dias",
                        "default": 30
                    },
                    "segmento": {
                        "type": "string",
                        "description": "Filtrar por segmento específico"
                    }
                },
                "required": []
            }
        }
    }
]


def get_tools_for_gemini():
    """Retorna configuração de tools no formato Gemini"""
    return GEMINI_TOOLS
```

Continuo no próximo bloco...
