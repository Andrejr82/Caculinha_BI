import os
import datetime
from pathlib import Path

# Configuração
ROOT_DIR = Path(r"C:\\Agente_BI\\BI_Solution")
REPORT_FILE = ROOT_DIR / "RELATORIO_LIMPEZA_PROFUNDA.md"

# Listas de Padrões
KEEP_PATTERNS = [
    # Configs Essenciais
    "package.json", "tsconfig.json", "vite.config.ts", ".env", ".env.example",
    "requirements.txt", "pyproject.toml", "alembic.ini", "Taskfile.yml",
    ".gitignore", ".gitattributes", "CLAUDE.md", "README.md",
    
    # Código Fonte Core
    "*.py", "*.tsx", "*.ts", "*.js", "*.css", "*.html", "*.sql",
    
    # Dados Críticos
    "admmat.parquet", "users.parquet", "credentials.md"
]

DELETE_CANDIDATES = [
    # Logs e Temporários
    "*.log", "*.tmp", "*.bak", "*.old", "*.backup",
    "*.pyc", "__pycache__", ".pytest_cache",
    
    # Relatórios de Análise Gerados por Agentes (Auto-referência)
    "analise_projeto.json", "analise_projeto_detalhada.json",
    "RELATORIO_LIMPEZA_*.json", "RELATORIO_LIMPEZA_*.md",
    "DEEP_CLEAN_REPORT.md",
    
    # Scripts de Teste "Sujos" na Raiz (Spaghetti)
    "test_*.py", # Apenas na raiz, não em tests/
    
    # Docs Obsoletos Específicos
    "*_FIX_*.md", "*_SUMMARY.md", "ASYNC_RAG_IMPLEMENTATION.md",
    "QUICK_START_MODERNIZATION.md"
]

IGNORE_DIRS = [
    ".git", "node_modules", ".venv", "venv", "__pycache__", 
    ".idea", ".vscode", "dist", "build", "coverage", 
    "BACKUP_LIMPEZA_*" # Ignorar backups já feitos
]

def get_file_status(file_path, root_path):
    rel_path = file_path.relative_to(root_path)
    parts = rel_path.parts
    filename = file_path.name
    
    # 1. Ignorar diretórios protegidos
    if any(ignore in parts for ignore in IGNORE_DIRS):
        return "IGNORADO"
    
    # 2. Analisar Raiz
    if len(parts) == 1: # Arquivo na raiz
        if filename in ["deep_analyze.py", "cleanup.bat", "restore.bat", "start.bat"]:
             return "MANTER (Ferramenta)"
        
        if filename.startswith("test_") or filename.startswith("analyze_"):
            return "SUGERIR EXCLUSÃO (Script Temporário)"
            
        if filename.endswith(".json") and "analise" in filename:
             return "SUGERIR EXCLUSÃO (Artefato de Análise)"

    # 3. Analisar Docs
    if "docs" in parts:
        if "archive" in parts:
             return "MANTER (Já Arquivado)"
        if filename.startswith("RELATORIO_") or "FIX" in filename:
             return "AVALIAR (Relatório Antigo?)"

    # 4. Analisar Logs
    if file_path.suffix == ".log":
        return "SUGERIR EXCLUSÃO (Log)"

    # 5. Analisar Dados
    if "data" in parts:
        if "cache" in parts or "sessions" in parts:
             if filename.startswith("test-") or "cache-test" in filename:
                 return "SUGERIR EXCLUSÃO (Sessão de Teste)"
    
    # Padrão: Manter Código Fonte
    if file_path.suffix in [".py", ".ts", ".tsx", ".js", ".css"]:
        return "MANTER (Código Fonte)"

    return "MANTER (Padrão)"

def generate_deep_report():
    report_lines = []
    report_lines.append(f"# Relatório de Análise Profunda do Projeto")
    report_lines.append(f"**Data:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report_lines.append(f"**Diretório:** `{ROOT_DIR}`")
    report_lines.append("\n---\n")

    files_to_review = []
    files_to_delete = []
    
    total_size_delete = 0

    for root, dirs, files in os.walk(ROOT_DIR):
        # Modificar dirs in-place para ignorar
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith("BACKUP_LIMPEZA")]
        
        for file in files:
            file_path = Path(root) / file
            status = get_file_status(file_path, ROOT_DIR)
            
            if "SUGERIR EXCLUSÃO" in status or "AVALIAR" in status:
                size = file_path.stat().st_size
                entry = {
                    "path": str(file_path.relative_to(ROOT_DIR)),
                    "status": status,
                    "size": size
                }
                
                if "SUGERIR EXCLUSÃO" in status:
                    files_to_delete.append(entry)
                    total_size_delete += size
                else:
                    files_to_review.append(entry)

    # Seção: Sugestão de Exclusão
    report_lines.append(f"## 🗑️ Sugestão de Exclusão (Seguro)")
    report_lines.append(f"**Total:** {len(files_to_delete)} arquivos | **Espaço Recuperável:** {total_size_delete / 1024 / 1024:.2f} MB")
    report_lines.append("\n| Arquivo | Motivo |")
    report_lines.append("|---|---|")
    
    for item in sorted(files_to_delete, key=lambda x: x['path']):
        report_lines.append(f"| `{item['path']}` | {item['status'].replace('SUGERIR EXCLUSÃO ', '')} | {item['size']/1024:.1f} KB |")

    # Seção: Avaliação
    report_lines.append(f"\n## ⚠️ Requer Avaliação Manual")
    report_lines.append("Arquivos que parecem antigos ou deslocados, mas requerem sua confirmação.")
    report_lines.append("\n| Arquivo | Dúvida |")
    report_lines.append("|---|---|")
    
    for item in sorted(files_to_review, key=lambda x: x['path']):
        report_lines.append(f"| `{item['path']}` | {item['status']} |")

    # Escrever Relatório
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    
    print(f"Análise completa. Relatório gerado em: {REPORT_FILE}")

if __name__ == "__main__":
    generate_deep_report()
