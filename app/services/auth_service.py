import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest
from app.security import create_access_token, hash_password, verify_password

settings = get_settings()


class AuthService:
    @staticmethod
    async def register_tenant_and_admin(
        session: AsyncSession,
        data: UserRegisterRequest,
    ) -> TokenResponse:
        # Check if email is already taken
        query = select(User).where(User.email == data.email)
        result = await session.execute(query)
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists.",
            )

        # Create new tenant
        tenant = Tenant(name=data.tenant_name)
        session.add(tenant)
        await session.flush()  # Populates tenant.id

        # Create first admin user
        hashed_pwd = hash_password(data.password)
        user = User(
            tenant_id=tenant.id,
            email=data.email,
            password_hash=hashed_pwd,
            role=data.role or "admin",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Generate JWT access token
        access_token = create_access_token(
            subject=str(user.id),
            tenant_id=str(tenant.id),
            role=user.role,
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
            tenant_id=tenant.id,
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

    @staticmethod
    async def authenticate_user(
        session: AsyncSession,
        data: UserLoginRequest,
    ) -> TokenResponse:
        # Retrieve user by email
        query = select(User).where(User.email == data.email)
        result = await session.execute(query)
        user = result.scalars().first()

        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(
            subject=str(user.id),
            tenant_id=str(user.tenant_id),
            role=user.role,
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
            tenant_id=user.tenant_id,
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

