from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter


def configure_telemetry(connection_string: str) -> None:
    """Set up OpenTelemetry pipeline exporting traces to Application Insights.

    Call once at application startup (inside FastAPI lifespan).
    Structlog processors add trace/span IDs to every log record as
    customDimensions, making them queryable in App Insights via Kusto.
    """
    if not connection_string:
        return

    exporter = AzureMonitorTraceExporter(connection_string=connection_string)
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def get_tracer(name: str = "document_processor") -> trace.Tracer:
    return trace.get_tracer(name)
