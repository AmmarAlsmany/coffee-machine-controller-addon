from django.apps import AppConfig
import logging

logger = logging.getLogger('machine')

class MachineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'machine'
    
    def ready(self):
        # Initialize coffee machine connection on app startup
        try:
            from .coffee_machine import get_coffee_machine
            machine = get_coffee_machine()
            logger.info("Coffee machine controller initialized")
        except Exception as e:
            logger.error(f"Failed to initialize coffee machine controller: {e}")