import uuid
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import CurrentUser
from app.security import decode_access_token

security = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CurrentUser:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        tenant_id_str: str = payload.get("tenant_id")
        if not user_id_str or not tenant_id_str:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
        tenant_id = uuid.UUID(tenant_id_str)
    except (InvalidTokenError, ValueError):
        raise credentials_exception

    # Query strictly filtering by tenant_id and user_id
    query = select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    result = await session.execute(query)
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    return CurrentUser(
        id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        role=user.role,
    )


async def get_current_tenant(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> uuid.UUID:
    """Dependency returning the verified tenant_id of the authenticated caller."""
    return current_user.tenant_id
