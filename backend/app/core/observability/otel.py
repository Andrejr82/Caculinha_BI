
import os
from typing import Optional

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Variáveis de Ambiente
OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "caculinha-bi")
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

def setup_otel(app: FastAPI):
    """
    Configura OpenTelemetry para a aplicação FastAPI.
    """
    if os.getenv("ENABLE_OTEL", "false").lower() != "true":
        return

    resource = Resource.create(attributes={
        "service.name": OTEL_SERVICE_NAME,
        "deployment.environment": os.getenv("ENVIRONMENT", "development")
    })

    trace.set_tracer_provider(TracerProvider(resource=resource))
    
    # Configurar Exporter (GRPC padrão para Collector)
    otlp_exporter = OTLPSpanExporter(endpoint=OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True)
    
    # Batch Span Processor para performance
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Instrumentar FastAPI
    FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())

def get_tracer(name: str):
    return trace.get_tracer(name)

def start_span(name: str, attributes: Optional[dict] = None):
    tracer = get_tracer("caculinha-bi")
    return tracer.start_as_current_span(name, attributes=attributes or {})
