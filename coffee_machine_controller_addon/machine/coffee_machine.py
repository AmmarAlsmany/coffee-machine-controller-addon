# machine/coffee_machine.py - CORRECTED VERSION
import time
import logging
import threading
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('machine')

class CoffeeMachineException(Exception):
    """Custom exception for coffee machine operations"""
    pass

class LaSpazialeCoffeeMachine:
    """Enhanced LaSpaziale S50-QSS Robot controller with correct register addresses"""
    
    # Command constants (from official documentation)
    COMMANDS = {
        'SINGLE_SHORT': 0x0001,     # 1
        'SINGLE_LONG': 0x0002,      # 2
        'DOUBLE_SHORT': 0x0004,     # 4
        'DOUBLE_LONG': 0x0008,      # 8
        'NO_ACTION': 0x0010,        # 16
        'SINGLE_MEDIUM': 0x0020,    # 32
        'DOUBLE_MEDIUM': 0x0040,    # 64
        'STOP_DELIVERY': 0x0080,    # 128
        'START_PURGE': 0x0100,      # 256
    }
    
    # Status bit masks (from official documentation)
    STATUS_MASKS = {
        'single_short': 0x0001,     # bit 0
        'single_long': 0x0002,      # bit 1
        'double_short': 0x0004,     # bit 2
        'double_long': 0x0008,      # bit 3
        'continuous_flow': 0x0010,  # bit 4
        'single_medium': 0x0020,    # bit 5
        'double_medium': 0x0040,    # bit 6
        'purge': 0x0080             # bit 7
    }
    
    # Register addresses (from official documentation)
    REGISTERS = {
        # Group 0: Identifying
        'SERIAL_NUMBER': 0,         # 0-9 (20 chars, 10 registers)
        'FIRMWARE_VERSION': 11,     # 11 (2 bytes: major.minor)
        
        # Group 1: Coffee Machine State
        'GROUP_1_SELECTION': 256,   # 0x100
        'GROUP_2_SELECTION': 257,   # 0x101
        'GROUP_3_SELECTION': 258,   # 0x102
        'GROUP_4_SELECTION': 259,   # 0x103
        
        'SENSOR_FAULT_GROUP_1': 260,  # 0x104
        'SENSOR_FAULT_GROUP_2': 261,  # 0x105
        'SENSOR_FAULT_GROUP_3': 262,  # 0x106
        'SENSOR_FAULT_GROUP_4': 263,  # 0x107
        
        'PURGE_COUNTDOWN_GROUP_1': 264,  # 0x108
        'PURGE_COUNTDOWN_GROUP_2': 265,  # 0x109
        'PURGE_COUNTDOWN_GROUP_3': 266,  # 0x10A
        'PURGE_COUNTDOWN_GROUP_4': 267,  # 0x10B
        
        'MACHINE_CONFIG': 268,      # 0x10C
        'MACHINE_BLOCKED': 269,     # 0x10D
        'NUMBER_OF_GROUPS': 270,    # 0x10E
        
        # Group 2: Commands
        'COMMAND_GROUP_1': 512,     # 0x200
        'COMMAND_GROUP_2': 513,     # 0x201
        'COMMAND_GROUP_3': 514,     # 0x202
        'COMMAND_GROUP_4': 515,     # 0x203
        'WATER_COMMAND': 516,       # 0x204
        'MAT_COMMAND': 517,         # 0x205
    }
    
    def __init__(self, port=None, baudrate=None):
        """Initialize connection to LaSpaziale S50-QSS Robot"""
        self.port = port or getattr(settings, 'COFFEE_MACHINE_PORT', '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_BG01CG7P-if00-port0')
        self.baudrate = baudrate or getattr(settings, 'COFFEE_MACHINE_BAUDRATE', 9600)
        
        try:
            # Official communication settings from documentation
            self.client = ModbusSerialClient(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',        # None
                stopbits=1,        # 1 stop bit
                timeout=2          # Increased timeout for RS232
            )
        except Exception as e:
            logger.error(f"Failed to create Modbus client: {e}")
            # Create a dummy client that will fail on connect
            self.client = None
        
        self.node_address = 0x01  # Official node address from documentation
        self.is_connected = False
        self._connection_lock = threading.Lock()
        
        logger.info(f"Coffee machine initialized on port {self.port} at {self.baudrate} bps")
    
    def connect(self) -> bool:
        """Establish connection to the coffee machine"""
        with self._connection_lock:
            try:
                if self.client is None:
                    logger.error("Modbus client not initialized - check port settings")
                    self.is_connected = False
                    cache.set('coffee_machine_connected', False, timeout=60)
                    return False
                    
                self.is_connected = self.client.connect()
                if self.is_connected:
                    logger.info("Successfully connected to coffee machine")
                    cache.set('coffee_machine_connected', True, timeout=300)
                else:
                    logger.error(f"Failed to connect to coffee machine on {self.port}")
                    cache.set('coffee_machine_connected', False, timeout=60)
                
                return self.is_connected
            except Exception as e:
                logger.error(f"Connection error on {self.port}: {e}")
                self.is_connected = False
                cache.set('coffee_machine_connected', False, timeout=60)
                return False
    
    def disconnect(self):
        """Close connection"""
        with self._connection_lock:
            try:
                if self.client:
                    self.client.close()
                self.is_connected = False
                cache.set('coffee_machine_connected', False, timeout=60)
                logger.info("Disconnected from coffee machine")
            except Exception as e:
                logger.error(f"Disconnection error: {e}")
    
    def ensure_connection(self) -> bool:
        """Ensure connection is active, reconnect if needed"""
        if not self.is_connected:
            return self.connect()
        return True
    
    def _read_registers(self, address: int, count: int = 1) -> Optional[List[int]]:
        """Safely read registers with error handling"""
        if not self.is_connected:
            logger.warning(f"Attempted to read registers while disconnected")
            return None
            
        if not self.ensure_connection():
            logger.error("Cannot establish connection to coffee machine")
            return None
        
        try:
            result = self.client.read_holding_registers(
                address=address, 
                count=count, 
                slave=self.node_address
            )
            if result.isError():
                logger.error(f"Modbus error reading registers {address}-{address+count-1}: {result}")
                return None
            return result.registers
        except Exception as e:
            logger.error(f"Error reading registers {address}-{address+count-1}: {e}")
            return None
    
    def _write_register(self, address: int, value: int) -> bool:
        """Safely write register with error handling"""
        if not self.is_connected:
            logger.warning(f"Attempted to write register while disconnected")
            return False
            
        if not self.ensure_connection():
            logger.error("Cannot establish connection to coffee machine")
            return False
        
        try:
            result = self.client.write_register(
                address=address, 
                value=value, 
                slave=self.node_address
            )
            success = not result.isError()
            if success:
                logger.info(f"Successfully wrote value {value} to register {address}")
            else:
                logger.error(f"Failed to write value {value} to register {address}: {result}")
            return success
        except Exception as e:
            logger.error(f"Error writing register {address}: {e}")
            return False
    
    # Enhanced identification functions
    def get_machine_info(self) -> Dict:
        """Get comprehensive machine information"""
        info = {
            'serial_number': self.get_serial_number(),
            'firmware_version': self.get_firmware_version(),
            'number_of_groups': self.get_number_of_groups(),
            'is_blocked': self.is_machine_blocked(),
            'machine_config': self.get_machine_config(),
            'connection_status': self.is_connected,
            'port': self.port,
            'baudrate': self.baudrate,
            'last_updated': datetime.now().isoformat()
        }
        
        # Cache machine info for 5 minutes
        cache.set('machine_info', info, timeout=300)
        return info
    
    def get_serial_number(self) -> Optional[str]:
        """Read board serial number (20 chars from registers 0-9)"""
        registers = self._read_registers(address=self.REGISTERS['SERIAL_NUMBER'], count=10)
        if registers is None:
            return None
        
        try:
            # Convert 10 registers (20 bytes) to string
            serial_chars = []
            for reg in registers:
                # Each register contains 2 characters (high byte, low byte)
                high_char = chr((reg >> 8) & 0xFF) if (reg >> 8) & 0xFF != 0 else ''
                low_char = chr(reg & 0xFF) if reg & 0xFF != 0 else ''
                serial_chars.extend([high_char, low_char])
            
            serial = ''.join(serial_chars).rstrip('\x00')
            return serial if serial else None
        except Exception as e:
            logger.error(f"Error processing serial number: {e}")
            return None
    
    def get_firmware_version(self) -> Optional[str]:
        """Read firmware version (register 11)"""
        registers = self._read_registers(address=self.REGISTERS['FIRMWARE_VERSION'], count=1)
        if registers is None:
            return None
        
        reg = registers[0]
        major = (reg >> 8) & 0xFF  # High byte = major version
        minor = reg & 0xFF         # Low byte = minor version
        return f"{major}.{minor}"
    
    def get_number_of_groups(self) -> Optional[int]:
        """Get total number of groups present (register 270)"""
        registers = self._read_registers(address=self.REGISTERS['NUMBER_OF_GROUPS'], count=1)
        return registers[0] if registers else None
    
    def is_machine_blocked(self) -> Optional[bool]:
        """Check if coffee machine is blocked (register 269)"""
        registers = self._read_registers(address=self.REGISTERS['MACHINE_BLOCKED'], count=1)
        return registers[0] == 1 if registers else None
    
    def get_machine_config(self) -> Optional[Dict]:
        """Get machine configuration (register 268)"""
        registers = self._read_registers(address=self.REGISTERS['MACHINE_CONFIG'], count=1)
        if registers is None:
            return None
        
        config_value = registers[0]
        doses_config = config_value & 0x03  # bits 0-1
        
        doses_map = {
            0x00: 4,  # 4 doses available
            0x01: 6,  # 6 doses available
            0x02: 2,  # 2 doses available
            0x03: 0   # Not used configuration
        }
        
        return {
            'doses_available': doses_map.get(doses_config, 0),
            'raw_config': config_value
        }
    
    # Enhanced status functions
    def get_all_groups_status(self) -> Dict:
        """Get status of all groups"""
        num_groups = self.get_number_of_groups() or 3
        groups_status = {}
        
        for group in range(1, min(num_groups + 1, 5)):  # Max 4 groups supported
            groups_status[f'group_{group}'] = {
                'selection': self.get_group_selection(group),
                'sensor_fault': self.get_sensor_fault(group),
                'purge_countdown': self.get_purge_countdown(group),
                'is_busy': self.is_group_busy(group)
            }
        
        status = {
            'groups': groups_status,
            'machine_blocked': self.is_machine_blocked(),
            'machine_config': self.get_machine_config(),
            'last_updated': datetime.now().isoformat()
        }
        
        # Cache status for 30 seconds
        cache.set('machine_status', status, timeout=30)
        return status
    
    def get_group_selection(self, group_num: int) -> Optional[Dict]:
        """Get current selection/delivery status for a group (1-4)"""
        if not 1 <= group_num <= 4:
            raise ValueError("Group number must be 1-4")
        
        register_map = {
            1: self.REGISTERS['GROUP_1_SELECTION'],
            2: self.REGISTERS['GROUP_2_SELECTION'],
            3: self.REGISTERS['GROUP_3_SELECTION'],
            4: self.REGISTERS['GROUP_4_SELECTION']
        }
        
        register_addr = register_map[group_num]
        registers = self._read_registers(register_addr, count=1)
        
        if registers is None:
            return None
        
        status = registers[0]
        return {
            'single_short': bool(status & self.STATUS_MASKS['single_short']),
            'single_long': bool(status & self.STATUS_MASKS['single_long']),
            'double_short': bool(status & self.STATUS_MASKS['double_short']),
            'double_long': bool(status & self.STATUS_MASKS['double_long']),
            'continuous_flow': bool(status & self.STATUS_MASKS['continuous_flow']),
            'single_medium': bool(status & self.STATUS_MASKS['single_medium']),
            'double_medium': bool(status & self.STATUS_MASKS['double_medium']),
            'purge': bool(status & self.STATUS_MASKS['purge']),
            'raw_status': status
        }
    
    def get_sensor_fault(self, group_num: int) -> Optional[bool]:
        """Check if volumetric sensor has fault for group (1-4)"""
        if not 1 <= group_num <= 4:
            raise ValueError("Group number must be 1-4")
        
        register_map = {
            1: self.REGISTERS['SENSOR_FAULT_GROUP_1'],
            2: self.REGISTERS['SENSOR_FAULT_GROUP_2'],
            3: self.REGISTERS['SENSOR_FAULT_GROUP_3'],
            4: self.REGISTERS['SENSOR_FAULT_GROUP_4']
        }
        
        register_addr = register_map[group_num]
        registers = self._read_registers(register_addr, count=1)
        return registers[0] == 1 if registers else None
    
    def get_purge_countdown(self, group_num: int) -> Optional[int]:
        """Get seconds until automatic purge for group (1-4)"""
        if not 1 <= group_num <= 4:
            raise ValueError("Group number must be 1-4")
        
        register_map = {
            1: self.REGISTERS['PURGE_COUNTDOWN_GROUP_1'],
            2: self.REGISTERS['PURGE_COUNTDOWN_GROUP_2'],
            3: self.REGISTERS['PURGE_COUNTDOWN_GROUP_3'],
            4: self.REGISTERS['PURGE_COUNTDOWN_GROUP_4']
        }
        
        register_addr = register_map[group_num]
        registers = self._read_registers(register_addr, count=1)
        return registers[0] if registers else None
    
    def is_group_busy(self, group_num: int) -> Optional[bool]:
        """Check if a group is busy (has an ongoing delivery)"""
        selection = self.get_group_selection(group_num)
        if selection is None:
            return None
        
        # Check if any delivery is ongoing (bits 0-7)
        return (selection['single_short'] or selection['single_long'] or 
                selection['double_short'] or selection['double_long'] or
                selection['continuous_flow'] or selection['single_medium'] or
                selection['double_medium'] or selection['purge'])
    
    # Enhanced command functions
    def send_coffee_command(self, group_num: int, command: int) -> bool:
        """Send coffee delivery command to group (1-4)"""
        if not 1 <= group_num <= 4:
            raise ValueError("Group number must be 1-4")
        
        if command not in self.COMMANDS.values():
            raise ValueError(f"Invalid command: {command}")
        
        register_map = {
            1: self.REGISTERS['COMMAND_GROUP_1'],
            2: self.REGISTERS['COMMAND_GROUP_2'],
            3: self.REGISTERS['COMMAND_GROUP_3'],
            4: self.REGISTERS['COMMAND_GROUP_4']
        }
        
        register_addr = register_map[group_num]
        result = self._write_register(register_addr, command)
        
        if result:
            logger.info(f"Command {command} (0x{command:04X}) sent to group {group_num}")
            # Clear cached status to force refresh
            cache.delete('machine_status')
        
        return result
    
    def deliver_coffee(self, group_num: int, coffee_type: str) -> Dict:
        """Deliver specific coffee type with enhanced error handling"""
        command_map = {
            'single_short': self.COMMANDS['SINGLE_SHORT'],
            'single_medium': self.COMMANDS['SINGLE_MEDIUM'],
            'single_long': self.COMMANDS['SINGLE_LONG'],
            'double_short': self.COMMANDS['DOUBLE_SHORT'],
            'double_medium': self.COMMANDS['DOUBLE_MEDIUM'],
            'double_long': self.COMMANDS['DOUBLE_LONG']
        }
        
        if coffee_type not in command_map:
            raise ValueError(f"Invalid coffee type: {coffee_type}")
        
        # Check if group is busy before sending command
        if self.is_group_busy(group_num):
            return {
                'success': False,
                'message': f'Group {group_num} is currently busy',
                'group': group_num,
                'coffee_type': coffee_type
            }
        
        # Check purge countdown - don't deliver if near purge time
        countdown = self.get_purge_countdown(group_num)
        if countdown is not None and countdown < 10:  # Less than 10 seconds to purge
            return {
                'success': False,
                'message': f'Group {group_num} is near automatic purge ({countdown}s). Please wait.',
                'group': group_num,
                'coffee_type': coffee_type
            }
        
        command = command_map[coffee_type]
        success = self.send_coffee_command(group_num, command)
        
        return {
            'success': success,
            'message': f'{"Successfully delivered" if success else "Failed to deliver"} {coffee_type} on group {group_num}',
            'group': group_num,
            'coffee_type': coffee_type,
            'command': command,
            'timestamp': datetime.now().isoformat()
        }
    
    def stop_delivery(self, group_num: int) -> bool:
        """Stop ongoing delivery"""
        return self.send_coffee_command(group_num, self.COMMANDS['STOP_DELIVERY'])
    
    def start_purge(self, group_num: int) -> bool:
        """Start purge cycle"""
        return self.send_coffee_command(group_num, self.COMMANDS['START_PURGE'])
    
    def wait_until_group_is_free(self, group_num: int, timeout: int = 30, 
                                check_interval: float = 1.0) -> bool:
        """Wait until the group is free (not busy with any delivery)"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            busy = self.is_group_busy(group_num)
            
            if busy is None:
                logger.error(f"Error checking group {group_num} status")
                return False
            
            if not busy:
                logger.info(f"Group {group_num} is now free")
                return True
            
            logger.debug(f"Group {group_num} is busy, waiting...")
            time.sleep(check_interval)
        
        logger.warning(f"Timeout waiting for group {group_num} to become free")
        return False
    
    # Water and MAT commands
    def send_water_command(self, set_num: int) -> bool:
        """Send water delivery command (1=SET1, 2=SET2, 0=stop)"""
        if set_num not in [0, 1, 2]:
            raise ValueError("Water set number must be 0, 1, or 2")
        return self._write_register(self.REGISTERS['WATER_COMMAND'], set_num)
    
    def send_mat_command(self, set_num: int) -> bool:
        """Send MAT delivery command (1=SET1, 2=SET2, 0=stop)"""
        if set_num not in [0, 1, 2]:
            raise ValueError("MAT set number must be 0, 1, or 2")
        return self._write_register(self.REGISTERS['MAT_COMMAND'], set_num)
    
    # Health check and diagnostics
    def health_check(self) -> Dict:
        """Perform comprehensive health check"""
        health = {
            'connection': self.is_connected,
            'machine_blocked': False,
            'groups_status': {},
            'timestamp': datetime.now().isoformat(),
            'errors': []
        }
        
        try:
            # Check machine block status
            blocked = self.is_machine_blocked()
            health['machine_blocked'] = blocked if blocked is not None else False
            if blocked:
                health['errors'].append('Machine is blocked - no deliveries possible')
            
            # Check all groups
            num_groups = self.get_number_of_groups() or 3
            for group in range(1, min(num_groups + 1, 5)):
                try:
                    group_status = {
                        'busy': self.is_group_busy(group),
                        'sensor_fault': self.get_sensor_fault(group),
                        'purge_countdown': self.get_purge_countdown(group)
                    }
                    health['groups_status'][f'group_{group}'] = group_status
                    
                    if group_status['sensor_fault']:
                        health['errors'].append(f'Sensor fault detected on group {group}')
                    
                    if group_status['purge_countdown'] is not None and group_status['purge_countdown'] < 30:
                        health['errors'].append(f'Group {group} approaching automatic purge in {group_status["purge_countdown"]}s')
                        
                except Exception as e:
                    health['errors'].append(f'Error checking group {group}: {str(e)}')
            
        except Exception as e:
            health['errors'].append(f'Health check error: {str(e)}')
        
        health['overall_status'] = 'healthy' if not health['errors'] and health['connection'] else 'unhealthy'
        
        # Cache health check results
        cache.set('machine_health', health, timeout=60)
        return health


# Singleton instance for Django integration
_coffee_machine_instance = None
_instance_lock = threading.Lock()

def get_coffee_machine(port=None, baudrate=None, force_new=False) -> LaSpazialeCoffeeMachine:
    """Get singleton coffee machine instance
    
    Args:
        port: Override port for the connection
        baudrate: Override baudrate for the connection  
        force_new: Force creation of a new instance with new parameters
    """
    global _coffee_machine_instance
    
    # If forcing new instance or parameters changed, recreate
    if force_new or (port and _coffee_machine_instance and _coffee_machine_instance.port != port):
        with _instance_lock:
            if _coffee_machine_instance:
                _coffee_machine_instance.disconnect()
            _coffee_machine_instance = LaSpazialeCoffeeMachine(port=port, baudrate=baudrate)
    
    if _coffee_machine_instance is None:
        with _instance_lock:
            if _coffee_machine_instance is None:
                _coffee_machine_instance = LaSpazialeCoffeeMachine(port=port, baudrate=baudrate)
                
    return _coffee_machine_instance