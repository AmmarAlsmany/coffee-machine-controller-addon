from django.core.management.base import BaseCommand
from django.conf import settings
from pymodbus.client import ModbusSerialClient
import time

class Command(BaseCommand):
    help = 'Test direct connection to coffee machine'

    def handle(self, *args, **options):
        port = '/dev/ttyUSB0'
        baudrate = 9600
        
        self.stdout.write(f"Testing connection to coffee machine...")
        self.stdout.write(f"Port: {port}")
        self.stdout.write(f"Baudrate: {baudrate}")
        self.stdout.write("-" * 50)
        
        try:
            # Create client with exact settings
            client = ModbusSerialClient(
                port=port,
                baudrate=baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=3,
                strict=False
            )
            
            self.stdout.write("Attempting to connect...")
            connected = client.connect()
            
            if connected:
                self.stdout.write(self.style.SUCCESS("✓ Connection successful!"))
                
                # Test reading serial number (registers 0-9)
                self.stdout.write("\nTesting Modbus communication...")
                
                for slave_id in [1, 0]:  # Try both slave addresses
                    self.stdout.write(f"\nTrying slave address {slave_id}...")
                    
                    try:
                        # Try to read serial number
                        result = client.read_holding_registers(
                            address=0,
                            count=10,
                            slave=slave_id
                        )
                        
                        if not result.isError():
                            self.stdout.write(self.style.SUCCESS(f"✓ Successfully read from slave {slave_id}"))
                            self.stdout.write(f"Registers: {result.registers}")
                            
                            # Try to read firmware version
                            fw_result = client.read_holding_registers(
                                address=11,
                                count=1,
                                slave=slave_id
                            )
                            
                            if not fw_result.isError():
                                fw_bytes = fw_result.registers[0].to_bytes(2, 'big')
                                major, minor = fw_bytes[0], fw_bytes[1]
                                self.stdout.write(f"Firmware: {major}.{minor}")
                            
                            # Try to read number of groups
                            groups_result = client.read_holding_registers(
                                address=270,  # NUMBER_OF_GROUPS register
                                count=1,
                                slave=slave_id
                            )
                            
                            if not groups_result.isError():
                                self.stdout.write(f"Number of groups: {groups_result.registers[0]}")
                            
                            break
                        else:
                            self.stdout.write(f"Error reading from slave {slave_id}: {result}")
                            
                    except Exception as e:
                        self.stdout.write(f"Exception with slave {slave_id}: {e}")
                
                client.close()
                
            else:
                self.stdout.write(self.style.ERROR("✗ Failed to connect"))
                self.stdout.write("\nPossible issues:")
                self.stdout.write("1. Coffee machine is not powered on")
                self.stdout.write("2. USB cable is not properly connected")
                self.stdout.write("3. Wrong port or baudrate")
                self.stdout.write("4. Permission issues (user not in dialout group)")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            self.stdout.write("\nMake sure:")
            self.stdout.write("1. pymodbus is installed: pip install pymodbus")
            self.stdout.write("2. User has permission to access serial ports")
            self.stdout.write("3. Coffee machine is connected and powered on")