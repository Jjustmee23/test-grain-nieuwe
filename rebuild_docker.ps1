Write-Host "========================================" -ForegroundColor Green
Write-Host "Rebuilding Docker Containers" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host ""
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

Write-Host ""
Write-Host "Removing old images..." -ForegroundColor Yellow
docker-compose down --rmi all

Write-Host ""
Write-Host "Building new images..." -ForegroundColor Yellow
docker-compose build --no-cache

Write-Host ""
Write-Host "Starting containers..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "Waiting for containers to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "Checking container status..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Docker rebuild complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "You can now access the application at:" -ForegroundColor Cyan
Write-Host "http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "To view logs, run: docker-compose logs -f" -ForegroundColor Gray
Write-Host "To stop containers, run: docker-compose down" -ForegroundColor Gray
Write-Host ""
Read-Host "Press Enter to continue" 