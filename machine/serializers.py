from rest_framework import serializers
from .models import CoffeeMachine, CoffeeDelivery, MaintenanceLog


class CoffeeMachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoffeeMachine
        fields = ['id', 'name', 'serial_number', 'firmware_version',
                  'port', 'baudrate', 'number_of_groups', 'is_connected',
                  'is_blocked', 'last_updated']


class CoffeeDeliverySerializer(serializers.ModelSerializer):
    coffee_type_display = serializers.CharField(
        source='get_coffee_type_display', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)

    class Meta:
        model = CoffeeDelivery
        fields = ['id', 'coffee_type', 'coffee_type_display', 'group_number',
                  'status', 'status_display', 'started_at', 'completed_at',
                  'error_message']


class MaintenanceLogSerializer(serializers.ModelSerializer):
    log_type_display = serializers.CharField(
        source='get_log_type_display', read_only=True)

    class Meta:
        model = MaintenanceLog
        fields = ['id', 'log_type', 'log_type_display', 'group_number',
                  'message', 'timestamp', 'resolved']
