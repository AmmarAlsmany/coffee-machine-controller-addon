from django.core.management.base import BaseCommand
from pymodbus.client import ModbusSerialClient
import time

class Command(BaseCommand):
    help = 'Debug Modbus communication with detailed diagnostics'
    
    def handle(self, *args, **options):
        port = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_BG01CG7P-if00-port0'
        
        # Test 1: Basic connection with different timeouts
        self.stdout.write("=== Test 1: Connection with different timeouts ===")
        for timeout in [1, 2, 3, 5]:
            client = ModbusSerialClient(
                port=port,
                baudrate=9600,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=timeout
            )
            
            try:
                if client.connect():
                    self.stdout.write(f"Connected with {timeout}s timeout")
                    
                    # Try simple read
                    result = client.read_holding_registers(0, 1, slave=1)
                    if not result.isError():
                        self.stdout.write(f"SUCCESS: Read register 0 = {result.registers[0]}")
                        client.close()
                        break
                    else:
                        self.stdout.write(f"Read failed: {result}")
                else:
                    self.stdout.write(f"Connection failed with {timeout}s timeout")
                client.close()
            except Exception as e:
                self.stdout.write(f"Error with {timeout}s timeout: {e}")
        
        # Test 2: Different Modbus functions
        self.stdout.write("\n=== Test 2: Different Modbus functions ===")
        client = ModbusSerialClient(port=port, baudrate=9600, timeout=3)
        
        if client.connect():
            functions_to_test = [
                ('read_coils', lambda: client.read_coils(0, 1, slave=1)),
                ('read_discrete_inputs', lambda: client.read_discrete_inputs(0, 1, slave=1)),
                ('read_holding_registers', lambda: client.read_holding_registers(0, 1, slave=1)),
                ('read_input_registers', lambda: client.read_input_registers(0, 1, slave=1)),
            ]
            
            for func_name, func in functions_to_test:
                try:
                    result = func()
                    if not result.isError():
                        self.stdout.write(f"✓ {func_name}: SUCCESS")
                    else:
                        self.stdout.write(f"✗ {func_name}: {result}")
                except Exception as e:
                    self.stdout.write(f"✗ {func_name}: {e}")
                time.sleep(0.5)
            
            client.close()
        
        # Test 3: Raw frame inspection
        self.stdout.write("\n=== Test 3: Raw frame inspection ===")
        import serial
        
        try:
            ser = serial.Serial(port, 9600, timeout=2)
            self.stdout.write("Serial port opened for raw communication")
            
            # Manually construct Modbus RTU frame for reading holding register 0
            # Slave ID: 1, Function: 3, Start: 0, Count: 1
            frame = bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x01, 0x84, 0x0A])  # CRC calculated
            
            self.stdout.write(f"Sending raw frame: {frame.hex().upper()}")
            ser.write(frame)
            
            time.sleep(0.1)
            response = ser.read(100)
            
            if response:
                self.stdout.write(f"Raw response: {response.hex().upper()} ({len(response)} bytes)")
            else:
                self.stdout.write("No response received")
            
            ser.close()
            
        except Exception as e:
            self.stdout.write(f"Raw communication error: {e}")
        
        # Test 4: Coffee machine specific diagnostics
        self.stdout.write("\n=== Test 4: Coffee machine wake-up attempt ===")
        client = ModbusSerialClient(port=port, baudrate=9600, timeout=3)
        
        if client.connect():
            # Sometimes machines need a "wake-up" command
            wake_up_commands = [
                (512, 16),    # NO ACTION command to group 1
                (516, 0),     # Stop water command
                (517, 0),     # Stop MAT command
            ]
            
            for reg, value in wake_up_commands:
                try:
                    self.stdout.write(f"Sending wake-up command: reg={reg}, value={value}")
                    result = client.write_register(reg, value, slave=1)
                    if not result.isError():
                        self.stdout.write(f"Wake-up command successful")
                        time.sleep(1)
                        
                        # Try reading after wake-up
                        read_result = client.read_holding_registers(270, 1, slave=1)  # Number of groups
                        if not read_result.isError():
                            self.stdout.write(f"SUCCESS after wake-up! Register 270 = {read_result.registers[0]}")
                            break
                    time.sleep(0.5)
                except Exception as e:
                    self.stdout.write(f"Wake-up command error: {e}")
            
            client.close()