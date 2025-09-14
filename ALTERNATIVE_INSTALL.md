# Alternative Installation Methods

## Method 1: Direct Local Installation

If the add-on doesn't appear in the store, you can install it locally:

1. **SSH into Home Assistant**:
```bash
ssh root@homeassistant.local
# or use the Terminal add-on
```

2. **Navigate to addons folder**:
```bash
cd /addons
```

3. **Clone the repository**:
```bash
git clone https://github.com/AmmarAlsmany/coffee-machine-controller-addon coffee_machine
cd coffee_machine
```

4. **Restart Home Assistant**:
```bash
ha supervisor restart
```

5. **Check logs**:
```bash
ha supervisor logs
```

6. **The add-on should now appear in the "Local add-ons" section**

## Method 2: Manual Docker Run (For Testing)

Run the coffee machine controller directly on your Home Assistant host:

```bash
docker run -d \
  --name coffee-controller \
  -p 8000:8000 \
  --device=/dev/ttyUSB0 \
  -e DJANGO_SECRET_KEY="your-secret-key" \
  -e COFFEE_MACHINE_PORT="/dev/ttyUSB0" \
  -e COFFEE_MACHINE_BAUDRATE="9600" \
  --restart unless-stopped \
  python:3.9-alpine \
  sh -c "apk add --no-cache git && \
         git clone https://github.com/AmmarAlsmany/coffee-machine-controller-addon /app && \
         cd /app && \
         pip install -r requirements.txt && \
         python manage.py runserver 0.0.0.0:8000"
```

## Method 3: Using Portainer

If you have Portainer installed:

1. Open Portainer
2. Go to "Stacks"
3. Create new stack with this docker-compose:

```yaml
version: '3'
services:
  coffee-controller:
    build:
      context: https://github.com/AmmarAlsmany/coffee-machine-controller-addon.git
    ports:
      - "8000:8000"
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0
    environment:
      - DJANGO_SECRET_KEY=your-secret-key
      - COFFEE_MACHINE_PORT=/dev/ttyUSB0
      - COFFEE_MACHINE_BAUDRATE=9600
    restart: unless-stopped
```

## Method 4: Debug Why Add-on Isn't Showing

1. **Check Supervisor logs**:
```bash
ha supervisor logs | grep -i coffee
```

2. **Check if repository was loaded**:
```bash
ha addons
```

3. **Force reload**:
```bash
ha supervisor reload
ha addons reload
```

4. **Check for errors**:
```bash
ha supervisor info
```

## Common Issues & Solutions

### Issue: "Can't find add-on"
**Solution**: The repository structure might be wrong. Check that config.yaml is in the root.

### Issue: "Invalid config"
**Solution**: Validate YAML/JSON syntax at https://jsonlint.com

### Issue: "No image found"
**Solution**: Remove the `image` line from config.yaml to build locally

### Issue: "Permission denied"
**Solution**: Add proper device permissions in config.yaml

## Direct Access Without Add-on

If you just want to use the controller now:

1. **On any machine with Python**:
```bash
git clone https://github.com/AmmarAlsmany/coffee-machine-controller-addon
cd coffee-machine-controller-addon
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

2. **Access at**: `http://your-machine-ip:8000`

This bypasses Home Assistant completely and runs the coffee controller directly.