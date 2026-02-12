# DoWhat API Reference

Base URL: `http://localhost:8000`

Interactive docs (dev only): `http://localhost:8000/docs`

## Authentication

All authenticated endpoints require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens are Supabase-signed JWTs returned by `/register` and `/login`.

---

## System

### GET `/`

Root info endpoint.

**Response** `200`

```json
{
  "message": "doWhat API v1.0.0",
  "status": "healthy",
  ...
}
```

### GET `/health`

Health check with DB and Redis status.

**Response** `200`

```json
{
  "status": "healthy",
  "timestamp": "2026-02-12T10:02:11.057261",
  "service": "doWhat API",
  "version": "1.0.0",
  "environment": "development",
  "database": "connected",
  "redis": "connected"
}
```

### GET `/api/v1/status`

API status with available endpoint groups.

---

## Auth Endpoints

### POST `/api/v1/auth/register`

Register a new user.

**Request Body**

| Field      | Type   | Required | Description                                    |
|------------|--------|----------|------------------------------------------------|
| `email`    | string | yes      | Valid email address (unique)                   |
| `password` | string | yes      | Min 8 chars, 1 uppercase, 1 lowercase, 1 digit |

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response** `201`

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "email_verified": false,
    "auth_provider": "email",
    "created_at": "2026-02-12T10:30:00Z",
    "last_login_at": null
  },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Errors**

| Status | Error             | When                    |
|--------|-------------------|-------------------------|
| 409    | `email_exists`    | Email already registered |
| 422    | Validation error  | Weak password / bad email |

---

### POST `/api/v1/auth/login`

Authenticate with email and password.

**Request Body**

| Field      | Type   | Required |
|------------|--------|----------|
| `email`    | string | yes      |
| `password` | string | yes      |

**Response** `200` - Same shape as register response.

**Errors**

| Status | Error                 | When                       |
|--------|-----------------------|----------------------------|
| 401    | `invalid_credentials` | Wrong email or password    |

---

### POST `/api/v1/auth/google`

Google OAuth sign-in. Requires Supabase Auth to be configured.

**Request Body**

| Field      | Type   | Required | Description                     |
|------------|--------|----------|---------------------------------|
| `id_token` | string | yes      | Google OAuth ID token from frontend |

**Response** `200` - Same shape as register response.

**Errors**

| Status | Error                  | When                              |
|--------|------------------------|-----------------------------------|
| 401    | `google_auth_failed`   | Invalid/expired Google token      |
| 501    | `oauth_not_configured` | Supabase Auth not set up          |

---

### POST `/api/v1/auth/refresh`

Get a new access token using a refresh token.

**Authorization Header** - Send refresh token (not access token):

```
Authorization: Bearer <refresh_token>
```

**Response** `200`

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Errors**

| Status | Error                    | When                            |
|--------|--------------------------|---------------------------------|
| 401    | `invalid_refresh_token`  | Expired or invalid refresh token |

---

### GET `/api/v1/auth/me`

Get current authenticated user info. **Requires auth.**

**Response** `200`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "email_verified": false,
  "auth_provider": "email",
  "created_at": "2026-02-12T10:30:00Z",
  "last_login_at": "2026-02-12T12:00:00Z"
}
```

---

## Event Endpoints

### GET `/api/v1/events/feed`

Paginated event feed. Active, upcoming events ordered by date. Optional auth to mark `isSaved`.

**Query Parameters**

| Param        | Type    | Default | Description                                |
|--------------|---------|---------|--------------------------------------------|
| `page`       | int     | 1       | Page number (>= 1)                        |
| `limit`      | int     | 50      | Events per page (1-100)                   |
| `categories` | string  | null    | Comma-separated: `music,arts,food`         |
| `time_filter`| string  | null    | `today`, `week`, or `all`                  |

**Response** `200`

```json
{
  "events": [
    {
      "id": "uuid",
      "title": "Jazz Night at Fringe Club",
      "category": "music",
      "startTime": "2026-02-15T20:00:00",
      "endTime": "2026-02-15T23:00:00",
      "venue": {
        "name": "Fringe Club",
        "address": "2 Lower Albert Rd, Central",
        "latitude": 22.2808,
        "longitude": 114.1557
      },
      "imageUrl": "https://...",
      "organizer": "instagram",
      "description": "Live jazz performance...",
      "sourceUrl": "https://instagram.com/p/...",
      "price": "HK$200",
      "bookingUrl": "https://...",
      "isSaved": false,
      "interestCount": 42,
      "status": "active",
      "schedule": { ... }
    }
  ],
  "count": 20,
  "total": 150,
  "page": 1,
  "hasMore": true
}
```

---

### GET `/api/v1/events/map`

Events for map display. Only returns events that have coordinates (`venue_lat` and `venue_lng` are not null). Optional auth to mark `isSaved`.

**Query Parameters**

| Param        | Type    | Default | Description                                         |
|--------------|---------|---------|-----------------------------------------------------|
| `lat`        | float   | null    | Center latitude (for radius filtering)              |
| `lng`        | float   | null    | Center longitude (for radius filtering)             |
| `radius`     | int     | 50000   | Radius in meters (only used if lat/lng provided)    |
| `categories` | string  | null    | Comma-separated category filter                     |
| `time_filter`| string  | null    | `today`, `week`, or `all`                           |
| `limit`      | int     | 200     | Max events (1-500)                                  |

**Response** `200`

```json
{
  "events": [ ... ],
  "count": 45,
  "bounds": {
    "ne": { "latitude": 22.35, "longitude": 114.25 },
    "sw": { "latitude": 22.25, "longitude": 114.10 }
  }
}
```

**How it works:**

1. Filters to active events with non-null `venue_lat`/`venue_lng`
2. If `lat`/`lng` provided: applies a bounding-box filter using the radius (degree approximation)
3. If no `lat`/`lng`: returns all geolocated events (up to `limit`)
4. Computes `bounds` (NE/SW corners) from the returned events
5. `bounds` is `null` if no events have valid coordinates

**Frontend usage (React Native Maps):**

```typescript
// Fetch events for current map region
const response = await fetch(
  `${API_URL}/api/v1/events/map?lat=${region.latitude}&lng=${region.longitude}&radius=10000`
);
const { events, bounds } = await response.json();

