
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest
from prometheus_client import CollectorRegistry, multiprocess

# Defining custom registry to avoid conflicts if multiprocess is needed
# For simplicity in this phase, we use the default registry implicit in the metrics definition

# --- GOLDEN SIGNALS (HTTP) ---
HTTP_REQUESTS_TOTAL = Counter(
    'caculinha_http_requests_total',
    'Total HTTP requests',
    ['method', 'route', 'status', 'tenant']
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    'caculinha_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'route', 'tenant'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
)

# --- AI AGENTS & LLM ---
AGENT_INVOCATIONS_TOTAL = Counter(
    'caculinha_agent_invocations_total',
    'Total agent invocations',
    ['agent', 'status', 'tenant']
)

AGENT_DURATION_SECONDS = Histogram(
    'caculinha_agent_duration_seconds',
    'Agent execution duration in seconds',
    ['agent', 'tenant'],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0)
)

LLM_TOKENS_TOTAL = Counter(
    'caculinha_llm_tokens_total',
    'Total LLM tokens consumed',
    ['model', 'direction', 'tenant']  # direction: input, output
)

LLM_COST_ESTIMATED_TOTAL = Counter(
    "caculinha_llm_cost_estimated_total",
    "Estimated LLM cost in USD",
    ["model", "tenant"]
)

RAG_RETRIEVALS_TOTAL = Counter(
    'caculinha_rag_retrievals_total',
    'Total RAG document retrievals',
    ['source', 'tenant']
)

TOOL_EXECUTION_TOTAL = Counter(
    'caculinha_tool_execution_total',
    'Total tool executions',
    ['tool', 'status', 'tenant']
)

# --- ERRORS ---
ERRORS_TOTAL = Counter(
    'caculinha_errors_total',
    'Total application errors',
    ['component', 'type', 'tenant']
)

# --- QUALITY GATE ---
from prometheus_client import Gauge

RESPONSE_QUALITY_SCORE = Gauge(
    'caculinha_response_quality_score',
    'Response quality score (Judge LLM)',
    ['tenant', 'agent']
)

RESPONSE_UTILITY_SCORE = Gauge(
    'caculinha_response_utility_score',
    'Response utility score (Judge LLM)',
    ['tenant', 'agent']
)

RESPONSE_GROUNDEDNESS_SCORE = Gauge(
    'caculinha_response_groundedness_score',
    'Response groundedness score (Judge LLM)',
    ['tenant', 'agent']
)

RESPONSES_BLOCKED_TOTAL = Counter(
    'caculinha_responses_blocked_total',
    'Total responses blocked by Quality Gate',
    ['tenant']
)

RESPONSES_WARNING_TOTAL = Counter(
    'caculinha_responses_warning_total',
    'Total responses with Warning from Quality Gate',
    ['tenant']
)

def get_metrics_content():
    """Generates the metrics output for the /metrics endpoint."""
    return generate_latest(), CONTENT_TYPE_LATEST
