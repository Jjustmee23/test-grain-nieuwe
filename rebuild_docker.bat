@echo off
echo ========================================
echo Rebuilding Docker Containers
echo ========================================

echo.
echo Stopping existing containers...
docker-compose down

echo.
echo Removing old images...
docker-compose down --rmi all

echo.
echo Building new images...
docker-compose build --no-cache

echo.
echo Starting containers...
docker-compose up -d

echo.
echo Waiting for containers to be ready...
timeout /t 10 /nobreak > nul

echo.
echo Checking container status...
docker-compose ps

echo.
echo ========================================
echo Docker rebuild complete!
echo ========================================
echo.
echo You can now access the application at:
echo http://localhost:8000
echo.
echo To view logs, run: docker-compose logs -f
echo To stop containers, run: docker-compose down
echo.
pause 