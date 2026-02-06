# backend/tests/integration/test_chat_endpoint.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
import asyncio

# Assuming 'main' is your FastAPI application instance
from main import app
from app.config.settings import settings
from app.core.utils.response_cache import ResponseCache
from app.core.utils.query_history import QueryHistory
from app.core.utils.field_mapper import FieldMapper
from app.core.rag.query_retriever import QueryRetriever
from app.core.learning.pattern_matcher import PatternMatcher
from app.core.agents.code_gen_agent import CodeGenAgent
from app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
from app.core.llm_gemini_adapter import GeminiLLMAdapter

# Create a test client
client = TestClient(app)

# Mocking external dependencies
@pytest.fixture(autouse=True)
def mock_dependencies():
    with patch('backend.app.api.dependencies.get_current_user_from_token', new_callable=AsyncMock) as mock_get_current_user_from_token, \
         patch('backend.app.core.llm_factory.LLMFactory.get_adapter') as mock_llm_adapter, \
         patch('backend.app.core.agents.caculinha_bi_agent.CaculinhaBIAgent') as MockCaculinhaBIAgent, \
         patch('backend.app.core.agents.code_gen_agent.CodeGenAgent') as MockCodeGenAgent, \
         patch('backend.app.core.utils.response_cache.ResponseCache') as MockResponseCache, \
         patch('backend.app.core.utils.query_history.QueryHistory') as MockQueryHistory, \
         patch('backend.app.core.utils.field_mapper.FieldMapper') as MockFieldMapper, \
         patch('backend.app.core.rag.query_retriever.QueryRetriever') as MockQueryRetriever, \
         patch('backend.app.core.learning.pattern_matcher.PatternMatcher') as MockPatternMatcher:
        
        # Mock get_current_user_from_token to return a valid user
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.id = "123"
        mock_user.is_active = True
        mock_user.role = "user"
        mock_get_current_user_from_token.return_value = mock_user

        # Mock the LLM adapter (GeminiLLMAdapter)
        mock_gemini_llm_adapter_instance = MagicMock(spec=GeminiLLMAdapter)
        mock_gemini_llm_adapter_instance.get_llm.return_value = MagicMock() # Return a mock LLM for LangChain
        mock_llm_adapter.return_value = mock_gemini_llm_adapter_instance

        # Mock ResponseCache and QueryHistory instances
        mock_response_cache_instance = MagicMock(spec=ResponseCache)
        mock_response_cache_instance.get.return_value = None # No cache hit by default
        MockResponseCache.return_value = mock_response_cache_instance

        mock_query_history_instance = MagicMock(spec=QueryHistory)
        MockQueryHistory.return_value = mock_query_history_instance

        mock_field_mapper_instance = MagicMock(spec=FieldMapper)
        MockFieldMapper.return_value = mock_field_mapper_instance

        mock_query_retriever_instance = MagicMock(spec=QueryRetriever)
        MockQueryRetriever.return_value = mock_query_retriever_instance

        mock_pattern_matcher_instance = MagicMock(spec=PatternMatcher)
        MockPatternMatcher.return_value = mock_pattern_matcher_instance


        # Mock CaculinhaBIAgent instance
        mock_caculinha_bi_agent_instance = MockCaculinhaBIAgent.return_value
        mock_caculinha_bi_agent_instance.run.return_value = {
            "type": "text", 
            "result": "Olá! Esta é uma resposta mock do agente. ", 
            "response_id": "mock_id_1"
        }
        
        # Mock CodeGenAgent instance
        mock_code_gen_agent_instance = MockCodeGenAgent.return_value

        yield

