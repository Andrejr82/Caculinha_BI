import asyncio
import logging
import traceback
import uuid
from app.config.settings import settings

# Force Mock
settings.LLM_PROVIDER = "mock"

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_flow():
    print("🚀 Starting Debug Flow for Messy Query")
    
    try:
        from app.services.chat_service_v2 import ChatServiceV2
        from app.core.utils.session_manager import SessionManager
        
        session_manager = SessionManager(storage_dir="app/data/sessions")
        service = ChatServiceV2(session_manager=session_manager)
        
        # Simulate Endpoint
        # query = "Gráfico de vendas do produto 369947 em todas as lojas"
        query = "gere gráfico de rankig de venddas segmentos na une 2365"
        session_id = str(uuid.uuid4()) # Valid UUID
        user_id = "debug-user"
        
        print(f"👉 Processing message via ChatServiceV2...")
        try:
            response = await service.process_message(query, session_id, user_id)
            print(f"✅ Service returned type: {type(response)}")
            print(f"✅ Response content keys: {response.keys() if isinstance(response, dict) else 'Not Dict'}")
            
            result_data = response.get("result", {})
            print(f"✅ Result Data Type: {type(result_data)}")
            
            if isinstance(result_data, dict):
                print("✅ Result Data is Dict. Attempting .get('chart_spec')...")
                spec = result_data.get("chart_spec")
                print(f"✅ Chart Spec found: {spec is not None}")
                
        except Exception as e:
            print("❌ CRASH INSIDE SERVICE:")
            traceback.print_exc()
            
    except Exception as e:
        print("❌ CRASH DURING SETUP:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_flow())
