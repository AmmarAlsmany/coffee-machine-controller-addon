#!/usr/bin/with-contenv bashio

# Coffee Machine Controller - Home Assistant Ingress Support
# This script properly configures Django for Home Assistant ingress/Nabu Casa

echo "Starting Coffee Machine Controller with Ingress support..."

# Get the ingress configuration
INGRESS_INTERFACE=$(bashio::addon.ingress_interface)
INGRESS_PORT=$(bashio::addon.ingress_port)
INGRESS_ENTRY=$(bashio::addon.ingress_entry)

# Export environment variables for Django
export DJANGO_SETTINGS_MODULE="coffee_machine_controller.settings"
export PYTHONUNBUFFERED=1

# Configure for ingress
if bashio::addon.ingress; then
    echo "Ingress is enabled"
    export SCRIPT_NAME="${INGRESS_ENTRY}"
    export FORCE_SCRIPT_NAME="${INGRESS_ENTRY}"
    export USE_X_FORWARDED_HOST="True"
    export USE_X_FORWARDED_PORT="True"
    export SECURE_PROXY_SSL_HEADER="HTTP_X_FORWARDED_PROTO,https"

    # Update Django ALLOWED_HOSTS
    export ALLOWED_HOSTS="*"

    # Update CSRF settings for ingress
    export CSRF_TRUSTED_ORIGINS="https://*.ui.nabu.casa,http://homeassistant.local:8123,http://supervisor"

    echo "Ingress URL path: ${INGRESS_ENTRY}"
    echo "Access through Home Assistant sidebar or Nabu Casa"
else
    echo "Ingress is disabled, using direct access"
    echo "Access at: http://homeassistant.local:8000"
fi

# Navigate to project directory
cd /app || cd /root/config/La-Spaziale-S50-V2 || exit 1

# Check for virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install requirements if needed
pip install -r requirements.txt --quiet

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput --clear

# Start the server
echo "Starting server on 0.0.0.0:8000..."
exec python manage.py runserver 0.0.0.0:8000