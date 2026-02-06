"""
Script para remover emojis dos logs que causam UnicodeEncodeError no Windows.
"""
import re
from pathlib import Path

# Emojis comuns em logs
EMOJI_PATTERN = r'[✅❌🔴🔧⚠️🎯🔍💡📊🚀⏰🔄]'

def remove_emojis_from_file(file_path: Path):
    """Remove emojis de um arquivo Python."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Substituir emojis por texto equivalente
        replacements = {
            '✅': '[OK]',
            '❌': '[ERROR]',
            '🔴': '[DEBUG]',
            '🔧': '[DEBUG]',
            '⚠️': '[WARNING]',
            '🎯': '[INFO]',
            '🔍': '[SEARCH]',
            '💡': '[TIP]',
            '📊': '[DATA]',
            '🚀': '[START]',
            '⏰': '[TIME]',
            '🔄': '[RETRY]',
        }
        
        for emoji, replacement in replacements.items():
            content = content.replace(emoji, replacement)
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            print(f"✓ Corrigido: {file_path.name}")
            return True
        return False
    except Exception as e:
        print(f"✗ Erro em {file_path}: {e}")
        return False

def main():
    """Remove emojis de todos os arquivos Python no backend."""
    backend_path = Path("backend/app")
    
    if not backend_path.exists():
        print(f"Erro: {backend_path} não encontrado!")
        return
    
    python_files = list(backend_path.rglob("*.py"))
    print(f"Encontrados {len(python_files)} arquivos Python")
    print(f"Removendo emojis...\n")
    
    fixed_count = 0
    for file_path in python_files:
        if remove_emojis_from_file(file_path):
            fixed_count += 1
    
    print(f"\n{'='*60}")
    print(f"Concluído! {fixed_count} arquivos corrigidos.")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
