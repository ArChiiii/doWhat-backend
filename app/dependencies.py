"""
FastAPI dependencies for authentication and database access.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User


# Security scheme for JWT bearer token
security = HTTPBearer()


async def get_auth_service() -> AuthService:
    """
    Dependency to get AuthService instance.

    Returns:
        AuthService instance
    """
    return AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    Requires valid access token in Authorization header.

    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        auth_service: Authentication service

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found (401)
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    user = await auth_service.get_current_user(token, db)
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> Optional[User]:
    """
    Dependency to get current authenticated user (optional).
    Does not raise error if no token is provided.
    Useful for endpoints that work for both authenticated and guest users.

    Args:
        credentials: HTTP Bearer token credentials (optional)
        db: Database session
        auth_service: Authentication service

    Returns:
        Current authenticated user or None
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(token, db)
        return user
    except HTTPException:
        # Invalid token, treat as guest user
        return None


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get current active user.
    Can be extended to check for user status, bans, etc.

    Args:
        current_user: Current authenticated user

    Returns:
        Current active user

    Raises:
        HTTPException: If user is inactive or banned (403)
    """
    # Future: Add checks for user.is_active, user.is_banned, etc.
    # if not current_user.is_active:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="User account is inactive"
    #     )

    return current_user


async def verify_refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> str:
    """
    Dependency to verify refresh token from Authorization header.

    Args:
        credentials: HTTP Bearer token credentials
        auth_service: Authentication service

    Returns:
        Verified refresh token string

    Raises:
        HTTPException: If token is invalid or not a refresh token (401)
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    if auth_service.supabase:
        # Supabase handles refresh token verification in refresh_access_token()
        return token
    else:
        # Fallback: Verify token locally
        try:
            payload = auth_service.verify_token(token, token_type="refresh")
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )
            return token
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
