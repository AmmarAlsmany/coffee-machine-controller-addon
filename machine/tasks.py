from celery import shared_task
from .coffee_machine import get_coffee_machine
from .models import CoffeeDelivery, MaintenanceLog
from django.utils import timezone
import logging

logger = logging.getLogger('machine')

@shared_task
def deliver_coffee_async(delivery_id):
    """Async coffee delivery task"""
    try:
        delivery = CoffeeDelivery.objects.get(id=delivery_id)
        machine = get_coffee_machine()
        
        if not machine.ensure_connection():
            delivery.status = 'failed'
            delivery.error_message = 'Failed to connect to machine'
            delivery.save()
            return False
        
        # Start delivery
        result = machine.deliver_coffee(delivery.group_number, delivery.coffee_type)
        
        if result['success']:
            delivery.status = 'in_progress'
            delivery.save()
            
            # Wait for completion
            if machine.wait_until_group_is_free(delivery.group_number, timeout=120):
                delivery.status = 'completed'
                delivery.completed_at = timezone.now()
            else:
                delivery.status = 'failed'
                delivery.error_message = 'Delivery timeout'
                
        else:
            delivery.status = 'failed'
            delivery.error_message = result['message']
            
        delivery.save()
        return delivery.status == 'completed'
        
    except Exception as e:
        logger.error(f"Error in async coffee delivery: {e}")
        try:
            delivery = CoffeeDelivery.objects.get(id=delivery_id)
            delivery.status = 'failed'
            delivery.error_message = str(e)
            delivery.save()
        except:
            pass
        return False

@shared_task
def health_check_task():
    """Periodic health check task"""
    try:
        machine = get_coffee_machine()
        health = machine.health_check()
        
        MaintenanceLog.objects.create(
            log_type='health_check',
            message=f'Scheduled health check - Status: {health["overall_status"]}',
            resolved=health['overall_status'] == 'healthy'
        )
        
        return health['overall_status'] == 'healthy'
        
    except Exception as e:
        logger.error(f"Error in health check task: {e}")
        MaintenanceLog.objects.create(
            log_type='health_check',
            message=f'Health check failed: {str(e)}',
            resolved=False
        )
        return False