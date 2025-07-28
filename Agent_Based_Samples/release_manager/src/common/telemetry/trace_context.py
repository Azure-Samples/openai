# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from opentelemetry.propagate import inject, extract
from opentelemetry import context

def inject_trace_context(context_dict: dict) -> None:
    """
    Injects tracing context into the provided dictionary for distributed tracing.
    This is a wrapper around OpenTelemetry's inject function that provides
    a more descriptive API for our services.

    Args:
        context_dict: Dictionary to inject the tracing context into.
    """
    inject(context_dict)

def extract_and_attach_trace_context(carrier: dict) -> None:
    """
    Extracts tracing context from a carrier dictionary and attaches it to the current context.
    This combines extraction and attachment in one operation to ensure proper context propagation.

    Args:
        carrier: Dictionary containing the tracing context to extract.
    """
    trace_context = extract(carrier)
    context.attach(trace_context)
