"""
Authentication service for Supabase integration.
Handles user registration, login, OAuth, and JWT token management.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from supabase import create_client, Client
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.config import settings
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    GoogleAuthRequest,
    AuthResponse,
    TokenResponse,
    UserResponse,
)


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Authentication service handling user registration, login, and token
    management. Integrates with Supabase Auth for OAuth and token verification.
    """

    def __init__(self):
        """Initialize Supabase client."""
        if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
            self.supabase: Client = create_client(
                settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY
            )
        else:
            self.supabase = None

    # ========================================================================
    # Password Hashing
    # ========================================================================

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password from database

        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)

    # ========================================================================
    # JWT Token Management
    # ========================================================================

    @staticmethod
    def create_access_token(
        data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            data: Payload data to encode in token
            expires_delta: Token expiration time (defaults to 15 minutes)

        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire, "type": "access"})

        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """
        Create a JWT refresh token.

        Args:
            data: Payload data to encode in token

        Returns:
            Encoded JWT refresh token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})

        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string
            token_type: Expected token type ('access' or 'refresh')

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )

            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "error": "invalid_token",
                        "message": f"Invalid token type. Expected {token_type}",
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return payload

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_token",
                    "message": "Invalid or expired token",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

    # ========================================================================
    # User Registration
    # ========================================================================

    async def register_user(
        self, request: UserRegisterRequest, db: Session
    ) -> AuthResponse:
        """
        Register a new user with email and password.

        Args:
            request: User registration request data
            db: Database session

        Returns:
            Authentication response with user info and tokens

        Raises:
            HTTPException: If email already exists or registration fails
        """
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "email_exists",
                    "message": "An account with this email already exists",
                },
            )

        # Use Supabase Auth if available, otherwise create user directly
        if self.supabase:
            try:
                # Register user with Supabase Auth
                auth_response = self.supabase.auth.sign_up(
                    {"email": request.email, "password": request.password}
                )

                print("auth_response", auth_response)

                if not auth_response.user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error": "registration_failed",
                            "message": "Failed to create user account. Please try again.",
                        },
                    )

                # Create user record in our database
                new_user = User(
                    id=auth_response.user.id,
                    email=request.email,
                    email_verified=False,
                    auth_provider="email",
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)

                # Return Supabase tokens
                return AuthResponse(
                    user=UserResponse(
                        id=str(new_user.id),
                        email=new_user.email,
                        email_verified=new_user.email_verified,
                        auth_provider=new_user.auth_provider,
                        created_at=new_user.created_at,
                        last_login_at=new_user.last_login_at,
                    ),
                    access_token=auth_response.session.access_token,
                    refresh_token=auth_response.session.refresh_token,
                    token_type="bearer",
                    expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                )

            except Exception:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": "registration_failed",
                        "message": "Failed to register user. Please try again.",
                    },
                )

        else:
            # Fallback: Create user without Supabase Auth (for local dev)
            try:
                new_user = User(
                    email=request.email,
                    email_verified=False,
                    auth_provider="email",
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)

                # Create JWT tokens
                access_token = self.create_access_token(
                    data={"sub": str(new_user.id), "email": new_user.email}
                )
                refresh_token = self.create_refresh_token(
                    data={"sub": str(new_user.id)}
                )

                return AuthResponse(
                    user=UserResponse(
                        id=str(new_user.id),
                        email=new_user.email,
                        email_verified=new_user.email_verified,
                        auth_provider=new_user.auth_provider,
                        created_at=new_user.created_at,
                        last_login_at=new_user.last_login_at,
                    ),
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_type="bearer",
                    expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                )

            except Exception:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": "registration_failed",
                        "message": "Failed to register user. Please try again.",
                    },
                )

    # ========================================================================
    # User Login
    # ========================================================================

    async def login_user(self, request: UserLoginRequest, db: Session) -> AuthResponse:
        """
        Authenticate user with email and password.

        Args:
            request: User login request data
            db: Database session

        Returns:
            Authentication response with user info and tokens

        Raises:
            HTTPException: If credentials are invalid
        """
        # Use Supabase Auth if available
        if self.supabase:
            try:
                # Authenticate with Supabase
                auth_response = self.supabase.auth.sign_in_with_password(
                    {"email": request.email, "password": request.password}
                )

                if not auth_response.user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail={
                            "error": "invalid_credentials",
                            "message": "Email or password is incorrect",
                        },
                    )

                # Get or create user in our database
                user = db.query(User).filter(User.id == auth_response.user.id).first()
                if not user:
                    user = User(
                        id=auth_response.user.id,
                        email=request.email,
                        email_verified=auth_response.user.email_confirmed_at
                        is not None,
                        auth_provider="email",
                    )
                    db.add(user)

                # Update last login
                user.last_login_at = datetime.utcnow()
                db.commit()
                db.refresh(user)

                return AuthResponse(
                    user=UserResponse(
                        id=str(user.id),
                        email=user.email,
                        email_verified=user.email_verified,
                        auth_provider=user.auth_provider,
                        created_at=user.created_at,
                        last_login_at=user.last_login_at,
                    ),
                    access_token=auth_response.session.access_token,
                    refresh_token=auth_response.session.refresh_token,
                    token_type="bearer",
                    expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                )

            except HTTPException:
                raise
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "error": "invalid_credentials",
                        "message": "Email or password is incorrect",
                    },
                )

        else:
            # Fallback: Local authentication without Supabase
            user = db.query(User).filter(User.email == request.email).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "error": "invalid_credentials",
                        "message": "Email or password is incorrect",
                    },
                )

            # Update last login
            user.last_login_at = datetime.utcnow()
            db.commit()
            db.refresh(user)

            # Create JWT tokens
            access_token = self.create_access_token(
                data={"sub": str(user.id), "email": user.email}
            )
            refresh_token = self.create_refresh_token(data={"sub": str(user.id)})

            return AuthResponse(
                user=UserResponse(
                    id=str(user.id),
                    email=user.email,
                    email_verified=user.email_verified,
                    auth_provider=user.auth_provider,
                    created_at=user.created_at,
                    last_login_at=user.last_login_at,
                ),
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )

    # ========================================================================
    # Google OAuth
    # ========================================================================

    async def google_auth(
        self, request: GoogleAuthRequest, db: Session
    ) -> AuthResponse:
        """
        Authenticate user with Google OAuth.

        Args:
            request: Google auth request with ID token
            db: Database session

        Returns:
            Authentication response with user info and tokens

        Raises:
            HTTPException: If Google authentication fails
        """
        if not self.supabase:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail={
                    "error": "oauth_not_configured",
                    "message": "Google OAuth requires Supabase Auth to be configured",
                },
            )

        try:
            # Verify Google ID token with Supabase
            # Note: Frontend should use Supabase client to get the ID token
            auth_response = self.supabase.auth.sign_in_with_id_token(
                {"provider": "google", "token": request.id_token}
            )

            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "error": "google_auth_failed",
                        "message": "Failed to authenticate with Google",
                    },
                )

            # Get or create user in our database
            user = db.query(User).filter(User.id == auth_response.user.id).first()
            if not user:
                user = User(
                    id=auth_response.user.id,
                    email=auth_response.user.email,
                    email_verified=True,  # Google accounts are pre-verified
                    auth_provider="google",
                    auth_provider_id=auth_response.user.id,
                )
                db.add(user)

            # Update last login
            user.last_login_at = datetime.utcnow()
            db.commit()
            db.refresh(user)

            return AuthResponse(
                user=UserResponse(
                    id=str(user.id),
                    email=user.email,
                    email_verified=user.email_verified,
                    auth_provider=user.auth_provider,
                    created_at=user.created_at,
                    last_login_at=user.last_login_at,
                ),
                access_token=auth_response.session.access_token,
                refresh_token=auth_response.session.refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )

        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "google_auth_failed",
                    "message": "Google ID token is invalid or expired",
                },
            )

    # ========================================================================
    # Token Refresh
    # ========================================================================

    async def refresh_access_token(
        self, refresh_token: str, db: Session
    ) -> TokenResponse:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token
            db: Database session

        Returns:
            New access token

        Raises:
            HTTPException: If refresh token is invalid
        """
        if self.supabase:
            try:
                # Use Supabase to refresh token
                auth_response = self.supabase.auth.refresh_session(refresh_token)

                if not auth_response.session:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail={
                            "error": "invalid_refresh_token",
                            "message": "Refresh token is invalid or expired",
                        },
                    )

                return TokenResponse(
                    access_token=auth_response.session.access_token,
                    refresh_token=auth_response.session.refresh_token,
                    token_type="bearer",
                    expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                )

            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "error": "invalid_refresh_token",
                        "message": "Refresh token is invalid or expired",
                    },
                )

        else:
            # Fallback: Verify and create new token locally
            try:
                payload = self.verify_token(refresh_token, token_type="refresh")
                user_id = payload.get("sub")

                if not user_id:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail={
                            "error": "invalid_refresh_token",
                            "message": "Refresh token is invalid or expired",
                        },
                    )

                # Verify user still exists
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail={
                            "error": "invalid_refresh_token",
                            "message": "Refresh token is invalid or expired",
                        },
                    )

                # Create new access token
                access_token = self.create_access_token(
                    data={"sub": str(user.id), "email": user.email}
                )

                return TokenResponse(
                    access_token=access_token,
                    token_type="bearer",
                    expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                )

            except HTTPException:
                raise
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "error": "invalid_refresh_token",
                        "message": "Refresh token is invalid or expired",
                    },
                )

    # ========================================================================
    # User Retrieval
    # ========================================================================

    async def get_current_user(self, token: str, db: Session) -> User:
        """
        Get current user from access token.

        Args:
            token: JWT access token
            db: Database session

        Returns:
            User object

        Raises:
            HTTPException: If token is invalid or user not found
        """
        # Verify token
        payload = self.verify_token(token, token_type="access")
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_token",
                    "message": "Invalid authentication token",
                },
            )

        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_token", "message": "User not found"},
            )

        return user
