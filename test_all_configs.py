#!/usr/bin/env python3
import serial
from pymodbus.client import ModbusSerialClient
import time

def test_config(port, baudrate, parity, stopbits, timeout=2):
    """Test a specific serial configuration"""
    print(f"Testing: {baudrate} bps, parity={parity}, stopbits={stopbits}")
    
    try:
        client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            bytesize=8,
            parity=parity,
            stopbits=stopbits,
            timeout=timeout
        )
        
        if client.connect():
            # Try reading register 270 (number of groups)
            result = client.read_holding_registers(270, 1, slave=1)
            if not result.isError():
                print(f"  ✓ SUCCESS! Register 270 = {result.registers[0]}")
                client.close()
                return True
            else:
                print(f"  ✗ Read failed: {result}")
        else:
            print(f"  ✗ Connection failed")
        
        client.close()
        return False
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

# Test all common configurations
port = '/dev/ttyUSB1'
configs = [
    # baudrate, parity, stopbits
    (9600, 'N', 1),    # Default from documentation
    (9600, 'E', 1),    # Even parity
    (9600, 'O', 1),    # Odd parity
    (9600, 'N', 2),    # 2 stop bits
    (19200, 'N', 1),   # Different baudrate
    (4800, 'N', 1),    # Lower baudrate
    (38400, 'N', 1),   # Higher baudrate
]

print("Testing all common serial configurations...")
for baudrate, parity, stopbits in configs:
    if test_config(port, baudrate, parity, stopbits):
        print(f"\n*** FOUND WORKING CONFIG: {baudrate} bps, {parity}, {stopbits} stop bits ***")
        break
    time.sleep(1)