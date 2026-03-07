#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Convert static files (CSS, Images) for production
python manage.py collectstatic --no-input

# Apply database migrations to Render's PostgreSQL
python manage.py migrate