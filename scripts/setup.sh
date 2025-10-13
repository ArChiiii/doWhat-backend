#!/bin/bash

# doWhat Backend Setup Script
# This script automates the initial setup process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        return 1
    else
        log_info "$1 is installed ✓"
        return 0
    fi
}

# Header
echo ""
echo "╔════════════════════════════════════════╗"
echo "║   doWhat Backend Setup Script          ║"
echo "╔════════════════════════════════════════╗"
echo ""

# Check prerequisites
log_step "Checking prerequisites..."
echo ""

PREREQS_OK=true

if ! check_command docker; then
    PREREQS_OK=false
fi

if ! check_command docker-compose; then
    PREREQS_OK=false
fi

if [ "$PREREQS_OK" = false ]; then
    log_error "Please install missing prerequisites and run this script again."
    exit 1
fi

echo ""

# Check if .env file exists
log_step "Checking environment configuration..."
echo ""

if [ ! -f .env ]; then
    log_warn ".env file not found. Creating from template..."
    cp env.example .env
    log_info "Created .env file from env.example"
    echo ""
    log_warn "⚠️  IMPORTANT: Please update .env with your actual credentials before proceeding!"
    echo ""
    read -p "Press Enter to open .env in your default editor, or Ctrl+C to exit..."
    
    if command -v code &> /dev/null; then
        code .env
    elif command -v nano &> /dev/null; then
        nano .env
    elif command -v vim &> /dev/null; then
        vim .env
    else
        log_warn "No suitable editor found. Please manually edit .env file."
    fi
    
    echo ""
    read -p "Have you updated the .env file with your credentials? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "Please update .env file and run this script again."
        exit 1
    fi
else
    log_info ".env file already exists ✓"
fi

echo ""

# Generate JWT secret if not set
log_step "Checking JWT secret key..."
echo ""

if ! grep -q "JWT_SECRET_KEY=your-secret-key" .env; then
    log_info "JWT_SECRET_KEY is already set ✓"
else
    log_warn "Generating new JWT secret key..."
    JWT_SECRET=$(openssl rand -hex 32)
    sed -i.bak "s/JWT_SECRET_KEY=your-secret-key.*/JWT_SECRET_KEY=$JWT_SECRET/" .env
    log_info "Generated and saved new JWT secret key ✓"
fi

echo ""

# Ask about development or production setup
log_step "Choose setup type..."
echo ""

echo "1) Development (with hot reload, debugging tools)"
echo "2) Production (optimized, no dev tools)"
echo ""
read -p "Enter your choice (1 or 2): " -n 1 -r
echo ""

COMPOSE_FILE="docker-compose.yml"
if [[ $REPLY == "2" ]]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    log_info "Using production configuration"
else
    log_info "Using development configuration"
fi

echo ""

# Build Docker images
log_step "Building Docker images..."
echo ""

docker-compose -f $COMPOSE_FILE build

echo ""
log_info "Docker images built successfully ✓"
echo ""

# Start services
log_step "Starting services..."
echo ""

docker-compose -f $COMPOSE_FILE up -d

echo ""
log_info "Services started successfully ✓"
echo ""

# Wait for services to be healthy
log_step "Waiting for services to be healthy..."
echo ""

log_info "Waiting for Redis..."
sleep 5

MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker-compose -f $COMPOSE_FILE exec -T redis redis-cli ping &> /dev/null; then
        log_info "Redis is healthy ✓"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "Redis failed to start"
    exit 1
fi

echo ""

log_info "Waiting for API..."
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        log_info "API is healthy ✓"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "API failed to start"
    log_info "Check logs with: docker-compose -f $COMPOSE_FILE logs api"
    exit 1
fi

echo ""

# Run database migrations
log_step "Running database migrations..."
echo ""

if docker-compose -f $COMPOSE_FILE exec -T api alembic upgrade head; then
    log_info "Database migrations completed successfully ✓"
else
    log_error "Database migrations failed"
    log_info "Check logs with: docker-compose -f $COMPOSE_FILE logs api"
    exit 1
fi

echo ""

# Success message
echo "╔════════════════════════════════════════╗"
echo "║      Setup completed successfully! ✓   ║"
echo "╚════════════════════════════════════════╝"
echo ""

log_info "Services are running:"
echo ""
echo "  📡 API:           http://localhost:8000"
echo "  📚 API Docs:      http://localhost:8000/docs"
echo "  🔍 Health Check:  http://localhost:8000/health"

if [[ $REPLY == "1" ]]; then
    echo "  🔧 Redis UI:      http://localhost:8081"
fi

echo ""
log_info "Useful commands:"
echo ""
echo "  View logs:        docker-compose -f $COMPOSE_FILE logs -f"
echo "  Stop services:    docker-compose -f $COMPOSE_FILE down"
echo "  Restart:          docker-compose -f $COMPOSE_FILE restart"
echo "  Shell access:     docker-compose -f $COMPOSE_FILE exec api sh"
echo ""

if command -v make &> /dev/null; then
    log_info "You can also use Make commands:"
    echo ""
    echo "  make help         Show all available commands"
    echo "  make logs         View logs"
    echo "  make shell        Open shell in API container"
    echo "  make test         Run tests"
    echo ""
fi

log_info "For more information, see README.md"
echo ""

