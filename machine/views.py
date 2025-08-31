from django.shortcuts import render

# Create your views here.
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import CoffeeMachine, CoffeeDelivery, MaintenanceLog
from .coffee_machine import get_coffee_machine, CoffeeMachineException
import logging

logger = logging.getLogger('machine')

def dashboard(request):
    """Main dashboard view"""
    context = {
        'title': 'Coffee Machine Controller',
        'machine_info': cache.get('machine_info', {}),
        'machine_status': cache.get('machine_status', {}),
    }
    return render(request, 'dashboard.html', context)

@api_view(['GET'])
def machine_info(request):
    """Get machine information"""
    try:
        machine = get_coffee_machine()
        
        # Return basic info if not connected
        if not machine.is_connected:
            return Response({
                'serial_number': 'Not Connected',
                'firmware_version': 'Not Connected',
                'number_of_groups': 'Not Connected',
                'is_blocked': 'Unknown',
                'machine_config': None,
                'connection_status': False,
                'port': machine.port,
                'baudrate': machine.baudrate,
                'last_updated': None
            })
        
        info = machine.get_machine_info()
        return Response(info)
    except Exception as e:
        logger.error(f"Error getting machine info: {e}")
        return Response({
            'serial_number': 'Error',
            'firmware_version': 'Error',
            'number_of_groups': 'Error',
            'is_blocked': 'Unknown',
            'machine_config': None,
            'connection_status': False,
            'port': getattr(settings, 'COFFEE_MACHINE_PORT', '/dev/ttyUSB1'),
            'baudrate': getattr(settings, 'COFFEE_MACHINE_BAUDRATE', 9600),
            'last_updated': None,
            'error': str(e)
        })

@api_view(['GET'])
def machine_status(request):
    """Get current machine status"""
    try:
        machine = get_coffee_machine()
        
        # Return empty status if not connected
        if not machine.is_connected:
            return Response({
                'groups': {
                    'group_1': {'is_busy': False, 'sensor_fault': False, 'purge_countdown': 0, 'current_action': 'Not Connected'},
                    'group_2': {'is_busy': False, 'sensor_fault': False, 'purge_countdown': 0, 'current_action': 'Not Connected'},
                    'group_3': {'is_busy': False, 'sensor_fault': False, 'purge_countdown': 0, 'current_action': 'Not Connected'}
                },
                'machine_blocked': False,
                'connection_status': False
            })
        
        machine_status = machine.get_all_groups_status()
        return Response(machine_status)
    except Exception as e:
        logger.error(f"Error getting machine status: {e}")
        return Response({
            'groups': {
                'group_1': {'is_busy': False, 'sensor_fault': False, 'purge_countdown': 0, 'current_action': 'Error'},
                'group_2': {'is_busy': False, 'sensor_fault': False, 'purge_countdown': 0, 'current_action': 'Error'},
                'group_3': {'is_busy': False, 'sensor_fault': False, 'purge_countdown': 0, 'current_action': 'Error'}
            },
            'machine_blocked': False,
            'connection_status': False,
            'error': str(e)
        })

