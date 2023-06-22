#!/usr/bin/env python
import os
import sys

from django.conf import settings
from opentelemetry import trace as OpenTelemetry
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, sampling
from opentelemetry.sdk.trace.export import BatchSpanProcessor

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings.local")

    from django.core.management import execute_from_command_line

    resource = Resource.create(
        {
            "service.name": "flagsmith-api",
            "service.version": "1.0.0",
        }
    )

    tracer_provider = TracerProvider(sampler=sampling.ALWAYS_ON, resource=resource)
    OpenTelemetry.set_tracer_provider(tracer_provider)
    DjangoInstrumentor().instrument()

    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=settings.OPENTELEMETRY_ENDPOINT_URL,
                headers={"Authorization": "Api-Token XXX"},
            )
        )
    )

    execute_from_command_line(sys.argv)
