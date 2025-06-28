from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
import logging

def setup_telemetry():
    # Create resource with service information
    resource = Resource.create({
        "service.name": "mcp-server",
        "service.version": "1.0.0",
        "service.instance.id": os.environ.get("HOSTNAME"),
    })
    
    # Configure tracing
    trace_exporter = OTLPSpanExporter(
        endpoint=os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"),
        headers={"Authorization": f"Bearer {os.environ.get('OTEL_AUTH_TOKEN', '')}"} if os.environ.get('OTEL_AUTH_TOKEN') else {}
    )
    
    tracer_provider = TracerProvider(resource=resource)
    span_processor = BatchSpanProcessor(trace_exporter)
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)
    
    # Configure metrics
    metric_exporter = OTLPMetricExporter(
        endpoint=os.environ.get("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT"),
        headers={"Authorization": f"Bearer {os.environ.get('OTEL_AUTH_TOKEN', '')}"} if os.environ.get('OTEL_AUTH_TOKEN') else {}
    )
    
    metric_reader = PeriodicExportingMetricReader(
        exporter=metric_exporter,
        export_interval_millis=30000,  # Export every 30 seconds
    )
    
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)
    
    # Auto-instrument FastAPI
    FastAPIInstrumentor().instrument()
    
    # Auto-instrument SQLite
    SQLite3Instrumentor().instrument()
    
    # Auto-instrument logging
    LoggingInstrumentor().instrument(set_logging_format=True)
    
    logging.info("OpenTelemetry instrumentation configured")