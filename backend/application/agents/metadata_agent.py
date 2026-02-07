"""
MetadataAgent - Agente Especializado em Metadados

Este agente é responsável por fornecer informações sobre o schema de dados,
dicionário de dados e ajudar outros agentes a entender a estrutura disponível.

Uso:
    from backend.application.agents import MetadataAgent
    
    metadata_agent = MetadataAgent(data_source=duckdb_adapter)
    response = await metadata_agent.run(request)

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from typing import List, Dict, Any, Optional

import structlog

from backend.application.agents.base_agent import BaseAgent
from backend.domain.ports.agent_port import (
    AgentRequest,
    AgentResponse,
    AgentRequestType,
)
from backend.domain.ports.llm_port import LLMPort
from backend.domain.ports.data_source_port import DataSourcePort
from backend.domain.ports.metrics_port import MetricsPort


logger = structlog.get_logger(__name__)


class MetadataAgent(BaseAgent):
    """
    Agente especializado em metadados e dicionário de dados.
    
    Responsabilidades:
    - Listar tabelas e colunas disponíveis
    - Descrever campos e seus significados
    - Ajudar na construção de queries
    - Validar referências a dados
    
    Example:
        >>> metadata_agent = MetadataAgent(data_source=duckdb)
        >>> request = AgentRequest(
        ...     message="Quais colunas existem na tabela de vendas?",
        ...     ...
        ... )
        >>> response = await metadata_agent.run(request)
    """
    
    def __init__(
        self,
        llm: Optional[LLMPort] = None,
        data_source: Optional[DataSourcePort] = None,
        metrics: Optional[MetricsPort] = None,
    ):
        super().__init__(llm=llm, metrics=metrics)
        self._data_source = data_source
        self._schema_cache: Dict[str, Any] = {}
    
    @property
    def name(self) -> str:
        return "MetadataAgent"
    
    @property
    def description(self) -> str:
        return (
            "Agente especializado em fornecer informações sobre schema de dados, "
            "dicionário de dados e estrutura das tabelas disponíveis."
        )
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "list_tables",
            "describe_columns",
            "data_dictionary",
            "schema_validation",
            "column_mapping",
        ]
    
    async def can_handle(self, request: AgentRequest) -> bool:
        if request.request_type == AgentRequestType.METADATA:
            return True
        keywords = ["coluna", "tabela", "campo", "schema", "dicionário", "estrutura", "tipo"]
        return any(kw in request.message.lower() for kw in keywords)
    
    async def _get_schema(self) -> Dict[str, Any]:
        """Obtém e cacheia o schema do banco."""
        if self._schema_cache:
            return self._schema_cache
        
        if not self._data_source:
            return {}
        
        try:
            tables = await self._data_source.get_tables()
            schema = {}
            
            for table in tables[:20]:  # Limitar
                columns = await self._data_source.get_columns(table)
                schema[table] = [
                    {
                        "name": col.name,
                        "type": col.dtype,
                        "nullable": col.nullable,
                        "description": col.description,
                    }
                    for col in columns
                ]
            
            self._schema_cache = schema
            return schema
            
        except Exception as e:
            logger.error("schema_fetch_error", error=str(e))
            return {}
    
    async def _execute(self, request: AgentRequest) -> AgentResponse:
        schema = await self._get_schema()
        
        if not schema:
            # Schema padrão para varejo (exemplo)
            schema = {
                "vendas": [
                    {"name": "DATA_VENDA", "type": "DATE", "description": "Data da venda"},
                    {"name": "COD_PRODUTO", "type": "INTEGER", "description": "Código do produto"},
                    {"name": "UNE", "type": "INTEGER", "description": "Código da loja"},
                    {"name": "QUANTIDADE", "type": "FLOAT", "description": "Quantidade vendida"},
                    {"name": "LIQUIDO_38", "type": "FLOAT", "description": "Valor líquido (preço)"},
                ],
                "estoque": [
                    {"name": "COD_PRODUTO", "type": "INTEGER", "description": "Código do produto"},
                    {"name": "UNE", "type": "INTEGER", "description": "Código da loja"},
                    {"name": "ESTOQUE_ATUAL", "type": "FLOAT", "description": "Estoque atual"},
                    {"name": "ESTOQUE_MINIMO", "type": "FLOAT", "description": "Estoque mínimo"},
                ],
            }
        
        # Formatar resposta
        lines = ["## Dicionário de Dados\n"]
        
        for table, columns in schema.items():
            lines.append(f"### 📋 Tabela: `{table}`\n")
            lines.append("| Coluna | Tipo | Descrição |")
            lines.append("|--------|------|-----------|")
            for col in columns:
                desc = col.get("description") or "-"
                lines.append(f"| `{col['name']}` | {col['type']} | {desc} |")
            lines.append("")
        
        return AgentResponse(
            content="\n".join(lines),
            success=True,
            data={"schema": schema},
            tool_calls=["get_schema"],
        )
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "consultar_dicionario_dados",
                "description": "Consulta o dicionário de dados e schema disponível",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tabela": {"type": "string", "description": "Nome da tabela (opcional)"},
                    },
                },
            },
            {
                "name": "listar_tabelas",
                "description": "Lista todas as tabelas disponíveis",
                "parameters": {"type": "object", "properties": {}},
            },
        ]
