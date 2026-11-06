from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes.auth import router as auth_router
from app.routes.documents import router as documents_router
from app.routes.health import router as health_router
from app.routes.invoices import router as invoices_router
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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include core routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(invoices_router)
app.include_router(ui_router)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {
        "message": "AuditFlow AI API is running",
        "docs": "/docs",
        "testing_ui": "/ui",
    }

