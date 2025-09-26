# ULS24 Device Python Interface

This directory contains Python scripts for interfacing with the ULS24 device using HID communication, similar to the C++ implementation in the TestCl project.

## Requirements

- Python 3.6 or higher
- `hidapi` Python package

## Installation

1. Install the required Python package:

```bash
pip install hidapi
```

## Files

- `python_hid_wrapper.py`: Contains the `ULS24Device` class that handles communication with the device
- `example_script.py`: Example script demonstrating a sequence of operations with the device
- `uls24_cli.py`: Command-line interface script for controlling the device

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