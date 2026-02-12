"""
Authentication endpoints for user registration, login, and token management.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_auth_service, get_current_user, verify_refresh_token
from app.services.auth_service import AuthService
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    GoogleAuthRequest,
    AuthResponse,
    TokenResponse,
    UserResponse,
    ErrorResponse,
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user with email and password. Returns user info and authentication tokens.",
    responses={
        201: {
            "description": "User successfully registered",
            "model": AuthResponse,
        },
        400: {
            "description": "Invalid request data",
            "model": ErrorResponse,
        },
        409: {
            "description": "Email already registered",
            "model": ErrorResponse,
        },
        422: {
            "description": "Validation error (password too weak, invalid email, etc.)",
            "model": ErrorResponse,
        },
    },
)
async def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """
    Register a new user account.

    **Request Body:**
    - `email`: Valid email address (unique)
    - `password`: Strong password (min 8 chars, uppercase, lowercase, digit)

    **Returns:**
    - User information
    - Access token (15 min expiry)
    - Refresh token (30 day expiry)

    **Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit

    **Example Request:**
    ```json
    {
      "email": "user@example.com",
      "password": "SecurePass123!"
    }
    ```
    """
    return await auth_service.register_user(request, db)


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate user with email and password. Returns user info and authentication tokens.",
    responses={
        200: {
            "description": "User successfully authenticated",
            "model": AuthResponse,
        },
        401: {
            "description": "Invalid credentials",
            "model": ErrorResponse,
        },
    },
)
async def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """
    Authenticate user with email and password.

    **Request Body:**
    - `email`: User's email address
    - `password`: User's password

    **Returns:**
    - User information (including last_login_at)
    - Access token (15 min expiry)
    - Refresh token (30 day expiry)

    **Example Request:**
    ```json
    {
      "email": "user@example.com",
      "password": "SecurePass123!"
    }
    ```

    **Error Responses:**
    - `401 Unauthorized`: Invalid email or password
    """
    return await auth_service.login_user(request, db)


@router.post(
    "/google",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Google OAuth authentication",
    description="Authenticate user with Google OAuth ID token. Creates account if first time.",
    responses={
        200: {
            "description": "User successfully authenticated with Google",
            "model": AuthResponse,
        },
        400: {
            "description": "Invalid Google token",
            "model": ErrorResponse,
        },
        401: {
            "description": "Google authentication failed",
            "model": ErrorResponse,
        },
        501: {
            "description": "Supabase Auth not configured",
            "model": ErrorResponse,
        },
    },
)
async def google_auth(
    request: GoogleAuthRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """
    Authenticate user with Google OAuth.

    **Request Body:**
    - `id_token`: Google OAuth ID token (obtained from Google Sign-In on frontend)

    **Returns:**
    - User information
    - Access token (15 min expiry)
    - Refresh token (30 day expiry)

    **Implementation Note:**
    - Frontend should use Supabase client or Google Sign-In SDK to obtain the ID token
    - If user doesn't exist, a new account will be created automatically
    - Google accounts are pre-verified (email_verified = true)

    **Example Request:**
    ```json
    {
      "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE4MmU0M..."
    }
    ```
    """
    return await auth_service.google_auth(request, db)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Get a new access token using refresh token. Refresh token must be sent in Authorization header.",
    responses={
        200: {
            "description": "New access token generated",
            "model": TokenResponse,
        },
        401: {
            "description": "Invalid or expired refresh token",
            "model": ErrorResponse,
        },
    },
)
async def refresh_token(
    refresh_token: str = Depends(verify_refresh_token),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Refresh access token using refresh token.

    **Authorization Header:**
    ```
    Authorization: Bearer <refresh_token>
    ```

    **Returns:**
    - New access token (15 min expiry)
    - Token type ("bearer")
    - Expiration time in seconds

    **Usage:**
    When the access token expires, use this endpoint to get a new one without requiring the user to log in again.
    The refresh token is long-lived (30 days) and should be stored securely.

    **Example Response:**
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "expires_in": 900
    }
    ```

    **Error Responses:**
    - `401 Unauthorized`: Invalid or expired refresh token
    """
    return await auth_service.refresh_access_token(refresh_token, db)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get information about the currently authenticated user.",
    responses={
        200: {
            "description": "Current user information",
            "model": UserResponse,
        },
        401: {
            "description": "Not authenticated or invalid token",
            "model": ErrorResponse,
        },
    },
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user information.

    **Authorization Header:**
    ```
    Authorization: Bearer <access_token>
    ```

    **Returns:**
    - User ID
    - Email
    - Email verification status
    - Authentication provider
    - Creation timestamp
    - Last login timestamp

    **Example Response:**
    ```json
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "email_verified": false,
      "auth_provider": "email",
      "created_at": "2025-10-13T10:30:00Z",
      "last_login_at": "2025-10-14T08:15:00Z"
    }
    ```

    **Error Responses:**
    - `401 Unauthorized`: Not authenticated or invalid token
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        email_verified=current_user.email_verified,
        auth_provider=current_user.auth_provider,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at,
    )
