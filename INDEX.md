# Backend Documentation Index

Complete guide to the doWhat backend infrastructure and deployment.

## 📚 Documentation Structure

### 🚀 Getting Started
1. **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
   - Automated setup script
   - Manual setup instructions
   - Common tasks and troubleshooting

2. **[README.md](README.md)** - Complete backend guide
   - Project structure
   - Development workflow
   - API documentation
   - Testing guide

### 🐳 Docker & DevOps
3. **[DOCKER_ARCHITECTURE.md](DOCKER_ARCHITECTURE.md)** - Architecture overview
   - Visual diagrams
   - Container specifications
   - Network architecture
   - Scaling strategies

4. **[DEVOPS_SUMMARY.md](DEVOPS_SUMMARY.md)** - DevOps setup summary
   - Files created
   - Quick commands
   - Security features
   - Production checklist

### 🌐 Deployment
5. **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment guide
   - Railway deployment (recommended)
   - AWS, Azure, DigitalOcean
   - CI/CD pipeline
   - Monitoring setup
   - Rollback procedures

## 📁 Configuration Files

### Docker
- `Dockerfile` - Production container
- `Dockerfile.dev` - Development container
- `docker-compose.yml` - Local development
- `docker-compose.prod.yml` - Production setup
- `.dockerignore` - Build optimization

### Environment
- `env.example` - Environment template
- `.env` - Your local config (git-ignored)
- `.gitignore` - Git ignore patterns

### Build Tools
- `requirements.txt` - Python dependencies
- `Makefile` - Convenience commands
- `railway.toml` - Railway deployment

### Database
- `alembic.ini` - Migration config
- `alembic/env.py` - Migration environment
- `alembic/script.py.mako` - Migration template

### Web Server
- `nginx/nginx.conf` - Reverse proxy config

### CI/CD
- `.github/workflows/ci.yml` - GitHub Actions pipeline

## 🛠️ Scripts

### Setup & Utilities
- `scripts/setup.sh` - Automated setup (Linux/Mac)
- `scripts/health_check.sh` - Health monitoring

## 🎯 Quick Reference

### Local Development
```bash
# Quick start
./scripts/setup.sh              # Linux/Mac
docker-compose up -d            # Windows

# Common tasks
make logs                       # View logs
make shell                      # Open shell
make test                       # Run tests
make db-migrate                 # Run migrations
```

### Production Deployment
```bash
# Railway (recommended)
railway login
railway up

# Docker
docker-compose -f docker-compose.prod.yml up -d

# See DEPLOYMENT.md for more options
```

### Monitoring
```bash
# Health check
curl http://localhost:8000/health

# Container stats
docker stats

# Service logs
docker-compose logs -f api
```

## 📊 Architecture Components

### Services
| Service | Port | Description | Docs |
|---------|------|-------------|------|
| API | 8000 | FastAPI backend | [README.md](README.md) |
| Redis | 6379 | Cache & queue | [DOCKER_ARCHITECTURE.md](DOCKER_ARCHITECTURE.md) |
| Worker | - | Background jobs | [README.md](README.md) |
| Scheduler | - | Cron jobs | [README.md](README.md) |
| Nginx | 80/443 | Reverse proxy | [DEPLOYMENT.md](DEPLOYMENT.md) |

### External Services
| Service | Purpose | Setup |
|---------|---------|-------|
| Supabase | PostgreSQL database | [env.example](env.example) |
| Redis Cloud | Managed Redis | [DEPLOYMENT.md](DEPLOYMENT.md) |
| Cloudinary | Image CDN | [env.example](env.example) |
| OpenAI | Category inference | [env.example](env.example) |
| Sentry | Error tracking | [DEPLOYMENT.md](DEPLOYMENT.md) |

## 🔑 Key Concepts

### Docker Services
- **API Server**: FastAPI with 4 Uvicorn workers
- **Worker Pool**: RQ workers for background jobs
- **Scheduler**: Cron-based job scheduler
- **Redis**: Cache, queue, and rate limiting

### Data Flow
1. Mobile App → API Server
2. API checks Redis cache
3. If miss, query Supabase
4. Apply personalization
5. Cache and return

### Background Jobs
- Event scraping (every 6 hours)
- Category inference (OpenAI)
- Image upload (Cloudinary)
- Deduplication
- Cleanup tasks

## 📖 Reading Path

### For Solo Founders (Quick Start)
1. ✅ [QUICKSTART.md](QUICKSTART.md) - Get running
2. ✅ [README.md](README.md) - Understand basics
3. ✅ [DEPLOYMENT.md](DEPLOYMENT.md) - Deploy to Railway

