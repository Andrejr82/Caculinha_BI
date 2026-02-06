from app.core.llm_mock import MockLLM
from langchain_core.messages import ToolMessage

def test_null_crash():
    print("Testing MockLLM with 'null' tool output...")
    mock = MockLLM()
    
    # Simulate a tool returning "null" JSON
    # This parses to Python None.
    # If code does data.get(...), it will crash.
    msg = ToolMessage(content="null", tool_call_id="123")
    
    try:
        response = mock.invoke([msg])
        print("✅ SUCCESS: MockLLM handled 'null' without crashing.")
        print(f"Output: {response.content}")
    except AttributeError as e:
        print(f"❌ CRASH CONFIRMED: {e}")
    except Exception as e:
        print(f"❌ OTHER CRASH: {e}")

if __name__ == "__main__":
    test_null_crash()
