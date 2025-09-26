#!/usr/bin/env python3
"""
USB Sniffer tool for Linux - Monitors USB traffic for a specific device
Requires: sudo apt-get install usbutils python3-usb
"""
import os
import sys
import time
import re
import subprocess
import signal
import threading

# Device info
VENDOR_ID = 0x0483
PRODUCT_ID = 0x5750

def get_device_bus_address():
    """Get the bus and device address for the target device"""
    cmd = "lsusb"
    try:
        output = subprocess.check_output(cmd, shell=True).decode('utf-8')
        for line in output.splitlines():
            if f"{VENDOR_ID:04x}:{PRODUCT_ID:04x}" in line.lower():
                match = re.search(r'Bus (\d+) Device (\d+)', line)
                if match:
                    return int(match.group(1)), int(match.group(2))
    except Exception as e:
        print(f"Error running lsusb: {e}")
    
    return None, None

def setup_usbmon():
    """Set up usbmon if it's not already loaded"""
    try:
        # Check if usbmon is loaded
        lsmod_output = subprocess.check_output("lsmod | grep usbmon", shell=True).decode('utf-8')
        print("usbmon kernel module is already loaded")
    except subprocess.CalledProcessError:
        # Load usbmon module
        print("Loading usbmon kernel module...")
        try:
            subprocess.check_call("sudo modprobe usbmon", shell=True)
            print("usbmon loaded successfully")
        except subprocess.CalledProcessError as e:
            print(f"Failed to load usbmon: {e}")
            return False
    
    # Check if usbmon device nodes exist
    if not os.path.exists("/dev/usbmon0"):
        print("Creating usbmon device nodes...")
        try:
            subprocess.check_call("sudo mkdir -p /dev/usb", shell=True)
            subprocess.check_call("sudo chmod 0777 /dev/usb", shell=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to set up USB directories: {e}")
            return False
    
    return True

def monitor_usb_traffic(bus_num, device_num):
    """Monitor USB traffic for the specified device using usbmon"""
    print(f"Monitoring USB traffic for device on bus {bus_num}, address {device_num}")
    
    # Use tcpdump to watch usbmon
    cmd = f"sudo tcpdump -i usbmon{bus_num} -XX -w /tmp/usb_capture.pcap"
    
    try:
        # Start tcpdump in the background
        tcpdump_proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("USB traffic capture started. Press Ctrl+C to stop and analyze.")
        print("Now run your ULS24 device commands in another terminal...")
        
        # Wait for Ctrl+C
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping USB capture...")
            
        # Kill tcpdump
        tcpdump_proc.terminate()
        tcpdump_proc.wait()
        
        # Analyze the capture
        print("\nAnalyzing captured USB traffic...")
        analysis_cmd = f"tcpdump -r /tmp/usb_capture.pcap -XX"
        
        try:
            # Run the analysis and capture output
            analysis = subprocess.check_output(analysis_cmd, shell=True).decode('utf-8')
            
            # Filter for relevant packets (those involving our device)
            device_filter = f" {device_num}[:.] "
            relevant_packets = []
            current_packet = []
            
            for line in analysis.splitlines():
                if re.search(r'^\d\d:', line):  # Start of a new packet
                    if current_packet and any(device_filter in p for p in current_packet):
                        relevant_packets.append(current_packet)
                    current_packet = [line]
                else:
                    current_packet.append(line)
            
            # Add the last packet if it's relevant
            if current_packet and any(device_filter in p for p in current_packet):
                relevant_packets.append(current_packet)
            
            # Write relevant packets to a file
            output_file = "uls24_usb_traffic.txt"
            with open(output_file, "w") as f:
                f.write(f"USB Traffic for ULS24 Device (VID:{VENDOR_ID:04x} PID:{PRODUCT_ID:04x})\n")
                f.write(f"Bus {bus_num}, Device {device_num}\n\n")
                
                for i, packet in enumerate(relevant_packets):
                    f.write(f"Packet {i+1}:\n")
                    for line in packet:
                        f.write(line + "\n")
                    f.write("\n")
            
            print(f"Analysis written to {output_file}")
            
            # Also print summary
            print(f"\nFound {len(relevant_packets)} packets for device {device_num}")
            
        except subprocess.CalledProcessError as e:
            print(f"Error analyzing capture: {e}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error monitoring USB traffic: {e}")

def main():
    """Main function"""
    print("ULS24 USB Traffic Monitor")
    
    # Check if running as root
    if os.geteuid() != 0:
        print("This script must be run as root (sudo).")
        return 1
    
    # Set up usbmon
    if not setup_usbmon():
        return 1
    
    # Get device bus and address
    bus_num, device_num = get_device_bus_address()
    if not bus_num or not device_num:
        print(f"Could not find ULS24 device with VID:{VENDOR_ID:04x} PID:{PRODUCT_ID:04x}")
        return 1
    
    # Monitor traffic
    monitor_usb_traffic(bus_num, device_num)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())