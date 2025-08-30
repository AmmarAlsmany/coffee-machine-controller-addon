#!/usr/bin/env python3
"""
Check available serial ports on Raspberry Pi and test connection
"""
import os
import sys
import glob
import serial
from pymodbus.client import ModbusSerialClient

def list_serial_ports():
    """List all available serial ports on Linux"""
    ports = []
    
    # Check for USB serial devices
    usb_ports = glob.glob('/dev/ttyUSB*')
    ports.extend(usb_ports)
    
    # Check for ACM devices (Arduino, etc)
    acm_ports = glob.glob('/dev/ttyACM*')
    ports.extend(acm_ports)
    
    # Check for AMA devices (Raspberry Pi GPIO)
    ama_ports = glob.glob('/dev/ttyAMA*')
    ports.extend(ama_ports)
    
    # Check for standard serial ports
    serial_ports = glob.glob('/dev/ttyS*')
    ports.extend(serial_ports)
    
    return sorted(ports)

def test_modbus_connection(port, baudrate=9600):
    """Test if we can connect to a Modbus device on the given port"""
    print(f"\nTesting port {port} at {baudrate} baud...")
    
    try:
        client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=2
        )
        
        if client.connect():
            print(f"✓ Successfully connected to {port}")
            
            # Try to read a register to verify it's a Modbus device
            try:
                result = client.read_holding_registers(address=0, count=1, slave=1)
                if not result.isError():
                    print(f"✓ Modbus communication successful on {port}")
                    client.close()
                    return True
                else:
                    print(f"  Modbus error: {result}")
            except Exception as e:
                print(f"  Modbus read error: {e}")
            
            client.close()
        else:
            print(f"✗ Could not connect to {port}")
            
    except Exception as e:
        print(f"✗ Error on {port}: {e}")
    
    return False

def main():
    print("=" * 60)
    print("Serial Port Scanner for Coffee Machine")
    print("=" * 60)
    
    # List available ports
    ports = list_serial_ports()
    
    if not ports:
        print("\nNo serial ports found!")
        print("\nMake sure:")
        print("1. The coffee machine is connected via USB")
        print("2. The USB cable is working (data cable, not just power)")
        print("3. You have permission to access serial ports (add user to dialout group)")
        return
    
    print(f"\nFound {len(ports)} serial port(s):")
    for port in ports:
        # Check if port exists and is accessible
        if os.path.exists(port):
            try:
                # Try to check permissions
                if os.access(port, os.R_OK | os.W_OK):
                    print(f"  ✓ {port} - accessible")
                else:
                    print(f"  ✗ {port} - exists but no read/write permission")
            except:
                print(f"  ? {port} - exists but cannot check permissions")
        else:
            print(f"  ✗ {port} - does not exist")
    
    # Test each USB port for Modbus connection
    usb_ports = [p for p in ports if 'ttyUSB' in p and os.path.exists(p)]
    
    if usb_ports:
        print("\n" + "=" * 60)
        print("Testing USB ports for Modbus/Coffee Machine...")
        print("=" * 60)
        
        found_port = None
        for port in usb_ports:
            if test_modbus_connection(port, 9600):
                found_port = port
                break
        
        if found_port:
            print("\n" + "=" * 60)
            print(f"SUCCESS! Coffee machine found on: {found_port}")
            print(f"Update your settings.py with: COFFEE_MACHINE_PORT = '{found_port}'")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("No Modbus device found on any USB port.")
            print("\nTroubleshooting steps:")
            print("1. Check if the coffee machine is powered on")
            print("2. Verify the USB cable is properly connected")
            print("3. Ensure you're using the correct baudrate (9600)")
            print("4. Check coffee machine's RS232/USB settings")
            print("=" * 60)
    else:
        print("\nNo USB serial ports found. Is the coffee machine connected?")

if __name__ == "__main__":
    main()