"""
Metrics Calculator - Motor de cálculo de métricas com DuckDB otimizado.

Arquitetura Metrics-First - Fase 4
Responsável por executar queries determinísticas e calcular métricas.

Princípios:
- SELECT apenas colunas necessárias (não SELECT *)
- WHERE sempre aplicado (predicate pushdown)
- Queries determinísticas e auditáveis
- Nenhuma lógica de negócio na LLM
"""

import logging
import time
import duckdb
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class MetricsResult:
    """
    Resultado do cálculo de métricas.
    
    Attributes:
        metrics: Métricas agregadas (total_vendas, avg_ticket, etc)
        dimensions: Dados dimensionais (por produto, segmento, etc)
        segments: Breakdown por segmento (NOVO)
        metadata: Metadados da query (filtros, período, etc)
        row_count: Número de linhas retornadas
        execution_time_ms: Tempo de execução em ms
        cache_hit: Se o resultado veio do cache
        query_sql: Query SQL executada (para debug)
    """
    metrics: Dict[str, float]
    dimensions: List[Dict[str, Any]] = field(default_factory=list)
    segments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    row_count: int = 0
    execution_time_ms: float = 0.0
    cache_hit: bool = False
    query_sql: str = ""


class MetricsCalculator:
    """
    Calculador de métricas usando DuckDB com otimizações.
    
    Otimizações aplicadas:
    - read_parquet() direto (não carregar tudo em memória)
    - SELECT apenas colunas necessárias
    - WHERE com predicate pushdown
    - Paralelização automática do DuckDB
    - Reutilização de conexão
    """
    
    def __init__(self, parquet_path: Optional[str] = None):
        """
        Args:
            parquet_path: Caminho para o arquivo parquet (opcional)
        """
        # Path para o parquet
        if parquet_path:
            self.parquet_path = Path(parquet_path)
        else:
            # Default: data/parquet/admmat.parquet
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            self.parquet_path = project_root / "data" / "parquet" / "admmat.parquet"
        
        if not self.parquet_path.exists():
            raise FileNotFoundError(f"Arquivo parquet não encontrado: {self.parquet_path}")
        
        # Conexão DuckDB (reutilizada)
        self.conn = duckdb.connect(database=':memory:')
        
        # Configurar DuckDB para performance
        self.conn.execute("SET threads TO 4;")  # Usar 4 threads
        self.conn.execute("SET memory_limit = '2GB';")
        
        logger.info(f"MetricsCalculator inicializado com parquet: {self.parquet_path}")
    
    def calculate(
        self,
        intent_type: str,
        entities: Dict[str, Any],
        aggregations: Optional[List[str]] = None,
        user_filters: Optional[Dict[str, Any]] = None
    ) -> MetricsResult:
        """
        Calcula métricas baseado na intenção e entidades.
        
        Args:
            intent_type: Tipo de intenção (vendas, estoque, etc)
            entities: Entidades extraídas (une, segmento, produto)
            aggregations: Agregações solicitadas (sum, avg, count)
            user_filters: Filtros adicionais do usuário (RLS, etc)
        
        Returns:
            MetricsResult com métricas calculadas
        """
        start_time = time.time()
        
        # Mesclar filtros
        filters = {**entities, **(user_filters or {})}
        
        # Selecionar query baseado na intenção
        if intent_type == "vendas":
            result = self._calculate_vendas(filters, aggregations)
        elif intent_type == "estoque":
            result = self._calculate_estoque(filters, aggregations)
        elif intent_type == "ruptura":
            result = self._calculate_ruptura(filters, aggregations)
        elif intent_type == "comparacao":
            result = self._calculate_comparacao(filters, aggregations)
        else:
            # Fallback: métricas gerais
            result = self._calculate_general(filters, aggregations)
        
        # Adicionar tempo de execução
        result.execution_time_ms = (time.time() - start_time) * 1000
        result.metadata["filters"] = filters
        result.metadata["intent_type"] = intent_type
        
        logger.info(
            f"Métricas calculadas: {result.row_count} linhas em {result.execution_time_ms:.2f}ms"
        )
        
        return result
    
    def _calculate_vendas(
        self,
        filters: Dict[str, Any],
        aggregations: Optional[List[str]]
    ) -> MetricsResult:
        """
        Calcula métricas de vendas.
        
        Métricas:
        - Total de vendas (soma)
        - Ticket médio
        - Quantidade de produtos
        - Top produtos por vendas
        """
        # Construir WHERE clause
        where_clauses = []
        params = {}
        
        if "une" in filters:
            where_clauses.append("UNE = $une")
            params["une"] = filters["une"]
        
        if "segmento" in filters:
            where_clauses.append("UPPER(NOMESEGMENTO) = UPPER($segmento)")
            params["segmento"] = filters["segmento"]
        
        if "produto" in filters:
            where_clauses.append("PRODUTO = $produto")
            params["produto"] = filters["produto"]
        
        # Sempre filtrar vendas > 0
        where_clauses.append("VENDA_30DD > 0")
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Query otimizada com predicate pushdown
        query = f"""
        WITH vendas_filtradas AS (
            SELECT
                PRODUTO,
                NOME as DESCRICAO,
                NOMESEGMENTO as SEGMENTO,
                UNE,
                TRY_CAST(VENDA_30DD AS DOUBLE) as VENDA_30DD,
                TRY_CAST(LIQUIDO_38 AS DOUBLE) as preco,
                TRY_CAST(ESTOQUE_UNE AS DOUBLE) as ESTOQUE_UNE
            FROM read_parquet('{self.parquet_path}')
            WHERE {where_clause}
        )
        SELECT
            -- Métricas agregadas
            SUM(TRY_CAST(VENDA_30DD AS DOUBLE)) as total_vendas,
            AVG(preco) as preco_medio,
            COUNT(DISTINCT PRODUTO) as qtd_produtos,
            COUNT(*) as qtd_registros,
            
            -- Top 10 produtos
            (
                SELECT LIST(
                    STRUCT_PACK(
                        produto := PRODUTO,
                        descricao := DESCRICAO,
                        vendas := VENDA_30DD,
                        preco := preco
                    )
                )
                FROM (
                    SELECT PRODUTO, DESCRICAO, VENDA_30DD, preco
                    FROM vendas_filtradas
                    ORDER BY VENDA_30DD DESC
                    LIMIT 10
                )
            ) as top_produtos,

            -- Top 5 Segmentos
            (
                SELECT LIST(
                    STRUCT_PACK(
                        segmento := SEGMENTO,
                        vendas := total_segmento
                    )
                )
                FROM (
                    SELECT SEGMENTO, SUM(VENDA_30DD) as total_segmento
                    FROM vendas_filtradas
                    GROUP BY SEGMENTO
                    ORDER BY total_segmento DESC
                    LIMIT 5
                )
            ) as top_segmentos
        FROM vendas_filtradas;
        """
        
        # Executar query
        try:
            result_df = self.conn.execute(query, params).df()
            
            if result_df.empty or result_df.iloc[0]['qtd_registros'] == 0:
                return MetricsResult(
                    metrics={},
                    dimensions=[],
                    segments=[],
                    row_count=0,
                    query_sql=query
                )
            
            row = result_df.iloc[0]
            
            # Extrair métricas
            metrics = {
                "total_vendas": float(row['total_vendas']) if row['total_vendas'] else 0.0,
                "preco_medio": float(row['preco_medio']) if row['preco_medio'] else 0.0,
                "qtd_produtos": int(row['qtd_produtos']) if row['qtd_produtos'] else 0,
            }
            
            # Extrair dimensões (top produtos)
            dimensions = []
            if row['top_produtos'] is not None and len(row['top_produtos']) > 0:
                for item in row['top_produtos']:
                    dimensions.append({
                        "produto": item['produto'],
                        "descricao": item['descricao'],
                        "vendas": float(item['vendas']),
                        "preco": float(item['preco'])
                    })

            # Extrair segmentos
            segments = []
            if row['top_segmentos'] is not None and len(row['top_segmentos']) > 0:
                for item in row['top_segmentos']:
                    segments.append({
                        "segmento": item['segmento'],
                        "vendas": float(item['vendas'])
                    })
            
            return MetricsResult(
                metrics=metrics,
                dimensions=dimensions,
                segments=segments,
                row_count=int(row['qtd_registros']),
                query_sql=query
            )
        
        except Exception as e:
            logger.error(f"Erro ao calcular vendas: {e}")
            logger.error(f"Query: {query}")
            raise
    
    def _calculate_estoque(
        self,
        filters: Dict[str, Any],
        aggregations: Optional[List[str]]
    ) -> MetricsResult:
        """Calcula métricas de estoque"""
        where_clauses = []
        params = {}
        
        if "une" in filters:
            where_clauses.append("UNE = $une")
            params["une"] = filters["une"]
        
        if "segmento" in filters:
            where_clauses.append("UPPER(NOMESEGMENTO) = UPPER($segmento)")
            params["segmento"] = filters["segmento"]
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
        SELECT
            SUM(TRY_CAST(ESTOQUE_UNE AS DOUBLE)) as total_estoque,
            AVG(TRY_CAST(ESTOQUE_UNE AS DOUBLE)) as estoque_medio,
            COUNT(DISTINCT PRODUTO) as qtd_produtos,
            COUNT(*) as qtd_registros
        FROM read_parquet('{self.parquet_path}')
        WHERE {where_clause};
        """
        
        try:
            result_df = self.conn.execute(query, params).df()
            
            if result_df.empty:
                return MetricsResult(metrics={}, row_count=0, query_sql=query)
            
            row = result_df.iloc[0]
            
            metrics = {
                "total_estoque": float(row['total_estoque']) if row['total_estoque'] else 0.0,
                "estoque_medio": float(row['estoque_medio']) if row['estoque_medio'] else 0.0,
                "qtd_produtos": int(row['qtd_produtos']) if row['qtd_produtos'] else 0,
            }
            
            return MetricsResult(
                metrics=metrics,
                row_count=int(row['qtd_registros']),
                query_sql=query
            )
        
        except Exception as e:
            logger.error(f"Erro ao calcular estoque: {e}")
            raise
    
    def _calculate_ruptura(
        self,
        filters: Dict[str, Any],
        aggregations: Optional[List[str]]
    ) -> MetricsResult:
        """
        Calcula métricas de ruptura usando regras do Guia UNE:
        - Gatilho Crítico: % ABAST <= 50%
        - Falha de Gatilho: % ABAST <= 50% sem disparo
        - Déficit de Parâmetro: MC > GONDOLA com TRAVA=SIM
        """
        # Filtro principal: % ABAST <= 50% (não apenas ESTOQUE = 0)
        where_clauses = [
            "TRY_CAST(ESTOQUE_LV AS DOUBLE) > 0",
            "(TRY_CAST(ESTOQUE_UNE AS DOUBLE) / TRY_CAST(ESTOQUE_LV AS DOUBLE)) <= 0.5"
        ]
        params = {}
        
        if "une" in filters:
            where_clauses.append("UNE = $une")
            params["une"] = filters["une"]
        
        if "segmento" in filters:
            where_clauses.append("UPPER(NOMESEGMENTO) = UPPER($segmento)")
            params["segmento"] = filters["segmento"]
        
        where_clause = " AND ".join(where_clauses)
        
        query = f"""
        SELECT
            COUNT(DISTINCT PRODUTO) as qtd_rupturas,
            COUNT(*) as qtd_registros,
            SUM(CASE WHEN COALESCE(TRY_CAST(SOLICITACAO_PENDENTE AS DOUBLE), 0) = 0 THEN 1 ELSE 0 END) as falhas_gatilho,
            SUM(CASE WHEN TRY_CAST(MEDIA_CONSIDERADA_LV AS DOUBLE) > TRY_CAST(ESTOQUE_GONDOLA_LV AS DOUBLE) 
                      AND UPPER(COALESCE(MEDIA_TRAVADA, '')) = 'SIM' THEN 1 ELSE 0 END) as deficit_parametro,
            LIST(STRUCT_PACK(
                produto := PRODUTO,
                descricao := NOME,
                segmento := NOMESEGMENTO,
                fornecedor := NOMEFABRICANTE,
                estoque_une := TRY_CAST(ESTOQUE_UNE AS DOUBLE),
                linha_verde := TRY_CAST(ESTOQUE_LV AS DOUBLE),
                perc_abast := ROUND(TRY_CAST(ESTOQUE_UNE AS DOUBLE) / TRY_CAST(ESTOQUE_LV AS DOUBLE) * 100, 2),
                necessidade := TRY_CAST(ESTOQUE_LV AS DOUBLE) - TRY_CAST(ESTOQUE_UNE AS DOUBLE)
            )) as produtos_ruptura
        FROM read_parquet('{self.parquet_path}')
        WHERE {where_clause}
        LIMIT 50;
        """
        
        try:
            result_df = self.conn.execute(query, params).df()
            
            if result_df.empty:
                return MetricsResult(metrics={}, row_count=0, query_sql=query)
            
            row = result_df.iloc[0]
            
            metrics = {
                "qtd_rupturas": int(row['qtd_rupturas']) if row['qtd_rupturas'] else 0,
                "falhas_gatilho": int(row['falhas_gatilho']) if row['falhas_gatilho'] else 0,
                "deficit_parametro": int(row['deficit_parametro']) if row['deficit_parametro'] else 0,
            }
            
            dimensions = []
            if row['produtos_ruptura'] is not None and len(row['produtos_ruptura']) > 0:
                for item in row['produtos_ruptura'][:20]:  # Limitar a 20
                    dimensions.append({
                        "produto": item['produto'],
                        "descricao": item['descricao'],
                        "segmento": item['segmento'],
                        "fornecedor": item['fornecedor'],
                        "estoque_une": float(item['estoque_une']) if item['estoque_une'] else 0,
                        "linha_verde": float(item['linha_verde']) if item['linha_verde'] else 0,
                        "perc_abast": float(item['perc_abast']) if item['perc_abast'] else 0,
                        "necessidade": float(item['necessidade']) if item['necessidade'] else 0,
                    })
            
            return MetricsResult(
                metrics=metrics,
                dimensions=dimensions,
                row_count=int(row['qtd_registros']),
                query_sql=query
            )
        
        except Exception as e:
            logger.error(f"Erro ao calcular rupturas: {e}")
            raise
    
    def _calculate_comparacao(
        self,
        filters: Dict[str, Any],
        aggregations: Optional[List[str]]
    ) -> MetricsResult:
        """Calcula métricas para comparação (múltiplas UNEs)"""
        if "unes" not in filters or len(filters["unes"]) < 2:
            # Fallback para vendas simples
            return self._calculate_vendas(filters, aggregations)
        
        unes = filters["unes"]
        unes_str = ", ".join(str(u) for u in unes)
        
        query = f"""
        SELECT
            UNE,
            SUM(TRY_CAST(VENDA_30DD AS DOUBLE)) as total_vendas,
            COUNT(DISTINCT PRODUTO) as qtd_produtos
        FROM read_parquet('{self.parquet_path}')
        WHERE UNE IN ({unes_str}) AND VENDA_30DD > 0
        GROUP BY UNE
        ORDER BY total_vendas DESC;
        """
        
        try:
            result_df = self.conn.execute(query).df()
            
            if result_df.empty:
                return MetricsResult(metrics={}, row_count=0, query_sql=query)
            
            # Métricas agregadas
            metrics = {
                "total_vendas": float(result_df['total_vendas'].sum()),
                "qtd_lojas": len(result_df),
            }
            
            # Dimensões (por loja)
            dimensions = result_df.to_dict('records')
            
            return MetricsResult(
                metrics=metrics,
                dimensions=dimensions,
                row_count=len(result_df),
                query_sql=query
            )
        
        except Exception as e:
            logger.error(f"Erro ao calcular comparação: {e}")
            raise
    
    def _calculate_general(
        self,
        filters: Dict[str, Any],
        aggregations: Optional[List[str]]
    ) -> MetricsResult:
        """Métricas gerais (fallback)"""
        return self._calculate_vendas(filters, aggregations)
    
    def close(self):
        """Fecha a conexão DuckDB"""
        if self.conn:
            self.conn.close()
            logger.info("Conexão DuckDB fechada")
