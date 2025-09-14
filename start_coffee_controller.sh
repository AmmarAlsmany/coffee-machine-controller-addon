#!/bin/bash

# Coffee Machine Controller Startup Script
# For Home Assistant OS/Supervised installations

echo "Starting Coffee Machine Controller..."

# Navigate to Home Assistant config directory
cd /root/config || cd /config || cd ~/config || {
    echo "Error: Cannot find config directory"
    exit 1
}

# Check if repository exists, clone if not
if [ ! -d "La-Spaziale-S50-V2" ]; then
    echo "Cloning repository..."
    git clone https://github.com/AmmarAlsmany/La-Spaziale-S50-V2.git
fi

# Enter the project directory
cd La-Spaziale-S50-V2 || {
    echo "Error: Cannot find La-Spaziale-S50-V2 directory"
    exit 1
}

# Update repository
echo "Updating repository..."
git pull

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv || python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || source venv/Scripts/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Setting up database..."
python manage.py migrate --noinput

# Create static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || echo "Static files collection skipped"

# Set environment variables for ingress support
export FORCE_SCRIPT_NAME="/api/hassio_ingress/$(cat /data/ingress_token 2>/dev/null || echo '')"
export USE_X_FORWARDED_HOST=1
export SECURE_PROXY_SSL_HEADER="('HTTP_X_FORWARDED_PROTO', 'https')"

# Start the Django server
echo "Starting Django server on port 8000..."
echo "=================================="
echo "Access the interface through:"
echo "1. Home Assistant Sidebar (if ingress configured)"
echo "2. Nabu Casa URL (remote access)"
echo "3. Local: http://homeassistant.local:8000"
echo "=================================="
python manage.py runserver 0.0.0.0:8000