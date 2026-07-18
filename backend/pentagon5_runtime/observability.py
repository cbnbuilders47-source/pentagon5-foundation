"""FastAPI metrics, tracing, correlation, and health primitives."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import JSONResponse
from starlette.types import Message

from pentagon5_runtime.config import RuntimeSettings
from pentagon5_runtime.envelopes import error_envelope
from pentagon5_runtime.logging import request_id
from pentagon5_runtime.uuid7 import is_uuid7, uuid7

LOGGER = logging.getLogger(__name__)

REQUESTS = Counter(
    "p5_http_requests_total",
    "HTTP requests processed",
    ("service", "method", "route", "status"),
)
LATENCY = Histogram(
    "p5_http_request_duration_seconds",
    "HTTP request duration",
    ("service", "method", "route"),
)


class BodyTooLargeError(ValueError):
    """Raised when a request body exceeds the configured bound."""


def instrument(app: FastAPI, settings: RuntimeSettings) -> None:
    """Attach bounded-cardinality metrics and optional OTLP tracing."""
    if settings.otlp_endpoint:
        provider = TracerProvider(resource=Resource.create({"service.name": settings.service_name}))
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otlp_endpoint))
        )
        trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)

    @app.middleware("http")
    async def observe(request: Request, call_next: Callable[[Request], Any]) -> Response:
        supplied_id = request.headers.get("x-request-id", "")
        correlation_id = supplied_id if is_uuid7(supplied_id) else str(uuid7())
        token = request_id.set(correlation_id)
        started = time.monotonic()
        response: Response | None = None
        original_receive = request.receive
        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await original_receive()
            received += len(message.get("body", b""))
            if received > settings.max_body_bytes:
                raise BodyTooLargeError
            return message

        request._receive = limited_receive
        try:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.max_body_bytes:
                raise BodyTooLargeError
            async with asyncio.timeout(settings.request_timeout_seconds):
                response = await call_next(request)
            if (
                request.method == "OPTIONS"
                and request.headers.get("origin")
                and response.status_code >= 400
            ):
                response = JSONResponse(
                    error_envelope(
                        correlation_id,
                        code="CORS_ORIGIN_DENIED",
                        message="Cross-origin request is not allowed",
                        retryable=False,
                    ),
                    status_code=400,
                )
        except BodyTooLargeError:
            response = JSONResponse(
                error_envelope(
                    correlation_id,
                    code="REQUEST_BODY_TOO_LARGE",
                    message="Request body exceeds the configured limit",
                    retryable=False,
                ),
                status_code=413,
            )
        except TimeoutError:
            response = JSONResponse(
                error_envelope(
                    correlation_id,
                    code="REQUEST_TIMEOUT",
                    message="Request processing timed out",
                    retryable=True,
                ),
                status_code=504,
            )
        except Exception as error:
            LOGGER.error("Request middleware failure: %s", type(error).__name__)
            response = JSONResponse(
                error_envelope(
                    correlation_id,
                    code="INTERNAL_ERROR",
                    message="An internal error occurred",
                    retryable=True,
                ),
                status_code=500,
            )
        finally:
            if response is not None:
                route = request.scope.get("route")
                route_path = getattr(route, "path", "unmatched")
                REQUESTS.labels(
                    settings.service_name,
                    request.method,
                    route_path,
                    str(response.status_code),
                ).inc()
                LATENCY.labels(settings.service_name, request.method, route_path).observe(
                    time.monotonic() - started
                )
            request_id.reset(token)
        if response is None:
            raise RuntimeError("request completed without a response")
        response.headers["x-request-id"] = correlation_id
        return response

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
