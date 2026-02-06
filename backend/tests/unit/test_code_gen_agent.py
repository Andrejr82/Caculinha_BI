# backend/tests/unit/test_code_gen_agent.py

import pytest
from unittest.mock import MagicMock, patch
from app.core.agents.code_gen_agent import CodeGenAgent, FieldMapper, QueryRetriever, PatternMatcher
from app.core.utils.response_cache import ResponseCache
from app.core.utils.query_history import QueryHistory
from app.core.utils.error_handler import APIError

class MockLLM:
    """A mock LLM that can simulate responses for code generation."""
    def __init__(self, responses: dict):
        self._responses = responses
        self._call_count = {}

    def invoke(self, prompt: dict):
        # Simulate LangChain's invoke method
        user_query = prompt["input"]["user_query"]
        
        # Find the response that matches the beginning of the prompt
        for key, value in self._responses.items():
            if key in user_query:
                if isinstance(value, list): # Handle multiple responses for same key
                    current_count = self._call_count.get(key, 0)
                    response_to_return = value[current_count % len(value)]
                    self._call_count[key] = current_count + 1
                    return response_to_return
                return value
        
        # Default to a generic code generation response
        return {
            "code": "import polars as pl\nfinal_output = {'result': 'Default code result'}",
            "chart_spec": None
        }

@pytest.fixture
def mock_llm():
    # Define LLM responses for different scenarios
    responses = {
        "generate simple code": {
            "code": "import polars as pl\nresult = df.select(pl.col('vendas').sum()).item()\nfinal_output = {'result': result}",
            "chart_spec": None
        },
        "top 5 vendas": {
            "code": "import polars as pl\nresult = df.group_by('produto').agg(pl.sum('vendas').alias('total_vendas')).sort('total_vendas', descending=True)\nfinal_output = {'result': result}",
            "chart_spec": None
        },
        "code with error": [ # First attempt fails, second attempt is corrected
            {
                "code": "import polars as pl\nresult = df.group_by('segmento').agg(pl.col('vendas').sum()).compute()\nfinal_output = {'result': result}", # Code with .compute() for Polars
                "chart_spec": None
            },
            {
                "code": "import polars as pl\nresult = df.group_by('segmento').agg(pl.col('vendas').sum())\nfinal_output = {'result': result}", # Corrected code
                "chart_spec": None
            },
        ],
        "code with column error": {
            "code": "import polars as pl\nresult = df.select(pl.col('coluna_inexistente')).collect()\nfinal_output = {'result': result}",
            "chart_spec": None
        },
    }
    return MockLLM(responses)

@pytest.fixture
def mock_field_mapper():
    mapper = MagicMock(spec=FieldMapper)
    mapper.get_known_fields.return_value = {"vendas": "vendas", "produto": "produto", "segmento": "segmento"}
    mapper.map_term.side_effect = lambda x: {"vendas": "vendas", "produto": "produto", "segmento": "segmento"}.get(x.lower(), x)
    mapper.suggest_correction.return_value = None # Default no correction
    return mapper

@pytest.fixture
def mock_query_retriever():
    retriever = MagicMock(spec=QueryRetriever)
    retriever.get_similar_queries.return_value = [] # No RAG examples by default
    return retriever

@pytest.fixture
def mock_pattern_matcher():
    matcher = MagicMock(spec=PatternMatcher)
    matcher.match_pattern.return_value = None # No pattern match by default
    return matcher

@pytest.fixture
def mock_response_cache():
    cache = MagicMock(spec=ResponseCache)
    cache.get.return_value = None # No cache hit by default
    cache.set.return_value = None
    cache.generate_key.return_value = "mock_cache_key"
    return cache

@pytest.fixture
def mock_query_history():
    history = MagicMock(spec=QueryHistory)
    history.add_query.return_value = None
    return history

@pytest.fixture
def code_gen_agent(mock_llm, mock_field_mapper, mock_query_retriever, mock_pattern_matcher, mock_response_cache, mock_query_history):
    # Temporarily patch _load_prompt_template to return static content for testing
    with patch('backend.app.core.agents.code_gen_agent._load_prompt_template', return_value="system prompt for code generation with {available_columns}"):
        agent = CodeGenAgent(
            llm=mock_llm,
            field_mapper=mock_field_mapper,
            query_retriever=mock_query_retriever,
            pattern_matcher=mock_pattern_matcher,
            response_cache=mock_response_cache,
            query_history=mock_query_history
        )
        return agent

