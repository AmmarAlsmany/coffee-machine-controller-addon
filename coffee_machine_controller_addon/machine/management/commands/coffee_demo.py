import time
from django.core.management.base import BaseCommand
from machine.coffee_machine import get_coffee_machine

class Command(BaseCommand):
    help = 'Run a coffee delivery demonstration'
    
    def add_arguments(self, parser):
        parser.add_argument('--group', type=int, default=1, help='Group number (1-3)')
        parser.add_argument('--type', type=str, default='single_long', 
                          help='Coffee type (single_short, single_medium, single_long, etc.)')
    
    def handle(self, *args, **options):
        group = options['group']
        coffee_type = options['type']
        
        self.stdout.write(f"Starting coffee delivery demo...")
        self.stdout.write(f"Group: {group}, Type: {coffee_type}")
        
        machine = get_coffee_machine()
        
        try:
            # Connect
            self.stdout.write("Connecting to machine...")
            if not machine.connect():
                self.stdout.write(self.style.ERROR('Failed to connect!'))
                return
            
            self.stdout.write(self.style.SUCCESS('Connected!'))
            
            # Check if group is busy
            busy = machine.is_group_busy(group)
            if busy:
                self.stdout.write(self.style.WARNING(f'Group {group} is busy, stopping first...'))
                machine.stop_delivery(group)
                time.sleep(2)
            
            # Purge cycle
            self.stdout.write("Starting purge cycle...")
            if machine.start_purge(group):
                self.stdout.write("Purge started, waiting for completion...")
                if machine.wait_until_group_is_free(group, timeout=30):
                    self.stdout.write(self.style.SUCCESS('Purge completed!'))
                else:
                    self.stdout.write(self.style.WARNING('Purge timeout'))
            
            # Deliver coffee
            self.stdout.write(f"Delivering {coffee_type}...")
            result = machine.deliver_coffee(group, coffee_type)
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS(result['message']))
                
                # Monitor progress
                self.stdout.write("Monitoring delivery progress...")
                start_time = time.time()
                
                while time.time() - start_time < 60:  # Max 60 seconds
                    busy = machine.is_group_busy(group)
                    if not busy:
                        self.stdout.write(self.style.SUCCESS('Coffee delivery completed!'))
                        break
                    
                    self.stdout.write('.', ending='')
                    time.sleep(1)
                else:
                    self.stdout.write(self.style.WARNING('\nDelivery monitoring timeout'))
                    
            else:
                self.stdout.write(self.style.ERROR(f'Delivery failed: {result["message"]}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during demo: {e}'))
            
        finally:
            machine.disconnect()
            self.stdout.write("\nDemo completed.")