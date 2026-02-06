import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.data_source_manager import get_data_manager
from app.infrastructure.data.config.column_mapping import list_all_columns, COLUMN_INFO
from app.core.prompts.master_prompt import MASTER_PROMPT

def diagnose():
    print("=== DIAGNOSIS: AGENT DATABASE KNOWLEDGE ===\n")

    # 1. Check Real Columns from Parquet
    print("1. Checking Real Parquet Columns (via DataSourceManager)...")
    try:
        manager = get_data_manager()
        real_columns = manager.get_columns()
        print(f"[OK] Found {len(real_columns)} columns in Parquet.")
        print(f"    Sample: {real_columns[:5]}...")
    except Exception as e:
        print(f"[ERROR] Failed to get real columns: {e}")
        return

    # 2. Check Mapped Columns
    print("\n2. Checking Mapped Columns (column_mapping.py)...")
    try:
        mapped_columns = [col for col, _ in list_all_columns()]
        print(f"[OK] Found {len(mapped_columns)} columns in Mapping.")
        print(f"    Sample: {mapped_columns[:5]}...")
    except Exception as e:
        print(f"[ERROR] Failed to get mapped columns: {e}")
        return

    # 3. Compare
    real_set = set([c.upper() for c in real_columns])
    mapped_set = set([c.upper() for c in mapped_columns])
    
    missing_in_map = real_set - mapped_set
    missing_in_parquet = mapped_set - real_set
    
    print("\n3. Comparison:")
    if missing_in_map:
        print(f"    [WARNING] {len(missing_in_map)} columns in Parquet but NOT in Mapping:")
        print(f"    {list(missing_in_map)[:10]}...")
    else:
        print("    [OK] All Parquet columns are mapped.")

    if missing_in_parquet:
        print(f"    [WARNING] {len(missing_in_parquet)} columns in Mapping but NOT in Parquet:")
        print(f"    {list(missing_in_parquet)[:10]}...")
    else:
        print("    [OK] All Mapped columns exist in Parquet.")

    # 4. Simulate Prompt Injection
    print("\n4. Simulating Dynamic Prompt Injection (CaculinhaBIAgent logic)...")
    try:
        cols = real_columns
        important_keywords = ['PRODUTO', 'NOME', 'UNE', 'SEGMENTO', 'CATEGORIA', 'VENDA', 'ESTOQUE', 'PRECO', 'CUSTO', 'LIQUIDO', 'MARGEM', 'FABRICANTE']
        priority_cols = [c for c in cols if any(k in c.upper() for k in important_keywords)]
        other_cols = [c for c in cols if c not in priority_cols]
        
        schema_str = "**Colunas Prioritárias (Use estas preferencialmente):**\n"
        schema_str += ", ".join([f"`{c}`" for c in priority_cols])
        schema_str += "\n\n**Outras Colunas Disponíveis:**\n"
        schema_str += ", ".join([f"`{c}`" for c in other_cols[:30]])
        
        print(f"\n[INJECTED SCHEMA PREVIEW]:\n{schema_str[:500]}...")
        
        if len(priority_cols) == 0:
            print("\n[CRITICAL ERROR] No priority columns found! The keyword matching is failing.")
        else:
            print(f"\n[OK] Found {len(priority_cols)} priority columns for injection.")

    except Exception as e:
        print(f"[ERROR] Prompt simulation failed: {e}")

if __name__ == "__main__":
    diagnose()
