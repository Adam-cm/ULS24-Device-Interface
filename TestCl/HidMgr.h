// Copyright 2014-2017, Anitoa Systems, LLC
// All rights reserved

#pragma once

#include <wtypes.h>
#include <initguid.h>
#include "hidapi.h"

#define TxNum 64		// the number of the buffer for sent data to HID
#define RxNum 64		// the number of the buffer for received data from HID

#define HIDREPORTNUM 64+1		//	HID report num bytes
#define HIDBUFSIZE 12

#define GetCmd		0x02			// return 0x02 command 
#define ReadCmd		0x04			// Read command

// Function declarations
bool FindTheHID();
void CloseHandles();
void DisplayInputReport();
void DisplayReceivedData(char ReceivedByte);
void GetDeviceCapabilities();
void ReadAndWriteToDevice();
void ReadHIDInputReport();
void WriteHIDOutputReport();
