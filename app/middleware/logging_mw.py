"""Request logging middleware — logs method, path, status, and latency.

Uses a raw ASGI middleware (not BaseHTTPMiddleware) so that streaming /
SSE responses (e.g. /mcp/sse) are never buffered and work correctly.
"""

import time
import logging
from typing import Callable

logger = logging.getLogger("city_liveability_api")


class RequestLoggingMiddleware:
    """Logs every HTTP request with method, path, status code, and duration.

    Implemented as a pure ASGI middleware to avoid the body-buffering that
    BaseHTTPMiddleware performs, which breaks SSE / streaming endpoints.
    """

    def __init__(self, app: Callable) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            # Pass websocket / lifespan scopes straight through.
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = scope.get("method", "")
        start = time.perf_counter()
        status_code = 0

        async def send_with_logging(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                duration_ms = (time.perf_counter() - start) * 1000
                logger.info(
                    "%s %s → %d (%.1fms)",
                    method,
                    path,
                    status_code,
                    duration_ms,
                )
                # Inject timing header
                headers = list(message.get("headers", []))
                headers.append(
                    (b"x-process-time-ms", f"{duration_ms:.1f}".encode())
                )
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_logging)
