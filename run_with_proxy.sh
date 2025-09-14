#!/bin/bash

# Coffee Machine Controller - Proxy-aware startup
# This script configures Django to work behind Home Assistant's ingress proxy

echo "Starting Coffee Machine Controller with proxy support..."

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

# Install gunicorn if not installed (better proxy support than runserver)
pip install gunicorn whitenoise django-cors-headers --quiet

# Export environment variables for proxy
export DJANGO_SETTINGS_MODULE="coffee_machine_controller.settings"
export PYTHONUNBUFFERED=1

# Set proxy-aware environment variables
export USE_X_FORWARDED_HOST=True
export USE_X_FORWARDED_PORT=True
export USE_X_FORWARDED_PROTO=True
export SECURE_PROXY_SSL_HEADER="HTTP_X_FORWARDED_PROTO,https"

# IMPORTANT: Set the script name to handle ingress paths
export SCRIPT_NAME="/api/hassio_ingress/a7kTy9yWuGIYa4LYXaRi1yBUJVht8erRXTMTCUZ_cHY"
export FORCE_SCRIPT_NAME="/api/hassio_ingress/a7kTy9yWuGIYa4LYXaRi1yBUJVht8erRXTMTCUZ_cHY"

# Update ALLOWED_HOSTS and CSRF settings
export ALLOWED_HOSTS="*"
export CSRF_TRUSTED_ORIGINS="https://xrqlxhrnom02wtf3cfz3odga9u80vpyc.ui.nabu.casa"

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput --clear

echo ""
echo "=========================================="
echo "🌐 COFFEE MACHINE CONTROLLER READY"
echo "=========================================="
echo ""
echo "📱 Access through Nabu Casa:"
echo "   https://xrqlxhrnom02wtf3cfz3odga9u80vpyc.ui.nabu.casa"
echo "   Then navigate to Coffee Machine in sidebar"
echo ""
echo "🏠 Direct Local Access (if not using ingress):"
echo "   http://homeassistant.local:8000"
echo ""
echo "=========================================="
echo "Using Gunicorn for better proxy support..."
echo "=========================================="
echo ""

# Use gunicorn instead of runserver for better proxy support
gunicorn coffee_machine_controller.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --timeout 120

# Fallback to runserver if gunicorn fails
if [ $? -ne 0 ]; then
    echo "Gunicorn failed, falling back to Django runserver..."
    python manage.py runserver 0.0.0.0:8000
fi