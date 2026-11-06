from app.routes.auth import router as auth_router
from app.routes.documents import router as documents_router
from app.routes.health import router as health_router
from app.routes.invoices import router as invoices_router
from app.routes.ui import router as ui_router

__all__ = ["auth_router", "health_router", "documents_router", "invoices_router", "ui_router"]
