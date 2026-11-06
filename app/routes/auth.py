from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.auth import CurrentUser, TokenResponse, UserLoginRequest, UserRegisterRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register tenant and initial admin user",
)
async def register(
    data: UserRegisterRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Create a new tenant organization and the primary admin account."""
    return await AuthService.register_tenant_and_admin(session=session, data=data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and retrieve JWT access token",
)
async def login(
    data: UserLoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Validate credentials and return a scoped bearer token."""
    return await AuthService.authenticate_user(session=session, data=data)


@router.get(
    "/me",
    response_model=CurrentUser,
    summary="Get current authenticated user and tenant context",
)
async def get_me(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """Return the profile and tenant context for the authenticated user."""
    return current_user