# Test cases
@pytest.mark.asyncio
async def test_stream_chat_success(mock_dependencies):
    query = "Hello agent"
    token = "mock_token" # The mock_dependencies fixture provides a valid user
    
    with patch('backend.app.core.agents.caculinha_bi_agent.CaculinhaBIAgent.run', new_callable=AsyncMock) as mock_agent_run:
        mock_agent_run.return_value = {
            "type": "text",
            "result": "Resposta do agente para Hello agent.",
            "response_id": "test_id_stream"
        }
        
        response = client.get(f"/api/v1/chat/stream?q={query}&token={token}")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"
        
        events = [line for line in response.iter_lines() if line.startswith("data:")]
        
        # Expect at least two data events: one for text, one for done
        assert len(events) >= 2 
        
        first_event_data = json.loads(events[0].replace("data: ", ""))
        assert first_event_data["type"] == "text"
        assert "Resposta do agente" in first_event_data["text"]
        assert first_event_data["done"] == False
        
        # Check final event
        last_event_data = json.loads(events[-1].replace("data: ", ""))
        assert last_event_data["type"] == "final"
        assert last_event_data["done"] == True

@pytest.mark.asyncio
async def test_stream_chat_chart_response(mock_dependencies):
    query = "show chart"
    token = "mock_token"
    
    chart_spec = {"data": [{"type": "bar", "y": [1,2,3]}], "layout": {"title": "Test Chart"}}
    
    with patch('backend.app.core.agents.caculinha_bi_agent.CaculinhaBIAgent.run', new_callable=AsyncMock) as mock_agent_run:
        mock_agent_run.return_value = {
            "type": "code_result",
            "result": {"some_data": 123},
            "chart_spec": chart_spec,
            "response_id": "chart_id_stream"
        }
        
        response = client.get(f"/api/v1/chat/stream?q={query}&token={token}")
        
        assert response.status_code == 200
        events = [json.loads(line.replace("data: ", "")) for line in response.iter_lines() if line.startswith("data:")]
        
        # Expect a chart event and then text/final events
        chart_event = next((e for e in events if e.get("type") == "chart"), None)
        assert chart_event is not None
        assert chart_event["chart_spec"] == chart_spec
        assert chart_event["done"] == False

@pytest.mark.asyncio
async def test_stream_chat_auth_failure():
    query = "test"
    invalid_token = "invalid"
    
    with patch('backend.app.api.dependencies.get_current_user_from_token', new_callable=AsyncMock) as mock_get_current_user_from_token:
        mock_get_current_user_from_token.side_effect = Exception("Invalid token")
        
        response = client.get(f"/api/v1/chat/stream?q={query}&token={invalid_token}")
        
        assert response.status_code == 200 # SSE returns 200 but data contains error
        events = [json.loads(line.replace("data: ", "")) for line in response.iter_lines() if line.startswith("data:")]
        
        assert len(events) >= 1
        assert "error" in events[0]
        assert "Não autenticado" in events[0]["error"]

@pytest.mark.asyncio
async def test_post_chat_success(mock_dependencies):
    query = "Post test query"
    
    with patch('backend.app.core.agents.caculinha_bi_agent.CaculinhaBIAgent.run', new_callable=AsyncMock) as mock_agent_run:
        mock_agent_run.return_value = {
            "type": "text",
            "result": "Resposta direta do agente para Post query.",
            "response_id": "test_id_post"
        }
        
        response = client.post("/api/v1/chat", json={"query": query}, headers={"Authorization": "Bearer mock_token"})
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "Resposta direta do agente" in data["response"]
        assert "full_agent_response" in data
        assert data["full_agent_response"]["response_id"] == "test_id_post"

@pytest.mark.asyncio
async def test_post_feedback_success(mock_dependencies):
    response_id = "test_response_123"
    feedback_type = "positive"
    
    response = client.post("/api/v1/chat/feedback", json={
        "response_id": response_id,
        "feedback_type": feedback_type,
        "comment": "Muito útil!"
    }, headers={"Authorization": "Bearer mock_token"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Feedback submitted successfully."

    # Verify that feedback was logged (mocking file write)
    with open(f"logs/security/feedback.jsonl", "r") as f: # Assuming default path
        logged_feedback = json.loads(f.readlines()[-1])
        assert logged_feedback["response_id"] == response_id
        assert logged_feedback["feedback_type"] == feedback_type
        assert logged_feedback["user_id"] == "testuser"
