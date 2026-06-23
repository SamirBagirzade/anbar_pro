#!/bin/bash

set -e  # Stop if any command fails
echo "Activating virtual environment..."
source .venv/bin/activate

echo "Pulling latest code..."
git pull

echo "Compiling messages..."
python manage.py compilemessages

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Restarting service..."
sudo systemctl restart anbar

echo "Deployment completed successfully."
