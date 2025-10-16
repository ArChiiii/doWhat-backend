"""
Authentication schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re


class UserRegisterRequest(BaseModel):
    """
    Request schema for user registration.
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (min 8 characters)",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password strength.
        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")

        return v

    model_config = {
        "json_schema_extra": {
            "example": {"email": "user@example.com", "password": "SecurePass123!"}
        }
    }


class UserLoginRequest(BaseModel):
    """
    Request schema for user login.
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    model_config = {
        "json_schema_extra": {
            "example": {"email": "user@example.com", "password": "SecurePass123!"}
        }
    }


class GoogleAuthRequest(BaseModel):
    """
    Request schema for Google OAuth authentication.
    """

    id_token: str = Field(..., description="Google OAuth ID token from frontend")

    model_config = {
        "json_schema_extra": {
            "example": {"id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE4MmU0M..."}
        }
    }


class TokenRefreshRequest(BaseModel):
    """
    Request schema for refreshing access token.
    Note: Refresh token is sent in Authorization header, not in body.
    """

    pass


class UserResponse(BaseModel):
    """
    Response schema for user information.
    """

    id: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email address")
    email_verified: bool = Field(False, description="Whether email is verified")
    auth_provider: str = Field(
        "email", description="Authentication provider (email or google)"
    )
    created_at: datetime = Field(..., description="User creation timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "email_verified": False,
                "auth_provider": "email",
                "created_at": "2025-10-13T10:30:00Z",
                "last_login_at": "2025-10-14T08:15:00Z",
            }
        }
    }


class TokenResponse(BaseModel):
    """
    Response schema for token information.
    """

    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(
        None, description="JWT refresh token (only on login/register)"
    )
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(900, description="Token expiration time in seconds")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900,
            }
        }
    }


class AuthResponse(BaseModel):
    """
    Response schema for authentication (login/register).
    Combines user info and tokens.
    Tokens may be None if email confirmation is required.
    """

    user: UserResponse = Field(..., description="User information")
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(900, description="Access token expiration time in seconds")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "user@example.com",
                    "email_verified": False,
                    "auth_provider": "email",
                    "created_at": "2025-10-13T10:30:00Z",
                    "last_login_at": None,
                },
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900,
            }
        }
    }


class ErrorResponse(BaseModel):
    """
    Standard error response schema.
    """

    error: str = Field(..., description="Error type/category")
    message: str = Field(..., description="Human-readable error message")
    detail: Optional[str] = Field(None, description="Additional error details")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "INVALID_CREDENTIALS",
                "message": "Invalid email or password",
                "detail": "The provided credentials do not match our records",
            }
        }
    }