@api_view(['POST'])
def connect_machine(request):
    """Connect to coffee machine"""
    try:
        # Get port and baudrate from request or use defaults
        data = request.data or {}
        port = data.get('port') or settings.COFFEE_MACHINE_PORT
        baudrate = data.get('baudrate') or settings.COFFEE_MACHINE_BAUDRATE
        
        logger.info(f"Attempting to connect to coffee machine on {port} at {baudrate} baud")
        
        # Get machine instance with specified port/baudrate
        machine = get_coffee_machine(port=port, baudrate=baudrate, force_new=True)
        connected = machine.connect()
        
        if connected:
            # Update database record
            try:
                machine_obj, created = CoffeeMachine.objects.get_or_create(
                    port=machine.port,
                    defaults={'baudrate': machine.baudrate}
                )
                
                info = machine.get_machine_info()
                if info:
                    machine_obj.serial_number = info.get('serial_number')
                    machine_obj.firmware_version = info.get('firmware_version')
                    machine_obj.number_of_groups = info.get('number_of_groups', 3)
                    machine_obj.is_connected = True
                    machine_obj.save()
                
                return Response({
                    'success': True,
                    'message': 'Successfully connected to coffee machine',
                    'machine_info': info
                })
            except Exception as db_error:
                logger.error(f"Database error after connection: {db_error}")
                # Connection succeeded but database update failed
                return Response({
                    'success': True,
                    'message': 'Connected to coffee machine (database update failed)',
                    'machine_info': {}
                })
        else:
            logger.warning(f"Failed to connect to coffee machine on {port}")
            return Response(
                {'success': False, 'message': f'Failed to connect to coffee machine on {port} at {baudrate} baud'}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    except Exception as e:
        logger.error(f"Connection error: {e}", exc_info=True)
        return Response(
            {'success': False, 'error': str(e), 'message': f'Connection error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def disconnect_machine(request):
    """Disconnect from coffee machine"""
    try:
        machine = get_coffee_machine()
        machine.disconnect()
        
        # Update database
        CoffeeMachine.objects.filter(port=machine.port).update(is_connected=False)
        
        return Response({
            'success': True,
            'message': 'Successfully disconnected from coffee machine'
        })
    except Exception as e:
        logger.error(f"Disconnection error: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@csrf_exempt
def deliver_coffee(request):
    """Deliver coffee"""
    try:
        # Parse JSON from request body directly - this is the most reliable way
        import json
        
        # Always try to parse JSON from body first
        if request.body:
            try:
                data = json.loads(request.body.decode('utf-8'))
                logger.info(f"Parsed JSON from body: {data}")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"Failed to parse JSON from body: {e}")
                # Fallback to request.data if JSON parsing fails
                data = getattr(request, 'data', {})
                logger.info(f"Fallback to request.data: {data}")
        else:
            # No body, try request.data
            data = getattr(request, 'data', {})
            logger.info(f"No body, using request.data: {data}")
            
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Request body (first 500 chars): {request.body[:500] if request.body else 'No body'}")
        
        group_number = data.get('group_number')
        coffee_type = data.get('coffee_type')
        
        logger.info(f"Deliver coffee request: group={group_number}, type={coffee_type}")
        
        if not group_number or not coffee_type:
            logger.warning(f"Missing parameters: group_number={group_number}, coffee_type={coffee_type}")
            return Response(
                {'success': False, 'message': 'group_number and coffee_type are required', 'error': 'Missing parameters'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            group_number = int(group_number)
        except (ValueError, TypeError):
            return Response(
                {'success': False, 'message': f'Invalid group_number: {group_number}', 'error': 'Invalid group_number'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not (1 <= group_number <= 3):
            return Response(
                {'success': False, 'message': f'group_number must be between 1 and 3, got {group_number}', 'error': 'Invalid group_number'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate coffee_type
        valid_types = ['single_short', 'single_medium', 'single_long', 'double_short', 'double_medium', 'double_long']
        if coffee_type not in valid_types:
            return Response(
                {'success': False, 'message': f'Invalid coffee_type: {coffee_type}. Must be one of {valid_types}', 'error': 'Invalid coffee_type'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create delivery record
        try:
            delivery = CoffeeDelivery.objects.create(
                coffee_type=coffee_type,
                group_number=group_number,
                status='pending'
            )
        except Exception as db_error:
            logger.error(f"Database error creating delivery: {db_error}")
            return Response(
                {'success': False, 'message': f'Database error: {str(db_error)}', 'error': 'Database error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            machine = get_coffee_machine()
            result = machine.deliver_coffee(int(group_number), coffee_type)
            
            if result['success']:
                delivery.status = 'in_progress'
                delivery.save()
                
                return Response({
                    'success': True,
                    'message': result['message'],
                    'delivery_id': delivery.id,
                    'result': result
                })
            else:
                delivery.status = 'failed'
                delivery.error_message = result['message']
                delivery.save()
                
                return Response(
                    {'success': False, 'message': result['message']}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            delivery.status = 'failed'
            delivery.error_message = str(e)
            delivery.save()
            raise
            
    except Exception as e:
        logger.error(f"Error delivering coffee: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def stop_delivery(request):
    """Stop ongoing coffee delivery"""
    try:
        data = request.data
        group_number = data.get('group_number')
        
        if not group_number:
            return Response(
                {'error': 'group_number is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        machine = get_coffee_machine()
        success = machine.stop_delivery(int(group_number))
        
        if success:
            # Update any in-progress deliveries
            CoffeeDelivery.objects.filter(
                group_number=group_number,
                status='in_progress'
            ).update(
                status='stopped',
                completed_at=timezone.now()
            )
            
            # Log maintenance action
            MaintenanceLog.objects.create(
                log_type='manual_stop',
                group_number=group_number,
                message=f'Manual stop command sent to group {group_number}'
            )
            
            return Response({
                'success': True,
                'message': f'Stop command sent to group {group_number}'
            })
        else:
            return Response(
                {'success': False, 'message': 'Failed to send stop command'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error stopping delivery: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def start_purge(request):
    """Start purge cycle"""
    try:
        data = request.data
        group_number = data.get('group_number')
        
        if not group_number:
            return Response(
                {'error': 'group_number is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        machine = get_coffee_machine()
        success = machine.start_purge(int(group_number))
        
        if success:
            # Log maintenance action
            MaintenanceLog.objects.create(
                log_type='purge',
                group_number=group_number,
                message=f'Purge cycle started for group {group_number}'
            )
            
            return Response({
                'success': True,
                'message': f'Purge cycle started for group {group_number}'
            })
        else:
            return Response(
                {'success': False, 'message': 'Failed to start purge cycle'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error starting purge: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def health_check(request):
    """Perform health check"""
    try:
        machine = get_coffee_machine()
        health = machine.health_check()
        
        # Log health check
        MaintenanceLog.objects.create(
            log_type='health_check',
            message=f'Health check performed - Status: {health["overall_status"]}',
            resolved=health['overall_status'] == 'healthy'
        )
        
        return Response(health)
        
    except Exception as e:
        logger.error(f"Error during health check: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def delivery_history(request):
    """Get delivery history"""
    try:
        limit = request.GET.get('limit', 50)
        deliveries = CoffeeDelivery.objects.all()[:int(limit)]
        
        data = []
        for delivery in deliveries:
            data.append({
                'id': delivery.id,
                'coffee_type': delivery.get_coffee_type_display(),
                'group_number': delivery.group_number,
                'status': delivery.get_status_display(),
                'started_at': delivery.started_at.isoformat(),
                'completed_at': delivery.completed_at.isoformat() if delivery.completed_at else None,
                'error_message': delivery.error_message
            })
        
        return Response({'deliveries': data})
        
    except Exception as e:
        logger.error(f"Error getting delivery history: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def maintenance_logs(request):
    """Get maintenance logs"""
    try:
        limit = request.GET.get('limit', 100)
        logs = MaintenanceLog.objects.all()[:int(limit)]
        
        data = []
        for log in logs:
            data.append({
                'id': log.id,
                'log_type': log.get_log_type_display(),
                'group_number': log.group_number,
                'message': log.message,
                'timestamp': log.timestamp.isoformat(),
                'resolved': log.resolved
            })
        
        return Response({'logs': data})
        
    except Exception as e:
        logger.error(f"Error getting maintenance logs: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )