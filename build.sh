#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files for WhiteNoise
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Create superuser automatically if DJANGO_SUPERUSER_PASSWORD is set
python manage.py create_superuser_if_none
