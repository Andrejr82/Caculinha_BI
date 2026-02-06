import asyncio
import logging
import sys
from app.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_gemini():
    print(f"🔧 CONFIG CHECK:")
    print(f"   Provider: {settings.LLM_PROVIDER}")
    print(f"   Model:    {settings.LLM_MODEL_NAME}")
    print(f"   Parquet:  {settings.PARQUET_DATA_PATH}")
    
    if settings.LLM_PROVIDER != "google":
        print("❌ Error: Provider is not google! Check .env update.")
        return

    print("\n🚀 INITIALIZING AGENT (Gemini)...")
    try:
        from app.services.chat_service_v2 import ChatServiceV2
        from app.core.utils.session_manager import SessionManager
        import uuid
        
        session_mgr = SessionManager("app/data/sessions")
        service = ChatServiceV2(session_mgr)
        
        query = "Qual é o produto mais vendido com base no arquivo admmat?"
        print(f"\n❓ QUERY: {query}")
        
        response = await service.process_message(
            query=query,
            session_id=str(uuid.uuid4()),
            user_id="test-admin"
        )
        
        print("\n✅ RESPONSE RECEIVED:")
        if isinstance(response, dict) and "result" in response:
            print(f"   {response['result']}")
        else:
            print(f"   {response}")
            
    except Exception as e:
        print(f"\n❌ CRASH: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gemini())
