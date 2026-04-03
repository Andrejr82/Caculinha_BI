import json
import logging
import asyncio
import re
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
from backend.app.core.tools.tool_metadata import compose_tool_description
try:
    from backend.app.core.tools.competitive_intelligence_tool import pesquisar_precos_concorrentes
    from backend.app.core.tools.competitive_intelligence_tool import pesquisar_mercado_web
except (ImportError, OSError):
    logger.warning("Competitive Intelligence Tool unavailable. Agent seguirá sem pesquisa concorrencial.")
    pesquisar_precos_concorrentes = None
    pesquisar_mercado_web = None

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
except Exception as e:
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
from backend.app.core.utils.response_sanitizer import clean_response_violations

# Import Tool Scoping - Security 2025
from backend.app.core.utils.tool_scoping import ToolPermissionManager, get_scoped_tools

# Alias para manter compatibilidade com código existente
safe_json_serialize = safe_json_dumps

# System instruction is centrally assembled in app.core.prompts.master_prompt
from backend.app.core.prompts.master_prompt import get_system_prompt
from backend.app.core.prompts.business_contracts import (
    BUSINESS_CONTRACT_RESPONSE_FORMAT,
    normalize_business_contract,
)

class CaculinhaBIAgent:
    """
    Agent responsible for Business Intelligence queries using Groq + Llama
    with local tool orchestration.
    """
    def __init__(
        self,
        llm: Any,
        code_gen_agent: Any,
        field_mapper: FieldMapper,
        user_role: str = "analyst",  # NEW: Role-based tool scoping (default: analyst)
        enable_rag: bool = True  # ASYNC RAG 2025-12-27: Re-enabled with background warming (non-blocking)
    ):
        # llm follows the project adapter contract (SmartLLM/Groq in the runtime principal)
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
        # Mantém o núcleo de tools enxuto e previsível para o roteamento local.
        core_tools = [
            consultar_dados_flexivel,  # Consulta genérica
            gerar_grafico_universal_v2,  # Visualização
            pesquisar_precos_concorrentes,  # Pesquisa concorrencial externa
            pesquisar_mercado_web,  # Pesquisa de mercado aberta (ML, Google Shopping, etc.)
            calcular_abastecimento_une,  # Abastecimento
            calcular_mc_produto,  # Média comum / dimensionamento
            calcular_preco_final_une,  # Política comercial de preço
            encontrar_rupturas_criticas,  # Rupturas
            sugerir_transferencias_automaticas,  # Otimização de transferências
            consultar_dicionario_dados,  # FIX 2026-02-04: Restaurado para schema discovery
            analisar_historico_vendas,  # Histórico de vendas (analysis route)
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

        # 3. Advanced analytics tools (SciPy/Sklearn dependency)
            try:
                from backend.app.core.tools.advanced_analytics_tool import (
                    analise_regressao_vendas,
                    detectar_anomalias_vendas,
                    analise_correlacao_produtos,
                    segmentar_lojas_por_performance,
                    classificar_risco_estoque,
                )
                optional_tools.extend([
                    analise_regressao_vendas,
                    detectar_anomalias_vendas,
                    analise_correlacao_produtos,
                    segmentar_lojas_por_performance,
                    classificar_risco_estoque,
                ])
                logger.info("[OK] Advanced Analytics tools loaded")
            except ImportError as e:
                logger.warning(f"[WARNING] Advanced Analytics tools missing (SciPy/Sklearn issue): {e}")

        # 4. Basket / Promotion / Margin Tools
            try:
                from backend.app.core.tools.basket_tools import (
                    analisar_cesta_compras,
                    simular_promocao_cesta,
                    minerar_cestas_frequentes,
                )
                optional_tools.extend([
                    analisar_cesta_compras,
                    simular_promocao_cesta,
                    minerar_cestas_frequentes,
                ])
                logger.info("[OK] Basket analysis tools loaded")
            except ImportError as e:
                logger.warning(f"[WARNING] Basket analysis tools missing: {e}")

        # 5. RAG Tools (LangChain/FAISS/Torch dependency)
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

        # Convert tool schemas to the internal function-declaration wrapper used by the adapters.
        self.tool_declarations = self._build_tool_declarations(self.bi_tools)
        
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
                
            system_prompt_template = get_system_prompt()

            # Substituir no template usando o placeholder canônico
            if "[SCHEMA_INJECTION_POINT]" in system_prompt_template:
                self.system_prompt = system_prompt_template.replace(
                    "[SCHEMA_INJECTION_POINT]", 
                    schema_str
                )
                logger.info(f"[OK] Dynamic Schema Injection: Sucesso ({len(cols)} colunas injetadas)")
            else:
                # Fallback: se o placeholder não existir, anexar ao final
                logger.warning("[WARNING] Placeholder [SCHEMA_INJECTION_POINT] não encontrado. Anexando schema ao final do prompt.")
                self.system_prompt = system_prompt_template + "\n\n## DADOS DISPONIVEIS\n" + schema_str
             
        except Exception as e:
            logger.warning(f"[ERROR] Dynamic Schema Injection Failed: {e}. Using static prompt.")
            self.system_prompt = get_system_prompt()

        if settings.DEV_FAST_MODE:
            self.system_prompt += (
                "\n\n## MODO DEV FAST\n"
                "- Responda objetivamente em no máximo 8 linhas.\n"
                "- Evite chamadas de ferramenta caras, a menos que sejam estritamente necessárias.\n"
            )


    def _build_tool_declarations(self, tools: List[BaseTool]) -> Dict[str, List[Dict[str, Any]]]:
        declarations = []
        for tool in tools:
            # Normalize tool metadata for both LangChain tools and plain callables.
            tool_name = getattr(tool, "name", None) or getattr(tool, "__name__", None)
            fallback_description = getattr(tool, "description", None) or getattr(tool, "__doc__", "") or ""
            if not tool_name:
                logger.warning(f"Skipping tool without resolvable name: {type(tool)}")
                continue

            # Generate schema using LangChain's standardized method when available.
            # For plain callables, fallback to empty object schema.
            schema = {}
            if hasattr(tool, "get_input_schema"):
                try:
                    schema = tool.get_input_schema().model_json_schema()
                except AttributeError:
                    if hasattr(tool, "args_schema") and tool.args_schema:
                        if hasattr(tool.args_schema, "schema"):
                            schema = tool.args_schema.schema()
                        else:
                            schema = {}
            elif hasattr(tool, "args_schema") and tool.args_schema:
                if hasattr(tool.args_schema, "schema"):
                    schema = tool.args_schema.schema()
            
            # Clean schema to be adapter-friendly (remove noisy metadata and unsupported branches)
            cleaned_schema = self._clean_schema(schema)
            
            # Ensure 'properties' and 'required' are present if parameters exist
            parameters = {
                "type": "object",
                "properties": cleaned_schema.get("properties", {}),
                "required": cleaned_schema.get("required", [])
            }

            declarations.append({
                "name": str(tool_name),
                "description": compose_tool_description(str(tool_name), str(fallback_description).strip()),
                "parameters": parameters
            })
        
        return {"function_declarations": declarations}

    def _clean_response_violations(self, content: str, context_type: str = "generic") -> str:
        """Sanitiza resposta técnica para narrativa legível."""
        return clean_response_violations(content=content, context_type=context_type)

    def _clean_context7_violations(self, content: str, context_type: str = "generic") -> str:
        """Alias legado para manter compatibilidade com chamadas antigas."""
        return self._clean_response_violations(content=content, context_type=context_type)

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
        Recursively cleans Pydantic JSON Schema for function-calling compatibility.
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
            non_null_options = [opt for opt in options if opt.get("type") != "null"]

            # Se houver múltiplos tipos primitivos (ex: boolean|string), usamos string
            # para evitar schemas frágeis entre adapters OpenAI-like.
            primitive_types = {
                opt.get("type")
                for opt in non_null_options
                if isinstance(opt, dict) and opt.get("type") in {"string", "boolean", "integer", "number"}
            }
            if len(primitive_types) > 1:
                new_schema["type"] = "string"
            else:
                valid_option = non_null_options[0] if non_null_options else None
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

        # Compatibilidade defensiva para consulta flexível (Groq costuma serializar tipos como string).
        if func_name == "consultar_dados_flexivel":
            # ordem_desc: aceitar "true"/"false"/"1"/"0"/etc
            if "ordem_desc" in args:
                raw_order = args.get("ordem_desc")
                if isinstance(raw_order, str):
                    args["ordem_desc"] = raw_order.strip().lower() in {"true", "1", "yes", "sim", "y"}
                elif raw_order is None:
                    args["ordem_desc"] = True

            # Converte JSON-string de filtros para dict quando apropriado
            if "filtros" in args and isinstance(args.get("filtros"), str):
                raw_filters = args["filtros"].strip()
                if raw_filters.startswith("{") and raw_filters.endswith("}"):
                    try:
                        args["filtros"] = json.loads(raw_filters)
                    except Exception:
                        pass

            # Converte colunas/agrupar_por de JSON-string para lista quando apropriado
            for list_key in ("colunas", "agrupar_por"):
                raw_value = args.get(list_key)
                if isinstance(raw_value, str):
                    raw_value = raw_value.strip()
                    if raw_value.startswith("[") and raw_value.endswith("]"):
                        try:
                            parsed = json.loads(raw_value)
                            if isinstance(parsed, list):
                                args[list_key] = parsed
                        except Exception:
                            pass

        # Compatibilidade para ferramentas de previsão/analytics.
        if func_name in {"prever_demanda", "prever_demanda_sazonal", "analise_regressao_vendas", "detectar_anomalias_vendas"}:
            if "produto_codigo" in args and "produto_id" not in args:
                args["produto_id"] = str(args.pop("produto_codigo"))
            if "dias_previsao" in args and "periodo_dias" not in args:
                args["periodo_dias"] = int(args.pop("dias_previsao"))
            if "dias_analise" in args and "periodo_dias" not in args:
                args["periodo_dias"] = int(args.pop("dias_analise"))
            if "produto_id" in args and args["produto_id"] is not None:
                args["produto_id"] = str(args["produto_id"])

        # Compatibilidade para ferramentas de cálculo/otimização.
        if func_name == "calcular_eoq":
            if "produto_codigo" in args and "produto_id" not in args:
                args["produto_id"] = str(args.pop("produto_codigo"))
            if "produto_id" in args and args["produto_id"] is not None:
                args["produto_id"] = str(args["produto_id"])

        if func_name == "calcular_mc_produto":
            if "produto_codigo" in args and "produto_id" not in args:
                try:
                    args["produto_id"] = int(args.pop("produto_codigo"))
                except (TypeError, ValueError):
                    args.pop("produto_codigo", None)
            if "une" in args and "une_id" not in args:
                try:
                    args["une_id"] = int(args.pop("une"))
                except (TypeError, ValueError):
                    args.pop("une", None)

        if func_name == "alocar_estoque_lojas":
            if "produto_codigo" in args and "produto_id" not in args:
                args["produto_id"] = str(args.pop("produto_codigo"))
            if "produto_id" in args and args["produto_id"] is not None:
                args["produto_id"] = str(args["produto_id"])

        if func_name == "analisar_produto_todas_lojas":
            if "produto_id" in args and "produto_codigo" not in args:
                try:
                    args["produto_codigo"] = int(args.pop("produto_id"))
                except (TypeError, ValueError):
                    args.pop("produto_id", None)
            elif "produto_codigo" in args:
                try:
                    args["produto_codigo"] = int(args["produto_codigo"])
                except (TypeError, ValueError):
                    args.pop("produto_codigo", None)

        if func_name == "calcular_abastecimento_une":
            if "une" in args and "une_id" not in args:
                args["une_id"] = str(args.pop("une"))
            elif "une_id" in args and args["une_id"] is not None:
                args["une_id"] = str(args["une_id"])

        if func_name == "analisar_historico_vendas":
            if "produto_codigo" in args and "codigo_produto" not in args:
                try:
                    args["codigo_produto"] = int(args.pop("produto_codigo"))
                except (TypeError, ValueError):
                    args.pop("produto_codigo", None)
            if "une" in args and "codigo_une" not in args:
                try:
                    args["codigo_une"] = int(args.pop("une"))
                except (TypeError, ValueError):
                    args.pop("une", None)
            if "codigo_produto" in args and args["codigo_produto"] is not None:
                try:
                    args["codigo_produto"] = int(args["codigo_produto"])
                except (TypeError, ValueError):
                    args.pop("codigo_produto", None)
            if "codigo_une" in args and args["codigo_une"] is not None:
                try:
                    args["codigo_une"] = int(args["codigo_une"])
                except (TypeError, ValueError):
                    args.pop("codigo_une", None)

        if func_name == "analise_correlacao_produtos":
            if "produto_codigo" in args and "produtos_ids" not in args:
                args["produtos_ids"] = [str(args.pop("produto_codigo"))]
            raw_produtos = args.get("produtos_ids")
            if raw_produtos is not None:
                if isinstance(raw_produtos, str):
                    args["produtos_ids"] = [p.strip() for p in raw_produtos.split(",") if p.strip()]
                elif isinstance(raw_produtos, list):
                    args["produtos_ids"] = [str(p) for p in raw_produtos if str(p).strip()]

        if func_name in {"analisar_cesta_compras", "simular_promocao_cesta"}:
            raw_items = args.get("itens")
            if isinstance(raw_items, str):
                try:
                    args["itens"] = json.loads(raw_items)
                except json.JSONDecodeError:
                    pass
            raw_targets = args.get("produto_ids_alvo")
            if isinstance(raw_targets, str):
                try:
                    parsed_targets = json.loads(raw_targets)
                    if isinstance(parsed_targets, list):
                        args["produto_ids_alvo"] = [str(v) for v in parsed_targets]
                    else:
                        args["produto_ids_alvo"] = [v.strip() for v in raw_targets.split(",") if v.strip()]
                except json.JSONDecodeError:
                    args["produto_ids_alvo"] = [v.strip() for v in raw_targets.split(",") if v.strip()]

        if func_name == "minerar_cestas_frequentes":
            raw_transactions = args.get("transacoes")
            if isinstance(raw_transactions, str):
                try:
                    args["transacoes"] = json.loads(raw_transactions)
                except json.JSONDecodeError:
                    pass

        return args

    def _execute_tool_with_recovery(self, tool_to_run: Any, func_name: str, func_args: Dict[str, Any]) -> Any:
        """
        Executa ferramenta com normalização e uma tentativa de recuperação.
        """
        normalized_args = self._normalize_tool_arguments(func_name, func_args)

        def _invoke(tool_obj: Any, args: Dict[str, Any]) -> Any:
            if hasattr(tool_obj, "invoke"):
                return tool_obj.invoke(args)
            if callable(tool_obj):
                return tool_obj(**args)
            raise TypeError(f"Ferramenta '{func_name}' não é invocável")

        try:
            return _invoke(tool_to_run, normalized_args)
        except Exception as first_error:
            # Retry defensivo para casos de validação estrita de tipo.
            retry_args = dict(normalized_args)
            if "limite" in retry_args and retry_args["limite"] is not None:
                retry_args["limite"] = str(retry_args["limite"])

            logger.warning(
                f"Tool {func_name} falhou na 1a tentativa ({first_error}). "
                f"Tentando recuperação com argumentos coercidos."
            )
            return _invoke(tool_to_run, retry_args)

    def _tool_name(self, tool_obj: Any) -> str:
        return str(getattr(tool_obj, "name", None) or getattr(tool_obj, "__name__", "") or "")

    def _find_tool_by_name(self, name: str) -> Any:
        for t in self.bi_tools:
            if self._tool_name(t) == name:
                return t
        return None

    def _is_chart_request(self, query: str) -> bool:
        q = (query or "").lower()
        return any(k in q for k in ["gráfico", "grafico", "plot", "visual", "barra", "pizza", "linha"])

    def _is_dashboard_request(self, query: str) -> bool:
        q = (query or "").lower()
        return any(k in q for k in ["dashboard", "painel", "kpi", "kpis", "indicadores"])

    def _infer_chart_breakdown(self, query: str) -> Optional[str]:
        from backend.app.core.utils.query_router import extract_chart_breakdown

        return extract_chart_breakdown(query)

    def _is_grounded_product_store_query(self, query: str) -> bool:
        from backend.app.core.utils.query_router import (
            extract_product_code,
            extract_product_store_ranking_request,
            is_product_rupture_query,
            is_product_store_leader_query,
        )

        q = (query or "").lower()
        product = extract_product_code(query)
        if not product:
            return False

        if is_product_rupture_query(query):
            return True
        if is_product_store_leader_query(query):
            return True
        if extract_product_store_ranking_request(query):
            return True

        store_terms = any(token in q for token in ["loja", "lojas", "une", "unes"])
        objective_terms = any(
            token in q for token in ["vende", "vendem", "venda", "vendas", "estoque", "ruptura", "rupturas"]
        )
        return store_terms and objective_terms

    def _is_small_talk_query(self, query: str) -> bool:
        import re

        q = (query or "").strip().lower()
        if not q:
            return False

        # Evita capturar perguntas de negócio que contenham palavras comuns
        business_terms = [
            "venda", "estoque", "une", "loja", "segmento", "produto", "gráfico", "grafico", "sql", "python",
            "item", "itens", "promoção", "promocao", "ação", "acao", "combo", "cesta", "cross-sell",
            "cross sell", "combina", "combinam", "compar", "margem", "desconto", "eoq",
        ]
        if any(t in q for t in business_terms):
            return False

        exact_small_talk = {
            "oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "tudo bem", "como vai", "ajuda", "help",
            "qual é o seu nome", "qual e o seu nome", "seu nome", "quem é você", "quem e voce", "quem é voce",
            "o que você faz", "o que voce faz",
        }
        if q in exact_small_talk:
            return True

        normalized = re.sub(r"\s+", " ", q)
        explicit_patterns = [
            r"^(?:oi|olá|ola|bom dia|boa tarde|boa noite)(?:[!.?, ]*)$",
            r"^(?:oi|olá|ola|bom dia|boa tarde|boa noite)\b.{0,24}$",
            r"^(?:qual é o seu nome|qual e o seu nome|seu nome|quem é você|quem e voce|quem é voce)$",
            r"^(?:o que você faz|o que voce faz|ajuda|help|tudo bem|como vai)$",
        ]
        return any(re.search(pattern, normalized, re.IGNORECASE) for pattern in explicit_patterns)

    def _small_talk_response(self, query: str) -> Dict[str, Any]:
        q = (query or "").strip().lower()
        if "nome" in q:
            msg = "Meu nome é Caçulinha. Posso ajudar com análises comerciais, vendas, estoque e concorrência."
        elif any(k in q for k in ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite"]):
            msg = "Olá! Sou o Caçulinha. Me diga o que você quer analisar (ex.: vendas por UNE, ruptura, preços de concorrentes)."
        else:
            msg = (
                "Posso te ajudar com análises de vendas, estoque, transferências e pesquisa concorrencial. "
                "Exemplo: 'total de vendas por UNE no segmento ARTES no RJ'."
            )
        return {"type": "text", "result": {"mensagem": msg}}

    def _normalize_progress_tool(self, tool_name: str) -> str:
        mapping = {
            "Pensando": "system.thinking",
            "Processando resposta": "system.finalizing",
            "calculation_sandbox": "tool.calculation_sandbox",
            "consultar_dados_flexivel": "tool.data_query",
            "consultar_dados_gerais": "tool.metadata_query",
            "gerar_grafico_universal": "tool.chart",
            "gerar_grafico_universal_v2": "tool.chart",
            "gerar_dashboard_executivo": "tool.dashboard",
            "pesquisar_precos_concorrentes": "tool.competitive_research",
            "pesquisar_mercado_web": "tool.market_research",
        }
        return mapping.get(str(tool_name or ""), f"tool.{str(tool_name or 'generic')}")

    async def _emit_progress(self, on_progress: Optional[Callable[[Dict[str, Any]], Awaitable[None]]], tool_name: str, status: str) -> None:
        if not on_progress:
            return
        await on_progress(
            {
                "type": "tool_progress",
                "tool": self._normalize_progress_tool(tool_name),
                "status": status,
            }
        )

    def _resolve_llm_task_type(self, intent: Optional[Any], tool_name: str, query: str) -> str:
        q = (query or "").lower()
        normalized_tool = str(tool_name or "").strip().lower()
        intent_value = str(getattr(intent, "value", intent or "")).strip().lower()

        if normalized_tool in {"pesquisar_precos_concorrentes", "pesquisar_mercado_web"}:
            return "market_research"
        if normalized_tool in {"simular_promocao_cesta", "analisar_cesta_compras", "minerar_cestas_frequentes"}:
            return "basket"
        if normalized_tool in {
            "calcular_abastecimento_une",
            "encontrar_rupturas_criticas",
            "calcular_eoq",
            "alocar_estoque_lojas",
            "sugerir_transferencias_automaticas",
        }:
            return "inventory"
        if normalized_tool == "gerar_dashboard_executivo":
            return "dashboard"
        if normalized_tool in {"gerar_grafico_universal_v2", "gerar_grafico_universal"}:
            return "visualization"

        if intent_value:
            return intent_value

        if any(k in q for k in ["pesquisa de mercado", "concorrente", "cotação", "cotacao"]):
            return "market_research"
        if any(k in q for k in ["dashboard", "gráfico", "grafico", "chart"]):
            return "visualization"
        if any(k in q for k in ["promoção", "promocao", "desconto", "bundle", "leve", "margem", "preço", "preco"]):
            return "promotion"
        if any(k in q for k in ["cesta", "ticket medio", "cross-sell", "cross sell", "afinidade", "combo"]):
            return "basket"
        if any(k in q for k in ["ruptura", "estoque", "abastecimento", "transferencia", "reposição", "reposicao"]):
            return "inventory"
        if any(k in q for k in ["eoq", "lote econômico", "lote economico", "sensibilidade", "simulação", "simulacao"]):
            return "calculation"
        if any(k in q for k in ["previsão", "previsao", "demanda sazonal", "sazonalidade"]):
            return "forecasting"
        return "analysis"

    def _llm_get_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[Dict[str, Any]],
        task_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Chamada compatível para adapters antigos (sem task_type) e SmartLLM (com task_type).
        """
        try:
            return self.llm.get_completion(messages, tools=tools, task_type=task_type)
        except TypeError:
            return self.llm.get_completion(messages, tools=tools)

    def _llm_generate_with_history(
        self,
        messages: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
        task_type: Optional[str] = None,
        **kwargs,
    ) -> str:
        try:
            return self.llm.generate_with_history(
                messages,
                system_instruction=system_instruction,
                task_type=task_type,
                **kwargs,
            )
        except TypeError:
            try:
                return self.llm.generate_with_history(messages, system_instruction, **kwargs)
            except TypeError:
                fallback = self._llm_get_completion(messages, tools=kwargs.get("tools"), task_type=task_type)
                return str(fallback.get("content", "")) if isinstance(fallback, dict) else str(fallback)

    @staticmethod
    def _extract_chart_title(chart_data: Any) -> Optional[str]:
        if not isinstance(chart_data, dict):
            return None
        layout = chart_data.get("layout")
        if not isinstance(layout, dict):
            return None
        title = layout.get("title")
        if isinstance(title, dict):
            text = str(title.get("text") or "").strip()
            return text or None
        if isinstance(title, str):
            return title.strip() or None
        return None

    def _build_visual_contract_payload(
        self,
        *,
        chart_data: Any = None,
        chart_summary: Any = None,
        table_rows: Any = None,
        dashboard_spec: Any = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if isinstance(chart_summary, dict) and chart_summary:
            payload["chart_summary"] = chart_summary
        chart_title = self._extract_chart_title(chart_data)
        if chart_title:
            payload["chart_title"] = chart_title
        if isinstance(chart_data, dict):
            traces = chart_data.get("data")
            if isinstance(traces, list):
                payload["chart_trace_count"] = len(traces)
                sample_traces = []
                for trace in traces[:3]:
                    if not isinstance(trace, dict):
                        continue
                    sample_entry = {
                        "name": str(trace.get("name") or "").strip() or None,
                        "type": str(trace.get("type") or "").strip() or None,
                    }
                    x_values = trace.get("x")
                    if isinstance(x_values, list) and x_values:
                        sample_entry["x_sample"] = x_values[:5]
                    y_values = trace.get("y")
                    if isinstance(y_values, list) and y_values:
                        sample_entry["y_sample"] = y_values[:5]
                    sample_traces.append({k: v for k, v in sample_entry.items() if v not in (None, "", [])})
                if sample_traces:
                    payload["chart_traces"] = sample_traces
        if isinstance(table_rows, list) and table_rows:
            payload["table_row_count"] = len(table_rows)
            first_row = table_rows[0] if isinstance(table_rows[0], dict) else {}
            if isinstance(first_row, dict) and first_row:
                payload["table_columns"] = list(first_row.keys())[:8]
            payload["table_sample_rows"] = table_rows[:5]
        if isinstance(dashboard_spec, dict) and dashboard_spec:
            payload["dashboard_title"] = str(dashboard_spec.get("title") or "").strip() or None
            widgets = dashboard_spec.get("widgets")
            if isinstance(widgets, list):
                payload["dashboard_widget_count"] = len(widgets)
            filters = dashboard_spec.get("filters")
            if isinstance(filters, list) and filters:
                payload["dashboard_filters"] = filters[:5]
            payload = {k: v for k, v in payload.items() if v not in (None, "", [])}
        return payload

    @staticmethod
    def _render_business_contract_markdown(contract: Dict[str, Any]) -> Optional[str]:
        if not isinstance(contract, dict):
            return None
        headline = str(contract.get("headline") or "").strip()
        summary = str(contract.get("summary") or "").strip()
        findings = contract.get("key_findings")
        actions = contract.get("recommended_actions")
        if not headline and not summary and not findings and not actions:
            return None

        lines: List[str] = []
        if headline:
            lines.append(f"### {headline}")
            lines.append("")
        if summary:
            lines.append(summary)
            lines.append("")
        if isinstance(findings, list) and findings:
            lines.append("**Principais achados**")
            for item in findings[:4]:
                text = str(item or "").strip()
                if text:
                    lines.append(f"- {text}")
            lines.append("")
        if isinstance(actions, list) and actions:
            lines.append("**Ações recomendadas**")
            for item in actions[:3]:
                text = str(item or "").strip()
                if text:
                    lines.append(f"- {text}")
        return "\n".join(line for line in lines if line is not None).strip() or None

    def _generate_structured_visual_narrative(
        self,
        *,
        user_query: str,
        task_type: Optional[str],
        fallback_text: str,
        chart_data: Any = None,
        chart_summary: Any = None,
        table_rows: Any = None,
        dashboard_spec: Any = None,
    ) -> str:
        payload = self._build_visual_contract_payload(
            chart_data=chart_data,
            chart_summary=chart_summary,
            table_rows=table_rows,
            dashboard_spec=dashboard_spec,
        )
        if not payload:
            return fallback_text

        system_message = (
            "Voce transforma resultados de BI em resumo executivo objetivo para varejo. "
            "Responda APENAS em JSON valido com as chaves: "
            "headline, summary, key_findings, recommended_actions. "
            "headline e summary devem ser strings. key_findings e recommended_actions devem ser listas de strings. "
            "Use linguagem de negocio, mencione impacto operacional e nao invente numeros."
        )
        user_message = (
            f"Pergunta do usuario: {user_query}\n"
            f"Texto livre atual: {fallback_text}\n"
            f"Payload de apoio: {json.dumps(payload, ensure_ascii=False)}"
        )
        try:
            raw_output = self._llm_generate_with_history(
                [{"role": "user", "content": user_message}],
                system_instruction=system_message,
                task_type=task_type or "analysis",
                json_mode=True,
                response_format=BUSINESS_CONTRACT_RESPONSE_FORMAT,
            )
            parsed = normalize_business_contract(raw_output)
            structured_markdown = self._render_business_contract_markdown(parsed)
            return structured_markdown or fallback_text
        except Exception as exc:
            logger.warning("Falha ao gerar narrativa estruturada em JSON mode: %s", exc)
            return fallback_text

    def _extract_numeric_hint(self, query: str, patterns: List[str]) -> Optional[float]:
        import re
        q = (query or "").lower()
        for pattern in patterns:
            match = re.search(pattern, q)
            if not match:
                continue
            try:
                raw = str(match.group(1)).replace(",", ".")
                return float(raw)
            except Exception:
                continue
        return None

    def _extract_percent_hint(self, query: str) -> Optional[float]:
        import re
        q = (query or "").lower()
        match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", q)
        if not match:
            return None
        try:
            return float(str(match.group(1)).replace(",", ".")) / 100.0
        except Exception:
            return None

    def _extract_payment_term_hint(self, query: str) -> Optional[str]:
        q = (query or "").lower()
        if any(token in q for token in ["à vista", "a vista", "avista", "vista"]):
            return "vista"
        for term in ("30d", "90d", "120d"):
            if term in q:
                return term
        return None

    def _extract_ranking_hint(self, query: str) -> Optional[int]:
        import re
        q = (query or "").lower()
        match = re.search(r"ranking\s+(\d)", q)
        if not match:
            return None
        try:
            return int(match.group(1))
        except Exception:
            return None

    def _detect_calculation_mode(self, query: str) -> str:
        q = (query or "").lower()
        if "desconto" in q and "margem" in q:
            return "discount_margin"
        if any(token in q for token in ["eoq", "lote econômico", "lote economico", "quanto comprar"]):
            return "eoq"
        if "markup" in q or "mark-up" in q:
            return "markup"
        if any(token in q for token in ["giro de estoque", "giro do estoque", "giro"]):
            return "inventory_turnover"
        if any(token in q for token in ["cobertura em dias", "dias de cobertura", "cobertura de estoque", "cobertura"]):
            return "stock_coverage"
        if any(token in q for token in ["margem", "margem de contribuição", "margem de contribuicao"]):
            return "margin"
        return "generic"

    def _is_tool_failure_result(self, tool_result: Any) -> bool:
        if not isinstance(tool_result, dict):
            return False

        if tool_result.get("error"):
            return True

        if "success" in tool_result and bool(tool_result.get("success")) is False:
            return True

        status = str(tool_result.get("status", "")).strip().lower()
        if status in {"error", "failed", "failure"}:
            return True

        if status and status not in {"success", "ok"}:
            return True

        return False

    def _is_tool_success_result(self, tool_result: Any) -> bool:
        if not isinstance(tool_result, dict):
            return False

        if self._is_tool_failure_result(tool_result):
            return False

        if "success" in tool_result:
            return bool(tool_result.get("success"))

        status = str(tool_result.get("status", "")).strip().lower()
        if status in {"success", "ok"}:
            return True

        if len(tool_result.get("resultados", []) or []) > 0:
            return True

        return False

    def _is_effectively_empty_tool_result(self, tool_name: str, tool_result: Any) -> bool:
        if not isinstance(tool_result, dict):
            return False

        normalized_tool = str(tool_name or "").strip().lower()
        message = str(tool_result.get("mensagem") or tool_result.get("message") or "").lower()
        no_data_markers = (
            "nenhum dado encontrado",
            "não encontrei dados",
            "nao encontrei dados",
            "não encontrei resultados",
            "nao encontrei resultados",
            "sem dados",
            "sem evidência",
            "sem evidencia",
        )
        if any(marker in message for marker in no_data_markers):
            return True

        if normalized_tool in {"gerar_grafico_universal_v2", "gerar_dashboard_executivo"}:
            chart_data = tool_result.get("chart_data")
            if isinstance(chart_data, str) and chart_data.strip():
                try:
                    chart_data = json.loads(chart_data)
                except json.JSONDecodeError:
                    # Algumas ferramentas retornam chart_data como JSON string.
                    # Se o payload existe, não devemos forçar fallback prematuro.
                    return False
            if isinstance(chart_data, dict):
                traces = chart_data.get("data")
                if isinstance(traces, list) and len(traces) > 0:
                    return False

            dashboard_spec = tool_result.get("dashboard_spec")
            if isinstance(dashboard_spec, str) and dashboard_spec.strip():
                try:
                    dashboard_spec = json.loads(dashboard_spec)
                except json.JSONDecodeError:
                    return False
            if isinstance(dashboard_spec, dict):
                widgets = dashboard_spec.get("widgets")
                if isinstance(widgets, list) and len(widgets) > 0:
                    return False

            return True

        if "resultados" in tool_result and len(tool_result.get("resultados", []) or []) == 0:
            return True

        if "total_resultados" in tool_result and int(tool_result.get("total_resultados") or 0) == 0:
            return True

        if "itens" in tool_result and len(tool_result.get("itens", []) or []) == 0:
            return True

        if "total_itens" in tool_result and int(tool_result.get("total_itens") or 0) == 0:
            return True

        return False

    def _should_attempt_semantic_recovery(
        self,
        user_query: str,
        tool_name: str,
        tool_result: Any = None,
        tool_error: Optional[Exception] = None,
    ) -> bool:
        if tool_error is not None:
            return True

        if self._is_tool_failure_result(tool_result):
            return True

        if self._is_effectively_empty_tool_result(tool_name, tool_result):
            normalized_tool = str(tool_name or "").strip().lower()
            if normalized_tool in {
                "gerar_dashboard_executivo",
                "gerar_grafico_universal_v2",
                "consultar_dados_flexivel",
                "pesquisar_precos_concorrentes",
                "pesquisar_mercado_web",
            }:
                return True

        return False

    def _infer_semantic_fallback_tools(
        self,
        primary_tool_name: str,
        configured_fallbacks: Optional[List[str]] = None,
        user_query: Optional[str] = None,
    ) -> List[str]:
        grounded_product_store_query = self._is_grounded_product_store_query(user_query or "")
        fallback_order: List[str] = list(configured_fallbacks or [])
        if grounded_product_store_query and fallback_order:
            allowed_for_grounded = {"consultar_dados_flexivel", "analisar_produto_todas_lojas"}
            if "ruptur" in str(user_query or "").lower():
                allowed_for_grounded = {"analisar_produto_todas_lojas"}
            fallback_order = [
                tool_name for tool_name in fallback_order
                if str(tool_name or "").strip() in allowed_for_grounded
            ]
        if user_query:
            if grounded_product_store_query:
                is_product_rupture = "ruptur" in str(user_query or "").lower()
                if str(primary_tool_name or "") == "consultar_dados_flexivel":
                    fallback_order.extend(["analisar_produto_todas_lojas"])
                elif str(primary_tool_name or "") == "analisar_produto_todas_lojas" and not is_product_rupture:
                    fallback_order.extend(["consultar_dados_flexivel"])
            elif self._is_dashboard_request(user_query):
                fallback_order.extend(["gerar_grafico_universal_v2", "consultar_dados_flexivel"])
            elif self._is_chart_request(user_query):
                fallback_order.extend(["gerar_grafico_universal_v2", "consultar_dados_flexivel"])

            if self._is_specific_competitor_query(user_query):
                fallback_order.extend(["pesquisar_precos_concorrentes", "pesquisar_mercado_web"])
            elif self._is_market_research_query(user_query):
                fallback_order.extend(["pesquisar_mercado_web", "pesquisar_precos_concorrentes"])

        default_map = {
            "gerar_dashboard_executivo": ["gerar_grafico_universal_v2", "consultar_dados_flexivel"],
            "gerar_grafico_universal_v2": ["consultar_dados_flexivel"],
            "consultar_dados_flexivel": ["gerar_grafico_universal_v2"],
            "analisar_produto_todas_lojas": ["consultar_dados_flexivel"],
            "pesquisar_precos_concorrentes": ["pesquisar_mercado_web", "consultar_dados_flexivel"],
            "pesquisar_mercado_web": ["pesquisar_precos_concorrentes", "consultar_dados_flexivel"],
            "calcular_eoq": ["consultar_dados_flexivel"],
        }
        if grounded_product_store_query:
            default_map["consultar_dados_flexivel"] = ["analisar_produto_todas_lojas"]
            if "ruptur" in str(user_query or "").lower():
                default_map["analisar_produto_todas_lojas"] = []
        for candidate in default_map.get(str(primary_tool_name or ""), []):
            fallback_order.append(candidate)

        deduped: List[str] = []
        seen = set()
        for tool in fallback_order:
            normalized = str(tool or "").strip()
            if not normalized or normalized in seen or normalized == primary_tool_name:
                continue
            seen.add(normalized)
            deduped.append(normalized)
        return deduped

    def _build_semantic_fallback_params(
        self,
        user_query: str,
        fallback_tool_name: str,
        primary_tool_params: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        params = dict(primary_tool_params or {})
        if fallback_tool_name == "gerar_grafico_universal_v2":
            params = {
                "descricao": user_query,
                "tipo_grafico": params.get("tipo_grafico", "bar"),
                "limite": params.get("limite", 50),
            }
            segment = self._extract_segment_from_query(user_query)
            if segment:
                params["filtro_segmento"] = segment
            une = self._extract_une_from_query(user_query)
            if une:
                params["filtro_une"] = une
            breakdown = self._infer_chart_breakdown(user_query)
            if breakdown:
                params["quebra_por"] = breakdown
        elif fallback_tool_name == "consultar_dados_flexivel":
            params = params if isinstance(params, dict) else {}
            segment = self._extract_segment_from_query(user_query)
            une = self._extract_une_from_query(user_query)
            breakdown = self._infer_chart_breakdown(user_query)

            if self._is_chart_request(user_query) or self._is_dashboard_request(user_query):
                group_map = {
                    "SEGMENTO": ["NOMESEGMENTO"],
                    "LOJA": ["UNE"],
                    "CATEGORIA": ["NOMECATEGORIA"],
                    "GRUPO": ["NOMEGRUPO"],
                    "PRODUTO": ["NOME"],
                    "FABRICANTE": ["NOMEFABRICANTE"],
                }
                params["agregacao"] = "SUM"
                params["coluna_agregacao"] = "VENDA_30DD"
                params["agrupar_por"] = group_map.get(str(breakdown or "SEGMENTO").upper(), ["NOMESEGMENTO"])
                params["ordenar_por"] = "valor"
                params["ordem_desc"] = True
                params["limite"] = params.get("limite", "50")
                filtros = params.get("filtros", {})
                if not isinstance(filtros, dict):
                    filtros = {}
                if segment:
                    filtros["NOMESEGMENTO"] = segment
                if une:
                    filtros["UNE"] = int(une) if str(une).isdigit() else une
                if filtros:
                    params["filtros"] = filtros
            else:
                params.setdefault("colunas", ["PRODUTO", "NOME", "UNE", "VENDA_30DD", "ESTOQUE_UNE"])
                params.setdefault("limite", "50")
        elif fallback_tool_name == "pesquisar_precos_concorrentes":
            params = {
                "descricao_produto": params.get("descricao_produto") or params.get("termo_pesquisa") or user_query,
                "limite": params.get("limite", "10"),
                "estado": params.get("estado") or self._extract_state_from_query(user_query) or "RJ",
            }
            segment = self._extract_segment_from_query(user_query)
            competitors = self._extract_competitors_from_query(user_query)
            if segment:
                params["segmento"] = segment
            if competitors:
                params["concorrentes"] = competitors
        elif fallback_tool_name == "pesquisar_mercado_web":
            params = {
                "termo_pesquisa": params.get("termo_pesquisa") or params.get("descricao_produto") or user_query,
                "limite": params.get("limite", "15"),
            }
        return self._normalize_tool_arguments(fallback_tool_name, params)

    async def _execute_semantic_tool_fallback(
        self,
        user_query: str,
        primary_tool_name: str,
        primary_tool_params: Optional[Dict[str, Any]],
        fallback_tools: Optional[List[str]],
        on_progress: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    ) -> Optional[Dict[str, Any]]:
        candidates = self._infer_semantic_fallback_tools(
            primary_tool_name,
            fallback_tools,
            user_query=user_query,
        )
        for fallback_tool_name in candidates:
            tool_to_run = self._find_tool_by_name(fallback_tool_name)
            if tool_to_run is None:
                continue

            fallback_params = self._build_semantic_fallback_params(user_query, fallback_tool_name, primary_tool_params)
            logger.warning(
                f"[TOOL-RECOVERY] {primary_tool_name} falhou; tentando fallback semântico {fallback_tool_name} "
                f"com params={fallback_params}"
            )
            try:
                await self._emit_progress(on_progress, fallback_tool_name, "executing")
                fallback_result = await asyncio.to_thread(
                    self._execute_tool_with_recovery,
                    tool_to_run,
                    fallback_tool_name,
                    fallback_params,
                )
            except Exception as fallback_error:
                logger.warning(
                    f"[TOOL-RECOVERY] fallback {fallback_tool_name} também falhou: {fallback_error}"
                )
                continue

            if self._is_tool_failure_result(fallback_result) or self._is_effectively_empty_tool_result(
                fallback_tool_name,
                fallback_result,
            ):
                logger.warning(
                    f"[TOOL-RECOVERY] fallback {fallback_tool_name} retornou erro ou resultado vazio."
                )
                continue

            return {
                "tool_name": fallback_tool_name,
                "tool_params": fallback_params,
                "tool_result": fallback_result,
            }
        return None

    def _execute_semantic_tool_fallback_sync(
        self,
        user_query: str,
        primary_tool_name: str,
        primary_tool_params: Optional[Dict[str, Any]],
        fallback_tools: Optional[List[str]],
    ) -> Optional[Dict[str, Any]]:
        candidates = self._infer_semantic_fallback_tools(
            primary_tool_name,
            fallback_tools,
            user_query=user_query,
        )
        for fallback_tool_name in candidates:
            tool_to_run = self._find_tool_by_name(fallback_tool_name)
            if tool_to_run is None:
                continue

            fallback_params = self._build_semantic_fallback_params(
                user_query,
                fallback_tool_name,
                primary_tool_params,
            )
            logger.warning(
                f"[TOOL-RECOVERY][SYNC] {primary_tool_name} falhou; tentando fallback semântico "
                f"{fallback_tool_name} com params={fallback_params}"
            )
            try:
                fallback_result = self._execute_tool_with_recovery(
                    tool_to_run,
                    fallback_tool_name,
                    fallback_params,
                )
            except Exception as fallback_error:
                logger.warning(
                    f"[TOOL-RECOVERY][SYNC] fallback {fallback_tool_name} também falhou: {fallback_error}"
                )
                continue

            if self._is_tool_failure_result(fallback_result) or self._is_effectively_empty_tool_result(
                fallback_tool_name,
                fallback_result,
            ):
                logger.warning(
                    f"[TOOL-RECOVERY][SYNC] fallback {fallback_tool_name} retornou erro ou resultado vazio."
                )
                continue

            return {
                "tool_name": fallback_tool_name,
                "tool_params": fallback_params,
                "tool_result": fallback_result,
            }
        return None

    def _has_business_metric_hint(self, query: str) -> bool:
        q = (query or "").lower()
        metric_tokens = [
            "venda",
            "vendas",
            "estoque",
            "margem",
            "ruptura",
            "rupturas",
            "preço",
            "preco",
            "custo",
            "ticket",
            "faturamento",
            "receita",
            "demanda",
            "giro",
            "abastecimento",
        ]
        return any(token in q for token in metric_tokens)

    def _has_market_subject_hint(self, query: str) -> bool:
        import re

        q = (query or "").lower()
        generic_phrases = [
            "pesquisa de mercado",
            "pesquisa de preço",
            "pesquisa de preco",
            "comparar preço",
            "comparar preco",
            "preço de mercado",
            "preco de mercado",
            "quanto custa",
            "onde comprar",
            "cotação",
            "cotacao",
            "concorrente",
            "concorrência",
            "concorrencia",
            "mercado",
            "internet",
        ]
        for phrase in generic_phrases:
            q = q.replace(phrase, " ")

        tokens = [
            token
            for token in re.findall(r"[a-z0-9à-ÿ]+", q)
            if len(token) > 2
            and token
            not in {
                "para",
                "com",
                "sem",
                "dos",
                "das",
                "por",
                "uma",
                "uns",
                "nas",
                "nos",
                "faca",
                "faça",
                "quero",
                "preciso",
                "busque",
                "buscar",
                "pesquise",
                "mostrar",
                "mostre",
            }
        ]
        return len(tokens) > 0

    def _format_tool_result_for_path(
        self,
        user_query: str,
        tool_name: str,
        tool_result: Any,
        tool_params: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if tool_name == "gerar_grafico_universal_v2":
            if self._is_dashboard_request(user_query) and not self._is_dashboard_followup_nonvisual_query(user_query):
                return self._format_governed_dashboard_result(user_query, tool_result, tool_params)
            return self._format_governed_chart_result(user_query, tool_result, tool_params)
        if tool_name == "gerar_dashboard_executivo":
            return self._format_governed_dashboard_result(user_query, tool_result, tool_params)
        if tool_name in {
            "consultar_dados_flexivel",
            "pesquisar_precos_concorrentes",
            "pesquisar_mercado_web",
            "encontrar_rupturas_criticas",
            "analisar_historico_vendas",
            "calcular_eoq",
            "calcular_mc_produto",
            "calcular_preco_final_une",
            "analisar_produto_todas_lojas",
        }:
            return self._format_deterministic_result(user_query, tool_name, tool_result, tool_params)
        return {"type": "text", "result": {"mensagem": "Consulta executada."}}

    def _should_use_calculation_sandbox(self, intent: Any, tool_name: str, query: str) -> bool:
        if not self.code_gen_agent:
            return False

        q = (query or "").lower()
        intent_value = str(getattr(intent, "value", intent or "")).lower()
        explicit_keywords = [
            "simulação",
            "simulacao",
            "cenário",
            "cenario",
            "sensibilidade",
            "what-if",
            "what if",
            "eoq",
            "lote econômico",
            "lote economico",
            "margem",
            "markup",
            "mark-up",
            "giro",
            "cobertura",
        ]
        if any(k in q for k in explicit_keywords):
            return True
        return intent_value == "calculation" and tool_name in {"calcular_eoq", "consultar_dados_flexivel"}

    def _resolve_product_snapshot_for_calculation(
        self,
        user_query: str,
        params: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        import re
        args = dict(params or {})
        product_id = str(args.get("produto_id") or args.get("produto_codigo") or "").strip()
        une_id = str(args.get("une_id") or args.get("une") or "").strip()
        if not product_id:
            match = re.search(r"(?:produto|sku|item)\s+(\d+)", user_query.lower())
            if match:
                product_id = str(match.group(1))
        if not une_id:
            match_une = re.search(r"(?:une|loja)\s+(\d{1,4})", user_query.lower())
            if match_une:
                une_id = str(match_une.group(1))

        snapshot: Dict[str, Any] = {"produto_id": product_id or None, "une_id": une_id or None}
        if not product_id:
            return snapshot

        query_tool = self._find_tool_by_name("consultar_dados_flexivel")
        if query_tool is None:
            return snapshot

        base_params = {
            "colunas": ["PRODUTO", "NOME", "UNE", "NOMESEGMENTO", "VENDA_30DD", "ULTIMA_ENTRADA_CUSTO_CD", "LIQUIDO_38", "ESTOQUE_UNE", "ESTOQUE_CD", "MEDIA_CONSIDERADA_LV"],
            "filtros": {"PRODUTO": int(product_id)},
            "limite": "1",
        }
        if une_id and une_id.isdigit():
            base_params["filtros"]["UNE"] = int(une_id)
        try:
            result = self._execute_tool_with_recovery(query_tool, "consultar_dados_flexivel", base_params)
            rows = result.get("resultados", []) if isinstance(result, dict) else []
            if rows and isinstance(rows[0], dict):
                row = rows[0]
                snapshot["produto_nome"] = row.get("NOME")
                snapshot["segmento"] = row.get("NOMESEGMENTO")
                snapshot["une_id"] = row.get("UNE") or snapshot.get("une_id")
                snapshot["venda_30dd"] = row.get("VENDA_30DD")
                snapshot["custo_unitario"] = row.get("ULTIMA_ENTRADA_CUSTO_CD")
                snapshot["preco_venda"] = row.get("LIQUIDO_38")
                snapshot["estoque_une"] = row.get("ESTOQUE_UNE")
                snapshot["estoque_cd"] = row.get("ESTOQUE_CD")
                snapshot["media_considerada_lv"] = row.get("MEDIA_CONSIDERADA_LV")
        except Exception as error:
            logger.warning(f"[SANDBOX] Falha ao coletar snapshot de produto {product_id}: {error}")

        return snapshot

    def _format_calculation_sandbox_result(
        self,
        user_query: str,
        calc_result: Dict[str, Any],
        assumptions: Dict[str, Any],
        sensitivity: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        if calc_result.get("error"):
            return {
                "type": "text",
                "result": {"mensagem": f"Não consegui concluir o cálculo no sandbox: {calc_result.get('error')}"},
                "source": "sandbox.code_gen_agent",
                "mode": "deterministic_sandbox_failed",
                "confidence": 0.35,
                "citations": [],
            }

        eoq = calc_result.get("eoq")
        orders = calc_result.get("orders_per_year")
        total_cost = calc_result.get("total_cost")
        order_point = calc_result.get("order_point")
        demand_annual = assumptions.get("demand_annual")
        unit_cost = assumptions.get("unit_cost")
        order_cost = assumptions.get("order_cost")
        holding_pct = assumptions.get("holding_cost_pct")
        product_id = assumptions.get("produto_id")
        product_name = assumptions.get("produto_nome")

        def _fmt_num(value: Any, digits: int = 2) -> str:
            try:
                if value is None:
                    return "-"
                return f"{float(value):,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except Exception:
                return str(value)

        assumptions_lines = [
            f"- Produto: {product_id or 'não informado'}" + (f" ({product_name})" if product_name else ""),
            f"- Demanda anual usada: {_fmt_num(demand_annual, 0)} unidades",
            f"- Custo por pedido: R$ {_fmt_num(order_cost)}",
            f"- Custo unitário: R$ {_fmt_num(unit_cost)}",
            f"- Custo de armazenagem: {_fmt_num(float(holding_pct or 0) * 100, 1)}% a.a.",
        ]

        msg = (
            "## Resumo executivo\n"
            "- Cálculo no sandbox concluído.\n"
            f"- EOQ recomendado: {_fmt_num(eoq, 0)} unidades por pedido.\n"
            f"- Pedidos por ano: {_fmt_num(orders, 1)}.\n"
            f"- Custo total anual estimado: R$ {_fmt_num(total_cost)}.\n"
            f"- Ponto de pedido de referência: {_fmt_num(order_point, 0)} unidades.\n\n"
            "## Premissas\n"
            + "\n".join(assumptions_lines)
        )

        table_data: List[Dict[str, Any]] = [
            {"Indicador": "EOQ recomendado", "Valor": _fmt_num(eoq, 0)},
            {"Indicador": "Pedidos por ano", "Valor": _fmt_num(orders, 1)},
            {"Indicador": "Custo total anual (R$)", "Valor": _fmt_num(total_cost)},
            {"Indicador": "Ponto de pedido", "Valor": _fmt_num(order_point, 0)},
        ]

        if sensitivity:
            table = "| Cenário | Demanda anual | EOQ | Pedidos/ano |\n|---|---:|---:|---:|\n"
            for row in sensitivity:
                table += (
                    f"| {row.get('cenario')} | {_fmt_num(row.get('demand_annual'), 0)} | "
                    f"{_fmt_num(row.get('eoq'), 0)} | {_fmt_num(row.get('orders_per_year'), 1)} |\n"
                )
            msg += "\n\n## Sensibilidade\n" + table
            table_data = [
                {
                    "Cenario": str(row.get("cenario") or "-"),
                    "Demanda anual": _fmt_num(row.get("demand_annual"), 0),
                    "EOQ": _fmt_num(row.get("eoq"), 0),
                    "Pedidos/ano": _fmt_num(row.get("orders_per_year"), 1),
                }
                for row in sensitivity
            ]

        citations = [{"source": "sandbox.code_gen_agent", "domain": "internal", "url": "", "competitor": "n/a"}]
        if product_id:
            citations.append({"source": "admmat.parquet", "domain": "internal_data", "url": "", "competitor": "n/a"})

        confidence = 0.86 if sensitivity else 0.82
        if assumptions.get("from_database"):
            confidence += 0.06
        confidence = round(min(confidence, 0.95), 2)

        return {
            "type": "text",
            "result": {"mensagem": msg},
            "source": "sandbox.code_gen_agent",
            "mode": "deterministic_sandbox",
            "confidence": confidence,
            "citations": citations,
            "table_data": table_data,
            "calculation": {
                "assumptions": assumptions,
                "result": calc_result,
                "sensitivity": sensitivity or [],
            },
        }

    def _format_operational_calculation_result(
        self,
        user_query: str,
        calculation_type: str,
        calc_result: Dict[str, Any],
        assumptions: Dict[str, Any],
    ) -> Dict[str, Any]:
        if calc_result.get("error"):
            return {
                "type": "text",
                "result": {"mensagem": f"Não consegui concluir o cálculo solicitado: {calc_result.get('error')}"},
                "source": "sandbox.code_gen_agent",
                "mode": "deterministic_sandbox_failed",
                "confidence": 0.35,
                "citations": [],
            }

        def _fmt_num(value: Any, digits: int = 2) -> str:
            try:
                if value is None:
                    return "-"
                return f"{float(value):,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except Exception:
                return str(value or "-")

        product_label = assumptions.get("produto_nome") or assumptions.get("produto_id") or "item analisado"
        support_table: List[Dict[str, Any]] = []

        if calculation_type == "discount_margin":
            current_margin_pct = calc_result.get("current_margin_pct")
            discount_pct = calc_result.get("discount_pct")
            new_margin_pct = calc_result.get("new_margin_pct")
            delta_margin_pct = calc_result.get("delta_margin_pct")
            support_table = [
                {"Indicador": "Margem atual (%)", "Valor": f"{_fmt_num(current_margin_pct, 1)}%"},
                {"Indicador": "Desconto aplicado (%)", "Valor": f"{_fmt_num(discount_pct, 1)}%"},
                {"Indicador": "Nova margem estimada (%)", "Valor": f"{_fmt_num(new_margin_pct, 1)}%"},
                {"Indicador": "Variação da margem (p.p.)", "Valor": _fmt_num(delta_margin_pct, 1)},
            ]
            msg = (
                "## Resumo executivo\n"
                f"- Aplicando { _fmt_num(discount_pct, 1) }% de desconto sobre um item com margem atual de { _fmt_num(current_margin_pct, 1) }%, a margem estimada cai para { _fmt_num(new_margin_pct, 1) }%.\n"
                f"- A perda aproximada é de { _fmt_num(abs(delta_margin_pct), 1) } pontos percentuais.\n\n"
                "## Tabela operacional\n"
                + "| Indicador | Valor |\n|---|---|\n"
                + "\n".join(f"| {row['Indicador']} | {row['Valor']} |" for row in support_table)
                + "\n\n## Próximas ações\n"
                + "- Valide se a nova margem continua acima da meta mínima da categoria.\n"
                "- Se quiser, eu posso calcular o volume adicional necessário para compensar esse desconto."
            )
        elif calculation_type == "margin":
            margin_pct = calc_result.get("margin_pct")
            markup_pct = calc_result.get("markup_pct")
            margin_value = calc_result.get("margin_value")
            support_table = [
                {"Indicador": "Preço de venda (R$)", "Valor": _fmt_num(assumptions.get("price"), 2)},
                {"Indicador": "Custo unitário (R$)", "Valor": _fmt_num(assumptions.get("cost"), 2)},
                {"Indicador": "Margem bruta (R$)", "Valor": _fmt_num(margin_value, 2)},
                {"Indicador": "Margem bruta (%)", "Valor": f"{_fmt_num(margin_pct, 1)}%"},
                {"Indicador": "Markup (%)", "Valor": f"{_fmt_num(markup_pct, 1)}%"},
            ]
            msg = (
                "## Resumo executivo\n"
                f"- Cálculo de margem concluído para {product_label}.\n"
                f"- Margem bruta estimada: {_fmt_num(margin_value, 2)} por unidade, equivalente a {_fmt_num(margin_pct, 1)}% sobre a venda.\n"
                f"- Markup implícito: {_fmt_num(markup_pct, 1)}% sobre o custo.\n"
                f"- Premissas: preço de venda {_fmt_num(assumptions.get('price'), 2)} e custo unitário {_fmt_num(assumptions.get('cost'), 2)}.\n\n"
                "## Tabela operacional\n"
                + "| Indicador | Valor |\n|---|---|\n"
                + "\n".join(f"| {row['Indicador']} | {row['Valor']} |" for row in support_table)
                + "\n\n## Próximas ações\n"
                + "- Compare a margem calculada com a meta comercial do segmento antes de aplicar desconto.\n"
                "- Se quiser, eu também posso simular impacto de desconto, frete ou imposto sobre essa margem."
            )
        elif calculation_type == "markup":
            markup_pct = calc_result.get("markup_pct")
            price = assumptions.get("price")
            cost = assumptions.get("cost")
            margin_pct = calc_result.get("margin_pct")
            support_table = [
                {"Indicador": "Preço de venda (R$)", "Valor": _fmt_num(price, 2)},
                {"Indicador": "Custo unitário (R$)", "Valor": _fmt_num(cost, 2)},
                {"Indicador": "Markup (%)", "Valor": f"{_fmt_num(markup_pct, 1)}%"},
                {"Indicador": "Margem equivalente (%)", "Valor": f"{_fmt_num(margin_pct, 1)}%"},
            ]
            msg = (
                "## Resumo executivo\n"
                f"- Cálculo de markup concluído para {product_label}.\n"
                f"- Markup estimado: {_fmt_num(markup_pct, 1)}% sobre o custo.\n"
                f"- Isso equivale a uma margem bruta aproximada de {_fmt_num(margin_pct, 1)}% sobre a venda.\n\n"
                "## Tabela operacional\n"
                + "| Indicador | Valor |\n|---|---|\n"
                + "\n".join(f"| {row['Indicador']} | {row['Valor']} |" for row in support_table)
                + "\n\n## Próximas ações\n"
                + "- Valide se o markup calculado sustenta a política comercial e a meta de margem da categoria.\n"
                "- Se quiser, eu posso transformar isso em preço-alvo ou simular cenários de desconto."
            )
        elif calculation_type == "stock_coverage":
            support_table = [
                {"Indicador": "Estoque base (un)", "Valor": _fmt_num(calc_result.get("stock_units"), 0)},
                {"Indicador": "Venda 30 dias (un)", "Valor": _fmt_num(calc_result.get("sales_30d"), 0)},
                {"Indicador": "Consumo diário médio", "Valor": _fmt_num(calc_result.get("daily_run_rate"), 2)},
                {"Indicador": "Cobertura (dias)", "Valor": _fmt_num(calc_result.get("coverage_days"), 1)},
            ]
            msg = (
                "## Resumo executivo\n"
                f"- Cálculo de cobertura concluído para {product_label}.\n"
                f"- Cobertura estimada: {_fmt_num(calc_result.get('coverage_days'), 1)} dias.\n"
                f"- Base usada: estoque de {_fmt_num(calc_result.get('stock_units'), 0)} unidades para uma venda de {_fmt_num(calc_result.get('sales_30d'), 0)} unidades nos últimos 30 dias.\n\n"
                "## Tabela operacional\n"
                + "| Indicador | Valor |\n|---|---|\n"
                + "\n".join(f"| {row['Indicador']} | {row['Valor']} |" for row in support_table)
                + "\n\n## Próximas ações\n"
                + "- Compare a cobertura atual com o lead time e a linha verde antes de reduzir compra.\n"
                "- Se quiser, eu posso listar as lojas com menor cobertura para o mesmo item."
            )
        else:
            support_table = [
                {"Indicador": "Estoque base (un)", "Valor": _fmt_num(calc_result.get("stock_units"), 0)},
                {"Indicador": "Venda 30 dias (un)", "Valor": _fmt_num(calc_result.get("sales_30d"), 0)},
                {"Indicador": "Giro 30 dias (x)", "Valor": _fmt_num(calc_result.get("inventory_turnover_30d"), 2)},
                {"Indicador": "Cobertura (dias)", "Valor": _fmt_num(calc_result.get("coverage_days"), 1)},
            ]
            msg = (
                "## Resumo executivo\n"
                f"- Cálculo de giro de estoque concluído para {product_label}.\n"
                f"- Giro aproximado em 30 dias: {_fmt_num(calc_result.get('inventory_turnover_30d'), 2)}x.\n"
                f"- A cobertura equivalente do estoque atual é de {_fmt_num(calc_result.get('coverage_days'), 1)} dias.\n\n"
                "## Tabela operacional\n"
                + "| Indicador | Valor |\n|---|---|\n"
                + "\n".join(f"| {row['Indicador']} | {row['Valor']} |" for row in support_table)
                + "\n\n## Próximas ações\n"
                + "- Use o giro junto com margem e cobertura para decidir reposição e profundidade de sortimento.\n"
                "- Se quiser, eu posso comparar esse giro com outras UNEs ou com o segmento do item."
            )

        citations = [{"source": "sandbox.code_gen_agent", "domain": "internal", "url": "", "competitor": "n/a"}]
        if assumptions.get("produto_id"):
            citations.append({"source": "admmat.parquet", "domain": "internal_data", "url": "", "competitor": "n/a"})
        return {
            "type": "text",
            "result": {"mensagem": msg},
            "source": "sandbox.code_gen_agent",
            "mode": "deterministic_sandbox",
            "confidence": 0.84 if assumptions.get("from_database") else 0.78,
            "citations": citations,
            "table_data": support_table,
            "calculation": {
                "type": calculation_type,
                "assumptions": assumptions,
                "result": calc_result,
            },
        }

    def _execute_calculation_sandbox(self, user_query: str, tool_selection: Any) -> Optional[Dict[str, Any]]:
        if not self.code_gen_agent:
            return None

        params = dict(getattr(tool_selection, "tool_params", {}) or {})
        snapshot = self._resolve_product_snapshot_for_calculation(user_query, params)
        calculation_mode = self._detect_calculation_mode(user_query)

        if calculation_mode in {"margin", "markup", "stock_coverage", "inventory_turnover", "discount_margin"}:
            price = self._extract_numeric_hint(
                user_query,
                [
                    r"pre[çc]o\s+(?:de\s+venda\s+)?(?:de\s+)?r?\$?\s*(\d+(?:[.,]\d+)?)",
                    r"venda\s+(?:de\s+)?r?\$?\s*(\d+(?:[.,]\d+)?)",
                ],
            )
            cost = self._extract_numeric_hint(
                user_query,
                [
                    r"custo\s+(?:unit[aá]rio\s+)?(?:de\s+)?r?\$?\s*(\d+(?:[.,]\d+)?)",
                    r"custo\s+de\s+aquisi[çc][aã]o\s+(?:de\s+)?r?\$?\s*(\d+(?:[.,]\d+)?)",
                ],
            )
            sales_30d = self._extract_numeric_hint(
                user_query,
                [
                    r"venda(?:s)?\s+(?:de\s+)?(\d+(?:[.,]\d+)?)\s*(?:unidades?|itens|pe[cç]as)?\s*(?:nos\s+[uú]ltimos\s+30\s+dias)?",
                    r"(\d+(?:[.,]\d+)?)\s*(?:unidades?|itens|pe[cç]as)\s+nos\s+[uú]ltimos\s+30\s+dias",
                ],
            )
            stock_units = self._extract_numeric_hint(
                user_query,
                [
                    r"estoque\s+(?:atual\s+)?(?:de\s+)?(\d+(?:[.,]\d+)?)\s*(?:unidades?|itens|pe[cç]as)?",
                ],
            )

            if price is None:
                try:
                    if snapshot.get("preco_venda") is not None:
                        price = float(snapshot.get("preco_venda"))
                except Exception:
                    price = None
            if cost is None:
                try:
                    if snapshot.get("custo_unitario") is not None:
                        cost = float(snapshot.get("custo_unitario"))
                except Exception:
                    cost = None
            if sales_30d is None:
                try:
                    if snapshot.get("venda_30dd") is not None:
                        sales_30d = float(snapshot.get("venda_30dd"))
                except Exception:
                    sales_30d = None
            if stock_units is None:
                for stock_key in ("estoque_une", "estoque_cd", "media_considerada_lv"):
                    try:
                        if snapshot.get(stock_key) is not None:
                            stock_units = float(snapshot.get(stock_key))
                            break
                    except Exception:
                        continue

            if calculation_mode in {"margin", "markup"}:
                if price is None or price <= 0 or cost is None or cost < 0:
                    return None
                margin_value = price - cost
                margin_pct = (margin_value / price * 100.0) if price > 0 else 0.0
                markup_pct = (margin_value / cost * 100.0) if cost > 0 else 0.0
                calc_result = {
                    "margin_value": round(margin_value, 2),
                    "margin_pct": round(margin_pct, 2),
                    "markup_pct": round(markup_pct, 2),
                }
                assumptions = {
                    "calculation_type": calculation_mode,
                    "produto_id": snapshot.get("produto_id"),
                    "produto_nome": snapshot.get("produto_nome"),
                    "price": round(float(price), 2),
                    "cost": round(float(cost), 2),
                    "from_database": bool(snapshot.get("preco_venda") is not None and snapshot.get("custo_unitario") is not None),
                }
                return self._format_operational_calculation_result(user_query, calculation_mode, calc_result, assumptions)

            if calculation_mode == "discount_margin":
                discount_pct = self._extract_numeric_hint(
                    user_query,
                    [
                        r"(\d+(?:[.,]\d+)?)\s*%\s+de\s+desconto",
                        r"desconto\s+de\s+(\d+(?:[.,]\d+)?)\s*%",
                    ],
                )
                current_margin_pct = self._extract_numeric_hint(
                    user_query,
                    [
                        r"margem\s+atual\s+de\s+(\d+(?:[.,]\d+)?)\s*%",
                        r"margem\s+de\s+(\d+(?:[.,]\d+)?)\s*%",
                    ],
                )
                if current_margin_pct is None:
                    current_margin_pct = self._extract_percent_hint(user_query)
                if discount_pct is None or current_margin_pct is None:
                    return None

                discount_ratio = float(discount_pct) / 100.0
                current_margin_ratio = float(current_margin_pct) / 100.0
                cost_ratio = 1.0 - current_margin_ratio
                new_price_ratio = 1.0 - discount_ratio
                if new_price_ratio <= 0:
                    return None
                new_margin_ratio = (new_price_ratio - cost_ratio) / new_price_ratio
                calc_result = {
                    "discount_pct": round(float(discount_pct), 2),
                    "current_margin_pct": round(float(current_margin_pct), 2),
                    "new_margin_pct": round(new_margin_ratio * 100.0, 2),
                    "delta_margin_pct": round((new_margin_ratio * 100.0) - float(current_margin_pct), 2),
                }
                assumptions = {
                    "calculation_type": calculation_mode,
                    "price_reference": 100.0,
                    "cost_reference": round(cost_ratio * 100.0, 2),
                    "from_database": False,
                }
                return self._format_operational_calculation_result(user_query, calculation_mode, calc_result, assumptions)

            if stock_units is None or stock_units < 0 or sales_30d is None or sales_30d <= 0:
                return None

            daily_run_rate = sales_30d / 30.0
            coverage_days = stock_units / daily_run_rate if daily_run_rate > 0 else 0.0
            inventory_turnover_30d = sales_30d / stock_units if stock_units > 0 else 0.0
            calc_result = {
                "stock_units": round(float(stock_units), 2),
                "sales_30d": round(float(sales_30d), 2),
                "daily_run_rate": round(float(daily_run_rate), 4),
                "coverage_days": round(float(coverage_days), 2),
                "inventory_turnover_30d": round(float(inventory_turnover_30d), 4),
            }
            assumptions = {
                "calculation_type": calculation_mode,
                "produto_id": snapshot.get("produto_id"),
                "produto_nome": snapshot.get("produto_nome"),
                "une_id": snapshot.get("une_id"),
                "from_database": bool(snapshot.get("venda_30dd") is not None),
            }
            return self._format_operational_calculation_result(user_query, calculation_mode, calc_result, assumptions)

        demand_annual = self._extract_numeric_hint(
            user_query,
            [
                r"demanda\s+anual\s+(?:de\s+)?(\d+(?:[.,]\d+)?)",
                r"(\d+(?:[.,]\d+)?)\s+unidades?\s+por\s+ano",
            ],
        )
        order_cost = self._extract_numeric_hint(
            user_query,
            [
                r"custo\s+(?:do|de)\s+pedido\s+(?:de\s+)?r?\$?\s*(\d+(?:[.,]\d+)?)",
            ],
        )
        unit_cost = self._extract_numeric_hint(
            user_query,
            [
                r"custo\s+unit[aá]rio\s+(?:de\s+)?r?\$?\s*(\d+(?:[.,]\d+)?)",
                r"pre[çc]o\s+unit[aá]rio\s+(?:de\s+)?r?\$?\s*(\d+(?:[.,]\d+)?)",
            ],
        )
        holding_cost_pct = self._extract_percent_hint(user_query)

        if demand_annual is None:
            venda_30dd = snapshot.get("venda_30dd")
            try:
                if venda_30dd is not None:
                    demand_annual = float(venda_30dd) * 12.0
            except Exception:
                demand_annual = None
        if unit_cost is None:
            try:
                if snapshot.get("custo_unitario") is not None:
                    unit_cost = float(snapshot.get("custo_unitario"))
            except Exception:
                unit_cost = None

        order_cost = order_cost if order_cost and order_cost > 0 else 150.0
        holding_cost_pct = holding_cost_pct if holding_cost_pct and holding_cost_pct > 0 else 0.25

        if demand_annual is None or demand_annual <= 0 or unit_cost is None or unit_cost <= 0:
            return {
                "type": "text",
                "result": {
                    "mensagem": (
                        "## Resumo executivo\n"
                        "- Não é possível fechar um EOQ confiável sem os insumos mínimos.\n"
                        "- Para calcular o lote econômico eu preciso da demanda anual e do custo unitário do item; o custo por pedido e o custo de armazenagem podem ser assumidos ou informados.\n\n"
                        "## Tabela operacional\n"
                        "| Insumo | Situação |\n|---|---|\n"
                        "| Demanda anual | obrigatório |\n"
                        "| Custo unitário | obrigatório |\n"
                        "| Custo por pedido | opcional, usa padrão se não vier |\n"
                        "| Custo de armazenagem | opcional, usa padrão se não vier |\n\n"
                        "## Próximas ações\n"
                        "- Informe produto/SKU ou os parâmetros numéricos para eu calcular o EOQ agora.\n"
                        "- Se preferir, eu também posso montar um exemplo de EOQ com premissas explícitas."
                    )
                },
                "source": "sandbox.code_gen_agent",
                "mode": "deterministic_sandbox",
                "confidence": 0.74,
                "citations": [],
                "table_data": [
                    {"Insumo": "Demanda anual", "Situação": "obrigatório"},
                    {"Insumo": "Custo unitário", "Situação": "obrigatório"},
                    {"Insumo": "Custo por pedido", "Situação": "opcional"},
                    {"Insumo": "Custo de armazenagem", "Situação": "opcional"},
                ],
                "calculation": {
                    "type": "eoq",
                    "assumptions": {
                        "demand_annual": demand_annual,
                        "unit_cost": unit_cost,
                        "order_cost": order_cost,
                        "holding_cost_pct": holding_cost_pct,
                    },
                    "result": {},
                },
            }

        calc_result = self.code_gen_agent.calculate_eoq_internal(
            demand_annual=float(demand_annual),
            order_cost=float(order_cost),
            holding_cost_pct=float(holding_cost_pct),
            unit_cost=float(unit_cost),
        )

        q = (user_query or "").lower()
        wants_sensitivity = any(k in q for k in ["sensibilidade", "simulação", "simulacao", "cenário", "cenario", "what if", "what-if"])
        sensitivity_rows: Optional[List[Dict[str, Any]]] = None
        if wants_sensitivity:
            sensitivity_pct = self._extract_percent_hint(user_query) or 0.20
            sensitivity_pct = max(0.05, min(float(sensitivity_pct), 0.60))
            scenarios = [
                ("Base", float(demand_annual)),
                ("Demanda -{}".format(int(sensitivity_pct * 100)), float(demand_annual) * (1 - sensitivity_pct)),
                ("Demanda +{}".format(int(sensitivity_pct * 100)), float(demand_annual) * (1 + sensitivity_pct)),
            ]
            sensitivity_rows = []
            for label, scenario_demand in scenarios:
                scenario_calc = self.code_gen_agent.calculate_eoq_internal(
                    demand_annual=float(max(1.0, scenario_demand)),
                    order_cost=float(order_cost),
                    holding_cost_pct=float(holding_cost_pct),
                    unit_cost=float(unit_cost),
                )
                sensitivity_rows.append(
                    {
                        "cenario": label,
                        "demand_annual": scenario_demand,
                        "eoq": scenario_calc.get("eoq"),
                        "orders_per_year": scenario_calc.get("orders_per_year"),
                    }
                )

        assumptions = {
            "produto_id": snapshot.get("produto_id"),
            "produto_nome": snapshot.get("produto_nome"),
            "demand_annual": round(float(demand_annual), 2),
            "order_cost": round(float(order_cost), 2),
            "unit_cost": round(float(unit_cost), 2),
            "holding_cost_pct": round(float(holding_cost_pct), 4),
            "from_database": bool(snapshot.get("venda_30dd") is not None and snapshot.get("custo_unitario") is not None),
        }
        return self._format_calculation_sandbox_result(user_query, calc_result, assumptions, sensitivity_rows)

    def _requires_governed_path(self, intent: Any, tool_name: str, confidence: float, query: str) -> bool:
        """
        Fluxo governado para reduzir variação e aumentar assertividade em produção.
        """
        intent_val = getattr(intent, "value", str(intent))
        q = (query or "").lower()
        high_value_intents = {"data_query", "visualization", "analysis"}
        local_critical_tools = {
            "consultar_dados_flexivel",
            "encontrar_rupturas_criticas",
            "analisar_historico_vendas",
            "pesquisar_precos_concorrentes",
            "pesquisar_mercado_web",
            "gerar_dashboard_executivo",
            "gerar_grafico_universal_v2",
        }
        explicit_business = any(k in q for k in ["vendas", "venda", "total", "segmento", "une", "lojas"])
        explicit_competitive = any(
            k in q for k in [
                "concorrente", "concorrência", "cotação", "cotacao", "pesquisa de preço",
                "pesquisa de preco", "pesquisa de mercado", "preço de mercado", "preco de mercado",
                "benchmark de mercado", "pesquisa concorrencial", "americanas", "amigão", "amigao",
                "tid", "bellart", "tubarão", "tubarao", "kalunga", "casa&video", "casa e video"
            ]
        )
        return (
            (intent_val in high_value_intents and confidence >= 0.60)
            or explicit_business
            or explicit_competitive
            or tool_name in {"gerar_grafico_universal_v2", "pesquisar_precos_concorrentes"}
            or (tool_name in local_critical_tools and confidence >= 0.55)
        )

    def _is_explicit_business_query(self, query: str) -> bool:
        q = (query or "").lower()
        return any(k in q for k in ["vendas", "venda", "total", "segmento", "une", "lojas"])

    def _format_governed_chart_result(self, user_query: str, tool_result: Dict[str, Any], tool_params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(tool_result, dict):
            return {"type": "text", "result": {"mensagem": "Não consegui gerar o gráfico no momento."}}
        if tool_result.get("status") != "success":
            msg = tool_result.get("message") or tool_result.get("error") or "Falha ao gerar gráfico."
            error_code = str(tool_result.get("error_code") or "")
            diagnostics = tool_result.get("diagnostics", {}) if isinstance(tool_result.get("diagnostics"), dict) else {}
            if error_code == "NO_DATA":
                requested_segment = diagnostics.get("requested_segment")
                likely_rls_block = bool(diagnostics.get("likely_rls_block"))
                if likely_rls_block:
                    msg = (
                        f"Não consegui gerar o gráfico porque o segmento '{requested_segment or 'informado'}' "
                        "não está disponível no escopo de acesso deste usuário (RLS)."
                    )
                else:
                    msg = (
                        "Não encontrei dados para montar o gráfico nesse recorte. "
                        "Confirme segmento/período/lojas ou remova filtros mais restritivos."
                    )
            return {"type": "text", "result": {"mensagem": f"Não consegui gerar o gráfico: {msg}"}}

        summary = tool_result.get("summary", {}) if isinstance(tool_result.get("summary"), dict) else {}
        q = (user_query or "").lower()
        low_performance_focus = any(
            marker in q
            for marker in (
                "pontos críticos",
                "pontos criticos",
                "critico",
                "crítico",
                "criticos",
                "críticos",
                "menor",
                "menores",
                "piores",
                "recomenda",
                "ações",
                "acoes",
                "próximos passos",
                "proximos passos",
            )
        )
        ranked_rows = (
            summary.get("bottom_10", []) if low_performance_focus and isinstance(summary.get("bottom_10"), list) else []
        )
        if not ranked_rows:
            ranked_rows = (
                summary.get("bottom_3", []) if low_performance_focus and isinstance(summary.get("bottom_3"), list) else []
            )
        if not ranked_rows:
            ranked_rows = summary.get("top_10", []) if isinstance(summary.get("top_10"), list) else []
        if not ranked_rows:
            ranked_rows = summary.get("top_3", []) if isinstance(summary.get("top_3"), list) else []
        dimension_label = str(summary.get("dimensao") or "Dimensão")
        metric_label = str(summary.get("metrica") or "Valor")
        def _fmt_num(v: Any) -> str:
            try:
                fv = float(v or 0)
            except Exception:
                return str(v)
            return f"{fv:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        top_rows = ranked_rows[:10] if ranked_rows else []

        resumo = str(summary.get("mensagem") or "Gráfico gerado com os dados solicitados.")

        tabela_top = f"| {dimension_label} | {metric_label} |\n|---|---|\n"
        if top_rows:
            for item in top_rows:
                tabela_top += f"| {item.get('dimensao', '-')} | {_fmt_num(item.get('valor', 0))} |\n"
        else:
            tabela_top += "| - | - |\n"

        if any(k in dimension_label.lower() for k in ["loja", "une"]):
            if low_performance_focus:
                action = (
                    "- Priorize as UNEs da base do ranking com plano comercial e revisão de exposição ainda nesta semana.\n"
                    "- Verifique ruptura, cobertura e preço nas lojas com menor venda antes de ampliar compra.\n"
                    "- Reavalie o ranking no próximo ciclo semanal para medir recuperação."
                )
            else:
                action = (
                    "- Priorize as UNEs de menor venda com plano comercial em até 7 dias.\n"
                    "- Revise estoque e cobertura dos itens líderes para reduzir perda de venda.\n"
                    "- Reavalie o ranking no próximo ciclo semanal para medir ganho."
                )
        else:
            if low_performance_focus:
                action = (
                    "- Ataque primeiro os recortes na base do ranking com ajuste de preço, mix e exposição.\n"
                    "- Valide ruptura e cobertura dos itens com baixa tração antes de ampliar abastecimento.\n"
                    "- Reavalie o desempenho no próximo ciclo semanal para confirmar recuperação."
                )
            else:
                action = (
                    "- Priorize os recortes de menor venda para ajuste de preço/sortimento.\n"
                    "- Valide ruptura e disponibilidade dos itens de maior demanda.\n"
                    "- Reavalie o desempenho no próximo ciclo semanal."
                )

        msg = (
            "## Resumo executivo\n"
            + f"- {resumo}\n"
            + "\n\n## Tabela operacional\n"
            + tabela_top
            + "\n\n## Próximas ações\n"
            + action
        )
        return {
            "type": "text",
            "result": {"mensagem": msg},
            "chart_data": tool_result.get("chart_data"),
        }

    def _format_metric_value(self, value: Any) -> str:
        try:
            if value is None:
                return "-"
            if isinstance(value, (int, np.integer)):
                return f"{int(value):,}".replace(",", ".")
            if isinstance(value, (float, np.floating)):
                numeric_value = float(value)
                if abs(numeric_value) >= 1000:
                    return f"{numeric_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                return f"{numeric_value:.2f}".replace(".", ",")
            return str(value)
        except Exception:
            return str(value)

    def _format_governed_dashboard_result(
        self,
        user_query: str,
        tool_result: Dict[str, Any],
        tool_params: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not isinstance(tool_result, dict):
            return {
                "type": "text",
                "result": {"mensagem": "Não consegui montar o dashboard no momento."},
            }

        if tool_result.get("status") != "success":
            error_msg = str(tool_result.get("message") or tool_result.get("error") or "falha desconhecida")
            return {
                "type": "text",
                "result": {
                    "mensagem": (
                        "Não consegui montar o dashboard completo nesta rodada. "
                        f"Motivo: {error_msg}."
                    )
                },
            }

        chart_data = tool_result.get("chart_data")
        if isinstance(chart_data, str):
            try:
                chart_data = json.loads(chart_data)
            except Exception:
                chart_data = None

        summary = tool_result.get("summary", {})
        if not isinstance(summary, dict):
            summary = {}

        params = tool_params if isinstance(tool_params, dict) else {}
        filters: Dict[str, Any] = {}
        if params.get("segmento") or params.get("filtro_segmento"):
            filters["segmento"] = params.get("segmento") or params.get("filtro_segmento")
        if params.get("une") or params.get("filtro_une"):
            filters["une"] = params.get("une") or params.get("filtro_une")
        if params.get("periodo"):
            filters["periodo"] = params.get("periodo")
        if params.get("escopo"):
            filters["escopo"] = params.get("escopo")

        kpi_candidates = [
            ("vendas_totais", "Vendas Totais (R$)"),
            ("lucro_total", "Lucro Total (R$)"),
            ("total_produtos", "Total de Produtos"),
            ("estoque_total", "Estoque Total"),
            ("total_grupos", "Total de Grupos"),
            ("valor_estoque", "Valor do Estoque (R$)"),
        ]

        widgets: List[Dict[str, Any]] = []
        for key, label in kpi_candidates:
            if key in summary:
                widgets.append(
                    {
                        "kind": "kpi",
                        "id": key,
                        "title": label,
                        "value": self._format_metric_value(summary.get(key)),
                    }
                )

        if chart_data:
            widgets.append(
                {
                    "kind": "chart",
                    "id": "visao_geral",
                    "title": "Visao consolidada",
                    "chart_spec": chart_data,
                }
            )

        top_10 = summary.get("top_10", []) if isinstance(summary.get("top_10"), list) else []
        if not top_10:
            top_10 = summary.get("top_3", []) if isinstance(summary.get("top_3"), list) else []
        dimension_label = str(summary.get("dimensao") or "Dimensão")
        metric_label = str(summary.get("metrica") or "Valor")
        if top_10:
            top_rows = []
            for item in top_10[:10]:
                if not isinstance(item, dict):
                    continue
                top_rows.append(
                    {
                        dimension_label: str(item.get("dimensao") or "-"),
                        metric_label: self._format_metric_value(item.get("valor")),
                    }
                )
            if top_rows:
                widgets.append(
                    {
                        "kind": "table",
                        "id": "top_dimensoes",
                        "title": f"Ranking Top 10 - {metric_label} por {dimension_label}",
                        "rows": top_rows,
                    }
                )

        table_rows = [
            {"Indicador": label, "Valor": self._format_metric_value(summary.get(key))}
            for key, label in kpi_candidates
            if key in summary
        ]
        if table_rows:
            widgets.append(
                {
                    "kind": "table",
                    "id": "resumo_metricas",
                    "title": "Resumo de metricas",
                    "rows": table_rows,
                }
            )

        if not widgets and chart_data:
            # Fallback para cenário com apenas gráfico.
            return self._format_governed_chart_result(user_query, tool_result, tool_params)

        def _period_label(raw: Any) -> str:
            import re
            value = str(raw or "").strip().lower()
            match = re.match(r"^(\d+)\s*([dwm])$", value)
            if match:
                qty = int(match.group(1))
                unit = match.group(2)
                if unit == "d":
                    return f"Últimos {qty} dias"
                if unit == "w":
                    return f"Últimas {qty} semanas"
                if unit == "m":
                    return f"Últimos {qty} meses"
            aliases = {
                "mes_atual": "Mês atual",
                "hoje": "Hoje",
            }
            return aliases.get(value, str(raw or ""))

        subtitle_parts: List[str] = []
        if filters.get("segmento"):
            subtitle_parts.append(f"Segmento {filters.get('segmento')}")
        if filters.get("une"):
            subtitle_parts.append(f"UNE {filters.get('une')}")
        if filters.get("periodo"):
            human_period = _period_label(filters.get("periodo"))
            subtitle_parts.append(human_period)
            filters["periodo"] = human_period
        if filters.get("escopo") == "rede":
            subtitle_parts.append("Toda a rede")
        subtitle = " • ".join([p for p in subtitle_parts if p]) if subtitle_parts else "Visão consolidada da rede"
        dashboard_title = "Painel de Vendas Interativo"
        if filters.get("segmento"):
            dashboard_title = f"Painel de Vendas - {filters.get('segmento')}"
        dashboard_spec = {
            "title": dashboard_title,
            "subtitle": subtitle,
            "filters": filters,
            "widgets": widgets,
        }
        message = (
            "Dashboard interativo gerado com sucesso. "
            "Use os widgets para navegar pelos indicadores principais."
        )
        return {
            "type": "dashboard",
            "result": {"mensagem": message},
            "dashboard_spec": dashboard_spec,
            "chart_data": chart_data,
            "source": "deterministic_tool",
            "confidence": 0.9,
        }

    def _extract_segment_from_query(self, query: str) -> Optional[str]:
        from backend.app.core.utils.query_router import extract_segment_filter
        return extract_segment_filter(query)

    def _extract_product_code_from_query(self, query: str) -> Optional[int]:
        from backend.app.core.utils.query_router import extract_product_code

        return extract_product_code(query)

    def _extract_une_from_query(self, query: str) -> Optional[str]:
        from backend.app.core.utils.query_router import extract_une_filter
        return extract_une_filter(query)

    def _extract_period_from_query(self, query: str) -> Optional[str]:
        from backend.app.core.utils.query_router import extract_period_filter
        return extract_period_filter(query)

    def _extract_state_from_query(self, query: str) -> Optional[str]:
        import re
        q = (query or "").upper()
        for uf in ("RJ", "MG", "ES"):
            if re.search(rf"\b{uf}\b", q):
                return uf
        for label, uf in [("RIO DE JANEIRO", "RJ"), ("MINAS GERAIS", "MG"), ("ESPÍRITO SANTO", "ES"), ("ESPIRITO SANTO", "ES")]:
            if label in q:
                return uf
        return None

    def _is_all_stores_request(self, query: str) -> bool:
        from backend.app.core.utils.query_router import is_all_stores_scope
        return is_all_stores_scope(query)

    def _ensure_tool_selection_available(self, user_query: str, tool_selection: Any) -> None:
        """
        Garante que a ferramenta selecionada está disponível no escopo atual.
        Se não estiver, aplica alias/fallback para evitar erro operacional.
        """
        selected = str(getattr(tool_selection, "tool_name", "") or "")
        if not selected:
            return

        # Caso principal: ferramenta está disponível no role/dependências atuais.
        if self._find_tool_by_name(selected) is not None:
            return

        alias_map = {
            "prever_demanda_sazonal": "prever_demanda",
        }
        alias_target = alias_map.get(selected)
        if alias_target and self._find_tool_by_name(alias_target) is not None:
            logger.warning(f"[ROUTER] Tool '{selected}' indisponível. Usando alias '{alias_target}'.")
            tool_selection.tool_name = alias_target
            tool_selection.tool_params = self._normalize_tool_arguments(
                alias_target,
                getattr(tool_selection, "tool_params", {}) or {},
            )
            return

        fallback_tools = list(getattr(tool_selection, "fallback_tools", []) or [])
        for fallback_name in fallback_tools:
            if self._find_tool_by_name(fallback_name) is None:
                continue
            logger.warning(f"[ROUTER] Tool '{selected}' indisponível. Fallback para '{fallback_name}'.")
            params = dict(getattr(tool_selection, "tool_params", {}) or {})
            if fallback_name == "gerar_grafico_universal_v2":
                params.setdefault("descricao", user_query)
                params.setdefault("tipo_grafico", "bar")
                if params.get("segmento") and not params.get("filtro_segmento"):
                    params["filtro_segmento"] = params.get("segmento")
                if params.get("une") and not params.get("filtro_une"):
                    params["filtro_une"] = str(params.get("une"))
                if not params.get("quebra_por"):
                    inferred_breakdown = self._infer_chart_breakdown(user_query)
                    if inferred_breakdown:
                        params["quebra_por"] = inferred_breakdown
            elif fallback_name == "consultar_dados_flexivel":
                params.setdefault("colunas", ["PRODUTO", "NOME", "UNE", "VENDA_30DD", "ESTOQUE_UNE"])
                params.setdefault("limite", "50")
            tool_selection.tool_name = fallback_name
            tool_selection.tool_params = self._normalize_tool_arguments(fallback_name, params)
            return

        # Fallback final por tipo de consulta.
        if self._is_chart_request(user_query) and self._find_tool_by_name("gerar_grafico_universal_v2") is not None:
            logger.warning(f"[ROUTER] Tool '{selected}' indisponível. Fallback final para gráfico universal.")
            tool_selection.tool_name = "gerar_grafico_universal_v2"
            tool_selection.tool_params = {"descricao": user_query, "tipo_grafico": "bar", "limite": 50}
            return

        if self._find_tool_by_name("consultar_dados_flexivel") is not None:
            logger.warning(f"[ROUTER] Tool '{selected}' indisponível. Fallback final para consulta flexível.")
            tool_selection.tool_name = "consultar_dados_flexivel"
            tool_selection.tool_params = {
                "colunas": ["PRODUTO", "NOME", "UNE", "VENDA_30DD", "ESTOQUE_UNE"],
                "limite": "50",
            }

    def _is_competitive_query(self, query: str) -> bool:
        """Retorna True para qualquer query competitiva (concorrente OU mercado)."""
        return self._is_specific_competitor_query(query) or self._is_market_research_query(query)

    def _is_specific_competitor_query(self, query: str) -> bool:
        """Retorna True se a query menciona concorrentes específicos."""
        q = (query or "").lower()
        return any(
            k in q for k in [
                "concorrente", "concorrência", "pesquisa concorrencial",
                "americanas", "amigão", "amigao",
                "bellart", "tid", "tubarão", "tubarao", "kalunga",
                "casa&video", "casa e video",
                "amazon", "shopee", "le biscuit", "lebiscuit",
                "mercado livre", "mercadolivre", "meli",
            ]
        )

    def _is_market_research_query(self, query: str) -> bool:
        """Retorna True para pesquisa genérica de mercado (sem concorrente específico)."""
        q = (query or "").lower()
        return any(
            k in q for k in [
                "pesquisa de mercado", "preço de mercado", "preco de mercado",
                "cotação", "cotacao", "pesquisa de preço", "pesquisa de preco",
                "comparar preço", "comparar preco", "benchmark de mercado",
                "quanto custa", "onde comprar", "preço na internet",
                "preco na internet", "marketplace", "mercado livre",
            ]
        )

    def _extract_competitors_from_query(self, query: str) -> str:
        q = (query or "").lower()
        names = []
        mappings = [
            ("kalunga", ["kalunga"]),
            ("casa&video", ["casa&video", "casa e video", "casa video", "casaevideo"]),
            ("le biscuit", ["le biscuit", "lebiscuit"]),
            ("americanas", ["americanas", "lojas americanas"]),
            ("amigao", ["amigão", "amigao"]),
            ("tid's", ["tid's", "tids", " tid "]),
            ("bellart", ["bellart"]),
            ("tubarao", ["tubarão", "tubarao"]),
            ("amazon", ["amazon"]),
            ("shopee", ["shopee"]),
            ("mercado livre", ["mercado livre", "mercadolivre", "meli"]),
        ]
        for canonical, aliases in mappings:
            if any(alias in q for alias in aliases):
                names.append(canonical)
        unique = []
        for n in names:
            if n not in unique:
                unique.append(n)
        return ",".join(unique)

    def _extract_market_product_hint(self, query: str) -> Optional[str]:
        import re

        q = str(query or "").strip()
        if not q:
            return None

        lowered = q.lower()
        market_markers = (
            "pesquisa de mercado",
            "preço de mercado",
            "preco de mercado",
            "pesquisa de preço",
            "pesquisa de preco",
            "concorrente",
            "concorrência",
            "concorrencia",
            "mercado livre",
            "mercadolivre",
            "meli",
            "kalunga",
            "americanas",
            "amazon",
            "shopee",
            "le biscuit",
            "lebiscuit",
        )
        if not any(marker in lowered for marker in market_markers):
            return None

        lowered = re.sub(r"^(faca|faça|faz|fazer)\s+(uma\s+)?", "", lowered)
        lowered = re.sub(r"^(realize|realizar|realiza)\s+(uma\s+)?", "", lowered)
        lowered = re.sub(r"^(pesquisa|pesquise|compare|comparar|benchmark)\s+", "", lowered)
        lowered = re.sub(r"^(de\s+mercado|de\s+pre[çc]o)\s+", "", lowered)
        lowered = re.sub(r"^(do|da|de|o|a)?\s*produto\s+", "", lowered)
        lowered = re.sub(
            r"\b(nos?\s+concorrentes?\s+.+)$",
            "",
            lowered,
        )
        lowered = re.sub(
            r"\b(?:na|no|em)\s+(mercado livre|mercadolivre|meli|kalunga|americanas|amazon|shopee|le biscuit|lebiscuit|casa&video|casa e video|bellart|amig[aã]o|tubar[aã]o|tid'?s?)\b.*$",
            "",
            lowered,
        )
        lowered = re.sub(
            r"\b(?:em|no estado)\s+(rj|rio de janeiro|mg|minas gerais|es|esp[ií]rito santo|espirito santo)\b.*$",
            "",
            lowered,
        )
        lowered = re.sub(r"\s+", " ", lowered).strip(" .,-")
        return lowered or None

    def _normalize_market_text(self, value: Any) -> str:
        import re
        import unicodedata

        raw = unicodedata.normalize("NFKD", str(value or ""))
        raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
        raw = raw.lower()
        raw = re.sub(r"[^a-z0-9]+", " ", raw)
        return re.sub(r"\s+", " ", raw).strip()

    def _extract_market_query_tokens(self, query: str) -> List[str]:
        import re

        normalized = self._normalize_market_text(query)
        if not normalized:
            return []

        stopwords = {
            "fa", "faca", "uma", "um", "de", "do", "da", "dos", "das", "para", "no", "na", "nos", "nas",
            "com", "e", "em", "por", "ou", "a", "o", "as", "os",
            "pesquisa", "mercado", "preco", "precos", "precoo", "produto", "itens", "item", "fontes",
            "publicas", "publica", "links", "link", "consulta", "comparar", "compare", "pesquise",
            "concorrente", "concorrentes", "concorrencia", "benchmark",
            "rj", "mg", "es", "rio", "janeiro",
            "kalunga", "americanas", "amazon", "shopee", "mercado", "livre", "meli", "casa", "video",
            "inexistente", "inexistentes",
        }
        raw_tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", normalized)
        tokens: List[str] = []
        for token in raw_tokens:
            if token in stopwords:
                continue
            has_digit = any(ch.isdigit() for ch in token)
            if len(token) < 3 and not has_digit:
                continue
            if token not in tokens:
                tokens.append(token)
        return tokens

    def _filter_relevant_market_items(self, user_query: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        tokens = self._extract_market_query_tokens(user_query)
        if not tokens:
            return items

        has_numeric_token = any(any(ch.isdigit() for ch in t) for t in tokens)
        relevant: List[Dict[str, Any]] = []
        for item in items:
            haystack = self._normalize_market_text(
                " ".join(
                    [
                        str(item.get("produto") or ""),
                        str(item.get("concorrente") or ""),
                        str(item.get("dominio") or ""),
                        str(item.get("url") or ""),
                    ]
                )
            )
            if not haystack:
                continue
            matches = [t for t in tokens if t in haystack]
            if not matches:
                continue
            match_ratio = len(matches) / float(max(1, len(tokens)))
            min_ratio = 0.34 if len(tokens) >= 3 else 0.5
            if match_ratio >= min_ratio or len(matches) >= 2:
                relevant.append(item)

        # Em consultas altamente específicas (SKU/medida), sem match = sem evidência.
        if not relevant and has_numeric_token:
            return []
        return relevant if relevant else items

    def _resolve_query_with_history_context(self, user_query: str, chat_history: Optional[List[Dict[str, Any]]]) -> str:
        """
        Resolve follow-up curto/ambíguo com base na última pergunta do usuário.
        """
        import re

        query = (user_query or "").strip()
        if not query or not chat_history:
            return query

        q_lower = query.lower()
        # Follow-up estratégico/comercial deve manter a intenção da pergunta atual;
        # mesclar com a query anterior reduz precisão e induz repetição de relatório.
        if self._is_contextual_action_followup_query(q_lower, chat_history):
            return query
        expanded_followup_query = self._expand_business_followup_with_context(query, chat_history)
        if expanded_followup_query != query:
            logger.info(f"[CONTEXT] Follow-up ancorado. atual='{query}' expandido='{expanded_followup_query}'")
            return expanded_followup_query
        word_count = len([w for w in q_lower.split() if w.strip()])
        has_domain_scope = any(
            k in q_lower
            for k in [
                "venda",
                "estoque",
                "segmento",
                "categoria",
                "grupo",
                "produto",
                "une",
                "loja",
                "grafico",
                "gráfico",
                "dashboard",
                "eoq",
                "sensibilidade",
                "simulacao",
                "simulação",
                "pesquisa de mercado",
                "concorrente",
            ]
        )
        followup_marker = any(
            k in q_lower
            for k in [
                "completa",
                "completo",
                "essas",
                "dessas",
                "delas",
                "agora",
                "continua",
                "continue",
                "detalhe",
                "refine",
                "refinar",
                "anterior",
            ]
        )
        strong_standalone = any(
            k in q_lower
            for k in [
                "calcule",
                "calcular",
                "gere",
                "gerar",
                "pesquise",
                "pesquisa",
                "me mostre",
                "mostre",
                "sql",
                "python",
                "parquet",
            ]
        )

        # Sensibilidade sem premissas numéricas costuma depender da rodada anterior.
        has_sensitivity = any(k in q_lower for k in ["sensibilidade", "simulação", "simulacao", "cenário", "cenario"])
        has_calc_inputs = all(
            [
                bool(re.search(r"demanda\s+anual|unidades?\s+por\s+ano", q_lower)),
                bool(re.search(r"custo\s+(?:do|de)\s+pedido", q_lower)),
                bool(re.search(r"custo\s+unit[aá]rio|pre[çc]o\s+unit[aá]rio", q_lower)),
            ]
        ) or bool(re.search(r"(?:produto|sku|item)\s+\d+", q_lower))
        needs_previous_context = has_sensitivity and not has_calc_inputs
        if "dashboard" in q_lower and any(k in q_lower for k in ["refine", "refinar", "anterior", "compare", "comparar"]):
            needs_previous_context = True

        if not needs_previous_context and has_domain_scope and (strong_standalone or not followup_marker or word_count > 12):
            return query

        wants_period_refine = any(
            k in q_lower for k in ["refine por periodo", "refinar por periodo", "por período", "por periodo", "periodo anterior", "período anterior"]
        )
        prefers_dashboard_context = "dashboard" in q_lower

        last_user_query = None
        candidate_queries: List[str] = []
        for msg in reversed(chat_history):
            if str(msg.get("role", "")).lower() == "user":
                content = str(msg.get("content", "")).strip()
                if content and content.lower() != q_lower:
                    candidate_queries.append(content)

        if wants_period_refine:
            # Prioriza última pergunta compatível com o tipo da continuação.
            for c in candidate_queries:
                c_low = c.lower()
                if prefers_dashboard_context:
                    if "dashboard" in c_low or self._is_chart_request(c_low):
                        last_user_query = c
                        break
                else:
                    if any(k in c_low for k in ["venda", "vendas", "segmento", "une", "loja"]) and not self._is_chart_request(c_low):
                        last_user_query = c
                        break

        if not last_user_query:
            last_user_query = candidate_queries[0] if candidate_queries else None

        if not last_user_query:
            return query

        merged = f"{last_user_query}. {query}"
        logger.info(f"[CONTEXT] Follow-up resolvido. atual='{query}' base='{last_user_query}'")
        return merged

    def _is_context_dependent_business_followup(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        q = (query or "").strip().lower()
        if not q:
            return False

        followup_context = self._extract_followup_context(chat_history)
        context_has_anchor = any(
            followup_context.get(key) not in (None, "", [])
            for key in ("product_code", "segment", "une", "response_breakdown", "last_user_query")
        )
        if not context_has_anchor:
            return False

        has_explicit_anchor = any(
            [
                self._extract_product_code_from_query(q),
                self._extract_segment_from_query(q),
                self._extract_une_from_query(q),
                self._extract_period_from_query(q),
            ]
        )
        if has_explicit_anchor:
            return False

        objective_markers = (
            "vende",
            "vendem",
            "venda",
            "vendas",
            "estoque",
            "ruptura",
            "rupturas",
            "líder",
            "lider",
            "menos",
            "mais",
            "top",
            "ranking",
            "giro",
            "cobertura",
        )
        word_count = len([token for token in q.split() if token.strip()])
        has_objective = any(marker in q for marker in objective_markers)
        has_reference = self._has_followup_reference_marker(q)
        return has_objective and (has_reference or word_count <= 6)

    def _is_underspecified_business_followup(self, query: str) -> bool:
        q = (query or "").strip().lower()
        if not q:
            return False
        if self._is_commercial_plan_query(q):
            return False
        if (
            (self._is_chart_request(q) or self._is_dashboard_request(q))
            and self._has_business_metric_hint(q)
            and bool(self._infer_chart_breakdown(q))
        ):
            return False

        has_explicit_anchor = any(
            [
                self._extract_product_code_from_query(q),
                self._extract_segment_from_query(q),
                self._extract_une_from_query(q),
                self._extract_period_from_query(q),
            ]
        )
        if has_explicit_anchor:
            return False

        objective_markers = (
            "vende",
            "vendem",
            "venda",
            "vendas",
            "estoque",
            "ruptura",
            "rupturas",
            "mais",
            "menos",
            "ranking",
            "top",
            "lider",
            "líder",
        )
        has_reference = self._has_followup_reference_marker(q)
        return any(marker in q for marker in objective_markers) and has_reference

    @staticmethod
    def _has_followup_reference_marker(query: str) -> bool:
        q = (query or "").strip().lower()
        if not q:
            return False
        patterns = (
            r"^e\s+",
            r"\bagora\b",
            r"\bdessas\b",
            r"\bdelas\b",
            r"\bdesse\b",
            r"\bdessa\b",
            r"\bnesse\b",
            r"\bnessa\b",
            r"\bnisso\b",
            r"\banterior\b",
            r"\búltima resposta\b",
            r"\bultima resposta\b",
        )
        return any(re.search(pattern, q) for pattern in patterns)

    def _expand_business_followup_with_context(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        import re
        from backend.app.core.utils.query_router import extract_top_limit

        q = (query or "").strip()
        if not q or not chat_history:
            return q

        if not self._is_context_dependent_business_followup(q, chat_history):
            return q

        followup_context = self._extract_followup_context(chat_history)
        product_code = (
            self._extract_product_code_from_query(q)
            or followup_context.get("product_code")
        )
        segment = self._extract_segment_from_query(q) or followup_context.get("segment")
        une = self._extract_une_from_query(q) or followup_context.get("une")
        scope_all_stores = bool(followup_context.get("scope_all_stores"))

        q_lower = q.lower()
        normalized = re.sub(r"^(e|agora)\s+", "", q_lower).strip()

        if product_code:
            if "ruptur" in normalized or "sem estoque" in normalized or "falta de estoque" in normalized:
                return f"quais lojas estão com rupturas do produto {product_code}"

            limit = extract_top_limit(q_lower)
            if "vende menos" in normalized or "vendem menos" in normalized:
                if limit and limit > 1:
                    return f"quais {limit} lojas menos vendem o produto {product_code}"
                return f"qual loja vende menos o produto {product_code}"

            if "vende mais" in normalized or "vendem mais" in normalized:
                if limit and limit > 1:
                    return f"quais {limit} lojas mais vendem o produto {product_code}"
                return f"qual loja mais vende o produto {product_code}"

            if re.fullmatch(r"(qual\s+o\s+)?estoque\??", normalized) or normalized == "o estoque?":
                return f"qual o estoque do produto {product_code}"

        additions: List[str] = []
        if product_code and "produto" not in normalized and "sku" not in normalized and "item" not in normalized:
            additions.append(f"do produto {product_code}")
        if segment and "segmento" in q_lower and "segmento" not in normalized:
            additions.append(f"do segmento {segment}")
        if une and any(token in q_lower for token in ["loja", "une"]) and not self._extract_une_from_query(q):
            additions.append(f"na UNE {une}")
        if scope_all_stores and any(token in q_lower for token in ["loja", "lojas", "une", "unes"]) and not self._extract_une_from_query(q):
            additions.append("em todas as lojas")

        if additions:
            return f"{q.rstrip(' ?')}" + " " + " ".join(additions)
        return q

    @staticmethod
    def _is_commercial_plan_query(query: str) -> bool:
        import re

        q = (query or "").lower()
        explicit_markers = (
            "plano comercial",
            "plano de ação",
            "plano de acao",
            "estratégia comercial",
            "estrategia comercial",
            "plano de 7 dias",
            "ações para 7 dias",
            "acoes para 7 dias",
            "me dê um plano",
            "me de um plano",
            "me dê ações",
            "me de acoes",
            "recomende ações",
            "recomende acoes",
        )
        if any(marker in q for marker in explicit_markers):
            return True

        if re.search(r"pr[oó]xim\w+\s+(a[çc][oõ]es|passos)", q):
            return True
        if re.search(r"o\s+que\s+fazer", q):
            return True
        if re.search(r"quais?\s+a[çc][oõ]es", q):
            return True
        if re.search(r"recomend\w+.*a[çc][oõ]es|a[çc][oõ]es.*recomend\w+", q):
            return True
        if re.search(r"como\s+(agir|melhorar|recuperar)", q):
            return True

        action_markers = (
            "próximas ações",
            "proximas acoes",
            "próximos passos",
            "proximos passos",
            "o que fazer",
            "quais ações",
            "quais acoes",
            "como agir",
            "como melhorar",
            "como recuperar",
            "ações recomenda",
            "acoes recomenda",
        )
        business_markers = (
            "une",
            "unes",
            "loja",
            "lojas",
            "venda",
            "vendas",
            "segmento",
            "segmentos",
            "categoria",
            "categorias",
            "grupo",
            "grupos",
            "estoque",
            "ruptura",
            "desempenho",
            "resultado",
            "giro",
            "demanda",
            "ranking",
        )
        return any(marker in q for marker in action_markers) and any(
            marker in q for marker in business_markers
        )

    def _is_contextual_action_followup_query(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        q = (query or "").lower()
        if self._is_commercial_plan_query(q):
            return True

        followup_action_markers = (
            "próximas ações",
            "proximas acoes",
            "próximos passos",
            "proximos passos",
            "o que fazer",
            "quais ações",
            "quais acoes",
            "como agir",
            "como melhorar",
            "como recuperar",
            "recomende ações",
            "recomende acoes",
            "me dê ações",
            "me de acoes",
            "me dê um plano",
            "me de um plano",
        )
        if not any(marker in q for marker in followup_action_markers):
            return False

        if self._has_contextual_followup_markers(q):
            return True

        followup_context = self._extract_followup_context(chat_history)
        if followup_context.get("response_breakdown") or followup_context.get("query_breakdown"):
            return True

        last_user_query = str(followup_context.get("last_user_query") or "").lower()
        business_markers = (
            "une",
            "unes",
            "loja",
            "lojas",
            "venda",
            "vendas",
            "segmento",
            "segmentos",
            "categoria",
            "categorias",
            "grupo",
            "grupos",
            "estoque",
            "ruptura",
            "desempenho",
            "resultado",
            "ranking",
        )
        return any(marker in last_user_query for marker in business_markers)

    @staticmethod
    def _extract_plan_days(query: str, default_days: int = 7) -> int:
        import re

        q = (query or "").lower()
        match = re.search(r"\b(\d{1,2})\s*dias?\b", q)
        if match:
            try:
                # Janela operacional útil: entre 3 e 30 dias.
                return max(3, min(30, int(match.group(1))))
            except ValueError:
                return default_days
        if "semana" in q or "semanal" in q:
            return 7
        return default_days

    def _infer_breakdown_from_assistant_text(self, content: str) -> Optional[str]:
        text = str(content or "")
        if not text.strip():
            return None

        header_lines = [line.strip().lower() for line in text.splitlines() if line.strip().startswith("|")]
        header = header_lines[0] if header_lines else text.lower()

        if "loja (une)" in header or __import__("re").search(r"\|\s*une\s*\|", header):
            return "LOJA"
        if "segmento" in header:
            return "SEGMENTO"
        if "categoria" in header:
            return "CATEGORIA"
        if "grupo" in header:
            return "GRUPO"
        if "fabricante" in header or "marca" in header:
            return "FABRICANTE"
        if "produto" in header or "sku" in header or "item" in header:
            return "PRODUTO"
        return None

    def _extract_followup_context(self, chat_history: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        context: Dict[str, Any] = {}
        if not chat_history:
            return context

        last_user_query = None
        last_assistant_msg: Optional[Dict[str, Any]] = None

        for msg in reversed(chat_history):
            role = str(msg.get("role", "")).lower()
            if role == "assistant" and last_assistant_msg is None:
                last_assistant_msg = msg
            elif role == "user" and last_user_query is None:
                content = str(msg.get("content", "")).strip()
                if content:
                    last_user_query = content
            if last_user_query and last_assistant_msg is not None:
                break

        if last_user_query:
            context["last_user_query"] = last_user_query

        if isinstance(last_assistant_msg, dict):
            assistant_content = str(last_assistant_msg.get("content", "")).strip()
            if assistant_content:
                context["last_assistant_content"] = assistant_content

            metadata = last_assistant_msg.get("metadata")
            if isinstance(metadata, dict):
                meta_context = metadata.get("context")
                if isinstance(meta_context, dict):
                    for key in (
                        "response_breakdown",
                        "query_breakdown",
                        "period",
                        "scope_all_stores",
                        "product_code",
                        "segment",
                        "une",
                        "market_product_hint",
                        "market_competitors",
                        "response_type",
                        "has_dashboard",
                        "has_chart",
                        "source",
                        "dashboard_title",
                        "dashboard_filters",
                    ):
                        if meta_context.get(key) not in (None, "", []):
                            context[key] = meta_context.get(key)

                for key in ("source", "confidence", "mode"):
                    if metadata.get(key) not in (None, "", []):
                        context[key] = metadata.get(key)

            if not context.get("response_breakdown") and assistant_content:
                inferred = self._infer_breakdown_from_assistant_text(assistant_content)
                if inferred:
                    context["response_breakdown"] = inferred

        return context

    def _is_dashboard_context_followup_query(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        q = (query or "").lower()
        followup_context = self._extract_followup_context(chat_history)
        has_dashboard_context = bool(
            followup_context.get("has_dashboard")
            or str(followup_context.get("response_type") or "").lower() == "dashboard"
            or "dashboard" in str(followup_context.get("last_user_query") or "").lower()
        )
        if not has_dashboard_context:
            return False

        detail_markers = (
            "detalhe",
            "aprofunde",
            "pontos críticos",
            "pontos criticos",
            "critico",
            "crítico",
            "criticos",
            "críticos",
            "o que você recomenda",
            "o que voce recomenda",
            "quais ações",
            "quais acoes",
            "próximas ações",
            "proximas acoes",
            "próximos passos",
            "proximos passos",
        )
        return any(marker in q for marker in detail_markers) and (
            self._has_contextual_followup_markers(q) or "dashboard" in q
        )

    def _is_dashboard_followup_nonvisual_query(self, query: str) -> bool:
        q = (query or "").lower()
        if "dashboard" not in q:
            return False
        markers = (
            "detalhe",
            "aprofunde",
            "pontos críticos",
            "pontos criticos",
            "o que você recomenda",
            "o que voce recomenda",
            "quais ações",
            "quais acoes",
            "próximas ações",
            "proximas acoes",
            "próximos passos",
            "proximos passos",
        )
        return any(marker in q for marker in markers)

    def _is_market_research_followup_query(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        q = (query or "").lower()
        followup_context = self._extract_followup_context(chat_history)
        source = str(followup_context.get("source") or "").lower()
        last_assistant = str(followup_context.get("last_assistant_content") or "").lower()
        has_market_context = (
            "pesquisar_precos_concorrentes" in source
            or "pesquisar_mercado_web" in source
            or "pesquisa de mercado" in last_assistant
            or "pesquisa concorrencial" in last_assistant
        )
        if not has_market_context:
            return False

        markers = (
            "negociação",
            "negociacao",
            "negociar",
            "o que você recomenda",
            "o que voce recomenda",
            "quais ações",
            "quais acoes",
            "próximos passos",
            "proximos passos",
            "estratégia de compra",
            "estrategia de compra",
        )
        return any(marker in q for marker in markers) and (
            self._has_contextual_followup_markers(q) or "pesquisa" in q
        )

    def _build_market_research_followup_response(
        self,
        user_query: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not self._is_market_research_followup_query(user_query, chat_history):
            return None

        import re
        import unicodedata

        followup_context = self._extract_followup_context(chat_history)
        assistant_text = str(followup_context.get("last_assistant_content") or "")
        if not assistant_text.strip():
            return None

        normalized_text = (
            unicodedata.normalize("NFKD", assistant_text)
            .encode("ascii", "ignore")
            .decode("ascii")
            .lower()
        )

        avg_match = re.search(
            r"preco medio de (?:mercado|referencia):\s*r\$\s*([\d\.,]+)",
            normalized_text,
            re.IGNORECASE,
        )
        range_match = re.search(
            r"faixa(?: de preco encontrada)?:\s*r\$\s*([\d\.,]+)\s*(?:ate|a)\s*r\$\s*([\d\.,]+)",
            normalized_text,
            re.IGNORECASE,
        )
        competitors_match = re.search(
            r"concorrentes com pre[çc]o identificado:\s*(.+)",
            assistant_text,
            re.IGNORECASE,
        )
        product_match = re.search(r"para\s+\*\*(.+?)\*\*", assistant_text, re.IGNORECASE)

        avg_price = avg_match.group(1) if avg_match else None
        range_min = range_match.group(1) if range_match else None
        range_max = range_match.group(2) if range_match else None
        competitors = competitors_match.group(1).strip(" .") if competitors_match else "evidência pública disponível"
        product = product_match.group(1).strip() if product_match else None
        if not product:
            last_user_query = str(followup_context.get("last_user_query") or "")
            product = re.sub(
                r"(?i)(fa[çc]a\s+uma?\s+)?pesquisa\s+de\s+mercado\s+(do\s+produto\s+|de\s+|para\s+)?",
                "",
                last_user_query,
            ).strip(" .") or "item pesquisado"

        price_reference = (
            f"- Referência de preço: média pública em R$ {avg_price} e faixa entre R$ {range_min} e R$ {range_max}.\n"
            if avg_price and range_min and range_max
            else ""
        )
        negotiation_anchor = (
            f"- Abra a negociação usando a faixa observada como âncora e tente iniciar próximo ao piso público (R$ {range_min}) quando frete e prazo forem equivalentes.\n"
            if range_min
            else "- Abra a negociação usando a média pública como referência inicial e ajuste pela condição comercial real.\n"
        )
        avg_cap = (
            f"- Use R$ {avg_price} como teto de referência para compras spot; acima disso, só avance se prazo, marca ou pacote forem claramente superiores.\n"
            if avg_price
            else "- Valide o preço ofertado contra a média da pesquisa antes de fechar o pedido.\n"
        )

        msg = (
            "## Resumo executivo\n"
            f"- Recomendação de negociação estruturada com base na última pesquisa de mercado para {product}.\n"
            f"- Concorrentes com evidência pública: {competitors}.\n"
            + price_reference
            + "\n## Próximas ações\n"
            + negotiation_anchor
            + avg_cap
            + "- Confirme frete, prazo, quantidade mínima e disponibilidade antes de fechar.\n"
            + "- Se a cobertura estiver concentrada em poucos marketplaces, valide 2-3 cotações adicionais para reduzir risco de preço fora do mercado."
        )
        return {
            "type": "text",
            "result": {"mensagem": msg},
            "source": "context.market_research_followup",
            "confidence": 0.82,
            "mode": "deterministic_contextual_followup",
        }

    def _is_market_competitor_followup_query(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        q = (query or "").lower()
        followup_context = self._extract_followup_context(chat_history)
        source = str(followup_context.get("source") or "").lower()
        last_assistant = str(followup_context.get("last_assistant_content") or "").lower()
        has_market_context = (
            "pesquisar_precos_concorrentes" in source
            or "pesquisar_mercado_web" in source
            or "context.market_research_followup" in source
            or "pesquisa de mercado" in last_assistant
            or "pesquisa concorrencial" in last_assistant
        )
        if not has_market_context:
            return False

        mentions_competitor = bool(self._extract_competitors_from_query(q))
        mentions_marketplace = any(alias in q for alias in ("mercado livre", "mercadolivre", "meli"))
        if not (mentions_competitor or mentions_marketplace):
            return False

        short_followup = len([word for word in q.split() if word.strip()]) <= 8
        return short_followup or self._has_contextual_followup_markers(q) or q.startswith(("e ", "na ", "no "))

    def _build_market_competitor_followup_query(
        self,
        user_query: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[str]:
        if not self._is_market_competitor_followup_query(user_query, chat_history):
            return None

        followup_context = self._extract_followup_context(chat_history)
        base_query = str(followup_context.get("last_user_query") or "")
        market_product = (
            str(followup_context.get("market_product_hint") or "").strip()
            or str(self._extract_market_product_hint(base_query) or "").strip()
        )
        if not market_product:
            return None

        q = (user_query or "").lower()
        competitors = self._extract_competitors_from_query(q)
        state = self._extract_state_from_query(user_query) or self._extract_state_from_query(base_query)

        if any(alias in q for alias in ("mercado livre", "mercadolivre", "meli")) and not competitors.replace("mercado livre", "").strip(", "):
            resolved = f"pesquisa de mercado de {market_product} no mercado livre"
        elif competitors:
            resolved = f"pesquisa de mercado de {market_product} nos concorrentes {competitors.replace(',', ', ')}"
        else:
            resolved = f"pesquisa de mercado de {market_product}"

        if state:
            resolved += f" em {state}"
        return resolved

    def _configure_market_followup_tool_selection(
        self,
        user_query: str,
        tool_selection: Any,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        resolved_market_query = self._build_market_competitor_followup_query(user_query, chat_history)
        if not resolved_market_query:
            return False

        q = resolved_market_query.lower()
        segment = self._extract_segment_from_query(resolved_market_query)
        state = self._extract_state_from_query(resolved_market_query) or "RJ"
        competitors = self._extract_competitors_from_query(q)
        mentions_ml = any(alias in q for alias in ("mercado livre", "mercadolivre", "meli"))
        mentions_other_competitor = any(name in competitors for name in ("amazon", "kalunga", "americanas", "shopee", "le biscuit", "bellart", "amigao", "tid's", "tubarao", "casa&video"))

        if mentions_ml and not mentions_other_competitor:
            tool_selection.tool_name = "pesquisar_mercado_web"
            tool_selection.tool_params = {
                "termo_pesquisa": self._extract_market_product_hint(resolved_market_query) or resolved_market_query,
                "limite": "15",
            }
            tool_selection.confidence = max(float(tool_selection.confidence or 0), 0.94)
            return True

        tool_selection.tool_name = "pesquisar_precos_concorrentes"
        tool_selection.tool_params = {
            "descricao_produto": resolved_market_query,
            "segmento": segment or "",
            "estado": state,
            "cidade": "",
            "limite": "15",
            "concorrentes": competitors,
        }
        tool_selection.confidence = max(float(tool_selection.confidence or 0), 0.94)
        return True

    def _build_contextual_followup_response(
        self,
        user_query: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        market_response = self._build_market_research_followup_response(user_query, chat_history)
        if market_response is not None:
            return market_response
        return None

    def _build_dashboard_followup_chart_query(
        self,
        user_query: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        followup_context = self._extract_followup_context(chat_history)
        breakdown = str(
            followup_context.get("response_breakdown")
            or followup_context.get("query_breakdown")
            or "LOJA"
        ).upper()
        dimension_label = {
            "LOJA": "UNE",
            "SEGMENTO": "segmento",
            "CATEGORIA": "categoria",
            "GRUPO": "grupo",
            "FABRICANTE": "fabricante",
            "PRODUTO": "produto",
        }.get(breakdown, "UNE")
        filters = followup_context.get("dashboard_filters")
        if not isinstance(filters, dict):
            filters = {}

        scope_parts: List[str] = [f"vendas por {dimension_label}"]
        segment = filters.get("segmento") or followup_context.get("segment")
        if segment:
            scope_parts.append(f"do segmento {segment}")
        une = filters.get("une") or followup_context.get("une")
        if une and dimension_label.lower() != "une":
            scope_parts.append(f"na UNE {une}")
        period = followup_context.get("period")
        if period:
            scope_parts.append(f"no período {period}")

        focus = "com foco nos pontos críticos e menores vendas"
        q = (user_query or "").lower()
        if any(token in q for token in ["recomenda", "ações", "acoes", "passos"]):
            focus = "com foco nas menores vendas para orientar ações recomendadas"

        return "gere um gráfico de " + " ".join(scope_parts) + f" {focus}"

    def _configure_dashboard_followup_tool_selection(
        self,
        user_query: str,
        tool_selection: Any,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        if not self._is_dashboard_context_followup_query(user_query, chat_history):
            return False

        followup_context = self._extract_followup_context(chat_history)
        breakdown = str(
            followup_context.get("response_breakdown")
            or followup_context.get("query_breakdown")
            or "LOJA"
        ).upper()
        chart_query = self._build_dashboard_followup_chart_query(user_query, chat_history)
        filters = followup_context.get("dashboard_filters")
        if not isinstance(filters, dict):
            filters = {}

        params: Dict[str, Any] = {
            "descricao": chart_query,
            "tipo_grafico": "bar",
            "quebra_por": breakdown,
            "limite": 20,
        }

        segment = filters.get("segmento") or followup_context.get("segment")
        if segment:
            params["filtro_segmento"] = segment

        une = filters.get("une") or followup_context.get("une")
        if une and breakdown != "LOJA":
            params["filtro_une"] = str(une)

        if followup_context.get("scope_all_stores"):
            params["limite"] = 50

        tool_selection.tool_name = "gerar_grafico_universal_v2"
        tool_selection.tool_params = params
        tool_selection.confidence = max(float(getattr(tool_selection, "confidence", 0) or 0), 0.9)
        return True

    @staticmethod
    def _has_contextual_followup_markers(query: str) -> bool:
        q = (query or "").lower()
        markers = (
            "com base",
            "continue",
            "continuar",
            "continua",
            "detalhe",
            "agora",
            "última resposta",
            "ultima resposta",
            "anterior",
            "próximas ações",
            "proximas acoes",
            "nisso",
        )
        return any(marker in q for marker in markers)

    def _should_use_reference_examples(
        self,
        query: str,
        tool_selection: Optional[Any] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        q = (query or "").lower().strip()
        if not q:
            return False

        if self._is_contextual_action_followup_query(q, chat_history):
            return False

        if self._has_contextual_followup_markers(q):
            return False

        if chat_history:
            followup_context = self._extract_followup_context(chat_history)
            if followup_context.get("response_breakdown") or followup_context.get("last_assistant_content"):
                if self._is_chart_request(q) or self._is_dashboard_request(q) or self._is_explicit_business_query(q):
                    return False

        confidence = 0.0
        if tool_selection is not None:
            try:
                confidence = float(getattr(tool_selection, "confidence", 0) or 0)
            except Exception:
                confidence = 0.0

        if confidence >= 0.75 and (
            self._is_chart_request(q)
            or self._is_dashboard_request(q)
            or self._is_explicit_business_query(q)
        ):
            return False

        return True

    def _should_attempt_routed_tool_rescue(
        self,
        user_query: str,
        llm_text: str,
        tool_selection: Optional[Any],
        successful_tool_calls: int,
    ) -> bool:
        if successful_tool_calls > 0 or tool_selection is None:
            return False

        tool_name = str(getattr(tool_selection, "tool_name", "") or "").strip()
        if not tool_name or self._find_tool_by_name(tool_name) is None:
            return False

        q = (user_query or "").lower()
        strategic_followup = self._has_contextual_followup_markers(q) and any(
            marker in q
            for marker in (
                "próximas ações",
                "proximas acoes",
                "próximos passos",
                "proximos passos",
                "o que fazer",
                "quais ações",
                "quais acoes",
                "como agir",
                "como melhorar",
                "como recuperar",
                "recomende ações",
                "recomende acoes",
            )
        )
        explicit_data_need = (
            self._is_chart_request(q)
            or self._is_dashboard_request(q)
            or self._is_commercial_plan_query(q)
            or self._is_explicit_business_query(q)
            or strategic_followup
        )
        if not explicit_data_need:
            return False

        try:
            confidence = float(getattr(tool_selection, "confidence", 0) or 0)
        except Exception:
            confidence = 0.0

        if confidence < 0.70 and not (self._is_chart_request(q) or self._is_dashboard_request(q)):
            return False

        text = str(llm_text or "").lower().strip()
        if not text:
            return True

        clarification_markers = (
            "confirme",
            "me informe",
            "qual período",
            "qual periodo",
            "quer que eu",
            "posso detalhar",
            "não encontrei dados",
            "nao encontrei dados",
            "preciso de mais",
        )
        if any(marker in text for marker in clarification_markers):
            return False

        return True

    async def _attempt_routed_tool_rescue(
        self,
        user_query: str,
        tool_selection: Any,
        on_progress: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    ) -> Optional[Dict[str, Any]]:
        tool_name = str(getattr(tool_selection, "tool_name", "") or "").strip()
        if not tool_name:
            return None

        tool_to_run = self._find_tool_by_name(tool_name)
        if tool_to_run is None:
            return None

        tool_params = dict(getattr(tool_selection, "tool_params", {}) or {})
        await self._emit_progress(on_progress, tool_name, "executing")

        primary_error: Optional[Exception] = None
        try:
            tool_result = await asyncio.to_thread(
                self._execute_tool_with_recovery,
                tool_to_run,
                tool_name,
                tool_params,
            )
        except Exception as error:
            primary_error = error
            logger.warning(f"[TOOL-RECOVERY] Ferramenta primária {tool_name} falhou com exceção: {error}")
            tool_result = {"status": "error", "error": str(error)}
        active_tool_name = tool_name
        active_tool_params = tool_params
        active_tool_result = tool_result

        if self._should_attempt_semantic_recovery(
            user_query=user_query,
            tool_name=tool_name,
            tool_result=tool_result,
            tool_error=primary_error,
        ):
            recovered = await self._execute_semantic_tool_fallback(
                user_query=user_query,
                primary_tool_name=tool_name,
                primary_tool_params=tool_params,
                fallback_tools=getattr(tool_selection, "fallback_tools", []),
                on_progress=on_progress,
            )
            if recovered:
                active_tool_name = str(recovered["tool_name"])
                active_tool_params = dict(recovered["tool_params"])
                active_tool_result = recovered["tool_result"]
            elif primary_error is not None:
                return None

        return self._format_tool_result_for_path(
            user_query,
            active_tool_name,
            active_tool_result,
            active_tool_params,
        )

    def _attempt_routed_tool_rescue_sync(
        self,
        user_query: str,
        tool_selection: Any,
    ) -> Optional[Dict[str, Any]]:
        tool_name = str(getattr(tool_selection, "tool_name", "") or "").strip()
        if not tool_name:
            return None

        tool_to_run = self._find_tool_by_name(tool_name)
        if tool_to_run is None:
            return None

        tool_params = dict(getattr(tool_selection, "tool_params", {}) or {})
        primary_error: Optional[Exception] = None
        try:
            tool_result = self._execute_tool_with_recovery(
                tool_to_run,
                tool_name,
                tool_params,
            )
        except Exception as error:
            primary_error = error
            logger.warning(f"[TOOL-RECOVERY][SYNC] Ferramenta primária {tool_name} falhou com exceção: {error}")
            tool_result = {"status": "error", "error": str(error)}
        active_tool_name = tool_name
        active_tool_params = tool_params
        active_tool_result = tool_result

        if self._should_attempt_semantic_recovery(
            user_query=user_query,
            tool_name=tool_name,
            tool_result=tool_result,
            tool_error=primary_error,
        ):
            recovered = self._execute_semantic_tool_fallback_sync(
                user_query=user_query,
                primary_tool_name=tool_name,
                primary_tool_params=tool_params,
                fallback_tools=getattr(tool_selection, "fallback_tools", []),
            )
            if recovered:
                active_tool_name = str(recovered["tool_name"])
                active_tool_params = dict(recovered["tool_params"])
                active_tool_result = recovered["tool_result"]
            elif primary_error is not None:
                return None

        return self._format_tool_result_for_path(
            user_query,
            active_tool_name,
            active_tool_result,
            active_tool_params,
        )

    def _configure_commercial_plan_tool_selection(
        self,
        user_query: str,
        tool_selection: Any,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        if not self._is_contextual_action_followup_query(user_query, chat_history):
            return False

        q = (user_query or "").lower()
        followup_context = self._extract_followup_context(chat_history)
        base_query = str(followup_context.get("last_user_query") or "")

        breakdown_map = {
            "LOJA": ["UNE"],
            "SEGMENTO": ["NOMESEGMENTO"],
            "CATEGORIA": ["NOMECATEGORIA"],
            "GRUPO": ["NOMEGRUPO"],
            "FABRICANTE": ["NOMEFABRICANTE"],
            "PRODUTO": ["PRODUTO", "NOME"],
        }

        if any(token in q for token in ["une", "unes", "loja", "lojas"]):
            breakdown = "LOJA"
        elif any(token in q for token in ["segmento", "segmentos"]):
            breakdown = "SEGMENTO"
        elif any(token in q for token in ["categoria", "categorias"]):
            breakdown = "CATEGORIA"
        elif any(token in q for token in ["grupo", "grupos"]):
            breakdown = "GRUPO"
        elif any(token in q for token in ["produto", "produtos", "sku", "item", "itens"]):
            breakdown = "PRODUTO"
        else:
            breakdown = str(followup_context.get("response_breakdown") or followup_context.get("query_breakdown") or "LOJA").upper()

        produto = (
            self._extract_product_code_from_query(user_query)
            or self._extract_product_code_from_query(base_query)
            or followup_context.get("product_code")
        )
        segmento = self._extract_segment_from_query(user_query) or self._extract_segment_from_query(base_query) or followup_context.get("segment")
        une = self._extract_une_from_query(user_query) or self._extract_une_from_query(base_query) or followup_context.get("une")

        is_high_performer_focus = any(token in q for token in ["maior", "maiores", "melhores", "top", "lideres", "líderes"])
        scope_all_stores = self._is_all_stores_request(user_query) or self._is_all_stores_request(base_query) or bool(
            followup_context.get("scope_all_stores")
        )

        filtros: Dict[str, Any] = {}
        if produto:
            filtros["PRODUTO"] = int(produto)
        if segmento and breakdown != "SEGMENTO":
            filtros["NOMESEGMENTO"] = segmento
        if une and breakdown != "LOJA":
            filtros["UNE"] = int(une) if str(une).isdigit() else une

        tool_selection.tool_name = "consultar_dados_flexivel"
        tool_selection.tool_params = {
            "agregacao": "SUM",
            "coluna_agregacao": "VENDA_30DD",
            "agrupar_por": breakdown_map.get(breakdown, ["UNE"]),
            "ordenar_por": "valor",
            "ordem_desc": is_high_performer_focus,
            "limite": 200 if scope_all_stores and breakdown == "LOJA" else 50,
            "filtros": filtros,
        }
        tool_selection.confidence = max(float(tool_selection.confidence or 0), 0.93)
        return True

    def _enrich_tool_selection_for_business(
        self,
        user_query: str,
        tool_selection: Any,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Ajusta roteamento/parâmetros para perguntas comerciais comuns, mantendo dados reais.
        """
        q = (user_query or "").lower()
        ml_aliases = ["mercado livre", "mercadolivre", "meli"]
        other_competitors = [
            "americanas", "kalunga", "bellart", "shopee", "amazon",
            "casa&video", "casa e video", "le biscuit", "lebiscuit",
            "tubarão", "tubarao", "tid", "amigão", "amigao",
        ]
        mentions_ml = any(alias in q for alias in ml_aliases)
        mentions_other_competitor = any(name in q for name in other_competitors)
        is_all_stores = self._is_all_stores_request(user_query)
        segment = self._extract_segment_from_query(user_query)
        une = self._extract_une_from_query(user_query)
        period = self._extract_period_from_query(user_query)
        state = self._extract_state_from_query(user_query) or "RJ"

        if self._configure_commercial_plan_tool_selection(user_query, tool_selection, chat_history=chat_history):
            return

        if self._configure_dashboard_followup_tool_selection(user_query, tool_selection, chat_history=chat_history):
            return

        if self._configure_market_followup_tool_selection(user_query, tool_selection, chat_history=chat_history):
            return

        if self._is_specific_competitor_query(user_query):
            # Mercado Livre explícito sem outro concorrente: usar pesquisa aberta.
            if mentions_ml and not mentions_other_competitor:
                import re as _re
                product_query = _re.sub(
                    r"(?i)(fa[çc]a\s+uma?\s+)?pesquisa\s+de\s+mercado\s+(do\s+produto\s+|de\s+|para\s+)?",
                    "", user_query
                ).strip() or user_query
                tool_selection.tool_name = "pesquisar_mercado_web"
                tool_selection.tool_params = {
                    "termo_pesquisa": product_query,
                    "limite": "15",
                }
                tool_selection.confidence = max(float(tool_selection.confidence or 0), 0.92)
                return

            # Concorrente específico mencionado → pesquisar_precos_concorrentes
            competitors = self._extract_competitors_from_query(user_query)
            tool_selection.tool_name = "pesquisar_precos_concorrentes"
            tool_selection.tool_params = {
                "descricao_produto": user_query,
                "segmento": segment or "",
                "estado": state,
                "cidade": "",
                "limite": "15",
                "concorrentes": competitors,
            }
            tool_selection.confidence = max(float(tool_selection.confidence or 0), 0.92)
            return

        if self._is_market_research_query(user_query):
            # Pesquisa de mercado genérica: prioriza ferramenta aberta multi-provider.
            tool_selection.tool_name = "pesquisar_mercado_web"
            tool_selection.tool_params = {
                "termo_pesquisa": self._extract_market_product_hint(user_query) or user_query,
                "limite": "15",
            }
            tool_selection.confidence = max(float(tool_selection.confidence or 0), 0.92)
            return

        # Dashboard com filtros executivos: prioriza ferramenta universal para suportar recortes por segmento/UNE.
        if self._is_dashboard_request(user_query):
            breakdown = self._infer_chart_breakdown(user_query)
            tool_selection.tool_name = "gerar_grafico_universal_v2"
            tool_selection.tool_params = {
                "descricao": user_query,
                "tipo_grafico": "bar",
                "limite": 200 if is_all_stores else 50,
            }
            if segment:
                tool_selection.tool_params["filtro_segmento"] = segment
            if une:
                tool_selection.tool_params["filtro_une"] = une
            if breakdown:
                tool_selection.tool_params["quebra_por"] = breakdown
            # Preserva contexto temporal para o formatter de dashboard.
            if period:
                tool_selection.tool_params["periodo"] = period
            if is_all_stores:
                tool_selection.tool_params["escopo"] = "rede"
            tool_selection.confidence = max(float(tool_selection.confidence or 0), 0.93)
            return

        # Pedido explícito de gráfico: direciona para ferramenta de visualização.
        if self._is_chart_request(user_query):
            breakdown = self._infer_chart_breakdown(user_query)
            tool_selection.tool_name = "gerar_grafico_universal_v2"
            tool_selection.tool_params = {
                "descricao": user_query,
                "tipo_grafico": "bar",
                "limite": 200 if is_all_stores else 50,
                "filtro_segmento": segment,
            }
            if breakdown:
                tool_selection.tool_params["quebra_por"] = breakdown
            tool_selection.confidence = max(float(tool_selection.confidence or 0), 0.90)
            return

        # Perguntas de vendas por segmento em todas as lojas: reforça recorte correto.
        if tool_selection.tool_name == "consultar_dados_flexivel":
            params = dict(tool_selection.tool_params or {})
            filtros = params.get("filtros", {})
            if not isinstance(filtros, dict):
                filtros = {}

            if is_all_stores:
                # Remove filtro por UNE indevido quando a pergunta pede toda a rede.
                filtros.pop("UNE", None)
                filtros.pop("une", None)
                params["limite"] = 500

            if segment and not any(k.upper() in {"NOMESEGMENTO", "SEGMENTO"} for k in filtros.keys()):
                filtros["NOMESEGMENTO"] = segment

            # Garante colunas suficientes para consolidação executiva por UNE.
            cols = params.get("colunas")
            if not isinstance(cols, list):
                cols = []
            for required in ["UNE", "VENDA_30DD", "ESTOQUE_UNE", "NOMESEGMENTO", "NOME", "PRODUTO"]:
                if required not in cols:
                    cols.append(required)

            # Pedido explícito de "total" por UNE/loja: força agregação correta.
            is_sales_by_store_request = (
                any(k in q for k in ["une", "unes", "loja", "lojas"])
                and any(k in q for k in ["venda", "vendas"])
                and (is_all_stores or any(k in q for k in ["total", "venda total", "por une", "por loja", "todas"]))
            )
            if is_sales_by_store_request:
                tool_selection.tool_name = "consultar_dados_flexivel"
                tool_selection.confidence = max(float(tool_selection.confidence or 0), 0.90)
                params["agregacao"] = "SUM"
                params["coluna_agregacao"] = "VENDA_30DD"
                params["agrupar_por"] = ["UNE"]
                params["ordenar_por"] = "valor"
                params["ordem_desc"] = True
                params["limite"] = 200 if is_all_stores else max(int(params.get("limite", 50) or 50), 50)
                params["colunas"] = ["UNE"]
            else:
                params["colunas"] = cols

            params["filtros"] = filtros
            tool_selection.tool_params = params

    def _should_use_deterministic_path(self, tool_name: str, confidence: float) -> bool:
        """
        Define quando executar ferramenta diretamente sem rodada LLM,
        reduzindo custo e falhas em consultas determinísticas.
        """
        # Para consultas de dados comerciais, priorizamos decisão da LLM
        # (tool selection + síntese contextual), evitando respostas engessadas.
        deterministic_tools = {
            "encontrar_rupturas_criticas",
            "consultar_dados_flexivel",
            "analisar_historico_vendas",
            "pesquisar_precos_concorrentes",
            "pesquisar_mercado_web",
        }
        return tool_name in deterministic_tools and confidence >= 0.78

    def _format_deterministic_result(
        self,
        user_query: str,
        tool_name: str,
        tool_result: Any,
        tool_params: Optional[Dict[str, Any]] = None,
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

        if tool_name == "analisar_produto_todas_lojas":
            from backend.app.core.utils.query_router import (
                is_product_rupture_query,
                is_product_store_leader_query,
            )

            produto = tool_result.get("produto") or (tool_params or {}).get("produto_codigo") or "-"
            nome = str(tool_result.get("nome") or "Produto").strip()
            mensagem = str(tool_result.get("mensagem") or "").strip()
            if not bool(tool_result.get("success", False)):
                detalhe = mensagem or f"Não encontrei dados do produto {produto} na base consultada."
                sugestao = str(tool_result.get("sugestao") or "Confirme o código e tente novamente.").strip()
                return {
                    "type": "text",
                    "result": {
                        "mensagem": (
                            "## Resumo executivo\n"
                            f"- {detalhe}\n\n"
                            "## Tabela operacional\n"
                            "- Sem dados tabulares adicionais para exibir nesta resposta.\n\n"
                            "## Próximas ações\n"
                            f"- {sugestao}"
                        )
                    },
                }

            resumo = tool_result.get("resumo", {}) if isinstance(tool_result.get("resumo"), dict) else {}
            total_lojas = int(resumo.get("total_lojas_com_produto", 0) or 0)
            lojas_com_estoque = int(resumo.get("lojas_com_estoque", 0) or 0)
            lojas_em_ruptura = int(resumo.get("lojas_em_ruptura", 0) or 0)
            total_vendas = resumo.get("total_vendas_30d", 0) or 0
            total_estoque = resumo.get("total_estoque_lojas", 0) or 0
            estoque_cd = resumo.get("estoque_cd", 0) or 0
            top_lojas = tool_result.get("top_5_lojas_vendas", []) if isinstance(tool_result.get("top_5_lojas_vendas"), list) else []
            rupturas = tool_result.get("lojas_em_ruptura", []) if isinstance(tool_result.get("lojas_em_ruptura"), list) else []

            def _fmt_money(v: Any) -> str:
                try:
                    return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                except Exception:
                    return str(v or "-")

            def _table(rows: List[Dict[str, Any]]) -> str:
                header = "| Loja (UNE) | Sigla | Venda 30 dias (R$) | Estoque |\n|---|---|---|---|\n"
                body = []
                for row in rows[:5]:
                    body.append(
                        "| "
                        + " | ".join(
                            [
                                str(row.get("une") or "-"),
                                str(row.get("nome") or "-"),
                                _fmt_money(row.get("vendas_30d")),
                                _fmt_money(row.get("estoque")),
                            ]
                        )
                        + " |"
                    )
                return header + ("\n".join(body) if body else "| - | - | - | - |")

            if is_product_rupture_query(user_query):
                if not rupturas:
                    msg = (
                        "## Resumo executivo\n"
                        f"- Não identifiquei lojas em ruptura do produto {produto} ({nome}) no recorte atual.\n"
                        f"- Cobertura analisada: {total_lojas} lojas com o produto.\n\n"
                        "## Tabela operacional\n"
                        "- Sem lojas em ruptura para este produto.\n\n"
                        "## Próximas ações\n"
                        "- Se quiser, eu listo as lojas com menor cobertura de estoque para antecipar risco de ruptura.\n"
                        "- Também posso comparar o estoque atual com a linha verde por UNE."
                    )
                    return {"type": "text", "result": {"mensagem": msg}}

                msg = (
                    "## Resumo executivo\n"
                    f"- Identifiquei {len(rupturas)} loja(s) em ruptura do produto {produto} ({nome}).\n"
                    f"- Cobertura analisada: {total_lojas} lojas com o produto.\n"
                    f"- Estoque CD disponível: {_fmt_money(estoque_cd)}.\n\n"
                    "## Tabela operacional\n"
                    + _table(rupturas)
                    + "\n\n## Próximas ações\n"
                    "- Priorize reposição imediata nas lojas em ruptura com venda recente para reduzir perda de venda.\n"
                    "- Avalie transferência entre UNEs ou uso do estoque CD antes de ampliar compra.\n"
                    "- Se quiser, eu também listo as lojas com menor cobertura para prevenção de novas rupturas."
                )
                return {"type": "text", "result": {"mensagem": msg}}

            if is_product_store_leader_query(user_query):
                lider = top_lojas[0] if top_lojas else {}
                une_lider = str(lider.get("une") or "-")
                sigla_lider = str(lider.get("nome") or "-")
                venda_lider = _fmt_money(lider.get("vendas_30d"))
                estoque_lider = _fmt_money(lider.get("estoque"))
                msg = (
                    "## Resumo executivo\n"
                    f"- A loja que mais vende o produto {produto} ({nome}) é a UNE {une_lider} ({sigla_lider}).\n"
                    f"- Venda 30 dias da loja líder: R$ {venda_lider}. Estoque atual: {estoque_lider}.\n"
                    f"- Cobertura analisada: {total_lojas} lojas com o produto.\n\n"
                    "## Tabela operacional\n"
                    + _table(top_lojas)
                    + "\n\n## Próximas ações\n"
                    "- Replique preço, exposição e disponibilidade da loja líder nas demais UNEs com potencial.\n"
                    "- Valide ruptura e cobertura das lojas abaixo do top 5 antes de redistribuir estoque.\n"
                    "- Se quiser, eu comparo a loja líder com a UNE de menor venda desse produto."
                )
                return {"type": "text", "result": {"mensagem": msg}}

            table_md = _table(top_lojas)
            if rupturas:
                table_md += (
                    "\n\n**Rupturas críticas**\n"
                    + _table(rupturas)
                )

            msg = (
                "## Resumo executivo\n"
                f"- Produto {produto} ({nome}) encontrado em {total_lojas} lojas.\n"
                f"- Vendas nos últimos 30 dias: R$ {_fmt_money(total_vendas)}. "
                f"Estoque total nas lojas: {_fmt_money(total_estoque)}. Estoque CD: {_fmt_money(estoque_cd)}.\n"
                f"- Lojas com estoque: {lojas_com_estoque}. Lojas em ruptura: {lojas_em_ruptura}.\n\n"
                "## Tabela operacional\n"
                + table_md
                + "\n\n## Próximas ações\n"
                "- Priorize reposição imediata nas lojas em ruptura com venda recente para reduzir perda de venda.\n"
                "- Replique preço, exposição e sortimento das lojas líderes nas unidades abaixo da média.\n"
                "- Valide transferência ou reabastecimento a partir do estoque CD antes de ampliar compra."
            )
            return {"type": "text", "result": {"mensagem": msg}}

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

        if tool_name in ("pesquisar_precos_concorrentes", "pesquisar_mercado_web"):
            raw_items = tool_result.get("itens", []) or []
            itens = [item for item in raw_items if isinstance(item, dict)]
            itens = self._filter_relevant_market_items(user_query, itens)
            low_relevance_detected = bool(raw_items and not itens)
            total_itens = len(itens)
            fontes = tool_result.get("fontes_consultadas", []) or []
            escopo = tool_result.get("escopo", {}) if isinstance(tool_result.get("escopo"), dict) else {}
            fallback_benchmark = bool(tool_result.get("fallback_benchmark_aplicado", False))

            source = str(tool_result.get("source") or f"tool.{tool_name}")
            mode = str(
                tool_result.get("mode")
                or ("deterministic_fallback" if fallback_benchmark else "deterministic_tool")
            )
            confidence_raw = tool_result.get("confidence")
            try:
                confidence = float(confidence_raw) if confidence_raw is not None else None
            except Exception:
                confidence = None

            if confidence is None:
                confidence = 0.35
                confidence += min(0.30, total_itens * 0.04)
                confidence += min(0.20, len(fontes) * 0.05 if isinstance(fontes, list) else 0.0)
                if fallback_benchmark:
                    confidence -= 0.12
                confidence = round(max(0.05, min(confidence, 0.98)), 2)

            citations = tool_result.get("citations")
            if not isinstance(citations, list):
                citations = []
            if not citations and isinstance(fontes, list):
                derived: List[Dict[str, Any]] = []
                for src in fontes[:8]:
                    if not isinstance(src, dict):
                        continue
                    derived.append(
                        {
                            "source": str(src.get("fonte") or "fonte_publica"),
                            "domain": str(src.get("dominio") or "n/a"),
                            "url": str(src.get("url") or "").strip(),
                            "competitor": str(src.get("concorrente") or "n/a"),
                        }
                    )
                citations = derived

            if total_itens <= 0:
                scope_parts: List[str] = []
                if escopo.get("estado"):
                    scope_parts.append(f"Estado {escopo.get('estado')}")
                if escopo.get("cidade"):
                    scope_parts.append(f"Cidade {escopo.get('cidade')}")
                if escopo.get("segmento"):
                    scope_parts.append(f"Segmento {escopo.get('segmento')}")
                if not scope_parts:
                    scope_parts.append("Mercado nacional")
                scope_txt = ", ".join(scope_parts)

                msg = (
                    "## Resumo executivo\n"
                    "- A busca de mercado foi concluída, porém sem preço público confiável para este item nesta rodada.\n"
                    f"- Escopo analisado: {scope_txt}.\n"
                    + (
                        "- Resultados públicos foram descartados por baixa aderência ao item solicitado.\n"
                        if low_relevance_detected
                        else ""
                    )
                    + "\n## Tabela operacional\n"
                    "| Indicador | Valor |\n"
                    "|---|---|\n"
                    "| Evidência pública válida | Não encontrada |\n"
                    f"| Escopo consultado | {scope_txt} |\n\n"
                    "## Próximas ações\n"
                    "- Solicite 2-3 cotações diretas para fechar a negociação imediata.\n"
                    "- Refaça a pesquisa com marca/modelo ou SKU.\n"
                    "- Informe especificação exata (medida, gramatura, cor e embalagem)."
                )
                return {
                    "type": "text",
                    "result": {"mensagem": msg},
                    "source": source,
                    "confidence": confidence,
                    "mode": mode if mode else "deterministic_no_evidence",
                    "citations": citations,
                }

            def _fmt_money(v: Any) -> str:
                try:
                    fv = float(v)
                    return f"{fv:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                except Exception:
                    return str(v or "-")

            def _fmt_competitor(value: Any) -> str:
                raw = str(value or "-").strip()
                if not raw:
                    return "-"
                mapping = {
                    "benchmark_mercado": "Referência de mercado",
                    "mercado livre": "Mercado Livre",
                    "tid's": "TID'S",
                }
                normalized = raw.lower()
                if normalized in mapping:
                    return mapping[normalized]
                return raw

            price_values: List[float] = []
            for item in itens:
                if not isinstance(item, dict):
                    continue
                try:
                    price_values.append(float(item.get("preco")))
                except Exception:
                    continue
            min_price = min(price_values) if price_values else None
            max_price = max(price_values) if price_values else None
            top = itens[:10]
            header = "| Concorrente | Produto | Preço (R$) | Evidência |\n|---|---|---|---|\n"
            rows = []
            for item in top:
                if not isinstance(item, dict):
                    continue
                url = str(item.get("url") or "").strip()
                rows.append(
                    "| "
                    + " | ".join(
                        [
                            _fmt_competitor(item.get("concorrente")),
                            str(item.get("produto") or "-"),
                            _fmt_money(item.get("preco")),
                            "Link público" if url else "Referência operacional",
                        ]
                    )
                    + " |"
                )
            table_md = header + ("\n".join(rows) if rows else "| - | - | - | - |")
            preco_medio = tool_result.get("preco_medio_referencia")
            preco_medio_txt = _fmt_money(preco_medio) if preco_medio is not None else "N/D"
            faixa_txt = "N/D"
            if min_price is not None and max_price is not None:
                faixa_txt = f"R$ {_fmt_money(min_price)} a R$ {_fmt_money(max_price)}"
            competitors_found: List[str] = []
            for item in itens:
                if not isinstance(item, dict):
                    continue
                comp = _fmt_competitor(item.get("concorrente"))
                if comp not in competitors_found:
                    competitors_found.append(comp)

            scope_parts: List[str] = []
            if escopo.get("estado"):
                scope_parts.append(f"Estado {escopo.get('estado')}")
            if escopo.get("cidade"):
                scope_parts.append(f"Cidade {escopo.get('cidade')}")
            if escopo.get("segmento"):
                scope_parts.append(f"Segmento {escopo.get('segmento')}")
            scope_parts.append(
                f"Cobertura {len(competitors_found)} concorrente(s) com preço identificado"
            )
            scope_txt = "; ".join(scope_parts)

            fontes_lines = []
            for f in fontes[:5]:
                if not isinstance(f, dict):
                    continue
                domain = str(f.get("dominio") or "fonte pública")
                url = str(f.get("url") or "").strip()
                comp = _fmt_competitor(f.get("concorrente") or "n/a")
                if url:
                    fontes_lines.append(f"- {comp} | {domain} | {url}")
                else:
                    fontes_lines.append(f"- {comp} | {domain}")
            fontes_txt = "\n".join(fontes_lines) if fontes_lines else "- Sem URL pública validada."
            low_evidence = fallback_benchmark or total_itens < 3
            action_txt = (
                "Use esta faixa como referência inicial de negociação e confirme com cotação direta antes de fechar o pedido."
                if low_evidence
                else "Use a faixa mínima e média para negociar e confirme prazo/frete para decisão final de compra."
            )
            refinement_section = ""
            if low_evidence:
                refinement_section = (
                    "\n\n## Como melhorar a próxima pesquisa\n"
                    "- Informe marca/modelo ou SKU do item.\n"
                    "- Inclua variação exata (tamanho, cor, unidade/embalagem).\n"
                    "- Defina concorrentes-alvo e cidade para refinar a evidência."
                )

            fallback_note = (
                "- Observação: sem evidência pública suficiente do concorrente-alvo nesta rodada; benchmark de mercado foi usado como referência complementar.\n"
                if fallback_benchmark
                else ""
            )
            msg = (
                "## Resumo executivo\n"
                f"- Pesquisa concorrencial concluída com {total_itens} referências.\n"
                f"- Escopo analisado: {scope_txt}.\n"
                f"- Faixa de preço encontrada: {faixa_txt}.\n"
                f"- Preço médio de referência: R$ {preco_medio_txt}.\n"
                + fallback_note
                + "\n## Tabela operacional\n"
                + table_md
                + "\n\n## Próximas ações\n"
                + f"- {action_txt}\n"
                + "\n## Fontes consultadas\n"
                + fontes_txt
                + refinement_section
            )
            return {
                "type": "text",
                "result": {"mensagem": msg},
                "source": source,
                "confidence": confidence,
                "mode": mode,
                "citations": citations,
            }

        if tool_name == "calcular_eoq":
            if tool_result.get("error"):
                return {
                    "type": "text",
                    "result": {"mensagem": f"Não consegui concluir o cálculo de EOQ: {tool_result.get('error')}"},
                }

            eoq = tool_result.get("eoq_ajustado") or tool_result.get("eoq")
            pedidos = tool_result.get("orders_per_year") or tool_result.get("pedidos_por_ano")
            custo_total = tool_result.get("custo_total_anual") or tool_result.get("total_cost")
            produto = tool_result.get("produto") or (tool_params or {}).get("produto_id")
            nome = tool_result.get("nome")

            def _fmt_money(v: Any) -> str:
                try:
                    return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                except Exception:
                    return str(v or "-")

            msg = (
                "## Resumo executivo\n"
                f"- EOQ calculado para produto {produto or '-'}"
                + (f" ({nome})" if nome else "")
                + ".\n"
                f"- Quantidade recomendada por pedido: {eoq or '-'} unidades.\n"
                f"- Pedidos estimados por ano: {pedidos or '-'}.\n"
                f"- Custo total anual estimado: R$ {_fmt_money(custo_total)}.\n\n"
                "## Próximas ações\n"
                "- Use este EOQ como baseline e ajuste por lead-time, orçamento e giro real da loja.\n"
                "- Rode sensibilidade de demanda (+/-20%) antes de fixar o lote operacional."
            )
            return {
                "type": "text",
                "result": {"mensagem": msg},
                "source": "tool.calcular_eoq",
                "confidence": 0.84,
                "mode": "deterministic_tool",
                "citations": [{"source": "admmat.parquet", "domain": "internal_data", "url": "", "competitor": "n/a"}],
            }

        if tool_name == "calcular_mc_produto":
            if tool_result.get("error"):
                return {
                    "type": "text",
                    "result": {"mensagem": f"Não consegui concluir o cálculo de MC: {tool_result.get('error')}"},
                }

            produto = tool_result.get("produto_id") or (tool_params or {}).get("produto_id")
            une = tool_result.get("une_id") or (tool_params or {}).get("une_id")
            nome = tool_result.get("nome")
            segmento = tool_result.get("segmento")
            mc_calculada = tool_result.get("mc_calculada")
            estoque_atual = tool_result.get("estoque_atual")
            linha_verde = tool_result.get("linha_verde")
            percentual_lv = tool_result.get("percentual_linha_verde")
            recomendacao = tool_result.get("recomendacao")

            def _fmt_calc(v: Any) -> str:
                try:
                    return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                except Exception:
                    return str(v or "-")

            table_data = [
                {"Indicador": "MC calculada", "Valor": _fmt_calc(mc_calculada)},
                {"Indicador": "Estoque atual", "Valor": _fmt_calc(estoque_atual)},
                {"Indicador": "Linha verde", "Valor": _fmt_calc(linha_verde)},
                {"Indicador": "% da linha verde", "Valor": f"{_fmt_calc(percentual_lv)}%"},
            ]
            msg = (
                "## Resumo executivo\n"
                f"- MC calculada para o produto {produto or '-'}"
                + (f" ({nome})" if nome else "")
                + f" na UNE {une or '-'}.\n"
                f"- Segmento: {segmento or '-'}.\n"
                f"- MC de referência: {_fmt_calc(mc_calculada)}; estoque atual: {_fmt_calc(estoque_atual)}; linha verde: {_fmt_calc(linha_verde)}.\n"
                f"- Leitura operacional: o item está em { _fmt_calc(percentual_lv) }% da linha verde. Recomendação: {recomendacao or '-'}.\n\n"
                "## Tabela operacional\n"
                + "| Indicador | Valor |\n|---|---|\n"
                + "\n".join(f"| {row['Indicador']} | {row['Valor']} |" for row in table_data)
                + "\n\n## Próximas ações\n"
                + "- Use a MC e o percentual da linha verde para calibrar abastecimento e exposição em gôndola.\n"
                "- Se quiser, eu também posso comparar esse item com outras UNEs."
            )
            return {
                "type": "text",
                "result": {"mensagem": msg},
                "source": "tool.calcular_mc_produto",
                "confidence": 0.86,
                "mode": "deterministic_tool",
                "citations": [{"source": "admmat.parquet", "domain": "internal_data", "url": "", "competitor": "n/a"}],
                "table_data": table_data,
            }

        if tool_name == "calcular_preco_final_une":
            if tool_result.get("error"):
                return {
                    "type": "text",
                    "result": {"mensagem": f"Não consegui concluir o cálculo de preço final: {tool_result.get('error')}"},
                }

            def _fmt_calc(v: Any) -> str:
                try:
                    return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                except Exception:
                    return str(v or "-")

            table_data = [
                {"Indicador": "Valor original (R$)", "Valor": _fmt_calc(tool_result.get("valor_original"))},
                {"Indicador": "Tipo de preço", "Valor": str(tool_result.get("tipo") or "-")},
                {"Indicador": "Desconto ranking", "Valor": str(tool_result.get("desconto_ranking") or "-")},
                {"Indicador": "Desconto pagamento", "Valor": str(tool_result.get("desconto_pagamento") or "-")},
                {"Indicador": "Preço final (R$)", "Valor": _fmt_calc(tool_result.get("preco_final"))},
                {"Indicador": "Economia (R$)", "Valor": _fmt_calc(tool_result.get("economia"))},
            ]
            msg = (
                "## Resumo executivo\n"
                f"- Cálculo de preço final concluído para compra de R$ {_fmt_calc(tool_result.get('valor_original'))}.\n"
                f"- Tipo de preço aplicado: {tool_result.get('tipo') or '-'}; ranking: {tool_result.get('ranking') or '-'}; forma de pagamento: {tool_result.get('forma_pagamento') or '-'}.\n"
                f"- Preço final calculado: R$ {_fmt_calc(tool_result.get('preco_final'))}, com economia estimada de R$ {_fmt_calc(tool_result.get('economia'))}.\n\n"
                "## Tabela operacional\n"
                + "| Indicador | Valor |\n|---|---|\n"
                + "\n".join(f"| {row['Indicador']} | {row['Valor']} |" for row in table_data)
                + "\n\n## Próximas ações\n"
                + "- Valide se a política de ranking aplicada está aderente à campanha e ao canal.\n"
                "- Se quiser, eu também posso simular outras formas de pagamento ou faixas de compra."
            )
            return {
                "type": "text",
                "result": {"mensagem": msg},
                "source": "tool.calcular_preco_final_une",
                "confidence": 0.84,
                "mode": "deterministic_tool",
                "citations": [{"source": "politica_une", "domain": "internal_rule", "url": "", "competitor": "n/a"}],
                "table_data": table_data,
            }

        if tool_name == "consultar_dados_flexivel":
            from backend.app.core.utils.query_router import (
                extract_product_code,
                extract_product_store_ranking_request,
            )

            resultados = tool_result.get("resultados", []) or []
            if not resultados:
                msg = tool_result.get("mensagem") or "Não encontrei dados para este recorte."
                return {"type": "text", "result": {"mensagem": msg}}

            def _fmt(v: Any) -> str:
                if v is None:
                    return "-"
                if isinstance(v, bool):
                    return "Sim" if v else "Não"
                if isinstance(v, (int, np.integer)):
                    return str(int(v))
                if isinstance(v, (float, np.floating)):
                    fv = float(v)
                    if abs(fv - round(fv)) < 1e-9:
                        return str(int(round(fv)))
                    return f"{fv:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                text = str(v).strip()
                return text or "-"

            def _clean_dimension_value(v: Any) -> str:
                text = str(v or "").strip()
                return text or "N/A"

            def _as_float(v: Any) -> float:
                try:
                    return float(v or 0)
                except (TypeError, ValueError):
                    return 0.0

            def _table(rows: List[Dict[str, Any]], cols: List[str], max_rows: int = 10) -> str:
                display_map = {
                    "UNE": "Loja (UNE)",
                    "valor": "Venda (R$)",
                    "TOTAL_VENDAS": "Venda (R$)",
                    "GAP_MEDIA": "Gap para média (R$)",
                    "VENDA_30DD": "Venda 30 dias (R$)",
                    "VENDA_30DD_TOTAL": "Venda 30 dias (R$)",
                    "ESTOQUE_UNE": "Estoque na loja",
                    "ESTOQUE_UNE_TOTAL": "Estoque na loja",
                    "ITENS": "Quantidade de itens",
                    "NOMESEGMENTO": "Segmento",
                    "NOMECATEGORIA": "Categoria",
                    "NOME": "Produto",
                    "PRODUTO": "Código do produto",
                }
                display_cols = [display_map.get(c, c.replace("_", " ").title()) for c in cols]
                header = "| " + " | ".join(display_cols) + " |"
                sep = "|" + "|".join(["---" for _ in cols]) + "|"
                body_lines = []
                for r in rows[:max_rows]:
                    body_lines.append("| " + " | ".join(_fmt(r.get(c)) for c in cols) + " |")
                table_md = "\n".join([header, sep] + body_lines)
                if len(rows) > max_rows:
                    table_md += f"\n... (+{len(rows) - max_rows} linhas)"
                return table_md

            def _table_payload(
                rows: List[Dict[str, Any]],
                cols: Optional[List[str]] = None,
                max_rows: int = 50,
            ) -> List[Dict[str, Any]]:
                payload_rows: List[Dict[str, Any]] = []
                for row in rows[:max_rows]:
                    if not isinstance(row, dict):
                        continue
                    if cols:
                        projected = {col: row.get(col) for col in cols}
                    else:
                        projected = dict(row)
                    payload_rows.append(projected)
                return payload_rows

            def _build_sales_dimension_report(
                *,
                rows: List[Dict[str, Any]],
                dim_col: str,
                dim_label: str,
                filters_text: str = "Sem filtros adicionais",
                max_rows: int = 15,
            ) -> str:
                sorted_rows = sorted(
                    [dict(row) for row in rows if isinstance(row, dict)],
                    key=lambda item: _as_float(item.get("TOTAL_VENDAS") or item.get("valor")),
                    reverse=True,
                )
                if not sorted_rows:
                    return (
                        "## Resumo executivo\n"
                        "- Não encontrei vendas suficientes para montar o relatório neste recorte.\n\n"
                        "## Tabela operacional\n"
                        "- Sem dados tabulares adicionais para exibir nesta resposta.\n\n"
                        "## Próximas ações\n"
                        "- Revise filtros de período, segmento e lojas antes de repetir a consulta."
                    )

                valores = [_as_float(row.get("TOTAL_VENDAS") or row.get("valor")) for row in sorted_rows]
                total_valor = sum(valores)
                media_valor = total_valor / len(sorted_rows) if sorted_rows else 0.0
                valores_ordenados = sorted(valores)
                meio = len(valores_ordenados) // 2
                if len(valores_ordenados) % 2 == 0:
                    mediana_valor = (valores_ordenados[meio - 1] + valores_ordenados[meio]) / 2 if valores_ordenados else 0.0
                else:
                    mediana_valor = valores_ordenados[meio] if valores_ordenados else 0.0

                top_5_share = (sum(valores[:5]) / total_valor * 100.0) if total_valor > 0 else 0.0
                bottom_5_share = (sum(valores[-5:]) / total_valor * 100.0) if total_valor > 0 else 0.0
                lider_row = sorted_rows[0]
                lider_nome = _clean_dimension_value(lider_row.get(dim_col))
                lider_valor = _as_float(lider_row.get("TOTAL_VENDAS") or lider_row.get("valor"))
                lider_share = (lider_valor / total_valor * 100.0) if total_valor > 0 else 0.0
                amplitude = lider_valor - (valores[-1] if valores else 0.0)

                if lider_share >= 25 or top_5_share >= 65:
                    concentracao = "alta"
                elif lider_share >= 15 or top_5_share >= 45:
                    concentracao = "moderada"
                else:
                    concentracao = "baixa"

                leitura = (
                    f"a distribuição está {concentracao}mente concentrada nas posições líderes"
                    if dim_col == "UNE"
                    else f"há concentração {concentracao} entre os principais {dim_label.lower()}"
                )

                enriched_rows: List[Dict[str, Any]] = []
                for idx, row in enumerate(sorted_rows, start=1):
                    valor = _as_float(row.get("TOTAL_VENDAS") or row.get("valor"))
                    share_pct = (valor / total_valor * 100.0) if total_valor > 0 else 0.0
                    gap_media = valor - media_valor
                    if valor >= media_valor * 1.2:
                        classificacao = "liderança" if idx <= 3 else "acima da média"
                    elif valor <= media_valor * 0.8:
                        classificacao = "cauda" if idx > max(5, len(sorted_rows) - 3) else "abaixo da média"
                    else:
                        classificacao = "na média"
                    enriched_rows.append(
                        {
                            dim_col: row.get(dim_col),
                            "TOTAL_VENDAS": valor,
                            "SHARE_PCT": f"{share_pct:.1f}%",
                            "RANK": idx,
                            "GAP_MEDIA": gap_media,
                            "CLASSIFICACAO": classificacao,
                        }
                    )

                display_map_extra = {
                    "SHARE_PCT": "Part. %",
                    "RANK": "Ranking",
                    "CLASSIFICACAO": "Classificação",
                }

                def _table_enriched(rows_to_show: List[Dict[str, Any]], cols: List[str], max_rows_inner: int = 10) -> str:
                    display_cols = []
                    for c in cols:
                        if c in display_map_extra:
                            display_cols.append(display_map_extra[c])
                        else:
                            display_cols.append({
                                "UNE": "Loja (UNE)",
                                "TOTAL_VENDAS": "Venda (R$)",
                                "GAP_MEDIA": "Gap p/ média (R$)",
                                "NOMESEGMENTO": "Segmento",
                                "NOMEGRUPO": "Grupo",
                            }.get(c, c.replace("_", " ").title()))
                    header = "| " + " | ".join(display_cols) + " |"
                    sep = "|" + "|".join(["---" for _ in cols]) + "|"
                    body = []
                    for row in rows_to_show[:max_rows_inner]:
                        rendered = []
                        for c in cols:
                            value = row.get(c)
                            if c in {"SHARE_PCT", "CLASSIFICACAO", "RANK"}:
                                rendered.append(str(value))
                            else:
                                rendered.append(_fmt(value))
                        body.append("| " + " | ".join(rendered) + " |")
                    table_md = "\n".join([header, sep] + body)
                    if len(rows_to_show) > max_rows_inner:
                        table_md += f"\n... (+{len(rows_to_show) - max_rows_inner} linhas)"
                    return table_md

                action_lines = (
                    "- Priorize as lojas abaixo da mediana com revisão de mix, preço e execução comercial em até 7 dias.\n"
                    "- Compare Top 5 e Bottom 5 para validar ruptura, exposição e profundidade de sortimento.\n"
                    "- Reavalie o segmento no próximo ciclo semanal para medir ganho de cobertura e venda."
                    if dim_col == "UNE"
                    else f"- Priorize os {dim_label.lower()} abaixo da mediana para revisão de sortimento, preço e execução comercial.\n"
                    f"- Compare os {dim_label.lower()} líderes com a cauda para identificar lacunas de mix e demanda.\n"
                    "- Reavalie o desempenho no próximo ciclo semanal com o mesmo recorte."
                )

                return (
                    "## Resumo executivo\n"
                    f"- Consolidado de vendas por {dim_label.lower()} concluído. Total vendido: {_fmt(total_valor)} em {len(sorted_rows)} {dim_label.lower()} analisados.\n"
                    f"- Destaque: {lider_nome} lidera com {_fmt(lider_valor)} e participação de {round(lider_share, 1):.1f}% no total.\n"
                    f"- KPIs-chave: média de {_fmt(media_valor)} por {dim_label.lower()}, mediana de {_fmt(mediana_valor)}, participação do Top 5 em {round(top_5_share, 1):.1f}% e da cauda em {round(bottom_5_share, 1):.1f}%.\n"
                    f"- Leitura gerencial: {leitura}; a amplitude entre líder e última posição é de {_fmt(amplitude)}. Filtros aplicados: {filters_text}.\n\n"
                    "## Tabela operacional\n"
                    + _table_enriched(
                        enriched_rows,
                        [dim_col, "TOTAL_VENDAS", "SHARE_PCT", "RANK", "GAP_MEDIA", "CLASSIFICACAO"],
                        max_rows_inner=max_rows,
                    )
                    + "\n\n## Próximas ações\n"
                    + action_lines
                )

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

                linhas_md = [
                    f"| {idx + 1} | {g} | {_fmt(v)} |"
                    for idx, (g, v) in enumerate(top_neg)
                ]
                msg = (
                    "## Resumo executivo\n"
                    f"- Identifiquei {len(negativos)} grupo(s) com venda negativa no recorte atual.\n"
                    "- Os 10 grupos mais críticos estão na tabela abaixo.\n\n"
                    "## Tabela operacional\n"
                    "| Ranking | Grupo | Venda (R$) |\n"
                    "|---|---|---|\n"
                    + "\n".join(linhas_md)
                    + "\n\n## Próximas ações\n"
                    "- Revisar preço, mix e ruptura dos grupos críticos.\n"
                    "- Validar devoluções e ajustes contábeis no período."
                )
                return {"type": "text", "result": {"mensagem": msg}}

            # Caso especial: resultado agregado com métrica "valor" por dimensão (segmento, UNE, categoria etc.).
            first_row = resultados[0] if resultados and isinstance(resultados[0], dict) else {}
            if isinstance(first_row, dict) and "valor" in first_row:
                dim_candidates = [
                    ("UNE", "Loja (UNE)"),
                    ("NOMESEGMENTO", "Segmento"),
                    ("NOMECATEGORIA", "Categoria"),
                    ("NOMEGRUPO", "Grupo"),
                    ("NOMEFABRICANTE", "Fabricante"),
                    ("NOME", "Produto"),
                ]
                dim_col = None
                dim_label = "Dimensão"
                for candidate, label in dim_candidates:
                    if candidate in first_row:
                        dim_col = candidate
                        dim_label = label
                        break

                if dim_col:
                    rows = []
                    total_valor = 0.0
                    for r in resultados:
                        if not isinstance(r, dict):
                            continue
                        try:
                            valor = float(r.get("valor", 0) or 0)
                        except (TypeError, ValueError):
                            valor = 0.0
                        total_valor += valor
                        rows.append({dim_col: _clean_dimension_value(r.get(dim_col)), "TOTAL_VENDAS": valor})
                    ranking_request = extract_product_store_ranking_request(user_query) if dim_col == "UNE" else None
                    reverse_sort = True
                    if isinstance(ranking_request, dict):
                        reverse_sort = bool(ranking_request.get("ordem_desc", True))
                    rows.sort(key=lambda x: float(x.get("TOTAL_VENDAS", 0) or 0), reverse=reverse_sort)
                    top_rows = rows[:10]
                    lider = top_rows[0].get(dim_col) if top_rows else "N/A"
                    if self._is_commercial_plan_query(query_lower):
                        plan_days = self._extract_plan_days(query_lower, default_days=7)
                        avg_venda = (total_valor / len(rows)) if rows else 0.0
                        high_performer_focus = any(
                            token in query_lower for token in ["maior", "maiores", "melhores", "top", "lideres", "líderes"]
                        )
                        candidate_rows = [
                            row for row in rows
                            if str(row.get(dim_col) or "").strip().upper() != "N/A"
                        ] or rows
                        low_rows = sorted(
                            candidate_rows,
                            key=lambda x: float(x.get("TOTAL_VENDAS", 0) or 0),
                            reverse=high_performer_focus,
                        )[:5]
                        prioritized_labels = [
                            str(r.get(dim_col))
                            for r in low_rows[:3]
                            if str(r.get(dim_col) or "").strip()
                            and str(r.get(dim_col)).strip().upper() != "N/A"
                        ]
                        plan_rows = []
                        for item in low_rows:
                            venda = float(item.get("TOTAL_VENDAS", 0) or 0)
                            plan_rows.append(
                                {
                                    dim_col: item.get(dim_col),
                                    "TOTAL_VENDAS": venda,
                                    "GAP_MEDIA": max(0.0, avg_venda - venda),
                                }
                            )
                        focus_label = dim_label.lower()
                        focus_descriptor = "maior desempenho" if high_performer_focus else "menor venda"
                        focuses = ", ".join(prioritized_labels) if prioritized_labels else f"{dim_label}s prioritários"
                        if dim_col == "UNE":
                            next_actions = (
                                "- Dia 1: validar estoque, exposição e preço nas UNEs prioritárias.\n"
                                "- Dia 2: ajustar ponto extra e comunicação de oferta local.\n"
                                "- Dia 3: ativar ação comercial de giro rápido com meta diária por UNE.\n"
                                "- Dia 4: reforçar reposição dos SKUs de maior conversão e retirar itens de baixo giro.\n"
                                "- Dia 5: revisar execução com equipe de loja e corrigir ruptura/excesso.\n"
                                "- Dia 6: replicar prática das UNEs líderes nas unidades abaixo da média.\n"
                                "- Dia 7: fechar resultado D+7 por UNE e recalibrar meta para o próximo ciclo."
                            )
                        else:
                            next_actions = (
                                f"- Dia 1: revisar mix, preço e ruptura dos {focus_label}s priorizados.\n"
                                f"- Dia 2: ajustar exposição e comunicação comercial dos {focus_label}s de baixa conversão.\n"
                                f"- Dia 3: ativar oferta tática e meta diária para recuperar giro.\n"
                                f"- Dia 4: reforçar disponibilidade dos itens líderes dentro de cada {focus_label}.\n"
                                f"- Dia 5: medir adesão e cortar itens com baixa resposta comercial.\n"
                                f"- Dia 6: replicar práticas dos {focus_label}s acima da média.\n"
                                f"- Dia 7: fechar resultado D+7 e recalibrar sortimento/preço."
                            )
                        msg = (
                            "## Resumo executivo\n"
                            f"- Plano comercial de {plan_days} dias estruturado para {focus_label} com foco em {focus_descriptor}.\n"
                            f"- Prioridades imediatas: {focuses}.\n"
                            f"- Referência de desempenho: média de {_fmt(avg_venda)} por {focus_label} no recorte atual.\n\n"
                            "## Tabela operacional\n"
                            + _table(plan_rows, [dim_col, "TOTAL_VENDAS", "GAP_MEDIA"], max_rows=5)
                            + "\n\n## Próximas ações\n"
                            + next_actions
                        )
                        return {
                            "type": "text",
                            "result": {"mensagem": msg},
                            "table_data": _table_payload(plan_rows, [dim_col, "TOTAL_VENDAS", "GAP_MEDIA"], max_rows=20),
                        }
                    if dim_col == "UNE" and isinstance(ranking_request, dict):
                        requested_limit = max(1, int(ranking_request.get("limite", 1) or 1))
                        ranking_rows = rows[:requested_limit]
                        product_code = extract_product_code(user_query)
                        singular = requested_limit == 1 and "lojas" not in query_lower
                        if ranking_request.get("ordem_desc", True):
                            if singular:
                                top_store = ranking_rows[0] if ranking_rows else {"UNE": "N/A", "TOTAL_VENDAS": 0.0}
                                msg = (
                                    "## Resumo executivo\n"
                                    f"- A loja que mais vende o produto {product_code or '-'} é a UNE {top_store.get('UNE', 'N/A')}.\n"
                                    f"- Venda 30 dias da loja líder: R$ {_fmt(top_store.get('TOTAL_VENDAS'))}.\n"
                                    f"- Cobertura analisada: {len(rows)} lojas com vendas do produto no recorte atual.\n\n"
                                    "## Tabela operacional\n"
                                    + _table(ranking_rows, [dim_col, "TOTAL_VENDAS"], max_rows=requested_limit)
                                    + "\n\n## Próximas ações\n"
                                    "- Replique preço, exposição e disponibilidade da UNE líder nas demais lojas com potencial.\n"
                                    "- Se quiser, eu comparo a UNE líder com as lojas abaixo da média desse produto."
                                )
                            else:
                                msg = (
                                    "## Resumo executivo\n"
                                    f"- Top {requested_limit} lojas por venda do produto {product_code or '-'} calculado com sucesso.\n"
                                    f"- UNE líder: {ranking_rows[0].get('UNE', 'N/A')} com R$ {_fmt(ranking_rows[0].get('TOTAL_VENDAS'))}.\n"
                                    f"- Cobertura analisada: {len(rows)} lojas com vendas do produto no recorte atual.\n\n"
                                    "## Tabela operacional\n"
                                    + _table(ranking_rows, [dim_col, "TOTAL_VENDAS"], max_rows=requested_limit)
                                    + "\n\n## Próximas ações\n"
                                    "- Replique preço, exposição e disponibilidade das lojas líderes nas demais UNEs com potencial.\n"
                                    "- Valide ruptura e cobertura das lojas fora do top ranking antes de redistribuir estoque."
                                )
                        else:
                            if singular:
                                bottom_store = ranking_rows[0] if ranking_rows else {"UNE": "N/A", "TOTAL_VENDAS": 0.0}
                                msg = (
                                    "## Resumo executivo\n"
                                    f"- A loja que menos vende o produto {product_code or '-'} é a UNE {bottom_store.get('UNE', 'N/A')}.\n"
                                    f"- Venda 30 dias da loja com menor giro: R$ {_fmt(bottom_store.get('TOTAL_VENDAS'))}.\n"
                                    f"- Cobertura analisada: {len(rows)} lojas com vendas do produto no recorte atual.\n\n"
                                    "## Tabela operacional\n"
                                    + _table(ranking_rows, [dim_col, "TOTAL_VENDAS"], max_rows=requested_limit)
                                    + "\n\n## Próximas ações\n"
                                    "- Revise preço, exposição, ruptura e sortimento da UNE com menor giro.\n"
                                    "- Se quiser, eu comparo a UNE de menor giro com a loja líder desse produto."
                                )
                            else:
                                msg = (
                                    "## Resumo executivo\n"
                                    f"- Top {requested_limit} lojas de menor venda do produto {product_code or '-'} calculado com sucesso.\n"
                                    f"- UNE com menor giro: {ranking_rows[0].get('UNE', 'N/A')} com R$ {_fmt(ranking_rows[0].get('TOTAL_VENDAS'))}.\n"
                                    f"- Cobertura analisada: {len(rows)} lojas com vendas do produto no recorte atual.\n\n"
                                    "## Tabela operacional\n"
                                    + _table(ranking_rows, [dim_col, "TOTAL_VENDAS"], max_rows=requested_limit)
                                    + "\n\n## Próximas ações\n"
                                    "- Atue primeiro nas UNEs de menor giro com revisão de preço, exposição e abastecimento.\n"
                                    "- Compare o bottom ranking com as lojas líderes para identificar lacunas operacionais."
                                )
                        return {
                            "type": "text",
                            "result": {"mensagem": msg},
                            "table_data": _table_payload(ranking_rows, [dim_col, "TOTAL_VENDAS"], max_rows=max(requested_limit, 1)),
                        }
                    filtros_txt = "Sem filtros adicionais"
                    if isinstance(tool_params, dict):
                        filtros = tool_params.get("filtros")
                        if isinstance(filtros, dict) and filtros:
                            filtros_txt = "; ".join(
                                f"{str(k).replace('_', ' ').title()}: {v}"
                                for k, v in filtros.items()
                                if v not in (None, "", [])
                            ) or filtros_txt
                    msg = _build_sales_dimension_report(
                        rows=rows,
                        dim_col=dim_col,
                        dim_label=dim_label,
                        filters_text=filtros_txt,
                        max_rows=10,
                    )
                    return {
                        "type": "text",
                        "result": {"mensagem": msg},
                        "table_data": _table_payload(rows, [dim_col, "TOTAL_VENDAS"], max_rows=50),
                    }

            # Caso especial: resultado agregado por UNE (colunas UNE + valor).
            if all(isinstance(r, dict) and "UNE" in r and "valor" in r for r in resultados[:1]):
                rows = []
                total = 0.0
                for r in resultados:
                    try:
                        v = float(r.get("valor", 0) or 0)
                    except (TypeError, ValueError):
                        v = 0.0
                    total += v
                    rows.append({"UNE": r.get("UNE"), "TOTAL_VENDAS": v})
                rows.sort(key=lambda x: float(x.get("TOTAL_VENDAS", 0) or 0), reverse=True)

                filtros = (tool_params or {}).get("filtros", {}) if isinstance(tool_params, dict) else {}
                key_alias = {
                    "UNE": "Loja (UNE)",
                    "NOMESEGMENTO": "Segmento",
                    "NOMEGRUPO": "Grupo",
                }
                filtros_txt = "Sem filtros adicionais"
                if isinstance(filtros, dict) and filtros:
                    parts = []
                    for k, v in filtros.items():
                        k_str = str(k or "").strip()
                        if not k_str:
                            k_str = "Filtro"
                        label = key_alias.get(k_str, k_str)
                        parts.append(f"{label}: {v}")
                    if parts:
                        filtros_txt = "; ".join(parts)
                msg = _build_sales_dimension_report(
                    rows=rows,
                    dim_col="UNE",
                    dim_label="UNE",
                    filters_text=filtros_txt,
                    max_rows=50,
                )
                return {
                    "type": "text",
                    "result": {"mensagem": msg},
                    "table_data": _table_payload(rows, ["UNE", "VENDA_30DD_TOTAL", "ESTOQUE_UNE_TOTAL", "ITENS"], max_rows=50),
                }

            # Resposta executiva para perguntas de vendas em todas as lojas/UNEs.
            if (
                (
                    (
                        any(k in query_lower for k in ["venda", "vendas"])
                        and any(k in query_lower for k in ["todas as lojas", "todas as unes", "todas as unes", "todas lojas"])
                    )
                    or self._is_commercial_plan_query(query_lower)
                )
                and all("UNE" in r for r in resultados[:1])
                and all("VENDA_30DD" in r for r in resultados[:1])
            ):
                agg: Dict[str, Dict[str, float]] = {}
                for r in resultados:
                    une = str(r.get("UNE", "N/A"))
                    venda = r.get("VENDA_30DD", 0) or 0
                    estoque = r.get("ESTOQUE_UNE", 0) or 0
                    try:
                        venda_f = float(venda)
                    except (TypeError, ValueError):
                        venda_f = 0.0
                    try:
                        estoque_f = float(estoque)
                    except (TypeError, ValueError):
                        estoque_f = 0.0
                    if une not in agg:
                        agg[une] = {"venda": 0.0, "estoque": 0.0, "linhas": 0.0}
                    agg[une]["venda"] += venda_f
                    agg[une]["estoque"] += estoque_f
                    agg[une]["linhas"] += 1.0

                rows = [
                    {
                        "UNE": une,
                        "VENDA_30DD_TOTAL": vals["venda"],
                        "ESTOQUE_UNE_TOTAL": vals["estoque"],
                        "ITENS": int(vals["linhas"]),
                    }
                    for une, vals in agg.items()
                ]
                rows.sort(key=lambda x: float(x.get("VENDA_30DD_TOTAL", 0) or 0), reverse=True)

                total_venda = sum(float(r.get("VENDA_30DD_TOTAL", 0) or 0) for r in rows)
                total_estoque = sum(float(r.get("ESTOQUE_UNE_TOTAL", 0) or 0) for r in rows)
                top_une = rows[0]["UNE"] if rows else "N/A"
                filtros = (tool_params or {}).get("filtros", {}) if isinstance(tool_params, dict) else {}

                if self._is_commercial_plan_query(query_lower):
                    plan_days = self._extract_plan_days(query_lower, default_days=7)
                    avg_venda = (total_venda / len(rows)) if rows else 0.0
                    low_rows = sorted(rows, key=lambda x: float(x.get("VENDA_30DD_TOTAL", 0) or 0))[:5]
                    focused_unes = [str(r.get("UNE")) for r in low_rows[:3] if r.get("UNE") is not None]
                    plan_rows = []
                    for item in low_rows:
                        venda = float(item.get("VENDA_30DD_TOTAL", 0) or 0)
                        plan_rows.append(
                            {
                                "UNE": item.get("UNE"),
                                "TOTAL_VENDAS": venda,
                                "GAP_MEDIA": max(0.0, avg_venda - venda),
                            }
                        )
                    msg = (
                        "## Resumo executivo\n"
                        f"- Plano comercial de {plan_days} dias estruturado para as UNEs de menor venda.\n"
                        f"- UNEs prioritárias: {', '.join(focused_unes) if focused_unes else 'definir após validação operacional'}.\n"
                        f"- Referência: média de {_fmt(avg_venda)} por UNE no recorte atual.\n\n"
                        "## Tabela operacional\n"
                        + _table(plan_rows, ["UNE", "TOTAL_VENDAS", "GAP_MEDIA"], max_rows=5)
                        + "\n\n## Próximas ações\n"
                        "- Dia 1: validar ruptura, preço e exposição nas UNEs abaixo da média.\n"
                        "- Dia 2: ajustar sortimento e ativar comunicação comercial local.\n"
                        "- Dia 3: definir meta diária de recuperação por UNE.\n"
                        "- Dia 4: reforçar reposição dos itens com maior conversão.\n"
                        "- Dia 5: revisar execução e corrigir desvios de abastecimento.\n"
                        "- Dia 6: replicar práticas das UNEs líderes.\n"
                        "- Dia 7: medir ganho, fechar D+7 e recalibrar meta."
                    )
                    return {
                        "type": "text",
                        "result": {"mensagem": msg},
                        "table_data": _table_payload(plan_rows, ["UNE", "TOTAL_VENDAS", "GAP_MEDIA"], max_rows=20),
                    }

                segment_hint = ""
                if "segmento" in query_lower and not any(
                    k.upper() in {"NOMESEGMENTO", "SEGMENTO", "NOME_SEGMENTO"} for k in filtros.keys()
                ):
                    segment_hint = (
                        "\nObservação: não encontrei filtro explícito de segmento aplicado nesta execução. "
                        "Posso refazer com filtro de segmento para precisão."
                    )

                msg = (
                    "## Resumo executivo\n"
                    f"Consolidei vendas e estoque por UNE no recorte consultado. "
                    f"UNE líder: {top_une}. Venda total: {_fmt(total_venda)}. Estoque total: {_fmt(total_estoque)}."
                    "\n\n## Tabela operacional\n"
                    + _table(rows, ["UNE", "VENDA_30DD_TOTAL", "ESTOQUE_UNE_TOTAL", "ITENS"], max_rows=12)
                    + "\n\n## Próximas ações\n"
                    "Priorizar as UNEs com menor venda total e estoque elevado para plano comercial/abastecimento dirigido."
                    + segment_hint
                )
                return {
                    "type": "text",
                    "result": {"mensagem": msg},
                    "table_data": _table_payload(rows, ["UNE", "VENDA_30DD_TOTAL", "ESTOQUE_UNE_TOTAL", "ITENS"], max_rows=50),
                }

            # Default determinístico para consulta flexível.
            first = resultados[0] if resultados else {}
            cols = list(first.keys())[:6] if isinstance(first, dict) else []
            msg = (
                "## Resumo executivo\n"
                f"Consulta executada com sucesso. Registros retornados: {len(resultados)}."
                "\n\n## Tabela operacional\n"
                + (_table(resultados, cols, max_rows=8) if cols else "Sem colunas para exibir.")
                + "\n\n## Próximas ações\n"
                "- Informe período, UNE ou segmento alvo para eu retornar ranking Top 10 e comparação com período anterior."
            )
            return {
                "type": "text",
                "result": {"mensagem": msg},
                "table_data": _table_payload(resultados, cols if cols else None, max_rows=50),
            }

        return {
            "type": "text",
            "result": {"mensagem": "Consulta executada com sucesso."},
        }

    def _build_clarification_if_needed(
        self,
        user_query: str,
        tool_name: str,
        confidence: float,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Detecta consultas comerciais vagas e retorna pergunta de desambiguação.
        """
        q = (user_query or "").lower().strip()
        chart_related_tools = {
            "consultar_dados_flexivel",
            "gerar_grafico_universal_v2",
            "gerar_dashboard_executivo",
        }
        market_related_tools = {
            "pesquisar_precos_concorrentes",
            "pesquisar_mercado_web",
        }

        if self._is_underspecified_business_followup(q):
            return {
                "type": "text",
                "result": {
                    "mensagem": (
                        "Para responder com precisão, confirme o contexto principal da continuação.\n"
                        "Exemplos: 'qual loja vende menos o produto 369947' ou "
                        "'quais lojas estão com rupturas do produto 369947'."
                    )
                },
            }

        if self._is_context_dependent_business_followup(q, chat_history):
            expanded_query = self._expand_business_followup_with_context(q, chat_history)
            if expanded_query == q:
                return {
                    "type": "text",
                    "result": {
                        "mensagem": (
                            "Para responder essa continuação com precisão, confirme o contexto principal.\n"
                            "Exemplos: 'qual loja vende menos o produto 369947' ou "
                            "'quais lojas estão com rupturas do produto 369947'."
                        )
                    },
                }

        # Refinamento por período sem período explícito: pedir confirmação antes de executar.
        wants_period_refine = any(k in q for k in ["refine por periodo", "refinar por periodo", "por período", "por periodo"])
        has_period_value = bool(__import__("re").search(r"\b(\d+)\s*(dias?|mes(es)?|semanas?|anos?)\b", q) or any(
            k in q for k in ["hoje", "ontem", "semana", "mensal", "mês", "mes", "trimestre", "ano", "últimos", "ultimos"]
        ))
        if wants_period_refine and not has_period_value:
            return {
                "type": "text",
                "result": {
                    "mensagem": (
                        "Para refinar por período, confirme o intervalo desejado.\n"
                        "Exemplos: últimos 30 dias, últimos 90 dias, mês atual, trimestre atual."
                    )
                },
            }

        wants_chart_or_dashboard = self._is_chart_request(q) or self._is_dashboard_request(q)
        if wants_chart_or_dashboard and tool_name in chart_related_tools:
            if self._is_dashboard_request(q):
                return None
            has_breakdown = bool(self._infer_chart_breakdown(q))
            has_metric = self._has_business_metric_hint(q)
            if not has_breakdown or not has_metric:
                missing_parts = []
                if not has_metric:
                    missing_parts.append("a métrica principal (ex.: vendas, estoque, margem)")
                if not has_breakdown:
                    missing_parts.append("o recorte do gráfico (ex.: por UNE, segmento, grupo ou produto)")
                msg = (
                    "Para montar a visualização correta, confirme "
                    + " e ".join(missing_parts)
                    + ".\n"
                    + "Exemplo: 'gere um gráfico de vendas por segmento nos últimos 30 dias'."
                )
                return {"type": "text", "result": {"mensagem": msg}}

        if self._is_competitive_query(q) and tool_name in market_related_tools and not self._has_market_subject_hint(q):
            msg = (
                "Para fazer a pesquisa de mercado corretamente, informe o produto ou SKU que você quer pesquisar.\n"
                "Você também pode complementar com cidade, estado ou concorrente-alvo."
            )
            return {"type": "text", "result": {"mensagem": msg}}

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
        resolved_query = self._resolve_query_with_history_context(user_query, chat_history)
        if resolved_query != user_query:
            logger.info(f"[CONTEXT] Query enriquecida para roteamento: {resolved_query}")
        if self._is_small_talk_query(resolved_query):
            logger.info("[SMALLTALK] Resposta direta sem uso de ferramentas.")
            return self._small_talk_response(resolved_query)

        contextual_followup_response = self._build_contextual_followup_response(
            resolved_query,
            chat_history,
        )
        if contextual_followup_response is not None:
            logger.info("[CONTEXT] Follow-up contextual resolvido sem nova rodada analítica.")
            return contextual_followup_response

        # ========================================================================
        # CAMADA 1: INTENT CLASSIFICATION (NEW 2026-01-24)
        # ========================================================================
        from backend.app.core.utils.intent_classifier import classify_intent
        from backend.app.core.utils.query_router import route_query
        
        intent_result = classify_intent(resolved_query)
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
            query=resolved_query,
            confidence=intent_result.confidence
        )
        logger.info(
            f"[ROUTER] Selected tool: {tool_selection.tool_name} "
            f"(confidence: {tool_selection.confidence:.2f})"
        )
        logger.info(f"[ROUTER] Extracted params: {tool_selection.tool_params}")
        logger.info(f"[ROUTER] Reasoning: {tool_selection.reasoning}")

        # Ajustes comerciais de alto valor (gráfico explícito, toda rede, segmento).
        self._enrich_tool_selection_for_business(resolved_query, tool_selection, chat_history=chat_history)
        # Garante compatibilidade com escopo de tools por role e dependências carregadas.
        self._ensure_tool_selection_available(resolved_query, tool_selection)
        logger.info(
            f"[ROUTER] Adjusted tool: {tool_selection.tool_name} "
            f"(confidence: {tool_selection.confidence:.2f}, params: {tool_selection.tool_params})"
        )

        clarification = self._build_clarification_if_needed(
            resolved_query,
            tool_selection.tool_name,
            tool_selection.confidence,
            chat_history=chat_history,
        )
        if clarification is not None:
            logger.info("[CLARIFICATION] Consulta vaga detectada. Retornando pergunta guiada.")
            return clarification

        llm_task_type = self._resolve_llm_task_type(
            intent_result.intent,
            tool_selection.tool_name,
            resolved_query,
        )

        # ========================================================================
        # CAMADA 2.3: SANDBOX DE CÁLCULO (FIRST-CLASS)
        # Consulta matemática complexa/sensibilidade pode ser resolvida sem rodada LLM.
        # ========================================================================
        if self._should_use_calculation_sandbox(intent_result.intent, tool_selection.tool_name, resolved_query):
            try:
                await self._emit_progress(on_progress, "calculation_sandbox", "executing")
                sandbox_result = await asyncio.to_thread(
                    self._execute_calculation_sandbox,
                    resolved_query,
                    tool_selection,
                )
                if sandbox_result:
                    logger.info("[SANDBOX] Resposta de cálculo retornada com sucesso.")
                    return sandbox_result
            except Exception as sandbox_error:
                logger.warning(f"[SANDBOX] Falha no cálculo sandbox: {sandbox_error}. Seguindo fluxo padrão.")

        # ========================================================================
        # CAMADA 2.4: GOVERNED TOOL EXECUTION (PRODUÇÃO)
        # Seleção controlada de ferramenta para reduzir variação e erro.
        # ========================================================================
        if self._requires_governed_path(intent_result.intent, tool_selection.tool_name, tool_selection.confidence, resolved_query):
            tool_to_run = self._find_tool_by_name(tool_selection.tool_name)
            if tool_to_run is not None:
                try:
                    await self._emit_progress(on_progress, tool_selection.tool_name, "executing")

                    primary_error: Optional[Exception] = None
                    try:
                        tool_result = await asyncio.to_thread(
                            self._execute_tool_with_recovery,
                            tool_to_run,
                            tool_selection.tool_name,
                            tool_selection.tool_params,
                        )
                    except Exception as error:
                        primary_error = error
                        logger.warning(
                            f"[TOOL-RECOVERY] Ferramenta primária {tool_selection.tool_name} falhou "
                            f"com exceção: {error}"
                        )
                        tool_result = {"status": "error", "error": str(error)}

                    active_tool_name = tool_selection.tool_name
                    active_tool_params = tool_selection.tool_params
                    active_tool_result = tool_result

                    if self._should_attempt_semantic_recovery(
                        user_query=resolved_query,
                        tool_name=tool_selection.tool_name,
                        tool_result=tool_result,
                        tool_error=primary_error,
                    ):
                        recovered = await self._execute_semantic_tool_fallback(
                            user_query=resolved_query,
                            primary_tool_name=tool_selection.tool_name,
                            primary_tool_params=tool_selection.tool_params,
                            fallback_tools=getattr(tool_selection, "fallback_tools", []),
                            on_progress=on_progress,
                        )
                        if recovered:
                            active_tool_name = str(recovered["tool_name"])
                            active_tool_params = dict(recovered["tool_params"])
                            active_tool_result = recovered["tool_result"]
                        elif primary_error is not None:
                            raise primary_error
                        else:
                            logger.warning(
                                f"[TOOL-RECOVERY] Sem fallback semântico válido para {tool_selection.tool_name}."
                            )

                    if active_tool_name == "gerar_grafico_universal_v2":
                        return self._format_tool_result_for_path(
                            resolved_query,
                            active_tool_name,
                            active_tool_result,
                            active_tool_params,
                        )

                    if active_tool_name == "gerar_dashboard_executivo":
                        dashboard_response = self._format_governed_dashboard_result(
                            resolved_query,
                            active_tool_result,
                            active_tool_params,
                        )
                        if dashboard_response.get("type") != "dashboard":
                            fallback_chart_tool = self._find_tool_by_name("gerar_grafico_universal_v2")
                            if fallback_chart_tool is not None:
                                fallback_segment = self._extract_segment_from_query(resolved_query)
                                fallback_une = self._extract_une_from_query(resolved_query)
                                fallback_breakdown = self._infer_chart_breakdown(resolved_query)
                                fallback_chart_params = {
                                    "descricao": resolved_query,
                                    "tipo_grafico": "bar",
                                    "limite": 20,
                                }
                                if fallback_segment:
                                    fallback_chart_params["filtro_segmento"] = fallback_segment
                                if fallback_une:
                                    fallback_chart_params["filtro_une"] = fallback_une
                                if fallback_breakdown:
                                    fallback_chart_params["quebra_por"] = fallback_breakdown
                                fallback_result = await asyncio.to_thread(
                                    self._execute_tool_with_recovery,
                                    fallback_chart_tool,
                                    "gerar_grafico_universal_v2",
                                    fallback_chart_params,
                                )
                                return self._format_tool_result_for_path(
                                    resolved_query,
                                    "gerar_grafico_universal_v2",
                                    fallback_result,
                                    fallback_chart_params,
                                )
                        return dashboard_response

                    return self._format_tool_result_for_path(
                        resolved_query,
                        active_tool_name,
                        active_tool_result,
                        active_tool_params,
                    )
                except Exception as e:
                    logger.warning(f"[GOVERNED] Falha na execução governada ({tool_selection.tool_name}): {e}. Fallback para fluxo LLM.")

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
                await self._emit_progress(on_progress, tool_selection.tool_name, "executing")

            tool_to_run = self._find_tool_by_name(tool_selection.tool_name)
            if tool_to_run is not None:
                try:
                    tool_result = await asyncio.to_thread(
                        self._execute_tool_with_recovery,
                        tool_to_run,
                        tool_selection.tool_name,
                        tool_selection.tool_params,
                    )

                    if self._is_tool_failure_result(tool_result):
                        recovered = await self._execute_semantic_tool_fallback(
                            user_query=resolved_query,
                            primary_tool_name=tool_selection.tool_name,
                            primary_tool_params=tool_selection.tool_params,
                            fallback_tools=getattr(tool_selection, "fallback_tools", []),
                            on_progress=on_progress,
                        )
                        if recovered:
                            return self._format_tool_result_for_path(
                                resolved_query,
                                str(recovered["tool_name"]),
                                recovered["tool_result"],
                                dict(recovered["tool_params"]),
                            )

                    return self._format_tool_result_for_path(
                        resolved_query,
                        tool_selection.tool_name,
                        tool_result,
                        tool_selection.tool_params,
                    )
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
        rag_context_str = ""
        if self._should_use_reference_examples(resolved_query, tool_selection=tool_selection, chat_history=chat_history):
            try:
                # [OK] FIX: Timeout de 500ms para não bloquear (continua sem RAG se demorar)
                rag_context_str = await asyncio.wait_for(
                    self._get_rag_examples(resolved_query, top_k=1),  # [OK] Reduzido de 2 para 1 exemplo
                    timeout=0.5  # 500ms timeout
                )
            except asyncio.TimeoutError:
                logger.warning("[RAG] Timeout de 500ms excedido. Continuando sem RAG.")
                rag_context_str = ""
            except Exception as e:
                logger.error(f"[RAG] Erro ao recuperar contexto: {e}")
                rag_context_str = ""
        else:
            logger.info("[RAG] Referência histórica pulada para evitar viés em contexto forte da sessão.")
        
        # Combinar query do usuário com o contexto RAG (se houver)
        # BEST PRACTICE: Contexto ANTES da Query (Recency Bias)
        if rag_context_str:
            full_prompt_content = rag_context_str + "\n\n" + "PERGUNTA DO USUÁRIO AGORA:\n" + resolved_query
            logger.info("[RAG] Contexto PREPENDED na mensagem do usuário (Context Fencing)")
        else:
            full_prompt_content = resolved_query

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
            # Mantemos a dica de roteamento perto da mensagem do usuário para adapters OpenAI-like.
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
        # Agentic tool loop with Groq + local tool orchestration.
        # ========================================================================
        # We trust the model's internal reasoning (ReAct) to decide between tools and text.
        # No more keyword-based forcing or prefilling.
        
        # Determine tools to use (all tools available by default)
        tools_to_use = self.tool_declarations
        
        max_turns = 15
        current_turn = 0
        successful_tool_calls = 0  # Track tool usage for final reporting

        while current_turn < max_turns:
            try:
                # Notify thinking
                await self._emit_progress(on_progress, "Pensando", "start")

                # Call LLM with tools (Blocking call wrapped in thread)
                # Adapter call is synchronous and runs in a worker thread.
                response = await asyncio.to_thread(
                    self._llm_get_completion,
                    messages,
                    tools_to_use,
                    llm_task_type,
                )

                if "error" in response:
                    logger.error(f"LLM Error: {response['error']}")
                    return self._generate_error_response(response['error'])

                # [OK] FIX: LOGGING (mesmo do run())
                response_type = "tool_call" if "tool_calls" in response else "text"
                logger.info(f"[ASYNC] LLM Response Type: {response_type}")

                # MODERN CHECK: Trust the LLM. If it returns text, it's text.
                # No more forcing graph generation based on keywords.
                if response_type == "text" and successful_tool_calls == 0:
                     content_preview = str(response.get("content", "") or "")
                     if self._should_attempt_routed_tool_rescue(
                         resolved_query,
                         content_preview,
                         tool_selection,
                         successful_tool_calls,
                     ):
                         logger.warning(
                             "[ASYNC] LLM retornou texto sem tool call para query analítica. "
                             f"Executando resgate pela tool roteada: {tool_selection.tool_name}"
                         )
                         rescued_response = await self._attempt_routed_tool_rescue(
                             resolved_query,
                             tool_selection,
                             on_progress=on_progress,
                         )
                         if rescued_response is not None:
                             return rescued_response

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
                        await self._emit_progress(on_progress, func_name, "executing")

                        tool_to_run = self._find_tool_by_name(func_name)
                        
                        if tool_to_run:
                            try:
                                # Execute tool (Blocking call wrapped in thread)
                                tool_output = await asyncio.to_thread(
                                    self._execute_tool_with_recovery,
                                    tool_to_run,
                                    func_name,
                                    func_args,
                                )

                                if self._is_tool_failure_result(tool_output):
                                    recovered = await self._execute_semantic_tool_fallback(
                                        user_query=resolved_query,
                                        primary_tool_name=func_name,
                                        primary_tool_params=func_args,
                                        fallback_tools=[],
                                        on_progress=on_progress,
                                    )
                                    if recovered:
                                        tool_output = recovered["tool_result"]
                                        if isinstance(tool_output, dict):
                                            tool_output.setdefault("_recovery", {})
                                            tool_output["_recovery"]["fallback_tool"] = recovered["tool_name"]
                                            tool_output["_recovery"]["mode"] = "semantic_fallback"
                                
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
                            is_success = self._is_tool_success_result(tool_result)
                            
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
                await self._emit_progress(on_progress, "Processando resposta", "finishing")

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
                    content = self._generate_structured_visual_narrative(
                        user_query=resolved_query,
                        task_type=llm_task_type or "visualization",
                        fallback_text=self._clean_context7_violations(content, context_type="chart"),
                        chart_data=found_chart_data,
                        chart_summary=found_chart_summary,
                    )

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
                    content = self._generate_structured_visual_narrative(
                        user_query=resolved_query,
                        task_type=llm_task_type or "analysis",
                        fallback_text=self._clean_context7_violations(content, context_type="data"),
                        table_rows=found_resultados,
                    )
                    
                    return {
                        "type": "code_result",
                        "result": found_resultados, # Lista de dicts para o frontend renderizar Tabela
                        "table_data": found_resultados,
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
        if self._is_small_talk_query(user_query):
            logger.info("[SMALLTALK] Resposta direta sem uso de ferramentas (sync).")
            return self._small_talk_response(user_query)

        resolved_query = self._resolve_query_with_history_context(user_query, chat_history)
        contextual_followup_response = self._build_contextual_followup_response(
            resolved_query,
            chat_history,
        )
        if contextual_followup_response is not None:
            logger.info("[CONTEXT][SYNC] Follow-up contextual resolvido sem nova rodada analítica.")
            return contextual_followup_response
        try:
            from backend.app.core.utils.intent_classifier import classify_intent
            from backend.app.core.utils.query_router import route_query

            sync_intent = classify_intent(resolved_query)
            tool_selection = route_query(
                intent=sync_intent.intent,
                query=resolved_query,
                confidence=sync_intent.confidence,
            )
        except Exception:
            sync_intent = None
            tool_selection = None

        if tool_selection is not None:
            self._enrich_tool_selection_for_business(
                resolved_query,
                tool_selection,
                chat_history=chat_history,
            )
            self._ensure_tool_selection_available(resolved_query, tool_selection)
            clarification = self._build_clarification_if_needed(
                resolved_query,
                tool_selection.tool_name,
                tool_selection.confidence,
                chat_history=chat_history,
            )
            if clarification is not None:
                logger.info("[CLARIFICATION][SYNC] Consulta vaga detectada. Retornando pergunta guiada.")
                return clarification

        llm_task_type = self._resolve_llm_task_type(
            getattr(sync_intent, "intent", None),
            getattr(tool_selection, "tool_name", ""),
            resolved_query,
        )

        if tool_selection is not None and self._should_use_calculation_sandbox(
            getattr(sync_intent, "intent", None),
            tool_selection.tool_name,
            resolved_query,
        ):
            try:
                sandbox_result = self._execute_calculation_sandbox(
                    resolved_query,
                    tool_selection,
                )
                if sandbox_result:
                    logger.info("[SANDBOX][SYNC] Resposta de cálculo retornada com sucesso.")
                    return sandbox_result
            except Exception as sandbox_error:
                logger.warning(
                    f"[SANDBOX][SYNC] Falha no cálculo sandbox: {sandbox_error}. Seguindo fluxo padrão."
                )

        if tool_selection is not None and self._requires_governed_path(
            getattr(sync_intent, "intent", None),
            tool_selection.tool_name,
            tool_selection.confidence,
            resolved_query,
        ):
            tool_to_run = self._find_tool_by_name(tool_selection.tool_name)
            if tool_to_run is not None:
                try:
                    primary_error: Optional[Exception] = None
                    try:
                        tool_result = self._execute_tool_with_recovery(
                            tool_to_run,
                            tool_selection.tool_name,
                            tool_selection.tool_params,
                        )
                    except Exception as error:
                        primary_error = error
                        logger.warning(
                            f"[TOOL-RECOVERY][SYNC] Ferramenta primária {tool_selection.tool_name} falhou "
                            f"com exceção: {error}"
                        )
                        tool_result = {"status": "error", "error": str(error)}

                    active_tool_name = tool_selection.tool_name
                    active_tool_params = dict(tool_selection.tool_params or {})
                    active_tool_result = tool_result

                    if self._should_attempt_semantic_recovery(
                        user_query=resolved_query,
                        tool_name=tool_selection.tool_name,
                        tool_result=tool_result,
                        tool_error=primary_error,
                    ):
                        recovered = self._execute_semantic_tool_fallback_sync(
                            user_query=resolved_query,
                            primary_tool_name=tool_selection.tool_name,
                            primary_tool_params=tool_selection.tool_params,
                            fallback_tools=getattr(tool_selection, "fallback_tools", []),
                        )
                        if recovered:
                            active_tool_name = str(recovered["tool_name"])
                            active_tool_params = dict(recovered["tool_params"])
                            active_tool_result = recovered["tool_result"]
                        elif primary_error is not None:
                            raise primary_error
                        else:
                            logger.warning(
                                f"[GOVERNED][SYNC] Sem fallback semântico válido para {tool_selection.tool_name}."
                            )

                    if active_tool_name == "gerar_dashboard_executivo":
                        dashboard_response = self._format_governed_dashboard_result(
                            resolved_query,
                            active_tool_result,
                            active_tool_params,
                        )
                        if dashboard_response.get("type") == "dashboard":
                            return dashboard_response

                    return self._format_tool_result_for_path(
                        resolved_query,
                        active_tool_name,
                        active_tool_result,
                        active_tool_params,
                    )
                except Exception as error:
                    logger.warning(
                        f"[GOVERNED][SYNC] Falha na execução governada ({tool_selection.tool_name}): {error}. "
                        "Fallback para fluxo LLM."
                    )

        if tool_selection is not None and self._should_use_deterministic_path(
            tool_selection.tool_name,
            tool_selection.confidence,
        ):
            tool_to_run = self._find_tool_by_name(tool_selection.tool_name)
            if tool_to_run is not None:
                try:
                    primary_error: Optional[Exception] = None
                    try:
                        tool_result = self._execute_tool_with_recovery(
                            tool_to_run,
                            tool_selection.tool_name,
                            tool_selection.tool_params,
                        )
                    except Exception as error:
                        primary_error = error
                        logger.warning(
                            f"[TOOL-RECOVERY][SYNC] Ferramenta primária {tool_selection.tool_name} falhou "
                            f"com exceção: {error}"
                        )
                        tool_result = {"status": "error", "error": str(error)}
                    active_tool_name = tool_selection.tool_name
                    active_tool_params = dict(tool_selection.tool_params or {})
                    active_tool_result = tool_result

                    if self._should_attempt_semantic_recovery(
                        user_query=resolved_query,
                        tool_name=tool_selection.tool_name,
                        tool_result=tool_result,
                        tool_error=primary_error,
                    ):
                        recovered = self._execute_semantic_tool_fallback_sync(
                            user_query=resolved_query,
                            primary_tool_name=tool_selection.tool_name,
                            primary_tool_params=tool_selection.tool_params,
                            fallback_tools=getattr(tool_selection, "fallback_tools", []),
                        )
                        if recovered:
                            active_tool_name = str(recovered["tool_name"])
                            active_tool_params = dict(recovered["tool_params"])
                            active_tool_result = recovered["tool_result"]
                        elif primary_error is not None:
                            raise primary_error
                        else:
                            logger.warning(
                                f"[DETERMINISTIC][SYNC] Sem fallback semântico válido para {tool_selection.tool_name}."
                            )

                    return self._format_tool_result_for_path(
                        resolved_query,
                        active_tool_name,
                        active_tool_result,
                        active_tool_params,
                    )
                except Exception as error:
                    logger.warning(
                        f"[DETERMINISTIC][SYNC] Falha na execução determinística ({tool_selection.tool_name}): {error}. "
                        "Fallback para fluxo LLM."
                    )

        # The adapter injects the effective system instruction.
        # Avoid duplicating system-role messages here to keep provider behavior consistent.
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
        if (
            self.enable_rag
            and self.retriever
            and self.retriever._initialized
            and self._should_use_reference_examples(
                resolved_query,
                tool_selection=tool_selection,
                chat_history=chat_history,
            )
        ):
            try:
                # Reutilizar lógica de formatação do _get_rag_examples mas de forma síncrona
                similar_docs = self.retriever.retrieve(resolved_query, top_k=2, method='hybrid')
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
            full_prompt_content = rag_context_str + "\n\n" + "PERGUNTA DO USUÁRIO AGORA:\n" + resolved_query
        else:
            full_prompt_content = resolved_query
            
        messages.append({"role": "user", "content": full_prompt_content})

        # ========================================================================
        # MODERN SYNC RUN (Context7)
        # ========================================================================
        
        # Determine tools to use
        tools_to_use = self.tool_declarations

        max_turns = 15
        current_turn = 0
        successful_tool_calls = 0

        while current_turn < max_turns:
            try:
                # Call LLM with tools using the active adapter contract.
                response = self._llm_get_completion(messages, tools_to_use, llm_task_type)

                if "error" in response:
                    logger.error(f"LLM Error: {response['error']}")
                    return self._generate_error_response(response['error'])

                # FIX: LOGGING DETALHADO - Detectar quando LLM ignora solicitações de gráfico
                response_type = "tool_call" if "tool_calls" in response else "text"
                logger.info(f"LLM Response Type: {response_type}")

                if response_type == "text" and self._should_attempt_routed_tool_rescue(
                    resolved_query,
                    str(response.get("content", "") or ""),
                    tool_selection,
                    successful_tool_calls,
                ):
                    logger.warning(
                        "[SYNC] LLM retornou texto sem tool call para query analítica. "
                        f"Executando resgate pela tool roteada: {getattr(tool_selection, 'tool_name', '')}"
                    )
                    rescued_response = self._attempt_routed_tool_rescue_sync(
                        resolved_query,
                        tool_selection,
                    )
                    if rescued_response is not None:
                        return rescued_response

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
                        tool_to_run = self._find_tool_by_name(func_name)
                        
                        tool_result = None
                        if tool_to_run:
                            try:
                                # Execute tool
                                tool_output = self._execute_tool_with_recovery(
                                    tool_to_run,
                                    func_name,
                                    func_args,
                                )

                                if self._is_tool_failure_result(tool_output):
                                    recovered = self._execute_semantic_tool_fallback_sync(
                                        user_query=resolved_query,
                                        primary_tool_name=func_name,
                                        primary_tool_params=func_args,
                                        fallback_tools=[],
                                    )
                                    if recovered:
                                        tool_output = recovered["tool_result"]
                                        if isinstance(tool_output, dict):
                                            tool_output.setdefault("_recovery", {})
                                            tool_output["_recovery"]["fallback_tool"] = recovered["tool_name"]
                                            tool_output["_recovery"]["mode"] = "semantic_fallback"

                                # CRITICAL FIX: Detectar se gerou gráfico com sucesso
                                if isinstance(tool_output, dict):
                                    is_chart = "chart_data" in tool_output or "chart_spec" in tool_output
                                    is_success = self._is_tool_success_result(tool_output)
                                    
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
                    content = self._generate_structured_visual_narrative(
                        user_query=resolved_query,
                        task_type=llm_task_type or "visualization",
                        fallback_text=self._clean_context7_violations(content, context_type="chart"),
                        chart_data=found_chart_data,
                        chart_summary=found_chart_summary,
                    )

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
                    content = self._generate_structured_visual_narrative(
                        user_query=resolved_query,
                        task_type=llm_task_type or "analysis",
                        fallback_text=self._clean_context7_violations(content, context_type="data"),
                        table_rows=found_resultados,
                    )
                    
                    return {
                        "type": "code_result",
                        "result": found_resultados, # Lista de dicts para o frontend renderizar Tabela
                        "table_data": found_resultados,
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
