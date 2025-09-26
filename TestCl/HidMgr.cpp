// Copyright 2014-2017, Anitoa Systems, LLC
// All rights reserved

#include "stdafx.h"

#include "HidMgr.h"
#include "TrimReader.h"

//Application global variables 
char                InputReport[HIDREPORTNUM];
char                OutputReport[HIDREPORTNUM];
hid_device*         DeviceHandle = NULL;
bool                MyDeviceDetected = FALSE; 
CString             MyDevicePathName;

extern HWND         hWnd;				

//These are the vendor and product IDs to look for.
int VendorID = 0x0483;
int ProductID = 0x5750;

BYTE TxData[TxNum+1];      // the buffer of sent data to HID
BYTE RxData[RxNum+1];      // the buffer of received data from HID

BOOL g_DeviceDetected = false;
BOOL Continue_Flag = false;
BOOL ee_continue = true;

int chan_num = 1;

bool FindTheHID()
{
    //Use hidapi to find a device with specified Vendor ID and Product ID.
    struct hid_device_info *devs, *cur_dev;
    
    // Initialize hidapi
    hid_init();
    
    // Enumerate HID devices matching our VendorID and ProductID
    devs = hid_enumerate(VendorID, ProductID);
    cur_dev = devs;
    
    // Reset device detection flag
    MyDeviceDetected = FALSE;
    
    // Loop through all matching devices
    while (cur_dev) {
        // We found a device with matching VID and PID
        DeviceHandle = hid_open_path(cur_dev->path);
        
        if (DeviceHandle) {
            // Device was successfully opened
            MyDeviceDetected = TRUE;
            MyDevicePathName = cur_dev->path;
            
            // Get the device capabilities (we'll use default hidapi values)
            GetDeviceCapabilities();
            
            // Success, break out of the loop
            break;
        }
        
        // Try the next device
        cur_dev = cur_dev->next;
    }
    
    // Free the enumeration list
    hid_free_enumeration(devs);
    
    if (MyDeviceDetected) {
        g_DeviceDetected = true;
    } else {
        g_DeviceDetected = false;
    }
    
    return MyDeviceDetected;
}

void CloseHandles()
{
    //Close the device handle
    if (DeviceHandle != NULL) {
        hid_close(DeviceHandle);
        DeviceHandle = NULL;
    }
}

void DisplayInputReport()
{
    // This is a stub function that doesn't do anything in this version
    // Kept for compatibility with existing code
}

void DisplayReceivedData(char ReceivedByte)
{
    // This is a stub function that doesn't do anything in this version
    // Kept for compatibility with existing code
}

void GetDeviceCapabilities()
{
    // With hidapi we don't need to explicitly get capabilities as they're
    // handled internally. This function is kept as a stub for compatibility.
}

void ReadAndWriteToDevice()
{
    //If necessary, find the device and learn its capabilities.
    //Then send a report and request a report.

    //If the device hasn't been detected already, look for it.
    if (MyDeviceDetected==FALSE) {
        MyDeviceDetected=FindTheHID();
    }

    // Do nothing if the device isn't detected.
    if (MyDeviceDetected==TRUE) {
        //Write a report to the device.
        WriteHIDOutputReport();

        //Read a report from the device.
        ReadHIDInputReport();
    } 
}

void ReadHIDInputReport()
{
    // Retrieve an Input report from the device using hidapi
    
    int result;
    
    // The first byte is the report number (0)
    InputReport[0] = 0;
    
    if (DeviceHandle != NULL) {
        // Read with timeout (equivalent to previous WaitForSingleObject timeout)
        result = hid_read_timeout(DeviceHandle, (unsigned char*)InputReport, HIDREPORTNUM, 264000);
        
        if (result > 0) {
            // Successful read
            
            // Copy the data to the RxData buffer (skip the report ID byte)
            for (int k = 0; k < HIDREPORTNUM - 1; k++) {
                RxData[k] = InputReport[k + 1];
            }
            
            BYTE rCmd = RxData[2];
            BYTE rType = RxData[4];
            
            switch (rCmd) {
                case GetCmd:
                    if ((rType == 0x01) || (rType == 0x02) || (rType == 0x12) || 
                        (rType == 0x22) || (rType == 0x32) || (rType == 0x03)) {
                        
                        chan_num = (rType & 0xF0) / 16 + 1;
                        
                        // F1 Code detection
                        if ((RxData[5] == 0x0b) || (RxData[5] == 0xf1)) {
                            Continue_Flag = false;
                            if (RxData[5] == 0xf1) {
                                return;
                            }
                        } else {
                            Continue_Flag = true;
                        }
                    } else {
                        if ((rType == 0x07) || (rType == 0x08) || (rType == 0x0b)) {
                            if (RxData[5] == 0x17)
                                Continue_Flag = false;
                            else
                                Continue_Flag = true;
                        }
                    }
                    break;
            }
        } else if (result == 0) {
            // Timeout occurred
            CloseHandles();
            MyDeviceDetected = FALSE;
        } else {
            // Error occurred
            CloseHandles();
            MyDeviceDetected = FALSE;
        }
    }
    
    // Display the report data (optional)
    DisplayInputReport();
}

void WriteHIDOutputReport()
{
    // Send a report to the device using hidapi
    
    // Set the first byte to the report number (0)
    OutputReport[0] = 0;
    
    // Copy the data from TxData to OutputReport (skip the report ID byte)
    for (int i = 1; i < TxNum + 1; i++) {
        OutputReport[i] = TxData[i - 1];
    }
    
    if (DeviceHandle != NULL) {
        int result = hid_write(DeviceHandle, (unsigned char*)OutputReport, HIDREPORTNUM);
        
        if (result < 0) {
            // Write failed
            CloseHandles();
            MyDeviceDetected = FALSE;
        }
    }
}