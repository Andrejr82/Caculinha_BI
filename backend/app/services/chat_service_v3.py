"""
Chat Service V3 - Arquitetura Agent-Based (Refatorado 2026-01-24)

Arquitetura Agent-Based - Usando CaculinhaBIAgent
Serviço principal que orquestra o fluxo agent-based com ferramentas.

Fluxo:
1. Obter histórico da sessão
2. Preparar contexto do usuário (RLS, filtros)
3. Executar CaculinhaBIAgent.run_async()
4. Processar resposta do agente
5. Salvar no histórico

Princípios:
- LLM decide quais ferramentas usar
- Agente tem acesso a 20+ ferramentas
- Resposta natural e contextualizada
- Compatibilidade com API existente
"""

import logging
import asyncio
import sys
import time
import re
import json
import hashlib
import threading
import uuid
import structlog
from types import SimpleNamespace
from pathlib import Path
from datetime import date, timedelta
from typing import Dict, Any, Optional, Callable, Awaitable, Union, List
from dataclasses import dataclass
from collections import defaultdict, deque
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

# Componentes do agente
from backend.app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
from backend.app.core.agents.code_gen_agent import CodeGenAgent
from backend.application.agents.rag_agent import RAGAgent
from backend.application.agents.vectorization_agent import VectorizationAgent
from backend.domain.entities.memory_entry import MemoryEntry
from backend.infrastructure.adapters.duckdb_vector_adapter import DuckDBVectorAdapter

# Componentes existentes
from backend.app.core.llm_factory import LLMFactory
from backend.app.core.utils.session_manager import SessionManager
from backend.app.core.utils.field_mapper import FieldMapper
from backend.app.core.utils.executive_output import build_sales_dimension_report_from_rows, ensure_executive_output
from backend.app.core.utils.response_validator import validate_response
from backend.app.core.security.content_safety import sanitize_citations, sanitize_public_url, sanitize_text_label
from backend.app.core.learning.chat_example_capture import build_chat_example_payload
from backend.app.core.learning.unified_dataset_builder import build_default_unified_learning_dataset
from backend.app.core.rag.example_collector import ExampleCollector
from backend.app.config.settings import settings
from backend.app.config.database import get_db_context
from backend.app.infrastructure.redis_client import get_sync_redis_client
from backend.app.infrastructure.database.models import UserPreference
from backend.services.metrics import MetricsService
from backend.app.services.audit_log import get_audit_logger, AuditAction
from backend.app.services.image_generation import ImageGenerationService
from backend.app.services.chat_automation_service import ChatAutomationService
from backend.app.services.basket_analysis_service import BasketAnalysisService
from backend.app.schemas.basket_analysis import BasketAnalysisRequest
from backend.app.core.tools.basket_attachment_parser import build_basket_payload_from_documents
from backend.app.core.tools.basket_tools import (
    analyze_basket_logic,
    mine_market_basket_logic,
    simulate_promotion_logic,
)

logger = logging.getLogger(__name__)
trace_logger = structlog.get_logger("agentbi.chat.trace")

# Legacy namespace compatibility for contract/pipeline tests.
_THIS_MODULE = sys.modules[__name__]
sys.modules["app.services.chat_service_v3"] = _THIS_MODULE
sys.modules["backend.app.services.chat_service_v3"] = _THIS_MODULE


