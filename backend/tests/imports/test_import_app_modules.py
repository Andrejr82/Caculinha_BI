
import pytest
import pkgutil
import importlib
import sys
from pathlib import Path

# Adiciona backend/ ao path para simular o ambiente de execução real
# Isso já deve ser feito pelo conftest.py, mas reforçamos aqui se necessário
# ou confiamos no conftest.

def get_all_modules(package_path, package_name):
    """
    Retorna uma lista de todos os submódulos em um pacote.
    """
    modules = []
    if not package_path.exists():
        return modules
        
    for _, name, is_pkg in pkgutil.walk_packages([str(package_path)]):
        full_name = f"{package_name}.{name}"
        modules.append(full_name)
    return modules

def test_import_backend_app():
    """Tenta importar backend.app e verifica se é um pacote válido."""
    import backend.app
    assert backend.app.__file__ is not None

def test_import_app_core():
    """Tenta importar app.core (com path injection funcionando)."""
    try:
        import backend.app.core
    except ImportError as e:
        pytest.fail(f"Falha ao importar app.core: {e}. Verifique se backend/ está no sys.path.")

def test_can_import_all_app_modules():
    """
    Tenta importar todos os módulos dentro de backend/app recursivamente.
    Falha se qualquer módulo tiver erro de sintaxe ou dependência faltando.
    """
    # Caminho absoluto para backend/app
    root_dir = Path(__file__).parent.parent.parent # backend/tests/imports -> backend/tests -> backend -> raiz? 
    # Não, __file__ está em backend/tests/imports/
    # parent = backend/tests
    # parent.parent = backend
    
    app_dir = root_dir / "app"
    
    assert app_dir.exists(), f"Diretório app não encontrado em {app_dir}"
    
    modules = get_all_modules(app_dir, "app")
    
    # Lista de exclusão temporária para módulos sabidamente problemáticos (se houver)
    # Por enquanto tentamos importar tudo.
    
    failed_imports = []
    
    for module_name in modules:
        try:
            importlib.import_module(module_name)
        except Exception as e:
            failed_imports.append(f"{module_name}: {str(e)}")
            
    if failed_imports:
        pytest.fail(f"Falha ao importar os seguintes módulos:\n" + "\n".join(failed_imports))
