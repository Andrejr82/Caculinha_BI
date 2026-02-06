"""
Script de Reprodução: Verificar quantas UNEs têm o produto 369947
Fase 1 do Debugger: REPRODUÇÃO
"""
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "backend"))

from app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter

def verify_product_coverage():
    print("=== FASE 1: REPRODUÇÃO - Verificando Produto 369947 ===\n")
    
    adapter = get_duckdb_adapter()
    
    # Query 1: Quantas UNEs têm o produto?
    print("1. Verificando quantas UNEs têm o produto 369947...")
    query1 = """
    SELECT 
        COUNT(DISTINCT UNE) as total_unes,
        COUNT(*) as total_registros
    FROM read_parquet('data/parquet/admmat.parquet')
    WHERE PRODUTO = 369947
    """
    
    result1 = adapter.query(query1)
    print(f"   Total de UNEs: {result1['total_unes'][0]}")
    print(f"   Total de registros: {result1['total_registros'][0]}\n")
    
    # Query 2: Listar todas as UNEs com vendas
    print("2. Listando UNEs com vendas do produto 369947...")
    query2 = """
    SELECT 
        UNE,
        UNE_NOME,
        VENDA_30DD,
        ESTOQUE_UNE
    FROM read_parquet('data/parquet/admmat.parquet')
    WHERE PRODUTO = 369947
      AND VENDA_30DD > 0
    ORDER BY VENDA_30DD DESC
    """
    
    result2 = adapter.query(query2)
    print(f"   UNEs com vendas: {len(result2)}")
    print("\n   Top 15 UNEs por vendas:")
    print(result2.head(15).to_string(index=False))
    
    # Query 3: Verificar se há limite de 9 em algum lugar
    print("\n3. Verificando se há exatamente 9 UNEs com vendas significativas...")
    query3 = """
    SELECT 
        COUNT(*) as unes_com_vendas
    FROM read_parquet('data/parquet/admmat.parquet')
    WHERE PRODUTO = 369947
      AND VENDA_30DD > 0
    """
    
    result3 = adapter.query(query3)
    print(f"   UNEs com vendas > 0: {result3['unes_com_vendas'][0]}")
    
    # Conclusão
    print("\n=== CONCLUSÃO DA FASE 1 ===")
    total_unes = result1['total_unes'][0]
    unes_com_vendas = result3['unes_com_vendas'][0]
    
    if unes_com_vendas == 9:
        print(f"✅ CORRETO: Existem exatamente {unes_com_vendas} UNEs com vendas.")
        print("   O gráfico está mostrando TODAS as lojas com vendas.")
        print("   NÃO É UM BUG - é o comportamento esperado.")
    elif unes_com_vendas > 9:
        print(f"❌ BUG CONFIRMADO: Existem {unes_com_vendas} UNEs com vendas,")
        print(f"   mas o gráfico mostrou apenas 9.")
        print(f"   Faltam {unes_com_vendas - 9} UNEs no gráfico!")
    else:
        print(f"⚠️ ATENÇÃO: Existem apenas {unes_com_vendas} UNEs com vendas,")
        print("   mas o gráfico mostrou 9. Pode estar incluindo UNEs sem vendas.")

if __name__ == "__main__":
    verify_product_coverage()
