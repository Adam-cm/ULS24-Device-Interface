#!/usr/bin/env python3
"""
Simple test script for ULS24 device - provides basic functionality tests
"""
import sys
import time
from python_hid_wrapper import ULS24Device

def main():
    """Test basic device functionality step by step"""
    # Create device with debug enabled
    device = ULS24Device(debug=True)
    
    print("=== ULS24 Device Basic Test ===")
    
    # Step 1: Connect to device
    print("\nStep 1: Connecting to device...")
    if not device.find_device():
        print("ERROR: Device not found")
        return 1
    
    print("SUCCESS: Device connected")
    
    try:
        # Step 2: Test simple commands with acknowledgment
        print("\nStep 2: Testing simple commands...")
        
        # Try selecting channel
        print("  Testing channel selection...")
        if device.sel_sensor(1):
            print("  SUCCESS: Channel selection command sent")
        else:
            print("  ERROR: Failed to select channel")
        
        # Add a small delay between commands
        time.sleep(0.5)
        
        # Try setting integration time
        print("  Testing integration time setting...")
        if device.set_int_time(30):
            print("  SUCCESS: Integration time command sent")
        else:
            print("  ERROR: Failed to set integration time")
        
        # Add a small delay between commands
        time.sleep(0.5)
        
        # Try setting gain mode
        print("  Testing gain mode setting...")
        if device.set_gain_mode(1):
            print("  SUCCESS: Gain mode command sent")
        else:
            print("  ERROR: Failed to set gain mode")
        
        # Add a small delay before capture
        time.sleep(1)
        
        # Step 3: Attempt frame capture
        print("\nStep 3: Testing frame capture (this may take some time)...")
        if device.capture_frame(1):
            print("SUCCESS: Frame captured")
            
            # Display the first few rows only
            print("\nFirst 3 rows of frame data:")
            dim = 24 if device.frame_size else 12
            for i in range(min(3, dim)):
                row = " ".join(f"{device.frame_data[i][j]}" for j in range(dim))
                print(row)
        else:
            print("ERROR: Failed to capture frame")
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nERROR: An exception occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Step 4: Clean up
        print("\nStep 4: Closing device connection...")
        device.close()
        print("Device closed")
    
    print("\n=== Test Complete ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())