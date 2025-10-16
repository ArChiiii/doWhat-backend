# doWhat Backend API

Event discovery API for Hong Kong built with FastAPI, PostgreSQL (Supabase), Redis, and RQ workers.

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for local development)
- Make (optional, for convenience commands)

### Local Development Setup

1. **Clone the repository and navigate to backend directory**
```bash
cd backend
```

2. **Copy environment variables**
```bash
cp env.example .env
```

3. **Update `.env` with your credentials**
   - Supabase credentials (required)
   - OpenAI API key (required for category inference)
   - Cloudinary credentials (required for image uploads)
   - Other API keys as needed

4. **Start all services**
```bash
# Using Make (recommended)
make up

# Or using Docker Compose directly
docker-compose up -d
```

5. **Set up Supabase and run database migrations**

**Important**: This project uses **Supabase CLI** for migrations, not Alembic.

First, set up your Supabase project following the [Supabase Setup Guide](./docs/SUPABASE_SETUP.md).

Then, run migrations:

```bash
# Install Supabase CLI (if not already installed)
npm install -g supabase

# Link to your Supabase project
supabase link --project-ref your-project-ref

# Push migrations to Supabase
supabase db push

# Or run migrations manually in Supabase Dashboard > SQL Editor
# Copy contents of supabase/migrations/*.sql files
```

6. **Access the application**
   - API: http://localhost:8000
   - API Docs (Swagger): http://localhost:8000/docs
   - Redis Commander (dev tools): http://localhost:8081

### Using Make Commands

```bash
make help           # Show all available commands
make build          # Build Docker containers
make up             # Start all services
make down           # Stop all services
make logs           # Show logs
make shell          # Open shell in API container
make test           # Run tests
make db-migrate     # Run migrations
```

## 📁 Project Structure

```
backend/
├── app/                        # FastAPI application
│   ├── main.py                # Entry point
│   ├── config.py              # Configuration
│   ├── database.py            # Database connection
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # Pydantic schemas
│   ├── routers/               # API endpoints
│   ├── services/              # Business logic
│   ├── middleware/            # Custom middleware
│   └── utils/                 # Utilities
├── scrapers/                  # Web scraping services
│   ├── base_scraper.py        # Base scraper class
│   ├── popticket_scraper.py   # PopTicket scraper
│   ├── eventbrite_scraper.py  # Eventbrite API client
│   ├── deduplication.py       # Duplicate detection
│   └── image_uploader.py      # Cloudinary integration
├── jobs/                      # RQ background jobs
│   ├── worker.py              # RQ worker
│   ├── scheduler.py           # Job scheduler
│   ├── scraper_job.py         # Scraper jobs
│   └── cleanup_job.py         # Cleanup jobs
├── supabase/                  # Supabase migrations and config
│   ├── migrations/            # SQL migration files
│   └── config.toml            # Supabase CLI config
├── tests/                     # Test suite
├── Dockerfile                 # Production Dockerfile
├── Dockerfile.dev             # Development Dockerfile
├── docker-compose.yml         # Local orchestration
├── railway.toml               # Railway deployment config
├── requirements.txt           # Python dependencies
└── Makefile                   # Convenience commands
```

## 🔐 Authentication

The doWhat API uses **JWT (JSON Web Tokens)** with **Supabase Auth** for user authentication.

### Features
- Email/Password registration and login
- Google OAuth (optional)
- JWT access tokens (15 min expiry)
- Refresh tokens (30 day expiry)
- Secure token storage with Expo SecureStore (mobile)

### Quick Start

**Register a new user:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!"}'
```

**Access protected endpoint:**
```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <access_token>"
```

**Refresh access token:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Authorization: Bearer <refresh_token>"
```

### Documentation
- [Authentication Guide](./docs/AUTHENTICATION.md) - Complete authentication implementation guide
- [Supabase Setup](./docs/SUPABASE_SETUP.md) - Database and auth configuration

### API Endpoints
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login with email/password
- `POST /api/v1/auth/google` - Login with Google OAuth
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user info (requires auth)

See full API documentation at http://localhost:8000/docs

## 🐳 Docker Services

### API Service
- **Port**: 8000
- **Description**: FastAPI backend with 4 Uvicorn workers
- **Hot Reload**: Enabled in development mode

### Worker Service
- **Description**: RQ worker for background jobs (scrapers, cleanup)
- **Queues**: `scrapers`, `cleanup`

### Scheduler Service
- **Description**: RQ scheduler for cron jobs
- **Schedule**: Runs scrapers every 6 hours

### Redis Service
- **Port**: 6379
- **Description**: In-memory cache and job queue
- **Persistence**: Enabled with AOF

### Redis Commander (Dev Tools)
- **Port**: 8081
- **Description**: Web UI for Redis
- **Usage**: `docker-compose --profile dev-tools up -d`

## 🗄️ Database Migrations

**Important**: This project uses **Supabase CLI** for migrations, not Alembic.

See [Supabase Setup Guide](./docs/SUPABASE_SETUP.md) for detailed instructions.

