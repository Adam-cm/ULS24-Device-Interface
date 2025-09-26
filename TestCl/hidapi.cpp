#include "stdafx.h"
#include "hidapi.h"

#ifdef _WIN32
#include <windows.h>
#include <setupapi.h>
#include <cfgmgr32.h>
#include <hidsdi.h>
#pragma comment(lib, "setupapi.lib")
#pragma comment(lib, "hid.lib")
#else
#include <unistd.h>
#include <sys/types.h>
#include <fcntl.h>
#endif

#define MAX_STRING 255
#define HIDBUFSIZE 12  // Match the value in HidMgr.h

struct hid_device_ {
#ifdef _WIN32
    HANDLE device_handle;
    BOOL blocking;
    OVERLAPPED ol;
#else
    int device_handle;
    int blocking;
#endif
};

// Static variables
static int hid_init_done = 0;

// Functions

int hid_init(void)
{
    if (!hid_init_done) {
#ifdef _WIN32
        // No initialization needed for Windows
#else
        // Initialization for other platforms
#endif
        hid_init_done = 1;
    }
    return 0;
}

int hid_exit(void)
{
    if (hid_init_done) {
#ifdef _WIN32
        // No cleanup needed for Windows
#else
        // Cleanup for other platforms
#endif
        hid_init_done = 0;
    }
    return 0;
}

void hid_close(hid_device *device)
{
    if (!device)
        return;
        
#ifdef _WIN32
    CloseHandle(device->ol.hEvent);
    CloseHandle(device->device_handle);
    free(device);
#else
    // Close for other platforms
#endif
}

struct hid_device_info* hid_enumerate(unsigned short vendor_id, unsigned short product_id)
{
    struct hid_device_info *root = NULL; // return object
    struct hid_device_info *cur_dev = NULL;

#ifdef _WIN32
    GUID hid_guid;
    HDEVINFO device_info_set;
    SP_DEVINFO_DATA device_info_data;
    SP_DEVICE_INTERFACE_DATA device_interface_data;
    SP_DEVICE_INTERFACE_DETAIL_DATA_A *device_interface_detail_data = NULL;
    DWORD device_index = 0;
    DWORD required_size = 0;
    HIDD_ATTRIBUTES attrib;
    HANDLE dev_handle = INVALID_HANDLE_VALUE;
    BOOL res;
    
    // Get the GUID for HID devices
    HidD_GetHidGuid(&hid_guid);
    
    // Get all devices matching the HID class GUID
    device_info_set = SetupDiGetClassDevsA(&hid_guid, NULL, NULL, DIGCF_PRESENT | DIGCF_DEVICEINTERFACE);
    device_interface_data.cbSize = sizeof(SP_DEVICE_INTERFACE_DATA);
    
    // Enumerate all HID devices
    device_index = 0;
    while (SetupDiEnumDeviceInterfaces(device_info_set, NULL, &hid_guid, device_index, &device_interface_data)) {
        // Get the required size for the device interface detail structure
        SetupDiGetDeviceInterfaceDetailA(device_info_set, &device_interface_data, NULL, 0, &required_size, NULL);
        device_interface_detail_data = (SP_DEVICE_INTERFACE_DETAIL_DATA_A*)malloc(required_size);
        device_interface_detail_data->cbSize = sizeof(SP_DEVICE_INTERFACE_DETAIL_DATA_A);
        
        // Get the device interface detail
        res = SetupDiGetDeviceInterfaceDetailA(device_info_set, &device_interface_data, device_interface_detail_data, required_size, NULL, NULL);
        if (!res) {
            free(device_interface_detail_data);
            device_index++;
            continue;
        }
        
        // Open the device
        dev_handle = CreateFileA(device_interface_detail_data->DevicePath,
                                GENERIC_READ|GENERIC_WRITE,
                                FILE_SHARE_READ|FILE_SHARE_WRITE,
                                NULL,
                                OPEN_EXISTING,
                                FILE_FLAG_OVERLAPPED, // Use overlapped IO
                                NULL);
        
        if (dev_handle == INVALID_HANDLE_VALUE) {
            free(device_interface_detail_data);
            device_index++;
            continue;
        }
        
        attrib.Size = sizeof(HIDD_ATTRIBUTES);
        HidD_GetAttributes(dev_handle, &attrib);
        
        // Check if this device matches the VID/PID we're looking for
        if ((vendor_id == 0x0 || attrib.VendorID == vendor_id) && 
            (product_id == 0x0 || attrib.ProductID == product_id)) {
            
            struct hid_device_info* tmp;
            tmp = (struct hid_device_info*)calloc(1, sizeof(struct hid_device_info));
            if (cur_dev) {
                cur_dev->next = tmp;
            }
            else {
                root = tmp;
            }
            cur_dev = tmp;
            
            // Fill in the device info
            cur_dev->path = _strdup(device_interface_detail_data->DevicePath);
            cur_dev->vendor_id = attrib.VendorID;
            cur_dev->product_id = attrib.ProductID;
            cur_dev->release_number = attrib.VersionNumber;
            
            // Get the manufacturer, product strings and serial number
            wchar_t wstr[MAX_STRING];
            if (HidD_GetManufacturerString(dev_handle, wstr, sizeof(wstr))) {
                cur_dev->manufacturer_string = _wcsdup(wstr);
            }
            
            if (HidD_GetProductString(dev_handle, wstr, sizeof(wstr))) {
                cur_dev->product_string = _wcsdup(wstr);
            }
            
            if (HidD_GetSerialNumberString(dev_handle, wstr, sizeof(wstr))) {
                cur_dev->serial_number = _wcsdup(wstr);
            }
            
            // Get the usage page and usage
            PHIDP_PREPARSED_DATA pp_data = NULL;
            if (HidD_GetPreparsedData(dev_handle, &pp_data)) {
                HIDP_CAPS caps;
                if (HidP_GetCaps(pp_data, &caps) == HIDP_STATUS_SUCCESS) {
                    cur_dev->usage_page = caps.UsagePage;
                    cur_dev->usage = caps.Usage;
                }
                HidD_FreePreparsedData(pp_data);
            }
        }
        
        CloseHandle(dev_handle);
        free(device_interface_detail_data);
        device_index++;
    }
    
