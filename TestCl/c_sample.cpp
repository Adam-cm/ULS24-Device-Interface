#include <stdio.h>
#include <stdlib.h>

// ULS24 C Interface declarations
extern "C" {
    int ULS24_Initialize();
    void ULS24_Cleanup();
    int ULS24_SelectChannel(int channel);
    int ULS24_SetIntegrationTime(int time_ms);
    int ULS24_SetGainMode(int gain);
    int ULS24_CaptureFrame(int channel);
    int ULS24_GetFrameData(int* frame_data, int* frame_size);
    int ULS24_Reset();
}

int main() {
    printf("ULS24 C Interface Sample\n");
    
    // Initialize the device
    printf("Initializing device...\n");
    if (!ULS24_Initialize()) {
        printf("Failed to initialize device\n");
        return 1;
    }
    
    printf("Device initialized successfully\n");
    
    // Set parameters
    ULS24_SelectChannel(1);
    ULS24_SetIntegrationTime(30);
    ULS24_SetGainMode(1);
    
    // Capture frame
    printf("Capturing frame from channel 1...\n");
    if (ULS24_CaptureFrame(1)) {
        printf("Frame captured successfully\n");
        
        // Get frame data
        int frame_size;
        int frame_data[24 * 24]; // Maximum size
        
        if (ULS24_GetFrameData(frame_data, &frame_size)) {
            printf("Frame data (%dx%d):\n", frame_size, frame_size);
            
            // Print the frame data
            for (int i = 0; i < frame_size; i++) {
                for (int j = 0; j < frame_size; j++) {
                    printf("%d ", frame_data[i * frame_size + j]);
                }
                printf("\n");
            }
        }
    }
    else {
        printf("Failed to capture frame\n");
    }
    
    // Cleanup
    ULS24_Cleanup();
    printf("Done\n");
    
    return 0;
}