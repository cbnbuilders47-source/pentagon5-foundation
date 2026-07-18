"""Strict environment configuration with Docker/Kubernetes secret-file support."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

PREFIX = "P5_"
KNOWN_KEYS = {
    "P5_DATABASE_URL",
    "P5_DATABASE_URL_FILE",
    "P5_ENVIRONMENT",
    "P5_LOG_LEVEL",
    "P5_CORS_ORIGINS",
    "P5_MAX_BODY_BYTES",
    "P5_OTLP_ENDPOINT",
    "P5_REQUEST_TIMEOUT_SECONDS",
    "P5_SERVICE_NAME",
}


class ConfigurationError(ValueError):
    """Raised when service configuration is missing or unsafe."""


def secret_value(name: str, environ: Mapping[str, str]) -> str:
    """Read exactly one of NAME and NAME_FILE, stripping only a final newline."""
    direct = environ.get(name)
    file_name = environ.get(f"{name}_FILE")
    if direct and file_name:
        raise ConfigurationError(f"{name} and {name}_FILE are mutually exclusive")
    if file_name:
        path = Path(file_name)
        if not path.is_file():
            raise ConfigurationError(f"{name}_FILE does not reference a regular file")
        value = path.read_text(encoding="utf-8").removesuffix("\n")
    else:
        value = direct or ""
    if not value:
        raise ConfigurationError(f"{name} is required")
    return value


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    """Configuration shared by all backend processes."""

    service_name: str
    environment: str
    database_url: str
    log_level: str = "INFO"
    otlp_endpoint: str | None = None
    cors_origins: tuple[str, ...] = ()
    max_body_bytes: int = 1_048_576
    request_timeout_seconds: float = 15.0


def _bounded_number(
    values: Mapping[str, str],
    name: str,
    default: str,
    minimum: float,
    maximum: float,
) -> float:
    try:
        value = float(values.get(name, default))
    except ValueError as error:
        raise ConfigurationError(f"{name} must be numeric") from error
    if not minimum <= value <= maximum:
        raise ConfigurationError(f"{name} must be between {minimum:g} and {maximum:g}")
    return value


def load_runtime_settings(
    environ: Mapping[str, str] | None = None,
    *,
    allowed_extra: frozenset[str] = frozenset(),
) -> RuntimeSettings:
    """Load settings while rejecting misspelled P5 variables."""
    values = dict(os.environ if environ is None else environ)
    unknown = sorted(
        key for key in values if key.startswith(PREFIX) and key not in KNOWN_KEYS | allowed_extra
    )
    if unknown:
        raise ConfigurationError(f"unknown PENTAGON5 settings: {', '.join(unknown)}")
    environment = values.get("P5_ENVIRONMENT", "production")
    if environment not in {"development", "test", "staging", "production"}:
        raise ConfigurationError("P5_ENVIRONMENT must be development, test, staging, or production")
    database_url = secret_value("P5_DATABASE_URL", values)
    scheme = urlparse(database_url).scheme
    if scheme not in {"postgresql", "postgresql+psycopg"}:
        raise ConfigurationError("P5_DATABASE_URL must use PostgreSQL")
    log_level = values.get("P5_LOG_LEVEL", "INFO").upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ConfigurationError("P5_LOG_LEVEL is invalid")
    service_name = values.get("P5_SERVICE_NAME", "").strip()
    if not service_name:
        raise ConfigurationError("P5_SERVICE_NAME is required")
    raw_origins = values.get("P5_CORS_ORIGINS", "")
    origins = tuple(origin.strip() for origin in raw_origins.split(",") if origin.strip())
    parsed_origins = tuple(urlparse(origin) for origin in origins)
    if any(
        origin == "*"
        or parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.path not in {"", "/"}
        or parsed.params
        or parsed.query
        or parsed.fragment
        for origin, parsed in zip(origins, parsed_origins, strict=True)
    ):
        raise ConfigurationError("P5_CORS_ORIGINS must contain exact HTTP(S) origins")
    max_body_bytes = int(_bounded_number(values, "P5_MAX_BODY_BYTES", "1048576", 1024, 10_485_760))
    request_timeout = _bounded_number(
        values,
        "P5_REQUEST_TIMEOUT_SECONDS",
        "15",
        1,
        60,
    )
    return RuntimeSettings(
        service_name=service_name,
        environment=environment,
        database_url=database_url,
        log_level=log_level,
        otlp_endpoint=values.get("P5_OTLP_ENDPOINT") or None,
        cors_origins=origins,
        max_body_bytes=max_body_bytes,
        request_timeout_seconds=request_timeout,
    )
