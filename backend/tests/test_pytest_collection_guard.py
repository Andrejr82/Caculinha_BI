
import pytest
import subprocess
import sys
from pathlib import Path

def test_pytest_does_not_collect_scripts():
    """
    Garante que o pytest NÃO coleta scripts de 'backend/scripts' 
    que não são testes unitários reais, mas têm prefixo test_.
    """
    # Executa pytest --collect-only na raiz e verifica a saída
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent  # Raiz do projeto
    )
    
    # Debug information
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    
    # 1. Deve rodar com sucesso
    assert result.returncode == 0
    
    # 2. NÃO deve coletar scripts da pasta backend/scripts
    # Ex: backend/scripts/test_product_analysis_fix.py
    assert "backend/scripts/test_product_analysis_fix.py" not in result.stdout
    assert "backend/scripts/test_integration.py" not in result.stdout
    
    # 3. DEVE coletar testes oficiais
    assert "backend/tests" in result.stdout or "tests" in result.stdout

def test_no_sys_exit_on_import():
    """
    Verifica se importar os scripts não causa sys.exit() acidental.
    Isso é crucial para ferramentas de análise estática e IDEs.
    """
    scripts_dir = Path(__file__).parent.parent.parent / "backend/scripts"
    
    suspect_scripts = [
        "test_product_analysis_fix.py",
        "validate_modernization.py"
    ]
    
    for script in suspect_scripts:
        script_path = scripts_dir / script
        if not script_path.exists():
            continue
            
        # Tenta importar em um subprocesso para isolar side-effects
        # Se o script tiver código solto fora de if __name__ == "__main__",
        # ele pode executar e falhar ou sair.
        cmd = [sys.executable, "-c", f"import sys; sys.path.append('backend/scripts'); import {script.replace('.py', '')}"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # O import deve ser seguro (return code 0) OU falhar por ModuleNotFoundError 
        # (se faltar dep), mas não por execução lógica
        if result.returncode != 0:
            # Se falhar, verifique se não foi sys.exit
            if "SystemExit" in result.stderr:
                 pytest.fail(f"Script {script} executa sys.exit() ao ser importado! Mova código para main().\nErro: {result.stderr}")
