# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import set_tracer_provider
from opentelemetry.sdk.resources import Resource, ResourceAttributes
from opentelemetry.sdk.trace.export import BatchSpanProcessor

resource = Resource.create({ResourceAttributes.SERVICE_NAME: "telemetry"})

class AppTracerProvider:

    def __init__(self, connection_string:str):
        self.connection_string = connection_string
        self.resource = resource    
        

    def set_up(self):
        exporter = AzureMonitorTraceExporter(connection_string=self.connection_string)

        # Initialize a trace provider for the application. This is a factory for creating tracers.
        tracer_provider = TracerProvider(resource=self.resource)
        # Span processors are initialized with an exporter which is responsible
        # for sending the telemetry data to a particular backend.
        tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
        # Sets the global default tracer provider
        set_tracer_provider(tracer_provider)