### For DevOps Engineers
1. ✅ [DEVOPS_SUMMARY.md](DEVOPS_SUMMARY.md) - Overview
2. ✅ [DOCKER_ARCHITECTURE.md](DOCKER_ARCHITECTURE.md) - Architecture
3. ✅ [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment
4. ✅ Configuration files review

### For Backend Developers
1. ✅ [README.md](README.md) - Complete guide
2. ✅ [QUICKSTART.md](QUICKSTART.md) - Local setup
3. ✅ API documentation at `/docs`
4. ✅ Review `app/` directory structure

## 🔍 Finding Information

### How do I...?

**Set up locally**
→ [QUICKSTART.md](QUICKSTART.md)

**Deploy to production**
→ [DEPLOYMENT.md](DEPLOYMENT.md)

**Understand the architecture**
→ [DOCKER_ARCHITECTURE.md](DOCKER_ARCHITECTURE.md)

**Run database migrations**
→ [README.md](README.md#database-migrations)

**Scale the application**
→ [DOCKER_ARCHITECTURE.md](DOCKER_ARCHITECTURE.md#scaling-strategies)

**Configure environment variables**
→ [env.example](env.example)

**Set up CI/CD**
→ [.github/workflows/ci.yml](.github/workflows/ci.yml)

**Monitor services**
→ [DEPLOYMENT.md](DEPLOYMENT.md#monitoring-setup)

**Troubleshoot issues**
→ [QUICKSTART.md](QUICKSTART.md#troubleshooting)

**Secure the application**
→ [DEPLOYMENT.md](DEPLOYMENT.md#security-best-practices)

## 🎓 Learning Resources

### Internal Documentation
- [System Architecture](../project-documentation/system-architecture.md)
- [Event App Overview](../project-documentation/event-app-overview.md)
- [Tech Stack Preferences](../tech-stack-pref.md)

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Railway Documentation](https://docs.railway.app/)
- [Supabase Documentation](https://supabase.com/docs)
- [Redis Documentation](https://redis.io/docs/)

## ✅ Checklists

### Initial Setup Checklist
- [ ] Docker installed
- [ ] Environment configured (`.env`)
- [ ] Services running (`docker-compose ps`)
- [ ] API responding (`/health`)
- [ ] Migrations applied
- [ ] Tests passing

### Deployment Checklist
- [ ] All tests passing
- [ ] Security scan clean
- [ ] Environment variables set
- [ ] Database backed up
- [ ] Monitoring configured
- [ ] SSL/TLS enabled
- [ ] Rollback plan ready

### Production Readiness
- [ ] Load testing completed
- [ ] Error tracking active
- [ ] Backups automated
- [ ] Alerts configured
- [ ] Documentation complete
- [ ] Team trained

## 🆘 Support & Help

### Troubleshooting Steps
1. Check [QUICKSTART.md](QUICKSTART.md#troubleshooting)
2. Review service logs: `make logs`
3. Run health check: `make health`
4. Check Docker status: `docker-compose ps`
5. Review relevant documentation

### Getting Help
- Check documentation in this index
- Review configuration files
- Check system logs
- Open GitHub issue

## 🔄 Maintenance

### Regular Tasks
- Update dependencies: `pip install -U -r requirements.txt`
- Rebuild images: `make build`
- Run security scans: `docker scan dowhat-api`
- Review logs: `make logs`
- Check health: `make health`

### Updates
- Pull latest code: `git pull`
- Rebuild: `make build`
- Restart: `make restart`
- Run migrations: `make db-migrate`

## 📊 Metrics & KPIs

### Development Metrics
- Build time: < 2 minutes
- Test coverage: > 80%
- Startup time: < 30 seconds
- Hot reload: < 2 seconds

### Production Metrics
- API response time: < 500ms (p95)
- Uptime: > 99.9%
- Error rate: < 0.1%
- Worker queue: < 10 jobs

## 🚀 Next Steps

### After Setup
1. ✅ Explore API docs: http://localhost:8000/docs
2. ✅ Run tests: `make test`
3. ✅ Review code structure in `app/`
4. ✅ Understand data models in `app/models/`
5. ✅ Check API routes in `app/routers/`

### For Deployment
1. ✅ Follow [DEPLOYMENT.md](DEPLOYMENT.md)
2. ✅ Set up monitoring
3. ✅ Configure alerts
4. ✅ Run load tests
5. ✅ Document runbooks

---

**📚 Start with [QUICKSTART.md](QUICKSTART.md) to get the backend running!**

**🚀 Deploy with [DEPLOYMENT.md](DEPLOYMENT.md) when ready for production!**

**🏗️ Understand architecture with [DOCKER_ARCHITECTURE.md](DOCKER_ARCHITECTURE.md)!**

