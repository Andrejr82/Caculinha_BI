from unittest.mock import patch

from backend.app.core.llm_factory import SmartLLM
from backend.app.infrastructure.resilience.circuit_breaker import CircuitBreakerOpenError


class _FakeAdapter:
    def __init__(self, provider: str, *, fail: bool = False):
        self.provider = provider
        self.fail = fail
        self.calls = 0

    def get_completion(self, messages, tools=None):
        self.calls += 1
        if self.fail:
            return {"error": f"{self.provider} unavailable"}
        return {"content": f"ok-{self.provider}"}


def _mocked_llm():
    llm = SmartLLM(primary="groq")
    adapters = {
        "groq": _FakeAdapter("groq"),
        "mock": _FakeAdapter("mock"),
    }
    llm._get_adapter = lambda provider: adapters.get(provider)  # type: ignore[assignment]
    return llm, adapters


def test_task_routing_prefers_groq_for_market_research():
    llm, adapters = _mocked_llm()

    response = llm.get_completion(
        [{"role": "user", "content": "pesquisa de mercado para caderno"}],
        tools=None,
        task_type="market_research",
    )

    assert response.get("provider") == "groq"
    assert adapters["groq"].calls == 1
    assert adapters["mock"].calls == 0


def test_legacy_google_alias_is_normalized_to_groq():
    llm = SmartLLM(primary="google")
    assert llm.primary == "groq"


def test_task_routing_prefers_groq_for_calculation():
    llm, adapters = _mocked_llm()

    response = llm.get_completion(
        [{"role": "user", "content": "calcule eoq"}],
        tools=None,
        task_type="calculation",
    )

    assert response.get("provider") == "groq"
    assert adapters["groq"].calls == 1
    assert adapters["mock"].calls == 0


def test_task_routing_respects_explicit_mapping_override():
    llm, adapters = _mocked_llm()
    llm.task_provider_routing = {"calculation": ["mock", "groq"]}

    response = llm.get_completion(
        [{"role": "user", "content": "simulação de eoq"}],
        tools=None,
        task_type="calculation",
    )

    assert response.get("provider") == "mock"
    assert adapters["mock"].calls == 1
    assert adapters["groq"].calls == 0


def test_task_routing_fallbacks_when_first_provider_errors():
    llm, adapters = _mocked_llm()
    adapters["mock"].fail = True
    llm.task_provider_routing = {"analysis": ["mock", "groq"]}

    response = llm.get_completion(
        [{"role": "user", "content": "analise vendas por segmento"}],
        tools=None,
        task_type="analysis",
    )

    assert response.get("provider") == "groq"
    assert adapters["mock"].calls == 1
    assert adapters["groq"].calls == 1


def test_get_completion_uses_circuit_breaker_wrapper():
    llm, _ = _mocked_llm()
    llm_globals = llm._call_with_circuit_breaker.__globals__

    class _Breaker:
        def __init__(self):
            self.calls = 0

        def call(self, fn):
            self.calls += 1
            return fn()

    breaker = _Breaker()
    with patch.dict(llm_globals, {"get_circuit_breaker": lambda *_args, **_kwargs: breaker}):
        response = llm.get_completion(
            [{"role": "user", "content": "analise de vendas"}],
            tools=None,
            task_type="analysis",
        )

    assert response.get("provider") == "groq"
    assert breaker.calls >= 1


def test_get_completion_skips_provider_when_circuit_is_open():
    llm, adapters = _mocked_llm()
    llm.task_provider_routing = {"analysis": ["mock", "groq"]}
    llm_globals = llm._call_with_circuit_breaker.__globals__
    circuit_open_exc = llm_globals.get("CircuitBreakerOpenError", CircuitBreakerOpenError)

    class _OpenOnFirstBreaker:
        def __init__(self):
            self._calls = 0

        def call(self, fn):
            self._calls += 1
            if self._calls == 1:
                raise circuit_open_exc("open")
            return fn()

    breaker = _OpenOnFirstBreaker()
    with patch.dict(llm_globals, {"get_circuit_breaker": lambda *_args, **_kwargs: breaker}):
        response = llm.get_completion(
            [{"role": "user", "content": "analise de vendas"}],
            tools=None,
            task_type="analysis",
        )

    assert response.get("provider") == "groq"
    assert adapters["mock"].calls == 0
    assert adapters["groq"].calls == 1
