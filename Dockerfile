ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.19
FROM ${BUILD_FROM}

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install system dependencies
RUN apk update && apk add --no-cache \
    python3 \
    python3-dev \
    py3-pip \
    py3-setuptools \
    py3-wheel \
    gcc \
    musl-dev \
    linux-headers \
    libffi-dev \
    openssl-dev \
    curl \
    bash \
    git \
    && rm -rf /var/cache/apk/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt ./

# Upgrade pip and install Python dependencies
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir -r requirements.txt && \
    python3 -m pip install --no-cache-dir gunicorn

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /data && \
    mkdir -p /app/static && \
    mkdir -p /app/staticfiles && \
    mkdir -p /var/log

# Set permissions
RUN chmod +x /app/run.sh

# Set Django settings for build
ENV DJANGO_SETTINGS_MODULE=coffee_machine_controller.settings
ENV DJANGO_SECRET_KEY=build-time-secret-key-only

# Collect static files (ignore database requirement during build)
RUN python3 manage.py collectstatic --noinput --clear || echo "Static files collection skipped"

# Copy rootfs
COPY rootfs /

# Expose port
EXPOSE 8000

# Labels
LABEL \
    io.hass.name="Coffee Machine Controller" \
    io.hass.description="Control LaSpaziale coffee machines via Modbus RTU" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version="${BUILD_VERSION}" \
    maintainer="AmmarAlsmany <ammar@example.com>" \
    org.opencontainers.image.title="Coffee Machine Controller" \
    org.opencontainers.image.description="Home Assistant Add-on for coffee machine control" \
    org.opencontainers.image.vendor="AmmarAlsmany" \
    org.opencontainers.image.authors="AmmarAlsmany <ammar@example.com>" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://github.com/AmmarAlsmany/coffee-machine-controller-addon" \
    org.opencontainers.image.source="https://github.com/AmmarAlsmany/coffee-machine-controller-addon"

# Run
CMD [ "/app/run.sh" ]