// Place markers
events.forEach(event => {
  // event.venue.latitude, event.venue.longitude are guaranteed non-zero
});
```

---

### GET `/api/v1/events/{event_id}`

Get full event details. Optional auth to indicate `isSaved`.

**Response** `200` - Single `EventResponse` object.

**Errors**

| Status | Error       | When              |
|--------|-------------|-------------------|
| 404    | `not_found` | Event doesn't exist |

---

### POST `/api/v1/events/{event_id}/swipe`

Record a swipe action. **Requires auth.** Upserts (re-swipe updates the record).

**Request Body**

| Field       | Type   | Required | Values          |
|-------------|--------|----------|-----------------|
| `direction` | string | yes      | `left` or `right` |

**Response** `200`

```json
{
  "success": true,
  "message": "Swipe right recorded"
}
```

**Errors**

| Status | Error       | When              |
|--------|-------------|-------------------|
| 401    | Unauthorized | No/invalid token  |
| 404    | `not_found` | Event doesn't exist |
| 422    | Validation   | Invalid direction  |

---

## Saved Events Endpoints

All require authentication.

### GET `/api/v1/users/saved-events/`

List all saved events for the current user. Ordered by most recently saved.

**Response** `200` - Array of `EventResponse` objects (all with `isSaved: true`).

---

### POST `/api/v1/users/saved-events/{event_id}`

Save an event. Idempotent (saving twice returns success).

**Response** `200`

```json
{
  "success": true,
  "message": "Event saved"
}
```

**Errors**

| Status | Error       | When              |
|--------|-------------|-------------------|
| 404    | `not_found` | Event doesn't exist |

---

### DELETE `/api/v1/users/saved-events/{event_id}`

Remove a saved event.

**Response** `200`

```json
{
  "success": true,
  "message": "Event removed from saved"
}
```

**Errors**

| Status | Error       | When                    |
|--------|-------------|-------------------------|
| 404    | `not_found` | Event was not saved     |

---

## Event Object Reference

```typescript
interface EventResponse {
  id: string;               // UUID
  title: string;
  category: string;         // music | arts | food | sports | nightlife | workshops
                            // outdoor | family | markets | theater | education
                            // festival | other
  startTime: string;        // ISO8601 datetime
  endTime: string | null;   // ISO8601 datetime
  venue: {
    name: string;
    address: string;
    latitude: number;       // 0.0 if not available
    longitude: number;      // 0.0 if not available
  };
  imageUrl: string;         // Cloudinary/Supabase Storage URL, "" if none
  organizer: string;        // source_name (e.g. "instagram")
  description: string;
  sourceUrl: string;        // Original source link
  price: string | null;     // "Free", "HK$200", "HK$100 - HK$300", null
  bookingUrl: string | null;
  isSaved: boolean;         // true if authed user has saved this event
  interestCount: number;    // Total saves across all users
  status: string;           // "active" | "cancelled" | "expired"
  schedule: object | null;  // JSONB schedule details
}
```

## Categories

Valid values for the `categories` filter parameter:

`music`, `arts`, `food`, `sports`, `nightlife`, `workshops`, `outdoor`, `family`, `markets`, `theater`, `education`, `festival`, `other`

## Rate Limits

- No rate limiting currently enforced (planned: 100 req/min per user via Redis)

## Error Format

All errors follow this shape:

```json
{
  "error": "error_code",
  "message": "Human-readable description"
}
```

For validation errors (422), FastAPI returns its standard format:

```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "type": "string_too_short"
    }
  ]
}
```
