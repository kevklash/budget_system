# Budget Management System Startup Script
Write-Host "🚀 Starting Budget Management System..." -ForegroundColor Green

# Stop any existing containers
Write-Host "📦 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Build and start all services
Write-Host "🏗️  Building and starting services..." -ForegroundColor Yellow
docker-compose up --build -d

Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "✅ Budget Management System is running!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Access points:" -ForegroundColor Cyan
Write-Host "   - Django Admin: http://localhost:8000/admin/" -ForegroundColor White
Write-Host "   - Celery Monitor: http://localhost:5555/" -ForegroundColor White
Write-Host ""
Write-Host "🔍 To view logs:" -ForegroundColor Cyan
Write-Host "   - All services: docker-compose logs -f" -ForegroundColor White
Write-Host "   - Django only: docker-compose logs -f web" -ForegroundColor White
Write-Host "   - Celery worker: docker-compose logs -f celery-worker" -ForegroundColor White
Write-Host "   - Celery beat: docker-compose logs -f celery-beat" -ForegroundColor White
Write-Host ""
Write-Host "🛑 To stop all services:" -ForegroundColor Cyan
Write-Host "   docker-compose down" -ForegroundColor White