@dataclass
class SystemResponse:
    """
    Resposta do sistema (não gerada pela LLM).
    
    Usado para:
    - Erros
    - Esclarecimentos
    - Mensagens do sistema
    """
    message: str
    type: str  # "no_data", "error", "clarification_needed", "system"
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para resposta API"""
        result = {
            "type": "text",
            "result": {
                "mensagem": self.message
            },
            "system_response": True,
            "response_type": self.type
        }
        
        if self.suggestion:
            result["result"]["sugestao"] = self.suggestion
        
        return result


class ChatServiceV3:
    """
    Serviço de chat com arquitetura Agent-Based.
    
    Mudanças da refatoração (2026-01-24):
    - Usa CaculinhaBIAgent em vez de metrics-first
    - LLM decide quais ferramentas usar
    - Acesso a 20+ ferramentas de BI
    - Resposta mais flexível e contextualizada
    """
    
    _role_rate_limit_lock = threading.Lock()
    _role_rate_limit_events: Dict[str, deque[float]] = defaultdict(deque)
    _ROLE_RATE_LIMIT_FALLBACK = {
        "admin": 180,
        "analyst": 120,
        "viewer": 40,
        "guest": 20,
    }
    _AB_VARIANT_OPTIONS = {
        "prompt_variant": ("control", "concise"),
        "tool_routing_variant": ("control", "fast_fallback"),
        "ux_variant": ("control", "rich_progress"),
    }

    def __init__(
        self,
        session_manager: SessionManager,
        parquet_path: Optional[str] = None
    ):
        """
        Args:
            session_manager: Gerenciador de sessões
            parquet_path: Caminho para o parquet (opcional)
        """
        self.session_manager = session_manager
        self.basket_analysis_service = BasketAnalysisService()
        
        # Inicializar componentes
        logger.info("[DEBUG] [DEBUG] ChatServiceV3.__init__ INICIANDO (Agent-Based)...")
        
        # LLM adapter
        logger.info("[DEBUG] [DEBUG] Criando LLM adapter...")
        self.llm = LLMFactory.get_adapter(use_smart=True)
        logger.info(f"[DEBUG] [DEBUG] LLM adapter criado: {type(self.llm)}")
        
        # Field mapper para o agente
        logger.info("[DEBUG] [DEBUG] Criando FieldMapper...")
        self.field_mapper = FieldMapper()
        
        # CodeGenAgent (usado pelo CaculinhaBIAgent para cálculos complexos)
        logger.info("[DEBUG] [DEBUG] Criando CodeGenAgent...")
        try:
            self.code_gen_agent = CodeGenAgent()
        except Exception as e:
            logger.warning(f"CodeGenAgent indisponível no ambiente atual: {e}")
            self.code_gen_agent = None
        
        # [OK] NOVO: Usar CaculinhaBIAgent em vez de componentes separados
        logger.info("[DEBUG] [DEBUG] Criando CaculinhaBIAgent (default=analyst)...")
        self.agent = CaculinhaBIAgent(
            llm=self.llm,
            code_gen_agent=self.code_gen_agent,
            field_mapper=self.field_mapper,
            user_role="analyst",
            enable_rag=True
        )
        # Cache de agentes por role para evitar recriação por request
        self._agents_by_role: Dict[str, CaculinhaBIAgent] = {"analyst": self.agent}
        logger.info(f"[DEBUG] [DEBUG] CaculinhaBIAgent criado com sucesso: {type(self.agent)}")

        self.vectorization_agent: Optional[VectorizationAgent] = None
        self.vector_memory_repository: Optional[DuckDBVectorAdapter] = None
        self.memory_rag_agent: Optional[RAGAgent] = None
        self.image_generation_service = ImageGenerationService()
        self.chat_automation_service = ChatAutomationService()
        self.example_collector = ExampleCollector(examples_dir=settings.LEARNING_EXAMPLES_PATH)
        self._memory_index_lock = asyncio.Lock()
        self._memory_indexed_sessions: set[str] = set()
        try:
            vector_db_path = Path(SessionManager.default_db_path()).with_name("conversation_vectors.duckdb")
            self.vectorization_agent = VectorizationAgent()
            self.vector_memory_repository = DuckDBVectorAdapter(db_path=str(vector_db_path))
            self.memory_rag_agent = RAGAgent(
                vector_repository=self.vector_memory_repository,
                vectorization_agent=self.vectorization_agent,
            )
            logger.info("[OK] Conversational memory RAG inicializado: %s", vector_db_path)
        except Exception as exc:
            logger.warning("Conversational memory RAG indisponível no ambiente atual: %s", exc)
            self.vectorization_agent = None
            self.vector_memory_repository = None
            self.memory_rag_agent = None
        
        logger.info("[OK] ChatServiceV3 inicializado com CaculinhaBIAgent")

    @staticmethod
    def _memory_entry_id(conversation_id: str, message: Dict[str, Any]) -> str:
        metadata = message.get("metadata") if isinstance(message.get("metadata"), dict) else {}
        stable_source = (
            f"{conversation_id}:"
            f"{message.get('id') or metadata.get('request_id') or ''}:"
            f"{message.get('role') or ''}:"
            f"{message.get('content') or ''}"
        )
        return f"mem-{hashlib.md5(stable_source.encode('utf-8')).hexdigest()[:16]}"

    @staticmethod
    def _build_memory_entry_metadata(
        conversation_id: str,
        user_id: str,
        message: Dict[str, Any],
    ) -> Dict[str, Any]:
        metadata = message.get("metadata") if isinstance(message.get("metadata"), dict) else {}
        context = metadata.get("context") if isinstance(metadata.get("context"), dict) else {}
        ui_payload = metadata.get("ui_payload") if isinstance(metadata.get("ui_payload"), dict) else {}

        entry_metadata: Dict[str, Any] = {
            "user_id": str(user_id),
            "session_id": conversation_id,
            "role": str(message.get("role") or metadata.get("role_kind") or "user"),
        }
        for key in ("request_id", "source", "confidence", "mode"):
            value = metadata.get(key)
            if value not in (None, "", []):
                entry_metadata[key] = value
        for key in ("product_code", "segment", "une", "market_product_hint", "response_breakdown", "response_type"):
            value = context.get(key)
            if value not in (None, "", []):
                entry_metadata[key] = value
        payload_type = ui_payload.get("type")
        if payload_type not in (None, "", []):
            entry_metadata["ui_type"] = payload_type
        return entry_metadata

    async def _index_memory_message(
        self,
        conversation_id: str,
        user_id: str,
        message: Dict[str, Any],
    ) -> None:
        if self.vector_memory_repository is None:
            return

        content = str(message.get("content") or "").strip()
        role = str(message.get("role") or "").strip().lower()
        if not content or role not in {"user", "assistant"}:
            return

        embedding = None
        if self.vectorization_agent is not None:
            try:
                embedding = await self.vectorization_agent.embed_text(content)
            except Exception as exc:
                logger.warning("Falha ao gerar embedding de memória: %s", exc)

        metadata = self._build_memory_entry_metadata(conversation_id, user_id, message)
        request_or_message_id = message.get("id")
        if request_or_message_id in (None, "", []):
            message_metadata = message.get("metadata") if isinstance(message.get("metadata"), dict) else {}
            request_or_message_id = message_metadata.get("request_id")

        entry = MemoryEntry(
            id=self._memory_entry_id(conversation_id, message),
            conversation_id=conversation_id,
            message_id=str(request_or_message_id or ""),
            content=content,
            embedding=embedding,
            metadata=metadata,
        )
        await self.vector_memory_repository.index_entry(entry)

    async def _hydrate_user_memory_index(
        self,
        user_id: str,
        session_limit: int = 8,
        per_session_message_limit: int = 8,
    ) -> None:
        if self.vector_memory_repository is None:
            return

        sessions = self.session_manager.list_sessions(user_id=user_id, limit=session_limit, offset=0)
        if not isinstance(sessions, list) or not sessions:
            return

        async with self._memory_index_lock:
            for session in sessions:
                if not isinstance(session, dict):
                    continue
                session_id = str(session.get("id") or "").strip()
                if not session_id or session_id in self._memory_indexed_sessions:
                    continue

                history = self.session_manager.get_full_history(session_id, user_id)
                if not isinstance(history, list):
                    history = []
                for message in history[-per_session_message_limit:]:
                    if not isinstance(message, dict):
                        continue
                    try:
                        await self._index_memory_message(session_id, user_id, message)
                    except Exception as exc:
                        logger.warning(
                            "Falha ao indexar memória conversacional. session_id=%s error=%s",
                            session_id,
                            exc,
                        )
                self._memory_indexed_sessions.add(session_id)

    async def _retrieve_cross_session_memory(
        self,
        query: str,
        session_id: str,
        user_id: str,
        limit: int = 3,
    ) -> List[MemoryEntry]:
        if self.memory_rag_agent is None or not str(query or "").strip():
            return []

        await self._hydrate_user_memory_index(user_id=user_id)

        try:
            candidates = await self.memory_rag_agent.search(query, limit=max(limit * 6, 12))
        except Exception as exc:
            logger.warning("Falha ao recuperar memória conversacional: %s", exc)
            return []

        filtered: List[MemoryEntry] = []
        seen: set[tuple[str, str]] = set()
        for entry in candidates:
            metadata = entry.metadata if isinstance(entry.metadata, dict) else {}
            if str(metadata.get("user_id") or "") != str(user_id):
                continue
            if str(entry.conversation_id or "") == str(session_id):
                continue
            snippet = str(entry.content or "").strip()
            if not snippet:
                continue

            dedupe_key = (str(entry.conversation_id or ""), snippet[:200])
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            filtered.append(entry)
            if len(filtered) >= limit:
                break
        return filtered

    @staticmethod
    def _memory_entries_to_system_message(entries: List[MemoryEntry]) -> Optional[Dict[str, str]]:
        if not entries:
            return None

        lines = [
            "Contexto relevante recuperado de conversas anteriores do mesmo usuário.",
            "Use apenas se ajudar a responder a pergunta atual.",
        ]
        for index, entry in enumerate(entries, start=1):
            metadata = entry.metadata if isinstance(entry.metadata, dict) else {}
            labels: list[str] = []
            response_type = metadata.get("response_type") or metadata.get("ui_type")
            if response_type:
                labels.append(str(response_type))
            if metadata.get("source"):
                labels.append(str(metadata["source"]))
            prefix = f"{index}. "
            if labels:
                prefix += f"[{' | '.join(labels)}] "
            snippet = " ".join(str(entry.content or "").split())
            lines.append(f"{prefix}{snippet[:280]}")

        return {"role": "system", "content": "\n".join(lines)}

    @staticmethod
    def _is_missing_preferences_table_error(exc: Exception) -> bool:
        return "no such table" in str(exc).lower()

    @staticmethod
    def _query_without_attachment_metadata(query: str) -> str:
        lines = [line.strip() for line in str(query or "").splitlines()]
        kept_lines: list[str] = []
        skip_attachment_block = False
        for line in lines:
            lowered = line.lower()
            if lowered.startswith("considere os anexos desta sessão:"):
                continue
            if lowered == "anexos enviados:":
                skip_attachment_block = True
                continue
            if skip_attachment_block and lowered.startswith("- "):
                continue
            if skip_attachment_block and not lowered:
                skip_attachment_block = False
                continue
            if line:
                kept_lines.append(line)
        return " ".join(kept_lines).strip()

    @staticmethod
    def _query_mentions_attachment_context(query: str) -> bool:
        lowered = ChatServiceV3._query_without_attachment_metadata(query).lower()
        markers = (
            "anexo",
            "anexado",
            "arquivo",
            "arquivos",
            "imagem",
            "imagens",
            "foto",
            "fotos",
            "print",
            "screenshot",
            "planilha",
            "planilhas",
            "csv",
            "png",
            "jpg",
            "jpeg",
            "webp",
            "txt",
            "markdown",
            "json",
            "xml",
        )
        return any(marker in lowered for marker in markers)

    @staticmethod
    def _query_mentions_basket_context(query: str) -> bool:
        lowered = ChatServiceV3._query_without_attachment_metadata(query).lower()
        markers = (
            "cesta",
            "carrinho",
            "basket",
            "itens juntos",
            "saem juntos",
            "cross-sell",
            "cross sell",
            "afinidade",
            "combo",
            "pedido",
            "margem real",
            "rentabilidade",
            "promo",
            "desconto",
            "oferta",
        )
        return any(marker in lowered for marker in markers)

    @staticmethod
    def _query_is_market_basket(query: str) -> bool:
        lowered = ChatServiceV3._query_without_attachment_metadata(query).lower()
        return any(
            marker in lowered
            for marker in (
                "itens juntos",
                "saem juntos",
                "comprados juntos",
                "cross-sell",
                "cross sell",
                "afinidade",
                "lift",
                "associacao",
                "associação",
            )
        )

    @staticmethod
    def _query_is_promotion_simulation(query: str) -> bool:
        lowered = ChatServiceV3._query_without_attachment_metadata(query).lower()
        return any(marker in lowered for marker in ("promo", "desconto", "oferta", "campanha", "leve"))

    @staticmethod
    def _query_is_generic_attachment_analysis(query: str) -> bool:
        lowered = ChatServiceV3._query_without_attachment_metadata(query).lower()
        generic_phrases = (
            "analise os arquivos anexados",
            "analise o arquivo anexado",
            "analise os anexos",
            "analise o anexo",
            "analisar os arquivos anexados",
            "analisar o arquivo anexado",
            "considere os anexos desta sessao",
            "considere os anexos desta sessão",
        )
        return any(phrase in lowered for phrase in generic_phrases)

    @staticmethod
    def _entry_is_session_attachment(entry: Dict[str, Any]) -> bool:
        metadata = entry.get("metadata") if isinstance(entry.get("metadata"), dict) else {}
        uploaded_via = str(metadata.get("uploaded_via") or "").strip().lower()
        has_session_id = bool(str(metadata.get("session_id") or "").strip())
        return has_session_id or uploaded_via in {"chat_attachment", "chat_image"}

    @staticmethod
    def _extract_percentage_from_query(query: str) -> Optional[float]:
        match = re.search(r"(-?\d+(?:[.,]\d+)?)\s*%", str(query or ""))
        if not match:
            return None
        try:
            return float(match.group(1).replace(",", "."))
        except ValueError:
            return None

    @staticmethod
    def _extract_category_from_query(query: str) -> Optional[str]:
        match = re.search(
            r"(?:categoria|grupo)\s+([a-zA-ZÀ-ÿ0-9 _-]+?)(?:\s+em\s+|\s+na\s+|\s+no\s+|\s+nos?\s+|\s+nas?\s+|\s+por\s+|$)",
            str(query or ""),
            re.IGNORECASE,
        )
        if not match:
            return None
        value = re.sub(r"\s+", " ", match.group(1)).strip(" .,:;!?-")
        return value or None

    @staticmethod
    def _resolve_period_dates(period_filter: Optional[str]) -> tuple[Optional[date], Optional[date]]:
        if not period_filter:
            return None, None
        today = date.today()
        if period_filter.endswith("d") and period_filter[:-1].isdigit():
            days = int(period_filter[:-1])
            return today - timedelta(days=max(days - 1, 0)), today
        if period_filter.endswith("w") and period_filter[:-1].isdigit():
            weeks = int(period_filter[:-1])
            return today - timedelta(days=max(weeks * 7 - 1, 0)), today
        if period_filter.endswith("m") and period_filter[:-1].isdigit():
            months = int(period_filter[:-1])
            return today - timedelta(days=max(months * 30 - 1, 0)), today
        if period_filter == "mes_atual":
            return today.replace(day=1), today
        if period_filter == "hoje":
            return today, today
        return None, None

    def _build_dataset_basket_request(self, query: str) -> BasketAnalysisRequest:
        from backend.app.core.utils.query_router import (
            extract_period_filter,
            extract_product_code,
            extract_segment_filter,
            extract_top_limit,
            extract_une_filter,
        )

        period_filter = extract_period_filter(query)
        start_date, end_date = self._resolve_period_dates(period_filter)
        product_code = extract_product_code(query)
        return BasketAnalysisRequest(
            start_date=start_date,
            end_date=end_date,
            une=extract_une_filter(query),
            segment=extract_segment_filter(query),
            category=self._extract_category_from_query(query),
            target_product=str(product_code) if product_code is not None else None,
            max_rules=extract_top_limit(query) or 20,
        )

    @staticmethod
    def _format_dataset_basket_message(result: Dict[str, Any]) -> str:
        status = str(result.get("status") or "")
        mode = str(result.get("analysis_mode") or "")
        summary = result.get("business_summary") or []
        limitations = result.get("limitations") or []
        top_rules = result.get("top_rules") or []
        parameters = result.get("parameters") if isinstance(result.get("parameters"), dict) else {}

        scope_parts: list[str] = []
        if parameters.get("une"):
            scope_parts.append(f"UNE {parameters['une']}")
        if parameters.get("segment"):
            scope_parts.append(f"segmento {parameters['segment']}")
        if parameters.get("category"):
            scope_parts.append(f"categoria {parameters['category']}")
        if parameters.get("start_date") or parameters.get("end_date"):
            scope_parts.append(
                f"periodo {parameters.get('start_date') or 'inicio aberto'} até {parameters.get('end_date') or 'fim aberto'}"
            )

        lines: list[str] = []
        if status == "unsupported":
            lines.append("Resumo executivo: a base local nao comprovou suporte transacional suficiente para basket analysis confiavel.")
        elif status == "no_data":
            lines.append("Resumo executivo: os filtros aplicados nao retornaram transacoes suficientes para gerar regras de associacao.")
        elif summary:
            lines.append(f"Resumo executivo: {summary[0]}")
        else:
            lines.append("Resumo executivo: a analise foi executada, mas nao encontrou regras relevantes com os thresholds atuais.")

        if scope_parts:
            lines.append(f"Escopo analisado: {', '.join(scope_parts)}.")

        if top_rules:
            best_rule = top_rules[0]
            antecedent = " + ".join(best_rule["antecedent"])
            consequent = " + ".join(best_rule["consequent"])
            lines.append(
                f"Principal regra encontrada: {antecedent} -> {consequent} (support {best_rule['support']:.2%}, confidence {best_rule['confidence']:.2%}, lift {best_rule['lift']:.2f})."
            )
            lines.append("Oportunidade de cross-sell: use a regra acima como inferencia analitica, nao como fato absoluto.")

        if mode == "subset_transactional_supported":
            lines.append("Modo da analise: subset_transactional_supported em subset controlado da base.")
        elif mode == "unsupported":
            lines.append("Modo da analise: unsupported.")

        if limitations:
            lines.append(f"Limitacoes: {limitations[0]}")

        return "\n".join(lines)

    def _run_dataset_basket_pipeline(self, query: str) -> Optional[Dict[str, Any]]:
        if not self._query_is_market_basket(query):
            return None

        request_payload = self._build_dataset_basket_request(query)
        try:
            result = self.basket_analysis_service.analyze(request_payload)
        except ValueError:
            return None
        response_text = self._format_dataset_basket_message(result)
        confidence = 0.98
        if result.get("analysis_mode") == "subset_transactional_supported":
            confidence = 0.76
        elif result.get("analysis_mode") == "unsupported":
            confidence = 0.99

        return {
            "response": response_text,
            "table_data": result.get("top_rules") or result.get("top_itemsets") or [],
            "source": "service.basket_analysis",
            "confidence": confidence,
            "mode": "dataset_basket_pipeline",
            "tool_calls": [
                {
                    "name": "basket_analysis_service",
                    "args": request_payload.model_dump(mode="json", exclude_none=True),
                }
            ],
            "result": {
                "mensagem": response_text,
                "basket_analysis": result,
                "warnings": result.get("limitations") or [],
            },
        }

    def _run_attachment_basket_pipeline(
        self,
        query: str,
        document_context: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if not document_context:
            return None

        is_market_basket = self._query_is_market_basket(query)
        is_promotion = self._query_is_promotion_simulation(query)
        mentions_basket = self._query_mentions_basket_context(query)
        is_generic_attachment_analysis = self._query_is_generic_attachment_analysis(query)

        if is_market_basket:
            preferred_kind = "transacoes"
        elif is_promotion:
            preferred_kind = "itens"
        elif mentions_basket:
            preferred_kind = "itens"
        elif is_generic_attachment_analysis:
            preferred_kind = "auto"
        else:
            return None

        parsed = build_basket_payload_from_documents(document_context, preferred_kind=preferred_kind)
        if not parsed:
            return None

        files = parsed.get("files") or []
        warnings = parsed.get("warnings") or []

        if parsed["kind"] == "transacoes" and (is_market_basket or is_generic_attachment_analysis):
            tool_result = mine_market_basket_logic(parsed["payload"]["transacoes"])
            top_rules = tool_result.get("regras_associacao") or []
            if top_rules:
                best_rule = top_rules[0]
                lead = (
                    f"O anexo mostra afinidade entre {' + '.join(best_rule['antecedente'])} "
                    f"e {' + '.join(best_rule['consequente'])}, com lift {best_rule['lift']:.2f}."
                )
            else:
                lead = "Analisei o anexo e nao encontrei combinacoes fortes o suficiente com os limiares atuais."
            return {
                "response": lead,
                "table_data": top_rules,
                "source": "tool.minerar_cestas_frequentes",
                "confidence": 0.99,
                "mode": "attachment_basket_pipeline",
                "tool_calls": [
                    {
                        "name": "minerar_cestas_frequentes",
                        "args": {
                            "transacoes": len(parsed["payload"]["transacoes"]),
                            "files": files,
                        },
                    }
                ],
                "result": {
                    "mensagem": lead,
                    "warnings": warnings,
                },
            }

        if parsed["kind"] != "itens":
            return None

        if is_promotion:
            desconto_pct = self._extract_percentage_from_query(query)
            tool_result = simulate_promotion_logic(
                itens=parsed["payload"]["itens"],
                tipo_promocao="percentual" if desconto_pct is not None else "valor_fixo",
                desconto_pct=desconto_pct,
            )
            before = tool_result["antes"]
            after = tool_result["depois"]
            lead = (
                f"No anexo, a promocao reduz a margem real de {before['margem_real_pct']:.2f}% "
                f"para {after['margem_real_pct']:.2f}%."
            )
            return {
                "response": lead,
                "table_data": tool_result.get("itens_criticos") or [],
                "source": "tool.simular_promocao_cesta",
                "confidence": 0.99,
                "mode": "attachment_basket_pipeline",
                "tool_calls": [
                    {
                        "name": "simular_promocao_cesta",
                        "args": {
                            "itens": len(parsed["payload"]["itens"]),
                            "desconto_pct": desconto_pct,
                            "files": files,
                        },
                    }
                ],
                "result": {
                    "mensagem": lead,
                    "warnings": warnings,
                },
            }

        tool_result = analyze_basket_logic(parsed["payload"]["itens"])
        totals = tool_result["totais"]
        lead = (
            f"Analisei a cesta do anexo: receita liquida de R$ {totals['receita_liquida']:.2f} "
            f"e margem real de {totals['margem_real_pct']:.2f}%."
        )
        return {
            "response": lead,
            "table_data": tool_result.get("itens") or [],
            "source": "tool.analisar_cesta_compras",
            "confidence": 0.99,
            "mode": "attachment_basket_pipeline",
            "tool_calls": [
                {
                    "name": "analisar_cesta_compras",
                    "args": {
                        "itens": len(parsed["payload"]["itens"]),
                        "files": files,
                    },
                }
            ],
            "result": {
                "mensagem": lead,
                "warnings": warnings,
            },
        }

    def _assign_ab_variants(self, user_id: str, session_id: str, request_id: str) -> Dict[str, str]:
        seed = f"{user_id}:{session_id}:{request_id}"
        variants: Dict[str, str] = {}
        for experiment_name, options in self._AB_VARIANT_OPTIONS.items():
            digest = hashlib.md5(f"{experiment_name}:{seed}".encode("utf-8")).hexdigest()
            bucket = int(digest[:8], 16)
            variants[experiment_name] = options[bucket % len(options)]
        return variants

    @staticmethod
    def _is_image_generation_query(query: str) -> bool:
        lowered = str(query or "").strip().lower()
        if not lowered:
            return False
        markers = (
            "gere uma imagem",
            "gerar uma imagem",
            "crie uma imagem",
            "criar uma imagem",
            "desenhe",
            "ilustre",
            "faça uma imagem",
            "faca uma imagem",
        )
        return any(marker in lowered for marker in markers)

    async def _load_user_preferences(self, user_id: str) -> Dict[str, str]:
        try:
            normalized_user_id = uuid.UUID(str(user_id))
        except (ValueError, TypeError, AttributeError):
            return {}

        try:
            async with get_db_context() as db:
                result = await db.execute(
                    select(UserPreference).where(UserPreference.user_id == normalized_user_id)
                )
                preferences = result.scalars().all()
        except SQLAlchemyError as exc:
            if self._is_missing_preferences_table_error(exc):
                return {}
            logger.warning("Falha ao carregar preferências do usuário %s: %s", user_id, exc)
            return {}
        except Exception as exc:
            logger.warning("Falha ao carregar preferências do usuário %s: %s", user_id, exc)
            return {}

        return {
            str(pref.key): str(pref.value)
            for pref in preferences
            if pref.key and pref.value not in (None, "")
        }

    @staticmethod
    def _preferences_to_system_message(preferences: Dict[str, str]) -> Optional[Dict[str, str]]:
        if not preferences:
            return None

        lines = ["Perfil e preferências persistidas do usuário:"]
        language = preferences.get(UserPreference.Keys.LANGUAGE)
        if language:
            lines.append(f"- Responda preferencialmente em {language}.")

        preferred_chart = preferences.get(UserPreference.Keys.PREFERRED_CHART_TYPE)
        if preferred_chart:
            lines.append(f"- Quando um gráfico for apropriado, priorize o tipo {preferred_chart}.")

        preferred_format = preferences.get(UserPreference.Keys.PREFERRED_DATA_FORMAT)
        if preferred_format == "table":
            lines.append("- Prefira respostas tabulares quando houver dados estruturados.")
        elif preferred_format == "chart":
            lines.append("- Prefira respostas visuais quando houver dados estruturados.")
        elif preferred_format == "both":
            lines.append("- Quando útil, combine texto com tabela ou gráfico.")

        analysis_focus = preferences.get(UserPreference.Keys.ANALYSIS_FOCUS)
        if analysis_focus:
            lines.append(f"- Dê ênfase analítica em {analysis_focus}.")

        company_name = preferences.get(UserPreference.Keys.COMPANY_NAME)
        if company_name:
            lines.append(f"- Considere que a empresa do usuário é {company_name}.")

        business_segment = preferences.get(UserPreference.Keys.BUSINESS_SEGMENT)
        if business_segment:
            lines.append(f"- Considere o segmento de negócio {business_segment}.")

        return {"role": "system", "content": "\n".join(lines)}

    async def _retrieve_document_context(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tenant_id: str = "default",
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        if self.vector_memory_repository is None or not str(query or "").strip():
            return []

        query_embedding = None
        if self.vectorization_agent is not None:
            try:
                query_embedding = await self.vectorization_agent.embed_text(query)
            except Exception as exc:
                logger.warning("Falha ao gerar embedding para documentos internos: %s", exc)

        try:
            results = await self.vector_memory_repository.hybrid_document_search(
                query=query,
                query_embedding=query_embedding,
                tenant_id=tenant_id,
                limit=max(limit * 2, 6),
            )
        except Exception as exc:
            logger.warning("Falha ao recuperar documentos internos: %s", exc)
            results = []

        explicit_attachment_context = self._query_mentions_attachment_context(query)
        if results:
            filtered_results: List[Dict[str, Any]] = []
            for item in results:
                if self._entry_is_session_attachment(item) and not explicit_attachment_context:
                    continue
                filtered_results.append(item)
            results = filtered_results

        attachment_candidates: List[Dict[str, Any]] = []
        normalized_session_id = str(session_id or "").strip()
        should_include_session_docs = bool(normalized_session_id) and explicit_attachment_context
        if should_include_session_docs:
            try:
                recent_documents = await self.vector_memory_repository.list_recent_documents(
                    limit=max(limit * 6, 18),
                    tenant_id=tenant_id,
                )
            except Exception as exc:
                logger.warning("Falha ao listar anexos recentes da sessão: %s", exc)
                recent_documents = []

            for item in recent_documents:
                metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
                if str(metadata.get("session_id") or "").strip() != normalized_session_id:
                    continue
                attachment_candidates.append(item)

        ranked_results = [*attachment_candidates, *results]

        deduped: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for item in ranked_results:
            document_id = str(item.get("document_id") or "").strip()
            content = str(item.get("content") or "").strip()
            metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            uploaded_by = str(metadata.get("uploaded_by") or "").strip()
            if uploaded_by and user_id and uploaded_by != str(user_id):
                continue
            if not document_id or not content or document_id in seen:
                continue
            seen.add(document_id)
            deduped.append(item)
            if len(deduped) >= limit:
                break
        return deduped

    @staticmethod
    def _documents_to_system_message(entries: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
        if not entries:
            return None

        lines = [
            "Trechos relevantes de documentos internos/base de conhecimento recuperados para a pergunta atual.",
            "Use estes trechos apenas se forem úteis e cite a origem quando fundamentarem a resposta.",
        ]
        if any(ChatServiceV3._entry_is_session_attachment(entry) for entry in entries):
            lines.append(
                "Anexos da sessao sao contexto auxiliar; a fonte primaria continua sendo a base local do projeto, salvo pedido explicito do usuario para analisar o anexo."
            )
        for index, entry in enumerate(entries, start=1):
            metadata = entry.get("metadata") if isinstance(entry.get("metadata"), dict) else {}
            source_label = (
                metadata.get("filename")
                or metadata.get("source")
                or metadata.get("title")
                or f"documento {index}"
            )
            snippet = " ".join(str(entry.get("content") or "").split())
            lines.append(f"{index}. [{source_label}] {snippet[:280]}")
        return {"role": "system", "content": "\n".join(lines)}

    @staticmethod
    def _documents_to_citations(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        citations: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for index, entry in enumerate(entries, start=1):
            metadata = entry.get("metadata") if isinstance(entry.get("metadata"), dict) else {}
            document_id = str(entry.get("document_id") or f"internal-doc-{index}")
            if document_id in seen:
                continue
            seen.add(document_id)
            source_label = (
                metadata.get("filename")
                or metadata.get("title")
                or metadata.get("source")
                or f"Documento interno {index}"
            )
            citations.append(
                {
                    "source": sanitize_text_label(source_label),
                    "domain": "internal_document",
                    "url": sanitize_public_url(metadata.get("url")),
                    "document_id": sanitize_text_label(document_id, max_length=120),
                }
            )
        return sanitize_citations(citations)

    @classmethod
    def _reset_role_rate_limit_state(cls) -> None:
        with cls._role_rate_limit_lock:
            cls._role_rate_limit_events.clear()

    def _get_role_rate_limit_per_minute(self, normalized_role: str) -> int:
        settings_map = {
            "admin": int(getattr(settings, "CHAT_RATE_LIMIT_PER_MINUTE_ADMIN", self._ROLE_RATE_LIMIT_FALLBACK["admin"]) or self._ROLE_RATE_LIMIT_FALLBACK["admin"]),
            "analyst": int(getattr(settings, "CHAT_RATE_LIMIT_PER_MINUTE_ANALYST", self._ROLE_RATE_LIMIT_FALLBACK["analyst"]) or self._ROLE_RATE_LIMIT_FALLBACK["analyst"]),
            "viewer": int(getattr(settings, "CHAT_RATE_LIMIT_PER_MINUTE_VIEWER", self._ROLE_RATE_LIMIT_FALLBACK["viewer"]) or self._ROLE_RATE_LIMIT_FALLBACK["viewer"]),
            "guest": int(getattr(settings, "CHAT_RATE_LIMIT_PER_MINUTE_GUEST", self._ROLE_RATE_LIMIT_FALLBACK["guest"]) or self._ROLE_RATE_LIMIT_FALLBACK["guest"]),
        }
        return max(1, int(settings_map.get(normalized_role, self._ROLE_RATE_LIMIT_FALLBACK["analyst"])))

    def _enforce_role_rate_limit(self, user_id: str, normalized_role: str) -> Optional[int]:
        """
        Rate limit por perfil/usuário em janela deslizante de 60s.
        Retorna `None` quando permitido ou o limite quando excedido.
        """
        limit = self._get_role_rate_limit_per_minute(normalized_role)
        key = f"{normalized_role}:{str(user_id or '').strip() or 'anonymous'}"
        redis_client = get_sync_redis_client()
        if redis_client is not None:
            now_wall = time.time()
            window_start = now_wall - 60.0
            redis_key = f"{settings.REDIS_KEY_PREFIX}:chat_role_rate_limit:{key}"
            member = f"{now_wall}:{time.monotonic_ns()}"
            try:
                redis_client.zremrangebyscore(redis_key, 0, window_start)
                current_count = int(redis_client.zcard(redis_key) or 0)
                if current_count >= limit:
                    return limit
                redis_client.zadd(redis_key, {member: now_wall})
                redis_client.expire(redis_key, 60)
                return None
            except Exception as exc:
                logger.warning("[DEBUG] Redis role rate limit falhou; usando fallback local: %s", exc)
        now = time.monotonic()
        window_start = now - 60.0
        with self._role_rate_limit_lock:
            bucket = self._role_rate_limit_events[key]
            while bucket and bucket[0] < window_start:
                bucket.popleft()
            if len(bucket) >= limit:
                return limit
            bucket.append(now)
        return None

    def _query_expected_capability(self, query: str) -> Optional[str]:
        q = self._query_without_attachment_metadata(query).lower()
        if any(k in q for k in ["pesquisa de mercado", "concorrente", "cotação", "cotacao", "preço de mercado", "preco de mercado"]):
            return "market_research"
        if any(k in q for k in ["exportar", "exporte", "export", "csv", "excel", "xlsx", "planilha", "baixar arquivo"]):
            return "export"
        if any(k in q for k in ["dashboard", "painel interativo"]):
            return "dashboard"
        if any(k in q for k in ["tabela", "tabular", "liste", "listar", "lista em tabela", "mostre em tabela"]):
            return "table"
        if any(k in q for k in ["gráfico", "grafico", "chart", "ranking"]):
            return "visualization"
        if any(k in q for k in [
            "eoq",
            "lote econômico",
            "lote economico",
            "simulação",
            "simulacao",
            "sensibilidade",
            "margem de contribuição",
            "mc",
            "cesta",
            "carrinho",
            "margem real",
            "desconto",
            "promoção",
            "promocao",
            "rentabilidade",
        ]):
            return "calculation"
        if any(k in q for k in ["ruptura", "estoque", "vendas", "segmento", "une", "loja"]):
            return "data_query"
        return None

    def _response_matches_query_intent(self, query: str, response: Dict[str, Any]) -> bool:
        expected_capability = self._query_expected_capability(query)
        if not expected_capability:
            return True

        actual_capability = self._response_capability(response)
        if expected_capability == actual_capability:
            return True

        mode = str(response.get("mode") or "").strip().lower()
        if mode in {"attachment_basket_pipeline", "dataset_basket_pipeline"}:
            if self._query_is_market_basket(query) or self._query_is_promotion_simulation(query):
                return True
            if self._query_mentions_basket_context(query):
                return expected_capability == "calculation"
            return False

        return True

    @staticmethod
    def _response_has_visual_payload(response: Dict[str, Any]) -> bool:
        return bool(response.get("chart_data") or response.get("dashboard_spec") or response.get("type") == "dashboard")

    @staticmethod
    def _response_has_export_payload(response: Dict[str, Any]) -> bool:
        artifact = response.get("artifact")
        if isinstance(artifact, dict) and any(artifact.get(key) for key in ("download_url", "filename")):
            return True

        automation_request = response.get("automation_request")
        result_payload = response.get("result", {}) if isinstance(response.get("result"), dict) else {}
        if not isinstance(automation_request, dict):
            automation_request = result_payload.get("automation_request")
        if not isinstance(automation_request, dict):
            return False

        action = str(automation_request.get("action") or "").strip().lower()
        follow_up_action = str(automation_request.get("follow_up_action") or "").strip().lower()
        nested_artifact = automation_request.get("artifact")
        if isinstance(nested_artifact, dict) and any(nested_artifact.get(key) for key in ("download_url", "filename")):
            return True

        export_markers = ("export", "csv", "spreadsheet", "excel", "xlsx", "report")
        return (
            any(marker in action for marker in export_markers)
            or any(marker in follow_up_action for marker in export_markers)
        ) and any(
            automation_request.get(key) not in (None, "", [])
            for key in ("approval_status", "proposal_id", "title")
        )

    @staticmethod
    def _response_capability(response: Dict[str, Any]) -> str:
        internal_meta = response.get("_internal_meta", {}) if isinstance(response.get("_internal_meta"), dict) else {}
        source = str(response.get("source") or internal_meta.get("source") or "").lower()
        if response.get("dashboard_spec") or response.get("type") == "dashboard":
            return "dashboard"
        if response.get("chart_data"):
            return "visualization"
        if ChatServiceV3._response_has_export_payload(response):
            return "export"
        if "gerar_dashboard_executivo" in source or source == "tool.dashboard":
            return "dashboard"
        if "gerar_grafico_universal_v2" in source or "gerar_grafico_universal" in source or source == "tool.chart":
            return "visualization"
        if "pesquisar_mercado_web" in source or "pesquisar_precos_concorrentes" in source:
            return "market_research"
        if (
            "sandbox.code_gen_agent" in source
            or "calcular_eoq" in source
            or "analisar_cesta_compras" in source
            or "simular_promocao_cesta" in source
            or "minerar_cestas_frequentes" in source
            or "basket_analysis" in source
        ):
            return "calculation"
        if isinstance(response.get("table_data"), list) and response.get("table_data"):
            return "table"
        return "data_query"

    @staticmethod
    def _response_has_dashboard_payload(response: Dict[str, Any]) -> bool:
        return bool(response.get("dashboard_spec") or response.get("type") == "dashboard")

    @staticmethod
    def _response_has_table_payload(response: Dict[str, Any]) -> bool:
        return bool(isinstance(response.get("table_data"), list) and response.get("table_data"))

    def _response_satisfies_expected_capability(
        self,
        expected_capability: str,
        response: Dict[str, Any],
    ) -> bool:
        if expected_capability == "visualization":
            return self._response_has_visual_payload(response)
        if expected_capability == "dashboard":
            return self._response_has_dashboard_payload(response)
        if expected_capability == "table":
            return self._response_has_table_payload(response)
        if expected_capability == "export":
            return self._response_has_export_payload(response)
        return True

    async def _attempt_capability_recovery(
        self,
        *,
        query: str,
        chat_history: List[Dict[str, Any]],
        agent: Any,
        current_response: Dict[str, Any],
        on_progress: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    ) -> Optional[Dict[str, Any]]:
        expected_capability = str(self._query_expected_capability(query) or "").strip().lower()
        if expected_capability not in {"visualization", "dashboard", "table", "export"}:
            return None
        if self._response_satisfies_expected_capability(expected_capability, current_response):
            return None
        if not hasattr(agent, "_attempt_routed_tool_rescue"):
            return None

        try:
            from backend.app.core.utils.intent_classifier import classify_intent
            from backend.app.core.utils.query_router import route_query

            resolved_query = (
                agent._resolve_query_with_history_context(query, chat_history)
                if hasattr(agent, "_resolve_query_with_history_context")
                else query
            )
            intent_result = classify_intent(resolved_query)
            tool_selection = route_query(
                intent=intent_result.intent,
                query=resolved_query,
                confidence=intent_result.confidence,
            )
            if hasattr(agent, "_enrich_tool_selection_for_business"):
                agent._enrich_tool_selection_for_business(resolved_query, tool_selection, chat_history=chat_history)
            if hasattr(agent, "_ensure_tool_selection_available"):
                agent._ensure_tool_selection_available(resolved_query, tool_selection)
            if hasattr(agent, "_build_clarification_if_needed"):
                clarification = agent._build_clarification_if_needed(
                    resolved_query,
                    tool_selection.tool_name,
                    tool_selection.confidence,
                    chat_history=chat_history,
                )
                if clarification is not None:
                    return None
            recovered = await agent._attempt_routed_tool_rescue(
                resolved_query,
                tool_selection,
                on_progress=on_progress,
            )
            if recovered and self._response_satisfies_expected_capability(expected_capability, recovered):
                return recovered
        except Exception as exc:
            logger.warning(
                "Falha ao executar recuperação orientada à intenção para capability %s: %s",
                expected_capability,
                exc,
            )
        return None

    @staticmethod
    def _is_no_data_message(text: str) -> bool:
        normalized = str(text or "").strip().lower()
        if not normalized:
            return False
        markers = [
            "não encontrei dados",
            "nao encontrei dados",
            "não consegui gerar o gráfico",
            "nao consegui gerar o grafico",
            "não consegui gerar uma visualização",
            "nao consegui gerar uma visualizacao",
            "não consegui gerar um dashboard",
            "nao consegui gerar um dashboard",
            "não consegui montar uma tabela",
            "nao consegui montar uma tabela",
            "não consegui preparar uma exportação",
            "nao consegui preparar uma exportacao",
            "sem evidência pública",
            "sem evidencia publica",
            "nenhum dado encontrado",
            "não foi possível gerar",
            "nao foi possivel gerar",
            "não houve evidência pública suficiente",
            "nao houve evidencia publica suficiente",
        ]
        return any(marker in normalized for marker in markers)

    @staticmethod
    def _extract_response_tools(response: Dict[str, Any]) -> list[str]:
        tools = ChatServiceV3._extract_tool_call_names(response.get("tool_calls"))
        internal_meta = response.get("_internal_meta", {}) if isinstance(response.get("_internal_meta"), dict) else {}
        source = str(response.get("source") or internal_meta.get("source") or "").strip()
        if source.startswith("tool."):
            tool_name = source.replace("tool.", "", 1).strip()
            if tool_name:
                tools.append(tool_name)
        if source == "sandbox.code_gen_agent":
            tools.append("calculation_sandbox")
        deduped = []
        seen = set()
        for item in tools:
            normalized = str(item or "").strip()
            if not normalized or normalized in seen:
                continue
            deduped.append(normalized)
            seen.add(normalized)
        return deduped

    def _record_semantic_quality_metrics(
        self,
        metrics: MetricsService,
        query: str,
        processed_response: Dict[str, Any],
        normalized_role: str,
    ) -> None:
        expected_capability = self._query_expected_capability(query)
        actual_capability = self._response_capability(processed_response)

        if expected_capability:
            metrics.increment("tool_selection_accuracy_total")
            metrics.increment("tool_selection_accuracy_total", labels={"capability": expected_capability})
            if expected_capability == actual_capability:
                metrics.increment("tool_selection_accuracy_hits_total")
                metrics.increment("tool_selection_accuracy_hits_total", labels={"capability": expected_capability})

            total_acc = metrics.get_counter("tool_selection_accuracy_total")
            hits_acc = metrics.get_counter("tool_selection_accuracy_hits_total")
            accuracy = (hits_acc / total_acc) if total_acc > 0 else 0.0
            metrics.set_gauge("tool_selection_accuracy", round(accuracy, 4))

        internal_meta = processed_response.get("_internal_meta", {}) if isinstance(processed_response.get("_internal_meta"), dict) else {}
        source = str(processed_response.get("source") or internal_meta.get("source") or "").lower()
        citations = processed_response.get("citations")
        if citations in (None, "", []):
            citations = internal_meta.get("citations")
        citations_count = len(citations) if isinstance(citations, list) else 0
        needs_citations = expected_capability == "market_research" or "pesquisar_mercado_web" in source or "pesquisar_precos_concorrentes" in source
        if needs_citations:
            metrics.increment("citation_coverage_total")
            metrics.increment("citation_coverage_total", labels={"role": normalized_role})
            if citations_count > 0:
                metrics.increment("citation_coverage_hits_total")
                metrics.increment("citation_coverage_hits_total", labels={"role": normalized_role})

            citations_total = metrics.get_counter("citation_coverage_total")
            citations_hits = metrics.get_counter("citation_coverage_hits_total")
            coverage = (citations_hits / citations_total) if citations_total > 0 else 0.0
            metrics.set_gauge("citation_coverage", round(coverage, 4))

        message = str(processed_response.get("result", {}).get("mensagem", "") or "")
        no_data_detected = self._is_no_data_message(message)
        has_evidence = bool(citations_count > 0 or processed_response.get("chart_data") or processed_response.get("dashboard_spec"))
        if no_data_detected:
            metrics.increment("no_data_total")
            if has_evidence:
                metrics.increment("no_data_false_positive_total")

            no_data_total = metrics.get_counter("no_data_total")
            false_positive_total = metrics.get_counter("no_data_false_positive_total")
            fp_rate = (false_positive_total / no_data_total) if no_data_total > 0 else 0.0
            metrics.set_gauge("no_data_false_positive_rate", round(fp_rate, 4))

    def _build_response_validation_context(self, query: str, processed_response: Dict[str, Any]) -> Dict[str, Any]:
        internal_meta = processed_response.get("_internal_meta", {}) if isinstance(processed_response.get("_internal_meta"), dict) else {}
        source = str(processed_response.get("source") or internal_meta.get("source") or "").strip()
        mode = str(processed_response.get("mode") or internal_meta.get("mode") or "").strip()
        citations = processed_response.get("citations")
        if citations in (None, "", []):
            citations = internal_meta.get("citations")
        citations = sanitize_citations(citations)
        message = str(processed_response.get("result", {}).get("mensagem", "") or "")
        chart_data = processed_response.get("chart_data")
        dashboard_spec = processed_response.get("dashboard_spec")
        table_data = processed_response.get("table_data")
        has_export_payload = self._response_has_export_payload(processed_response)
        return {
            "expected_capability": self._query_expected_capability(query),
            "actual_capability": self._response_capability(processed_response),
            "source": source,
            "mode": mode,
            "citations_count": len(citations) if isinstance(citations, list) else 0,
            "has_visual_payload": bool(chart_data or dashboard_spec),
            "has_dashboard_payload": bool(dashboard_spec),
            "has_table_payload": bool(isinstance(table_data, list) and table_data),
            "has_export_payload": has_export_payload,
            "no_data_detected": self._is_no_data_message(message),
            "has_evidence": bool((isinstance(citations, list) and citations) or chart_data or dashboard_spec or (isinstance(table_data, list) and table_data) or has_export_payload),
        }

    def _build_validation_block_response(
        self,
        *,
        query: str,
        validation_result: Any,
        validation_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        expected_capability = str(validation_context.get("expected_capability") or "").strip().lower()
        block_reason = str(getattr(validation_result, "block_reason", "") or "").strip().lower()
        response_mode = str(validation_context.get("mode") or "").strip().lower()

        if expected_capability == "market_research" and block_reason == "missing_market_evidence":
            message = (
                "## Resumo executivo\n"
                "- Não encontrei evidência pública suficiente para sustentar uma pesquisa de mercado confiável nesta rodada.\n\n"
                "## Tabela operacional\n"
                "- A resposta gerada não trouxe citações, links ou sinais verificáveis de mercado para o item solicitado.\n\n"
                "## Próximas ações\n"
                "- Refaça a pesquisa informando marca, medida, SKU ou concorrentes desejados.\n"
                "- Se quiser, peça explicitamente fontes públicas e links na resposta."
            )
        elif block_reason == "wrong_specialized_pipeline" or response_mode in {"attachment_basket_pipeline", "dataset_basket_pipeline"}:
            message = (
                "## Resumo executivo\n"
                "- A resposta automática gerada não ficou coerente com o assunto da sua pergunta.\n\n"
                "## Tabela operacional\n"
                "- Um pipeline especializado incompatível com a intenção da consulta foi descartado por segurança.\n\n"
                "## Próximas ações\n"
                "- Reenvie a pergunta deixando explícito o objetivo principal.\n"
                "- Se quiser usar o anexo, diga isso explicitamente na pergunta."
            )
        elif expected_capability == "table":
            message = (
                "## Resumo executivo\n"
                "- Não consegui montar uma tabela confiável para este pedido nesta rodada.\n\n"
                "## Tabela operacional\n"
                "- A intenção identificada foi tabular, mas a resposta não trouxe `table_data` válido para exibição.\n\n"
                "## Próximas ações\n"
                "- Refaça a consulta informando as colunas ou recortes desejados.\n"
                "- Se preferir, peça explicitamente a tabela por produto, loja, segmento ou período."
            )
        elif expected_capability == "export":
            message = (
                "## Resumo executivo\n"
                "- Não consegui preparar uma exportação confiável para este pedido nesta rodada.\n\n"
                "## Tabela operacional\n"
                "- A resposta não trouxe artefato ou metadata válida de exportação para aprovação/download.\n\n"
                "## Próximas ações\n"
                "- Refaça o pedido informando o formato desejado, como CSV ou planilha.\n"
                "- Se a exportação depender de aprovação, peça explicitamente para gerar o arquivo exportável."
            )
        elif expected_capability == "dashboard":
            message = (
                "## Resumo executivo\n"
                "- Não consegui gerar um dashboard confiável para este pedido nesta rodada.\n\n"
                "## Tabela operacional\n"
                "- A intenção identificada foi de dashboard, mas a resposta não trouxe `dashboard_spec` válido.\n\n"
                "## Próximas ações\n"
                "- Refaça o pedido informando o objetivo do painel e os filtros desejados.\n"
                "- Se preferir, peça explicitamente um painel executivo por período, loja ou segmento."
            )
        elif expected_capability == "visualization":
            message = (
                "## Resumo executivo\n"
                "- Não consegui gerar uma visualização confiável para o pedido nesta rodada.\n\n"
                "## Tabela operacional\n"
                "- A intenção identificada foi de gráfico/dashboard, mas a resposta gerada não trouxe payload visual válido.\n\n"
                "## Próximas ações\n"
                "- Refaça a consulta informando período, métrica e recorte desejado.\n"
                "- Se preferir, peça explicitamente o tipo de gráfico esperado."
            )
        else:
            message = (
                "## Resumo executivo\n"
                "- A resposta gerada nesta rodada não passou na validação interna de coerência.\n\n"
                "## Tabela operacional\n"
                "- O sistema detectou inconsistência entre a intenção da pergunta e o tipo de resposta montada.\n\n"
                "## Próximas ações\n"
                "- Refaça a pergunta com o objetivo principal de forma direta.\n"
                "- Se houver recortes importantes, informe período, produto, loja ou fonte desejada."
            )

        return {
            "type": "text",
            "result": {"mensagem": message},
            "source": "policy.response_validation",
            "mode": "validation_block",
            "confidence": max(0.0, min(0.99, float(getattr(validation_result, "confidence", 0.0) or 0.0))),
        }

    def get_llm_status(self) -> Dict[str, Any]:
        """
        Retorna status dos provedores LLM em uso.
        """
        if hasattr(self.llm, "get_provider_status"):
            return self.llm.get_provider_status()
        raw_provider = (getattr(settings, "LLM_PROVIDER", "") or "").strip().lower()
        provider_aliases = {"grq": "groq", "gemini": "google"}
        provider = provider_aliases.get(raw_provider, raw_provider or "unknown")
        model_name = getattr(settings, "GROQ_MODEL_NAME", None) if provider == "groq" else getattr(settings, "LLM_MODEL_NAME", None)
        return {
            "primary": provider,
            "chain": [provider],
            "providers": [
                {
                    "provider": provider,
                    "available": True,
                    "model": model_name,
                    "capabilities": {"chat": True, "tools": False, "streaming": False, "json_mode": False},
                }
            ],
        }

    @staticmethod
    def _estimate_tokens(text: Optional[str]) -> int:
        """
        Estimativa simples de tokens para observabilidade operacional.
        Aproximação: ~4 chars por token.
        """
        if not text:
            return 0
        return max(1, int(len(str(text)) / 4))

    @staticmethod
    def _extract_tool_call_names(tool_calls: Any) -> list[str]:
        names: list[str] = []
        if not tool_calls:
            return names
        if isinstance(tool_calls, list):
            for tc in tool_calls:
                if isinstance(tc, str):
                    names.append(tc)
                    continue
                if isinstance(tc, dict):
                    function_obj = tc.get("function")
                    if isinstance(function_obj, dict) and function_obj.get("name"):
                        names.append(str(function_obj["name"]))
                        continue
                    if tc.get("name"):
                        names.append(str(tc["name"]))
        return names

    @staticmethod
    def _classify_query_complexity(query: str) -> str:
        q = (query or "").lower()
        complex_markers = (
            "grafico", "gráfico", "dashboard", "forecast", "previs",
            "anomalia", "outlier", "alocar", "transfer", "otimiz",
            "segmento", "categoria", "correlação", "correlacao",
        )
        if len(q) > 120 or any(marker in q for marker in complex_markers):
            return "complex"
        return "simple"
    
    async def process_message(
        self,
        query: str,
        session_id: str,
        user_id: str,
        user_role: str = "analyst",
        user_capabilities: Optional[Dict[str, bool]] = None,
        request_id: Optional[str] = None,
        on_progress: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        Processa uma mensagem usando CaculinhaBIAgent.
        
        Args:
            query: Query do usuário
            session_id: ID da sessão
            user_id: ID do usuário
            on_progress: Callback para eventos de progresso
        
        Returns:
            Dicionário com resposta (compatível com API existente)
        """
        raw_query = str(query or "")
        normalized_query = self._query_without_attachment_metadata(raw_query) or raw_query.strip()
        query = normalized_query
        logger.info(f"[DEBUG] [DEBUG] process_message INICIANDO: query='{query[:100]}...'")

        request_id = str(request_id or uuid4())
        request_started_at = time.perf_counter()
        metrics = MetricsService()
        normalized_role_for_metrics = self._normalize_role(user_role)
        complexity = self._classify_query_complexity(query)
        audit_logger = get_audit_logger()
        resolved_capabilities = user_capabilities if isinstance(user_capabilities, dict) else {}
        memory_enabled = bool(resolved_capabilities.get("memory", True))
        multimodal_enabled = bool(resolved_capabilities.get("multimodal", True))

        metrics.increment("chat_requests_total")
        metrics.increment("chat_requests_total", labels={"role": normalized_role_for_metrics})
        ab_variants = self._assign_ab_variants(user_id=user_id, session_id=session_id, request_id=request_id)
        for experiment_name, variant in ab_variants.items():
            metrics.increment("chat_ab_bucket_total", labels={"experiment": experiment_name, "variant": variant})
        trace_logger.info(
            "chat_request_started",
            request_id=request_id,
            session_id=str(session_id),
            user_id=str(user_id),
            role=normalized_role_for_metrics,
            complexity=complexity,
            query_excerpt=str(query)[:160],
            ab_variants=ab_variants,
        )

        role_limit = self._enforce_role_rate_limit(user_id=user_id, normalized_role=normalized_role_for_metrics)
        if role_limit is not None:
            metrics.increment("chat_rate_limited_total")
            metrics.increment("chat_rate_limited_total", labels={"role": normalized_role_for_metrics})
            audit_logger.log_action(
                action=AuditAction.CHAT_MESSAGE,
                user_id=str(user_id),
                details={
                    "request_id": request_id,
                    "session_id": session_id,
                    "role": normalized_role_for_metrics,
                    "status": "rate_limited",
                    "limit_per_minute": role_limit,
                    "query_excerpt": str(query)[:240],
                },
                success=False,
                error_message="rate_limit_exceeded",
            )
            return {
                "type": "text",
                "result": {
                    "mensagem": (
                        f"Limite de solicitações excedido para seu perfil ({role_limit}/min). "
                        "Aguarde alguns segundos e tente novamente."
                    )
                },
                "request_id": request_id,
            }

        try:
            # Callback helper
            # Callback helper
            async def emit_progress(arg1: Union[str, Dict[str, Any]], arg2: Optional[str] = None):
                if isinstance(arg1, dict):
                    trace_logger.info(
                        "chat_tool_progress",
                        request_id=request_id,
                        session_id=str(session_id),
                        user_id=str(user_id),
                        event_type=str(arg1.get("type") or "unknown"),
                        tool=str(arg1.get("tool") or ""),
                        status=str(arg1.get("status") or ""),
                    )
                else:
                    trace_logger.info(
                        "chat_tool_progress",
                        request_id=request_id,
                        session_id=str(session_id),
                        user_id=str(user_id),
                        event_type="tool_progress",
                        tool=str(arg1 or ""),
                        status=str(arg2 or ""),
                    )
                if on_progress:
                    if isinstance(arg1, dict):
                        # Chamada do Agente (já é o evento completo)
                        await on_progress(arg1)
                    else:
                        tool_map = {
                            "Analisando pergunta": "system.thinking",
                            "Pensando": "system.thinking",
                            "Processando resposta": "system.finalizing",
                            "consultar_dados_flexivel": "tool.data_query",
                            "consultar_dados_gerais": "tool.metadata_query",
                            "gerar_grafico_universal": "tool.chart",
                            "gerar_grafico_universal_v2": "tool.chart",
                            "pesquisar_precos_concorrentes": "tool.competitive_research",
                            "pesquisar_mercado_web": "tool.market_research",
                        }
                        status_map = {
                            "start": "start",
                            "executing": "executing",
                            "processing": "finishing",
                            "done": "finishing",
                            "finishing": "finishing",
                        }
                        # Chamada interna (tool, status)
                        await on_progress({
                            "type": "tool_progress",
                            "tool": tool_map.get(str(arg1), f"tool.{str(arg1 or 'generic')}"),
                            "status": status_map.get(str(arg2 or "").lower(), "executing")
                        })
            
            role = normalized_role_for_metrics
            agent = self._get_agent_for_role(role)
            logger.info(f"[DEBUG] [DEBUG] Agente disponível para role '{role}': {agent is not None}")

            computer_use_enabled = bool(resolved_capabilities.get("computer_use", False))
            image_generation_query = self._is_image_generation_query(query)
            automation_actor = SimpleNamespace(
                id=user_id,
                role=user_role,
                username=str(user_id),
                email="",
            )
            agent_response = None
            if image_generation_query and not multimodal_enabled:
                agent_response = {
                    "response": "Recursos multimodais não estão habilitados para o seu perfil no momento.",
                    "source": "policy.capability.multimodal",
                    "confidence": 0.93,
                    "mode": "policy_block",
                }
                logger.info("[DEBUG] [DEBUG] Geração de imagem bloqueada por capability multimodal.")
            elif image_generation_query:
                image_asset = await self.image_generation_service.generate_image(query)
                agent_response = {
                    "response": "Imagem conceitual gerada com base no seu pedido.",
                    "image_asset": image_asset,
                    "source": "image_generation.local_svg",
                    "confidence": 0.79,
                    "mode": "image_generation",
                }
                logger.info("[DEBUG] [DEBUG] Resposta visual gerada localmente para prompt de imagem.")
            elif self.chat_automation_service.detect_automation_intent(query):
                if not computer_use_enabled:
                    agent_response = self.chat_automation_service.build_capability_block_response()
                else:
                    agent_response = self.chat_automation_service.build_proposal_response(
                        query=query,
                        request_id=request_id,
                        session_id=session_id,
                        current_user=automation_actor,
                    )
            await emit_progress("Analisando pergunta", "start")
            document_context: list[Dict[str, Any]] = []
            if agent_response is None:
                # 1. Obter histórico
                chat_history = self.session_manager.get_history(session_id, user_id) if memory_enabled else []
                 
                # 2. Preparar contexto do usuário (RLS, etc)
                user_filters = self._get_user_filters(user_id)
                user_preferences = await self._load_user_preferences(user_id) if memory_enabled else {}
                user_context = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "filters": user_filters,
                    "preferences": user_preferences,
                    "ab_variants": ab_variants,
                    "capabilities": {
                        "memory": memory_enabled,
                        "multimodal": multimodal_enabled,
                        "computer_use": computer_use_enabled,
                    },
                }
                
                # 3. Executar agente
                agent_history = self._convert_history_format(chat_history)
                logger.info(f"[DEBUG] [DEBUG] Histórico convertido: {len(agent_history)} mensagens")
                system_messages: list[Dict[str, str]] = []
                preference_system_message = self._preferences_to_system_message(user_preferences)
                if preference_system_message:
                    system_messages.append(preference_system_message)
                document_context = await self._retrieve_document_context(
                    query=query,
                    user_id=user_id,
                    session_id=session_id,
                    tenant_id="default",
                )
                agent_response = self._run_attachment_basket_pipeline(query, document_context)
                if agent_response is not None and not self._response_matches_query_intent(query, agent_response):
                    logger.info(
                        "[DEBUG] Pipeline de cesta por anexo descartado por incompatibilidade com a intencao da pergunta: %s",
                        agent_response.get("source"),
                    )
                    agent_response = None
                if agent_response is not None:
                    logger.info(
                        "[DEBUG] Pipeline deterministico de cestas acionado com anexos da sessao: %s",
                        agent_response.get("source"),
                    )
                if agent_response is None:
                    agent_response = self._run_dataset_basket_pipeline(query)
                    if agent_response is not None and not self._response_matches_query_intent(query, agent_response):
                        logger.info(
                            "[DEBUG] Pipeline analitico de basket descartado por incompatibilidade com a intencao da pergunta: %s",
                            agent_response.get("source"),
                        )
                        agent_response = None
                    if agent_response is not None:
                        logger.info(
                            "[DEBUG] Pipeline analitico de basket acionado na base local: %s",
                            agent_response.get("source"),
                        )
                document_system_message = self._documents_to_system_message(document_context)
                if agent_response is None and document_system_message:
                    system_messages.append(document_system_message)
                retrieved_memory = await self._retrieve_cross_session_memory(
                    query=query,
                    session_id=session_id,
                    user_id=user_id,
                ) if memory_enabled else []
                memory_system_message = self._memory_entries_to_system_message(retrieved_memory)
                if agent_response is None and memory_system_message:
                    system_messages.append(memory_system_message)
                if agent_response is None and system_messages:
                    agent_history = [*system_messages, *agent_history]
                if agent_response is None and memory_system_message:
                    logger.info(
                        "[DEBUG] Contexto adicional de memória aplicado ao agente: %s entradas",
                        len(retrieved_memory),
                    )

                if agent_response is None:
                    # Executar agente de forma assíncrona
                    logger.info(f"[DEBUG] [DEBUG] Chamando agent.run_async()...")

                    # FIX: run_async é nativamente async, não usar threads para ele
                    agent_response = await agent.run_async(
                        query,
                        agent_history, # Pass converted history directly
                        on_progress=emit_progress # Pass progress callback if supported
                    )
                    logger.info(f"[DEBUG] [DEBUG] agent.run_async() RETORNOU: {type(agent_response)}")
                    logger.info(f"[DEBUG] [DEBUG] Resposta do agente: {str(agent_response)[:200]}...")
                    capability_recovery = await self._attempt_capability_recovery(
                        query=query,
                        chat_history=agent_history,
                        agent=agent,
                        current_response=agent_response if isinstance(agent_response, dict) else {},
                        on_progress=emit_progress,
                    )
                    if capability_recovery is not None:
                        logger.info(
                            "[DEBUG] Recuperação orientada à capability acionada com sucesso: %s",
                            capability_recovery.get("source"),
                        )
                        agent_response = capability_recovery
            
            # TRAP: Se for coroutine, logar erro critico
            if asyncio.iscoroutine(agent_response):
                logger.error("[ERROR] CRITICAL: agent_response IS A COROUTINE! Force awaiting it...")
                agent_response = await agent_response
                logger.info("[OK] Recovered from coroutine state.")
            
            await emit_progress("Analisando pergunta", "done")
            
            # 4. Processar resposta do agente
            response = self._process_agent_response(agent_response, query=query, user_role=user_role)
            response["request_id"] = request_id
            response["ab_variants"] = ab_variants
            existing_citations = response.get("citations")
            if existing_citations in (None, "", []):
                internal_meta = response.get("_internal_meta", {}) if isinstance(response.get("_internal_meta"), dict) else {}
                existing_citations = internal_meta.get("citations")
            if document_context and existing_citations in (None, "", []):
                internal_meta = response.get("_internal_meta", {}) if isinstance(response.get("_internal_meta"), dict) else {}
                resolved_source = response.get("source") or internal_meta.get("source") or "rag.internal_documents"
                resolved_confidence = response.get("confidence")
                if resolved_confidence is None:
                    resolved_confidence = internal_meta.get("confidence")
                if resolved_confidence is None:
                    resolved_confidence = 0.76
                response["source"] = resolved_source
                response["confidence"] = float(resolved_confidence)
                response["citations"] = self._documents_to_citations(document_context)
                if "source" not in internal_meta:
                    internal_meta["source"] = response["source"]
                if "confidence" not in internal_meta:
                    internal_meta["confidence"] = response["confidence"]
                internal_meta["citations"] = response["citations"]
                response["_internal_meta"] = internal_meta

            # Métricas de tool usage/tokens/custo aproximado
            tool_names = self._extract_response_tools(response)
            if tool_names:
                metrics.increment("chat_tool_calls_total", value=len(tool_names))
                for tool_name in tool_names:
                    metrics.increment("chat_tool_calls_total", labels={"tool": tool_name})

            response_text = response.get("result", {}).get("mensagem", "")
            tokens_in = self._estimate_tokens(query)
            tokens_out = self._estimate_tokens(response_text)
            latency_seconds = max(0.0, time.perf_counter() - request_started_at)
            response["latency_seconds"] = latency_seconds

            # 5. Salvar no histórico
            assistant_metadata = self.build_session_message_metadata(
                query=query,
                response=response,
                role="assistant",
                request_id=request_id,
            )
            if memory_enabled:
                user_metadata = self.build_session_message_metadata(query=query, role="user", request_id=request_id)
                self.session_manager.add_message(session_id, "user", query, user_id, metadata=user_metadata)
                self.session_manager.add_message(
                    session_id, 
                    "assistant", 
                    response_text, 
                    user_id,
                    metadata=assistant_metadata,
                )
                trace_logger.info(
                    "chat_async_job_started",
                    request_id=request_id,
                    session_id=str(session_id),
                    user_id=str(user_id),
                    job_name="conversation_memory_index",
                    entry_count=2,
                )
                try:
                    await self._index_memory_message(
                        session_id,
                        user_id,
                        {"role": "user", "content": query, "id": request_id, "metadata": user_metadata},
                    )
                    await self._index_memory_message(
                        session_id,
                        user_id,
                        {"role": "assistant", "content": response_text, "id": request_id, "metadata": assistant_metadata},
                    )
                    self._memory_indexed_sessions.add(session_id)
                    trace_logger.info(
                        "chat_async_job_completed",
                        request_id=request_id,
                        session_id=str(session_id),
                        user_id=str(user_id),
                        job_name="conversation_memory_index",
                        entry_count=2,
                    )
                except Exception as exc:
                    logger.warning("Falha ao atualizar índice de memória conversacional: %s", exc)
                    trace_logger.warning(
                        "chat_async_job_failed",
                        request_id=request_id,
                        session_id=str(session_id),
                        user_id=str(user_id),
                        job_name="conversation_memory_index",
                        error=str(exc),
                    )

            self._capture_learning_example(
                query=query,
                user_id=user_id,
                response=response,
                assistant_text=response_text,
                assistant_metadata=assistant_metadata,
            )

            metrics.increment("chat_tokens_in_total", value=tokens_in)
            metrics.increment("chat_tokens_out_total", value=tokens_out)
            metrics.increment("chat_tokens_total", value=tokens_in + tokens_out)

            metrics.observe("chat_latency_seconds", latency_seconds)
            metrics.observe("chat_latency_seconds", latency_seconds, labels={"complexity": complexity})
            metrics.observe("agent_execution_seconds", latency_seconds)

            self._record_semantic_quality_metrics(
                metrics=metrics,
                query=query,
                processed_response=response,
                normalized_role=normalized_role_for_metrics,
            )

            validation_context = self._build_response_validation_context(query, response)
            validation_result = validate_response(
                response,
                query=query,
                context=validation_context,
            )
            metrics.increment("response_validation_total")
            if not validation_result.is_valid:
                metrics.increment("response_validation_failures_total")
            if getattr(validation_result, "should_block", False):
                metrics.increment("response_validation_blocks_total")
                trace_logger.warning(
                    "chat_response_blocked_by_validator",
                    request_id=request_id,
                    session_id=str(session_id),
                    user_id=str(user_id),
                    expected_capability=validation_context.get("expected_capability"),
                    actual_capability=validation_context.get("actual_capability"),
                    block_reason=getattr(validation_result, "block_reason", None),
                    issues=getattr(validation_result, "issues", []),
                )
                response = self._build_validation_block_response(
                    query=query,
                    validation_result=validation_result,
                    validation_context=validation_context,
                )

            internal_meta = response.get("_internal_meta", {}) if isinstance(response.get("_internal_meta"), dict) else {}
            source_value = response.get("source") or internal_meta.get("source")
            mode_value = response.get("mode") or internal_meta.get("mode")
            confidence_value = response.get("confidence")
            if confidence_value is None:
                confidence_value = internal_meta.get("confidence")
            citations_value = response.get("citations")
            if citations_value in (None, "", []):
                citations_value = internal_meta.get("citations")
            citations_value = sanitize_citations(citations_value)
            if tool_names:
                trace_logger.info(
                    "chat_tool_trace",
                    request_id=request_id,
                    session_id=str(session_id),
                    user_id=str(user_id),
                    tool_names=tool_names,
                    tool_count=len(tool_names),
                    source=source_value,
                    mode=mode_value,
                )

            audit_logger.log_action(
                action=AuditAction.CHAT_MESSAGE,
                user_id=str(user_id),
                details={
                    "request_id": request_id,
                    "session_id": session_id,
                    "role": normalized_role_for_metrics,
                    "query_excerpt": str(query)[:240],
                    "response_type": response.get("type"),
                    "source": source_value,
                    "mode": mode_value,
                    "confidence": confidence_value,
                    "tools": tool_names,
                    "latency_ms": round(latency_seconds * 1000, 2),
                    "citations_count": len(citations_value or []) if isinstance(citations_value, list) else 0,
                    "ab_variants": ab_variants,
                },
                success=True,
            )

            # Materializa metadados públicos para o frontend antes de remover a estrutura interna.
            if source_value not in (None, "", []):
                response["source"] = source_value
            if confidence_value not in (None, "", []):
                response["confidence"] = confidence_value
            if mode_value not in (None, "", []):
                response["mode"] = mode_value
            if isinstance(citations_value, list) and citations_value:
                response["citations"] = citations_value

            # Não expor metadados internos no payload final do usuário.
            response.pop("_internal_meta", None)

            trace_logger.info(
                "chat_request_finished",
                request_id=request_id,
                session_id=str(session_id),
                user_id=str(user_id),
                response_type=str(response.get("type") or "text"),
                source=source_value,
                mode=mode_value,
                latency_ms=round(latency_seconds * 1000, 2),
                citations_count=len(citations_value or []) if isinstance(citations_value, list) else 0,
                has_image=bool(response.get("image_asset")),
                has_audio=bool(response.get("audio_asset")),
            )
            logger.info(f"[AGENT] Resposta gerada com sucesso")
            return response
             
        except Exception as e:
            metrics.increment("chat_errors_total")
            metrics.increment("chat_errors_total", labels={"role": normalized_role_for_metrics})
            latency_seconds = max(0.0, time.perf_counter() - request_started_at)
            metrics.observe("chat_latency_seconds", latency_seconds)
            metrics.observe("chat_latency_seconds", latency_seconds, labels={"complexity": complexity})
            audit_logger.log_action(
                action=AuditAction.CHAT_MESSAGE,
                user_id=str(user_id),
                details={
                    "request_id": request_id,
                    "session_id": session_id,
                    "role": normalized_role_for_metrics,
                    "query_excerpt": str(query)[:240],
                    "status": "error",
                    "latency_ms": round(latency_seconds * 1000, 2),
                },
                success=False,
                error_message=str(e),
            )
            trace_logger.error(
                "chat_request_failed",
                request_id=request_id,
                session_id=str(session_id),
                user_id=str(user_id),
                role=normalized_role_for_metrics,
                complexity=complexity,
                latency_ms=round(latency_seconds * 1000, 2),
                error=str(e),
            )
            logger.error(f"Erro em process_message: {e}", exc_info=True)
            return {
                "type": "text",
                "result": {"mensagem": f"Erro ao processar: {str(e)}"},
                "request_id": request_id,
            }

    def _capture_learning_example(
        self,
        *,
        query: str,
        user_id: str,
        response: Dict[str, Any],
        assistant_text: str,
        assistant_metadata: Dict[str, Any],
    ) -> None:
        try:
            payload = build_chat_example_payload(
                query=query,
                user_id=user_id,
                response=response,
                assistant_text=assistant_text,
                assistant_metadata=assistant_metadata,
            )
            if payload is None:
                return
            inserted = self.example_collector.add_example(**payload)
            if inserted:
                build_default_unified_learning_dataset()
        except Exception as exc:
            logger.warning("Falha ao capturar exemplo real do chat: %s", exc, exc_info=True)

    def _get_agent_for_role(self, role: str) -> CaculinhaBIAgent:
        """Retorna (ou cria) um agente com escopo de ferramentas por role."""
        if role in self._agents_by_role:
            return self._agents_by_role[role]

        logger.info(f"[DEBUG] Criando agente para role dinâmica: {role}")
        scoped_agent = CaculinhaBIAgent(
            llm=self.llm,
            code_gen_agent=self.code_gen_agent,
            field_mapper=self.field_mapper,
            user_role=role,
            enable_rag=True
        )
        self._agents_by_role[role] = scoped_agent
        return scoped_agent

    def _normalize_role(self, user_role: Optional[str]) -> str:
        """
        Normaliza papel do usuário para escopo de ferramentas do agente.
        Mantém experiência funcional do chat para perfis de negócio.
        """
        role = (user_role or "analyst").strip().lower()
        role_map = {
            "admin": "admin",
            "analyst": "analyst",
            # Hardening: perfil "user" opera com escopo restrito de ferramentas (viewer).
            "user": "viewer",
            "compras": "analyst",
            "coordenador": "analyst",
            "coordinator": "analyst",
            "gerente": "analyst",
            "manager": "analyst",
            "viewer": "viewer",
            "guest": "guest",
        }
        normalized = role_map.get(role, "analyst")
        if normalized != role:
            logger.info(f"[DEBUG] Role normalizada para escopo do chat: '{role}' -> '{normalized}'")
        return normalized
    
    def _convert_history_format(self, chat_history: list) -> list:
        """
        Converte histórico do SessionManager para formato esperado pelo agente.
        
        SessionManager format: [{"role": "user/assistant", "content": str, ...}]
        Agent format: [{"role": "user/assistant", "content": str, "metadata": {...}}]
        """
        converted = []
        for msg in chat_history:
            normalized = {
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            }
            metadata = msg.get("metadata")
            if isinstance(metadata, dict) and metadata:
                normalized["metadata"] = metadata
            converted.append(normalized)
        return converted

    def _extract_breakdown_from_text(self, text: str) -> Optional[str]:
        content = str(text or "")
        if not content.strip():
            return None

        header_lines = [line.strip().lower() for line in content.splitlines() if line.strip().startswith("|")]
        header = header_lines[0] if header_lines else content.lower()

        if "loja (une)" in header or re.search(r"\|\s*une\s*\|", header):
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

    def _extract_market_product_hint(self, query: str) -> Optional[str]:
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

    def _extract_market_competitors(self, query: str) -> Optional[list[str]]:
        q = (query or "").lower()
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
        found: list[str] = []
        for canonical, aliases in mappings:
            if any(alias in q for alias in aliases) and canonical not in found:
                found.append(canonical)
        return found or None

    def _extract_response_breakdown(self, response: Optional[Dict[str, Any]]) -> Optional[str]:
        if not isinstance(response, dict):
            return None

        dashboard_spec = response.get("dashboard_spec")
        if isinstance(dashboard_spec, dict):
            widgets = dashboard_spec.get("widgets")
            if isinstance(widgets, list):
                for widget in widgets:
                    if not isinstance(widget, dict):
                        continue
                    title = str(widget.get("title") or "")
                    inferred = self._extract_breakdown_from_text(title)
                    if inferred:
                        return inferred
                    rows = widget.get("rows")
                    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
                        header = "| " + " | ".join(str(k) for k in rows[0].keys()) + " |"
                        inferred = self._extract_breakdown_from_text(header)
                        if inferred:
                            return inferred

        result_payload = response.get("result", {})
        if isinstance(result_payload, dict):
            inferred = self._extract_breakdown_from_text(str(result_payload.get("mensagem") or ""))
            if inferred:
                return inferred
        return self._extract_breakdown_from_text(str(response.get("response") or response.get("mensagem") or ""))

    def build_session_message_metadata(
        self,
        query: str,
        response: Optional[Dict[str, Any]] = None,
        role: str = "assistant",
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        from backend.app.core.utils.query_router import (
            extract_chart_breakdown,
            extract_period_filter,
            extract_product_code,
            extract_segment_filter,
            extract_une_filter,
            is_all_stores_scope,
        )

        context: Dict[str, Any] = {
            "query_breakdown": extract_chart_breakdown(query),
            "period": extract_period_filter(query),
            "product_code": extract_product_code(query),
            "segment": extract_segment_filter(query),
            "une": extract_une_filter(query),
            "scope_all_stores": is_all_stores_scope(query),
        }
        market_product_hint = self._extract_market_product_hint(query)
        if market_product_hint:
            context["market_product_hint"] = market_product_hint
        market_competitors = self._extract_market_competitors(query)
        if market_competitors:
            context["market_competitors"] = market_competitors

        metadata: Dict[str, Any] = {"role_kind": role, "context": context}
        resolved_request_id = request_id
        if resolved_request_id in (None, "", []) and isinstance(response, dict):
            response_request_id = response.get("request_id")
            if response_request_id not in (None, "", []):
                resolved_request_id = str(response_request_id)
        if resolved_request_id not in (None, "", []):
            metadata["request_id"] = str(resolved_request_id)
            context["request_id"] = str(resolved_request_id)
        if not isinstance(response, dict):
            return metadata

        response_type = str(response.get("type") or "text")
        context["response_type"] = response_type
        context["has_chart"] = bool(response.get("chart_data") or response.get("chart_spec"))
        context["has_dashboard"] = bool(response.get("dashboard_spec"))
        context["has_image"] = bool(response.get("image_asset"))
        context["has_audio"] = bool(response.get("audio_asset"))
        context["has_automation"] = bool(response.get("automation_request"))

        dashboard_spec = response.get("dashboard_spec")
        if isinstance(dashboard_spec, dict):
            filters = dashboard_spec.get("filters")
            if isinstance(filters, dict) and filters:
                context["dashboard_filters"] = {
                    str(k): v for k, v in filters.items() if v not in (None, "", [])
                }
            title = str(dashboard_spec.get("title") or "").strip()
            if title:
                context["dashboard_title"] = title

        response_breakdown = self._extract_response_breakdown(response)
        if response_breakdown:
            context["response_breakdown"] = response_breakdown

        internal_meta = response.get("_internal_meta")
        if isinstance(internal_meta, dict):
            for key in ("source", "confidence", "mode"):
                if internal_meta.get(key) not in (None, "", []):
                    metadata[key] = internal_meta.get(key)
                    if key == "source":
                        context["source"] = internal_meta.get(key)

        if "source" not in context and response.get("source") not in (None, "", []):
            context["source"] = response.get("source")

        citations = response.get("citations")
        if citations in (None, "", []):
            citations = internal_meta.get("citations") if isinstance(internal_meta, dict) else None
        citations = sanitize_citations(citations)
        if isinstance(citations, list) and citations:
            metadata["citations"] = citations

        ab_variants = response.get("ab_variants")
        if isinstance(ab_variants, dict) and ab_variants:
            metadata["ab_variants"] = {
                str(key): str(value)
                for key, value in ab_variants.items()
                if value not in (None, "", [])
            }

        tool_calls = response.get("tool_calls")
        if isinstance(tool_calls, list) and tool_calls:
            tool_names: list[str] = []
            for tool_call in tool_calls:
                if not isinstance(tool_call, dict):
                    continue
                function_payload = tool_call.get("function") if isinstance(tool_call.get("function"), dict) else {}
                tool_name = str(function_payload.get("name") or tool_call.get("name") or "").strip()
                if tool_name:
                    tool_names.append(tool_name)
            if tool_names:
                metadata["tool_names"] = tool_names
                metadata["tool_call_count"] = len(tool_names)
                context["tool_call_count"] = len(tool_names)

        latency_seconds = response.get("latency_seconds")
        if isinstance(latency_seconds, (int, float)):
            metadata["latency_seconds"] = round(float(latency_seconds), 6)
            context["latency_ms"] = round(float(latency_seconds) * 1000.0, 2)

        chart_spec = response.get("chart_data")
        if chart_spec in (None, "", {}):
            chart_spec = response.get("chart_spec")
        if isinstance(chart_spec, str):
            try:
                chart_spec = json.loads(chart_spec)
            except (TypeError, json.JSONDecodeError):
                chart_spec = None

        table_data = response.get("table_data")
        image_asset = response.get("image_asset")
        audio_asset = response.get("audio_asset")
        ui_payload: Dict[str, Any] = {"type": response_type}
        if isinstance(chart_spec, dict):
            ui_payload["chart_spec"] = chart_spec
            if response_type == "text":
                ui_payload["type"] = "chart"
        if isinstance(table_data, list) and table_data:
            ui_payload["data"] = table_data
            if response_type == "text":
                ui_payload["type"] = "table"
        if isinstance(dashboard_spec, dict):
            ui_payload["dashboard_spec"] = dashboard_spec
            ui_payload["type"] = "dashboard"
        if isinstance(image_asset, dict) and image_asset.get("url") not in (None, "", []):
            ui_payload["image_asset"] = image_asset
            if response_type == "text":
                ui_payload["type"] = "image"
        if isinstance(audio_asset, dict) and audio_asset.get("url") not in (None, "", []):
            ui_payload["audio_asset"] = audio_asset
            if response_type == "text" and "image_asset" not in ui_payload:
                ui_payload["type"] = "audio"
        automation_request = response.get("automation_request")
        if isinstance(automation_request, dict) and automation_request:
            ui_payload["automation_request"] = automation_request
        if metadata.get("request_id") not in (None, "", []):
            ui_payload["request_id"] = metadata["request_id"]
        for key in ("source", "confidence", "mode"):
            if metadata.get(key) not in (None, "", []):
                ui_payload[key] = metadata.get(key)
        if isinstance(citations, list) and citations:
            ui_payload["citations"] = citations
        if len(ui_payload) > 1:
            metadata["ui_payload"] = ui_payload
        return metadata
    
    def _is_internal_data_restricted_role(self, user_role: Optional[str]) -> bool:
        """
        Perfis com menor privilégio não devem receber detalhamento técnico/operacional interno.
        """
        role = (user_role or "analyst").strip().lower()
        return role in {"user", "viewer", "guest"}

    def _sanitize_executive_output_for_role(self, text: str, user_role: Optional[str]) -> str:
        """
        Remove blocos técnicos e detalhamento interno da mensagem final.
        """
        if not isinstance(text, str) or not text.strip():
            return text

        cleaned = text

        # Remove linha de template interno quando existir.
        cleaned = re.sub(r"(?im)^\s*-\s*Template oficial:.*$", "", cleaned)

        # Remove blocos técnicos e de auditoria (não devem aparecer para usuário final).
        cleaned = re.sub(
            r"(?ims)^\s*##\s*SQL/Python\s*\n.*?(?=^\s*##\s+|\Z)",
            "",
            cleaned,
        )
        cleaned = re.sub(
            r"(?ims)^\s*##\s*Recorte e evid[êe]ncia\s*\n.*?(?=^\s*##\s+|\Z)",
            "",
            cleaned,
        )

        # Remove metadados técnicos caso tenham sido injetados no texto.
        cleaned = re.sub(r"(?im)^\s*Fonte:\s*.*$", "", cleaned)
        cleaned = re.sub(r"(?im)^\s*Confianca:\s*.*$", "", cleaned)
        cleaned = re.sub(r"(?im)^\s*Confiança:\s*.*$", "", cleaned)
        cleaned = re.sub(r"(?im)^\s*Citacoes:\s*.*$", "", cleaned)
        cleaned = re.sub(r"(?im)^\s*Citações:\s*.*$", "", cleaned)

        # Padroniza heading de ação para o formato atual.
        cleaned = re.sub(r"(?im)^\s*##\s*(Ação recomendada|Acao recomendada)\s*$", "## Próximas ações", cleaned)

        # Remove placeholders sem valor analítico na tabela.
        cleaned = re.sub(
            r"(?im)^\s*\|\s*Status\s*\|\s*Dados retornados sem tabela estruturada nesta rodada\s*\|\s*$",
            "| Status | Sem dados tabulares adicionais para exibir nesta resposta |",
            cleaned,
        )

        # Perfis restritos ainda ocultam detalhamento por loja/UNE.
        if self._is_internal_data_restricted_role(user_role):
            table_pattern = r"(?ims)^(\s*##\s*Tabela operacional\s*\n)(.*?)(?=^\s*##\s+|\Z)"
            table_match = re.search(table_pattern, cleaned)
            if table_match:
                table_body = table_match.group(2)
                if re.search(r"(?i)\bUNE\b|Loja\s*\(UNE\)", table_body):
                    cleaned = re.sub(
                        table_pattern,
                        "## Tabela operacional\n- Detalhamento por loja/UNE restrito para este perfil.\n\n",
                        cleaned,
                    )

            # Evita exposição de identificador específico de UNE no resumo.
            cleaned = re.sub(r"(?i)UNE\s+l[ií]der:\s*\d+", "UNE lider: [restrito]", cleaned)

        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        return cleaned

    def _process_agent_response(self, agent_response: Dict[str, Any], query: str = "", user_role: str = "analyst") -> Dict[str, Any]:
        """
        Converte resposta do agente para formato esperado pela API.
        
        Agent response format:
        {
            "response": str,
            "tool_calls": [...],
            "chart_data": {...} (opcional)
        }
        
        API expected format:
        {
            "type": "text",
            "result": {"mensagem": str},
            "chart_data": {...} (opcional)
        }
        """
        logger.info(f"[DEBUG] [DEBUG] _process_agent_response INPUT: {str(agent_response)[:500]}...")
        
        # FIX 2026-01-27: Extração robusta de response_text com múltiplos fallbacks
        response_text = None
        
        # Tentativa 1: Chave "response" (formato padrão do agente)
        if "response" in agent_response and agent_response["response"]:
            response_text = agent_response["response"]
            logger.info(f"[DEBUG] [DEBUG] response_text extraído de 'response': {response_text[:100]}...")
        
        # Tentativa 2: Chave "text_override"
        elif "text_override" in agent_response and agent_response["text_override"]:
            response_text = agent_response["text_override"]
            logger.info(f"[DEBUG] [DEBUG] response_text extraído de 'text_override': {response_text[:100]}...")
        
        # Tentativa 3: Chave "result" (se for string)
        elif "result" in agent_response:
            result_data = agent_response["result"]
            if isinstance(result_data, str) and result_data:
                response_text = result_data
                logger.info(f"[DEBUG] [DEBUG] response_text extraído de 'result' (string): {response_text[:100]}...")
            elif isinstance(result_data, dict) and "mensagem" in result_data:
                response_text = result_data["mensagem"]
                logger.info(f"[DEBUG] [DEBUG] response_text extraído de 'result.mensagem': {response_text[:100]}...")
        
        # Tentativa 4: Chave "mensagem" direta
        elif "mensagem" in agent_response and agent_response["mensagem"]:
            response_text = agent_response["mensagem"]
            logger.info(f"[DEBUG] [DEBUG] response_text extraído de 'mensagem': {response_text[:100]}...")
        
        # Fallback final: Se ainda vazio, usar mensagem padrão
        if not response_text or (isinstance(response_text, str) and not response_text.strip()):
            logger.warning(f"[WARNING] [DEBUG] response_text VAZIO! agent_response keys: {agent_response.keys()}")
            response_text = "Desculpe, não consegui gerar uma resposta adequada. Por favor, reformule sua pergunta."
            
        result_data_payload = agent_response.get("result", {})
        if not isinstance(result_data_payload, dict):
            result_data_payload = {}

        # Dashboard estruturado não recebe wrapping executivo textual adicional.
        is_dashboard_payload = bool(agent_response.get("dashboard_spec"))

        table_data = agent_response.get("table_data")
        if not table_data:
            table_data = result_data_payload.get("table_data")

        structured_sales_report = None
        if isinstance(response_text, str) and response_text.strip() and not is_dashboard_payload and isinstance(table_data, list) and table_data:
            structured_sales_report = build_sales_dimension_report_from_rows(query=query, rows=table_data)
        if structured_sales_report:
            response_text = structured_sales_report
        elif isinstance(response_text, str) and response_text.strip() and not is_dashboard_payload:
            response_text = ensure_executive_output(query=query, message=response_text)
        response_text = self._sanitize_executive_output_for_role(response_text, user_role=user_role)

        # Handle chart data keys
        chart_data = agent_response.get("chart_data")
        if not chart_data:
            chart_data = agent_response.get("chart_spec")

        dashboard_spec = agent_response.get("dashboard_spec")
        if not dashboard_spec:
            dashboard_spec = result_data_payload.get("dashboard_spec")

        image_asset = agent_response.get("image_asset")
        if image_asset in (None, "", {}):
            image_asset = result_data_payload.get("image_asset")

        audio_asset = agent_response.get("audio_asset")
        if audio_asset in (None, "", {}):
            audio_asset = result_data_payload.get("audio_asset")
        automation_request = agent_response.get("automation_request")
        if automation_request in (None, "", {}):
            automation_request = result_data_payload.get("automation_request")
        
        if chart_data:
            logger.info(f"[DEBUG] [DEBUG] chart_data encontrado: {str(chart_data)[:200]}...")
        if dashboard_spec:
            logger.info("[DEBUG] [DEBUG] dashboard_spec encontrado para renderizacao no frontend")
        
        result = {
            "type": "dashboard" if dashboard_spec else "text",
            "result": {
                "mensagem": response_text
            }
        }
        
        # Adicionar chart_data se existir
        if chart_data:
            result["chart_data"] = chart_data

        if dashboard_spec:
            result["dashboard_spec"] = dashboard_spec

        if isinstance(table_data, list) and table_data:
            result["table_data"] = table_data

        if isinstance(image_asset, dict) and image_asset.get("url") not in (None, "", []):
            result["image_asset"] = image_asset

        if isinstance(audio_asset, dict) and audio_asset.get("url") not in (None, "", []):
            result["audio_asset"] = audio_asset

        if isinstance(automation_request, dict) and automation_request:
            result["automation_request"] = automation_request

        internal_meta: Dict[str, Any] = {}
        for field in ("source", "confidence", "citations", "mode"):
            field_value = agent_response.get(field)
            if field_value in (None, "", []):
                field_value = result_data_payload.get(field)
            if field_value not in (None, "", []):
                internal_meta[field] = field_value
        if internal_meta:
            result["_internal_meta"] = internal_meta

        tool_calls = agent_response.get("tool_calls")
        if tool_calls in (None, "", []):
            tool_calls = result_data_payload.get("tool_calls")
        if tool_calls not in (None, "", []):
            result["tool_calls"] = tool_calls
        
        logger.info(f"[DEBUG] [DEBUG] _process_agent_response OUTPUT: {str(result)[:500]}...")
        return result
    
    def _get_user_filters(self, user_id: str) -> Dict[str, Any]:
        """
        Obtém filtros efetivos do usuário para RLS com base no contexto autenticado.
        """
        try:
            from backend.app.core.context import get_current_user_context

            current_user = get_current_user_context()
            if current_user is None:
                try:
                    from app.core.context import get_current_user_context as get_legacy_user_context
                    current_user = get_legacy_user_context()
                except Exception:
                    current_user = None
            if current_user is None:
                return {}

            current_user_id = str(getattr(current_user, "id", "") or "")
            requested_user_id = str(user_id or "")
            if current_user_id and requested_user_id and current_user_id != requested_user_id:
                logger.warning(
                    "[RLS] Context user_id diverge do request user_id. context=%s request=%s",
                    current_user_id,
                    requested_user_id,
                )

            role = str(getattr(current_user, "role", "") or "").strip().lower()
            segments: list[str] = []

            if hasattr(current_user, "segments_list"):
                raw_segments = getattr(current_user, "segments_list") or []
                if isinstance(raw_segments, list):
                    segments = [str(s) for s in raw_segments if str(s).strip()]

            if not segments:
                raw_allowed = getattr(current_user, "allowed_segments", None)
                if isinstance(raw_allowed, str):
                    import json
                    try:
                        parsed = json.loads(raw_allowed)
                        if isinstance(parsed, list):
                            segments = [str(s) for s in parsed if str(s).strip()]
                    except (json.JSONDecodeError, TypeError):
                        segments = []
                elif isinstance(raw_allowed, list):
                    segments = [str(s) for s in raw_allowed if str(s).strip()]

            if role == "admin" or "*" in segments:
                return {"segments": ["*"], "rls_applied": False}

            if segments:
                return {"segments": segments, "rls_applied": True}

            return {}

        except Exception as exc:
            logger.warning(f"[RLS] Falha ao obter filtros do usuário: {exc}")
            return {}
