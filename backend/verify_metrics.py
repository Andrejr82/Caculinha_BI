import logging
import sys
import os
from pathlib import Path

# Add backend to sys.path
sys.path.append(str(Path(__file__).parent))

from app.services.metrics_calculator import MetricsCalculator

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test():
    try:
        print("Initializing MetricsCalculator...")
        calc = MetricsCalculator()
        
        print("Calculando vendas (simulação)...")
        # Simula query: "vendas do produto 123"
        result = calc.calculate(
            intent_type="vendas",
            entities={"produto": 59294}, # Produto do exemplo do user
            aggregations=["sum"],
            user_filters={}
        )
        
        print("RESULTADO:", result)
        print("SUCCESS")
        
    except Exception as e:
        print(f"FAILED: {e}")
        # Print full exception details if possible
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test())
