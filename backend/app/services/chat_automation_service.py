from __future__ import annotations

import csv
import json
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config.settings import settings
from backend.app.core.security.content_safety import (
    sanitize_text_label,
    validate_automation_action,
    validate_upload_filename,
)
from backend.app.infrastructure.database.models import AuditLog

_BROWSER_TARGETS: Dict[str, Dict[str, str]] = {
    "dashboard executivo": {
        "route": "/executive",
        "description": "Painel executivo com KPIs e visão consolidada.",
    },
    "dashboard fornecedores": {
        "route": "/dashboard",
        "description": "Dashboard operacional de fornecedores e rupturas.",
    },
    "playground ops": {
        "route": "/playground-ops",
        "description": "Ambiente controlado para operações assistidas.",
    },
    "chat": {
        "route": "/chat",
        "description": "Fluxo principal do assistente Caçulinha.",
    },
}

_BROWSER_EXTRACTIONS: Dict[str, list[dict[str, Any]]] = {
    "dashboard executivo": [
        {"widget": "vendas_30d", "label": "Vendas 30d", "value": "R$ 128.400,00"},
        {"widget": "margem_media", "label": "Margem média", "value": "31,4%"},
        {"widget": "alertas_criticos", "label": "Alertas críticos", "value": "6"},
    ],
    "dashboard fornecedores": [
        {"widget": "rupturas_ativas", "label": "Rupturas ativas", "value": "42"},
        {"widget": "lead_time_medio", "label": "Lead time médio", "value": "8 dias"},
        {"widget": "fornecedores_criticos", "label": "Fornecedores críticos", "value": "4"},
    ],
}

_RESOURCE_BY_SURFACE = {
    "chat": "chat_automation",
    "playground": "playground_ops_approval",
}


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _slugify(value: str, *, fallback: str = "artefato") -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower())
    normalized = normalized.strip("-")
    return normalized or fallback


def _clean_query(query: str) -> str:
    return " ".join(str(query or "").split()).strip()


def _strip_attachment_context(query: str) -> str:
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
    return _clean_query(" ".join(kept_lines))


def _resource_name(surface: str) -> str:
    return _RESOURCE_BY_SURFACE.get(surface, _RESOURCE_BY_SURFACE["chat"])


