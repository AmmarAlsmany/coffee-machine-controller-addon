from django.core.management.base import BaseCommand
from pymodbus.client import ModbusSerialClient
import time

class Command(BaseCommand):
    help = 'Scan Modbus registers to find correct addresses'
    
    def add_arguments(self, parser):
        parser.add_argument('--port', type=str, default='/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_BG01CG7P-if00-port0', help='Serial port')
        parser.add_argument('--baudrate', type=int, default=9600, help='Baudrate')
        parser.add_argument('--start', type=int, default=0, help='Start address')
        parser.add_argument('--end', type=int, default=100, help='End address')
        parser.add_argument('--node', type=int, default=1, help='Node address')
    
    def handle(self, *args, **options):
        port = options['port']
        baudrate = options['baudrate']
        start_addr = options['start']
        end_addr = options['end']
        node_addr = options['node']
        
        self.stdout.write(f"Scanning registers {start_addr}-{end_addr} on node {node_addr}")
        self.stdout.write(f"Port: {port}, Baudrate: {baudrate}")
        
        client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=2  # Increased timeout
        )
        
        try:
            if not client.connect():
                self.stdout.write(self.style.ERROR('Failed to connect'))
                return
            
            self.stdout.write(self.style.SUCCESS('Connected! Scanning registers...'))
            
            successful_reads = []
            
            for addr in range(start_addr, end_addr + 1):
                try:
                    # Try reading holding registers
                    result = client.read_holding_registers(address=addr, count=1, slave=node_addr)
                    if not result.isError():
                        value = result.registers[0]
                        successful_reads.append((addr, value, 'holding'))
                        self.stdout.write(f"✓ Holding Register {addr}: {value} (0x{value:04X})")
                    else:
                        # Try reading input registers
                        result = client.read_input_registers(address=addr, count=1, slave=node_addr)
                        if not result.isError():
                            value = result.registers[0]
                            successful_reads.append((addr, value, 'input'))
                            self.stdout.write(f"✓ Input Register {addr}: {value} (0x{value:04X})")
                except Exception as e:
                    pass  # Skip errors silently
                
                time.sleep(0.1)  # Small delay between requests
            
            self.stdout.write(f"\n=== Summary ===")
            self.stdout.write(f"Found {len(successful_reads)} readable registers:")
            
            for addr, value, reg_type in successful_reads:
                self.stdout.write(f"  {reg_type.capitalize()} Register {addr}: {value} (0x{value:04X})")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            
        finally:
            client.close()