
import pytest
import sys
import builtins
from unittest.mock import patch, MagicMock
import importlib

# Lista de módulos críticos para verificar side-effects
CRITICAL_MODULES = [
    "app.core.agents.caculinha_bi_agent",
    "app.core.agents.orchestrator",
    "app.core.llm_factory", # Factory crucial
    "app.infrastructure.database.relational_db",
]

@pytest.fixture
def clean_sys_modules():
    """
    Remove módulos alvo do sys.modules antes do teste para forçar re-importação.
    """
    # Remove dependências transitivas primeiro (GroqAdapter, etc)
    to_remove = [m for m in sys.modules if m.startswith("app.")]
    for m in to_remove:
        del sys.modules[m]

def test_no_sys_exit_on_import(clean_sys_modules):
    """
    Garante que nenhum módulo execute sys.exit() ao ser importado.
    Isso é crítico para testes e uso como biblioteca.
    """
    with patch.object(sys, 'exit', side_effect=SystemExit("SYS_EXIT_CALLED")) as mock_exit:
        try:
            # Tenta importar módulos de alto nível que costumam orquestrar coisas
            # app.main pode não existir ou pode ser o entrypoint
            import backend.app.core.agents.master_prompt
        except SystemExit as e:
            pytest.fail(f"Módulo chamou sys.exit() durante importação: {e}")
        except Exception:
            # Outros erros de importação não são o foco deste teste (tratados em test_import_app_modules)
            pass
            
        assert not mock_exit.called, "sys.exit() foi chamado durante a importação!"

def test_no_global_code_execution():
    """
    Tenta detectar execução de código pesado no nível global.
    Isso é subjetivo, mas podemos verificar se SINGLETONS pesados são instanciados.
    """
    # Força remoção do módulo factory E do adapter
    if "app.core.llm_factory" in sys.modules:
        del sys.modules["app.core.llm_factory"]
    if "app.core.llm_groq_adapter" in sys.modules:
        del sys.modules["app.core.llm_groq_adapter"]
        
    # Mockamos a classe GroqLLMAdapter onde ela é definida
    with patch("app.core.llm_groq_adapter.GroqLLMAdapter") as mock_groq_adapter:
         
        # Importa o módulo diretamente
        import backend.app.core.llm_factory
        
        # LLMFactory deve ser uma classe ou função factory, não deve instanciar nada no import
        # GroqLLMAdapter é importado no topo de llm_factory, mas não deve ser instanciado globalmente
        assert not mock_groq_adapter.called, "GroqLLMAdapter instanciado durante import do factory! (Efeito colateral)"
        
        # Verifica se o SmartLLM foi definido
        assert hasattr(app.core.llm_factory, "SmartLLM")
