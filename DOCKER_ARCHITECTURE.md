# Docker Architecture Overview

Visual representation of the doWhat backend Docker infrastructure.

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL CLIENTS                             │
│                    (Mobile App, Web Browser)                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTPS
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      NGINX REVERSE PROXY                             │
│                  (Optional - Production Only)                        │
│  - SSL Termination                                                   │
│  - Rate Limiting                                                     │
│  - Load Balancing                                                    │
│  - Security Headers                                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         FASTAPI API SERVER                           │
│                      (Port 8000 - 4 workers)                         │
├─────────────────────────────────────────────────────────────────────┤
│  Container: dowhat-api                                               │
│  Image: dowhat-api:latest                                           │
│  Resources:                                                          │
│    CPU: 0.5-2 cores                                                 │
│    Memory: 512MB-2GB                                                │
│                                                                      │
│  Features:                                                           │
│    ✓ JWT Authentication                                             │
│    ✓ Rate Limiting (Redis)                                          │
│    ✓ CORS Middleware                                                │
│    ✓ Error Tracking (Sentry)                                        │
│    ✓ Health Checks                                                  │
│                                                                      │
│  Endpoints:                                                          │
│    /api/v1/auth/*      - Authentication                             │
│    /api/v1/events/*    - Events API                                 │
│    /api/v1/users/*     - User Management                            │
│    /health             - Health Check                               │
│    /docs               - Swagger UI                                 │
└────┬─────────────┬─────────────────┬──────────────────┬────────────┘
     │             │                 │                  │
     ↓             ↓                 ↓                  ↓
┌─────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ REDIS   │  │   SUPABASE   │  │   CLOUDINARY │  │   OPENAI API     │
│ CACHE   │  │   DATABASE   │  │   CDN        │  │   GPT-4o-mini    │
└─────────┘  └──────────────┘  └──────────────┘  └──────────────────┘
     ↑             ↑
     │             │
┌────┴─────────────┴──────────────────────────────────────────────────┐
│                       BACKGROUND WORKERS                             │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │               RQ WORKER (1-5 instances)                      │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │  Container: dowhat-worker                                     │   │
│  │  Command: python jobs/worker.py                              │   │
│  │  Queues: scrapers, cleanup                                   │   │
│  │                                                               │   │
│  │  Jobs:                                                        │   │
│  │    • PopTicket Scraper (Puppeteer)                          │   │
│  │    • Eventbrite Scraper (API)                               │   │
│  │    • Image Upload (Cloudinary)                              │   │
│  │    • Category Inference (OpenAI)                            │   │
│  │    • Deduplication Engine                                    │   │
│  │    • Event Cleanup                                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    RQ SCHEDULER                              │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │  Container: dowhat-scheduler                                  │   │
│  │  Command: python jobs/scheduler.py                           │   │
│  │                                                               │   │
│  │  Cron Jobs:                                                   │   │
│  │    • Run scrapers every 6 hours                             │   │
│  │    • Cleanup expired events daily                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────┘
                             ↑
                             │
┌────────────────────────────┴───────────────────────────────────────┐
│                         REDIS SERVER                                │
│                      (Port 6379 - In-memory)                        │
├─────────────────────────────────────────────────────────────────────┤
│  Container: dowhat-redis                                            │
│  Image: redis:7-alpine                                             │
│  Resources:                                                         │
│    CPU: 0.5-1 core                                                 │
│    Memory: 256MB-512MB                                             │
│                                                                     │
│  Data Structures:                                                   │
│    • Feed Cache (5 min TTL)                                        │
│    • User Preferences (1 hour TTL)                                 │
│    • RQ Job Queues                                                 │
│    • Rate Limit Counters                                           │
│    • Swipe Queue (offline support)                                 │
│                                                                     │
│  Persistence: AOF (Append-Only File)                               │
│  Eviction: allkeys-lru (production)                                │
└─────────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow

### 1. Event Feed Request Flow
```
Mobile App → Nginx → API Server → Check Redis Cache
                                    ↓ Cache Miss
                                    Query Supabase
                                    ↓
                                    Apply Personalization
                                    ↓
                                    Store in Redis
                                    ↓
                                    Return JSON
```

### 2. Scraper Job Flow
```
RQ Scheduler → Enqueue Job to Redis
                ↓
RQ Worker → Dequeue Job
          → Scrape Source (PopTicket/Eventbrite)
          → Infer Category (OpenAI)
          → Upload Image (Cloudinary)
          → Check Duplicates
          → Save to Supabase
          → Mark Job Complete
```

### 3. Swipe Action Flow
```
Mobile App → API → Validate JWT
              → Record Swipe (Supabase)
              → Update Interest Count
              → Invalidate Cache (Redis)
              → Return Response
```

## 🐳 Container Specifications

### API Server Container
```dockerfile
FROM python:3.12-slim
WORKDIR /app
# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential libpq-dev curl
# Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
# Application code
COPY app ./app
COPY scrapers ./scrapers
COPY jobs ./jobs
# Non-root user
RUN useradd -m appuser
USER appuser
# Health check
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/health
# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Resource Allocation:**
- Development: 512MB RAM, 0.5 CPU
- Production: 1-2GB RAM, 1-2 CPU
- Scaling: Horizontal (1-10 instances)

### Worker Container
```dockerfile
FROM python:3.12-slim
# ... (same base as API)
# Start worker
CMD ["python", "jobs/worker.py"]
```

**Resource Allocation:**
- Development: 512MB RAM, 0.5 CPU
- Production: 1GB RAM, 1 CPU
- Scaling: Horizontal (1-5 workers)

### Redis Container
```dockerfile
FROM redis:7-alpine
# Custom config
CMD redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
```

**Resource Allocation:**
- Development: 256MB RAM
- Production: 256-512MB RAM
- Persistence: AOF enabled

## 🌐 Network Architecture

### Development Network
```yaml
networks:
  dowhat-network:
    driver: bridge
```

Services communicate via Docker DNS:
- `api:8000` - API Server
- `redis:6379` - Redis Server
- `worker` - Background Worker
- `scheduler` - Job Scheduler

### Production Network
```yaml
networks:
  dowhat-prod-network:
    driver: bridge
```

Additional isolation:
- External access only via Nginx
- Internal services communicate privately
- Redis not exposed externally

## 💾 Volume Management

### Development Volumes
```yaml
volumes:
  - ./app:/app/app           # Hot reload
  - ./scrapers:/app/scrapers # Hot reload
  - redis-data:/data         # Redis persistence
```

### Production Volumes
```yaml
volumes:
  - redis-prod-data:/data    # Redis persistence only
```

## 🔐 Security Features

### Container Security
- ✅ Non-root user (UID 1000)
- ✅ Read-only file system (where possible)
- ✅ No privileged containers
- ✅ Resource limits enforced
- ✅ Security scanning (Trivy)
- ✅ Minimal base images (Alpine)

### Network Security
- ✅ Internal network isolation
- ✅ No unnecessary port exposure
- ✅ TLS/SSL via Nginx
- ✅ Rate limiting (Nginx + Redis)
- ✅ CORS restrictions

### Runtime Security
- ✅ Secrets via environment variables
- ✅ Health checks for all services
- ✅ Automatic restarts
- ✅ Log aggregation
- ✅ Error tracking (Sentry)

## 🚀 Deployment Modes

### Local Development
```bash
docker-compose up -d
```
- Hot reload enabled
- Debug tools included
- Redis Commander UI
- Verbose logging
- No resource limits

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```
- Optimized builds
- Resource limits
- Multiple workers
- No dev tools
- Production logging

### Railway (Cloud)
```bash
railway up
```
- Managed infrastructure
- Auto-scaling
- Zero-downtime deploys
- Built-in monitoring
- Automatic SSL

## 📊 Monitoring & Observability

### Health Checks
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Logging
- Container logs: `docker-compose logs -f`
- Application logs: JSON structured
- Error tracking: Sentry
- Access logs: Nginx (production)

### Metrics
- Container stats: `docker stats`
- Redis metrics: Redis Commander
- API metrics: `/metrics` endpoint (optional)
- Worker metrics: RQ dashboard

## 🔄 Scaling Strategies

### Horizontal Scaling

**API Servers:**
```bash
docker-compose up -d --scale api=3
```
- Add load balancer (Nginx)
- Session affinity not required (stateless)
- Scale: 1-10 instances

**Workers:**
```bash
docker-compose up -d --scale worker=5
```
- RQ automatically distributes jobs
- Scale based on queue length
- Scale: 1-5 workers

### Vertical Scaling
Update resource limits:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
```

### Database Scaling
- Read replicas (Supabase)
- Connection pooling (PgBouncer)
- Query optimization

### Cache Scaling
- Redis cluster (high availability)
- Redis Sentinel (failover)
- Separate cache per region

## 🔧 Maintenance

### Updates
```bash
# Pull latest images
docker-compose pull

# Rebuild with new code
docker-compose build --no-cache

# Zero-downtime update
docker-compose up -d --force-recreate
```

### Backups
```bash
# Backup Redis data
docker-compose exec redis redis-cli BGSAVE

# Backup volumes
docker run --rm -v redis-data:/data -v $(pwd)/backup:/backup alpine tar czf /backup/redis-backup.tar.gz /data
```

### Cleanup
```bash
# Remove stopped containers
docker-compose down

# Remove volumes
docker-compose down -v

# Clean system
docker system prune -af --volumes
```

## 📝 Configuration Files

### docker-compose.yml
Local development configuration with:
- Hot reload
- Debug tools
- Redis Commander
- No resource limits

### docker-compose.prod.yml
Production configuration with:
- Optimized builds
- Resource limits
- Multiple replicas
- Health checks
- Nginx proxy

### Dockerfile
Multi-stage production build:
- Minimal image size
- Security hardened
- Non-root user
- Health checks

### Dockerfile.dev
Development build:
- Hot reload
- Debug tools
- Development packages
- No optimization

## ✅ Pre-flight Checklist

### Before Running Locally
- [ ] Docker installed and running
- [ ] `.env` file configured
- [ ] Required API keys obtained
- [ ] Ports 8000, 6379 available

### Before Deploying to Production
- [ ] All tests passing
- [ ] Security scan completed
- [ ] Secrets in vault
- [ ] SSL certificates ready
- [ ] Monitoring configured
- [ ] Backup strategy defined
- [ ] Rollback plan ready
- [ ] Team trained

## 🆘 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs <service>

# Check container status
docker-compose ps

# Rebuild
docker-compose build --no-cache <service>
```

### Network Issues
```bash
# Check network
docker network ls
docker network inspect dowhat-network

# Recreate network
docker-compose down
docker-compose up -d
```

### Resource Issues
```bash
# Check resource usage
docker stats

# Increase limits in docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
```

---

**For complete setup instructions, see [QUICKSTART.md](QUICKSTART.md)**