    // Clean up the device info set
    SetupDiDestroyDeviceInfoList(device_info_set);
#else
    // For non-Windows platforms
    // Add implementation here for other platforms
#endif
    
    return root;
}

void hid_free_enumeration(struct hid_device_info *devs)
{
    struct hid_device_info *d = devs;
    while (d) {
        struct hid_device_info *next = d->next;
        free(d->path);
        free(d->serial_number);
        free(d->manufacturer_string);
        free(d->product_string);
        free(d);
        d = next;
    }
}

hid_device* hid_open(unsigned short vendor_id, unsigned short product_id, const wchar_t *serial_number)
{
    // Get the list of devices with the specified VID/PID
    struct hid_device_info *devs = hid_enumerate(vendor_id, product_id);
    if (!devs)
        return NULL;
        
    struct hid_device_info *cur_dev = devs;
    hid_device *device = NULL;
    
    while (cur_dev) {
        if (serial_number) {
            // If a serial number was specified, find the device with matching serial
            if (cur_dev->serial_number && wcscmp(serial_number, cur_dev->serial_number) == 0) {
                device = hid_open_path(cur_dev->path);
                break;
            }
        }
        else {
            // If no serial was specified, use the first device
            device = hid_open_path(cur_dev->path);
            break;
        }
        cur_dev = cur_dev->next;
    }
    
    hid_free_enumeration(devs);
    return device;
}

hid_device* hid_open_path(const char *path)
{
    hid_device *dev = NULL;

#ifdef _WIN32
    dev = (hid_device*)calloc(1, sizeof(hid_device));
    if (!dev)
        return NULL;
        
    // Open the device
    dev->device_handle = CreateFileA(path,
                                   GENERIC_READ|GENERIC_WRITE,
                                   FILE_SHARE_READ|FILE_SHARE_WRITE,
                                   NULL,
                                   OPEN_EXISTING,
                                   FILE_FLAG_OVERLAPPED, // Use overlapped IO
                                   NULL);
    
    if (dev->device_handle == INVALID_HANDLE_VALUE) {
        free(dev);
        return NULL;
    }
    
    dev->blocking = TRUE;
    
    // Set up the overlapped structure
    memset(&dev->ol, 0, sizeof(dev->ol));
    dev->ol.hEvent = CreateEvent(NULL, FALSE, FALSE, NULL);
    
    // Set the buffer size to improve performance
    HidD_SetNumInputBuffers(dev->device_handle, HIDBUFSIZE);
#else
    // For non-Windows platforms
    // Add implementation here
#endif
    
    return dev;
}

int hid_write(hid_device *device, const unsigned char *data, size_t length)
{
    if (!device)
        return -1;
        
#ifdef _WIN32
    DWORD bytes_written = 0;
    BOOL res;
    
    // Make sure the device handle is valid
    if (device->device_handle == INVALID_HANDLE_VALUE)
        return -1;
        
    // WriteFile() will return immediately for non-blocking handles.
    // For blocking handles, it will wait until the write is complete.
    res = WriteFile(device->device_handle, data, (DWORD)length, &bytes_written, &device->ol);
    
    if (!res) {
        if (GetLastError() != ERROR_IO_PENDING) {
            // WriteFile() failed, but not because of pending I/O
            return -1;
        }
        
        // Wait for the I/O to complete
        res = GetOverlappedResult(device->device_handle, &device->ol, &bytes_written, TRUE);
        if (!res) {
            // The write failed
            return -1;
        }
    }
    
    return (int)bytes_written;
#else
    // For non-Windows platforms
    return -1;
#endif
}

