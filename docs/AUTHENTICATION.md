# Authentication Documentation

Complete guide to authentication implementation in the doWhat backend API.

## Table of Contents

1. [Overview](#overview)
2. [Authentication Flow](#authentication-flow)
3. [API Endpoints](#api-endpoints)
4. [Token Management](#token-management)
5. [Protected Endpoints](#protected-endpoints)
6. [Frontend Integration](#frontend-integration)
7. [Security Best Practices](#security-best-practices)
8. [Testing](#testing)

---

## Overview

The doWhat backend uses **JWT (JSON Web Tokens)** for authentication, integrated with **Supabase Auth** for user management and OAuth providers.

### Key Features

- **Email/Password Authentication**: Traditional registration and login
- **Google OAuth**: Social login (optional)
- **JWT Tokens**: Stateless authentication with access + refresh tokens
- **Token Refresh**: Automatic token renewal without re-login
- **Supabase Integration**: Leverages Supabase Auth for user management

### Technology Stack

- **FastAPI**: Web framework
- **Supabase Auth**: User authentication service
- **python-jose**: JWT encoding/decoding
- **passlib + bcrypt**: Password hashing
- **SQLAlchemy**: Database ORM

---

## Authentication Flow

### Registration Flow

```
┌─────────┐                ┌─────────┐                ┌──────────┐
│ Client  │                │ Backend │                │ Supabase │
└────┬────┘                └────┬────┘                └────┬─────┘
     │                          │                          │
     │ POST /api/v1/auth/register                         │
     │ {email, password}        │                          │
     ├─────────────────────────>│                          │
     │                          │                          │
     │                          │ supabase.auth.sign_up()  │
     │                          ├─────────────────────────>│
     │                          │                          │
     │                          │  User Created + Tokens   │
     │                          │<─────────────────────────┤
     │                          │                          │
     │                          │ Create user in DB        │
     │                          │ (users table)            │
     │                          │                          │
     │  201 Created             │                          │
     │  {user, access_token,    │                          │
     │   refresh_token}         │                          │
     │<─────────────────────────┤                          │
     │                          │                          │
     │ Store tokens in          │                          │
     │ SecureStore              │                          │
     │                          │                          │
```

### Login Flow

```
┌─────────┐                ┌─────────┐                ┌──────────┐
│ Client  │                │ Backend │                │ Supabase │
└────┬────┘                └────┬────┘                └────┬─────┘
     │                          │                          │
     │ POST /api/v1/auth/login  │                          │
     │ {email, password}        │                          │
     ├─────────────────────────>│                          │
     │                          │                          │
     │                          │ supabase.auth.sign_in_with_password()
     │                          ├─────────────────────────>│
     │                          │                          │
     │                          │  Auth Success + Tokens   │
     │                          │<─────────────────────────┤
     │                          │                          │
     │                          │ Update last_login_at     │
     │                          │ in users table           │
     │                          │                          │
     │  200 OK                  │                          │
     │  {user, access_token,    │                          │
     │   refresh_token}         │                          │
     │<─────────────────────────┤                          │
     │                          │                          │
```

### Token Refresh Flow

```
┌─────────┐                ┌─────────┐                ┌──────────┐
│ Client  │                │ Backend │                │ Supabase │
└────┬────┘                └────┬────┘                └────┬─────┘
     │                          │                          │
     │ Access token expired     │                          │
     │ (401 response)           │                          │
     │                          │                          │
     │ POST /api/v1/auth/refresh│                          │
     │ Authorization: Bearer    │                          │
     │ <refresh_token>          │                          │
     ├─────────────────────────>│                          │
     │                          │                          │
     │                          │ supabase.auth.refresh_session()
     │                          ├─────────────────────────>│
     │                          │                          │
     │                          │  New Access Token        │
     │                          │<─────────────────────────┤
     │                          │                          │
     │  200 OK                  │                          │
     │  {access_token}          │                          │
     │<─────────────────────────┤                          │
     │                          │                          │
     │ Retry original request   │                          │
     │ with new access token    │                          │
     │                          │                          │
```

---

## API Endpoints

### 1. Register

**Endpoint**: `POST /api/v1/auth/register`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Password Requirements**:
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit

**Success Response (201 Created)**:
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "email_verified": false,
    "auth_provider": "email",
    "created_at": "2025-10-14T10:30:00Z",
    "last_login_at": null
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Error Responses**:
- `409 Conflict`: Email already registered
- `422 Unprocessable Entity`: Password validation failed

---

### 2. Login

**Endpoint**: `POST /api/v1/auth/login`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Success Response (200 OK)**:
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "email_verified": false,
    "auth_provider": "email",
    "created_at": "2025-10-13T10:30:00Z",
    "last_login_at": "2025-10-14T08:15:00Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid credentials

---

### 3. Google OAuth

**Endpoint**: `POST /api/v1/auth/google`

**Request Body**:
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE4MmU0M..."
}
```

**Note**: The `id_token` should be obtained from Google Sign-In SDK on the frontend.

**Success Response (200 OK)**: Same as login response

**Error Responses**:
- `400 Bad Request`: Invalid Google token
- `501 Not Implemented`: Supabase Auth not configured

---

### 4. Refresh Token

**Endpoint**: `POST /api/v1/auth/refresh`

**Request Headers**:
```
Authorization: Bearer <refresh_token>
```

**Success Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid or expired refresh token

---

## Token Management

### Token Types

1. **Access Token**:
   - **Purpose**: Authenticate API requests
   - **Lifetime**: 15 minutes (900 seconds)
   - **Storage**: In-memory or SecureStore (mobile)
   - **Usage**: Sent in `Authorization` header for all protected endpoints

2. **Refresh Token**:
   - **Purpose**: Obtain new access tokens
   - **Lifetime**: 30 days
   - **Storage**: SecureStore (mobile) or HttpOnly cookie (web)
   - **Usage**: Only for `/api/v1/auth/refresh` endpoint

### Token Payload

**Access Token Payload**:
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // User ID
  "email": "user@example.com",
  "type": "access",
  "exp": 1697200000,  // Expiration timestamp
  "iat": 1697199100   // Issued at timestamp
}
```

**Refresh Token Payload**:
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "type": "refresh",
  "exp": 1699791100,
  "iat": 1697199100
}
```

### Token Storage Best Practices

**Mobile (React Native + Expo)**:
```typescript
import * as SecureStore from 'expo-secure-store';

// Store tokens
await SecureStore.setItemAsync('access_token', accessToken);
await SecureStore.setItemAsync('refresh_token', refreshToken);

// Retrieve tokens
const accessToken = await SecureStore.getItemAsync('access_token');

// Delete tokens (logout)
await SecureStore.deleteItemAsync('access_token');
await SecureStore.deleteItemAsync('refresh_token');
```

**Web (Browser)**:
- **Access Token**: LocalStorage or in-memory (for SPAs)
- **Refresh Token**: HttpOnly cookie (most secure)

---

## Protected Endpoints

### Using Authentication Dependency

Any endpoint can be protected by adding the `get_current_user` dependency:

```python
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/api/v1/users/me")
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile.
    Requires authentication.
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
    }
```

### Optional Authentication

For endpoints that work for both guests and authenticated users:

```python
from app.dependencies import get_current_user_optional

@router.get("/api/v1/events/feed")
async def get_event_feed(
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get event feed.
    Personalized if authenticated, generic if guest.
    """
    if current_user:
        # Return personalized feed
        return get_personalized_feed(current_user.id)
    else:
        # Return generic feed
        return get_generic_feed()
```

---

## Frontend Integration

### React Native Example (Expo)

#### 1. Register User

```typescript
import * as SecureStore from 'expo-secure-store';

async function register(email: string, password: string) {
  try {
    const response = await fetch('https://api.dowhat.hk/api/v1/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message);
    }

    const data = await response.json();

    // Store tokens
    await SecureStore.setItemAsync('access_token', data.access_token);
    await SecureStore.setItemAsync('refresh_token', data.refresh_token);

    return data.user;
  } catch (error) {
    console.error('Registration failed:', error);
    throw error;
  }
}
```

#### 2. Login User

```typescript
async function login(email: string, password: string) {
  const response = await fetch('https://api.dowhat.hk/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error('Invalid credentials');
  }

  const data = await response.json();

  await SecureStore.setItemAsync('access_token', data.access_token);
  await SecureStore.setItemAsync('refresh_token', data.refresh_token);

  return data.user;
}
```

#### 3. Make Authenticated Request

```typescript
async function getMyProfile() {
  const accessToken = await SecureStore.getItemAsync('access_token');

  const response = await fetch('https://api.dowhat.hk/api/v1/users/me', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });

  if (response.status === 401) {
    // Token expired, refresh it
    await refreshAccessToken();
    return getMyProfile(); // Retry
  }

  return response.json();
}
```

#### 4. Refresh Access Token

```typescript
async function refreshAccessToken() {
  const refreshToken = await SecureStore.getItemAsync('refresh_token');

  const response = await fetch('https://api.dowhat.hk/api/v1/auth/refresh', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${refreshToken}`,
    },
  });

  if (!response.ok) {
    // Refresh token expired, require re-login
    await logout();
    throw new Error('Session expired, please login again');
  }

  const data = await response.json();
  await SecureStore.setItemAsync('access_token', data.access_token);
}
```

#### 5. Logout

```typescript
async function logout() {
  await SecureStore.deleteItemAsync('access_token');
  await SecureStore.deleteItemAsync('refresh_token');
  // Redirect to login screen
}
```

### Using React Query for Authentication

```typescript
import { useMutation } from '@tanstack/react-query';
import * as SecureStore from 'expo-secure-store';

export function useLogin() {
  return useMutation({
    mutationFn: async ({ email, password }: LoginInput) => {
      const response = await fetch('https://api.dowhat.hk/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        throw new Error('Invalid credentials');
      }

      return response.json();
    },
    onSuccess: async (data) => {
      await SecureStore.setItemAsync('access_token', data.access_token);
      await SecureStore.setItemAsync('refresh_token', data.refresh_token);
    },
  });
}

// Usage in component
function LoginScreen() {
  const loginMutation = useLogin();

  const handleLogin = () => {
    loginMutation.mutate({ email, password });
  };

  return (
    <Button
      onPress={handleLogin}
      loading={loginMutation.isPending}
    >
      Login
    </Button>
  );
}
```

---

## Security Best Practices

### Backend Security

1. **Use HTTPS Only**: Never send tokens over HTTP
2. **Validate Input**: Email format, password strength
3. **Rate Limiting**: Limit login attempts (100 req/min per IP)
4. **Secure Password Storage**: bcrypt with 12 rounds
5. **Short-Lived Access Tokens**: 15 minutes expiry
6. **Rotate Refresh Tokens**: Issue new refresh token on each refresh
7. **Verify Token Type**: Check `type` claim (access vs refresh)

### Frontend Security

1. **Store Tokens Securely**:
   - Mobile: Expo SecureStore (encrypted)
   - Web: HttpOnly cookies for refresh tokens
2. **Don't Log Tokens**: Never log tokens in console
3. **Handle Token Expiry**: Implement auto-refresh logic
4. **Clear on Logout**: Delete all tokens on logout
5. **Validate HTTPS**: Reject non-HTTPS API calls in production

### Supabase Security

1. **Enable Row Level Security (RLS)**: Protect user data
2. **Use Service Role Key Carefully**: Only for server-side operations
3. **Configure Email Verification**: Require email confirmation in production
4. **Monitor Auth Logs**: Check for suspicious activity
5. **Enable 2FA**: For admin accounts (if applicable)

---

## Testing

### Manual Testing with cURL

#### Register

```bash
curl -X POST https://api.dowhat.hk/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

#### Login

```bash
curl -X POST https://api.dowhat.hk/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

#### Access Protected Endpoint

```bash
curl https://api.dowhat.hk/api/v1/users/me \
  -H "Authorization: Bearer <access_token>"
```

#### Refresh Token

```bash
curl -X POST https://api.dowhat.hk/api/v1/auth/refresh \
  -H "Authorization: Bearer <refresh_token>"
```

### Automated Testing with Pytest

See `backend/tests/test_auth.py` for comprehensive test suite.

```bash
cd backend
pytest tests/test_auth.py -v
```

---

## Common Issues

### 1. "Invalid or expired token"

**Causes**:
- Token expired (access token = 15 min, refresh = 30 days)
- Wrong JWT secret key in `.env`
- Token malformed or tampered

**Solution**:
- Implement automatic token refresh
- Verify `JWT_SECRET_KEY` matches Supabase JWT secret

### 2. "Email already registered"

**Cause**: User already exists with that email

**Solution**: Prompt user to login instead, or implement "forgot password" flow

### 3. "Invalid credentials"

**Cause**: Wrong email or password

**Solution**: Double-check credentials, implement rate limiting to prevent brute force

### 4. "Supabase Auth not configured"

**Cause**: Missing Supabase environment variables

**Solution**: Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`

---

## Additional Resources

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [JWT.io Token Debugger](https://jwt.io/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

---

**Last Updated**: October 14, 2025
**Version**: 1.0