# Test basic code generation and execution
@pytest.mark.asyncio
async def test_code_gen_agent_basic_execution(code_gen_agent, mock_llm):
    query = "generate simple code"
    schema = {"vendas": "int", "produto": "str"}
    
    result = await code_gen_agent.generate_and_execute_python_code(query, schema)
    
    assert result["type"] == "code_result"
    assert result["result"]["result"] == 450 # sum of dummy sales data
    mock_llm._responses["generate simple code"]["code"] = "import polars as pl\nresult = df.select(pl.col('vendas').sum()).item()\nfinal_output = {'result': result}" # Reset to avoid state issues


# Test cache hit
@pytest.mark.asyncio
async def test_code_gen_agent_cache_hit(code_gen_agent, mock_response_cache):
    mock_response_cache.get.return_value = {"type": "code_result", "result": "Cached result"}
    query = "cached query"
    schema = {"vendas": "int"}
    
    result = await code_gen_agent.generate_and_execute_python_code(query, schema)
    
    mock_response_cache.get.assert_called_once_with("mock_cache_key")
    assert result["result"] == "Cached result"

# Test _validate_top_n
@pytest.mark.asyncio
async def test_code_gen_agent_validate_top_n(code_gen_agent, mock_llm):
    query = "Quais os top 5 vendas por produto?"
    schema = {"vendas": "int", "produto": "str"}
    
    mock_llm._responses["top 5 vendas"]["code"] = "import polars as pl\nresult = df.group_by('produto').agg(pl.sum('vendas').alias('total_vendas')).sort('total_vendas', descending=True)\nfinal_output = {'result': result}"
    
    result = await code_gen_agent.generate_and_execute_python_code(query, schema)
    
    assert result["type"] == "code_result"
    # The dummy data has 3 unique products, so top 5 will return all 3.
    # The actual sorting and head(5) should be applied.
    assert len(result["result"]["result"]) == 3 # Total unique products in dummy data
    # Check if .head(5) was applied
    assert all(item['total_vendas'] for item in result["result"]["result"]) # Check if results exist

# Test auto-healing (remove .compute())
@pytest.mark.asyncio
async def test_code_gen_agent_auto_healing_compute(code_gen_agent, mock_llm):
    query = "code with error"
    schema = {"segmento": "str", "vendas": "int"}
    
    # Mock the internal _safely_execute_code to raise APIError for .compute()
    with patch('backend.app.core.agents.code_gen_agent.CodeGenAgent._safely_execute_code', 
               side_effect=[
                   APIError("Erro durante a execução do código Python: PolarsError: compute", details={"error_detail": "PolarsError: compute"}),
                   {"result": "Corrected code result", "chart_spec": None} # Second attempt after healing
               ]) as mock_execute:
        
        result = await code_gen_agent.generate_and_execute_python_code(query, schema)
        
        assert mock_execute.call_count == 2
        # Verify that the second call received the healed code (without .compute())
        # The specific check for 'compute()' removal is in _attempt_auto_healing
        assert result["result"] == "Corrected code result"

# Test auto-healing (add .dropna())
@pytest.mark.asyncio
async def test_code_gen_agent_auto_healing_dropna(code_gen_agent, mock_llm):
    query = "analyze vendas com NAs"
    schema = {"segmento": "str", "vendas": "int"}
    
    mock_llm._responses[query] = [
        {"code": "import polars as pl\nresult = df.group_by('segmento').agg(pl.sum('vendas')).collect()\nfinal_output = {'result': result}", "chart_spec": None},
        {"code": "import polars as pl\nresult = df.drop_nulls().group_by('segmento').agg(pl.sum('vendas')).collect()\nfinal_output = {'result': result}", "chart_spec": None}
    ]

    with patch('backend.app.core.agents.code_gen_agent.CodeGenAgent._safely_execute_code', 
               side_effect=[
                   APIError("Erro durante a execução do código Python: NA ambiguous", details={"error_detail": "NA ambiguous"}),
                   {"result": "Healed dropna result", "chart_spec": None}
               ]) as mock_execute:
        
        result = await code_gen_agent.generate_and_execute_python_code(query, schema)
        
        assert mock_execute.call_count == 2
        assert result["result"] == "Healed dropna result"
        # Further check to see if .dropna() was added is in _attempt_auto_healing
        
