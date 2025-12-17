"""FastAPI middleware setup."""
import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from ml import config, log

settings = config.get_settings()
logger = log.get_logger("middleware")


class RequestID(BaseHTTPMiddleware):
    """Add request ID to requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class Timing(BaseHTTPMiddleware):
    """Log request timing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        response.headers["X-Process-Time"] = str(process_time)
        logger.info(
            "%s %s - %s - %.3fs",
            request.method,
            request.url.path,
            response.status_code,
            process_time,
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        return response


def setup_middleware(app: FastAPI) -> None:
    """Setup all middleware for the FastAPI app."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestID)
    app.add_middleware(Timing)

