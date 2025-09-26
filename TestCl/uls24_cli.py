#!/usr/bin/env python3
"""
Command line interface for ULS24 device using Python.
This script provides a CLI interface similar to the C++ program.
"""
import argparse
import sys
import time
from python_hid_wrapper import ULS24Device

def main():
    """Main function handling command line arguments"""
    parser = argparse.ArgumentParser(description='ULS24 Device Control Script')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    parser.add_argument('--selchan', type=int, choices=range(1, 5), 
                        help='Select sensor channel (1-4)')
    parser.add_argument('--get', action='store_true', 
                        help='Capture frame from current or specified channel')
    parser.add_argument('--setinttime', type=int, 
                        help='Set integration time in milliseconds (1-66000)')
    parser.add_argument('--setgain', type=int, choices=[0, 1], 
                        help='Set gain mode (0-high, 1-low)')
    parser.add_argument('--reset', action='store_true', 
                        help='Reset and reconnect to the device')
    parser.add_argument('--channel', type=int, choices=range(1, 5), 
                        help='Channel to use with --get (1-4)')
    parser.add_argument('--output', type=str, 
                        help='Output file to save frame data')
    
    args = parser.parse_args()
    
    # Create device instance
    device = ULS24Device()
    
    # Connect to device
    print("Connecting to device...")
    if not device.find_device():
        print("Error: Device not found.")
        return 1
    
    print("Device connected successfully!")
    
    try:
        if args.interactive:
            # Interactive mode - similar to the C++ application
            print("\nallowable commands are: selchan, get, setinttime, setgain, reset, exit...")
            
            while True:
                command = input("> ")
                
                if command == "selchan":
                    channel = int(input("chan: "))
                    device.sel_sensor(channel)
                
                elif command == "get":
                    device.capture_frame()
                    device.print_data()
                
                elif command == "setinttime":
                    int_time = int(input("int time: "))
                    device.set_int_time(int_time)
                
                elif command == "setgain":
                    gain = int(input("gain (0-high, 1-low): "))
                    device.set_gain_mode(gain)
                
                elif command == "reset":
                    found = device.find_device()
                    if found:
                        print("Device found")
                    else:
                        print("Device not found")
                
                elif command == "exit":
                    break
                
                else:
                    print(f"Unknown command: {command}")
        else:
            # Process command line arguments
            if args.reset:
                print("Resetting device connection...")
                if device.find_device():
                    print("Device reconnected successfully!")
                else:
                    print("Error reconnecting to device.")
                    return 1
            
            if args.selchan is not None:
                print(f"Selecting channel {args.selchan}...")
                device.sel_sensor(args.selchan)
            
            if args.setinttime is not None:
                print(f"Setting integration time to {args.setinttime}ms...")
                device.set_int_time(args.setinttime)
            
            if args.setgain is not None:
                gain_str = "high" if args.setgain == 0 else "low"
                print(f"Setting gain mode to {gain_str} ({args.setgain})...")
                device.set_gain_mode(args.setgain)
            
            if args.get:
                channel = args.channel if args.channel is not None else device.current_channel
                print(f"Capturing frame from channel {channel}...")
                if device.capture_frame(channel):
                    print("Frame captured successfully!")
                    print("\nFrame data:")
                    device.print_data()
                    
                    # Save frame data to file if requested
                    if args.output:
                        try:
                            with open(args.output, 'w') as f:
                                dim = 24 if device.frame_size else 12
                                for i in range(dim):
                                    row = " ".join(f"{device.frame_data[i][j]}" for j in range(dim))
                                    f.write(row + "\n")
                            print(f"Frame data saved to {args.output}")
                        except IOError as e:
                            print(f"Error saving frame data to file: {e}")
                else:
                    print("Error capturing frame.")
    
    except Exception as e:
        print(f"Error during operation: {e}")
        return 1
    finally:
        # Clean up
        print("Closing device connection...")
        device.close()
        print("Device connection closed.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())