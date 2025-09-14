#!/usr/bin/with-contenv bashio

echo "Coffee Machine Controller Add-on is starting..."
echo "This is a test version to verify the add-on appears in Home Assistant"
echo "Port: 8000"

# Simple Python HTTP server for testing
python3 -m http.server 8000