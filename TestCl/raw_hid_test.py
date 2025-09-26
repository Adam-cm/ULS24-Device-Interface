#!/usr/bin/env python3
"""
Basic HID communication test - tries different approaches to communicate with the ULS24 device
"""
import sys
import time
import hid  # pip install hidapi

# Device information
VENDOR_ID = 0x0483
PRODUCT_ID = 0x5750

def print_device_info(device_path=None):
    """Print details about the device"""
    print("\n=== Device Information ===")
    try:
        # Open device
        dev = hid.device()
        if device_path:
            dev.open_path(device_path)
        else:
            dev.open(VENDOR_ID, PRODUCT_ID)
        
        # Get device information
        try:
            manufacturer = dev.get_manufacturer_string()
            product = dev.get_product_string()
            serial = dev.get_serial_number_string()
            
            print(f"Manufacturer: {manufacturer}")
            print(f"Product: {product}")
            print(f"Serial Number: {serial}")
        except Exception as e:
            print(f"Error getting device strings: {e}")
        
        dev.close()
    except Exception as e:
        print(f"Error opening device: {e}")

def test_raw_write():
    """Test raw write to the device without expecting a response"""
    print("\n=== Raw Write Test ===")
    try:
        # Open device
        dev = hid.device()
        dev.open(VENDOR_ID, PRODUCT_ID)
        
        # Create a simple report - just select channel 1
        report = bytearray(65)  # 1 byte report ID + 64 bytes data
        report[0] = 0x00  # Report ID 0
        report[1] = 0x03  # Command code for SelSensor
        report[2] = 0x01  # Channel 1
        
        print(f"Sending command: {' '.join(f'{b:02x}' for b in report[:10])}...")
        
        # Write report
        dev.write(report)
        print("Write completed")
        
        # Wait a bit
        time.sleep(0.5)
        
        # Try to read any response
        print("Waiting for response (5 seconds)...")
        start_time = time.time()
        received = False
        
        while time.time() - start_time < 5:
            # Try to read with a short timeout
            data = dev.read(65, timeout_ms=100)
            
            if data:
                print(f"Received data: {' '.join(f'{b:02x}' for b in data[:10])}")
                received = True
                break
            
            # Small delay
            time.sleep(0.1)
        
        if not received:
            print("No response received")
        
        dev.close()
    except Exception as e:
        print(f"Error in raw write test: {e}")

def test_feature_report():
    """Test using feature reports instead of input/output reports"""
    print("\n=== Feature Report Test ===")
    try:
        # Open device
        dev = hid.device()
        dev.open(VENDOR_ID, PRODUCT_ID)
        
        # Try to send a feature report
        print("Sending feature report...")
        
        # Create feature report - select channel 1
        report = bytearray(65)
        report[0] = 0x00  # Report ID 0
        report[1] = 0x03  # Command code for SelSensor
        report[2] = 0x01  # Channel 1
        
        # Send feature report
        try:
            result = dev.send_feature_report(report)
            print(f"Feature report sent: {result} bytes")
        except Exception as e:
            print(f"Error sending feature report: {e}")
        
        # Try to get a feature report
        try:
            print("Getting feature report...")
            get_report = bytearray(65)
            get_report[0] = 0x00  # Report ID 0
            
            result = dev.get_feature_report(get_report, 65)
            print(f"Feature report received: {' '.join(f'{b:02x}' for b in result[:10])}")
        except Exception as e:
            print(f"Error getting feature report: {e}")
        
        dev.close()
    except Exception as e:
        print(f"Error in feature report test: {e}")

