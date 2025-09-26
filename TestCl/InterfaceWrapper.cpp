#include <stdio.h>
#include <stdlib.h>
#include "HidMgr.h"
#include "InterfaceObj.h"

// Exported C interface for use in other languages
extern "C" {

// Global interface object
static CInterfaceObject* g_InterfaceObj = nullptr;

// Initialize the device interface
int ULS24_Initialize() {
    if (g_InterfaceObj) {
        delete g_InterfaceObj;
    }
    
    g_InterfaceObj = new CInterfaceObject();
    
    // Find the device
    bool deviceFound = FindTheHID();
    if (deviceFound) {
        g_InterfaceObj->ReadTrimData();
        g_InterfaceObj->ResetTrim();
        
        g_InterfaceObj->SelSensor(1);
        g_InterfaceObj->SetIntTime(30);
        g_InterfaceObj->SetGainMode(1);
        
        return 1;
    }
    
    return 0;
}

// Close the device interface
void ULS24_Cleanup() {
    if (g_InterfaceObj) {
        delete g_InterfaceObj;
        g_InterfaceObj = nullptr;
    }
    
    CloseHandles();
}

// Select sensor channel (1-4)
int ULS24_SelectChannel(int channel) {
    if (!g_InterfaceObj || channel < 1 || channel > 4) {
        return 0;
    }
    
    g_InterfaceObj->SelSensor(channel);
    return 1;
}

// Set integration time in milliseconds
int ULS24_SetIntegrationTime(int time_ms) {
    if (!g_InterfaceObj || time_ms < 1 || time_ms > 66000) {
        return 0;
    }
    
    g_InterfaceObj->SetIntTime(time_ms);
    return 1;
}

// Set gain mode (0=high, 1=low)
int ULS24_SetGainMode(int gain) {
    if (!g_InterfaceObj || (gain != 0 && gain != 1)) {
        return 0;
    }
    
    g_InterfaceObj->SetGainMode(gain);
    return 1;
}

// Capture frame from specified channel
int ULS24_CaptureFrame(int channel) {
    if (!g_InterfaceObj || channel < 1 || channel > 4) {
        return 0;
    }
    
    int result = g_InterfaceObj->CaptureFrame12(channel);
    return (result == 0) ? 1 : 0;
}

// Get frame data
int ULS24_GetFrameData(int* frame_data, int* frame_size) {
    if (!g_InterfaceObj || !frame_data || !frame_size) {
        return 0;
    }
    
    extern int frame_size; // Global from InterfaceObj.cpp
    *frame_size = frame_size ? 24 : 12;
    
    int dim = *frame_size;
    for (int i = 0; i < dim; i++) {
        for (int j = 0; j < dim; j++) {
            frame_data[i * dim + j] = g_InterfaceObj->frame_data[i][j];
        }
    }
    
    return 1;
}

// Reset device connection
int ULS24_Reset() {
    bool deviceFound = FindTheHID();
    return deviceFound ? 1 : 0;
}

} // extern "C"