import json
import logging
import asyncio
import numpy as np
import pandas as pd
from decimal import Decimal
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Callable, Awaitable

logger = logging.getLogger(__name__)

# Safe Import for LangChain dependencies
LANGCHAIN_AVAILABLE = False
try:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.tools import BaseTool
    LANGCHAIN_AVAILABLE = True
except (ImportError, OSError):
    logger.warning("LangChain dependencies missing. CaculinhaBIAgent will run in degraded mode.")
    BaseChatModel = object # Dummy for type hinting
    BaseTool = object # Dummy for type hinting

from backend.app.core.tools.une_tools import (
    calcular_abastecimento_une,
    calcular_mc_produto,
    calcular_preco_final_une,
    validar_transferencia_produto,
    sugerir_transferencias_automaticas,
    encontrar_rupturas_criticas,
    consultar_dados_gerais,
    analisar_produto_todas_lojas,  # [OK] FIX 2026-01-15: Análise multi-loja sem loop
)
# Safe Import of Core Tools (LangChain dependency risk)
try:
    from backend.app.core.tools.flexible_query_tool import consultar_dados_flexivel
except (ImportError, OSError):
    logger.warning("Flexible Query Tool missing (LangChain/DLL issue). Agent running in degraded mode.")
    consultar_dados_flexivel = None

# from app.core.tools.anomaly_detection import analisar_anomalias # NOVA FERRAMENTA (Warning: Possible DL Dep)
from backend.app.core.tools.metadata_tools import consultar_dicionario_dados, analisar_historico_vendas  # Ferramentas de metadados e previsão

# [OK] NEW 2026-01-22: Purchasing Tools - Advanced Calculations
# WRAPPED IN SAFE IMPORT BELOW
# from app.core.tools.purchasing_tools import (
#     calcular_eoq,
#     prever_demanda_sazonal,
#     alocar_estoque_lojas
# )

from backend.app.core.data_source_manager import get_data_manager # Para injeção dinâmica

# Import NEW universal chart tool - Context7 2025 Best Practice
from backend.app.core.tools.universal_chart_generator import gerar_grafico_universal_v2
from backend.app.core.tools.test_minimal import teste_minimal  # DEBUG: Ferramenta mínima para teste

# Import legacy chart tools for compatibility
from backend.app.core.tools.chart_tools import (
    gerar_ranking_produtos_mais_vendidos,
    gerar_dashboard_executivo,
    listar_graficos_disponiveis,
    gerar_visualizacao_customizada
)

# Import NEW semantic search tool - RAG Implementation 2025
# MOVED TO __INIT__ FOR SAFETY
# from app.core.tools.semantic_search_tool import buscar_produtos_inteligente

# NEW 2026-02-07: Deep Catalog Search (Hybrid BM25 + Vector)
try:
    from backend.app.core.tools.catalog_search_tool import create_catalog_search_tool
    from backend.application.services.product_search_service import ProductSearchService
    from backend.infrastructure.adapters.search.whoosh_bm25_index_adapter import WhooshBM25IndexAdapter
    from backend.infrastructure.adapters.search.vector_index_adapter import VectorIndexAdapter
    from backend.infrastructure.adapters.search.hybrid_ranking_adapter import HybridRankingAdapter
    from backend.infrastructure.adapters.repository.duckdb_catalog_repository import DuckDBCatalogRepository
    CATALOG_SEARCH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Catalog Search dependencies missing: {e}")
    CATALOG_SEARCH_AVAILABLE = False

# Import RAG Hybrid Retriever - Query Example Retrieval 2025
from backend.app.core.rag.hybrid_retriever import HybridRetriever

# Optional: Import CodeGenAgent just for type hinting if needed,
# but we won't use it for logic anymore.
from backend.app.core.utils.field_mapper import FieldMapper

# Import TypeConverter para serialização segura
from backend.app.core.utils.serializers import TypeConverter, safe_json_dumps
from backend.app.config.settings import settings

# Import Tool Scoping - Security 2025
from backend.app.core.utils.tool_scoping import ToolPermissionManager, get_scoped_tools

# Alias para manter compatibilidade com código existente
safe_json_serialize = safe_json_dumps

# System instruction - Master Prompt: Assistente de BI Analítico Avançado
# DEPRECATED: Este arquivo faz parte da arquitetura V2 (removida)
# O SYSTEM_PROMPT agora está centralizado em app.core.prompts.master_prompt
# Este agente está deprecated. Use ChatServiceV3 para novas implementações.
from backend.app.core.prompts.master_prompt import MASTER_PROMPT as SYSTEM_PROMPT

