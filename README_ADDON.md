# Coffee Machine Controller - Home Assistant Add-on

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]
![Supports armhf Architecture][armhf-shield]
![Supports armv7 Architecture][armv7-shield]
![Supports i386 Architecture][i386-shield]

_Control your LaSpaziale S50-DEMO Robot coffee machine from Home Assistant!_

## About

This Home Assistant Add-on provides a web interface to control LaSpaziale S50-DEMO Robot coffee machines via Modbus RTU communication. It offers:

- **Real-time Control**: Start, stop, and monitor coffee deliveries
- **Multiple Coffee Types**: Support for 6 different coffee variations
- **Web Dashboard**: Clean, responsive web interface
- **REST API**: Full API access for automation
- **Health Monitoring**: Automatic status checks and logging
- **Multi-Group Support**: Control up to 3 groups simultaneously

## Installation

### Method 1: Add Repository (Recommended)

1. Navigate to **Supervisor** → **Add-on Store** in your Home Assistant UI
2. Click the **⋮** menu and select **Repositories**
3. Add this repository URL: `https://github.com/AmmarAlsmany/hassio-addons`
4. Find **Coffee Machine Controller** in the add-on store
5. Click **Install**

### Method 2: Manual Installation

1. Copy the add-on files to `/addons/coffee_machine_controller/` on your Home Assistant system
2. Navigate to **Supervisor** → **Add-on Store**
3. Refresh the page
4. Find **Coffee Machine Controller** in the local add-ons section
5. Click **Install**

## Configuration

### Basic Configuration

```yaml
serial_port: "/dev/ttyUSB0"
baudrate: 9600
django_secret_key: "your-secure-random-secret-key"
debug: false
log_level: "INFO"
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `serial_port` | `/dev/ttyUSB0` | Serial port connected to coffee machine |
| `baudrate` | `9600` | Serial communication baud rate |
| `django_secret_key` | auto-generated | Django secret key for security |
| `debug` | `false` | Enable debug mode |
| `log_level` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |

### Hardware Setup

1. **Connect Hardware**:
   - Connect your computer/Raspberry Pi to the coffee machine via RS485/RS232 adapter
   - Ensure proper wiring (Data+ and Data- for RS485, TX/RX/GND for RS232)

2. **Find Serial Port**:
   ```bash
   # In Home Assistant SSH add-on:
   ls /dev/tty*
   # Look for devices like /dev/ttyUSB0, /dev/ttyACM0, etc.
   ```

3. **Configure Machine**:
   - Set coffee machine to Modbus RTU mode
   - Set machine address to `1`
   - Ensure baudrate matches configuration

## Usage

### Web Interface

1. Start the add-on
2. Click **Open Web UI** or navigate to `http://your-ha-ip:8000`
3. Click **Connect** to establish communication
4. Use the group controls to operate your coffee machine

### Home Assistant Integration

The add-on exposes a REST API that can be integrated with Home Assistant automations:

#### Example Automation
```yaml
automation:
  - alias: "Morning Coffee"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: rest_command.make_coffee
        data:
          group_number: 1
          coffee_type: "single_long"

rest_command:
  make_coffee:
    url: "http://localhost:8000/api/deliver/"
    method: POST
    headers:
      Content-Type: "application/json"
    payload: |
      {
        "group_number": {{ group_number }},
        "coffee_type": "{{ coffee_type }}"
      }
```

### API Endpoints

#### Machine Control
- `GET /api/info/` - Get machine information
- `GET /api/status/` - Get current status
- `POST /api/connect/` - Connect to machine
- `POST /api/disconnect/` - Disconnect from machine

#### Coffee Operations
- `POST /api/deliver/` - Start coffee delivery
- `POST /api/stop/` - Stop current delivery
- `POST /api/purge/` - Start purge cycle

#### Monitoring
- `GET /api/health/` - Health check
- `GET /api/history/` - Delivery history
- `GET /api/logs/` - System logs

## Supported Coffee Types

- `single_short` - Single Short Coffee
- `single_medium` - Single Medium Coffee
- `single_long` - Single Long Coffee
- `double_short` - Double Short Coffee
- `double_medium` - Double Medium Coffee
- `double_long` - Double Long Coffee

## Troubleshooting

### Common Issues

#### 1. Serial Port Not Found
```
Error: Could not open port /dev/ttyUSB0
```
**Solution**:
- Check hardware connections
- Verify correct port in configuration
- Ensure port has proper permissions

#### 2. Machine Not Responding
```
Error: No response from coffee machine
```
**Solution**:
- Verify machine is in Modbus RTU mode
- Check baudrate settings
- Test different serial ports
- Verify wiring connections

#### 3. Permission Denied
```
Error: Permission denied: '/dev/ttyUSB0'
```
**Solution**: The add-on should handle permissions automatically, but if issues persist:
- Restart the add-on
- Check Home Assistant host system permissions

### Debug Mode

Enable debug mode for detailed logging:
```yaml
debug: true
log_level: "DEBUG"
```

Check logs in **Supervisor** → **Coffee Machine Controller** → **Logs**.

### Health Check

Monitor add-on health:
- Web UI: Navigate to `http://your-ha-ip:8000/api/health/`
- Logs: Check for connection status and error messages

## Support

- **Documentation**: [Full README](README.md)
- **Issues**: [GitHub Issues](https://github.com/AmmarAlsmany/coffee_machine_controller/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AmmarAlsmany/coffee_machine_controller/discussions)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with your coffee machine
5. Submit a pull request

## Changelog & Releases

This repository keeps a change log using [GitHub's releases][releases]
functionality.

Releases are based on [Semantic Versioning][semver], and use the format
of `MAJOR.MINOR.PATCH`. In a nutshell, the version will be incremented
based on the following:

- `MAJOR`: Incompatible or major changes.
- `MINOR`: Backwards-compatible new features and enhancements.
- `PATCH`: Backwards-compatible bugfixes and package updates.

## License

MIT License - see the [LICENSE](LICENSE) file for details.

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[commits-shield]: https://img.shields.io/github/commit-activity/y/AmmarAlsmany/coffee_machine_controller.svg
[commits]: https://github.com/AmmarAlsmany/coffee_machine_controller/commits/main
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
[license-shield]: https://img.shields.io/github/license/AmmarAlsmany/coffee_machine_controller.svg
[releases-shield]: https://img.shields.io/github/release/AmmarAlsmany/coffee_machine_controller.svg
[releases]: https://github.com/AmmarAlsmany/coffee_machine_controller/releases
[semver]: http://semver.org/spec/v2.0.0.html