### Apply migrations
```bash
# Push all migrations to Supabase
supabase db push

# Or run manually in Supabase Dashboard > SQL Editor
# Copy contents of supabase/migrations/*.sql files
```

### View migration status
```bash
supabase migration list
```

### Create a new migration
```bash
# Create empty migration file
supabase migration new your_migration_name

# Edit the file in supabase/migrations/
# Add your SQL statements
```

### Rollback (development only)
```bash
# WARNING: This will drop all tables and data
# Run the rollback migration in Supabase SQL Editor
# File: supabase/migrations/20251014999999_rollback_all.sql
```

## 🧪 Testing

### Run all tests
```bash
make test
```

### Run tests with coverage
```bash
make test-cov
```

### Run specific test file
```bash
docker-compose exec api pytest tests/test_auth.py -v
```

## 📝 Code Quality

### Format code
```bash
make format
```

### Lint code
```bash
make lint
```

### Fix linting issues
```bash
make lint-fix
```

## 🔍 Debugging

### View logs
```bash
# All services
make logs

# API only
make logs-api

# Worker only
make logs-worker
```

### Open shell in container
```bash
# API container
make shell

# Worker container
make shell-worker
```

### Check worker status
```bash
make worker-status
```

### Access Redis CLI
```bash
make redis-cli
```

## 🚀 Deployment

### Railway (Recommended)

1. **Install Railway CLI**
```bash
npm install -g @railway/cli
```

2. **Login and link project**
```bash
railway login
railway link
```

3. **Set environment variables**
```bash
railway variables set SUPABASE_URL=https://your-project.supabase.co
railway variables set OPENAI_API_KEY=sk-proj-...
# ... (add all variables from env.example)
```

4. **Deploy**
```bash
railway up
```

### Manual Deployment

1. **Build production image**
```bash
docker build -t dowhat-api:latest .
```

2. **Run migrations**
```bash
docker run --env-file .env dowhat-api:latest alembic upgrade head
```

3. **Start services**
```bash
docker run -p 8000:8000 --env-file .env dowhat-api:latest
```

## 🔧 Configuration

### Environment Variables

See `env.example` for all available configuration options.

**Required Variables:**
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET_KEY`: Secret key for JWT tokens (generate with `openssl rand -hex 32`)
- `OPENAI_API_KEY`: OpenAI API key for category inference
- `CLOUDINARY_*`: Cloudinary credentials for image uploads

**Optional Variables:**
- `GOOGLE_MAPS_API_KEY`: For geocoding
- `EVENTBRITE_API_KEY`: For Eventbrite scraper
- `MIXPANEL_TOKEN`: For analytics
- `SENTRY_DSN`: For error tracking

### Cache Configuration

Redis cache keys and TTL values:
- Event feed: `feed:user:{user_id}:filters:{hash}` (5 min TTL)
- User preferences: `user:preferences:{user_id}` (1 hour TTL)
- Event details: `event:details:{event_id}` (10 min TTL)
- Rate limiting: `rate_limit:{user_id|ip}:{minute}` (1 min TTL)

## 🔒 Security

### JWT Tokens
- **Access Token**: 15 minutes expiry
- **Refresh Token**: 30 days expiry
- **Algorithm**: HS256

### Rate Limiting
- **Default**: 100 requests per minute per user/IP
- **Configurable**: Set `RATE_LIMIT_PER_MINUTE` in `.env`

### Secrets Management
- Never commit `.env` file
- Use strong JWT secret key (32+ characters)
- Rotate credentials regularly

## 📊 Monitoring

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Or using Make
make health
```

### Container Stats
```bash
make stats
```

### Worker Queue Status
```bash
make worker-status
```

## 🐛 Troubleshooting

### Port already in use
```bash
# Stop conflicting services
sudo lsof -i :8000  # Find process using port 8000
sudo kill -9 <PID>  # Kill the process

# Or change port in docker-compose.yml
```

### Database connection errors
```bash
# Check Supabase connection
psql $DATABASE_URL

# Verify environment variables
docker-compose exec api env | grep DATABASE_URL
```

### Redis connection errors
```bash
# Check Redis status
make redis-cli
> ping
PONG

# Restart Redis
docker-compose restart redis
```

### Worker not processing jobs
```bash
# Check worker logs
make logs-worker

# Restart worker
make restart-worker

# Clear queue (if stuck)
make queue-clear
```

### Migration errors
```bash
# Check migration status
docker-compose exec api alembic current

# View migration history
docker-compose exec api alembic history

# Reset and re-run (WARNING: destroys data)
make db-reset
```

## 🤝 Contributing

1. Create feature branch
2. Make changes with tests
3. Run `make format` and `make lint`
4. Run `make test` to ensure all tests pass
5. Submit pull request

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📄 License

See main project LICENSE file.

## 🆘 Support

For issues or questions:
1. Check this README
2. Review system architecture documentation
3. Check Docker logs: `make logs`
4. Open an issue on GitHub

