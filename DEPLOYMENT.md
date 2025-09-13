# Deployment Guide - Coffee Machine Controller Add-on

This guide will walk you through deploying your Coffee Machine Controller as a Home Assistant Add-on.

## Prerequisites

- GitHub account
- Home Assistant installation (Supervised/OS/Container)
- Coffee machine with Modbus RTU support
- USB-to-Serial adapter

## Step 1: Create GitHub Repository

1. **Create a new repository on GitHub**:
   ```
   Repository name: coffee-machine-controller-addon
   Description: Home Assistant Add-on for LaSpaziale coffee machine control
   Public/Private: Your choice (Public recommended for community sharing)
   ```

2. **Push your code to the repository**:
   ```bash
   git remote add origin https://github.com/YOUR-USERNAME/coffee-machine-controller-addon.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Configure GitHub Container Registry

1. **Enable GitHub Container Registry**:
   - Go to your repository → Settings → Actions → General
   - Under "Workflow permissions", select "Read and write permissions"
   - Check "Allow GitHub Actions to create and approve pull requests"

2. **Update repository URLs** in these files:
   - `config.yaml`: Replace `your-username` with your GitHub username
   - `README_ADDON.md`: Replace all `your-username` references
   - `repository.yaml`: Update maintainer information

## Step 3: Create Add-on Repository Structure

Your repository should have this structure:
```
coffee-machine-controller-addon/
├── .github/
│   └── workflows/
│       └── build.yml
├── rootfs/
│   └── etc/
│       └── services.d/
│           └── coffee-controller/
│               ├── run
│               └── finish
├── api/
├── coffee_machine_controller/
├── machine/
├── templates/
├── static/
├── build.yaml
├── config.yaml
├── Dockerfile
├── run.sh
├── requirements.txt
├── manage.py
├── README_ADDON.md
├── repository.yaml
└── icon.png (you need to add this)
```

## Step 4: Add Icon (Required)

1. **Create or find a coffee-themed icon**:
   - Size: 512x512 pixels
   - Format: PNG
   - Name: `icon.png`

2. **Replace the placeholder**:
   ```bash
   # Remove the text placeholder
   rm icon.png
   # Add your actual PNG icon
   cp /path/to/your/coffee-icon.png icon.png
   ```

## Step 5: Test Local Build (Optional)

Test your Add-on locally before deploying:

```bash
# Install Home Assistant CLI
pip3 install homeassistant-cli

# Build the Add-on
docker run --rm --privileged \
  -v ~/.docker:/root/.docker \
  -v $(pwd):/data \
  homeassistant/amd64-builder:latest \
  --target /data --amd64
```

## Step 6: Deploy to GitHub

1. **Commit and push all changes**:
   ```bash
   git add .
   git commit -m "Initial Add-on release"
   git push origin main
   ```

2. **Create a release**:
   - Go to your repository on GitHub
   - Click "Releases" → "Create a new release"
   - Tag version: `v1.0.0`
   - Release title: `Coffee Machine Controller v1.0.0`
   - Description: Brief description of features
   - Click "Publish release"

3. **GitHub Actions will automatically**:
   - Build Docker images for all architectures
   - Push images to GitHub Container Registry
   - Make the Add-on available for installation

## Step 7: Install in Home Assistant

### Method 1: Direct Repository Installation

1. **In Home Assistant**:
   - Navigate to **Supervisor** → **Add-on Store**
   - Click **⋮** (three dots) → **Repositories**
   - Add: `https://github.com/YOUR-USERNAME/coffee-machine-controller-addon`
   - Wait for it to load

2. **Install the Add-on**:
   - Find "Coffee Machine Controller" in the store
   - Click **Install**
   - Wait for installation to complete

### Method 2: Community Add-on Repository (Future)

