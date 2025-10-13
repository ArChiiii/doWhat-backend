# Deployment Guide

Complete guide for deploying the doWhat backend to various platforms.

## 📋 Pre-Deployment Checklist

- [ ] All environment variables configured
- [ ] Database migrations tested
- [ ] SSL certificates obtained (if needed)
- [ ] API keys and secrets generated
- [ ] Monitoring and logging configured
- [ ] Backup strategy defined
- [ ] Security scan completed
- [ ] Load testing performed

## 🚂 Railway Deployment (Recommended)

Railway provides automatic scaling, managed PostgreSQL, and simple deployment.

### Initial Setup

1. **Install Railway CLI**
```bash
npm install -g @railway/cli
railway login
```

2. **Create New Project**
```bash
railway init
```

3. **Link to Existing Project** (if already created)
```bash
railway link
```

### Environment Configuration

Set all environment variables in Railway dashboard or via CLI:

```bash
# Database (Supabase)
railway variables set SUPABASE_URL=https://your-project.supabase.co
railway variables set SUPABASE_ANON_KEY=your-anon-key
railway variables set SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
railway variables set DATABASE_URL=postgresql://postgres:password@db.supabase.co:5432/postgres

# Redis (Railway managed)
railway variables set REDIS_URL=redis://redis.railway.internal:6379

# JWT & Security
railway variables set JWT_SECRET_KEY=$(openssl rand -hex 32)
railway variables set ENVIRONMENT=production
railway variables set DEBUG=false

# Third-Party APIs
railway variables set CLOUDINARY_CLOUD_NAME=your-cloud-name
railway variables set CLOUDINARY_API_KEY=your-api-key
railway variables set CLOUDINARY_API_SECRET=your-api-secret
railway variables set OPENAI_API_KEY=sk-proj-your-key
railway variables set GOOGLE_MAPS_API_KEY=your-google-key
railway variables set EVENTBRITE_API_KEY=your-eventbrite-key

# Monitoring
railway variables set SENTRY_DSN=https://your-dsn@sentry.io/project-id
railway variables set MIXPANEL_TOKEN=your-mixpanel-token

# App Config
railway variables set CORS_ORIGINS=capacitor://localhost,http://localhost,https://dowhat.hk
railway variables set RATE_LIMIT_PER_MINUTE=100
```

### Deploy Services

**1. Deploy API Service**
```bash
railway up --service api
```

**2. Deploy Worker Service**
```bash
railway service create worker
railway up --service worker
```

**3. Deploy Scheduler Service**
```bash
railway service create scheduler
railway up --service scheduler
```

### Run Migrations

```bash
railway run --service api alembic upgrade head
```

### Verify Deployment

```bash
# Check service status
railway status

# View logs
railway logs --service api

# Test API
curl https://your-api.railway.app/health
```

### Scaling

Railway auto-scales based on:
- CPU usage (target: 70%)
- Memory usage (target: 80%)
- Custom metrics

Configure in `railway.toml` or Railway dashboard.

## 🐳 Docker Deployment

### Build Production Image

```bash
docker build -t dowhat-api:latest -f Dockerfile .
```

### Run with Docker Compose

```bash
# Production compose file
docker-compose -f docker-compose.prod.yml up -d
```

### Push to Registry

```bash
# Docker Hub
docker tag dowhat-api:latest username/dowhat-api:latest
docker push username/dowhat-api:latest

# GitHub Container Registry
docker tag dowhat-api:latest ghcr.io/username/dowhat-api:latest
docker push ghcr.io/username/dowhat-api:latest
```

## ☁️ AWS Deployment (ECS/Fargate)

### Prerequisites

- AWS CLI configured
- ECR repository created
- ECS cluster created
- Application Load Balancer configured

### 1. Push Image to ECR

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -t dowhat-api .
docker tag dowhat-api:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/dowhat-api:latest

# Push
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/dowhat-api:latest
```

### 2. Create ECS Task Definition

```json
{
  "family": "dowhat-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/dowhat-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"}
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:dowhat/database-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/dowhat-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### 3. Deploy ECS Service

```bash
aws ecs create-service \
  --cluster dowhat-cluster \
  --service-name dowhat-api \
  --task-definition dowhat-api:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/dowhat-api/12345,containerName=api,containerPort=8000"
```

## 🔵 Azure Deployment (Container Instances)

### 1. Create Resource Group

```bash
az group create --name dowhat-rg --location eastus
```

### 2. Push to Azure Container Registry

```bash
# Create ACR
az acr create --resource-group dowhat-rg --name dowhatacr --sku Basic

# Login
az acr login --name dowhatacr

# Build and push
az acr build --registry dowhatacr --image dowhat-api:latest .
```

### 3. Deploy Container Instance

```bash
az container create \
  --resource-group dowhat-rg \
  --name dowhat-api \
  --image dowhatacr.azurecr.io/dowhat-api:latest \
  --cpu 1 \
  --memory 2 \
  --registry-login-server dowhatacr.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --dns-name-label dowhat-api \
  --ports 8000 \
  --environment-variables \
    ENVIRONMENT=production \
    DEBUG=false \
  --secure-environment-variables \
    DATABASE_URL=<database-url> \
    JWT_SECRET_KEY=<secret-key>
```

## 🌐 DigitalOcean App Platform

### 1. Create app.yaml

