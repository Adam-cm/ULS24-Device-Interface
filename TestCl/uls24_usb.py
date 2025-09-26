#!/usr/bin/env python3
"""
Alternative ULS24 device interface using PyUSB instead of hidapi
For systems where hidraw kernel module is not available
"""
import sys
import time
import struct
import usb.core
import usb.util

# Debug flag - set to True for verbose output
DEBUG = True

class ULS24DeviceUSB:
    """Class to interface with ULS24 device using direct USB communication"""
    
    # Constants from C++ code
    VENDOR_ID = 0x0483
    PRODUCT_ID = 0x5750
    TX_BUFFER_SIZE = 64
    RX_BUFFER_SIZE = 64
    
    # Protocol constants from TrimReader.cpp
    PREAMBLE_CODE = 0xaa
    BACKCODE = 0x17
    
    # Command codes
    CMD_SETPARAM = 0x01
    CMD_CAPTURE = 0x02
    CMD_EEPROM_READ = 0x04
    
    # Data type codes
    TYPE_RAMPGEN = 0x01
    TYPE_RANGE = 0x02
    TYPE_V20 = 0x04
    TYPE_V15 = 0x05
    TYPE_GAINMODE = 0x07
    TYPE_TXBIN = 0x08
    TYPE_CAPTURE12 = 0x02
    TYPE_CAPTURE24 = 0x08
    TYPE_INTTIME = 0x20
    TYPE_LEDCONFIG = 0x23
    TYPE_SELSENSOR = 0x26
    TYPE_EEPROM = 0x2d
    
    def __init__(self, debug=DEBUG):
        self.device = None
        self.ep_out = None
        self.ep_in = None
        self.interface = None
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
                print("Searching for USB devices...")
            
            # Find the device by vendor ID and product ID
            self.device = usb.core.find(idVendor=self.VENDOR_ID, idProduct=self.PRODUCT_ID)
            
            if self.device is None:
                print(f"Device not found (VID:PID {self.VENDOR_ID:04x}:{self.PRODUCT_ID:04x})")
                return False
            
            self.debug_print(f"Device found: {self.device}")
            
            # Detach kernel driver if it's being used
            try:
                if self.device.is_kernel_driver_active(0):
                    self.debug_print("Detaching kernel driver")
                    self.device.detach_kernel_driver(0)
            except Exception as e:
                self.debug_print(f"Could not detach kernel driver: {e}")
            
            # Set configuration
            self.debug_print("Setting configuration")
            self.device.set_configuration()
            
            # Get active configuration
            cfg = self.device.get_active_configuration()
            
            # Get interface
            self.interface = cfg[(0,0)]
            
            # Find endpoints
            for ep in self.interface:
                if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                    self.ep_out = ep
                elif usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN:
                    self.ep_in = ep
            
            if self.ep_out is None or self.ep_in is None:
                print("Could not find required endpoints")
                return False
            
            self.debug_print(f"Endpoints: OUT={self.ep_out.bEndpointAddress:02x}, IN={self.ep_in.bEndpointAddress:02x}")
            
            # Print device information
            try:
                manufacturer = usb.util.get_string(self.device, self.device.iManufacturer)
                product = usb.util.get_string(self.device, self.device.iProduct)
                print(f"Opened device: Manufacturer: {manufacturer}, Product: {product}")
            except Exception as e:
                self.debug_print(f"Error getting device strings: {e}")
                print("Device opened successfully, but couldn't get string descriptors")
            
            return True
        except usb.core.USBError as e:
            print(f"USB Error: {e}")
            if "Permission denied" in str(e):
                print("USB permission denied. Try running with sudo or set up udev rules.")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def close(self):
        """Close the device"""
        if self.device:
            try:
                self.debug_print("Releasing USB interface")
                usb.util.release_interface(self.device, self.interface)
                self.debug_print("USB interface released")
            except Exception as e:
                self.debug_print(f"Error releasing interface: {e}")
    
    def create_command(self, command, data_type, data):
        """Create a command buffer according to the protocol in C++ code"""
        tx_data = bytearray(self.TX_BUFFER_SIZE)
        
        # Match the format from TrimReader.cpp
        tx_data[0] = self.PREAMBLE_CODE  # preamble code 0xaa
        tx_data[1] = command  # command
        
        if isinstance(data, list):
            # Multiple data bytes
            tx_data[2] = len(data) + 1  # data length (including type)
            tx_data[3] = data_type  # data type
            
            # Copy data bytes
            for i, val in enumerate(data):
                tx_data[4 + i] = val
            
            # Calculate checksum (starting from tx_data[1] through all data bytes)
            checksum = 0
            for i in range(1, 4 + len(data)):
                checksum += tx_data[i]
            
            # Handle special case for checksum
            if checksum == 0x17:
                checksum = 0x18
            
            tx_data[4 + len(data)] = checksum
            
            # Back codes
            tx_data[5 + len(data)] = self.BACKCODE
            tx_data[6 + len(data)] = self.BACKCODE
        else:
            # Single data byte
            tx_data[2] = 0x02  # data length
            tx_data[3] = data_type  # data type
            tx_data[4] = data  # real data
            
            # Calculate checksum
            checksum = tx_data[1] + tx_data[2] + tx_data[3] + tx_data[4]
            
            # Handle special case for checksum
            if checksum == 0x17:
                checksum = 0x18
            
            tx_data[5] = checksum
            
            # Back codes
            tx_data[6] = self.BACKCODE
            tx_data[7] = self.BACKCODE
        
        return tx_data
    
    def write_usb(self, tx_data, timeout_ms=1000):
        """Write data to device with timeout"""
        if not self.device or not self.ep_out:
            print("Device not open")
            return False
        
        # Debug print output data
        if self.debug:
            hex_data = ' '.join([f"{b:02x}" for b in tx_data[:20]])
            self.debug_print(f"Writing data: {hex_data}")
        
        try:
            # In PyUSB, the first byte is not a report ID like in hidapi
            bytes_written = self.ep_out.write(tx_data, timeout=timeout_ms)
            self.debug_print(f"Wrote {bytes_written} bytes")
            return bytes_written > 0
        except usb.core.USBError as e:
            print(f"USB Error writing data: {e}")
            return False
    
    def read_usb(self, timeout_ms=5000):
        """Read data from device with timeout"""
        if not self.device or not self.ep_in:
            print("Device not open")
            return None
        
        try:
            # Read with timeout
            self.debug_print(f"Reading with timeout of {timeout_ms}ms")
            data = self.device.read(self.ep_in.bEndpointAddress, self.RX_BUFFER_SIZE, timeout=timeout_ms)
            
            if data:
                # Debug print received data
                if self.debug:
                    hex_data = ' '.join([f"{b:02x}" for b in data[:20]])
                    self.debug_print(f"Received data: {hex_data}")
                
                # Process according to C++ code (ReadHIDInputReport)
                rx_data = bytes(data)
                
                if len(rx_data) >= 5:
                    r_cmd = rx_data[2]
                    r_type = rx_data[4]
                    
                    self.debug_print(f"Received command: {r_cmd:02x}, type: {r_type:02x}")
                    
                    if r_cmd == 0x02:  # GetCmd from C++
                        if r_type in [0x01, 0x02, 0x12, 0x22, 0x32, 0x03]:
                            self.current_channel = ((r_type & 0xF0) // 16) + 1
                            
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
            
            self.debug_print(f"No data received within timeout")
            return None
        
        except usb.core.USBTimeoutError:
            self.debug_print("USB read timeout")
            return None
        except usb.core.USBError as e:
            print(f"USB Error reading data: {e}")
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
                        high_byte = rx_data[2*i + 7]  # Note: C++ uses rx_data[2*i+7]
                        low_byte = rx_data[2*i + 6]   # and rx_data[2*i+6]
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
                        high_byte = rx_data[2*i + 7]
                        low_byte = rx_data[2*i + 6]
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
        
        # Create command based on TrimReader::SelSensor
        tx_data = self.create_command(
            command=self.CMD_SETPARAM,
            data_type=self.TYPE_SELSENSOR,
            data=[channel - 1, 0x00]  # Channel is 0-indexed in protocol
        )
        
        # Send the command
        result = self.write_usb(tx_data)
        if result:
            # Read the response with shorter timeout for simple commands
            self.debug_print("Reading response after sensor selection")
            rx_data = self.read_usb(timeout_ms=2000)
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
        
        # Match the SetIntTime from TrimReader.cpp
        float_ms = float(int_time_ms)
        # Convert float to bytes (4 bytes in little-endian format)
        float_bytes = list(struct.pack('<f', float_ms))
        
        # Create command
        tx_data = self.create_command(
            command=self.CMD_SETPARAM,
            data_type=self.TYPE_INTTIME,
            data=float_bytes
        )
        
        # Send the command
        result = self.write_usb(tx_data)
        if result:
            # Read the response with shorter timeout for simple commands
            self.debug_print("Reading response after setting integration time")
            rx_data = self.read_usb(timeout_ms=2000)
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
        
        # Create command
        tx_data = self.create_command(
            command=self.CMD_SETPARAM,
            data_type=self.TYPE_GAINMODE,
            data=gain
        )
        
        # Send the command
        result = self.write_usb(tx_data)
        if result:
            # Read the response with shorter timeout for simple commands
            self.debug_print("Reading response after setting gain mode")
            rx_data = self.read_usb(timeout_ms=2000)
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
        
        # Create capture command based on Capture12 in TrimReader.cpp
        tx_data = bytearray(self.TX_BUFFER_SIZE)
        tx_data[0] = self.PREAMBLE_CODE  # 0xaa, preamble code
        tx_data[1] = self.CMD_CAPTURE    # 0x02, command
        tx_data[2] = 0x0C                # data length
        tx_data[3] = ((channel - 1) << 4) | 0x02  # data type with channel encoded
        tx_data[4] = 0xFF                # real data
        
        # Fill remaining bytes
        for i in range(5, 15):
            tx_data[i] = 0x00
        
        # Calculate checksum
        checksum = 0
        for i in range(1, 15):
            checksum += tx_data[i]
        
        # Handle special case for checksum
        if checksum == 0x17:
            checksum = 0x18
        
        tx_data[15] = checksum
        tx_data[16] = self.BACKCODE  # 0x17, back code
        tx_data[17] = self.BACKCODE  # 0x17, back code
        
        # Send the command
        result = self.write_usb(tx_data)
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
            
            rx_data = self.read_usb(timeout_ms=5000)
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
    device = ULS24DeviceUSB(debug=True)
    
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