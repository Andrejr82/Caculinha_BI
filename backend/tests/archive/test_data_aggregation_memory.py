import sys
import os
import json
import logging

# Adicionar o diretório atual ao path para importação
sys.path.append(os.getcwd())

from app.services.data_aggregation import DataAggregationService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_aggregation():
    logger.info("Iniciando teste de agregação de dados (Memory Safe)...")
    
    try:
        summary = DataAggregationService.get_retail_summary(limit_items=5)
        
        if "error" in summary:
            logger.error(f"❌ Erro retornado pelo serviço: {summary['error']}")
            return False
            
        stats = summary.get("general_stats", {})
        top_sales = summary.get("top_performing_products", [])
        
        logger.info(f"✅ Sucesso! Resumo gerado.")
        logger.info(f"   Total Vendas: {stats.get('total_sales_30d', 0):,.2f}")
        logger.info(f"   Total Estoque: {stats.get('total_stock_units', 0):,.2f}")
        logger.info(f"   Top Vendas (qtd): {len(top_sales)}")
        
        if top_sales:
            logger.info(f"   Top 1 Produto: {top_sales[0].get('DESCRICAO')} (Venda: {top_sales[0].get('VENDA_30DD')})")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Exceção não tratada: {e}")
        return False

if __name__ == "__main__":
    success = test_aggregation()
    sys.exit(0 if success else 1)