def test_non_blocking():
    """Test non-blocking mode for reads"""
    print("\n=== Non-Blocking Test ===")
    try:
        # Open device
        dev = hid.device()
        dev.open(VENDOR_ID, PRODUCT_ID)
        
        # Set non-blocking mode
        dev.set_nonblocking(1)
        
        # Send command
        report = bytearray(65)
        report[0] = 0x00  # Report ID 0
        report[1] = 0x03  # Command code for SelSensor
        report[2] = 0x01  # Channel 1
        
        print("Sending command in non-blocking mode...")
        dev.write(report)
        
        # Try to read responses
        print("Reading responses for 5 seconds...")
        start_time = time.time()
        received = False
        
        while time.time() - start_time < 5:
            # Try to read
            data = dev.read(65)
            
            if data:
                print(f"Received data: {' '.join(f'{b:02x}' for b in data[:10])}")
                received = True
            
            # Small delay
            time.sleep(0.1)
        
        if not received:
            print("No response received in non-blocking mode")
        
        dev.close()
    except Exception as e:
        print(f"Error in non-blocking test: {e}")

def test_byte_by_byte():
    """Test writing data byte by byte"""
    print("\n=== Byte-by-Byte Test ===")
    try:
        # Open device
        dev = hid.device()
        dev.open(VENDOR_ID, PRODUCT_ID)
        
        # Command sequence
        cmd = [0x00, 0x03, 0x01]  # Report ID, SelSensor command, Channel 1
        
        print("Sending command byte by byte...")
        
        # Write full report first (as reference)
        report = bytearray(65)
        for i in range(len(cmd)):
            report[i] = cmd[i]
        
        dev.write(report)
        print("Full report sent")
        
        # Wait and try to read
        time.sleep(0.5)
        data = dev.read(65, timeout_ms=1000)
        if data:
            print(f"Response: {' '.join(f'{b:02x}' for b in data[:10])}")
        else:
            print("No response")
        
        dev.close()
    except Exception as e:
        print(f"Error in byte-by-byte test: {e}")

def test_different_command_formats():
    """Test different command formats"""
    print("\n=== Different Command Formats Test ===")
    
    # Different command formats to try
    commands = [
        # Format 1: Standard approach with cmd in position 1
        [0x00, 0x03, 0x01, 0x00],
        
        # Format 2: Command in position 0, no report ID
        [0x03, 0x01, 0x00, 0x00],
        
        # Format 3: Different command code
        [0x00, 0x30, 0x01, 0x00],
        
        # Format 4: Different command structure
        [0x00, 0x01, 0x03, 0x01]
    ]
    
    for i, cmd in enumerate(commands):
        try:
            print(f"\nTrying command format {i+1}: {' '.join(f'{b:02x}' for b in cmd)}")
            
            # Open device
            dev = hid.device()
            dev.open(VENDOR_ID, PRODUCT_ID)
            
            # Create report
            report = bytearray(65)
            for j in range(len(cmd)):
                report[j] = cmd[j]
            
            # Send command
            dev.write(report)
            print("Command sent")
            
            # Try to read response
            print("Waiting for response...")
            data = dev.read(65, timeout_ms=1000)
            
            if data:
                print(f"Received response: {' '.join(f'{b:02x}' for b in data[:10])}")
            else:
                print("No response")
            
            dev.close()
            time.sleep(1)  # Wait between tests
        except Exception as e:
            print(f"Error in command format {i+1} test: {e}")

def main():
    """Main function"""
    print("=== ULS24 Raw Communication Test ===")
    
    # List available devices
    print("\nAvailable HID devices:")
    devices = hid.enumerate()
    
    uls_devices = []
    for dev in devices:
        print(f"VID: {dev['vendor_id']:04x}, PID: {dev['product_id']:04x}, Path: {dev['path']}")
        
        if dev['vendor_id'] == VENDOR_ID and dev['product_id'] == PRODUCT_ID:
            uls_devices.append(dev)
            print("  --> ULS24 device found!")
    
    if not uls_devices:
        print("No ULS24 devices found!")
        return 1
    
    # Get device information
    print_device_info()
    
    # Run tests
    test_raw_write()
    test_feature_report()
    test_non_blocking()
    test_byte_by_byte()
    test_different_command_formats()
    
    print("\n=== Tests Complete ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())