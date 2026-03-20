"""
Smoke tests for the ChatBI stack.
"""

from pathlib import Path

from backend.app.config.settings import settings
from backend.app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
from backend.app.core.agents.code_gen_agent import CodeGenAgent
from backend.app.core.llm_factory import LLMFactory
from backend.app.core.tools.flexible_query_tool import consultar_dados_flexivel
from backend.app.core.utils.field_mapper import FieldMapper


def test_1_imports():
    assert consultar_dados_flexivel is not None
    assert CaculinhaBIAgent is not None
    assert settings is not None


def test_2_model_config():
    model = str(getattr(settings, "LLM_MODEL_NAME", "") or "")
    assert model.strip() != ""


def test_3_flexible_tool():
    result = consultar_dados_flexivel.invoke({"limite": 5})
    assert isinstance(result, dict)
    assert "resultados" in result


def test_4_agent_tools():
    llm = LLMFactory.get_adapter(use_smart=True)
    field_mapper = FieldMapper()
    agent = CaculinhaBIAgent(
        llm=llm,
        code_gen_agent=CodeGenAgent(),
        field_mapper=field_mapper,
        user_role="analyst",
    )

    tool_names = [t.name for t in agent.bi_tools]
    assert "consultar_dados_flexivel" in tool_names


def test_5_parquet_config():
    configured = Path(settings.PARQUET_FILE_PATH)
    candidates = [
        configured,
        Path.cwd() / configured,
        Path.cwd() / "backend" / "data" / "parquet" / "admmat.parquet",
        Path.cwd() / "data" / "parquet" / "admmat.parquet",
    ]
    assert any(path.exists() for path in candidates)
