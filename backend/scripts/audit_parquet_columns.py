"""
Script de Auditoria: Colunas do Parquet vs Conhecimento da LLM
Objetivo: Garantir que todas as colunas do admmat.parquet sejam conhecidas pelo sistema
"""

import duckdb
import json

PARQUET_PATH = r"C:\Agente_BI\BI_Solution\backend\data\parquet\admmat.parquet"

def audit_columns():
    """Extrai todas as colunas do parquet e suas características"""
    try:
        conn = duckdb.connect()
        
        # 1. Obter schema completo
        print("=" * 80)
        print("AUDITORIA DE COLUNAS - admmat.parquet")
        print("=" * 80)
        
        schema_query = f"DESCRIBE SELECT * FROM read_parquet('{PARQUET_PATH}')"
        schema = conn.execute(schema_query).fetchall()
        
        print(f"\n📊 Total de Colunas: {len(schema)}\n")
        
        # 2. Listar todas as colunas com tipos
        print("LISTA COMPLETA DE COLUNAS:")
        print("-" * 80)
        
        columns_info = []
        for row in schema:
            # DuckDB DESCRIBE retorna: (column_name, column_type, null, key, default, extra)
            col_name = row[0]
            col_type = row[1]
            null_info = row[2] if len(row) > 2 else "UNKNOWN"
            
            columns_info.append({
                "nome": col_name,
                "tipo": col_type,
                "nullable": null_info
            })
            print(f"  {col_name:<40} | {col_type:<20} | {null_info}")
        
        # 3. Salvar em JSON para referência
        output_file = "C:/Agente_BI/BI_Solution/backend/data/parquet_schema_audit.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(columns_info, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Schema salvo em: {output_file}")
        
        # 4. Categorizar colunas por tipo
        print("\n" + "=" * 80)
        print("CATEGORIZAÇÃO POR TIPO:")
        print("-" * 80)
        
        type_groups = {}
        for col in columns_info:
            tipo = col["tipo"]
            if tipo not in type_groups:
                type_groups[tipo] = []
            type_groups[tipo].append(col["nome"])
        
        for tipo, colunas in sorted(type_groups.items()):
            print(f"\n{tipo} ({len(colunas)} colunas):")
            for col in colunas[:10]:  # Mostrar primeiras 10
                print(f"  - {col}")
            if len(colunas) > 10:
                print(f"  ... e mais {len(colunas) - 10} colunas")
        
        # 5. Identificar colunas críticas (com base em nomes comuns)
        print("\n" + "=" * 80)
        print("COLUNAS CRÍTICAS IDENTIFICADAS:")
        print("-" * 80)
        
        critical_keywords = ['PRODUTO', 'NOME', 'UNE', 'VENDA', 'ESTOQUE', 'PRECO', 'CUSTO', 
                            'SEGMENTO', 'CATEGORIA', 'GRUPO', 'FABRICANTE', 'MARGEM']
        
        critical_cols = []
        for col in columns_info:
            if any(keyword in col["nome"].upper() for keyword in critical_keywords):
                critical_cols.append(col["nome"])
        
        print(f"\nTotal de colunas críticas: {len(critical_cols)}")
        for col in sorted(critical_cols):
            print(f"  ✓ {col}")
        
        return columns_info
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    audit_columns()
