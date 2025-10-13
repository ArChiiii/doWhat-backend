.PHONY: help build up down logs clean test migrate shell redis-cli format lint

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all Docker containers
	docker-compose build

build-dev: ## Build development containers
	docker-compose -f docker-compose.yml build

up: ## Start all services in detached mode
	docker-compose up -d

up-dev: ## Start development services with logs
	docker-compose -f docker-compose.yml up

down: ## Stop all services
	docker-compose down

down-clean: ## Stop all services and remove volumes
	docker-compose down -v

logs: ## Show logs for all services
	docker-compose logs -f

logs-api: ## Show logs for API service
	docker-compose logs -f api

logs-worker: ## Show logs for worker service
	docker-compose logs -f worker

logs-scheduler: ## Show logs for scheduler service
	docker-compose logs -f scheduler

clean: ## Remove all containers, volumes, and images
	docker-compose down -v --rmi all

restart: ## Restart all services
	docker-compose restart

restart-api: ## Restart API service only
	docker-compose restart api

restart-worker: ## Restart worker service only
	docker-compose restart worker

shell: ## Open a shell in the API container
	docker-compose exec api /bin/sh

shell-worker: ## Open a shell in the worker container
	docker-compose exec worker /bin/sh

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

db-migrate: ## Run database migrations
	docker-compose exec api alembic upgrade head

db-migrate-create: ## Create a new migration (usage: make db-migrate-create MESSAGE="description")
	docker-compose exec api alembic revision --autogenerate -m "$(MESSAGE)"

db-downgrade: ## Rollback last migration
	docker-compose exec api alembic downgrade -1

db-reset: ## Reset database (WARNING: destroys all data)
	docker-compose down -v
	docker-compose up -d db
	sleep 5
	docker-compose exec api alembic upgrade head

test: ## Run tests
	docker-compose exec api pytest -v

test-cov: ## Run tests with coverage
	docker-compose exec api pytest --cov=app --cov-report=html --cov-report=term

format: ## Format code with black
	docker-compose exec api black app/ scrapers/ jobs/

lint: ## Lint code with ruff
	docker-compose exec api ruff check app/ scrapers/ jobs/

lint-fix: ## Fix linting issues
	docker-compose exec api ruff check --fix app/ scrapers/ jobs/

dev-tools: ## Start development tools (Redis Commander)
	docker-compose --profile dev-tools up -d

ps: ## Show running containers
	docker-compose ps

stats: ## Show container resource usage
	docker stats

install-local: ## Install dependencies locally (for IDE support)
	pip install -r requirements.txt

worker-status: ## Check RQ worker status
	docker-compose exec worker rq info --url redis://redis:6379

queue-clear: ## Clear all RQ queues
	docker-compose exec redis redis-cli FLUSHALL

health: ## Check health of all services
	@echo "Checking API health..."
	@curl -f http://localhost:8000/health || echo "API is down"
	@echo "\nChecking Redis health..."
	@docker-compose exec redis redis-cli ping || echo "Redis is down"

