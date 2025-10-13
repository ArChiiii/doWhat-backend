# 🚀 Quick Start Guide

Get the doWhat backend running in 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- Git installed
- Text editor (VS Code, Vim, etc.)

## Option 1: Automated Setup (Recommended)

### Step 1: Run Setup Script

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

The script will:
1. ✓ Check prerequisites
2. ✓ Create `.env` from template
3. ✓ Generate JWT secret key
4. ✓ Build Docker images
5. ✓ Start all services
6. ✓ Run database migrations

### Step 2: Update Environment Variables

When prompted, update `.env` with your actual credentials:

**Required:**
- `SUPABASE_URL` - Get from [Supabase Dashboard](https://supabase.com)
- `SUPABASE_ANON_KEY` - Get from Supabase Dashboard
- `DATABASE_URL` - PostgreSQL connection string from Supabase
- `OPENAI_API_KEY` - Get from [OpenAI Platform](https://platform.openai.com)
- `CLOUDINARY_*` - Get from [Cloudinary Dashboard](https://cloudinary.com)

**Optional (but recommended):**
- `GOOGLE_MAPS_API_KEY` - For geocoding
- `EVENTBRITE_API_KEY` - For Eventbrite scraper
- `SENTRY_DSN` - For error tracking

### Step 3: Verify Setup

```bash
# Check API health
curl http://localhost:8000/health

# Open API documentation
open http://localhost:8000/docs
```

✅ **You're done!** The backend is running.

---

## Option 2: Manual Setup

### Step 1: Clone & Navigate

```bash
cd backend
```

### Step 2: Configure Environment

```bash
cp env.example .env
```

Edit `.env` and update:
- Database credentials (Supabase)
- API keys (OpenAI, Cloudinary)
- JWT secret: `openssl rand -hex 32`

### Step 3: Build & Start

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head
```

### Step 4: Verify

```bash
# Check logs
docker-compose logs -f

# Test API
curl http://localhost:8000/health
```

---

## 🎯 What's Running?

After successful setup:

| Service | Port | Description |
|---------|------|-------------|
| API | 8000 | FastAPI backend |
| Swagger UI | 8000/docs | API documentation |
| Redis | 6379 | Cache & job queue |
| Redis Commander | 8081 | Redis GUI (dev mode) |
| Worker | - | Background jobs |
| Scheduler | - | Cron jobs |

---

## 🔧 Common Tasks

### View Logs
```bash
make logs
# or
docker-compose logs -f
```

### Open Shell
```bash
make shell
# or
docker-compose exec api sh
```

### Run Tests
```bash
make test
# or
docker-compose exec api pytest
```

### Stop Services
```bash
make down
# or
docker-compose down
```

### Restart Services
```bash
make restart
# or
docker-compose restart
```

---

## 📚 Next Steps

1. **Read the full documentation**
   - [README.md](README.md) - Complete guide
   - [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide

2. **Explore API endpoints**
   - Open http://localhost:8000/docs
   - Try the interactive API documentation

3. **Run tests**
   ```bash
   make test
   ```

4. **Set up your frontend**
   - The API is now ready for frontend integration
   - See frontend documentation

5. **Deploy to production**
   - Follow [DEPLOYMENT.md](DEPLOYMENT.md)
   - Railway deployment is recommended

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>
```

### Docker Build Fails
```bash
# Clean build
docker-compose down -v
docker system prune -f
docker-compose build --no-cache
```

### Database Connection Error
```bash
# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Test connection
docker-compose exec api psql $DATABASE_URL -c "SELECT 1"
```

### Migration Fails
```bash
# Check migration status
docker-compose exec api alembic current

# Reset database (WARNING: destroys data)
make db-reset
```

### Services Won't Start
```bash
# Check logs for errors
docker-compose logs api
docker-compose logs worker

# Check container status
docker-compose ps
```

---

## 💡 Tips

### Using Make Commands

If you have `make` installed:

```bash
make help      # Show all commands
make up        # Start services
make down      # Stop services
make logs      # View logs
make shell     # Open shell
make test      # Run tests
make db-migrate # Run migrations
```

### Development vs Production

**Development mode** (default):
- Hot reload enabled
- Debug tools included
- Redis Commander UI
- Verbose logging

**Production mode**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```
- Optimized performance
- Security hardened
- No debug tools
- Resource limits

### Health Checks

Monitor service health:

```bash
# Run health check script
chmod +x scripts/health_check.sh
./scripts/health_check.sh

# Or use Make
make health

# Or manually
curl http://localhost:8000/health
```

---

## 📞 Get Help

If you're stuck:

1. Check logs: `make logs`
2. Review [README.md](README.md)
3. Check [DEPLOYMENT.md](DEPLOYMENT.md)
4. Open an issue on GitHub

---

## ✅ Success Checklist

- [ ] Docker and Docker Compose installed
- [ ] `.env` file configured with credentials
- [ ] Services running (`docker-compose ps`)
- [ ] API responding (`curl http://localhost:8000/health`)
- [ ] Database migrations applied
- [ ] API docs accessible (`http://localhost:8000/docs`)
- [ ] Tests passing (`make test`)

**All checked?** You're ready to build! 🎉

