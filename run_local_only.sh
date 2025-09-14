#!/bin/bash

# Coffee Machine Controller - Local Only Mode
# This bypasses ingress and runs only on local network

echo "Starting Coffee Machine Controller (Local Mode)..."

# Navigate to Home Assistant config directory
cd /root/config || cd /config || cd ~/config || {
    echo "Error: Cannot find config directory"
    exit 1
}

# Enter the project directory
cd La-Spaziale-S50-V2 || {
    echo "Error: Cannot find La-Spaziale-S50-V2 directory"
    echo "Run install_and_run.sh first!"
    exit 1
}

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Clear any proxy settings that might interfere
unset FORCE_SCRIPT_NAME
unset SCRIPT_NAME
unset USE_X_FORWARDED_HOST
unset USE_X_FORWARDED_PORT

# Basic Django settings
export DJANGO_SETTINGS_MODULE="coffee_machine_controller.settings"
export PYTHONUNBUFFERED=1
export ALLOWED_HOSTS="*"

# Get the actual IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')

# Run migrations
python manage.py migrate --noinput

echo ""
echo "=========================================="
echo "☕ COFFEE MACHINE CONTROLLER"
echo "=========================================="
echo ""
echo "🏠 LOCAL ACCESS ONLY MODE"
echo ""
echo "Access the controller at:"
echo ""
echo "   http://${IP_ADDRESS}:8000"
echo "   http://homeassistant.local:8000"
echo "   http://localhost:8000"
echo ""
echo "=========================================="
echo "NOTE: This mode bypasses Nabu Casa ingress"
echo "Use this URL from any device on your network"
echo "=========================================="
echo ""

# Run the Django development server
python manage.py runserver 0.0.0.0:8000