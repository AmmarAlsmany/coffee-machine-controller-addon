# Setup Instructions (README.md)
"""
# Coffee Machine Controller - Django Web Interface

## Overview
A comprehensive Django web interface for controlling LaSpaziale S50-DEMO Robot coffee machines via Modbus RTU communication.

## Features
- Real-time machine monitoring and control
- Web-based dashboard with responsive design
- REST API for programmatic access
- Coffee delivery tracking and logging
- Maintenance logs and health checks
- Multi-group support (up to 3 groups)
- Automatic status updates
- Error handling and recovery

## Installation

### 1. Clone and Setup
```bash
git clone <your-repository>
cd coffee_machine_controller
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Settings
Edit `coffee_machine_controller/settings.py`:

```python
# Coffee Machine Settings
COFFEE_MACHINE_PORT = 'COM4'  # Windows: 'COM4', Linux: '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_BG01CG7P-if00-port0'
COFFEE_MACHINE_BAUDRATE = 9600
```

### 5. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 6. Test Connection
```bash
python manage.py test_connection --port COM4 --baudrate 9600
```

### 7. Run Development Server
```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000 to access the dashboard.

## Hardware Setup

### Serial Connection
1. Connect your computer to the coffee machine via RS485/RS232 adapter
2. Ensure proper wiring:
   - Data+ (A) and Data- (B) for RS485
   - TX, RX, GND for RS232
3. Set machine to Modbus RTU mode with address 1

### Supported Hardware
- LaSpaziale S50-DEMO Robot
- RS485/USB adapters
- RS232/USB adapters

## Usage

### Web Dashboard
1. Navigate to http://127.0.0.1:8000
2. Click "Connect" to establish connection
3. Use the group controls to:
   - Deliver different coffee types
   - Stop ongoing deliveries
   - Start purge cycles
   - Monitor group status

### REST API Endpoints

#### Machine Control
- `GET /api/info/` - Get machine information
- `GET /api/status/` - Get current status
- `POST /api/connect/` - Connect to machine
- `POST /api/disconnect/` - Disconnect from machine
- `GET /api/health/` - Perform health check

#### Coffee Delivery
- `POST /api/deliver/` - Deliver coffee
  ```json
  {
    "group_number": 1,
    "coffee_type": "single_long"
  }
  ```
- `POST /api/stop/` - Stop delivery
  ```json
  {
    "group_number": 1
  }
  ```
- `POST /api/purge/` - Start purge cycle
  ```json
  {
    "group_number": 1
  }
  ```

#### History and Logs
- `GET /api/history/` - Get delivery history
- `GET /api/logs/` - Get maintenance logs

### Coffee Types
- `single_short` - Single Short Coffee
- `single_medium` - Single Medium Coffee
- `single_long` - Single Long Coffee
- `double_short` - Double Short Coffee
- `double_medium` - Double Medium Coffee
- `double_long` - Double Long Coffee

## API Examples

### Python Client Example
```python
import requests
import json

base_url = 'http://127.0.0.1:8000/api'

# Connect to machine
response = requests.post(f'{base_url}/connect/')
print(response.json())

# Get machine status
response = requests.get(f'{base_url}/status/')
status = response.json()
print(f"Machine status: {status}")

# Deliver coffee
response = requests.post(f'{base_url}/deliver/', 
                        json={
                            'group_number': 1,
                            'coffee_type': 'single_long'
                        })
result = response.json()
print(f"Coffee delivery: {result}")

# Check delivery history
response = requests.get(f'{base_url}/history/')
history = response.json()
print(f"Recent deliveries: {len(history['deliveries'])}")
```

### JavaScript/AJAX Example
```javascript
// Connect to machine
async function connectMachine() {
    const response = await fetch('/api/connect/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    });
    return await response.json();
}

// Deliver coffee
async function deliverCoffee(group, type) {
    const response = await fetch('/api/deliver/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            group_number: group,
            coffee_type: type
        })
    });
    return await response.json();
}
```

## Production Deployment

### Using Gunicorn
```bash
pip install gunicorn
gunicorn coffee_machine_controller.wsgi:application --bind 0.0.0.0:8000
```

### Using Docker
Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput
RUN python manage.py migrate

EXPOSE 8000

CMD ["gunicorn", "coffee_machine_controller.wsgi:application", "--bind", "0.0.0.0:8000"]
```

Build and run:
```bash
docker build -t coffee-controller .
docker run -p 8000:8000 --device=/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_BG01CG7P-if00-port0 coffee-controller
```

### Environment Variables
Set these in production:
```bash
export DJANGO_SECRET_KEY='your-secret-key'
export DJANGO_DEBUG=False
export COFFEE_MACHINE_PORT='/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_BG01CG7P-if00-port0'
export COFFEE_MACHINE_BAUDRATE=9600
```

## Monitoring and Logging

### Log Files
- `coffee_machine.log` - Application logs
- Django logs in console/file

### Health Monitoring
- `/api/health/` endpoint for monitoring
- Automatic connection recovery
- Status caching for performance

### Metrics
- Delivery success rates
- Group utilization
- Error tracking
- Response times

## Troubleshooting

### Common Issues

#### Connection Problems
1. **Port not found**: Check device manager (Windows) or `ls /dev/tty*` (Linux)
2. **Permission denied**: Add user to dialout group: `sudo usermod -a -G dialout $USER`
3. **Port in use**: Close other applications using the serial port

#### Machine Not Responding
1. Check physical connections
2. Verify machine is in Modbus mode
3. Test with different baudrates
4. Use `python manage.py test_connection` command

#### Web Interface Issues
1. Clear browser cache
2. Check JavaScript console for errors
3. Verify API endpoints are responding
4. Check network connectivity

### Debug Mode
Enable debug logging in settings:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'machine': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Security Considerations

### Production Security
1. Change `SECRET_KEY` in production
2. Set `DEBUG = False`
3. Configure `ALLOWED_HOSTS`
4. Use HTTPS in production
5. Implement authentication for API access

### Network Security
1. Restrict access to coffee machine network
2. Use VPN for remote access
3. Monitor API usage
4. Implement rate limiting

## Development

### Project Structure
```
coffee_machine_controller/
├── manage.py
├── requirements.txt
├── coffee_machine_controller/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── machine/
│   ├── models.py
│   ├── views.py
│   ├── coffee_machine.py
│   └── management/commands/
└── templates/
    ├── base.html
    └── dashboard.html
```

### Adding Features
1. Extend models in `machine/models.py`
2. Add API endpoints in `machine/views.py`
3. Update frontend in templates
4. Add tests in `machine/tests.py`

### Testing
```bash
python manage.py test
python manage.py test_connection --port COM4
```

## License
This project is licensed under the MIT License.

## Support
For support and questions:
1. Check the troubleshooting section
2. Review logs for errors
3. Test hardware connections
4. Consult Modbus RTU documentation
"""