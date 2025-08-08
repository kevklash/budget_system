# Django + Celery Budget Management System

A comprehensive backend system for managing advertising budgets and campaigns at an ad agency. The system automatically tracks spending, enforces budget limits, handles dayparting schedules, and manages campaign activation based on multiple constraints.

## Features

- **Budget Tracking**: Real-time daily and monthly spend tracking per brand
- **Automatic Campaign Control**: Campaigns are automatically paused when budgets are exceeded
- **Dayparting Support**: Campaign scheduling based on time windows
- **Daily/Monthly Resets**: Automatic budget resets and campaign reactivation
- **Static Typing**: Full type annotations with MyPy support
- **Admin Interface**: Django admin for easy management
- **Celery Integration**: Background tasks for real-time monitoring
- **Docker Support**: Complete containerized deployment

## Quick Start with Docker (Recommended)

### Prerequisites
- Docker Desktop installed and running
- Git (to clone the repository)

### One-Command Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/budget-system.git
cd budget-system

# Windows PowerShell
.\start.ps1

# Or Linux/macOS
./start.sh

# Or manual Docker Compose
docker-compose up --build
```

That's it! Your entire system will be running with:
- **Django Admin**: http://localhost:8000/admin/
- **Celery Monitor**: http://localhost:5555/
- **Redis**: localhost:6379
- **Auto-scheduled tasks**: Budget enforcement, dayparting, daily resets
- **Database migrations**: Automatically applied on startup

### Create Superuser (Docker)
```bash
docker-compose exec web python manage.py createsuperuser
```

## Manual Setup (Alternative)

### Prerequisites
- Python 3.9+
- Redis (for Celery broker)

### Installation Steps

```bash
# Clone the repository
git clone https://github.com/yourusername/budget-system.git
cd budget-system

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser

# Run the Django development server
python manage.py runserver
```

### Running Celery Worker and Beat (Manual Setup)

In separate terminal windows:

```bash
# Terminal 1: Start Celery worker
celery -A budget_system worker --loglevel=info

# Terminal 2: Start Celery beat scheduler
celery -A budget_system beat --loglevel=info
```

## Docker Architecture

The Docker setup includes these services:

### Core Services
- **web**: Django application server (port 8000) - Automatically runs migrations on startup
- **redis**: Redis database for Celery (port 6379)
- **celery-worker**: Background task processor
- **celery-beat**: Scheduled task executor
- **celery-flower**: Celery monitoring UI (port 5555)

### Service Dependencies
```
redis (base service)
  ↓
web (depends on redis)
  ↓
celery-worker (depends on redis, web)
celery-beat (depends on redis, web)
celery-flower (depends on redis, celery-worker)
```

## Docker Management Commands

### Basic Operations
```bash
# Start all services
docker-compose up --build

# Start in background
docker-compose up --build -d

# Stop all services
docker-compose down

# View all logs
docker-compose logs -f

# Restart specific service
docker-compose restart web
```

### Service-Specific Logs
```bash
# Django application logs
docker-compose logs -f web

# Celery worker logs
docker-compose logs -f celery-worker

# Celery beat scheduler logs
docker-compose logs -f celery-beat

# Redis logs
docker-compose logs -f redis

# Flower monitoring logs
docker-compose logs -f celery-flower
```

### Django Management Commands (Docker)
```bash
# Access Django shell
docker-compose exec web python manage.py shell

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic

# Reset budgets manually
docker-compose exec web python manage.py reset_budgets
```

### Development Commands
```bash
# Rebuild specific service
docker-compose build web

# View running containers
docker-compose ps

# Access container shell
docker-compose exec web bash

# View container resource usage
docker stats
```

## Data Models and Relationships

### Brand
- Represents an advertising brand/client
- Contains daily and monthly budget limits
- Tracks current spend totals
- **Relationships**: One-to-many with Campaigns

### Campaign
- Individual advertising campaigns belonging to a brand
- Has active/inactive status
- **Relationships**: Belongs to Brand, has many SpendLogs, optionally has DaypartingSchedule

### SpendLog
- Records individual spending transactions
- Automatically updates brand totals via database signals
- **Relationships**: Belongs to Campaign

### DaypartingSchedule
- Defines time windows when campaigns should be active
- Supports overnight schedules (e.g., 22:00 - 06:00)
- **Relationships**: One-to-one with Campaign

## System Workflow

### Daily Operations
1. **00:00 (Midnight)**: 
   - Reset daily spends for all brands
   - Reset monthly spends (1st of month only)
   - Reactivate eligible campaigns

2. **Continuous Operations**:
   - Record spend logs as transactions occur
   - Auto-update brand totals via database signals

3. **Every Minute**: 
   - Check dayparting windows
   - Activate/deactivate campaigns based on time constraints

4. **Every 5 Minutes**:
   - Enforce budget limits
   - Pause campaigns exceeding budgets

### Campaign Status Logic
A campaign is **active** only when ALL conditions are met:
- Brand's daily budget not exceeded
- Brand's monthly budget not exceeded  
- Current time within dayparting window (if schedule exists)

## Management Commands

```bash
# Docker environment
docker-compose exec web python manage.py reset_budgets

