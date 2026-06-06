"""
Structured JSON request logging middleware.
Prometheus metrics are wired directly in fastapi_app.py via Instrumentator.
"""

import time
import logging
from pythonjsonlogger import jsonlogger
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


def _configure_json_logger() -> logging.Logger:
    logger = logging.getLogger("pune_api")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


logger = _configure_json_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )
        return response


def setup_logging(app):
    """Add structured JSON request logging to the FastAPI app."""
    app.add_middleware(RequestLoggingMiddleware)


# Kept for backwards compatibility
def setup_middleware(app):
    setup_logging(app)
