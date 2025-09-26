#!/usr/bin/env python3
"""
Tool to diagnose USB/HID device issues on Linux systems
"""
import os
import sys
import subprocess
import time
import traceback

def run_command(command, show_output=True):
    """Run a shell command and return its output"""
    try:
        result = subprocess.run(command, shell=True, check=False,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True)
        if show_output:
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr:
                print("ERROR:", result.stderr.strip())
        return result.stdout.strip(), result.returncode
    except Exception as e:
        print(f"Error running command '{command}': {e}")
        return "", 1

def check_python_version():
    """Check Python version"""
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    return True

def check_user_and_groups():
    """Check current user and groups"""
    user, _ = run_command("whoami")
    print(f"Current user: {user}")
    
    groups, _ = run_command("groups")
    print(f"User groups: {groups}")
    
    if "dialout" in groups or "plugdev" in groups:
        print("? User is in relevant groups (dialout or plugdev)")
        return True
    else:
        print("? User is NOT in dialout or plugdev groups")
        print("  Recommendation: Add user to these groups with:")
        print(f"  sudo usermod -a -G plugdev,dialout {user}")
        return False

def check_hidapi_installation():
    """Check if hidapi is installed"""
    try:
        import hid
        print(f"hidapi module found: {hid.__file__}")
        return True
    except ImportError:
        print("? hidapi module not found")
        print("  Recommendation: Install hidapi with:")
        print("  pip install hidapi")
        return False

def check_usb_devices():
    """Check for USB devices, particularly the ULS24"""
    print("\nUSB devices:")
    usb_devices, _ = run_command("lsusb")
    
    if "0483:5750" in usb_devices:
        print("? ULS24 device found (VID:PID 0483:5750)")
        found = True
    else:
        print("? ULS24 device NOT found")
        found = False
        
    return found

def check_device_permissions():
    """Check permissions on USB device files"""
    vid_pid = "0483:5750"
    
    # Find the device file for our VID:PID
    print("\nChecking device permissions:")
    devices, _ = run_command("find /dev/bus/usb -type c", False)
    
    found = False
    for dev_path in devices.splitlines():
        device_info, _ = run_command(f"udevadm info -q all -n {dev_path} | grep ID_VENDOR_ID", False)
        if "0483" in device_info:
            product_info, _ = run_command(f"udevadm info -q all -n {dev_path} | grep ID_MODEL_ID", False)
            if "5750" in product_info:
                found = True
                perms, _ = run_command(f"ls -l {dev_path}")
                print(f"Device path: {dev_path}")
                print(f"Permissions: {perms}")
                
                if "rw" in perms and ("crw-rw" in perms or "root" not in perms):
                    print("? Device has appropriate permissions")
                else:
                    print("? Device may not have appropriate permissions")
                    print("  Recommendation: Add udev rules to fix permissions:")
                    print("  sudo bash -c 'cat > /etc/udev/rules.d/99-hidapi.rules << EOF")
                    print("  SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"0483\", ATTRS{idProduct}==\"5750\", MODE=\"0666\"")
                    print("  EOF'")
                    print("  sudo udevadm control --reload-rules")
                    print("  sudo udevadm trigger")
    
    if not found:
        print("? Device file not found")
    
    return found

def check_hidapi_devices():
    """Try to enumerate HID devices using hidapi"""
    print("\nHID devices via hidapi:")
    try:
        import hid
        devices = hid.enumerate()
        
        found = False
        for dev in devices:
            if dev['vendor_id'] == 0x0483 and dev['product_id'] == 0x5750:
                found = True
                print(f"? ULS24 device found via hidapi:")
                print(f"  Path: {dev['path']}")
                print(f"  Manufacturer: {dev.get('manufacturer_string', 'Unknown')}")
                print(f"  Product: {dev.get('product_string', 'Unknown')}")
                break
                
        if not found:
            print("? ULS24 device NOT found via hidapi")
        
        return found
    except Exception as e:
        print(f"Error enumerating HID devices: {e}")
        traceback.print_exc()
        return False

def check_kernel_modules():
    """Check if necessary kernel modules are loaded"""
    print("\nChecking kernel modules:")
    for module in ["usbhid", "hidraw"]:
        loaded, _ = run_command(f"lsmod | grep {module}", False)
        if loaded:
            print(f"? {module} module is loaded")
        else:
            print(f"? {module} module is NOT loaded")
            print(f"  Recommendation: Try loading with 'sudo modprobe {module}'")

def try_open_device():
    """Try to open the device directly"""
    print("\nAttempting to open device:")
    try:
        import hid
        try:
            device = hid.device()
            device.open(0x0483, 0x5750)
            print(f"? Successfully opened device")
            try:
                print(f"  Manufacturer: {device.get_manufacturer_string()}")
                print(f"  Product: {device.get_product_string()}")
            except Exception as e:
                print(f"  Error getting device strings: {e}")
            device.close()
            return True
        except Exception as e:
            print(f"? Failed to open device: {e}")
            return False
    except ImportError:
        print("? Cannot test device opening without hidapi module")
        return False

def main():
    """Main function"""
    print("=== ULS24 Device Diagnostic Tool ===\n")
    
    # System checks
    print("--- System Information ---")
    check_python_version()
    check_user_and_groups()
    
    # Library checks
    print("\n--- Library Information ---")
    check_hidapi_installation()
    check_kernel_modules()
    
    # Device checks
    print("\n--- Device Information ---")
    device_found = check_usb_devices()
    if device_found:
        check_device_permissions()
        check_hidapi_devices()
        try_open_device()
    
    print("\n=== Diagnostic Complete ===")
    
    # Final recommendations
    if not device_found:
        print("\nRecommendations:")
        print("1. Make sure the device is connected")
        print("2. Try a different USB port")
        print("3. Try running 'sudo lsusb' to see if the device is visible as root")

if __name__ == "__main__":
    main()