# Local environment
python manage.py reset_budgets

# Check system status with Django shell
python manage.py shell
>>> from ads.services import BudgetService, CampaignService
>>> # Use service methods for analysis
```

## Configuration

### Docker Environment Variables
The Docker setup automatically configures:
- `CELERY_BROKER_URL=redis://redis:6379/0`
- `CELERY_RESULT_BACKEND=redis://redis:6379/0`
- `DEBUG=1` (development mode)

### Celery Task Schedules
Defined in `settings.py`:
- `enforce_budgets`: Every 5 minutes
- `enforce_dayparting`: Every minute  
- `reset_daily_monthly_spends`: Daily at midnight

### Custom Configuration
To modify settings, update `budget_system/settings.py` or use environment variables in `docker-compose.yml`.

## API Usage Examples

### Recording Spend
```python
from ads.models import Campaign
from ads.services import BudgetService
from decimal import Decimal

campaign = Campaign.objects.get(name="Summer Sale")
BudgetService.record_spend(campaign, Decimal("100.50"), "Google Ads click")
```

### Checking Campaign Status
```python
from ads.services import CampaignService

should_be_active, reasons = CampaignService.should_campaign_be_active(campaign)
if not should_be_active:
    print(f"Campaign blocked: {', '.join(reasons)}")
```

### Getting Brand Summary
```python
from ads.models import Brand
from ads.services import BudgetService

brand = Brand.objects.get(name="Acme Corp")
summary = BudgetService.get_brand_summary(brand)
print(f"Daily remaining: ${summary['daily_remaining']}")
```

## Monitoring and Debugging

### Flower Monitoring Dashboard
Access http://localhost:5555/ to view:
- Active/completed tasks
- Task execution times
- Worker status
- Task failure details
- Broker statistics

### System Health Checks
```bash
# Check if all containers are running
docker-compose ps

# Check Redis connection
docker-compose exec redis redis-cli ping

# Check Django health
curl http://localhost:8000/admin/

# Check Celery worker status
docker-compose exec web celery -A budget_system inspect active
```

### Troubleshooting
```bash
# View container resource usage
docker stats

# Check container disk space
docker system df

# Clean up unused Docker resources
docker system prune

# Rebuild everything from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

## Static Type Checking

The project uses MyPy for static type checking:

```bash
# Docker environment
docker-compose exec web mypy .

# Local environment
mypy .

# Should show: Success: no issues found
```

Configuration is in `mypy.ini` with strict mode enabled.

## Testing

```bash
# Docker environment
docker-compose exec web python manage.py test

# Local environment
python manage.py test

# Run with coverage
pip install coverage
coverage run manage.py test
coverage report
```

## Assumptions and Design Decisions

1. **Decimal Precision**: Using `DecimalField` for financial calculations to avoid floating-point errors
2. **UTC Timezone**: All times stored in UTC; dayparting uses server timezone
3. **Signal-Based Updates**: Brand totals updated automatically via Django signals
4. **Budget Priority**: Budget constraints take priority over dayparting
5. **Automatic Reactivation**: Campaigns auto-reactivate when constraints clear
6. **One Schedule Per Campaign**: Each campaign can have at most one dayparting schedule
7. **Real-time Monitoring**: Celery tasks provide near real-time budget enforcement
8. **Admin Interface**: Full Django admin integration for manual management
9. **Containerization**: Docker ensures consistent environment across development/production

## Security Considerations

- Django secret key should be changed for production
- Database credentials should be environment variables
- Redis should be secured in production
- Admin interface should be properly secured
- Docker containers should run with non-root users in production

## Production Deployment

### Docker Production Setup
1. Update `docker-compose.prod.yml` with production settings
2. Use environment variables for secrets
3. Configure proper logging and monitoring
4. Set up SSL/TLS termination
5. Use production-grade database (PostgreSQL)
6. Configure Redis persistence and clustering

### Scaling Considerations
- Multiple Celery workers can be added
- Redis can be clustered for high availability
- Django can run multiple instances behind a load balancer
- Database can be separated into its own service

## File Structure

```
budget_system/
├── ads/                          # Django app
│   ├── models.py                 # Data models
│   ├── tasks.py                  # Celery tasks
│   ├── services.py               # Business logic
│   ├── admin.py                  # Admin interface
│   └── management/commands/      # Management commands
├── budget_system/                # Django project
│   ├── settings.py               # Configuration
│   ├── celery.py                 # Celery setup
│   └── urls.py                   # URL routing
├── docker-compose.yml            # Docker services
├── Dockerfile                    # Docker image definition
├── start.ps1                     # Windows startup script
├── start.sh                      # Linux/macOS startup script
├── requirements.txt              # Python dependencies
├── mypy.ini                      # Type checking config
├── PSEUDOCODE.md                 # System documentation
└── README.md                     # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure MyPy passes with no errors
5. Test with Docker: `docker-compose up --build`
6. Submit a pull request

## License

This project is licensed under the MIT License.
