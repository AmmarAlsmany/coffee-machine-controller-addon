from django.core.management.base import BaseCommand
from pymodbus.client import ModbusSerialClient

class Command(BaseCommand):
    help = 'Test different Modbus parameters'
    
    def handle(self, *args, **options):
        port = '/dev/ttyUSB0'
        
        # Different parameter combinations to try
        test_configs = [
            {'baudrate': 9600, 'parity': 'N', 'stopbits': 1, 'bytesize': 8},
            {'baudrate': 19200, 'parity': 'N', 'stopbits': 1, 'bytesize': 8},
            {'baudrate': 9600, 'parity': 'E', 'stopbits': 1, 'bytesize': 8},
            {'baudrate': 9600, 'parity': 'O', 'stopbits': 1, 'bytesize': 8},
            {'baudrate': 9600, 'parity': 'N', 'stopbits': 2, 'bytesize': 8},
        ]
        
        for config in test_configs:
            self.stdout.write(f"\nTesting: {config}")
            
            client = ModbusSerialClient(
                port=port,
                timeout=3,
                **config
            )
            
            try:
                if client.connect():
                    # Try reading a simple register
                    for node in [0, 1, 2, 255]:
                        try:
                            result = client.read_holding_registers(address=0, count=1, slave=node)
                            if not result.isError():
                                self.stdout.write(self.style.SUCCESS(
                                    f"  ✓ SUCCESS with node {node}: {result.registers[0]}"
                                ))
                                break
                        except:
                            pass
                else:
                    self.stdout.write("  ✗ Connection failed")
                    
            except Exception as e:
                self.stdout.write(f"  ✗ Error: {e}")
            finally:
                client.close()