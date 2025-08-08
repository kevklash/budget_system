#!/bin/bash

# Budget System Entrypoint Script
# This script runs before starting the Django application

set -e

echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Setup complete! Starting Django server..."
exec "$@"