class CaculinhaBIAgent:
    """
    Agent responsible for Business Intelligence queries using Gemini Native Function Calling.
    Replaces the legacy keyword-based routing and CodeGenAgent fallback.
    """
    def __init__(
        self,
        llm: Any,
        code_gen_agent: Any,
        field_mapper: FieldMapper,
        user_role: str = "analyst",  # NEW: Role-based tool scoping (default: analyst)
        enable_rag: bool = True  # ASYNC RAG 2025-12-27: Re-enabled with background warming (non-blocking)
    ):
        # llm is expected to be GeminiLLMAdapter
        self.llm = llm
        self.field_mapper = field_mapper
        self.user_role = user_role  # Store user role for tool scoping
        self.enable_rag = enable_rag  # Store RAG config
        
        # Initialize early to prevent AttributeError in tool construction
        self.retriever = None 
        self.buscar_produtos_inteligente = None # Placeholder if needed by logic

        # [OK] REACTIVATED 2026-01-22: CodeGenAgent now actively used for complex calculations

        # [OK] REACTIVATED 2026-01-22: CodeGenAgent now actively used for complex calculations
        # (EOQ, forecasting, seasonal adjustments)
        self.code_gen_agent = code_gen_agent

        # Initialize RAG Retriever (lazy - background warming, não bloqueia)
        if self.enable_rag:
            try:
                self.retriever = HybridRetriever()
                logger.info("RAG Hybrid Retriever criado (warming será iniciado em background)")
                # NOTE: Warming será iniciado no primeiro run_async() via _start_rag_warming()
            except Exception as e:
                logger.warning(f"Falha ao criar RAG retriever: {e}. Continuando sem RAG.")
                self.retriever = None
                self.enable_rag = False
        else:
            self.retriever = None
            logger.info("RAG desabilitado (enable_rag=False)")

        # Define CORE tools (always available)
        # FIX DEFINITIVO: Gemini tem limite RÍGIDO de complexidade
        # Mantendo apenas 4 ferramentas CRÍTICAS
        core_tools = [
            consultar_dados_flexivel,  # Consulta genérica
            gerar_grafico_universal_v2,  # Visualização
            calcular_abastecimento_une,  # Abastecimento
            encontrar_rupturas_criticas,  # Rupturas
            consultar_dicionario_dados,  # FIX 2026-02-04: Restaurado para schema discovery
            analisar_produto_todas_lojas,  # FIX 2026-02-04: Restaurado para análise multi-loja
        ]
        
        # [OK] NEW 2026-02-07: Integration of Deep Catalog Search
        if CATALOG_SEARCH_AVAILABLE:
            try:
                # Initialize Search Infrastructure
                db_path = "backend/data/product_catalog.duckdb"
                index_dir = "backend/data/whoosh_index"
                
                repo = DuckDBCatalogRepository(db_path)
                bm25 = WhooshBM25IndexAdapter(index_dir)
                vec = VectorIndexAdapter(db_path)
                ranker = HybridRankingAdapter(repo)
                
                search_service = ProductSearchService(bm25, vec, ranker, repo)
                catalog_search_tool = create_catalog_search_tool(search_service)
                core_tools.append(catalog_search_tool)
                logger.info("[OK] Deep Catalog Search tool registered successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Catalog Search tool: {e}")
        
        # FIX 2026-02-04: Ferramentas restauradas para melhorar capacidade do agente
        
        # Remove None tools (failed imports)
        core_tools = [t for t in core_tools if t is not None]

        # Dynamically add OPTIONAL tools (ML/Deep Learning dependencies)
        optional_tools = []
        if settings.DEV_FAST_MODE:
            logger.info("[DEV_FAST_MODE] Optional expensive tools disabled by default.")
        else:
        
        # 1. Anomaly Detection (SciPy/Stats dependency)
            try:
                from backend.app.core.tools.anomaly_detection import analisar_anomalias
                optional_tools.append(analisar_anomalias)
            except ImportError:
                logger.warning("[WARNING] Anomaly Detection tools missing (dependency issue).")

        # 2. Purchasing Tools (StatsModels/Torch dependency)
            try:
                from backend.app.core.tools.purchasing_tools import (
                    calcular_eoq,
                    prever_demanda,
                    alocar_estoque_lojas
                )
                optional_tools.extend([calcular_eoq, prever_demanda, alocar_estoque_lojas])
            except ImportError:
                logger.warning("[WARNING] Purchasing tools missing (likely StatsModels/Torch issue).")

        # 3. Advanced Analytics Tools (SciPy/Sklearn dependency) - NOVO 2026-01-24
        # Ferramentas STEM para Gemini 2.5 Pro: regressão, anomalias, correlação
            try:
                from backend.app.core.tools.advanced_analytics_tool import (
                    analise_regressao_vendas,
                    detectar_anomalias_vendas,
                    analise_correlacao_produtos
                )
                optional_tools.extend([
                    analise_regressao_vendas,
                    detectar_anomalias_vendas,
                    analise_correlacao_produtos
                ])
                logger.info("[OK] Advanced Analytics tools loaded (Gemini 2.5 Pro STEM features)")
            except ImportError as e:
                logger.warning(f"[WARNING] Advanced Analytics tools missing (SciPy/Sklearn issue): {e}")

        # 4. RAG Tools (LangChain/FAISS/Torch dependency)
        # Already handled via self.buscar_produtos_inteligente logic in _register_retriever_tools
        # But for 'all_bi_tools' list used for scoping, we add it if enabled
        if self.enable_rag and self.buscar_produtos_inteligente and not settings.DEV_FAST_MODE:
             optional_tools.append(self.buscar_produtos_inteligente)

        all_bi_tools = core_tools + optional_tools

        # Apply role-based tool scoping (Security 2025)
        self.bi_tools = ToolPermissionManager.get_tools_for_role(
            all_tools=all_bi_tools,
            user_role=self.user_role
        )

        logger.info(
            f"Agent initialized with {len(self.bi_tools)}/{len(all_bi_tools)} tools "
            f"for role '{self.user_role}'"
        )

        # Convert LangChain tools to Gemini Function Declarations
        self.gemini_tools = self._convert_tools_to_gemini_format(self.bi_tools)
        
        # System instruction - Conversacional + BI Expert (Context7 Enhanced v2025)
        # DYNAMIC PROMPTING: Injetar schema real na inicialização
        try:
            manager = get_data_manager()
            # Tentar obter colunas (cache hit provável)
            cols = manager.get_columns()
            
            # Filtrar colunas importantes (evitar poluir com as 100)
            # Mas garantir que as críticas estejam lá
            important_keywords = ['PRODUTO', 'NOME', 'UNE', 'SEGMENTO', 'CATEGORIA', 'VENDA', 'ESTOQUE', 'PRECO', 'CUSTO', 'LIQUIDO', 'MARGEM', 'FABRICANTE']
            priority_cols = [c for c in cols if any(k in c.upper() for k in important_keywords)]
            other_cols = [c for c in cols if c not in priority_cols]
            
            # Montar string de schema com instruções claras para o LLM
            schema_str = f"""Você tem acesso a um banco de dados Parquet com **{len(cols)} colunas**.

**[DATA] COLUNAS PRIORITÁRIAS ({len(priority_cols)} colunas):**
Use estas colunas preferencialmente para análises. Elas cobrem os principais casos de uso:
{", ".join([f"`{c}`" for c in priority_cols])}

**📁 OUTRAS COLUNAS DISPONÍVEIS ({len(other_cols)} colunas):**
{", ".join([f"`{c}`" for c in other_cols[:30]])}
{f"... (+{len(other_cols)-30} colunas adicionais)" if len(other_cols) > 30 else ""}

**[WARNING] IMPORTANTE:**
- Se precisar de TODAS as colunas ou descrições detalhadas, use a ferramenta `consultar_dicionario_dados()`.
- NUNCA invente nomes de colunas. Use APENAS as listadas acima.
- Para histórico de vendas, use: `MES_01` a `MES_12` (vendas mensais) ou `VENDA_30DD` (últimos 30 dias).
- Para preços: `LIQUIDO_38` (preço de venda) e `ULTIMA_ENTRADA_CUSTO_CD` (custo).
"""
                
            # Substituir no template usando o novo placeholder
            if "[SCHEMA_INJECTION_POINT]" in SYSTEM_PROMPT:
                self.system_prompt = SYSTEM_PROMPT.replace(
                    "[SCHEMA_INJECTION_POINT]", 
                    schema_str
                )
                logger.info(f"[OK] Dynamic Schema Injection: Sucesso ({len(cols)} colunas injetadas)")
            else:
                # Fallback: se o placeholder não existir, anexar ao final
                logger.warning("[WARNING] Placeholder [SCHEMA_INJECTION_POINT] não encontrado. Anexando schema ao final do prompt.")
                self.system_prompt = SYSTEM_PROMPT + "\n\n## 🗄️ DADOS DISPONÍVEIS\n" + schema_str
            
        except Exception as e:
            logger.warning(f"[ERROR] Dynamic Schema Injection Failed: {e}. Using static prompt.")
            self.system_prompt = SYSTEM_PROMPT

        if settings.DEV_FAST_MODE:
            self.system_prompt += (
                "\n\n## MODO DEV FAST\n"
                "- Responda objetivamente em no máximo 8 linhas.\n"
                "- Evite chamadas de ferramenta caras, a menos que sejam estritamente necessárias.\n"
            )


    def _convert_tools_to_gemini_format(self, tools: List[BaseTool]) -> Dict[str, List[Dict[str, Any]]]:
        declarations = []
        for tool in tools:
            # Generate schema using LangChain's standardized method
            # compatible with Pydantic v1 and v2
            try:
                schema = tool.get_input_schema().model_json_schema()
            except AttributeError:
                # Fallback for older Pydantic or specific Tool implementations
                if hasattr(tool, 'args_schema') and tool.args_schema:
                    if hasattr(tool.args_schema, 'schema'):
                         schema = tool.args_schema.schema()
                    else:
                         schema = {}
                else:
                    schema = {}
            
            # Clean schema to be compatible with Gemini (remove anyOf, titles)
            cleaned_schema = self._clean_schema(schema)
            
            # Ensure 'properties' and 'required' are present if parameters exist
            parameters = {
                "type": "object",
                "properties": cleaned_schema.get("properties", {}),
                "required": cleaned_schema.get("required", [])
            }

            declarations.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": parameters
            })
        
        return {"function_declarations": declarations}

    def _clean_context7_violations(self, content: str, context_type: str = "generic") -> str:
        """
        Remove JSON bruto e estruturas técnicas das respostas (Context7 Storytelling).

        Args:
            content: Conteúdo a limpar
            context_type: Tipo de contexto ("chart", "data", "analysis", "generic")

        Returns:
            Conteúdo limpo com narrativa natural
        """
        if not isinstance(content, str) or not content:
            return content

        import re

        original_content = content
        cleaned = content

        # 1. Detectar e remover markdown JSON blocks (```json...```)
        markdown_json_pattern = r'```json\s*\n(.*?)\n```'
        if re.search(markdown_json_pattern, cleaned, re.DOTALL):
            logger.warning("[CONTEXT7] Detectado markdown JSON block. Removendo.")
            cleaned = re.sub(markdown_json_pattern, "", cleaned, flags=re.DOTALL)

        # 2. Detectar e remover blocos JSON inline grandes (chart specs, etc)
        # Padrão para detectar objetos JSON com "data" e "layout" (Plotly)
        plotly_json_pattern = r'\{[\s\S]*?"data"[\s\S]*?"layout"[\s\S]*?\}'
        if re.search(plotly_json_pattern, cleaned):
            logger.warning("[CONTEXT7] Detectado Plotly JSON inline. Removendo.")
            cleaned = re.sub(plotly_json_pattern, "", cleaned)

        # 3. Detectar JSON puro no início (objeto ou array)
        stripped = cleaned.strip()
        if (stripped.startswith("{") or stripped.startswith("[")) and len(stripped) > 50:
            # Tentar validar se é JSON
            try:
                json.loads(stripped)
                logger.warning("[CONTEXT7] Detectado JSON puro. Substituindo com narrativa.")
                cleaned = ""  # Limpar completamente, será substituído abaixo
            except json.JSONDecodeError:
                pass  # Não é JSON válido, manter

        # 4. Se ficou vazio ou muito curto, substituir com narrativa contextual
        cleaned = cleaned.strip()
        if not cleaned or len(cleaned) < 10:
            if context_type == "chart":
                cleaned = "Aqui está o gráfico que você solicitou."
            elif context_type == "data":
                cleaned = "Recuperei os dados solicitados e organizei para você."
            elif context_type == "analysis":
                cleaned = "Com base nos dados disponíveis, aqui está a análise:"
            else:
                cleaned = "Processado com sucesso."

            logger.info(f"[CONTEXT7] Substituído com narrativa contextual ({context_type})")

        # 5. Se mudou, logar a transformação
        if cleaned != original_content:
            logger.info(f"[CONTEXT7] Limpeza aplicada. Antes: {len(original_content)} chars, Depois: {len(cleaned)} chars")

        return cleaned

    async def _start_rag_warming(self) -> None:
        """
        Inicia warming do RAG em background (non-blocking).
        Chamado apenas uma vez no primeiro run_async().
        """
        if not self.enable_rag or self.retriever is None:
            return

        try:
            # Start warming in background (fire and forget)
            asyncio.create_task(self.retriever.start_background_warming())
            logger.info("[RAG] Background warming task criado")
        except Exception as e:
            logger.error(f"[RAG] Erro ao iniciar warming: {e}", exc_info=True)

    async def _get_rag_examples(self, query: str, top_k: int = 3) -> str:
        """
        Recupera exemplos similares e formata como BLOCO DE CONTEXTO SEGURO.
        Muda de 'lista de mensagens' para 'string formatada com instruções'.
        
        Returns:
            String formatada com XML tags <reference_context>
        """
        if not self.enable_rag or self.retriever is None:
            return ""

        try:
            # Use async retrieve
            similar_docs = await self.retriever.retrieve_async(
                query,
                top_k=top_k,
                method='hybrid',
                wait_if_warming=False
            )

            if not similar_docs:
                return ""

            logger.info(f"[RAG] Recuperados {len(similar_docs)} exemplos para contexto")

            # Formata como bloco de texto instrucional
            context_block = "\n\n<reference_context>\n"
            context_block += "[WARNING] EXEMPLOS DE INTERAÇÕES PASSADAS (PARA APRENDER A LÓGICA):\n"
            context_block += "INSTRUÇÃO CRÍTICA: Use estes exemplos APENAS para entender qual ferramenta chamar ou como formatar a resposta.\n"
            context_block += "PROIBIDO: Não copie números, IDs ou nomes destes exemplos. Os dados abaixo são OBSOLETOS.\n\n"

            for i, doc in enumerate(similar_docs[:top_k]):
                doc_data = doc.get('doc', doc)
                user_q = doc_data.get('query', doc_data.get('user_query', ''))
                assist_r = doc_data.get('response', doc_data.get('assistant_response', ''))
                
                # Truncar resposta se for muito longa para economizar tokens e reduzir ruído
                # FIX 2026-01-27: Aumentado de 500 para 2000 chars (respostas mais completas)
                if len(assist_r) > 2000:
                    assist_r = assist_r[:2000] + "... (truncado)"

                context_block += f"--- EXEMPLO {i+1} ---\n"
                context_block += f"Pergunta: {user_q}\n"
                context_block += f"Ação Correta: {assist_r}\n"

            context_block += "</reference_context>\n"
            return context_block

        except Exception as e:
            logger.error(f"[RAG] Erro ao recuperar exemplos: {e}", exc_info=True)
            return ""

    def _clean_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively cleans Pydantic JSON Schema for Gemini compatibility.
        """
        if not isinstance(schema, dict):
            return schema
            
        new_schema = schema.copy()
        
        # Remove incompatible keys
        if "title" in new_schema:
            del new_schema["title"]
        if "default" in new_schema:
            del new_schema["default"]
        if "additionalProperties" in new_schema:
            del new_schema["additionalProperties"]

        # Handle anyOf
        if "anyOf" in new_schema:
            options = new_schema.pop("anyOf")
            valid_option = next((opt for opt in options if opt.get("type") != "null"), None)
            if valid_option:
                cleaned_child = self._clean_schema(valid_option)
                new_schema.update(cleaned_child)
            else:
                new_schema["type"] = "string" 

        # Recurse
        if "properties" in new_schema:
            for prop, prop_schema in new_schema["properties"].items():
                new_schema["properties"][prop] = self._clean_schema(prop_schema)
        
        if "items" in new_schema:
            new_schema["items"] = self._clean_schema(new_schema["items"])

        return new_schema

    def _normalize_tool_arguments(self, func_name: str, func_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza argumentos de tool-call para reduzir falhas por drift de schema
        entre providers (ex.: string vs integer).
        """
        args = dict(func_args or {})

        # Normalização genérica de limite.
        if "limite" in args and args["limite"] is not None:
            raw = args["limite"]
            try:
                if isinstance(raw, str):
                    raw = raw.strip()
                limit_val = int(raw)
                if limit_val <= 0:
                    limit_val = 10
                args["limite"] = limit_val
            except (TypeError, ValueError):
                args["limite"] = 10

        # Compatibilidade para ferramenta de gráfico.
        if func_name == "gerar_grafico_universal_v2":
            for key in ("filtro_une", "filtro_produto"):
                if key in args and args[key] is not None:
                    args[key] = str(args[key])

            if "tipo_grafico" in args and isinstance(args["tipo_grafico"], str):
                mapping = {"barras": "bar", "linhas": "line"}
                args["tipo_grafico"] = mapping.get(args["tipo_grafico"].lower(), args["tipo_grafico"])

        return args

    def _execute_tool_with_recovery(self, tool_to_run: Any, func_name: str, func_args: Dict[str, Any]) -> Any:
        """
        Executa ferramenta com normalização e uma tentativa de recuperação.
        """
        normalized_args = self._normalize_tool_arguments(func_name, func_args)
        try:
            return tool_to_run.invoke(normalized_args)
        except Exception as first_error:
            # Retry defensivo para casos de validação estrita de tipo.
            retry_args = dict(normalized_args)
            if "limite" in retry_args and retry_args["limite"] is not None:
                retry_args["limite"] = str(retry_args["limite"])

            logger.warning(
                f"Tool {func_name} falhou na 1a tentativa ({first_error}). "
                f"Tentando recuperação com argumentos coercidos."
            )
            return tool_to_run.invoke(retry_args)

    def _should_use_deterministic_path(self, tool_name: str, confidence: float) -> bool:
        """
        Define quando executar ferramenta diretamente sem rodada LLM,
        reduzindo custo e falhas em consultas determinísticas.
        """
        deterministic_tools = {
            "encontrar_rupturas_criticas",
            "consultar_dados_flexivel",
        }
        return tool_name in deterministic_tools and confidence >= 0.80

    def _format_deterministic_result(
        self,
        user_query: str,
        tool_name: str,
        tool_result: Any,
    ) -> Dict[str, Any]:
        """
        Formata saída de ferramenta determinística para resposta de negócio.
        """
        if not isinstance(tool_result, dict):
            return {
                "type": "text",
                "result": {"mensagem": "Resultado recebido em formato inesperado."},
            }

        if tool_result.get("error"):
            return {
                "type": "text",
                "result": {"mensagem": f"Não consegui concluir a análise: {tool_result.get('error')}"},
            }

        query_lower = user_query.lower()

        if tool_name == "encontrar_rupturas_criticas":
            total = int(tool_result.get("total_criticos", 0) or 0)
            produtos = tool_result.get("produtos_criticos", []) or []
            if total == 0:
                msg = tool_result.get("mensagem") or "Não encontrei rupturas críticas no recorte atual."
                return {"type": "text", "result": {"mensagem": msg}}

            # Consolidar por segmento para visão executiva.
            seg_counts: Dict[str, int] = {}
            for p in produtos:
                seg = str(p.get("segmento", "N/A"))
                seg_counts[seg] = seg_counts.get(seg, 0) + 1
            top_segments = sorted(seg_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            seg_line = ", ".join([f"{s}: {c}" for s, c in top_segments]) if top_segments else "N/A"

            msg = (
                f"Identifiquei {total} rupturas críticas no recorte atual. "
                f"Segmentos mais afetados: {seg_line}. "
                "Posso detalhar os produtos críticos por grupo/UNE em seguida.\n"
                "Evidência: fonte=admmat.parquet, regra=estoque_cd<=0 e estoque_atual<linha_verde, "
                f"amostra_exibida={len(produtos)}."
            )
            return {"type": "text", "result": {"mensagem": msg}}

        if tool_name == "consultar_dados_flexivel":
            resultados = tool_result.get("resultados", []) or []
            if not resultados:
                msg = tool_result.get("mensagem") or "Não encontrei dados para este recorte."
                return {"type": "text", "result": {"mensagem": msg}}

            # Caso especial: perguntas sobre vendas negativas/ruins.
            if any(k in query_lower for k in ["negativ", "ruin", "piores grupos", "vendaas ruins"]):
                group_totals: Dict[str, float] = {}
                for row in resultados:
                    if not isinstance(row, dict):
                        continue
                    group = str(row.get("NOMEGRUPO") or row.get("nomegrupo") or "SEM_GRUPO")
                    segment = str(row.get("NOMESEGMENTO") or row.get("nomesegmento") or "SEM_SEGMENTO")
                    key = f"{group} ({segment})"
                    venda = row.get("valor") or row.get("VENDA_30DD") or row.get("venda_30dd") or 0
                    try:
                        venda_f = float(venda)
                    except (TypeError, ValueError):
                        venda_f = 0.0
                    group_totals[key] = group_totals.get(key, 0.0) + venda_f

                negativos = [(g, v) for g, v in group_totals.items() if v < 0]
                negativos.sort(key=lambda x: x[1])  # mais negativo primeiro
                top_neg = negativos[:10]

                if not top_neg:
                    return {
                        "type": "text",
                        "result": {"mensagem": "Não encontrei grupos com vendas negativas no recorte atual."},
                    }

                linhas = [f"{idx+1}. {g}: {v:,.2f}" for idx, (g, v) in enumerate(top_neg)]
                msg = (
                    "Diagnóstico: identifiquei grupos com vendas negativas no recorte atual.\n"
                    "Top grupos críticos:\n"
                    + "\n".join(linhas)
                    + "\nAção recomendada: revisar preço/mix/ruptura desses grupos e validar se houve devoluções ou ajustes contábeis no período."
                    + f"\nEvidência: métrica=SUM(VENDA_30DD), grupos_analisados={len(group_totals)}, grupos_negativos={len(negativos)}."
                )
                return {"type": "text", "result": {"mensagem": msg}}

            # Default determinístico para consulta flexível.
            return {
                "type": "text",
                "result": {"mensagem": tool_result.get("mensagem") or f"Consulta retornou {len(resultados)} registros."},
            }

        return {
            "type": "text",
            "result": {"mensagem": "Consulta executada com sucesso."},
        }

    def _build_clarification_if_needed(self, user_query: str, tool_name: str, confidence: float) -> Optional[Dict[str, Any]]:
        """
        Detecta consultas comerciais vagas e retorna pergunta de desambiguação.
        """
        q = (user_query or "").lower().strip()
        if confidence < 0.70:
            return None

        vague_markers = ["ruins", "negativa", "negativas", "piores", "melhores", "desempenho"]
        if not any(m in q for m in vague_markers):
            return None

        has_time_window = bool(
            any(
                token in q
                for token in [
                    "30d", "30 dias", "7 dias", "90 dias", "hoje", "ontem",
                    "semana", "mensal", "mês", "mes", "trimestre", "ano",
                    "últimos", "ultimos"
                ]
            )
            or __import__("re").search(r"\b\d+\s*dias?\b", q)
        )
        has_scope = any(token in q for token in ["grupo", "grupos", "segmento", "segmentos", "une", "loja", "lojas"])

        if has_scope:
            # Regra comercial: se recorte já está claro, usa janela padrão de 30 dias.
            return None

        if tool_name not in {"consultar_dados_flexivel", "gerar_grafico_universal_v2"}:
            return None

        if has_time_window:
            msg = (
                "Para te responder com precisão comercial, confirme o recorte da análise:\n"
                "por grupo, segmento ou UNE?\n"
                "Exemplo: 'top grupos com venda negativa nos últimos 30 dias na UNE 135'."
            )
        else:
            msg = (
                "Para te responder com precisão comercial, confirme o recorte da análise:\n"
                "por grupo, segmento ou UNE?\n"
                "Se você não informar período, vou usar os últimos 30 dias como padrão."
            )
        return {"type": "text", "result": {"mensagem": msg}}

    async def run_async(
        self, 
        user_query: str, 
        chat_history: Optional[List[Dict]] = None,
        on_progress: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        Async version of run method with Universal Tool Selection System.
        """
        logger.info(f"CaculinhaBIAgent (Modern Async): Processing query: {user_query}")

        # ========================================================================
        # CAMADA 1: INTENT CLASSIFICATION (NEW 2026-01-24)
        # ========================================================================
        from backend.app.core.utils.intent_classifier import classify_intent
        from backend.app.core.utils.query_router import route_query
        
        intent_result = classify_intent(user_query)
        logger.info(
            f"[INTENT] Classified as {intent_result.intent.value} "
            f"(confidence: {intent_result.confidence:.2f}, "
            f"patterns: {intent_result.matched_patterns})"
        )
        
        # ========================================================================
        # CAMADA 2: QUERY ROUTING (NEW 2026-01-24)
        # ========================================================================
        tool_selection = route_query(
            intent=intent_result.intent,
            query=user_query,
            confidence=intent_result.confidence
        )
        logger.info(
            f"[ROUTER] Selected tool: {tool_selection.tool_name} "
            f"(confidence: {tool_selection.confidence:.2f})"
        )
        logger.info(f"[ROUTER] Extracted params: {tool_selection.tool_params}")
        logger.info(f"[ROUTER] Reasoning: {tool_selection.reasoning}")

        clarification = self._build_clarification_if_needed(
            user_query,
            tool_selection.tool_name,
            tool_selection.confidence,
        )
        if clarification is not None:
            logger.info("[CLARIFICATION] Consulta vaga detectada. Retornando pergunta guiada.")
            return clarification

        # ========================================================================
        # CAMADA 2.5: DETERMINISTIC EXECUTION PATH (LOW COST / HIGH RELIABILITY)
        # Executa ferramentas determinísticas diretamente quando a confiança é alta.
        # ========================================================================
        if self._should_use_deterministic_path(tool_selection.tool_name, tool_selection.confidence):
            logger.info(
                f"[DETERMINISTIC] Executando {tool_selection.tool_name} sem rodada LLM "
                f"(confidence={tool_selection.confidence:.2f})"
            )
            if on_progress:
                await on_progress({"type": "tool_progress", "tool": tool_selection.tool_name, "status": "executing"})

            tool_to_run = next((t for t in self.bi_tools if t.name == tool_selection.tool_name), None)
            if tool_to_run is not None:
                try:
                    tool_result = await asyncio.to_thread(
                        self._execute_tool_with_recovery,
                        tool_to_run,
                        tool_selection.tool_name,
                        tool_selection.tool_params,
                    )
                    return self._format_deterministic_result(user_query, tool_selection.tool_name, tool_result)
                except Exception as e:
                    logger.warning(f"[DETERMINISTIC] Falhou, voltando para fluxo LLM: {e}")

        # START RAG WARMING
        await self._start_rag_warming()

        messages = []

        # OPTIMIZATION: Context Pruning
        if chat_history:
            filtered_history = [msg for msg in chat_history if msg.get("role") != "system"]
            max_history = settings.LLM_HISTORY_MAX_MESSAGES if settings.DEV_FAST_MODE else 15
            recent_history = filtered_history[-max_history:] if len(filtered_history) > max_history else filtered_history

            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                messages.append({"role": role, "content": content})

        # [OK] FIX RAG: Context Fencing Injection com TIMEOUT
        # Em vez de adicionar mensagens fake, adicionamos um bloco de contexto na mensagem do usuário
        try:
            # [OK] FIX: Timeout de 500ms para não bloquear (continua sem RAG se demorar)
            rag_context_str = await asyncio.wait_for(
                self._get_rag_examples(user_query, top_k=1),  # [OK] Reduzido de 2 para 1 exemplo
                timeout=0.5  # 500ms timeout
            )
        except asyncio.TimeoutError:
            logger.warning("[RAG] Timeout de 500ms excedido. Continuando sem RAG.")
            rag_context_str = ""
        except Exception as e:
            logger.error(f"[RAG] Erro ao recuperar contexto: {e}")
            rag_context_str = ""
        
        # Combinar query do usuário com o contexto RAG (se houver)
        # BEST PRACTICE: Contexto ANTES da Query (Recency Bias)
        if rag_context_str:
            full_prompt_content = rag_context_str + "\n\n" + "PERGUNTA DO USUÁRIO AGORA:\n" + user_query
            logger.info("[RAG] Contexto PREPENDED na mensagem do usuário (Context Fencing)")
        else:
            full_prompt_content = user_query

        # Add current user query (enhanced)
        messages.append({"role": "user", "content": full_prompt_content})

        # ========================================================================
        # CAMADA 3: SYSTEM HINT INJECTION (MODERN 2026)
        # Em vez de forçar, damos uma "dica" ao LLM sobre a ferramenta ideal.
        # Isso preserva o Chain of Thought e autonomia do modelo.
        # ========================================================================
        SYSTEM_HINT_THRESHOLD = 0.70
        
        if tool_selection.confidence > SYSTEM_HINT_THRESHOLD:
            logger.info(
                f"[HINT] High confidence ({tool_selection.confidence:.2f}) - "
                f"Injecting system hint for: {tool_selection.tool_name}"
            )
            
            # Mensagem de "Dica do Sistema" (visível apenas para o LLM)
            system_hint_msg = (
                f"SYSTEM_HINT: A intenção do usuário foi classificada como '{intent_result.intent.value}' "
                f"com {tool_selection.confidence:.0%} de confiança. "
                f"A ferramenta sugerida é `{tool_selection.tool_name}` com parâmetros {json.dumps(tool_selection.tool_params)}. "
                f"Use essa ferramenta se fizer sentido, mas sinta-se livre para ajustar os parâmetros ou pedir mais informações."
            )
            
            # Adicionar como mensagem 'user' ou 'system' dependendo do suporte do adapter
            # Para Gemini, adicionamos como uma nota prévia à query do usuário ou uma mensagem user separada
            messages.insert(-1, {"role": "user", "content": system_hint_msg})

        # ========================================================================
        # CAMADA 4: DYNAMIC SCHEMA INJECTION (TRUTH SOURCE)
        # Injeta colunas válidas para evitar alucinação (ex: VLR_VENDA_LIQ_NF)
        # ========================================================================
        try:
            from backend.app.core.utils.field_mapper import FieldMapper
            fm = FieldMapper()
            # Only inject if we are likely doing data analysis
            if tool_selection.confidence > 0.5 or intent_result.intent.value in ["analysis", "data_query"]:
                valid_cols = fm.get_essential_columns()
                schema_msg = (
                    "SYSTEM_FACT: Use APENAS estas colunas para queries SQL (DuckDB/Parquet). "
                    "Ignore nomes de colunas em exemplos antigos.\n"
                    f"Colunas Válidas: {json.dumps(valid_cols)}"
                )
                # Insert before user query (which is at -1 now due to previous insert, or -1 if no hint)
                # Making sure it's close to the user query
                messages.insert(-1, {"role": "user", "content": schema_msg})
                logger.info("[SCHEMA] Injetadas colunas essenciais no contexto.")
        except Exception as e:
            logger.warning(f"[SCHEMA] Falha ao injetar schema: {e}")

        
        # ========================================================================
        # MODERN REACT FLOW (Context7 - Gemini 2.5 Pro)
        # ========================================================================
        # We trust the model's internal reasoning (ReAct) to decide between tools and text.
        # No more keyword-based forcing or prefilling.
        
        # Determine tools to use (all tools available by default)
        tools_to_use = self.gemini_tools
        
        max_turns = 15
        current_turn = 0
        successful_tool_calls = 0  # Track tool usage for final reporting

        while current_turn < max_turns:
            try:
                # Notify thinking
                if on_progress:
                    await on_progress({"type": "tool_progress", "tool": "Pensando", "status": "start"})

                # Call LLM with tools (Blocking call wrapped in thread)
                # self.llm is GeminiLLMAdapter which is synchronous
                response = await asyncio.to_thread(
                    self.llm.get_completion,
                    messages,
                    tools=tools_to_use
                )

                if "error" in response:
                    logger.error(f"LLM Error: {response['error']}")
                    print(f"\n{'='*80}\n[CRITICAL DEBUG] LLM RETORNOU ERRO: {response['error']}\n{'='*80}\n", flush=True)
                    return self._generate_error_response(response['error'])

                # [OK] FIX: LOGGING (mesmo do run())
                response_type = "tool_call" if "tool_calls" in response else "text"
                logger.info(f"[ASYNC] LLM Response Type: {response_type}")

                # MODERN CHECK: Trust the LLM. If it returns text, it's text.
                # No more forcing graph generation based on keywords.
                if response_type == "text" and successful_tool_calls == 0:
                     # Log context for debugging but don't force fallback
                     pass

                # Check for tool calls
                if "tool_calls" in response:
                    tool_calls = response["tool_calls"]
                    messages.append({
                        "role": "model",
                        "tool_calls": tool_calls
                    })

                    # PARALLEL EXECUTION 2025: Executar todas as ferramentas simultaneamente
                    # Define helper function for individual execution
                    async def execute_single_tool(tc):
                        func_name = tc["function"]["name"]
                        try:
                            func_args = json.loads(tc["function"]["arguments"])
                        except json.JSONDecodeError:
                            return func_name, {"error": "Invalid JSON arguments"}

                        # Notify tool start
                        if on_progress:
                            await on_progress({"type": "tool_progress", "tool": func_name, "status": "executing"})

                        tool_to_run = next((t for t in self.bi_tools if t.name == func_name), None)
                        
                        if tool_to_run:
                            try:
                                # Execute tool (Blocking call wrapped in thread)
                                tool_output = await asyncio.to_thread(
                                    self._execute_tool_with_recovery,
                                    tool_to_run,
                                    func_name,
                                    func_args,
                                )
                                
                                # Convert MapComposite
                                def convert_mapcomposite(obj):
                                    if hasattr(obj, '_mapping'):
                                        return dict(obj._mapping)
                                    elif isinstance(obj, dict):
                                        return {k: convert_mapcomposite(v) for k, v in obj.items()}
                                    elif isinstance(obj, list):
                                        return [convert_mapcomposite(item) for item in obj]
                                    return obj
                                
                                return func_name, convert_mapcomposite(tool_output)
                            except Exception as e:
                                logger.error(f"Error executing {func_name}: {e}")
                                return func_name, {"error": str(e)}
                        else:
                            return func_name, {"error": f"Tool {func_name} not found"}

                    # Execute all tools in parallel
                    logger.info(f"[ASYNC] Disparando {len(tool_calls)} ferramentas em PARALELO")
                    tasks = [execute_single_tool(tc) for tc in tool_calls]
                    results = await asyncio.gather(*tasks)

                    # Process results sequentially
                    should_exit_early = False
                    
                    # Create a map of results by function name to match with call IDs
                    # Note: This assumes unique function names per turn, or we need to map by index if reliable
                    # Better approach: Map by call ID if we passed it to execute_single_tool, but we didn't.
                    # Since we iterate tasks in same order as tool_calls, we can zip them.
                    
                    for i, (func_name, tool_result) in enumerate(results):
                        original_tool_call = tool_calls[i]
                        tool_call_id = original_tool_call.get("id")
                        
                        # OPTIMIZATION 2025: Success detection and early exit for charts
                        if isinstance(tool_result, dict):
                            is_chart = "chart_data" in tool_result or "chart_spec" in tool_result
                            is_success = tool_result.get("status") == "success" or len(tool_result.get("resultados", [])) > 0
                            
                            if is_chart and is_success:
                                logger.info(f"[ASYNC] SUCESSO: Grafico gerado por {func_name}. Forcando saida antecipada.")
                                successful_tool_calls += 1
                                should_exit_early = True
                            elif is_success:
                                successful_tool_calls += 1

                        # OTIMIZAÇÃO DE SERIALIZAÇÃO: Offload para thread (CPU bound para grandes JSONs)
                        serialized_content = await asyncio.to_thread(safe_json_serialize, tool_result)

                        # Add tool result to messages with CORRECT ID
                        messages.append({
                            "role": "function", # Adapter converts to 'tool'
                            "name": func_name,  # Helpful for adapter fallback
                            "tool_call_id": tool_call_id, # CRITICAL for Groq
                            "content": serialized_content
                        })

                    if should_exit_early:
                        logger.info("[ASYNC] SUCESSO: Gráfico detectado. Encerrando loop de ferramentas para priorizar entrega.")
                        # BREAK LOOP: Don't ask LLM to narrate immediately to avoid loop risk.
                        # Instead, we will force the loop to end and let the final check handle the chart response.
                        break
                    
                    # Loop continues
                    current_turn += 1
                    continue
                
                # If no tool calls, it's a text response (Final Answer)
                content = response.get("content", "")

                # Notify finalizing
                if on_progress:
                     await on_progress({"type": "tool_progress", "tool": "Processando resposta", "status": "finishing"})

                # Same logic as run() for parsing result...
                # (Duplicating logic from run() to ensure consistency)
                
                # Acumuladores para múltiplos resultados de ferramentas
                found_chart_data = None
                found_chart_summary = None
                found_table_mensagem = None
                found_resultados = None

                for msg in reversed(messages):
                    if msg.get("role") == "function":
                        try:
                            content_str = msg.get("content", "{}")
                            func_content = json.loads(content_str)

                            chart_data = func_content.get("chart_data")
                            if chart_data and func_content.get("status") == "success" and found_chart_data is None:
                                if isinstance(chart_data, str):
                                    try:
                                        chart_data = json.loads(chart_data)
                                    except json.JSONDecodeError:
                                        continue
                                found_chart_data = chart_data
                                found_chart_summary = func_content.get("summary", {})
                            
                            mensagem = func_content.get("mensagem", "")
                            if isinstance(mensagem, str) and "|" in mensagem and "---" in mensagem and found_table_mensagem is None:
                                found_table_mensagem = mensagem
                            
                            resultados = func_content.get("resultados", [])
                            if isinstance(resultados, list) and len(resultados) > 0 and found_resultados is None:
                                found_resultados = resultados

                        except Exception as e:
                            logger.error(f"DEBUG: Erro ao parsear mensagem de função: {e}")
                            continue

                # PRIORIDADE DE RETORNO: Gráfico tem maior prioridade
                if found_chart_data is not None:
                    # CONTEXT7: Limpar JSON bruto e aplicar narrativa
                    content = self._clean_context7_violations(content, context_type="chart")

                    return {
                        "type": "code_result",
                        "result": {
                            "result": found_chart_summary,
                            "chart_spec": found_chart_data
                        },
                        "chart_spec": found_chart_data,
                        "text_override": content
                    }
                
                # PRIORIDADE 2: Dados Tabulares (Se encontrou resultados mas não é gráfico)
                elif found_resultados is not None:
                    # CONTEXT7: Limpar JSON bruto e aplicar narrativa
                    content = self._clean_context7_violations(content, context_type="data")
                    
                    return {
                        "type": "code_result",
                        "result": found_resultados, # Lista de dicts para o frontend renderizar Tabela
                        "text_override": content
                    }

                # SAFETY NET: Check if the content is the specific JSON ReAct pattern OR just a JSON block and extract/convert
                try:
                    if isinstance(content, str):
                        content_stripped = content.strip()
                        # Caso 1: JSON Puro (o problema relatado)
                        if content_stripped.startswith("{") and content_stripped.endswith("}"):
                            try:
                                json_data = json.loads(content_stripped)
                                
                                # Se for o formato analítico específico que o usuário mostrou
                                if "analise_executiva" in json_data:
                                    # Converter para Markdown Bonito
                                    md_output = ""
                                    
                                    # 1. Manchete
                                    exec_data = json_data.get("analise_executiva", {})
                                    emoji_status = "🚨" if "ALERTA" in str(exec_data.get("status_geral", "")).upper() else "[DATA]"
                                    md_output += f"### {emoji_status} {exec_data.get('manchete', 'Análise de Dados')}\n\n"
                                    
                                    # 2. Diagnóstico
                                    md_output += "**Diagnóstico Detalhado:**\n"
                                    diag_data = json_data.get("diagnostico_por_unidade", {})
                                    for unidade, dados in diag_data.items():
                                        insight = dados.get("insight", "")
                                        situacao = dados.get("situacao", "")
                                        md_output += f"- **{unidade} ({situacao})**: {insight}\n"
                                    md_output += "\n"
                                    
                                    # 3. Estratégia
                                    md_output += "**Estratégia Recomendada:**\n"
                                    strategies = json_data.get("estrategia_recomendada", [])
                                    if isinstance(strategies, list):
                                        for strat in strategies:
                                            md_output += f"- {strat}\n"
                                    elif isinstance(strategies, str):
                                        md_output += f"{strategies}\n"
                                        
                                    logger.info("SAFETY NET: Converteu JSON analítico para Markdown.")
                                    content = md_output

                                # Caso 2: ReAct Pattern (Legacy)
                                elif "action" in json_data and "content" in json_data:
                                    logger.info("SAFETY NET: Extracted content from ReAct JSON pattern.")
                                    content = json_data["content"]
                                
                            except json.JSONDecodeError:
                                pass # Não é JSON válido, segue o baile
                except Exception as e:
                    logger.warning(f"SAFETY NET: Failed to parse potential JSON content: {e}")

                # Se não há gráfico, retornar APENAS texto analítico (O usuário NÃO quer tabelas)
                return {
                    "type": "text",
                    "result": content
                }

            except Exception as e:
                logger.error(f"Exception in agent run loop: {e}", exc_info=True)
                return self._generate_error_response(str(e))

        # FIX: Antes de retornar erro, verificar se há gráfico gerado com sucesso
        # Isso evita perder o trabalho se o LLM não retornou texto mas gerou o gráfico
        logger.warning("[ASYNC] Max turns atingido. Verificando se ha grafico para retornar...")

        for msg in reversed(messages):
            if msg.get("role") == "function":
                try:
                    content_str = msg.get("content", "{}")
                    func_content = json.loads(content_str)
                    chart_data = func_content.get("chart_data")

                    if chart_data and func_content.get("status") == "success":
                        logger.info("[ASYNC] Grafico encontrado! Retornando mesmo sem texto final do LLM.")
                        if isinstance(chart_data, str):
                            try:
                                chart_data = json.loads(chart_data)
                            except:
                                pass

                        return {
                            "type": "code_result",
                            "result": {
                                "result": func_content.get("summary", {}),
                                "chart_spec": chart_data
                            },
                            "chart_spec": chart_data,
                            "text_override": func_content.get("mensagem")
                                or func_content.get("summary", {}).get("mensagem")
                                or func_content.get("analysis")
                                or "Gráfico gerado com base nos dados atuais."
                        }
                except:
                    continue

        return self._generate_error_response("Maximum conversation turns exceeded.")

    def run(self, user_query: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Executes the agent loop:
        1. Send query + tools to LLM.
        2. If LLM wants to call tool -> Execute tool -> Send result back to LLM.
        3. Repeat until LLM returns text.
        """
        logger.info(f"CaculinhaBIAgent (Modern): Processing query: {user_query}")

        # [OK] CRITICAL FIX: NÃO incluir system como mensagem
        # System instruction já está configurada no GeminiLLMAdapter via system_instruction parameter
        # Gemini NÃO aceita role="system" no array de mensagens - deve usar system_instruction no modelo
        # Ref: https://ai.google.dev/gemini-api/docs/system-instructions
        messages = []

        # OPTIMIZATION: Context pruning for cost control in dev-fast mode.
        if chat_history:
            # Filtrar mensagens system
            filtered_history = [msg for msg in chat_history if msg.get("role") != "system"]
            max_history = settings.LLM_HISTORY_MAX_MESSAGES if settings.DEV_FAST_MODE else 30
            recent_history = filtered_history[-max_history:] if len(filtered_history) > max_history else filtered_history

            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                messages.append({"role": role, "content": content})

            if len(filtered_history) > 30:
                logger.info(f"[CONTEXT PRUNING] Histórico reduzido: {len(filtered_history)} → {len(recent_history)} mensagens (Llama-3 Extended)")

        # RAG: Retrieve similar examples before processing query
        # NOTE: run() is sync, so we skip RAG warming and use sync retrieve
        rag_context_str = ""
        if self.enable_rag and self.retriever and self.retriever._initialized:
            try:
                # Reutilizar lógica de formatação do _get_rag_examples mas de forma síncrona
                similar_docs = self.retriever.retrieve(user_query, top_k=2, method='hybrid')
                if similar_docs:
                    rag_context_str = "\n\n<reference_context>\n"
                    rag_context_str += "[WARNING] EXEMPLOS DE INTERAÇÕES PASSADAS (PARA APRENDER A LÓGICA):\n"
                    rag_context_str += "INSTRUÇÃO CRÍTICA: Use estes exemplos APENAS para entender qual ferramenta chamar ou como formatar a resposta.\n"
                    rag_context_str += "PROIBIDO: Não copie números, IDs ou nomes destes exemplos. Os dados abaixo são OBSOLETOS.\n\n"

                    for i, doc in enumerate(similar_docs[:2]):
                        doc_data = doc.get('doc', doc)
                        user_q = doc_data.get('query', doc_data.get('user_query', ''))
                     # FIX 2026-01-27: Aumentado de 500 para 2000 chars (respostas mais completas)
                        assist_r = doc_data.get('response', doc_data.get('assistant_response', ''))
                        if len(assist_r) > 2000: assist_r = assist_r[:2000] + "..."
                        
                        rag_context_str += f"--- EXEMPLO {i+1} ---\nPergunta: {user_q}\nAção Correta: {assist_r}\n"
                    
                    rag_context_str += "</reference_context>\n"
                    logger.info(f"[RAG] Contexto injetado com sucesso (Sync Mode)")
            except Exception as e:
                logger.warning(f"[RAG] Erro ao recuperar exemplos no run() sync: {e}")

        # Add current user query (with context PREPENDED)
        if rag_context_str:
            full_prompt_content = rag_context_str + "\n\n" + "PERGUNTA DO USUÁRIO AGORA:\n" + user_query
        else:
            full_prompt_content = user_query
            
        messages.append({"role": "user", "content": full_prompt_content})

        # ========================================================================
        # MODERN SYNC RUN (Context7)
        # ========================================================================
        
        # Determine tools to use
        tools_to_use = self.gemini_tools

        max_turns = 15
        current_turn = 0
        successful_tool_calls = 0

        while current_turn < max_turns:
            try:
                # Call LLM with tools
                # Note: self.llm is GeminiLLMAdapter
                response = self.llm.get_completion(messages, tools=tools_to_use)

                if "error" in response:
                    logger.error(f"LLM Error: {response['error']}")
                    return self._generate_error_response(response['error'])

                # FIX: LOGGING DETALHADO - Detectar quando LLM ignora solicitações de gráfico
                response_type = "tool_call" if "tool_calls" in response else "text"
                logger.info(f"LLM Response Type: {response_type}")

                # FIX 2026-02-04: Definir is_graph_request que estava faltando (NameError)
                graph_keywords = ["gráfico", "grafico", "chart", "visualização", "visualizacao", "plote", "plot", "ranking", "top"]
                is_graph_request = any(keyword in user_query.lower() for keyword in graph_keywords)

                # ALERTA se pediu gráfico mas LLM respondeu só com texto
                if response_type == "text" and is_graph_request and successful_tool_calls == 0:
                    logger.error(f"WARNING: LLM IGNOROU PEDIDO DE GRAFICO!")
                    logger.error(f"WARNING - User Query: {user_query}")
                    logger.error(f"WARNING - LLM Text Response: {response.get('content', '')[:300]}")
                    logger.error(f"WARNING - Total messages in context: {len(messages)}")

                    # FALLBACK AUTOMÁTICO: Se LLM ignorou, forçar chamada da ferramenta manualmente
                    logger.warning(f"FALLBACK: Forcando chamada manual de gerar_grafico_universal_v2")
                    # Criar tool call sintético
                    synthetic_tool_call = {
                        "id": "call_fallback_graph",
                        "type": "function",
                        "function": {
                            "name": "gerar_grafico_universal_v2",
                            "arguments": json.dumps({"descricao": user_query})
                        }
                    }
                    # Injetar tool call sintético na resposta
                    response["tool_calls"] = [synthetic_tool_call]
                    logger.warning(f"FALLBACK APLICADO: Tool call sintetico criado")

                # Check for tool calls
                if "tool_calls" in response:
                    tool_calls = response["tool_calls"]
                    messages.append({
                        "role": "model",
                        "tool_calls": tool_calls
                    })

                    # Execute each tool
                    should_exit_early = False
                    for tc in tool_calls:
                        func_name = tc["function"]["name"]
                        tool_call_id = tc.get("id") # CRITICAL: Capture ID
                        func_args = json.loads(tc["function"]["arguments"])
                        
                        logger.info(f"Agent calling tool: {func_name} with args: {func_args}")
                        
                        # Find the matching tool
                        tool_to_run = next((t for t in self.bi_tools if t.name == func_name), None)
                        
                        tool_result = None
                        if tool_to_run:
                            try:
                                # Execute tool
                                tool_output = self._execute_tool_with_recovery(
                                    tool_to_run,
                                    func_name,
                                    func_args,
                                )

                                # CRITICAL FIX: Detectar se gerou gráfico com sucesso
                                if isinstance(tool_output, dict):
                                    is_chart = "chart_data" in tool_output or "chart_spec" in tool_output
                                    is_success = tool_output.get("status") == "success" or len(tool_output.get("resultados", [])) > 0
                                    
                                    if is_chart and is_success:
                                        logger.info(f"SUCESSO: Grafico gerado por {func_name}. Forcando saida antecipada.")
                                        successful_tool_calls += 1
                                        should_exit_early = True
                                    elif is_success:
                                        successful_tool_calls += 1

                                # CRÍTICO: Converter MapComposite para dict ANTES de serializar
                                def convert_mapcomposite(obj):
                                    """Recursivamente converte MapComposite para dict"""
                                    if hasattr(obj, '_mapping'):
                                        return dict(obj._mapping)
                                    elif isinstance(obj, dict):
                                        return {k: convert_mapcomposite(v) for k, v in obj.items()}
                                    elif isinstance(obj, list):
                                        return [convert_mapcomposite(item) for item in obj]
                                    return obj
                                
                                # Converter o output antes de usar
                                tool_result = convert_mapcomposite(tool_output)
                                logger.info(f"Tool {func_name} executed successfully, result type: {type(tool_result)}")
                            except Exception as e:
                                logger.error(f"Error executing {func_name}: {e}", exc_info=True)
                                tool_result = {"error": str(e)}
                        else:
                            tool_result = {"error": f"Tool {func_name} not found"}

                        # Add tool result to messages
                        messages.append({
                            "role": "function", # Adapter will map this to user/function_response
                            "name": func_name,
                            "tool_call_id": tool_call_id, # CRITICAL
                            "content": safe_json_serialize(tool_result)
                        })

                    if should_exit_early:
                        logger.info("Saindo do loop para retornar grafico imediatamente.")
                        # [OK] FIX: Forçar uma última iteração para LLM gerar texto narrativo
                        # Adicionar mensagem sintética para forçar resposta final
                        messages.append({
                            "role": "user",
                            "content": "Apresente o gráfico de forma clara e concisa."
                        })
                        # Continuar para obter resposta final do LLM
                        current_turn += 1
                        continue

                    # Loop continues to send tool outputs back to LLM
                    current_turn += 1
                    continue
                
                # If no tool calls, it's a text response (Final Answer)
                content = response.get("content", "")

                # CONTEXT7: Limpar JSON bruto da resposta (improved 2025-12-27)
                content = self._clean_context7_violations(content, context_type="generic")

                # NOVO: Verificar TODAS as ferramentas para encontrar gráficos ou tabelas
                # PRIORIDADE: Gráficos > Tabelas Markdown > Dados brutos > Texto do LLM
                logger.info(f"DEBUG: Verificando dados tabulares/gráficos. Total de mensagens: {len(messages)}")

                # Acumuladores para múltiplos resultados de ferramentas
                found_chart_data = None
                found_chart_summary = None
                found_table_mensagem = None
                found_resultados = None

                # Percorrer TODAS as mensagens de função (não parar no primeiro)
                for msg in reversed(messages):
                    if msg.get("role") == "function":
                        try:
                            content_str = msg.get("content", "{}")
                            func_content = json.loads(content_str)

                            # PRIMEIRO: Verificar se a ferramenta retornou um gráfico (chart_data)
                            chart_data = func_content.get("chart_data")
                            if chart_data and func_content.get("status") == "success" and found_chart_data is None:
                                logger.info(f"SUCESSO: Gráfico detectado (chart_type: {func_content.get('chart_type', 'unknown')})")

                                # CRÍTICO: chart_data pode ser string JSON (de fig.to_json())
                                # O frontend espera um objeto, não uma string
                                if isinstance(chart_data, str):
                                    try:
                                        chart_data = json.loads(chart_data)
                                        logger.info("chart_data parseado de string para objeto")
                                    except json.JSONDecodeError:
                                        logger.error("Falha ao parsear chart_data como JSON")
                                        continue  # Tentar próxima mensagem

                                found_chart_data = chart_data
                                found_chart_summary = func_content.get("summary", {})
                                # Continuar buscando para não perder outras ferramentas
                            
                            # SEGUNDO: Verificar se a mensagem contém uma tabela Markdown
                            mensagem = func_content.get("mensagem", "")
                            if isinstance(mensagem, str) and "|" in mensagem and "---" in mensagem and found_table_mensagem is None:
                                logger.info(f"SUCESSO: Tabela Markdown detectada na mensagem da ferramenta!")
                                found_table_mensagem = mensagem
                            
                            # TERCEIRO: Verificar se há dados brutos para retornar
                            resultados = func_content.get("resultados", [])
                            if isinstance(resultados, list) and len(resultados) > 0 and found_resultados is None:
                                logger.info(f"SUCESSO: Dados tabulares detectados: {len(resultados)} registros")
                                found_resultados = resultados

                        except Exception as e:
                            logger.error(f"DEBUG: Erro ao parsear mensagem de função: {e}")
                            continue  # Tentar próxima mensagem

                # PRIORIDADE DE RETORNO: Gráfico tem maior prioridade
                if found_chart_data is not None:
                    # CONTEXT7: Limpar JSON bruto e aplicar narrativa
                    content = self._clean_context7_violations(content, context_type="chart")

                    return {
                        "type": "code_result",
                        "result": {
                            "result": found_chart_summary,
                            "chart_spec": found_chart_data
                        },
                        "chart_spec": found_chart_data,
                        "text_override": content
                    }
                
                # PRIORIDADE 2: Dados Tabulares (Se encontrou resultados mas não é gráfico)
                elif found_resultados is not None:
                    # CONTEXT7: Limpar JSON bruto e aplicar narrativa
                    content = self._clean_context7_violations(content, context_type="data")
                    
                    return {
                        "type": "code_result",
                        "result": found_resultados, # Lista de dicts para o frontend renderizar Tabela
                        "text_override": content
                    }

                # SAFETY NET: Check if the content is the specific JSON ReAct pattern OR just a JSON block and extract/convert
                try:
                    if isinstance(content, str):
                        content_stripped = content.strip()
                        # Caso 1: JSON Puro (o problema relatado)
                        if content_stripped.startswith("{") and content_stripped.endswith("}"):
                            try:
                                json_data = json.loads(content_stripped)
                                
                                # Se for o formato analítico específico que o usuário mostrou
                                if "analise_executiva" in json_data:
                                    # Converter para Markdown Bonito
                                    md_output = ""
                                    
                                    # 1. Manchete
                                    exec_data = json_data.get("analise_executiva", {})
                                    emoji_status = "🚨" if "ALERTA" in str(exec_data.get("status_geral", "")).upper() else "[DATA]"
                                    md_output += f"### {emoji_status} {exec_data.get('manchete', 'Análise de Dados')}\n\n"
                                    
                                    # 2. Diagnóstico
                                    md_output += "**Diagnóstico Detalhado:**\n"
                                    diag_data = json_data.get("diagnostico_por_unidade", {})
                                    for unidade, dados in diag_data.items():
                                        insight = dados.get("insight", "")
                                        situacao = dados.get("situacao", "")
                                        md_output += f"- **{unidade} ({situacao})**: {insight}\n"
                                    md_output += "\n"
                                    
                                    # 3. Estratégia
                                    md_output += "**Estratégia Recomendada:**\n"
                                    strategies = json_data.get("estrategia_recomendada", [])
                                    if isinstance(strategies, list):
                                        for strat in strategies:
                                            md_output += f"- {strat}\n"
                                    elif isinstance(strategies, str):
                                        md_output += f"{strategies}\n"
                                        
                                    logger.info("SAFETY NET: Converteu JSON analítico para Markdown.")
                                    content = md_output

                                # Caso 2: ReAct Pattern (Legacy)
                                elif "action" in json_data and "content" in json_data:
                                    logger.info("SAFETY NET: Extracted content from ReAct JSON pattern.")
                                    content = json_data["content"]
                                
                            except json.JSONDecodeError:
                                pass # Não é JSON válido, segue o baile
                except Exception as e:
                    logger.warning(f"SAFETY NET: Failed to parse potential JSON content: {e}")

                # Caso contrário, retornar resposta de texto normal do LLM
                return {
                    "type": "text",
                    "result": content
                }

            except Exception as e:
                logger.error(f"Exception in agent run loop: {e}", exc_info=True)
                return self._generate_error_response(str(e))

        # FIX: Antes de retornar erro, verificar se há gráfico gerado com sucesso
        # Isso evita perder o trabalho se o LLM não retornou texto mas gerou o gráfico
        logger.warning("Max turns atingido. Verificando se ha grafico para retornar...")

        for msg in reversed(messages):
            if msg.get("role") == "function":
                try:
                    content_str = msg.get("content", "{}")
                    func_content = json.loads(content_str)
                    chart_data = func_content.get("chart_data")

                    if chart_data and func_content.get("status") == "success":
                        logger.info("Grafico encontrado! Retornando mesmo sem texto final do LLM.")
                        if isinstance(chart_data, str):
                            try:
                                chart_data = json.loads(chart_data)
                            except:
                                pass

                        return {
                            "type": "code_result",
                            "result": {
                                "result": func_content.get("summary", {}),
                                "chart_spec": chart_data
                            },
                            "chart_spec": chart_data,
                            "text_override": func_content.get("mensagem")
                                or func_content.get("summary", {}).get("mensagem")
                                or func_content.get("analysis")
                                or "Gráfico gerado com base nos dados atuais."
                        }
                except:
                    continue

        return self._generate_error_response("Maximum conversation turns exceeded.")

    def _create_tool_summary(self, tool_result: Dict[str, Any], func_name: str) -> Dict[str, Any]:
        """
        OPTIMIZATION 2025: Cria resumo compacto de tool response
        Reduz tamanho do contexto enviado ao LLM em 70-90%
        Ref: ChatGPT engineering - context filtering
        """
        if not isinstance(tool_result, dict):
            return tool_result

        # Se é erro, retornar completo
        if "error" in tool_result:
            return tool_result

        summary = {}

        # 1. Agregações - retornar completo (já são pequenas)
        if "resultado_agregado" in tool_result or "valor" in tool_result:
            return tool_result

        # 2. Listas de resultados - enviar apenas amostra + metadados
        if "resultados" in tool_result and isinstance(tool_result["resultados"], list):
            resultados = tool_result["resultados"]
            total = len(resultados)

            # Enviar apenas 3 registros de amostra ao LLM
            summary["resultados"] = resultados[:3] if total > 3 else resultados
            summary["total_resultados"] = total
            summary["_amostra"] = True if total > 3 else False

            # Manter mensagem se existir
            if "mensagem" in tool_result:
                summary["mensagem"] = tool_result["mensagem"]

            logger.info(f"[TOOL SUMMARY] {func_name}: {total} registros → enviando amostra de {len(summary['resultados'])}")
            return summary

        # 3. Chart data - PRESERVAR chart_data completo para renderização no frontend
        # CRITICAL FIX: As ferramentas de gráfico retornam 'chart_data', não 'chart_spec'
        if "chart_data" in tool_result:
            # Preservar chart_data COMPLETO - será usado pelo frontend para renderizar
            summary["status"] = tool_result.get("status", "success")
            summary["chart_type"] = tool_result.get("chart_type", "unknown")
            summary["chart_data"] = tool_result["chart_data"]  # MANTER INTACTO
            summary["mensagem"] = tool_result.get("mensagem", "Gráfico gerado com sucesso")
            
            if "summary" in tool_result:
                summary["summary"] = tool_result["summary"]

            logger.info(f"[TOOL SUMMARY] {func_name}: Chart data preservado (chart_type={summary['chart_type']})")
            return summary

        # 4. Chart spec (legacy) - enviar apenas metadados para o LLM
        if "chart_spec" in tool_result:
            spec = tool_result.get("chart_spec", {})
            summary["chart_type"] = spec.get("type", "unknown")
            summary["chart_generated"] = True
            summary["chart_spec"] = spec  # Preservar chart_spec para o frontend
            summary["mensagem"] = tool_result.get("mensagem", "Gráfico gerado com sucesso")

            # Contar pontos de dados
            if "data" in spec and isinstance(spec["data"], list) and len(spec["data"]) > 0:
                summary["data_points"] = len(spec["data"][0].get("x", []))

            logger.info(f"[TOOL SUMMARY] {func_name}: Chart spec preservado")
            return summary

        # 5. Outros casos - retornar original se pequeno
        return tool_result


    def _generate_error_response(self, error_msg: str) -> Dict[str, Any]:
        message = str(error_msg or "").strip()
        if not message:
            message = "falha temporaria no servico de IA"
        return {
            "type": "text",
            "result": f"Nao foi possivel concluir a analise agora ({message}). Tente novamente em instantes."
        }
