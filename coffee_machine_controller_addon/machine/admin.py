from django.contrib import admin
from .models import CoffeeMachine, CoffeeDelivery, MaintenanceLog

@admin.register(CoffeeMachine)
class CoffeeMachineAdmin(admin.ModelAdmin):
    list_display = ['name', 'serial_number', 'firmware_version', 'port', 'is_connected', 'last_updated']
    list_filter = ['is_connected', 'is_blocked']
    readonly_fields = ['serial_number', 'firmware_version', 'last_updated']

@admin.register(CoffeeDelivery)
class CoffeeDeliveryAdmin(admin.ModelAdmin):
    list_display = ['coffee_type', 'group_number', 'status', 'started_at', 'completed_at']
    list_filter = ['status', 'coffee_type', 'group_number']
    readonly_fields = ['started_at']

@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ['log_type', 'group_number', 'message', 'timestamp', 'resolved']
    list_filter = ['log_type', 'resolved', 'group_number']
    readonly_fields = ['timestamp']