import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.custom_rule import (
    CustomRuleCreate,
    CustomRuleResponse,
    CustomRuleUpdate,
    RuleCatalogItem,
)
from app.services.rule_service import RuleService

router = APIRouter(prefix="/rules", tags=["Audit Rules & Custom Engine"])


@router.get(
    "",
    response_model=list[RuleCatalogItem],
    summary="List all active rules (built-in and tenant-defined)",
)
async def list_rules(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[RuleCatalogItem]:
    """Retrieve all available audit rules including built-in invariants and tenant custom rules."""
    return await RuleService.list_all_rules(session, current_user.tenant_id)


@router.get(
    "/custom",
    response_model=list[CustomRuleResponse],
    summary="List tenant custom rules",
)
async def list_custom_rules(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[CustomRuleResponse]:
    """Retrieve only custom rules configured for the authenticated tenant."""
    rules = await RuleService.list_custom_rules(session, current_user.tenant_id)
    return [CustomRuleResponse.model_validate(r) for r in rules]


@router.post(
    "/custom",
    response_model=CustomRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new custom audit rule",
)
async def create_custom_rule(
    payload: CustomRuleCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CustomRuleResponse:
    """Create a new deterministic rule scoped strictly to the current tenant."""
    rule = await RuleService.create_custom_rule(session, current_user.tenant_id, payload)
    return CustomRuleResponse.model_validate(rule)


@router.get(
    "/custom/{rule_id}",
    response_model=CustomRuleResponse,
    summary="Get single custom rule",
)
async def get_custom_rule(
    rule_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CustomRuleResponse:
    """Get single custom rule by ID, ensuring tenant isolation."""
    rule = await RuleService.get_custom_rule(session, current_user.tenant_id, rule_id)
    return CustomRuleResponse.model_validate(rule)


@router.patch(
    "/custom/{rule_id}",
    response_model=CustomRuleResponse,
    summary="Update or toggle custom rule",
)
async def update_custom_rule(
    rule_id: uuid.UUID,
    payload: CustomRuleUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CustomRuleResponse:
    """Update custom rule fields or activate/deactivate."""
    rule = await RuleService.update_custom_rule(session, current_user.tenant_id, rule_id, payload)
    return CustomRuleResponse.model_validate(rule)


@router.delete(
    "/custom/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete custom rule",
)
async def delete_custom_rule(
    rule_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Permanently delete a custom rule from the tenant catalog."""
    await RuleService.delete_custom_rule(session, current_user.tenant_id, rule_id)
