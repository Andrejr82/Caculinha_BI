import polars as pl
from pathlib import Path

# Ler Parquet
parquet_path = Path("data/parquet/users.parquet")
df = pl.read_parquet(parquet_path)

# Verificar admin
admin = df.filter(pl.col('username') == 'admin')

print("\n=== VERIFICANDO ADMIN ===")
if len(admin) == 0:
    print("❌ Admin NÃO ENCONTRADO!")
else:
    admin_data = admin.row(0, named=True)
    print(f"Username: {admin_data['username']}")
    print(f"Role: {admin_data['role']}")
    print(f"Allowed Segments: {admin_data['allowed_segments']}")

    # Verificar se precisa corrigir
    if admin_data['role'] != 'admin':
        print(f"\n🚨 PROBLEMA ENCONTRADO: role='{admin_data['role']}' (deveria ser 'admin')")
        print("Corrigindo...")

        # Corrigir role para admin
        df = df.with_columns(
            pl.when(pl.col('username') == 'admin')
            .then(pl.lit('admin'))
            .otherwise(pl.col('role'))
            .alias('role')
        )

        # Garantir allowed_segments = ["*"]
        df = df.with_columns(
            pl.when(pl.col('username') == 'admin')
            .then(pl.lit('["*"]'))
            .otherwise(pl.col('allowed_segments'))
            .alias('allowed_segments')
        )

        # Salvar
        df.write_parquet(parquet_path)
        print("✅ CORRIGIDO! Admin agora tem role='admin' e allowed_segments='[\"*\"]'")

        # Verificar
        df_new = pl.read_parquet(parquet_path)
        admin_new = df_new.filter(pl.col('username') == 'admin')
        admin_new_data = admin_new.row(0, named=True)
        print(f"\nVERIFICAÇÃO PÓS-CORREÇÃO:")
        print(f"Role: {admin_new_data['role']}")
        print(f"Allowed Segments: {admin_new_data['allowed_segments']}")
    else:
        print("\n✅ Admin já está correto!")
        print(f"Role: {admin_data['role']}")
        print(f"Allowed Segments: {admin_data['allowed_segments']}")
