from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import get_settings
from app.middleware.logging import StructuredLoggingMiddleware
from app.middleware.rate_limit import RedisRateLimitMiddleware
from app.routes.agent import router as agent_router
from app.routes.auth import router as auth_router
from app.routes.documents import router as documents_router
from app.routes.findings import router as findings_router
from app.routes.health import router as health_router
from app.routes.invoices import router as invoices_router
from app.routes.projects import router as projects_router
from app.routes.rules import router as rules_router
from app.routes.ui import router as ui_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup actions
    yield
    # Shutdown actions


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Automated AP audit and fraud detection platform with pgvector RAG and LangChain agent.",
    version="0.1.0",
    lifespan=lifespan,
)

# Custom Middlewares
app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(RedisRateLimitMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Include core routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(projects_router)
app.include_router(invoices_router)
app.include_router(findings_router)
app.include_router(rules_router)
app.include_router(agent_router)
app.include_router(ui_router)

# Mount built Vite React Admin Panel if present
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/admin", include_in_schema=False)
    @app.get("/app", include_in_schema=False)
    async def serve_admin_panel() -> FileResponse:
        return FileResponse(os.path.join(frontend_dist, "index.html"))


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {
        "message": "AuditFlow AI API is running",
        "admin_panel": "/app",
        "testing_ui": "/ui",
        "api_docs": "/docs",
        "metrics": "/metrics",
    }

