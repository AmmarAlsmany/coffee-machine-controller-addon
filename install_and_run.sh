#!/bin/bash

# One-line installer and runner for Coffee Machine Controller
# Works in Home Assistant Terminal/SSH add-on

echo "==================================="
echo "Coffee Machine Controller Installer"
echo "==================================="

# Function to find the correct config directory
find_config_dir() {
    if [ -d "/root/config" ]; then
        echo "/root/config"
    elif [ -d "/config" ]; then
        echo "/config"
    elif [ -d "$HOME/config" ]; then
        echo "$HOME/config"
    elif [ -d "/homeassistant" ]; then
        echo "/homeassistant"
    else
        echo ""
    fi
}

# Find config directory
CONFIG_DIR=$(find_config_dir)

if [ -z "$CONFIG_DIR" ]; then
    echo "Error: Cannot find Home Assistant config directory"
    echo "Trying to create in current directory..."
    CONFIG_DIR="."
fi

echo "Using config directory: $CONFIG_DIR"
cd "$CONFIG_DIR"

# Clone or update repository
if [ -d "La-Spaziale-S50-V2" ]; then
    echo "Repository exists, updating..."
    cd La-Spaziale-S50-V2
    git pull
else
    echo "Cloning repository..."
    git clone https://github.com/AmmarAlsmany/La-Spaziale-S50-V2.git
    cd La-Spaziale-S50-V2
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv || python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || source venv/Scripts/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Setup database
echo "Setting up database..."
python3 manage.py migrate --noinput || python manage.py migrate --noinput

# Start server
echo "==================================="
echo "Starting Coffee Machine Controller"
echo "Access at: http://homeassistant.local:8000"
echo "Or: http://YOUR-HA-IP:8000"
echo "Press Ctrl+C to stop"
echo "==================================="

python3 manage.py runserver 0.0.0.0:8000 || python manage.py runserver 0.0.0.0:8000