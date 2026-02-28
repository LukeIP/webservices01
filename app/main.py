"""FastAPI application factory."""

import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import Base, engine
from app.exceptions import AppException, app_exception_handler, generic_exception_handler
from app.routers import cities, observations, analytics, query, auth
from app.routers import metrics as metrics_router
from app.middleware.rate_limit import setup_rate_limiting
from app.middleware.logging_mw import RequestLoggingMiddleware
from mcp_server.server import mcp

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    def _run_seed():
        try:
            from scripts.seed_data import seed
            seed()
        except Exception as exc:
            logger.error("Background seed failed: %s", exc)

    import os
    if not os.environ.get("SKIP_SEED"):
        threading.Thread(target=_run_seed, daemon=True).start()
    yield


# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        title="City Liveability & Urban Climate Insights API",
        description=(
            "Aggregates urban climate, air quality, and socioeconomic data for UK cities. "
            "Computes composite liveability scores and provides a natural-language query interface."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        redirect_slashes=True,
    )

    # Middleware (order: outermost first)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting
    setup_rate_limiting(app)

    # Exception handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Routers — analytics MUST be registered before cities so /cities/compare
    # is matched before /cities/{city_id}
    app.include_router(auth.router)
    app.include_router(analytics.router)
    app.include_router(cities.router)
    app.include_router(metrics_router.router)
    app.include_router(observations.router)
    app.include_router(query.router)

    @app.get("/", tags=["Health"])
    def health_check():
        return {"status": "healthy", "service": "city-liveability-api", "version": "1.0.0"}

    # --- Frontend (mounted if directory is found, redirects to /docs otherwise) ---
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    # Also try CWD as a fallback (Railway working directory may differ)
    if not frontend_dir.exists():
        frontend_dir = Path.cwd() / "frontend"

    try:
        app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="frontend-static")

        @app.get("/ui", include_in_schema=False)
        def serve_frontend():
            return FileResponse(str(frontend_dir / "index.html"))

    except RuntimeError:
        from fastapi.responses import RedirectResponse

        @app.get("/ui", include_in_schema=False)
        def serve_frontend_fallback():
            return RedirectResponse("/docs")

    # --- MCP Server (SSE transport) ---
    # Exposes all MCP tools at /mcp/sse so remote LLM clients (e.g. Claude Desktop)
    # can connect via: { "url": "https://<host>/mcp/sse" }
    app.mount("/mcp", mcp.sse_app())

    return app


app = create_app()
