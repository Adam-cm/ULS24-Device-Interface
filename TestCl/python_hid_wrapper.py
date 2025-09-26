#!/usr/bin/env python3
"""
Python wrapper for HID device communication, replicating the functionality in TestCl.cpp
"""
import sys
import time
import hid  # pip install hidapi

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
    
    def __init__(self):
        self.device = None
        self.frame_data = [[0 for _ in range(24)] for _ in range(24)]
        self.gain_mode = 0
        self.int_time = 1.0
        self.frame_size = 0  # 0: 12x12 frame; 1: 24x24 frame
        self.current_channel = 1
        self.continue_flag = False
    
    def find_device(self):
        """Find and open the ULS24 device"""
        try:
            # Initialize the device
            self.device = hid.device()
            self.device.open(self.VENDOR_ID, self.PRODUCT_ID)
            
            # Set some device properties
            self.device.set_nonblocking(0)  # Use blocking mode for simplicity
            
            print(f"Opened device: Manufacturer: {self.device.get_manufacturer_string()}, "
                  f"Product: {self.device.get_product_string()}")
            
            return True
        except IOError as e:
            print(f"Error opening device: {e}")
            return False
    
    def close(self):
        """Close the device"""
        if self.device:
            self.device.close()
            self.device = None
    
    def write_hid_report(self, tx_data):
        """Write data to device"""
        if not self.device:
            print("Device not open")
            return False
        
        # Create output report with report ID 0
        output_report = bytearray(self.HID_REPORT_SIZE)
        output_report[0] = 0  # Report ID
        
        # Copy the tx_data to output_report (skip the report ID)
        for i in range(min(len(tx_data), self.TX_BUFFER_SIZE)):
            output_report[i + 1] = tx_data[i]
        
        # Send the report
        try:
            self.device.write(output_report)
            return True
        except IOError as e:
            print(f"Error writing to device: {e}")
            return False
    
    def read_hid_report(self, timeout_ms=264000):
        """Read data from device with timeout"""
        if not self.device:
            print("Device not open")
            return None
        
        try:
            # Read with timeout
            start_time = time.time()
            while (time.time() - start_time) * 1000 < timeout_ms:
                # Read the report (blocking)
                data = self.device.read(self.HID_REPORT_SIZE)
                if data:
                    # Process the received data
                    rx_data = data[1:]  # Skip report ID
                    
                    if len(rx_data) >= 5:
                        r_cmd = rx_data[2]
                        r_type = rx_data[4]
                        
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
                time.sleep(0.001)
            
            print("Read timeout")
            return None
        
        except IOError as e:
            print(f"Error reading from device: {e}")
            return None
    
    def process_row_data(self, rx_data):
        """Process received data, similar to ProcessRowData in C++ code"""
        if not rx_data or len(rx_data) < 6:
            return
        
        r_type = rx_data[4]
        r_row = rx_data[5]
        
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
        
        self.current_channel = channel
        
        # Create the command
        tx_data = bytearray(self.TX_BUFFER_SIZE)
        tx_data[0] = 0x03  # Sensor select command
        tx_data[1] = channel
        
        # Send the command
        result = self.write_hid_report(tx_data)
        if result:
            # Read the response
            self.read_hid_report()
        return result
    
    def set_int_time(self, int_time_ms):
        """Set integration time in milliseconds"""
        if not 1 <= int_time_ms <= 66000:
            print(f"Invalid integration time: {int_time_ms}")
            return False
        
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
            # Read the response
            self.read_hid_report()
        return result
    
    def set_gain_mode(self, gain):
        """Set gain mode (0: high gain, 1: low gain)"""
        if gain not in [0, 1]:
            print(f"Invalid gain mode: {gain}")
            return False
        
        self.gain_mode = gain
        
        # Create the command
        tx_data = bytearray(self.TX_BUFFER_SIZE)
        tx_data[0] = 0x04  # Gain mode command
        tx_data[1] = gain
        
        # Send the command
        result = self.write_hid_report(tx_data)
        if result:
            # Read the response
            self.read_hid_report()
        return result
    
    def capture_frame(self, channel=None):
        """Capture a frame from the specified channel or current channel"""
        if channel is None:
            channel = self.current_channel
        
        if not 1 <= channel <= 4:
            print(f"Invalid channel: {channel}")
            return False
        
        # Create the capture command
        tx_data = bytearray(self.TX_BUFFER_SIZE)
        tx_data[0] = 0x01  # Capture command for 12x12
        tx_data[1] = channel
        
        # Send the command
        result = self.write_hid_report(tx_data)
        if not result:
            return False
        
        # Process data row by row
        self.continue_flag = True
        while self.continue_flag:
            rx_data = self.read_hid_report()
            if rx_data:
                self.process_row_data(rx_data)
            else:
                self.continue_flag = False
        
        return True
    
    def print_data(self):
        """Print the captured frame data"""
        dim = 24 if self.frame_size else 12
        
        for i in range(dim):
            row = " ".join(f"{self.frame_data[i][j]}" for j in range(dim))
            print(row)


def main():
    """Main function to demonstrate usage"""
    device = ULS24Device()
    
    if not device.find_device():
        print("Device not found")
        return 1
    
    print("Device found")
    
    # Initialize device
    # This would normally load trim data and reset trim like in the C++ code
    # device.read_trim_data()
    # device.reset_trim()
    
    # Set some initial parameters
    device.sel_sensor(1)
    device.set_int_time(30)  # 30ms
    device.set_gain_mode(1)  # low gain mode
    
    print("allowable commands are: selchan, get, setinttime, setgain, reset, exit...")
    
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
    
    device.close()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())