int hid_read_timeout(hid_device *device, unsigned char *data, size_t length, int milliseconds)
{
    if (!device)
        return -1;
        
#ifdef _WIN32
    DWORD bytes_read = 0;
    BOOL res;
    
    // Make sure the device handle is valid
    if (device->device_handle == INVALID_HANDLE_VALUE)
        return -1;
        
    // ReadFile() will return immediately for non-blocking handles.
    // For blocking handles, it will wait until the read is complete.
    res = ReadFile(device->device_handle, data, (DWORD)length, &bytes_read, &device->ol);
    
    if (!res) {
        if (GetLastError() != ERROR_IO_PENDING) {
            // ReadFile() failed, but not because of pending I/O
            return -1;
        }
        
        // Wait for the I/O to complete with timeout
        DWORD wait_result = WaitForSingleObject(device->ol.hEvent, milliseconds >= 0 ? milliseconds : INFINITE);
        
        if (wait_result == WAIT_OBJECT_0) {
            // I/O completed
            res = GetOverlappedResult(device->device_handle, &device->ol, &bytes_read, FALSE);
            if (!res) {
                // The read failed
                return -1;
            }
            return (int)bytes_read;
        }
        else if (wait_result == WAIT_TIMEOUT) {
            // Timeout
            CancelIo(device->device_handle);
            return 0;
        }
        else {
            // Error
            return -1;
        }
    }
    
    return (int)bytes_read;
#else
    // For non-Windows platforms
    return -1;
#endif
}

int hid_read(hid_device *device, unsigned char *data, size_t length)
{
    return hid_read_timeout(device, data, length, -1); // Blocking read
}

int hid_get_feature_report(hid_device *device, unsigned char *data, size_t length)
{
    if (!device)
        return -1;
        
#ifdef _WIN32
    BOOL res;
    
    // Make sure the device handle is valid
    if (device->device_handle == INVALID_HANDLE_VALUE)
        return -1;
        
    res = HidD_GetFeature(device->device_handle, data, (DWORD)length);
    if (!res) {
        return -1;
    }
    
    // Windows doesn't give us the actual number of bytes read, so return the length
    return (int)length;
#else
    // For non-Windows platforms
    return -1;
#endif
}

int hid_send_feature_report(hid_device *device, const unsigned char *data, size_t length)
{
    if (!device)
        return -1;
        
#ifdef _WIN32
    BOOL res;
    
    // Make sure the device handle is valid
    if (device->device_handle == INVALID_HANDLE_VALUE)
        return -1;
        
    res = HidD_SetFeature(device->device_handle, (PVOID)data, (DWORD)length);
    if (!res) {
        return -1;
    }
    
    // Windows doesn't give us the actual number of bytes written, so return the length
    return (int)length;
#else
    // For non-Windows platforms
    return -1;
#endif
}

int hid_get_manufacturer_string(hid_device *device, wchar_t *string, size_t maxlen)
{
    if (!device)
        return -1;
        
#ifdef _WIN32
    BOOL res;
    
    // Make sure the device handle is valid
    if (device->device_handle == INVALID_HANDLE_VALUE)
        return -1;
        
    res = HidD_GetManufacturerString(device->device_handle, string, (ULONG)(maxlen * sizeof(wchar_t)));
    if (!res) {
        return -1;
    }
    
    return 0;
#else
    // For non-Windows platforms
    return -1;
#endif
}

int hid_get_product_string(hid_device *device, wchar_t *string, size_t maxlen)
{
    if (!device)
        return -1;
        
#ifdef _WIN32
    BOOL res;
    
    // Make sure the device handle is valid
    if (device->device_handle == INVALID_HANDLE_VALUE)
        return -1;
        
    res = HidD_GetProductString(device->device_handle, string, (ULONG)(maxlen * sizeof(wchar_t)));
    if (!res) {
        return -1;
    }
    
    return 0;
#else
    // For non-Windows platforms
    return -1;
#endif
}

int hid_get_serial_number_string(hid_device *device, wchar_t *string, size_t maxlen)
{
    if (!device)
        return -1;
        
#ifdef _WIN32
    BOOL res;
    
    // Make sure the device handle is valid
    if (device->device_handle == INVALID_HANDLE_VALUE)
        return -1;
        
    res = HidD_GetSerialNumberString(device->device_handle, string, (ULONG)(maxlen * sizeof(wchar_t)));
    if (!res) {
        return -1;
    }
    
    return 0;
#else
    // For non-Windows platforms
    return -1;
#endif
}

int hid_get_indexed_string(hid_device *device, int string_index, wchar_t *string, size_t maxlen)
{
    if (!device)
        return -1;
        
#ifdef _WIN32
    BOOL res;
    
    // Make sure the device handle is valid
    if (device->device_handle == INVALID_HANDLE_VALUE)
        return -1;
        
    res = HidD_GetIndexedString(device->device_handle, string_index, string, (ULONG)(maxlen * sizeof(wchar_t)));
    if (!res) {
        return -1;
    }
    
    return 0;
#else
    // For non-Windows platforms
    return -1;
#endif
}

const wchar_t* hid_error(hid_device *device)
{
    // No specific error messages implemented yet
    return L"Unknown error";
}