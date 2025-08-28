# machine/coffee_machine.py
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
    """Enhanced LaSpaziale S50-QSS Robot controller with Django integration"""
    
    # Command constants
    COMMANDS = {
        'SINGLE_SHORT': 1,
        'SINGLE_LONG': 2,
        'DOUBLE_SHORT': 4,
        'DOUBLE_LONG': 8,
        'NO_ACTION': 16,
        'SINGLE_MEDIUM': 32,
        'DOUBLE_MEDIUM': 64,
        'STOP_DELIVERY': 128,
        'START_PURGE': 256,
    }
    
    # Status bit masks
    STATUS_MASKS = {
        'single_short': 0x01,
        'single_long': 0x02,
        'double_short': 0x04,
        'double_long': 0x08,
        'continuous_flow': 0x10,
        'single_medium': 0x20,
        'double_medium': 0x40,
        'purge': 0x80
    }
    
    def __init__(self, port=None, baudrate=None):
        """Initialize connection to LaSpaziale S50-QSS Robot"""
        self.port = port or getattr(settings, 'COFFEE_MACHINE_PORT', 'COM4')
        self.baudrate = baudrate or getattr(settings, 'COFFEE_MACHINE_BAUDRATE', 9600)
        
        self.client = ModbusSerialClient(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1
        )
        
        self.node_address = 1
        self.is_connected = False
        self._connection_lock = threading.Lock()
        
        logger.info(f"Coffee machine initialized on port {self.port} at {self.baudrate} bps")
    
    def connect(self) -> bool:
        """Establish connection to the coffee machine"""
        with self._connection_lock:
            try:
                self.is_connected = self.client.connect()
                if self.is_connected:
                    logger.info("Successfully connected to coffee machine")
                    # Cache connection status
                    cache.set('coffee_machine_connected', True, timeout=300)
                else:
                    logger.error("Failed to connect to coffee machine")
                    cache.set('coffee_machine_connected', False, timeout=60)
                
                return self.is_connected
            except Exception as e:
                logger.error(f"Connection error: {e}")
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
        if not self.ensure_connection():
            raise CoffeeMachineException("Cannot establish connection to coffee machine")
        
        try:
            result = self.client.read_holding_registers(address=address, count=count)
            if result.isError():
                logger.error(f"Modbus error reading registers {address}-{address+count-1}: {result}")
                return None
            return result.registers
        except Exception as e:
            logger.error(f"Error reading registers {address}-{address+count-1}: {e}")
            return None
    
    def _write_register(self, address: int, value: int) -> bool:
        """Safely write register with error handling"""
        if not self.ensure_connection():
            raise CoffeeMachineException("Cannot establish connection to coffee machine")
        
        try:
            result = self.client.write_register(address, value)
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
            'connection_status': self.is_connected,
            'port': self.port,
            'baudrate': self.baudrate,
            'last_updated': datetime.now().isoformat()
        }
        
        # Cache machine info for 5 minutes
        cache.set('machine_info', info, timeout=300)
        return info
    
    def get_serial_number(self) -> Optional[str]:
        """Read board serial number (20 chars)"""
        registers = self._read_registers(address=0, count=10)
        if registers is None:
            return None
        
        try:
            serial = ''.join([chr(reg >> 8) + chr(reg & 0xFF) for reg in registers])
            return serial.rstrip('\x00')
        except Exception as e:
            logger.error(f"Error processing serial number: {e}")
            return None
    
    def get_firmware_version(self) -> Optional[str]:
        """Read firmware version"""
        registers = self._read_registers(address=11, count=1)
        if registers is None:
            return None
        
        reg = registers[0]
        major = (reg >> 8) & 0xFF
        minor = reg & 0xFF
        return f"{major}.{minor}"
    
    def get_number_of_groups(self) -> Optional[int]:
        """Get total number of groups present"""
        registers = self._read_registers(address=270, count=1)
        return registers[0] if registers else None
    
    def is_machine_blocked(self) -> Optional[bool]:
        """Check if coffee machine is blocked"""
        registers = self._read_registers(address=269, count=1)
        return registers[0] == 1 if registers else None
    
    # Enhanced status functions
    def get_all_groups_status(self) -> Dict:
        """Get status of all groups"""
        num_groups = self.get_number_of_groups() or 3
        groups_status = {}
        
        for group in range(1, num_groups + 1):
            groups_status[f'group_{group}'] = {
                'selection': self.get_group_selection(group),
                'sensor_fault': self.get_sensor_fault(group),
                'purge_countdown': self.get_purge_countdown(group),
                'is_busy': self.is_group_busy(group)
            }
        
        status = {
            'groups': groups_status,
            'machine_blocked': self.is_machine_blocked(),
            'last_updated': datetime.now().isoformat()
        }
        
        # Cache status for 30 seconds
        cache.set('machine_status', status, timeout=30)
        return status
    
    def get_group_selection(self, group_num: int) -> Optional[Dict]:
        """Get current selection/delivery status for a group (1-3)"""
        if not 1 <= group_num <= 3:
            raise ValueError("Group number must be 1-3")
        
        register_addr = 256 + (group_num - 1)
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
        """Check if volumetric sensor has fault for group (1-3)"""
        if not 1 <= group_num <= 3:
            raise ValueError("Group number must be 1-3")
        
        register_addr = 260 + (group_num - 1)
        registers = self._read_registers(register_addr, count=1)
        return registers[0] == 1 if registers else None
    
    def get_purge_countdown(self, group_num: int) -> Optional[int]:
        """Get seconds until automatic purge for group (1-3)"""
        if not 1 <= group_num <= 3:
            raise ValueError("Group number must be 1-3")
        
        register_addr = 264 + (group_num - 1)
        registers = self._read_registers(register_addr, count=1)
        return registers[0] if registers else None
    
    def is_group_busy(self, group_num: int) -> Optional[bool]:
        """Check if a group is busy (has an ongoing delivery)"""
        if not 1 <= group_num <= 3:
            raise ValueError("Group number must be 1-3")
        
        register_addr = 256 + (group_num - 1)
        registers = self._read_registers(register_addr, count=1)
        
        if registers is None:
            return None
        
        status = registers[0]
        delivery_mask = 0xFF  # Bits 0-7 for coffee delivery
        return (status & delivery_mask) != 0
    
    # Enhanced command functions
    def send_coffee_command(self, group_num: int, command: int) -> bool:
        """Send coffee delivery command to group (1-3)"""
        if not 1 <= group_num <= 3:
            raise ValueError("Group number must be 1-3")
        
        if command not in self.COMMANDS.values():
            raise ValueError(f"Invalid command: {command}")
        
        register_addr = 512 + (group_num - 1)
        result = self._write_register(register_addr, command)
        
        if result:
            logger.info(f"Command {command} sent to group {group_num}")
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
        """Send water delivery command"""
        return self._write_register(516, set_num)
    
    def send_mat_command(self, set_num: int) -> bool:
        """Send MAT delivery command"""
        return self._write_register(517, set_num)
    
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
            
            # Check all groups
            num_groups = self.get_number_of_groups() or 3
            for group in range(1, num_groups + 1):
                try:
                    group_status = {
                        'busy': self.is_group_busy(group),
                        'sensor_fault': self.get_sensor_fault(group),
                        'purge_countdown': self.get_purge_countdown(group)
                    }
                    health['groups_status'][f'group_{group}'] = group_status
                    
                    if group_status['sensor_fault']:
                        health['errors'].append(f'Sensor fault detected on group {group}')
                        
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

def get_coffee_machine() -> LaSpazialeCoffeeMachine:
    """Get singleton coffee machine instance"""
    global _coffee_machine_instance
    
    if _coffee_machine_instance is None:
        with _instance_lock:
            if _coffee_machine_instance is None:
                _coffee_machine_instance = LaSpazialeCoffeeMachine()
                
    return _coffee_machine_instance