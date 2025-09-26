#!/usr/bin/env python3
"""
Example script demonstrating how to use the ULS24Device class
to perform a sequence of operations.
"""
import time
import sys
from python_hid_wrapper import ULS24Device

def main():
    """Main function performing a sequence of operations"""
    # Create device instance
    device = ULS24Device()
    
    # Connect to device
    print("Connecting to device...")
    if not device.find_device():
        print("Error: Device not found.")
        return 1
    
    print("Device connected successfully!")
    
    try:
        # Set initial parameters
        print("\nSetting initial parameters...")
        device.sel_sensor(1)  # Select channel 1
        print("Selected channel 1")
        
        device.set_int_time(30)  # Set integration time to 30ms
        print("Set integration time to 30ms")
        
        device.set_gain_mode(1)  # Set low gain mode
        print("Set gain mode to low (1)")
        
        # Capture frame from channel 1
        print("\nCapturing frame from channel 1...")
        if device.capture_frame(1):
            print("Frame captured successfully!")
            print("\nFrame data:")
            device.print_data()
        else:
            print("Error capturing frame.")
        
        # Change channel and capture another frame
        print("\nSwitching to channel 2...")
        device.sel_sensor(2)
        print("Selected channel 2")
        
        # Change integration time
        print("Setting integration time to 50ms...")
        device.set_int_time(50)
        
        # Capture frame from channel 2
        print("\nCapturing frame from channel 2...")
        if device.capture_frame():
            print("Frame captured successfully!")
            print("\nFrame data:")
            device.print_data()
        else:
            print("Error capturing frame.")
        
        # Change gain mode
        print("\nSwitching to high gain mode...")
        device.set_gain_mode(0)
        print("Set gain mode to high (0)")
        
        # Capture another frame with high gain
        print("\nCapturing frame with high gain...")
        if device.capture_frame():
            print("Frame captured successfully!")
            print("\nFrame data:")
            device.print_data()
        else:
            print("Error capturing frame.")
        
    except Exception as e:
        print(f"Error during operation: {e}")
        return 1
    finally:
        # Clean up
        print("\nClosing device connection...")
        device.close()
        print("Device connection closed.")
    
    print("\nScript completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())