```yaml
name: dowhat-api
services:
  - name: api
    github:
      repo: username/dowhat
      branch: main
      deploy_on_push: true
    dockerfile_path: backend/Dockerfile
    http_port: 8000
    instance_count: 2
    instance_size_slug: basic-xs
    routes:
      - path: /
    envs:
      - key: ENVIRONMENT
        value: production
      - key: DATABASE_URL
        scope: RUN_AND_BUILD_TIME
        type: SECRET
      - key: REDIS_URL
        scope: RUN_AND_BUILD_TIME
        type: SECRET
    health_check:
      http_path: /health
      initial_delay_seconds: 60

  - name: worker
    github:
      repo: username/dowhat
      branch: main
    dockerfile_path: backend/Dockerfile
    run_command: python jobs/worker.py
    instance_count: 1

databases:
  - name: redis
    engine: REDIS
    version: "7"
```

### 2. Deploy

```bash
doctl apps create --spec app.yaml
```

## 🔐 Security Best Practices

### 1. SSL/TLS Configuration

```bash
# Let's Encrypt with Certbot
certbot --nginx -d api.dowhat.hk
```

### 2. Secrets Management

**Use managed secret services:**
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- Railway/Render built-in secrets

**Never commit secrets to git!**

### 3. CORS Configuration

Update `CORS_ORIGINS` for production:
```bash
CORS_ORIGINS=https://dowhat.hk,https://app.dowhat.hk
```

### 4. Rate Limiting

Configure appropriate rate limits:
```bash
RATE_LIMIT_PER_MINUTE=100  # Adjust based on traffic
```

## 📊 Monitoring Setup

### 1. Sentry Error Tracking

```bash
railway variables set SENTRY_DSN=https://your-dsn@sentry.io/project-id
```

### 2. Application Monitoring

Deploy monitoring stack:
```bash
# Add to docker-compose.prod.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 3. Log Aggregation

Use managed services:
- Datadog
- LogDNA
- Papertrail
- AWS CloudWatch

## 🔄 CI/CD Pipeline

### GitHub Actions (Automated)

The `.github/workflows/ci.yml` file automatically:
1. Runs tests and security scans
2. Builds Docker image
3. Pushes to registry
4. Deploys to Railway
5. Runs database migrations
6. Performs health checks

### Manual Deployment

```bash
# Tag release
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Deploy specific version
railway up --service api --tag v1.0.0
```

## 🔙 Rollback Strategy

### Railway Rollback

```bash
# List deployments
railway deployments list

# Rollback to specific deployment
railway rollback <deployment-id>
```

### Database Rollback

```bash
# Rollback last migration
railway run --service api alembic downgrade -1

# Rollback to specific version
railway run --service api alembic downgrade <revision>
```

## 🧪 Production Testing

### Health Check

```bash
curl https://your-api.railway.app/health
```

### Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 https://your-api.railway.app/api/v1/events/feed

# Using k6
k6 run loadtest.js
```

### Smoke Tests

```bash
# Test authentication
curl -X POST https://your-api.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'

# Test event feed
curl https://your-api.railway.app/api/v1/events/feed
```

## 📈 Scaling Guidelines

### Horizontal Scaling

**Railway:**
- Auto-scales based on CPU/memory
- Configure in dashboard: Min 1, Max 5 instances

**Manual scaling:**
```bash
railway scale --replicas 3 --service api
```

### Vertical Scaling

Upgrade instance size in Railway dashboard:
- Basic: 0.5 vCPU, 512 MB
- Standard: 1 vCPU, 1 GB
- Pro: 2 vCPU, 2 GB

### Database Scaling

**Read Replicas:**
```bash
# Supabase: Configure in dashboard
# AWS RDS: Create read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier dowhat-db-replica \
  --source-db-instance-identifier dowhat-db
```

### Redis Scaling

**Railway Redis:**
- Auto-scales with usage
- Upgrade plan if needed

**Redis Cluster:**
```bash
# For high availability
docker-compose -f docker-compose.redis-cluster.yml up -d
```

## 🆘 Troubleshooting

### Common Issues

**1. Database Connection Errors**
```bash
# Verify DATABASE_URL
railway variables get DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

**2. Redis Connection Errors**
```bash
# Check Redis status
railway run --service api redis-cli -u $REDIS_URL ping
```

**3. Migration Failures**
```bash
# Check migration status
railway run --service api alembic current

# View migration history
railway run --service api alembic history
```

**4. High Memory Usage**
```bash
# Check container stats
railway logs --service api | grep memory

# Restart service
railway restart --service api
```

### Emergency Procedures

**1. Immediate Rollback**
```bash
railway rollback $(railway deployments list --json | jq -r '.[1].id')
```

**2. Enable Maintenance Mode**
```bash
railway variables set MAINTENANCE_MODE=true
```

**3. Scale Down (if under attack)**
```bash
railway scale --replicas 0 --service api
```

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Performance](https://www.postgresql.org/docs/current/performance-tips.html)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)

## ✅ Post-Deployment Checklist

- [ ] API responding to health checks
- [ ] Database migrations applied
- [ ] Workers processing jobs
- [ ] Logs flowing to monitoring service
- [ ] Error tracking active (Sentry)
- [ ] Alerts configured
- [ ] SSL certificate valid
- [ ] CORS configured correctly
- [ ] Rate limiting working
- [ ] Backups scheduled
- [ ] Documentation updated
- [ ] Team notified

