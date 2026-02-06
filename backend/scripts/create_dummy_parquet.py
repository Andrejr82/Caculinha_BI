import polars as pl
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import random

def create_dummy_data():
    print("Generating dummy data for Analytics Dashboard...")
    
    # Configuration matches settings.ALLOWED_UNES
    # Using a subset of allowed UNEs to ensure visibility
    allowed_unes = [1, 3, 11, 35, 57] 
    
    n_rows = 500
    
    # Products
    products = [
        (101, "Smartphone Galaxy S24", "Eletrônicos", "Telefonia"),
        (102, "iPhone 15 Pro", "Eletrônicos", "Telefonia"),
        (103, "Notebook Dell XPS", "Informática", "Computadores"),
        (104, "Monitor LG 27", "Informática", "Periféricos"),
        (105, "Cadeira Gamer", "Móveis", "Escritório"),
        (106, "Mesa de Escritório", "Móveis", "Escritório"),
        (107, "Smart TV 55 4K", "Eletrônicos", "TV e Vídeo"),
        (108, "Fone Bluetooth Sony", "Áudio", "Acessórios"),
    ]
    
    data = []
    
    for i in range(n_rows):
        prod = random.choice(products)
        une = random.choice(allowed_unes)
        
        # Random sales figures
        venda_30_d = round(random.uniform(0, 50000), 2)
        mes_01 = venda_30_d * random.uniform(0.8, 1.2) # Proxies
        mes_02 = mes_01 * random.uniform(0.8, 1.2)
        
        # Stock
        estoque_lojas = int(random.uniform(0, 50))
        estoque_cd = int(random.uniform(0, 200))
        
        row = {
            "id": str(i),
            "une": une,
            "codigo": prod[0],
            "tipo": "Normal",
            "une_nome": f"Loja {une}",
            "nome_produto": prod[1],
            "embalagem": "UN",
            "nomesegmento": prod[2],
            "nomecategoria": prod[3],
            "nomegrupo": prod[3], # Using same as category for simplicity
            "nomesubgrupo": "Geral",
            "nomefabricante": "Generic Brand",
            "ean": f"789{i:010d}",
            "promocional": random.choice(["S", "N"]),
            "foralinha": "N",
            "venda_30_d": venda_30_d,
            "estoque_atual": estoque_lojas + estoque_cd,
            "estoque_cd": estoque_cd,
            "estoque_lojas": estoque_lojas,
            "abc_une_mes_04": "A",
            "abc_une_mes_03": "A",
            "abc_une_mes_02": "A",
            "abc_une_mes_01": "A",
            "abc_une_30_dd": "A",
            "MES_01": mes_01, # Adding these for metric calc proxies if needed
            "MES_02": mes_02,
            "QTDE_SEMANA_ATUAL": random.randint(1, 100),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        data.append(row)
        
    df = pl.DataFrame(data)
    
    # Cast explicit types to match expected schema if needed, but Polars infers well
    # Ensure numericals are float where expected
    df = df.with_columns([
        pl.col("venda_30_d").cast(pl.Float64),
        pl.col("estoque_cd").cast(pl.Float64),
        pl.col("estoque_lojas").cast(pl.Float64),
        pl.col("une").cast(pl.Int64),
        pl.col("codigo").cast(pl.Int64),
    ])

    # Save to paths
    paths = [
        Path("backend/app/data/parquet/admmat.parquet"),
        Path("data/parquet/admmat.parquet")
    ]

    for p in paths:
        # Create directory if not exists
        if not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            
        df.write_parquet(p)
        print(f"✅ Successfully wrote {len(df)} rows to: {p}")
        
        # Verify schema
        print("Schema wrote:")
        print(df.schema)

if __name__ == "__main__":
    create_dummy_data()