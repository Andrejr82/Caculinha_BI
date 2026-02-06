
import pytest
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from app.orchestration.graph import check_safety

def test_no_tool_calls():
    state = {"messages": [HumanMessage(content="Hello")]}
    assert check_safety(state) == "__end__"

def test_normal_tool_call():
    state = {"messages": [AIMessage(content="Calling tool", tool_calls=[{"name": "test", "args": {}, "id": "1"}])]}
    assert check_safety(state) == "tools"

def test_loop_detected_first_time():
    # Simulate 3 identical calls
    call = {"name": "test", "args": {"q": "foo"}, "id": "1"}
    msgs = [
        AIMessage(content="1", tool_calls=[call]),
        ToolMessage(content="res", tool_call_id="1"),
        AIMessage(content="2", tool_calls=[call]),
        ToolMessage(content="res", tool_call_id="1"),
        AIMessage(content="3", tool_calls=[call]) # 3rd time
    ]
    state = {"messages": msgs}
    
    # Should trigger feedback, NOT abort
    assert check_safety(state) == "loop_feedback"

def test_loop_detected_after_feedback():
    # Simulate loop -> feedback -> loop again
    call = {"name": "test", "args": {"q": "foo"}, "id": "1"}
    msgs = [
        AIMessage(content="1", tool_calls=[call]),
        ToolMessage(content="res", tool_call_id="1"),
        AIMessage(content="2", tool_calls=[call]),
        ToolMessage(content="SYSTEM MONITOR: Loop Detectado", tool_call_id="1"), # Feedback was given here
        AIMessage(content="3", tool_calls=[call]) # Agent ignored and called again
    ]
    state = {"messages": msgs}
    
    # Should trigger ABORT now
    assert check_safety(state) == "abort"

if __name__ == "__main__":
    # Manual run for quick check
    try:
        test_no_tool_calls()
        print("test_no_tool_calls PASS")
        test_normal_tool_call()
        print("test_normal_tool_call PASS")
        test_loop_detected_first_time()
        print("test_loop_detected_first_time PASS")
        test_loop_detected_after_feedback()
        print("test_loop_detected_after_feedback PASS")
        print("\nALL TESTS PASSED")
    except AssertionError as e:
        print(f"TEST FAILED: {e}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR: {e}")
