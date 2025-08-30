#!/usr/bin/env python3
"""
Debug connection issues
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coffee_machine_controller.settings')
django.setup()

from machine.coffee_machine import get_coffee_machine, CoffeeMachineException
from django.conf import settings

def test_connection():
    print("=" * 60)
    print("Testing Coffee Machine Connection")
    print("=" * 60)
    
    print(f"Settings:")
    print(f"  Port: {settings.COFFEE_MACHINE_PORT}")
    print(f"  Baudrate: {settings.COFFEE_MACHINE_BAUDRATE}")
    print()
    
    try:
        print("Getting coffee machine instance...")
        machine = get_coffee_machine()
        
        print(f"Machine details:")
        print(f"  Port: {machine.port}")
        print(f"  Baudrate: {machine.baudrate}")
        print(f"  Is Connected: {machine.is_connected}")
        print()
        
        print("Attempting to connect...")
        result = machine.connect()
        
        if result:
            print("✓ Successfully connected!")
            
            # Try to get info
            print("\nTrying to read machine info...")
            try:
                info = machine.get_machine_info()
                print(f"Machine Info: {info}")
            except Exception as e:
                print(f"Error getting info: {e}")
                
        else:
            print("✗ Failed to connect")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()