# ULS24 Device Python Interface

This directory contains Python scripts for interfacing with the ULS24 device using HID communication, similar to the C++ implementation in the TestCl project.

## Requirements

- Python 3.6 or higher
- `hidapi` Python package

## Installation

1. Install the required Python package:

```bash
# On Windows/macOS:
pip install hidapi

# On newer Linux distributions (Python 3.11+) use one of these options:
# Option 1: Create a virtual environment (recommended)
python3 -m venv uls24_env
source uls24_env/bin/activate
pip install hidapi

# Option 2: Install for current user only
pip install --user hidapi

# Option 3: Force system-wide installation (not recommended)
pip install --break-system-packages hidapi

# Option 4: Use apt if available
sudo apt-get install python3-hid
```

2. On Linux, you may need to add udev rules for USB device access:

```bash
sudo bash -c 'cat > /etc/udev/rules.d/99-hidapi.rules << EOF
SUBSYSTEM=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5750", MODE="0666"
EOF'
sudo udevadm control --reload-rules
sudo udevadm trigger
```

3. Also on Linux, add your user to the appropriate groups:

```bash
sudo usermod -a -G plugdev,dialout $USER
# Log out and back in for this to take effect
```

## Files

- `python_hid_wrapper.py`: Contains the `ULS24Device` class that handles communication with the device
- `example_script.py`: Example script demonstrating a sequence of operations with the device
- `uls24_cli.py`: Command-line interface script for controlling the device
- `test_device.py`: Simple test script to verify basic device functionality
- `diagnose_device.py`: Diagnostic tool to help identify USB/HID device issues (Linux only)

## Usage

### Basic Usage with ULS24Device Class

```python
from python_hid_wrapper import ULS24Device

# Create device instance
device = ULS24Device()

# Connect to device
if device.find_device():
    # Set parameters
    device.sel_sensor(1)        # Select channel 1
    device.set_int_time(30)     # Set integration time to 30ms
    device.set_gain_mode(1)     # Set gain mode to low
    
    # Capture frame
    if device.capture_frame():
        # Print frame data
        device.print_data()
        
    # Close connection
    device.close()
else:
    print("Device not found")
```

### Example Script

Run the example script to perform a sequence of operations with the device:

```bash
python example_script.py
```

This script demonstrates:
- Connecting to the device
- Setting parameters (channel, integration time, gain mode)
- Capturing frames with different settings
- Printing frame data

### Command-Line Interface

The `uls24_cli.py` script provides a command-line interface similar to the C++ application.

#### Interactive Mode

Run in interactive mode to send commands interactively:

```bash
python uls24_cli.py --interactive
```

Available commands:
- `selchan`: Select sensor channel
- `get`: Capture frame from current channel
- `setinttime`: Set integration time
- `setgain`: Set gain mode
- `reset`: Reset and reconnect to the device
- `exit`: Exit the program

#### Command-Line Arguments

You can also use command-line arguments to perform operations:

```bash
# Select channel 2, set integration time to 50ms, and capture frame
python uls24_cli.py --selchan 2 --setinttime 50 --get

# Set high gain mode and capture frame from channel 3, save to file
python uls24_cli.py --setgain 0 --get --channel 3 --output frame_data.txt

# Reset the device
python uls24_cli.py --reset
```

## Troubleshooting

If you encounter issues with the device:

### 1. Run the Diagnostic Tool

The diagnostic tool can help identify USB/HID device issues:

```bash
python diagnose_device.py
```

This will check:
- Python and hidapi installation
- User permissions
- USB device presence
- Device file permissions
- Loaded kernel modules
- Whether the device can be opened

### 2. Run the Simple Test Script

The test script performs basic functionality tests step by step:

```bash
python test_device.py
```

### 3. Enable Debug Mode

You can enable debug mode in the ULS24Device class:

```python
device = ULS24Device(debug=True)
```

Or modify the scripts to set `DEBUG = True` at the top of python_hid_wrapper.py.

### Common Issues and Solutions

1. **Device Not Found**
   - Make sure the device is properly connected
   - Check USB cable and port
   - Verify device appears in `lsusb` output (on Linux)
   - Try a different USB port

2. **Permission Denied**
   - Add udev rules as described in the Installation section
   - Add your user to the appropriate groups
   - Try running the script with sudo as a temporary solution

3. **Script Freezes After Connection**
   - The device might not be responding to commands
   - Check power supply to the device
   - Verify that the device is properly initialized
   - Try unplugging and reconnecting the device
   - Run the diagnostic tool to check if the device can be opened

4. **Error: No Module Named 'hid'**
   - Install the hidapi package as described in the Installation section
   - If using a virtual environment, make sure it's activated
   - On newer Linux distributions, use one of the installation options provided

5. **Unable to Open Device**
   - Check if the device is already in use by another program
   - Verify that the correct VID/PID is being used (default: 0x0483/0x5750)
   - Try closing all other applications that might be using the device

## Command Details

### Select Channel

```python
device.sel_sensor(channel)  # channel: 1-4
```

### Set Integration Time

```python
device.set_int_time(time_ms)  # time_ms: 1-66000 milliseconds
```

### Set Gain Mode

```python
device.set_gain_mode(gain)  # gain: 0 for high gain, 1 for low gain
```

### Capture Frame

```python
device.capture_frame(channel)  # channel: 1-4 (optional, uses current channel if None)
```

## Notes

- The actual command codes and data formats may need adjustment based on your specific device protocol
- This implementation assumes similar behavior to the C++ code but may need tweaking for your hardware
- Error handling is basic and can be enhanced for production use