import duckdb

conn = duckdb.connect()

# Colunas que o DataAggregationService tenta usar
required_cols = ['CODIGO', 'DESCRICAO', 'NOMESEGMENTO', 'VENDA_30DD', 'ESTOQUE_UNE', 'LIQUIDO_38', 'ULTIMA_ENTRADA_CUSTO_CD']

# Pegar todas as colunas do parquet
result = conn.execute("DESCRIBE SELECT * FROM read_parquet('data/parquet/admmat.parquet')").fetchall()
available_cols = [col[0] for col in result]

print("\nVerificando colunas necessarias:")
print("="*60)
for col in required_cols:
    exists = col in available_cols
    status = "OK" if exists else "FALTANDO"
    print(f"{col:<30} [{status}]")

print("\n" + "="*60)
print(f"\nTotal de colunas disponiveis: {len(available_cols)}")
print("\nPrimeiras 20 colunas disponiveis:")
for col in available_cols[:20]:
    print(f"  - {col}")
