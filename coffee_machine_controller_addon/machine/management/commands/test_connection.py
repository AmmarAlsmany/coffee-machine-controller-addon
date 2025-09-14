import os
import django
from django.core.management.base import BaseCommand
from machine.coffee_machine import LaSpazialeCoffeeMachine

class Command(BaseCommand):
    help = 'Test coffee machine connection'
    
    def add_arguments(self, parser):
        parser.add_argument('--port', type=str, help='Serial port (e.g., COM4 or /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_BG01CG7P-if00-port0)')
        parser.add_argument('--baudrate', type=int, default=9600, help='Baudrate (default: 9600)')
    
    def handle(self, *args, **options):
        port = options.get('port') or 'COM4'
        baudrate = options.get('baudrate') or 9600
        
        self.stdout.write(f"Testing connection to {port} at {baudrate} bps...")
        
        machine = LaSpazialeCoffeeMachine(port=port, baudrate=baudrate)
        
        try:
            if machine.connect():
                self.stdout.write(self.style.SUCCESS('Connection successful!'))
                
                # Get machine info
                info = machine.get_machine_info()
                self.stdout.write(f"Serial Number: {info.get('serial_number', 'N/A')}")
                self.stdout.write(f"Firmware Version: {info.get('firmware_version', 'N/A')}")
                self.stdout.write(f"Number of Groups: {info.get('number_of_groups', 'N/A')}")
                
                # Test group status
                status = machine.get_all_groups_status()
                self.stdout.write("\nGroup Status:")
                for group_key, group_data in status['groups'].items():
                    group_num = group_key.split('_')[1]
                    busy = group_data['is_busy']
                    fault = group_data['sensor_fault']
                    self.stdout.write(f"  Group {group_num}: {'Busy' if busy else 'Ready'}" + 
                                    (f" (Sensor Fault)" if fault else ""))
                
            else:
                self.stdout.write(self.style.ERROR('Connection failed!'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
        
        finally:
            machine.disconnect()
            self.stdout.write("Connection closed.")
