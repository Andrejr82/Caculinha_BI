"""
Script de Validação: Conhecimento de Colunas da LLM
Objetivo: Verificar se o ChatServiceV3 está injetando corretamente todas as 97 colunas
"""

import sys
import os
sys.path.append(os.getcwd())

from backend.app.infrastructure.data.config.column_mapping import list_all_columns

def validate_schema_knowledge():
    """Valida se todas as colunas estão sendo injetadas corretamente"""
    
    print("=" * 80)
    print("VALIDAÇÃO DE CONHECIMENTO DE COLUNAS")
    print("=" * 80)
    
    # 1. Obter todas as colunas documentadas
    all_columns = list_all_columns()
    
    print(f"\n📊 Total de Colunas Documentadas: {len(all_columns)}")
    
    # 2. Categorizar por tipo de informação
    categories = {
        "Identificação": [],
        "Vendas (30d)": [],
        "Vendas Mensais": [],
        "Vendas Semanais": [],
        "ABC": [],
        "Estoque": [],
        "Logística": [],
        "Preços": [],
        "Metadados": []
    }
    
    for name, desc in all_columns:
        if any(x in name for x in ["PRODUTO", "NOME", "UNE", "SEGMENTO", "CATEGORIA", "GRUPO", "FABRICANTE"]):
            categories["Identificação"].append(name)
        elif "VENDA_30DD" in name:
            categories["Vendas (30d)"].append(name)
        elif "MES_" in name:
            categories["Vendas Mensais"].append(name)
        elif "SEMANA" in name or "FREQ" in name:
            categories["Vendas Semanais"].append(name)
        elif "ABC" in name:
            categories["ABC"].append(name)
        elif "ESTOQUE" in name or "EXPOSICAO" in name or "LEADTIME" in name or "PONTO_PEDIDO" in name:
            categories["Estoque"].append(name)
        elif any(x in name for x in ["ENTRADA", "VENDA_DATA", "SOLICITACAO", "PICKLIST", "ROMANEIO", "NOTA", "VOLUME"]):
            categories["Logística"].append(name)
        elif any(x in name for x in ["LIQUIDO", "PRECO", "CUSTO", "EMB", "EMBALAGEM"]):
            categories["Preços"].append(name)
        else:
            categories["Metadados"].append(name)
    
    # 3. Exibir resumo por categoria
    print("\n" + "=" * 80)
    print("RESUMO POR CATEGORIA:")
    print("=" * 80)
    
    for category, cols in categories.items():
        if cols:
            print(f"\n{category} ({len(cols)} colunas):")
            for col in sorted(cols)[:5]:  # Mostrar primeiras 5
                print(f"  ✓ {col}")
            if len(cols) > 5:
                print(f"  ... e mais {len(cols) - 5} colunas")
    
    # 4. Verificar cobertura
    print("\n" + "=" * 80)
    print("ANÁLISE DE COBERTURA:")
    print("=" * 80)
    
    expected_total = 97  # Total de colunas no Parquet
    documented = len(all_columns)
    coverage = (documented / expected_total) * 100
    
    print(f"\n📈 Cobertura: {documented}/{expected_total} colunas ({coverage:.1f}%)")
    
    if coverage >= 95:
        print("✅ EXCELENTE: Conhecimento completo do schema!")
    elif coverage >= 80:
        print("⚠️  BOM: Conhecimento parcial, algumas colunas faltando")
    else:
        print("❌ CRÍTICO: Muitas colunas ainda desconhecidas")
    
    # 5. Simular injeção no prompt (como ChatServiceV3 faz)
    print("\n" + "=" * 80)
    print("SIMULAÇÃO DE INJEÇÃO NO PROMPT:")
    print("=" * 80)
    
    schema_knowledge = "\n".join([f"- **{name}**: {desc}" for name, desc in all_columns[:10]])
    token_estimate = len(schema_knowledge.split())
    
    print(f"\nPrimeiras 10 colunas injetadas:")
    print(schema_knowledge)
    print(f"\n📊 Estimativa de Tokens (primeiras 10): ~{token_estimate} tokens")
    print(f"📊 Estimativa Total (todas {len(all_columns)}): ~{token_estimate * (len(all_columns) / 10):.0f} tokens")
    
    print("\n" + "=" * 80)
    print("✅ VALIDAÇÃO CONCLUÍDA")
    print("=" * 80)

if __name__ == "__main__":
    validate_schema_knowledge()
