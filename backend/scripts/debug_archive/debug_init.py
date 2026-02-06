import asyncio
import sys
import logging
import os

# Configure basic logging to console
logging.basicConfig(level=logging.DEBUG)

# Add parent dir to path
sys.path.append(os.getcwd())

async def test_init():
    import sys
    print("🚀 Starting Debug Initialization...", file=sys.stderr)
    
    # Trace imports
    # def trace_imports(frame, event, arg):
    #     if event == 'call': return None
    #     if event == 'line': return None
    #     return None
    
    try:
        print("📦 Importing ChatServiceV3...", file=sys.stderr)
        from app.services.chat_service_v3 import ChatServiceV3
        
        print("📦 Importing successful. Initializing SessionManager...", file=sys.stderr)
        from app.core.utils.session_manager import SessionManager
        sm = SessionManager(storage_dir="app/data/sessions")
        
        print("📦 Initializing ChatServiceV3...", file=sys.stderr)
        service = ChatServiceV3(session_manager=sm)
        
        print(f"✅ Success! Service initialized: {service}", file=sys.stderr)
        print(f"✅ Agent type: {type(service.agent)}", file=sys.stderr)
        
    except Exception as e:
        print(f"\n❌ CRASH DURING INIT: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_init())
