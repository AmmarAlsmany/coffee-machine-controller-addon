#!/usr/bin/with-contenv bashio

# ==============================================================================
# Home Assistant Community Add-on: Coffee Machine Controller
# Configures and starts the Coffee Machine Controller
# ==============================================================================

# Set default values
declare port
declare baudrate
declare secret_key
declare debug
declare log_level

bashio::log.info "Starting Coffee Machine Controller..."

# Get configuration from Add-on options
port=$(bashio::config 'serial_port')
baudrate=$(bashio::config 'baudrate')
secret_key=$(bashio::config 'django_secret_key')
debug=$(bashio::config 'debug')
log_level=$(bashio::config 'log_level')

bashio::log.info "Configuring Coffee Machine Controller..."
bashio::log.info "Serial Port: ${port}"
bashio::log.info "Baudrate: ${baudrate}"
bashio::log.info "Debug Mode: ${debug}"
bashio::log.info "Log Level: ${log_level}"

# Set environment variables
export DJANGO_SECRET_KEY="${secret_key}"
export DJANGO_DEBUG="${debug}"
export COFFEE_MACHINE_PORT="${port}"
export COFFEE_MACHINE_BAUDRATE="${baudrate}"
export DJANGO_LOG_LEVEL="${log_level}"

# Create database if it doesn't exist
if [ ! -f /data/db.sqlite3 ]; then
    bashio::log.info "Creating initial database..."
    cd /app
    python3 manage.py migrate --noinput

    # Create superuser if credentials are provided
    if bashio::var.has_value "$(bashio::config 'admin_username')"; then
        admin_username=$(bashio::config 'admin_username')
        admin_password=$(bashio::config 'admin_password')
        admin_email=$(bashio::config 'admin_email')

        bashio::log.info "Creating admin user: ${admin_username}"
        echo "from django.contrib.auth.models import User; User.objects.create_superuser('${admin_username}', '${admin_email}', '${admin_password}')" | python3 manage.py shell
    fi
else
    bashio::log.info "Running database migrations..."
    cd /app
    python3 manage.py migrate --noinput
fi

# Set permissions for data directory
chown -R root:root /data
chmod -R 755 /data

# Start the application
bashio::log.info "Starting Coffee Machine Controller web server..."
cd /app

# Use gunicorn for production
exec gunicorn coffee_machine_controller.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --log-level "${log_level,,}" \
    --access-logfile - \
    --error-logfile -