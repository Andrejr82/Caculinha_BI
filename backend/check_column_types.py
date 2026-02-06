import duckdb

conn = duckdb.connect()

# Verificar tipos das colunas criticas
cols_to_check = ['VENDA_30DD', 'ESTOQUE_UNE', 'LIQUIDO_38', 'ULTIMA_ENTRADA_CUSTO_CD']

result = conn.execute("DESCRIBE SELECT * FROM read_parquet('data/parquet/admmat.parquet')").fetchall()

print("\nTipos das colunas criticas:")
print("="*60)
for col in result:
    if col[0] in cols_to_check:
        print(f"{col[0]:<30} {col[1]}")
print("="*60)

# Testar uma query simples
print("\nTestando query simples...")
try:
    test_result = conn.execute("""
        SELECT PRODUTO, NOME, VENDA_30DD, ESTOQUE_UNE
        FROM read_parquet('data/parquet/admmat.parquet')
        WHERE TRY_CAST(VENDA_30DD AS DOUBLE) > 0
        LIMIT 5
    """).fetchall()
    print("OK - Query funcionou!")
    for row in test_result:
        print(f"  {row}")
except Exception as e:
    print(f"ERRO: {e}")
