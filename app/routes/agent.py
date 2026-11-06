from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.agent.agent_runner import ask_agent
from app.database import get_async_db
from app.dependencies import get_current_user
from app.schemas.agent import AgentAskRequest, AgentAskResponse
from app.schemas.auth import CurrentUser

logger = structlog.get_logger()
router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/ask", response_model=AgentAskResponse, status_code=status.HTTP_200_OK)
async def ask_audit_assistant(
    payload: AgentAskRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> AgentAskResponse:
    """Ask the AuditFlow AI assistant a question about invoices, POs, contracts, or audit findings.
    Answers strictly include citations [filename.pdf p.X] or [finding #ID].
    """
    try:
        response = await ask_agent(
            query=payload.query,
            tenant_id=current_user.tenant_id,
            db=db,
        )
        return response
    except Exception as exc:
        logger.error(
            "Agent request failed",
            tenant_id=str(current_user.tenant_id),
            error=str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while executing the audit assistant query.",
        )
