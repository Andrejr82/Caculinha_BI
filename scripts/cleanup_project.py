"""
Script Robusto de Limpeza do Projeto
Usa Python para contornar problemas de permissão do PowerShell
"""
import os
import shutil
from pathlib import Path
import time

# Cores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

def safe_remove(file_path):
    """Remove arquivo com retry e tratamento de erros"""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            if os.path.exists(file_path):
                # Tentar remover atributo read-only
                os.chmod(file_path, 0o777)
                os.remove(file_path)
                return True, f"Removido: {file_path}"
        except PermissionError:
            if attempt < max_attempts - 1:
                time.sleep(0.5)  # Aguardar e tentar novamente
                continue
            return False, f"Permissão negada: {file_path}"
        except Exception as e:
            return False, f"Erro ao remover {file_path}: {str(e)}"
    return False, f"Falha após {max_attempts} tentativas: {file_path}"

def safe_move(src, dst):
    """Move arquivo com retry e tratamento de erros"""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            if os.path.exists(src):
                # Criar diretório destino se não existir
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                # Tentar remover atributo read-only
                os.chmod(src, 0o777)
                shutil.move(src, dst)
                return True, f"Movido: {os.path.basename(src)}"
        except PermissionError:
            if attempt < max_attempts - 1:
                time.sleep(0.5)
                continue
            return False, f"Permissão negada: {os.path.basename(src)}"
        except Exception as e:
            return False, f"Erro ao mover {os.path.basename(src)}: {str(e)}"
    return False, f"Falha após {max_attempts} tentativas: {os.path.basename(src)}"

def main():
    backend_path = Path("d:/Dev/Agente_BI/BI_Solution/backend")
    
    print(f"{Colors.YELLOW}=== LIMPEZA ROBUSTA DO PROJETO ==={Colors.END}\n")
    
    # Contadores
    removed_count = 0
    moved_count = 0
    failed_count = 0
    
    # 1. REMOVER LOGS
    print(f"{Colors.YELLOW}1. Removendo arquivos .log...{Colors.END}")
    log_files = list(backend_path.glob("*.log"))
    for log_file in log_files:
        success, msg = safe_remove(log_file)
        if success:
            print(f"  {Colors.GREEN}✓{Colors.END} {msg}")
            removed_count += 1
        else:
            print(f"  {Colors.RED}✗{Colors.END} {msg}")
            failed_count += 1
    
    # 2. REMOVER OUTPUTS
    print(f"\n{Colors.YELLOW}2. Removendo arquivos *_output.txt...{Colors.END}")
    output_files = list(backend_path.glob("*_output.txt"))
    for output_file in output_files:
        success, msg = safe_remove(output_file)
        if success:
            print(f"  {Colors.GREEN}✓{Colors.END} {msg}")
            removed_count += 1
        else:
            print(f"  {Colors.RED}✗{Colors.END} {msg}")
            failed_count += 1
    
    # 3. REMOVER SUCCESS
    print(f"\n{Colors.YELLOW}3. Removendo arquivos success*.txt...{Colors.END}")
    success_files = list(backend_path.glob("success*.txt"))
    for success_file in success_files:
        success, msg = safe_remove(success_file)
        if success:
            print(f"  {Colors.GREEN}✓{Colors.END} {msg}")
            removed_count += 1
        else:
            print(f"  {Colors.RED}✗{Colors.END} {msg}")
            failed_count += 1
    
    # 4. REMOVER DEEP KNOWLEDGE
    print(f"\n{Colors.YELLOW}4. Removendo deep_knowledge_test_output*.txt...{Colors.END}")
    dk_files = list(backend_path.glob("deep_knowledge_test_output*.txt"))
    for dk_file in dk_files:
        success, msg = safe_remove(dk_file)
        if success:
            print(f"  {Colors.GREEN}✓{Colors.END} {msg}")
            removed_count += 1
        else:
            print(f"  {Colors.RED}✗{Colors.END} {msg}")
            failed_count += 1
    
    # 5. REMOVER OUTROS TEMPORÁRIOS
    print(f"\n{Colors.YELLOW}5. Removendo outros arquivos temporários...{Colors.END}")
    temp_files = [
        "auth_flow_result.txt", "diagnostico_resultado.txt", 
        "diagnostico_supabase_completo.txt", "eoq_test.txt",
        "forecast_test.txt", "groups_test.txt", "suppliers_test.txt",
        "out.txt", "resultado_testes.txt", "test_db_results.txt",
        "login_test_result.txt", "import_trace.txt", "startup_log.txt",
        "error_log.txt", "warnings_log.txt", "warnings_log_2.txt",
        "warnings_log_3.txt", "table_structure.txt", "columns_list.txt",
        "groups_output.txt"
    ]
    
    for temp_file in temp_files:
        file_path = backend_path / temp_file
        if file_path.exists():
            success, msg = safe_remove(file_path)
            if success:
                print(f"  {Colors.GREEN}✓{Colors.END} {msg}")
                removed_count += 1
            else:
                print(f"  {Colors.RED}✗{Colors.END} {msg}")
                failed_count += 1
    
    # 6. MOVER TESTES OBSOLETOS
    print(f"\n{Colors.YELLOW}6. Movendo testes obsoletos para archive...{Colors.END}")
    archive_path = backend_path / "tests" / "archive" / "legacy"
    archive_path.mkdir(parents=True, exist_ok=True)
    
    test_files = list(backend_path.glob("test_*.py"))
    for test_file in test_files:
        dst = archive_path / test_file.name
        success, msg = safe_move(test_file, dst)
        if success:
            print(f"  {Colors.GREEN}✓{Colors.END} {msg}")
            moved_count += 1
        else:
            print(f"  {Colors.RED}✗{Colors.END} {msg}")
            failed_count += 1
    
    # 7. MOVER DEBUG SCRIPTS
    print(f"\n{Colors.YELLOW}7. Movendo scripts de debug para archive...{Colors.END}")
    debug_archive = backend_path / "scripts" / "debug_archive"
    debug_archive.mkdir(parents=True, exist_ok=True)
    
    debug_files = list(backend_path.glob("debug_*.py"))
    for debug_file in debug_files:
        dst = debug_archive / debug_file.name
        success, msg = safe_move(debug_file, dst)
        if success:
            print(f"  {Colors.GREEN}✓{Colors.END} {msg}")
            moved_count += 1
        else:
            print(f"  {Colors.RED}✗{Colors.END} {msg}")
            failed_count += 1
    
    # RESUMO
    print(f"\n{Colors.YELLOW}=== RESUMO ==={Colors.END}")
    print(f"  {Colors.GREEN}✓ Removidos:{Colors.END} {removed_count} arquivos")
    print(f"  {Colors.GREEN}✓ Movidos:{Colors.END} {moved_count} arquivos")
    if failed_count > 0:
        print(f"  {Colors.RED}✗ Falhas:{Colors.END} {failed_count} arquivos")
        print(f"\n{Colors.YELLOW}Dica:{Colors.END} Feche editores e pare o backend para liberar arquivos bloqueados.")
    else:
        print(f"\n{Colors.GREEN}✅ LIMPEZA COMPLETA COM SUCESSO!{Colors.END}")
    
    return failed_count == 0

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"{Colors.RED}ERRO FATAL: {str(e)}{Colors.END}")
        exit(1)
