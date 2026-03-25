"""
Avaliação versionada de precisão operacional do ChatBI.

Foco:
- roteamento correto para consultas objetivas de negócio
- follow-up curto ancorado em contexto estruturado
- bloqueio de respostas vagas sem âncora suficiente
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from backend.app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
from backend.app.core.utils.intent_classifier import classify_intent
from backend.app.core.utils.query_router import route_query


def _agent_stub() -> CaculinhaBIAgent:
    return CaculinhaBIAgent.__new__(CaculinhaBIAgent)


def _is_subset(expected: Any, actual: Any) -> bool:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(key in actual and _is_subset(value, actual[key]) for key, value in expected.items())
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            return False
        return all(_is_subset(exp_item, act_item) for exp_item, act_item in zip(expected, actual))
    return expected == actual


def load_operational_precision_dataset(dataset_path: str | Path) -> Dict[str, Any]:
    path = Path(dataset_path)
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_operational_precision_case(case: Dict[str, Any]) -> Dict[str, Any]:
    case_id = str(case.get("id", "unknown"))
    kind = str(case.get("kind", "")).strip().lower()
    agent = _agent_stub()

    if kind == "route":
        query = str(case.get("query", ""))
        intent = classify_intent(query)
        selection = route_query(intent.intent, query, intent.confidence)
        expected_tool = case.get("expected_tool")
        expected_params = case.get("expected_params", {})
        min_confidence = float(case.get("min_confidence", 0.0) or 0.0)

        failures: List[str] = []
        if expected_tool and selection.tool_name != expected_tool:
            failures.append(f"tool={selection.tool_name} expected={expected_tool}")
        if expected_params and not _is_subset(expected_params, selection.tool_params):
            failures.append(f"params={selection.tool_params} expected_subset={expected_params}")
        if float(selection.confidence or 0.0) < min_confidence:
            failures.append(f"confidence={selection.confidence:.2f} min={min_confidence:.2f}")

        return {
            "id": case_id,
            "kind": kind,
            "passed": not failures,
            "failures": failures,
        }

    if kind == "resolve_followup":
        query = str(case.get("query", ""))
        chat_history = case.get("chat_history", [])
        actual = agent._resolve_query_with_history_context(query, chat_history)
        expected = str(case.get("expected_resolved_query", ""))
        failures = []
        if actual != expected:
            failures.append(f"resolved={actual!r} expected={expected!r}")
        return {
            "id": case_id,
            "kind": kind,
            "passed": not failures,
            "failures": failures,
        }

    if kind == "clarification":
        query = str(case.get("query", ""))
        tool_name = str(case.get("tool_name", "consultar_dados_flexivel"))
        confidence = float(case.get("confidence", 0.9) or 0.9)
        chat_history = case.get("chat_history")
        result = agent._build_clarification_if_needed(
            query,
            tool_name,
            confidence,
            chat_history=chat_history,
        )
        message = str((result or {}).get("result", {}).get("mensagem", "") or "")
        expected_substrings = [str(item) for item in case.get("expected_message_contains", [])]
        failures = []
        if result is None:
            failures.append("clarification=None")
        for snippet in expected_substrings:
            if snippet.lower() not in message.lower():
                failures.append(f"missing_message_snippet={snippet!r}")
        return {
            "id": case_id,
            "kind": kind,
            "passed": not failures,
            "failures": failures,
        }

    if kind == "fallback":
        primary_tool = str(case.get("primary_tool_name", "consultar_dados_flexivel"))
        configured = list(case.get("configured_fallbacks", []) or [])
        query = str(case.get("query", ""))
        actual = agent._infer_semantic_fallback_tools(primary_tool, configured, user_query=query)
        expected = list(case.get("expected_fallbacks", []) or [])
        failures = []
        if actual != expected:
            failures.append(f"fallbacks={actual} expected={expected}")
        return {
            "id": case_id,
            "kind": kind,
            "passed": not failures,
            "failures": failures,
        }

    return {
        "id": case_id,
        "kind": kind,
        "passed": False,
        "failures": [f"unsupported_kind={kind!r}"],
    }


def evaluate_operational_precision_dataset(dataset_path: str | Path) -> Dict[str, Any]:
    payload = load_operational_precision_dataset(dataset_path)
    cases = payload.get("cases", [])
    results = [evaluate_operational_precision_case(case) for case in cases]
    total = len(results)
    passed = sum(1 for result in results if result["passed"])
    failed_cases = [result for result in results if not result["passed"]]
    return {
        "dataset_version": payload.get("dataset_version"),
        "total_cases": total,
        "passed_cases": passed,
        "pass_rate": (passed / total) if total else 0.0,
        "failures": failed_cases,
    }
