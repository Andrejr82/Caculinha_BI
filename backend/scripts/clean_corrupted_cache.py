"""
Script para limpar cache semantic corrompido com erros "Maximum conversation turns exceeded"
"""

import json
import os
from pathlib import Path

def clean_corrupted_cache():
    """Remove arquivos de cache que contem erros de max turns"""
    cache_dir = Path("data/cache/semantic")

    if not cache_dir.exists():
        print(f"Diretorio de cache nao encontrado: {cache_dir}")
        return

    corrupted_files = []
    total_files = 0

    for cache_file in cache_dir.glob("*.json"):
        total_files += 1
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Verificar se contem erro de max turns
            if isinstance(data, dict):
                result = data.get('result', '')
                if 'Maximum conversation turns exceeded' in str(result):
                    corrupted_files.append(cache_file)
                    print(f"[CORRUPTED] {cache_file.name}")
        except Exception as e:
            print(f"[ERROR] Erro ao ler {cache_file.name}: {e}")

    print(f"\n=== RESUMO ===")
    print(f"Total de arquivos: {total_files}")
    print(f"Arquivos corrompidos: {len(corrupted_files)}")

    if corrupted_files:
        print(f"\nRemovendo {len(corrupted_files)} arquivos corrompidos...")
        for cache_file in corrupted_files:
            cache_file.unlink()
            print(f"[DELETED] {cache_file.name}")
        print(f"\n{len(corrupted_files)} arquivos removidos com sucesso!")
    else:
        print("Nenhum arquivo corrompido encontrado!")

if __name__ == "__main__":
    clean_corrupted_cache()
