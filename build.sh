#!/usr/bin/env bash

# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt
pip install --upgrade pip

# Convert static asset files
python manage.py collectstatic --no-input

# Create an admin user
# python manage.py initadmin

python manage.py collectstatic --noinput

# Apply any outstanding database migrations
python manage.py migrate