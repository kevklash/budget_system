#!/bin/bash

echo "🚀 Starting Budget Management System..."

# Stop any existing containers
echo "📦 Stopping existing containers..."
docker-compose down

# Build and start all services
echo "🏗️  Building and starting services..."
docker-compose up --build -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "✅ Budget Management System is running!"
echo ""
echo "📊 Access points:"
echo "   - Django Admin: http://localhost:8000/admin/"
echo "   - Celery Monitor: http://localhost:5555/"
echo ""
echo "🔍 To view logs:"
echo "   - All services: docker-compose logs -f"
echo "   - Django only: docker-compose logs -f web"
echo "   - Celery worker: docker-compose logs -f celery-worker"
echo "   - Celery beat: docker-compose logs -f celery-beat"
echo ""
echo "🛑 To stop all services:"
echo "   docker-compose down"
