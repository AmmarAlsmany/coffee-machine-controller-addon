#!/bin/bash

# Quick run script for Coffee Machine Controller
# For use in Home Assistant Terminal add-on

# Navigate to config folder and project
cd /root/config/La-Spaziale-S50-V2 || \
cd /config/La-Spaziale-S50-V2 || \
cd ~/config/La-Spaziale-S50-V2 || \
cd /homeassistant/La-Spaziale-S50-V2 || {
    echo "Project not found! Run install_and_run.sh first"
    exit 1
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv || python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate || source venv/Scripts/activate

# Quick install requirements (in case of updates)
pip install -r requirements.txt --quiet

# Run the server
echo ""
echo "=========================================="
echo "☕ COFFEE MACHINE CONTROLLER"
echo "=========================================="
echo ""
echo "📱 Nabu Casa Remote URL (Click below):"
echo "   https://xrqlxhrnom02wtf3cfz3odga9u80vpyc.ui.nabu.casa/api/hassio_ingress/YOUR_INGRESS_TOKEN/proxy/8000/"
echo ""
echo "🏠 Local Access:"
echo "   http://homeassistant.local:8000"
echo "   http://$(hostname -I | awk '{print $1}' 2>/dev/null || echo 'YOUR-IP'):8000"
echo ""
echo "=========================================="
echo ""
python manage.py runserver 0.0.0.0:8000