class ChatAutomationService:
    def __init__(self, artifact_root: Optional[str] = None) -> None:
        self.artifact_root = Path(artifact_root or settings.CHAT_AUTOMATION_ARTIFACTS_PATH)
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self.allowed_actions = {
            "browser.navigate",
            "browser.extract",
            "spreadsheet.create_report",
            "spreadsheet.update_cells",
            "export.csv",
            "email.draft",
            "email.send",
            "message.draft",
            "message.send",
        }
        self._action_registry = {
            "browser.navigate": self._execute_browser_navigate,
            "browser.extract": self._execute_browser_extract,
            "spreadsheet.create_report": self._execute_spreadsheet_create_report,
            "spreadsheet.update_cells": self._execute_spreadsheet_update_cells,
            "export.csv": self._execute_export_csv,
            "email.draft": self._execute_email_draft,
            "email.send": self._execute_email_send,
            "message.draft": self._execute_message_draft,
            "message.send": self._execute_message_send,
        }

    def detect_automation_intent(self, query: str) -> bool:
        return self._infer_action_spec(query) is not None

    def build_capability_block_response(self) -> Dict[str, Any]:
        return {
            "type": "text",
            "result": {
                "mensagem": (
                    "Posso preparar automações assistidas, mas esse recurso não está habilitado "
                    "para o seu perfil no momento."
                )
            },
            "source": "policy.capability.computer_use",
            "confidence": 0.95,
            "mode": "policy_block",
        }

    def build_proposal_response(
        self,
        *,
        query: str,
        request_id: str,
        session_id: str,
        current_user: Any,
        surface: str = "chat",
    ) -> Optional[Dict[str, Any]]:
        spec = self._infer_action_spec(query)
        if not spec:
            return None

        automation_request = {
            "proposal_id": str(request_id),
            "approval_id": None,
            "approval_status": "pending_user_approval",
            "action": spec["action"],
            "title": spec["title"],
            "summary": spec["summary"],
            "request_text": _clean_query(query),
            "params": spec["params"],
            "review_required": bool(spec.get("review_required", False)),
            "follow_up_action": spec.get("follow_up_action"),
            "follow_up_label": spec.get("follow_up_label"),
            "target_label": spec.get("target_label"),
            "surface": surface,
            "session_id": str(session_id),
            "user_id": str(getattr(current_user, "id", "") or ""),
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        message = (
            "Identifiquei uma automação compatível com o seu pedido. "
            "Revise o escopo abaixo e aprove ou rejeite antes de qualquer execução."
        )
        return {
            "type": "text",
            "result": {"mensagem": message},
            "source": "automation.registry",
            "confidence": 0.82,
            "mode": "automation_pending_approval",
            "automation_request": automation_request,
        }

    async def approve(
        self,
        db: AsyncSession,
        *,
        current_user: Any,
        surface: str = "chat",
        proposal: Optional[Dict[str, Any]] = None,
        approval_id: Optional[str] = None,
        follow_up_action: Optional[str] = None,
    ) -> Dict[str, Any]:
        automation = await self._ensure_automation_snapshot(
            db,
            current_user=current_user,
            surface=surface,
            proposal=proposal,
            approval_id=approval_id,
        )
        action_name = str(follow_up_action or automation.get("action") or "").strip().lower()
        if not action_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A automação não possui ação executável.")

        validate_automation_action(
            {"action": action_name, "params": automation.get("params") or {}},
            allowed_actions=self.allowed_actions,
        )

        automation["approval_status"] = "approved"
        automation["last_executed_action"] = action_name
        automation["updated_at"] = _now_iso()
        self._add_snapshot_log(
            db,
            action=f"{surface}_automation_approved",
            current_user=current_user,
            surface=surface,
            automation=automation,
        )

        try:
            executor = self._action_registry[action_name]
            execution_result = executor(automation=automation, current_user=current_user, surface=surface)
        except Exception as exc:
            automation["approval_status"] = "failed"
            automation["execution_error"] = sanitize_text_label(str(exc), max_length=400)
            automation["updated_at"] = _now_iso()
            self._add_snapshot_log(
                db,
                action=f"{surface}_automation_failed",
                current_user=current_user,
                surface=surface,
                automation=automation,
                status="error",
            )
            await db.commit()
            return automation

        automation.update(execution_result)
        automation["updated_at"] = _now_iso()
        self._normalize_artifact_download_url(automation, surface=surface)
        self._add_snapshot_log(
            db,
            action=f"{surface}_automation_executed",
            current_user=current_user,
            surface=surface,
            automation=automation,
        )
        await db.commit()
        return automation

    async def reject(
        self,
        db: AsyncSession,
        *,
        current_user: Any,
        surface: str = "chat",
        proposal: Optional[Dict[str, Any]] = None,
        approval_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        automation = await self._ensure_automation_snapshot(
            db,
            current_user=current_user,
            surface=surface,
            proposal=proposal,
            approval_id=approval_id,
        )
        automation["approval_status"] = "rejected"
        automation["result_summary"] = "A automação foi rejeitada e nenhum efeito operacional foi executado."
        automation["updated_at"] = _now_iso()
        self._add_snapshot_log(
            db,
            action=f"{surface}_automation_rejected",
            current_user=current_user,
            surface=surface,
            automation=automation,
        )
        await db.commit()
        return automation

    async def list_automations(
        self,
        db: AsyncSession,
        *,
        current_user: Any,
        surface: str = "chat",
        limit: int = 20,
    ) -> list[Dict[str, Any]]:
        logs = await self._load_logs(
            db,
            current_user=current_user,
            surface=surface,
            limit=max(limit * 5, 50),
        )
        latest_by_approval: Dict[str, Dict[str, Any]] = {}
        for log in logs:
            details = log.details if isinstance(log.details, dict) else {}
            automation = deepcopy(details.get("automation")) if isinstance(details.get("automation"), dict) else None
            if not automation:
                continue
            approval_key = str(automation.get("approval_id") or details.get("approval_id") or "").strip()
            if not approval_key or approval_key in latest_by_approval:
                continue
            self._normalize_artifact_download_url(automation, surface=surface)
            latest_by_approval[approval_key] = automation
            if len(latest_by_approval) >= max(1, int(limit)):
                break
        return list(latest_by_approval.values())

    async def get_automation(
        self,
        db: AsyncSession,
        *,
        current_user: Any,
        surface: str = "chat",
        approval_id: str,
    ) -> Dict[str, Any]:
        logs = await self._load_logs(db, current_user=current_user, surface=surface, limit=200)
        for log in logs:
            details = log.details if isinstance(log.details, dict) else {}
            automation = deepcopy(details.get("automation")) if isinstance(details.get("automation"), dict) else None
            if not automation:
                continue
            if str(automation.get("approval_id") or "").strip() != str(approval_id or "").strip():
                continue
            self._normalize_artifact_download_url(automation, surface=surface)
            return automation
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automação não encontrada.")

    def resolve_artifact_path(self, approval_id: str, filename: str) -> Path:
        safe_filename = validate_upload_filename(filename)
        approval_dir = self.artifact_root / _slugify(approval_id, fallback="approval")
        artifact_path = approval_dir / safe_filename
        if not artifact_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artefato não encontrado.")
        return artifact_path

    async def _ensure_automation_snapshot(
        self,
        db: AsyncSession,
        *,
        current_user: Any,
        surface: str,
        proposal: Optional[Dict[str, Any]],
        approval_id: Optional[str],
    ) -> Dict[str, Any]:
        if approval_id:
            return await self.get_automation(
                db,
                current_user=current_user,
                surface=surface,
                approval_id=str(approval_id),
            )

        normalized_proposal = self._normalize_proposal(
            proposal,
            current_user=current_user,
            surface=surface,
        )
        self._add_snapshot_log(
            db,
            action=f"{surface}_automation_requested",
            current_user=current_user,
            surface=surface,
            automation=normalized_proposal,
        )
        return normalized_proposal

    def _normalize_proposal(
        self,
        proposal: Optional[Dict[str, Any]],
        *,
        current_user: Any,
        surface: str,
    ) -> Dict[str, Any]:
        if not isinstance(proposal, dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Proposta de automação inválida.")

        action_name = sanitize_text_label(proposal.get("action"), max_length=80).lower()
        if not action_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A proposta de automação não possui ação.")

        params = proposal.get("params")
        normalized_action = validate_automation_action(
            {"action": action_name, "params": params if isinstance(params, dict) else {}},
            allowed_actions=self.allowed_actions,
        )
        now_iso = _now_iso()
        return {
            "proposal_id": sanitize_text_label(proposal.get("proposal_id"), max_length=120) or str(uuid4()),
            "approval_id": str(uuid4()),
            "approval_status": "pending_user_approval",
            "action": normalized_action["action"],
            "title": sanitize_text_label(proposal.get("title"), max_length=160) or "Automação assistida",
            "summary": sanitize_text_label(proposal.get("summary"), max_length=240) or "Automação aguardando aprovação explícita.",
            "request_text": _clean_query(str(proposal.get("request_text") or proposal.get("request") or "")),
            "params": normalized_action["params"],
            "review_required": bool(proposal.get("review_required", False)),
            "follow_up_action": sanitize_text_label(proposal.get("follow_up_action"), max_length=80).lower() or None,
            "follow_up_label": sanitize_text_label(proposal.get("follow_up_label"), max_length=80) or None,
            "target_label": sanitize_text_label(proposal.get("target_label"), max_length=120) or None,
            "surface": surface,
            "session_id": sanitize_text_label(proposal.get("session_id"), max_length=120) or None,
            "user_id": str(getattr(current_user, "id", "") or ""),
            "created_at": sanitize_text_label(proposal.get("created_at"), max_length=80) or now_iso,
            "updated_at": now_iso,
        }

    async def _load_logs(
        self,
        db: AsyncSession,
        *,
        current_user: Any,
        surface: str,
        limit: int,
    ) -> list[AuditLog]:
        resource = _resource_name(surface)
        stmt = (
            select(AuditLog)
            .where(AuditLog.resource == resource)
            .order_by(AuditLog.timestamp.desc())
            .limit(max(1, int(limit)))
        )
        if str(getattr(current_user, "role", "") or "").strip().lower() != "admin":
            stmt = stmt.where(AuditLog.user_id == getattr(current_user, "id", None))
        try:
            result = await db.execute(stmt)
        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Não foi possível consultar a trilha de automação agora: {exc}",
            ) from exc
        return list(result.scalars().all())

    def _add_snapshot_log(
        self,
        db: AsyncSession,
        *,
        action: str,
        current_user: Any,
        surface: str,
        automation: Dict[str, Any],
        status: str = "success",
    ) -> None:
        snapshot = deepcopy(automation)
        snapshot["surface"] = surface
        db.add(
            AuditLog(
                user_id=getattr(current_user, "id", None),
                action=action,
                resource=_resource_name(surface),
                details={
                    "approval_id": snapshot.get("approval_id"),
                    "proposal_id": snapshot.get("proposal_id"),
                    "approval_status": snapshot.get("approval_status"),
                    "action_name": snapshot.get("action"),
                    "surface": surface,
                    "automation": snapshot,
                },
                ip_address=f"{surface}-automation",
                status=status,
            )
        )

    def _normalize_artifact_download_url(self, automation: Dict[str, Any], *, surface: str) -> None:
        artifact = automation.get("artifact")
        if not isinstance(artifact, dict):
            return
        approval_id = sanitize_text_label(automation.get("approval_id"), max_length=120)
        filename = sanitize_text_label(artifact.get("filename"), max_length=180)
        if not approval_id or not filename:
            return
        if surface == "playground":
            artifact["download_url"] = f"/api/v1/playground/ops/artifacts/{approval_id}/{filename}"
        else:
            artifact["download_url"] = f"/api/v1/chat/automation/artifacts/{approval_id}/{filename}"

    def _infer_action_spec(self, query: str) -> Optional[Dict[str, Any]]:
        clean_query = _strip_attachment_context(query)
        lowered = clean_query.lower()
        if not lowered:
            return None

        if any(token in lowered for token in ("e-mail", "email")) and any(token in lowered for token in ("enviar", "redigir", "redija", "rascunho", "escrever")):
            recipient = self._extract_email(lowered) or "destinatario@exemplo.com"
            subject = self._build_subject(clean_query, prefix="Ação BI")
            return {
                "action": "email.draft",
                "title": "Preparar rascunho de e-mail",
                "summary": "Gerar um rascunho para revisão antes do envio final.",
                "params": {
                    "recipient": recipient,
                    "subject": subject,
                    "body_context": clean_query,
                },
                "review_required": True,
                "follow_up_action": "email.send",
                "follow_up_label": "Enviar e-mail",
                "target_label": recipient,
            }

        if any(token in lowered for token in ("mensagem", "whatsapp", "teams", "slack")) and any(token in lowered for token in ("enviar", "redigir", "redija", "rascunho", "escrever")):
            recipient = self._extract_contact_label(clean_query)
            return {
                "action": "message.draft",
                "title": "Preparar mensagem para revisão",
                "summary": "Gerar um rascunho de mensagem com revisão obrigatória antes do envio.",
                "params": {
                    "recipient": recipient,
                    "body_context": clean_query,
                },
                "review_required": True,
                "follow_up_action": "message.send",
                "follow_up_label": "Enviar mensagem",
                "target_label": recipient,
            }

        report_terms = ("planilha", "csv", "relatório", "relatorio", "export")
        report_action_terms = (
            "gerar",
            "gere",
            "criar",
            "crie",
            "montar",
            "monte",
            "exportar",
            "exporte",
            "baixar",
            "baixe",
            "emitir",
            "emita",
            "preencher",
            "preencha",
            "atualizar",
            "atualize",
        )
        if any(token in lowered for token in report_terms) and any(token in lowered for token in report_action_terms):
            segment = self._extract_segment(clean_query)
            filename = validate_upload_filename(f"{_slugify(self._build_subject(clean_query, prefix='relatorio-operacional'))}.csv")
            action = "export.csv" if "csv" in lowered or "export" in lowered else "spreadsheet.create_report"
            if any(token in lowered for token in ("preencher", "atualizar", "atualize", "preencha")):
                action = "spreadsheet.update_cells"
            return {
                "action": action,
                "title": "Gerar artefato exportável",
                "summary": "Criar ou atualizar uma planilha/relatório exportável sob aprovação explícita.",
                "params": {
                    "filename": filename,
                    "segment": segment,
                    "request_context": clean_query,
                },
                "review_required": False,
                "target_label": filename,
            }

        browser_action_terms = (
            "naveg",
            "abrir",
            "abra",
            "acessar",
            "acesse",
            "entrar",
            "entre",
            "ir para",
            "extrair",
            "extraia",
            "capturar",
            "copiar indicadores",
        )
        browser_target_terms = ("dashboard", "painel", "sistema", "playground", "chat", "kpi")
        if any(token in lowered for token in browser_action_terms) and any(token in lowered for token in browser_target_terms):
            target_key = self._infer_browser_target(lowered)
            if not target_key:
                return None
            extract_mode = any(token in lowered for token in ("extrair", "extraia", "capturar", "copiar indicadores"))
            return {
                "action": "browser.extract" if extract_mode else "browser.navigate",
                "title": "Executar navegação controlada",
                "summary": "Navegar em ambiente de teste ou extrair indicadores de um dashboard permitido.",
                "params": {
                    "target": target_key,
                    "route": _BROWSER_TARGETS[target_key]["route"],
                    "request_context": clean_query,
                },
                "review_required": False,
                "target_label": target_key.title(),
            }
        return None

    def _infer_browser_target(self, lowered_query: str) -> Optional[str]:
        if "fornecedor" in lowered_query or "ruptura" in lowered_query:
            return "dashboard fornecedores"
        if "playground" in lowered_query or "ops" in lowered_query:
            return "playground ops"
        if "chat" in lowered_query:
            return "chat"
        if "dashboard" in lowered_query or "painel" in lowered_query or "kpi" in lowered_query:
            return "dashboard executivo"
        return None

    def _extract_email(self, query: str) -> Optional[str]:
        match = re.search(r"([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})", query, flags=re.IGNORECASE)
        if not match:
            return None
        return match.group(1).lower()

    def _extract_contact_label(self, query: str) -> str:
        match = re.search(r"(?:para|ao|aos)\s+([a-zà-ÿ0-9 ._-]{3,80})", query, flags=re.IGNORECASE)
        if not match:
            return "time responsável"
        return sanitize_text_label(match.group(1), max_length=80) or "time responsável"

    def _extract_segment(self, query: str) -> Optional[str]:
        match = re.search(r"segmento\s+([a-zà-ÿ0-9 _-]{2,40})", query, flags=re.IGNORECASE)
        if not match:
            return None
        return sanitize_text_label(match.group(1), max_length=40) or None

    def _build_subject(self, query: str, *, prefix: str) -> str:
        subject = sanitize_text_label(query, max_length=80)
        return f"{prefix} - {subject or 'automação assistida'}"

    def _approval_dir(self, approval_id: str) -> Path:
        approval_dir = self.artifact_root / _slugify(approval_id, fallback="approval")
        approval_dir.mkdir(parents=True, exist_ok=True)
        return approval_dir

    def _write_csv_artifact(
        self,
        *,
        approval_id: str,
        filename: str,
        rows: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        safe_filename = validate_upload_filename(filename)
        artifact_path = self._approval_dir(approval_id) / safe_filename
        normalized_rows = [dict(row) for row in rows]
        with artifact_path.open("w", encoding="utf-8", newline="") as handle:
            if normalized_rows:
                fieldnames = list(normalized_rows[0].keys())
                writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=";")
                writer.writeheader()
                for row in normalized_rows:
                    writer.writerow({key: row.get(key, "") for key in fieldnames})
            else:
                handle.write("campo;valor\nsem_dados;sem_dados\n")
        return {
            "filename": safe_filename,
            "mime_type": "text/csv",
            "size_bytes": artifact_path.stat().st_size,
        }

    def _write_json_artifact(
        self,
        *,
        approval_id: str,
        filename: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        safe_filename = validate_upload_filename(filename)
        artifact_path = self._approval_dir(approval_id) / safe_filename
        with artifact_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
        return {
            "filename": safe_filename,
            "mime_type": "application/json",
            "size_bytes": artifact_path.stat().st_size,
        }

    def _execute_browser_navigate(self, *, automation: Dict[str, Any], current_user: Any, surface: str) -> Dict[str, Any]:
        target = str((automation.get("params") or {}).get("target") or "").strip().lower()
        if target not in _BROWSER_TARGETS:
            raise ValueError("Destino de navegação não autorizado")
        target_meta = _BROWSER_TARGETS[target]
        return {
            "approval_status": "completed",
            "result_summary": f"Navegação guiada preparada para {target.title()} em ambiente controlado.",
            "execution_trace": [
                "Aprovação registrada",
                f"Rota validada: {target_meta['route']}",
                "Sessão de navegação controlada concluída sem efeitos destrutivos",
            ],
            "browser_session": {
                "target": target,
                "route": target_meta["route"],
                "environment": "sandbox",
                "description": target_meta["description"],
            },
        }

    def _execute_browser_extract(self, *, automation: Dict[str, Any], current_user: Any, surface: str) -> Dict[str, Any]:
        target = str((automation.get("params") or {}).get("target") or "").strip().lower()
        if target not in _BROWSER_EXTRACTIONS:
            raise ValueError("Destino de extração não autorizado")
        payload = {
            "target": target,
            "extracted_at": _now_iso(),
            "items": _BROWSER_EXTRACTIONS[target],
        }
        artifact = self._write_json_artifact(
            approval_id=str(automation.get("approval_id")),
            filename=f"{_slugify(target, fallback='dashboard')}-extract.json",
            payload=payload,
        )
        return {
            "approval_status": "completed",
            "result_summary": f"Indicadores extraídos de {target.title()} com sucesso.",
            "extracted_items": payload["items"],
            "artifact": artifact,
        }

    def _build_report_rows(self, automation: Dict[str, Any], current_user: Any) -> list[Dict[str, Any]]:
        params = automation.get("params") if isinstance(automation.get("params"), dict) else {}
        return [
            {
                "campo": "solicitacao",
                "valor": automation.get("request_text") or params.get("request_context") or "",
            },
            {
                "campo": "segmento",
                "valor": params.get("segment") or "não informado",
            },
            {
                "campo": "usuario",
                "valor": getattr(current_user, "email", "") or getattr(current_user, "username", "") or getattr(current_user, "id", ""),
            },
            {
                "campo": "gerado_em",
                "valor": _now_iso(),
            },
            {
                "campo": "status",
                "valor": "aprovado e gerado",
            },
        ]

    def _execute_spreadsheet_create_report(self, *, automation: Dict[str, Any], current_user: Any, surface: str) -> Dict[str, Any]:
        params = automation.get("params") if isinstance(automation.get("params"), dict) else {}
        artifact = self._write_csv_artifact(
            approval_id=str(automation.get("approval_id")),
            filename=str(params.get("filename") or "relatorio_operacional.csv"),
            rows=self._build_report_rows(automation, current_user),
        )
        return {
            "approval_status": "completed",
            "result_summary": "Planilha operacional gerada com sucesso.",
            "artifact": artifact,
        }

    def _execute_spreadsheet_update_cells(self, *, automation: Dict[str, Any], current_user: Any, surface: str) -> Dict[str, Any]:
        params = automation.get("params") if isinstance(automation.get("params"), dict) else {}
        rows = self._build_report_rows(automation, current_user)
        rows.append({"campo": "acao", "valor": "células atualizadas no artefato controlado"})
        artifact = self._write_csv_artifact(
            approval_id=str(automation.get("approval_id")),
            filename=str(params.get("filename") or "planilha_operacional.csv"),
            rows=rows,
        )
        return {
            "approval_status": "completed",
            "result_summary": "Planilha controlada preenchida/atualizada com sucesso.",
            "artifact": artifact,
        }

    def _execute_export_csv(self, *, automation: Dict[str, Any], current_user: Any, surface: str) -> Dict[str, Any]:
        result = self._execute_spreadsheet_create_report(
            automation=automation,
            current_user=current_user,
            surface=surface,
        )
        result["result_summary"] = "Arquivo CSV exportável gerado com sucesso."
        return result

    def _execute_email_draft(self, *, automation: Dict[str, Any], current_user: Any, surface: str) -> Dict[str, Any]:
        params = automation.get("params") if isinstance(automation.get("params"), dict) else {}
        recipient = sanitize_text_label(params.get("recipient"), max_length=120) or "destinatario@exemplo.com"
        subject = sanitize_text_label(params.get("subject"), max_length=160) or "Atualização de BI"
        body = (
            f"Olá,\n\n"
            f"Segue um resumo do pedido solicitado: {sanitize_text_label(params.get('body_context'), max_length=240)}.\n\n"
            "Posso ajustar o texto antes do envio final, se necessário.\n\n"
            "Atenciosamente,\nCaçulinha BI"
        )
        return {
            "approval_status": "draft_ready",
            "result_summary": "Rascunho de e-mail pronto para revisão obrigatória.",
            "draft": {
                "channel": "email",
                "recipient": recipient,
                "subject": subject,
                "body": body,
            },
            "follow_up_action": "email.send",
            "follow_up_label": "Enviar e-mail",
        }

    def _execute_email_send(self, *, automation: Dict[str, Any], current_user: Any, surface: str) -> Dict[str, Any]:
        draft = automation.get("draft") if isinstance(automation.get("draft"), dict) else None
        if not draft:
            raise ValueError("Nenhum rascunho de e-mail disponível para envio.")
        payload = {
            "channel": "email",
            "recipient": draft.get("recipient"),
            "subject": draft.get("subject"),
            "body": draft.get("body"),
            "sent_at": _now_iso(),
            "sent_by": getattr(current_user, "email", "") or getattr(current_user, "username", "") or str(getattr(current_user, "id", "")),
        }
        artifact = self._write_json_artifact(
            approval_id=str(automation.get("approval_id")),
            filename="email-outbox.json",
            payload=payload,
        )
        return {
            "approval_status": "completed",
            "result_summary": "E-mail registrado na outbox auditável após revisão explícita.",
            "delivery": payload,
            "artifact": artifact,
            "follow_up_action": None,
            "follow_up_label": None,
        }

    def _execute_message_draft(self, *, automation: Dict[str, Any], current_user: Any, surface: str) -> Dict[str, Any]:
        params = automation.get("params") if isinstance(automation.get("params"), dict) else {}
        recipient = sanitize_text_label(params.get("recipient"), max_length=120) or "time responsável"
        body = (
            f"Resumo rápido: {sanitize_text_label(params.get('body_context'), max_length=220)}. "
            "Se estiver de acordo, aprove o envio final."
        )
        return {
            "approval_status": "draft_ready",
            "result_summary": "Mensagem pronta para revisão obrigatória.",
            "draft": {
                "channel": "message",
                "recipient": recipient,
                "body": body,
            },
            "follow_up_action": "message.send",
            "follow_up_label": "Enviar mensagem",
        }

    def _execute_message_send(self, *, automation: Dict[str, Any], current_user: Any, surface: str) -> Dict[str, Any]:
        draft = automation.get("draft") if isinstance(automation.get("draft"), dict) else None
        if not draft:
            raise ValueError("Nenhum rascunho de mensagem disponível para envio.")
        payload = {
            "channel": "message",
            "recipient": draft.get("recipient"),
            "body": draft.get("body"),
            "sent_at": _now_iso(),
            "sent_by": getattr(current_user, "email", "") or getattr(current_user, "username", "") or str(getattr(current_user, "id", "")),
        }
        artifact = self._write_json_artifact(
            approval_id=str(automation.get("approval_id")),
            filename="message-outbox.json",
            payload=payload,
        )
        return {
            "approval_status": "completed",
            "result_summary": "Mensagem registrada na outbox auditável após revisão explícita.",
            "delivery": payload,
            "artifact": artifact,
            "follow_up_action": None,
            "follow_up_label": None,
        }
