from typing import Annotated, Any
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health and readiness probe",
)
async def health_check(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """Verify application liveness and database connectivity."""
    db_status = "healthy"
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {exc}"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "database": db_status},
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy", "database": "connected"},
    )

