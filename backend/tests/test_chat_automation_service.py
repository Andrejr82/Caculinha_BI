from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from backend.app.services.chat_automation_service import ChatAutomationService


class _ScalarsResult:
    def __init__(self, data):
        self._data = data

    def all(self):
        return self._data


class _ExecuteResult:
    def __init__(self, data):
        self._data = data

    def scalars(self):
        return _ScalarsResult(self._data)


class FakeDbSession:
    def __init__(self):
        self.added = []

    def add(self, item):
        item.timestamp = datetime.utcnow()
        self.added.append(item)

    async def commit(self):
        return None

    async def execute(self, _query):
        return _ExecuteResult(list(reversed(self.added)))


def _make_user():
    return SimpleNamespace(
        id=uuid4(),
        role="admin",
        email="admin@agentbi.com",
        username="admin",
    )


def test_build_proposal_response_detects_email_automation():
    service = ChatAutomationService()

    response = service.build_proposal_response(
        query="redija um email para compras@empresa.com com resumo da ruptura",
        request_id="req-automation-001",
        session_id="session-1",
        current_user=_make_user(),
    )

    assert response is not None
    assert response["automation_request"]["action"] == "email.draft"
    assert response["automation_request"]["follow_up_action"] == "email.send"


def test_detect_automation_intent_ignores_analytical_dashboard_generation_request():
    service = ChatAutomationService()

    response = service.build_proposal_response(
        query="gere um dashboard interativo do segmento ARTES nos últimos 30 dias com tabela por UNE",
        request_id="req-automation-analytical-dashboard",
        session_id="session-dashboard",
        current_user=_make_user(),
    )

    assert service.detect_automation_intent(
        "gere um dashboard interativo do segmento ARTES nos últimos 30 dias com tabela por UNE"
    ) is False
    assert response is None


def test_detect_automation_intent_ignores_analytical_sales_report_chat_request():
    service = ChatAutomationService()

    query = "gere um relatório de vendas do segmento tecidos na une scr"
    response = service.build_proposal_response(
        query=query,
        request_id="req-automation-analytical-sales-report",
        session_id="session-sales-report",
        current_user=_make_user(),
    )

    assert service.detect_automation_intent(query) is False
    assert response is None


def test_detect_automation_intent_keeps_navigation_dashboard_request():
    service = ChatAutomationService()

    response = service.build_proposal_response(
        query="abra o dashboard executivo e extraia os indicadores principais",
        request_id="req-automation-browser-dashboard",
        session_id="session-browser",
        current_user=_make_user(),
    )

    assert response is not None
    assert response["automation_request"]["action"] == "browser.extract"
    assert response["automation_request"]["target_label"] == "Dashboard Executivo"


def test_detect_automation_intent_ignores_attachment_filename_context():
    service = ChatAutomationService()

    query = (
        "Quais produtos costumam ser comprados juntos?\n\n"
        "Considere os anexos desta sessão: csv_basket_realista_baseado_no_parquet_12000_linhas.csv."
    )

    assert service.detect_automation_intent(query) is False
    assert service.build_proposal_response(
        query=query,
        request_id="req-automation-attachment-filename",
        session_id="session-attachment-filename",
        current_user=_make_user(),
    ) is None


@pytest.mark.asyncio
async def test_approve_email_flow_requires_review_and_then_completes(tmp_path):
    service = ChatAutomationService(str(tmp_path))
    db = FakeDbSession()
    user = _make_user()

    draft = await service.approve(
        db,
        current_user=user,
        proposal={
            "proposal_id": "req-automation-002",
            "action": "email.draft",
            "title": "Enviar e-mail operacional",
            "summary": "Preparar e revisar um e-mail.",
            "request_text": "Enviar e-mail com resumo executivo.",
            "session_id": "session-2",
            "params": {
                "recipient": "compras@empresa.com",
                "subject": "Resumo executivo",
                "body_context": "Resumo de vendas e rupturas.",
            },
            "review_required": True,
            "follow_up_action": "email.send",
            "follow_up_label": "Enviar e-mail",
        },
    )

    assert draft["approval_status"] == "draft_ready"
    assert draft["draft"]["recipient"] == "compras@empresa.com"

    completed = await service.approve(
        db,
        current_user=user,
        approval_id=draft["approval_id"],
        follow_up_action="email.send",
    )

    assert completed["approval_status"] == "completed"
    assert completed["artifact"]["filename"] == "email-outbox.json"
    assert completed["delivery"]["channel"] == "email"

    history = await service.list_automations(db, current_user=user, limit=10)
    assert history[0]["approval_id"] == completed["approval_id"]


@pytest.mark.asyncio
async def test_approve_report_flow_generates_exportable_csv(tmp_path):
    service = ChatAutomationService(str(tmp_path))
    db = FakeDbSession()
    user = _make_user()

    result = await service.approve(
        db,
        current_user=user,
        proposal={
            "proposal_id": "req-automation-003",
            "action": "spreadsheet.create_report",
            "title": "Gerar planilha",
            "summary": "Exportar planilha operacional.",
            "request_text": "Gerar planilha de fornecedores críticos.",
            "session_id": "session-3",
            "params": {
                "filename": "fornecedores_criticos.csv",
                "segment": "ARTES",
                "request_context": "Exportar fornecedores críticos.",
            },
        },
    )

    assert result["approval_status"] == "completed"
    assert result["artifact"]["filename"] == "fornecedores_criticos.csv"
    artifact_path = service.resolve_artifact_path(result["approval_id"], result["artifact"]["filename"])
    assert artifact_path.exists()
