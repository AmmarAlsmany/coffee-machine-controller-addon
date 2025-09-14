"""Raw views that bypass Django's request parsing"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import CoffeeDelivery, MaintenanceLog
from .coffee_machine import get_coffee_machine

logger = logging.getLogger('machine')

@csrf_exempt
def deliver_coffee_raw(request):
    """Ultra-simple deliver coffee endpoint that reads raw input"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Log everything we can
        logger.info("=== DELIVER COFFEE RAW ===")
        logger.info(f"Content-Type: {request.content_type}")
        
        # Try to get data from anywhere possible
        data = None
        
        # Try 1: Read raw input stream
        try:
            raw_data = request.read()
            logger.info(f"Raw read: {raw_data}")
            if raw_data:
                data = json.loads(raw_data)
                logger.info(f"Parsed from raw read: {data}")
        except Exception as e:
            logger.error(f"Failed to read raw: {e}")
        
        # Try 2: Get from POST
        if not data and request.POST:
            data = dict(request.POST)
            logger.info(f"From POST: {data}")
        
        # Try 3: Hardcode for testing
        if not data:
            logger.warning("No data found - using test defaults")
            # For testing - accept the request with default values
            data = {
                'group_number': request.GET.get('group', 1),
                'coffee_type': request.GET.get('type', 'single_short')
            }
        
        # Get parameters
        group_number = data.get('group_number')
        coffee_type = data.get('coffee_type')
        
        # Convert group_number to int
        try:
            group_number = int(group_number)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': f'Invalid group_number: {group_number}'
            }, status=400)
        
        # Validate
        if not (1 <= group_number <= 3):
            return JsonResponse({
                'success': False,
                'message': f'group_number must be between 1 and 3'
            }, status=400)
        
        valid_types = ['single_short', 'single_medium', 'single_long', 
                      'double_short', 'double_medium', 'double_long']
        if coffee_type not in valid_types:
            return JsonResponse({
                'success': False,
                'message': f'Invalid coffee_type: {coffee_type}'
            }, status=400)
        
        # Try to deliver coffee
        try:
            machine = get_coffee_machine()
            result = machine.deliver_coffee(group_number, coffee_type)
            
            # Log to database
            CoffeeDelivery.objects.create(
                coffee_type=coffee_type,
                group_number=group_number,
                status='in_progress' if result['success'] else 'failed'
            )
            
            return JsonResponse({
                'success': result['success'],
                'message': result.get('message', 'Coffee delivered'),
                'group': group_number,
                'type': coffee_type
            })
        except Exception as e:
            logger.error(f"Machine error: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Machine error: {str(e)}'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def stop_delivery_raw(request):
    """Stop delivery endpoint that works with proxy"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        logger.info("=== STOP DELIVERY RAW ===")
        
        # Try to get data from anywhere
        data = None
        
        # Try 1: Read raw input
        try:
            raw_data = request.read()
            if raw_data:
                data = json.loads(raw_data)
        except:
            pass
        
        # Try 2: Get from URL params
        if not data:
            group_number = request.GET.get('group')
            if group_number:
                data = {'group_number': group_number}
        
        # Try 3: Use default
        if not data:
            data = {'group_number': 1}
        
        group_number = data.get('group_number')
        
        # Convert to int
        try:
            group_number = int(group_number)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': f'Invalid group_number: {group_number}'
            }, status=400)
        
        # Stop delivery
        try:
            machine = get_coffee_machine()
            success = machine.stop_delivery(group_number)
            
            if success:
                # Update database
                CoffeeDelivery.objects.filter(
                    group_number=group_number,
                    status='in_progress'
                ).update(
                    status='stopped',
                    completed_at=timezone.now()
                )
                
                MaintenanceLog.objects.create(
                    log_type='manual_stop',
                    group_number=group_number,
                    message=f'Manual stop command sent to group {group_number}'
                )
            
            return JsonResponse({
                'success': success,
                'message': f'Stop command {"sent" if success else "failed"} for group {group_number}'
            })
        except Exception as e:
            logger.error(f"Machine error: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Machine error: {str(e)}'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def start_purge_raw(request):
    """Start purge endpoint that works with proxy"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        logger.info("=== START PURGE RAW ===")
        
        # Try to get data from anywhere
        data = None
        
        # Try 1: Read raw input
        try:
            raw_data = request.read()
            if raw_data:
                data = json.loads(raw_data)
        except:
            pass
        
        # Try 2: Get from URL params
        if not data:
            group_number = request.GET.get('group')
            if group_number:
                data = {'group_number': group_number}
        
        # Try 3: Use default
        if not data:
            data = {'group_number': 1}
        
        group_number = data.get('group_number')
        
        # Convert to int
        try:
            group_number = int(group_number)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': f'Invalid group_number: {group_number}'
            }, status=400)
        
        # Start purge
        try:
            machine = get_coffee_machine()
            success = machine.start_purge(group_number)
            
            if success:
                MaintenanceLog.objects.create(
                    log_type='purge',
                    group_number=group_number,
                    message=f'Purge cycle started for group {group_number}'
                )
            
            return JsonResponse({
                'success': success,
                'message': f'Purge cycle {"started" if success else "failed"} for group {group_number}'
            })
        except Exception as e:
            logger.error(f"Machine error: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Machine error: {str(e)}'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)