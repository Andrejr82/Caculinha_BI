import asyncio
import logging
import sys
import os
import pandas as pd
import re
from typing import Dict, Any, List

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.chat_service_v3 import ChatServiceV3
from app.core.utils.session_manager import SessionManager
from app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter
from app.core.data_source_manager import get_data_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RealDataVerifier")

import uuid

# ... imports ...

class TruthContractVerifier:
    def __init__(self):
        self.duckdb = get_duckdb_adapter()
        self.session_manager = SessionManager(storage_dir="app/data/sessions_test")
        self.chat_service = ChatServiceV3(session_manager=self.session_manager)
        self.user_id = "tester_admin"
        self.session_id = str(uuid.uuid4())
        self.data_manager = get_data_manager()

    def get_ground_truth(self, sql_query: str) -> Any:
        """Executes raw SQL on DuckDB to get the absolute truth."""
        try:
            # Get path to parquet
            parquet_path = str(self.data_manager._source.file_path).replace("\\", "/")
            
            # Replace placeholder in SQL
            final_query = sql_query.replace("{parquet}", f"read_parquet('{parquet_path}')")
            
            df = self.duckdb.query(final_query)
            if df.empty:
                return None
            return df
        except Exception as e:
            logger.error(f"Failed to get ground truth: {e}")
            return None

    async def ask_agent(self, question: str) -> str:
        """Asks the agent and returns the full text response."""
        response = await self.chat_service.process_message(
            query=question,
            session_id=self.session_id,
            user_id=self.user_id
        )
        return response.get("result", {}).get("mensagem", "")

    def check_number_match(self, text: str, number: float, tolerance: float = 0.05) -> bool:
        """Checks if a number appears in the text (with formatting variations)."""
        # Create variations: 1000, 1.000, 1000.00, 1k, 1M
        import locale
        # locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8') # Might fail on some systems
        
        # Simple regex for finding numbers in text
        # Finds: 1.234,56 or 1,234.56 or 1234
        found_numbers = re.findall(r'[\d\.,]+', text)
        
        target = float(number)
        
        for num_str in found_numbers:
            try:
                # Clean string to float
                clean_str = num_str.replace('.', '').replace(',', '.')
                # Handle cases like 1.000.000,00 -> 1000000.00
                if clean_str.count('.') > 1: # Maybe it was 1.000.000
                     clean_str = num_str.replace('.', '')
                
                val = float(clean_str)
                
                # Check exact match or within tolerance
                if abs(val - target) <= (target * tolerance):
                    return True
                
                # Check if it's "Millions" (e.g. 3.74 M for 3,740,000)
                if abs(val * 1000000 - target) <= (target * tolerance):
                    return True
                 # Check if it's "Thousands" (e.g. 150 K for 150,000)
                if abs(val * 1000 - target) <= (target * tolerance):
                    return True

            except:
                continue
        
        return False

    async def verify_case(self, case_name: str, question: str, sql_query: str, metric_col: str):
        # Generate fresh session AND fresh service instance to avoid component state leak
        self.session_id = str(uuid.uuid4())
        # Re-init service to clear any internal state in QueryInterpreter
        self.chat_service = ChatServiceV3(session_manager=self.session_manager)
        
        logger.info(f"\n--- Running Case: {case_name} ---")
        logger.info(f"Question: {question}")
        
        # 1. Get Truth
        df_truth = self.get_ground_truth(sql_query)
        if df_truth is None or df_truth.empty:
            logger.warning("⚠️ SKIPPED: No data found in parquet for this case.")
            return
            
        truth_value = df_truth[metric_col].iloc[0]
        logger.info(f"Ground Truth ({metric_col}): {truth_value}")
        
        # 2. Get Agent Response
        agent_text = await self.ask_agent(question)
        logger.info(f"Agent Response: {agent_text[:200]}...")
        
        # 3. Verify
        is_correct = self.check_number_match(agent_text, float(truth_value))
        
        if is_correct:
            logger.info(f"✅ PASS: Found {truth_value} in narrative.")
        else:
            logger.error(f"❌ FAIL: Did not find {truth_value} in narrative.")
            logger.error(f"Full Text: {agent_text}")

async def run_tests():
    verifier = TruthContractVerifier()
    
    # CASE 1: Total Sales Global (Last 30 Days)
    await verifier.verify_case(
        case_name="Total Sales Global (30DD)",
        question="Qual o total de vendas nos últimos 30 dias?",
        sql_query="SELECT sum(VENDA_30DD) as val FROM {parquet}",
        metric_col="val"
    )

    # CASE 2: Store Specific
    # We first find a valid store ID to be safe
    df_store = verifier.get_ground_truth("SELECT UNE FROM {parquet} LIMIT 1")
    if df_store is not None and not df_store.empty:
        store_id = df_store['UNE'].iloc[0]
        await verifier.verify_case(
            case_name=f"Sales for Store {store_id} (30DD)",
            question=f"Quanto vendeu a loja {store_id} nos últimos 30 dias?",
            sql_query=f"SELECT sum(VENDA_30DD) as val FROM {{parquet}} WHERE UNE = {store_id}",
            metric_col="val"
        )
    
    # CASE 3: Segment Performance
    df_seg = verifier.get_ground_truth("SELECT NOMESEGMENTO, sum(VENDA_30DD) as val FROM {parquet} GROUP BY NOMESEGMENTO ORDER BY val DESC LIMIT 1")
    if df_seg is not None:
        best_seg = df_seg['NOMESEGMENTO'].iloc[0]
        best_val = df_seg['val'].iloc[0]
        
        # MANUALLY RESET SESSION FOR CASE 3 (Critical Fix)
        verifier.session_id = str(uuid.uuid4())
        verifier.chat_service = ChatServiceV3(session_manager=verifier.session_manager)
        
        logger.info(f"\n--- Running Case: Top Segment ({best_seg}) ---")
        agent_text = await verifier.ask_agent("Faça um ranking de vendas por segmento (geral)")
        
        if best_seg.lower() in agent_text.lower():
             logger.info(f"✅ PASS: Found segment '{best_seg}' in narrative.")
        else:
             logger.error(f"❌ FAIL: Expected '{best_seg}', got: {agent_text[:100]}...")
             
        if verifier.check_number_match(agent_text, float(best_val)):
             logger.info(f"✅ PASS: Found value {best_val} in narrative.")
        else:
             logger.warning(f"⚠️ WARNING: Did not find exact value {best_val} in narrative (might be rounded).")

if __name__ == "__main__":
    asyncio.run(run_tests())
