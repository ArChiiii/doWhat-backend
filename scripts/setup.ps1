# doWhat Backend Setup Script for Windows (PowerShell)
# Run this script to set up the backend quickly

Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   doWhat Backend Setup Script          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "[STEP] Checking Docker..." -ForegroundColor Blue
try {
    docker --version | Out-Null
    Write-Host "[INFO] Docker is installed ✓" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not installed or not running" -ForegroundColor Red
    Write-Host "Please install Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check if .env exists
Write-Host ""
Write-Host "[STEP] Checking environment configuration..." -ForegroundColor Blue

if (-not (Test-Path ".env")) {
    Write-Host "[WARN] .env file not found. Creating from template..." -ForegroundColor Yellow
    Copy-Item "env.example" ".env"
    Write-Host "[INFO] Created .env file from env.example" -ForegroundColor Green
    Write-Host ""
    Write-Host "[WARN] ⚠️  IMPORTANT: Please update .env with your actual credentials!" -ForegroundColor Yellow
    Write-Host ""
    
    $response = Read-Host "Open .env file in notepad? (Y/N)"
    if ($response -eq 'Y' -or $response -eq 'y') {
        notepad .env
    }
    
    Write-Host ""
    $response = Read-Host "Have you updated the .env file with your credentials? (Y/N)"
    if ($response -ne 'Y' -and $response -ne 'y') {
        Write-Host "[ERROR] Please update .env file and run this script again." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[INFO] .env file already exists ✓" -ForegroundColor Green
}

# Generate JWT secret if needed
Write-Host ""
Write-Host "[STEP] Checking JWT secret key..." -ForegroundColor Blue

$envContent = Get-Content ".env" -Raw
if ($envContent -match "JWT_SECRET_KEY=your-secret-key") {
    Write-Host "[WARN] Generating new JWT secret key..." -ForegroundColor Yellow
    
    # Generate random hex string (32 bytes = 64 hex chars)
    $bytes = New-Object byte[] 32
    (New-Object System.Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes)
    $jwtSecret = [System.BitConverter]::ToString($bytes) -replace '-',''
    
    $envContent = $envContent -replace "JWT_SECRET_KEY=your-secret-key.*", "JWT_SECRET_KEY=$jwtSecret"
    $envContent | Set-Content ".env"
    
    Write-Host "[INFO] Generated and saved new JWT secret key ✓" -ForegroundColor Green
} else {
    Write-Host "[INFO] JWT_SECRET_KEY is already set ✓" -ForegroundColor Green
}

# Build Docker images
Write-Host ""
Write-Host "[STEP] Building Docker images..." -ForegroundColor Blue
docker-compose build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[INFO] Docker images built successfully ✓" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[ERROR] Docker build failed" -ForegroundColor Red
    exit 1
}

# Start services
Write-Host ""
Write-Host "[STEP] Starting services..." -ForegroundColor Blue
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[INFO] Services started successfully ✓" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[ERROR] Failed to start services" -ForegroundColor Red
    exit 1
}

# Wait for services to be ready
Write-Host ""
Write-Host "[STEP] Waiting for services to be healthy..." -ForegroundColor Blue
Write-Host "[INFO] Waiting for API to be ready..." -ForegroundColor Green

Start-Sleep -Seconds 10

$maxRetries = 30
$retryCount = 0

while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host ""
            Write-Host "[INFO] API is healthy ✓" -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "." -NoNewline
        $retryCount++
        Start-Sleep -Seconds 2
    }
}

if ($retryCount -eq $maxRetries) {
    Write-Host ""
    Write-Host "[ERROR] API failed to start" -ForegroundColor Red
    Write-Host "Check logs with: docker-compose logs api" -ForegroundColor Yellow
    exit 1
}

# Run database migrations
Write-Host ""
Write-Host "[STEP] Running database migrations..." -ForegroundColor Blue

docker-compose exec -T api alembic upgrade head

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[INFO] Database migrations completed successfully ✓" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[ERROR] Database migrations failed" -ForegroundColor Red
    Write-Host "Check logs with: docker-compose logs api" -ForegroundColor Yellow
    exit 1
}

# Success message
Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║      Setup completed successfully! ✓   ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "[INFO] Services are running:" -ForegroundColor Green
Write-Host ""
Write-Host "  📡 API:           http://localhost:8000" -ForegroundColor Cyan
Write-Host "  📚 API Docs:      http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  🔍 Health Check:  http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""

Write-Host "[INFO] Useful commands:" -ForegroundColor Green
Write-Host ""
Write-Host "  View logs:        docker-compose logs -f" -ForegroundColor Cyan
Write-Host "  Stop services:    docker-compose down" -ForegroundColor Cyan
Write-Host "  Restart:          docker-compose restart" -ForegroundColor Cyan
Write-Host "  Shell access:     docker-compose exec api sh" -ForegroundColor Cyan
Write-Host ""

Write-Host "[INFO] For more information, see README.md" -ForegroundColor Green
Write-Host ""