Once tested, you can submit to community repositories:
- [Home Assistant Community Add-ons](https://github.com/hassio-addons/repository)
- [Home Assistant Official Add-ons](https://github.com/home-assistant/addons)

## Step 8: Configure the Add-on

1. **Go to Add-on Configuration**:
   ```yaml
   serial_port: "/dev/ttyUSB0"  # Your coffee machine port
   baudrate: 9600
   django_secret_key: "generate-a-secure-random-key-here"
   debug: false
   log_level: "INFO"
   admin_username: "admin"
   admin_password: "secure-password"
   admin_email: "admin@yourdomain.com"
   ```

2. **Find your serial port**:
   ```bash
   # In Home Assistant SSH Add-on:
   ls /dev/tty*
   # Look for /dev/ttyUSB0, /dev/ttyACM0, etc.
   ```

3. **Generate a secure secret key**:
   ```python
   # In Python:
   import secrets
   print(secrets.token_urlsafe(50))
   ```

## Step 9: Start and Test

1. **Start the Add-on**:
   - Click **Start**
   - Check logs for any errors

2. **Access the Web Interface**:
   - Click **Open Web UI** or go to `http://your-ha-ip:8000`
   - Test coffee machine connection

3. **Verify API Endpoints**:
   ```bash
   # Test API
   curl http://your-ha-ip:8000/api/status/
   curl -X POST http://your-ha-ip:8000/api/connect/
   ```

## Step 10: Integration with Home Assistant

### Create REST Commands
```yaml
# configuration.yaml
rest_command:
  coffee_connect:
    url: "http://localhost:8000/api/connect/"
    method: POST

  coffee_deliver:
    url: "http://localhost:8000/api/deliver/"
    method: POST
    headers:
      Content-Type: "application/json"
    payload: '{"group_number": {{ group }}, "coffee_type": "{{ type }}"}'

  coffee_status:
    url: "http://localhost:8000/api/status/"
    method: GET
```

### Create Automations
```yaml
# automations.yaml
- alias: "Morning Coffee Routine"
  trigger:
    - platform: time
      at: "07:00:00"
  condition:
    - condition: state
      entity_id: person.your_name
      state: "home"
  action:
    - service: rest_command.coffee_deliver
      data:
        group: 1
        type: "single_long"
```

## Troubleshooting Deployment

### Build Failures
```bash
# Check GitHub Actions logs
# Go to: Repository → Actions → Latest workflow run

# Common issues:
# 1. Missing icon.png file
# 2. Invalid YAML syntax in config files
# 3. Docker build errors
```

### Add-on Won't Start
```bash
# Check Home Assistant logs:
# Supervisor → Coffee Machine Controller → Logs

# Common issues:
# 1. Serial port not found (/dev/ttyUSB0)
# 2. Permission denied on serial port
# 3. Coffee machine not in Modbus mode
# 4. Wrong baudrate setting
```

### Connection Issues
```bash
# Test serial connection:
ls -la /dev/tty*  # Find your device
dmesg | grep tty  # Check for USB device detection

# Test from Add-on logs:
# Look for: "Connected to coffee machine" or error messages
```

## Updating the Add-on

1. **Make changes to your code**
2. **Update version in `config.yaml`**:
   ```yaml
   version: "1.1.0"
   ```
3. **Commit and create new release**:
   ```bash
   git add .
   git commit -m "Update to v1.1.0"
   git tag v1.1.0
   git push origin main --tags
   ```
4. **Create GitHub release** - Actions will automatically build

## Support and Community

- **Repository Issues**: Use GitHub Issues for bug reports
- **Documentation**: Keep README_ADDON.md updated
- **Community**: Consider sharing on:
  - [Home Assistant Community](https://community.home-assistant.io/)
  - [Home Assistant Reddit](https://reddit.com/r/homeassistant)

## Security Considerations

- **Change default credentials** immediately after installation
- **Use strong secret keys** for Django
- **Keep the Add-on updated** for security patches
- **Limit network access** if running on public networks
- **Monitor logs** for unauthorized access attempts

## Performance Optimization

- **Set appropriate log levels** (INFO in production, DEBUG only when needed)
- **Monitor resource usage** in Home Assistant Supervisor
- **Consider hardware requirements** for multiple coffee machines
- **Use appropriate timeouts** for Modbus communication

Your Coffee Machine Controller Add-on is now ready for deployment! 🎉☕