"""
Teste de filtragem por segmento no DataAggregationService
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

async def test_segment_filtering():
    print("\n=== TESTE DE FILTRAGEM POR SEGMENTO ===\n")
    
    try:
        from app.services.data_aggregation import DataAggregationService
        
        # 1. Testar sem filtro (Global)
        print("[1/3] Consultando Global (sem filtro)...")
        global_data = DataAggregationService.get_retail_summary()
        sales_global = global_data['general_stats']['total_sales_30d']
        print(f"   Vendas Globais: {sales_global:,.2f}")
        
        if sales_global == 0:
            print("   [ALERTA] Vendas globais zeradas. Verifique parquet.")
            
        # 2. Testar com filtro de segmento existente (Ex: 'PAPELARIA' - ajuste conforme seus dados)
        # Vamos primeiro descobrir um segmento que existe
        from app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter
        adapter = get_duckdb_adapter()
        segments_df = adapter.query_arrow("SELECT DISTINCT NOMESEGMENTO FROM read_parquet('data/parquet/admmat.parquet') LIMIT 5").read_all().to_pylist()
        valid_segments = [row['NOMESEGMENTO'] for row in segments_df if row['NOMESEGMENTO']]
        
        if not valid_segments:
            print("   [ERRO] Não foi possível encontrar segmentos no arquivo.")
            return False
            
        target_segment = valid_segments[0]
        print(f"\n[2/3] Consultando Segmento '{target_segment}'...")
        
        segment_data = DataAggregationService.get_retail_summary(filters={"segments": [target_segment]})
        sales_segment = segment_data['general_stats']['total_sales_30d']
        print(f"   Vendas Segmento '{target_segment}': {sales_segment:,.2f}")
        
        if sales_segment > sales_global:
            print("   [ERRO] Vendas do segmento maiores que global! Lógica invertida?")
            return False
            
        if sales_segment == 0:
             print(f"   [AVISO] Vendas do segmento '{target_segment}' estão zeradas.")

        # 3. Testar com filtro INEXISTENTE
        fake_segment = "SEGMENTO_FANTASMA_XYZ_123"
        print(f"\n[3/3] Consultando Segmento Inexistente '{fake_segment}'...")
        empty_data = DataAggregationService.get_retail_summary(filters={"segments": [fake_segment]})
        sales_empty = empty_data['general_stats']['total_sales_30d']
        print(f"   Vendas Segmento Inexistente: {sales_empty}")
        
        if sales_empty != 0:
            print(f"   [ERRO] Deveria ser 0, mas retornou {sales_empty}")
            return False
            
        print("\n=== CONCLUSÃO: FILTRAGEM FUNCIONANDO CORRETAMENTE ===")
        return True

    except Exception as e:
        print(f"\n[ERRO FATAL] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_segment_filtering())
