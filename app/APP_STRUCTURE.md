# Application Structure

This is the core FastAPI application for the doWhat backend.

## Directory Structure

```
app/
├── __init__.py              # Package initialization
├── main.py                  # FastAPI app entry point
├── config.py                # Application settings
├── database.py              # Database connection & session
│
├── models/                  # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── user.py              # User model
│   ├── event.py             # Event model
│   ├── swipe.py             # Swipe history model
│   ├── interested_event.py  # Interested events model
│   ├── user_preferences.py  # User preferences model
│   └── scraper_log.py       # Scraper logs model
│
├── schemas/                 # Pydantic schemas (TODO)
│   ├── __init__.py
│   ├── auth.py              # Auth request/response schemas
│   ├── event.py             # Event schemas
│   ├── user.py              # User schemas
│   └── filters.py           # Filter schemas
│
├── routers/                 # API route handlers (TODO)
│   ├── __init__.py
│   ├── auth.py              # /api/v1/auth/*
│   ├── events.py            # /api/v1/events/*
│   ├── users.py             # /api/v1/users/*
│   └── interested.py        # /api/v1/users/me/interested/*
│
├── services/                # Business logic (TODO)
│   ├── __init__.py
│   ├── auth_service.py      # Auth logic
│   ├── event_service.py     # Event CRUD
│   ├── swipe_service.py     # Swipe logic
│   └── cache_service.py     # Redis caching
│
├── middleware/              # Custom middleware (TODO)
│   ├── __init__.py
│   ├── rate_limiter.py      # Rate limiting
│   └── auth.py              # JWT verification
│
└── utils/                   # Utilities (TODO)
    ├── __init__.py
    ├── jwt.py               # JWT helpers
    └── validators.py        # Validation helpers
```

## Current Implementation Status

### ✅ Implemented
- **main.py**: FastAPI app with basic endpoints
  - `/` - Root endpoint
  - `/health` - Health check with DB & Redis status
  - `/api/v1/status` - API status
  - Error handlers (404, 500)
  - CORS middleware
  - Request timing middleware
  - Sentry integration (optional)

- **config.py**: Application settings
  - Environment variables
  - Database configuration
  - Redis configuration
  - Third-party API keys
  - CORS settings

- **database.py**: SQLAlchemy setup
  - Database engine
  - Session factory
  - Base model class
  - Dependency injection

- **models/**: Complete database models
  - User
  - Event
  - SwipeHistory
  - InterestedEvent
  - UserPreferences
  - ScraperLog

### 🚧 TODO (Next Steps)
- **schemas/**: Pydantic request/response models
- **routers/**: API endpoint implementations
- **services/**: Business logic layer
- **middleware/**: Rate limiting, auth
- **utils/**: Helper functions

## Quick Start

### Run Locally
```bash
# Start the API server
uvicorn app.main:app --reload

# Or use the Dockerfile
docker-compose up -d
```

### Access Endpoints
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Run Tests
```bash
pytest tests/
```

## Next Steps

1. **Add Schemas** (`app/schemas/`)
   - Define Pydantic models for requests/responses
   - Add validation rules

2. **Implement Routers** (`app/routers/`)
   - Create API endpoints
   - Connect to services

3. **Build Services** (`app/services/`)
   - Implement business logic
   - Add database operations

4. **Add Middleware** (`app/middleware/`)
   - Rate limiting
   - JWT authentication

5. **Create Utils** (`app/utils/`)
   - JWT helpers
   - Validators
   - Formatters

## Environment Variables

Required variables (see `config.py`):
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET_KEY` - Secret for JWT tokens

Optional variables:
- `SENTRY_DSN` - Error tracking
- `OPENAI_API_KEY` - For category inference
- `CLOUDINARY_*` - Image CDN

See `env.example` for complete list.

## Database Models

All models inherit from `Base` (SQLAlchemy declarative base).

### Key Models
- **User**: Authentication and user data
- **Event**: Event information from scrapers
- **SwipeHistory**: User swipe actions
- **InterestedEvent**: User's interested events
- **UserPreferences**: User category preferences
- **ScraperLog**: Scraper run history

### Migrations

Create migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

## Testing

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

## API Documentation

When running in debug mode:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

In production, docs are disabled by default.

