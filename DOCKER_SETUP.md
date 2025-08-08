# Quick Docker Setup Guide

## Prerequisites
1. **Docker Desktop**: Download and install from https://www.docker.com/products/docker-desktop/
2. **Git**: For cloning the repository

## Setup Steps

### 1. Clone and Navigate
```bash
git clone https://github.com/yourusername/budget-system.git
cd budget-system
```

### 2. Start Everything (Choose one method)

#### Option A: PowerShell Script (Windows)
```powershell
.\start.ps1
```

#### Option B: Bash Script (Linux/macOS)
```bash
./start.sh
```

#### Option C: Direct Docker Compose
```bash
docker-compose up --build
```

### 3. Create Admin User
```bash
docker-compose exec web python manage.py createsuperuser
```

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Django Admin | http://localhost:8000/admin/ | Web interface for managing data |
| Celery Monitor | http://localhost:5555/ | Real-time task monitoring |
| Redis | localhost:6379 | Database (internal) |

## Quick Commands

```bash
# Stop everything
docker-compose down

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart web

# Access Django shell
docker-compose exec web python manage.py shell
```

## Test the System

1. Go to http://localhost:8000/admin/
2. Log in with your superuser account
3. Create a Brand with daily/monthly budgets
4. Create a Campaign for that brand
5. Watch Celery Monitor at http://localhost:5555/ for background tasks

That's it! Your complete budget management system is running with automatic:
- Budget enforcement (every 5 minutes)
- Dayparting checks (every minute)  
- Daily resets (midnight)
- Real-time spend tracking
