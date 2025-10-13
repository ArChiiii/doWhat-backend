#!/bin/bash

# Health check script for monitoring service health
# Exit codes: 0 = healthy, 1 = unhealthy

set -e

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"
MAX_RETRIES=3
RETRY_DELAY=2

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

check_api_health() {
    local retries=0
    log_info "Checking API health at $API_URL/health"
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -sf "$API_URL/health" > /dev/null; then
            log_info "✓ API is healthy"
            return 0
        else
            retries=$((retries + 1))
            log_warn "API health check failed (attempt $retries/$MAX_RETRIES)"
            if [ $retries -lt $MAX_RETRIES ]; then
                sleep $RETRY_DELAY
            fi
        fi
    done
    
    log_error "✗ API is unhealthy after $MAX_RETRIES attempts"
    return 1
}

check_redis_health() {
    log_info "Checking Redis health at $REDIS_HOST:$REDIS_PORT"
    
    if command -v redis-cli &> /dev/null; then
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping | grep -q "PONG"; then
            log_info "✓ Redis is healthy"
            return 0
        else
            log_error "✗ Redis is unhealthy"
            return 1
        fi
    else
        log_warn "redis-cli not found, skipping Redis health check"
        return 0
    fi
}

check_database_health() {
    log_info "Checking database connectivity"
    
    if [ -n "$DATABASE_URL" ]; then
        # Try to connect using psql if available
        if command -v psql &> /dev/null; then
            if psql "$DATABASE_URL" -c "SELECT 1" > /dev/null 2>&1; then
                log_info "✓ Database is healthy"
                return 0
            else
                log_error "✗ Database is unhealthy"
                return 1
            fi
        else
            log_warn "psql not found, skipping database health check"
            return 0
        fi
    else
        log_warn "DATABASE_URL not set, skipping database health check"
        return 0
    fi
}

check_worker_health() {
    log_info "Checking RQ worker status"
    
    if command -v rq &> /dev/null; then
        if rq info --url "redis://$REDIS_HOST:$REDIS_PORT" > /dev/null 2>&1; then
            log_info "✓ RQ worker is healthy"
            return 0
        else
            log_error "✗ RQ worker is unhealthy"
            return 1
        fi
    else
        log_warn "rq not found, skipping worker health check"
        return 0
    fi
}

# Main execution
main() {
    log_info "Starting health checks..."
    echo ""
    
    local exit_code=0
    
    # API health check
    if ! check_api_health; then
        exit_code=1
    fi
    echo ""
    
    # Redis health check
    if ! check_redis_health; then
        exit_code=1
    fi
    echo ""
    
    # Database health check
    if ! check_database_health; then
        exit_code=1
    fi
    echo ""
    
    # Worker health check
    if ! check_worker_health; then
        exit_code=1
    fi
    echo ""
    
    if [ $exit_code -eq 0 ]; then
        log_info "All health checks passed ✓"
    else
        log_error "Some health checks failed ✗"
    fi
    
    exit $exit_code
}

# Run main function
main

