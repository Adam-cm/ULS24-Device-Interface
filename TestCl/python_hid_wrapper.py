#!/usr/bin/env python3
"""
Python wrapper for HID device communication, replicating the functionality in TestCl.cpp
"""
import sys
import time
import hid  # pip install hidapi
import traceback

# Debug flag - set to True for verbose output
DEBUG = True

class ULS24Device:
    """Class to interface with ULS24 device using HID communication"""
    
    # Constants from C++ code
    VENDOR_ID = 0x0483
    PRODUCT_ID = 0x5750
    TX_BUFFER_SIZE = 64
    RX_BUFFER_SIZE = 64
    HID_REPORT_SIZE = 65  # 64 + 1 for report ID
    
    # Command constants
    GET_CMD = 0x02
    READ_CMD = 0x04
    
    def __init__(self, debug=DEBUG):
        self.device = None
        self.frame_data = [[0 for _ in range(24)] for _ in range(24)]
        self.gain_mode = 0
        self.int_time = 1.0
        self.frame_size = 0  # 0: 12x12 frame; 1: 24x24 frame
        self.current_channel = 1
        self.continue_flag = False
        self.debug = debug
    
    def debug_print(self, message):
        """Print debug messages if debug mode is enabled"""
        if self.debug:
            print(f"DEBUG: {message}")
    
    def find_device(self):
        """Find and open the ULS24 device"""
        try:
            # List available devices for debugging
            if self.debug:
                print("Enumerating all HID devices:")
                for device_info in hid.enumerate():
                    print(f"  VID: {device_info['vendor_id']:04x}, "
                          f"PID: {device_info['product_id']:04x}, "
                          f"Path: {device_info['path']}")
            
            # Initialize the device
            self.debug_print("Initializing HID device...")
            self.device = hid.device()
            self.debug_print(f"Looking for device with VID: {self.VENDOR_ID:04x}, PID: {self.PRODUCT_ID:04x}")
            self.device.open(self.VENDOR_ID, self.PRODUCT_ID)
            
            # Set some device properties
            self.device.set_nonblocking(0)  # Use blocking mode for simplicity
            
            print(f"Opened device: Manufacturer: {self.device.get_manufacturer_string()}, "
                  f"Product: {self.device.get_product_string()}")
            
            return True
        except IOError as e:
            print(f"Error opening device: {e}")
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"Unexpected error opening device: {e}")
            traceback.print_exc()
            return False
    
    def close(self):
        """Close the device"""
        if self.device:
            try:
                self.debug_print("Closing device")
                self.device.close()
            except Exception as e:
                print(f"Error closing device: {e}")
            finally:
                self.device = None
    
    def write_hid_report(self, tx_data, timeout_ms=1000):
        """Write data to device with timeout"""
        if not self.device:
            print("Device not open")
            return False
        
        # Create output report with report ID 0
        output_report = bytearray(self.HID_REPORT_SIZE)
        output_report[0] = 0  # Report ID
        
        # Copy the tx_data to output_report (skip the report ID)
        for i in range(min(len(tx_data), self.TX_BUFFER_SIZE)):
            output_report[i + 1] = tx_data[i]
        
        # Debug print output report
        if self.debug:
            hex_data = ' '.join([f"{b:02x}" for b in output_report[:10]]) + " ..."
            self.debug_print(f"Writing data: {hex_data}")
        
        # Send the report with timeout
        try:
            start_time = time.time()
            self.device.write(output_report)
            elapsed = (time.time() - start_time) * 1000
            if elapsed > timeout_ms:
                self.debug_print(f"Write took longer than expected: {elapsed:.1f}ms")
            return True
        except IOError as e:
            print(f"Error writing to device: {e}")
            return False
    
    def read_hid_report(self, timeout_ms=5000):
        """Read data from device with timeout"""
        if not self.device:
            print("Device not open")
            return None
        
        try:
            # Read with timeout
            self.debug_print(f"Reading with timeout of {timeout_ms}ms")
            start_time = time.time()
            
            # Try to read until timeout
            while (time.time() - start_time) * 1000 < timeout_ms:
                # Read the report
                data = self.device.read(self.HID_REPORT_SIZE, timeout_ms=100)
                
                if data:
                    elapsed = (time.time() - start_time) * 1000
                    self.debug_print(f"Read completed in {elapsed:.1f}ms")
                    
                    # Debug print received data
                    if self.debug:
                        hex_data = ' '.join([f"{b:02x}" for b in data[:10]]) + " ..."
                        self.debug_print(f"Received data: {hex_data}")
                    
                    # Process the received data
                    rx_data = data[1:]  # Skip report ID
                    
                    if len(rx_data) >= 5:
                        r_cmd = rx_data[2]
                        r_type = rx_data[4]
                        
                        self.debug_print(f"Received command: {r_cmd:02x}, type: {r_type:02x}")
                        
                        if r_cmd == self.GET_CMD:
                            if r_type in [0x01, 0x02, 0x12, 0x22, 0x32, 0x03]:
                                self.current_channel = (r_type & 0xF0) // 16 + 1
                                
                                # F1 Code detection
                                if rx_data[5] in [0x0b, 0xf1]:
                                    self.continue_flag = False
                                    if rx_data[5] == 0xf1:
                                        print("Error code 0xF1. Sensor communication time out.")
                                        return None
                                else:
                                    self.continue_flag = True
                            elif r_type in [0x07, 0x08, 0x0b]:
                                if rx_data[5] == 0x17:
                                    self.continue_flag = False
                                else:
                                    self.continue_flag = True
                    
                    return rx_data
                
                # Small delay to prevent CPU hogging
                time.sleep(0.01)
            
            self.debug_print(f"Read timeout after {timeout_ms}ms")
            return None
        
        except IOError as e:
            print(f"Error reading from device: {e}")
            return None
    
    def process_row_data(self, rx_data):
        """Process received data, similar to ProcessRowData in C++ code"""
        if not rx_data or len(rx_data) < 6:
            self.debug_print("Invalid or incomplete data received")
            return
        
        r_type = rx_data[4]
        r_row = rx_data[5]
        
        self.debug_print(f"Processing row data: type={r_type:02x}, row={r_row}")
        
        if r_type == 0x01:  # 12x12 data
            self.frame_size = 0
            
            # Process 12x12 data
            if 0 <= r_row < 12:
                for i in range(12):
                    if len(rx_data) > 2*i + 6:
                        high_byte = rx_data[2*i + 6] 
                        low_byte = rx_data[2*i + 7]
                        adc_value = (high_byte << 8) | low_byte
                        
                        # Apply any needed calibration here
                        # In the C++ code this would call ADCCorrection
                        self.frame_data[r_row][i] = adc_value
        
        elif r_type in [0x02, 0x12, 0x22, 0x32]:  # 24x24 data
            self.frame_size = 1
            
            # Process 24x24 data
            chan = (r_type & 0xF0) // 16
            if 0 <= r_row < 24:
                for i in range(12):
                    if len(rx_data) > 2*i + 6:
                        high_byte = rx_data[2*i + 6]
                        low_byte = rx_data[2*i + 7]
                        adc_value = (high_byte << 8) | low_byte
                        
                        # Apply any needed calibration here
                        col = i
                        if chan == 1:  # upper right
                            col = i + 12
                        elif chan == 2:  # lower left
                            pass  # col = i
                        else:  # lower right
                            col = i + 12
                            
                        self.frame_data[r_row][col] = adc_value
    
    def sel_sensor(self, channel):
        """Select sensor channel"""
        if not 1 <= channel <= 4:
            print(f"Invalid channel: {channel}")
            return False
        
        self.debug_print(f"Selecting sensor channel {channel}")
        self.current_channel = channel
        
        # Create the command
        tx_data = bytearray(self.TX_BUFFER_SIZE)
        tx_data[0] = 0x03  # Sensor select command
        tx_data[1] = channel
        
        # Send the command
        result = self.write_hid_report(tx_data)
        if result:
            # Read the response with shorter timeout for simple commands
            self.debug_print("Reading response after sensor selection")
            rx_data = self.read_hid_report(timeout_ms=2000)
            if rx_data is None:
                self.debug_print("No response received for sensor selection, continuing anyway")
        return result
    
    def set_int_time(self, int_time_ms):
        """Set integration time in milliseconds"""
        if not 1 <= int_time_ms <= 66000:
            print(f"Invalid integration time: {int_time_ms}")
            return False
        
        self.debug_print(f"Setting integration time to {int_time_ms}ms")
        self.int_time = float(int_time_ms)
        
        # Create the command (the format will depend on your device protocol)
        tx_data = bytearray(self.TX_BUFFER_SIZE)
        tx_data[0] = 0x05  # Integration time command
        
        # Convert int_time to appropriate format for the device
        # This is a simple example - adjust according to your actual protocol
        ms_value = int(int_time_ms)
        tx_data[1] = (ms_value >> 8) & 0xFF  # high byte
        tx_data[2] = ms_value & 0xFF        # low byte
        
        # Send the command
        result = self.write_hid_report(tx_data)
        if result:
            # Read the response with shorter timeout for simple commands
            self.debug_print("Reading response after setting integration time")
            rx_data = self.read_hid_report(timeout_ms=2000)
            if rx_data is None:
                self.debug_print("No response received for integration time, continuing anyway")
        return result
    
    def set_gain_mode(self, gain):
        """Set gain mode (0: high gain, 1: low gain)"""
        if gain not in [0, 1]:
            print(f"Invalid gain mode: {gain}")
            return False
        
        self.debug_print(f"Setting gain mode to {'low' if gain else 'high'} ({gain})")
        self.gain_mode = gain
        
        # Create the command
        tx_data = bytearray(self.TX_BUFFER_SIZE)
        tx_data[0] = 0x04  # Gain mode command
        tx_data[1] = gain
        
        # Send the command
        result = self.write_hid_report(tx_data)
        if result:
            # Read the response with shorter timeout for simple commands
            self.debug_print("Reading response after setting gain mode")
            rx_data = self.read_hid_report(timeout_ms=2000)
            if rx_data is None:
                self.debug_print("No response received for gain mode, continuing anyway")
        return result
    
    def capture_frame(self, channel=None):
        """Capture a frame from the specified channel or current channel"""
        if channel is None:
            channel = self.current_channel
        
        if not 1 <= channel <= 4:
            print(f"Invalid channel: {channel}")
            return False
        
        self.debug_print(f"Capturing frame from channel {channel}")
        
        # Create the capture command
        tx_data = bytearray(self.TX_BUFFER_SIZE)
        tx_data[0] = 0x01  # Capture command for 12x12
        tx_data[1] = channel
        
        # Send the command
        result = self.write_hid_report(tx_data)
        if not result:
            return False
        
        # Process data row by row with timeout
        max_attempts = 20  # Maximum number of read attempts
        self.continue_flag = True
        attempts = 0
        
        self.debug_print("Starting frame capture loop")
        while self.continue_flag and attempts < max_attempts:
            attempts += 1
            self.debug_print(f"Read attempt {attempts}/{max_attempts}")
            
            rx_data = self.read_hid_report(timeout_ms=5000)
            if rx_data:
                self.process_row_data(rx_data)
            else:
                self.debug_print("No data received, breaking capture loop")
                self.continue_flag = False
        
        self.debug_print(f"Frame capture completed after {attempts} read attempts")
        return attempts > 0
    
    def print_data(self):
        """Print the captured frame data"""
        dim = 24 if self.frame_size else 12
        
        for i in range(dim):
            row = " ".join(f"{self.frame_data[i][j]}" for j in range(dim))
            print(row)


def main():
    """Main function to demonstrate usage"""
    device = ULS24Device(debug=True)
    
    if not device.find_device():
        print("Device not found")
        return 1
    
    print("Device found")
    
    # Set some initial parameters
    device.sel_sensor(1)
    device.set_int_time(30)  # 30ms
    device.set_gain_mode(1)  # low gain mode
    
    # Capture a frame
    device.capture_frame(1)
    device.print_data()
    
    # Close the device
    device.close()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())