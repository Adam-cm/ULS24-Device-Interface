#ifndef HIDAPI_H__
#define HIDAPI_H__

#include <wchar.h>

#ifdef __cplusplus
extern "C" {
#endif
		
struct hid_device_;
typedef struct hid_device_ hid_device;

struct hid_device_info {
	/** Platform-specific device path */
	char *path;
	/** Device Vendor ID */
	unsigned short vendor_id;
	/** Device Product ID */
	unsigned short product_id;
	/** Serial Number */
	wchar_t *serial_number;
	/** Device Release Number in binary-coded decimal,
		also known as Device Version Number */
	unsigned short release_number;
	/** Manufacturer String */
	wchar_t *manufacturer_string;
	/** Product string */
	wchar_t *product_string;
	/** Usage Page for this Device/Interface
		(Windows/Mac only) */
	unsigned short usage_page;
	/** Usage for this Device/Interface
		(Windows/Mac only) */
	unsigned short usage;
	/** The USB interface which this logical device
		represents (Linux/libusb only) */
	int interface_number;
	/** Pointer to the next device */
	struct hid_device_info *next;
};
	
/** Enumerate the HID Devices.
    This function returns a linked list of all the HID devices
    attached to the system which match vendor_id and product_id.
    If vendor_id is set to 0 then any vendor matches.
    If product_id is set to 0 then any product matches.
    If vendor_id and product_id are both set to 0, then
    all HID devices will be returned.
    @param vendor_id The Vendor ID (VID) of the types of device to open.
    @param product_id The Product ID (PID) of the types of device to open.
    @returns
        a pointer to a linked list of type struct hid_device_info,
        containing information about the HID devices attached to the system,
        or NULL in the case of failure. Free this linked list by calling hid_free_enumeration().
*/
struct hid_device_info * hid_enumerate(unsigned short vendor_id, unsigned short product_id);
	
/** Free an enumeration Linked List
    This function frees a linked list created by hid_enumerate().
    @param devs Pointer to a list of struct_device returned from hid_enumerate().
*/
void  hid_free_enumeration(struct hid_device_info *devs);

/** Open a HID device using a Vendor ID (VID), Product ID (PID) and optionally a serial number.
    If serial_number is NULL, the first device with the specified VID and PID is opened.
    @param vendor_id The Vendor ID (VID) of the device to open.
    @param product_id The Product ID (PID) of the device to open.
    @param serial_number The Serial Number of the device to open (Null-terminated string).
    @returns
        a pointer to a hid_device object on success or NULL on failure.
*/
hid_device * hid_open(unsigned short vendor_id, unsigned short product_id, const wchar_t *serial_number);

/** Open a HID device by its path name. The path name be determined by calling
    hid_enumerate(), or a platform-specific path name can be used (eg: /dev/hidraw0 on Linux).
    @param path The path name of the device to open
    @returns
        a pointer to a hid_device object on success or NULL on failure.
*/
hid_device * hid_open_path(const char *path);

/** Close a HID device.
    @param device A device handle returned from hid_open().
*/
void hid_close(hid_device *device);

/** Write an Output report to a HID device.
    The first byte of data[] must contain the Report ID. For
    devices which only support a single report, this must be set
    to 0x0. The remaining bytes contain the report data. Since
    the Report ID is mandatory, calls to hid_write() will always
    contain one more byte than the report contains. For example,
    if a hid report is 16 bytes long, 17 bytes must be passed to
    hid_write(), the Report ID (or 0x0, for devices with a
    single report), followed by the report data (16 bytes). In
    this example, the length passed in would be 17.
    hid_write() will send the data on the first OUT endpoint, if
    one exists. If it does not, it will send the data through
    the Control Endpoint (Endpoint 0).
    @param device A device handle returned from hid_open().
    @param data The data to send, including the report number as
        the first byte.
    @param length The length in bytes of the data to send.
    @returns
        the actual number of bytes written and -1 on error.
*/
int  hid_write(hid_device *device, const unsigned char *data, size_t length);

/** Read an Input report from a HID device with timeout.
    Input reports are returned to the host through the INTERRUPT IN endpoint.
    The first byte will contain the Report number if the device uses numbered reports.
    @param device A device handle returned from hid_open().
    @param data A buffer to put the read data into.
    @param length The number of bytes to read. For devices with multiple
        reports, make sure to read an extra byte for the report number.
    @param milliseconds timeout in milliseconds or -1 for blocking wait.
    @returns
        the actual number of bytes read and -1 on error. If no packet
        was available to be read within the timeout period, this function
        returns 0.
*/
int hid_read_timeout(hid_device *dev, unsigned char *data, size_t length, int milliseconds);

/** Read an Input report from a HID device.
    Input reports are returned to the host through the INTERRUPT IN endpoint.
    The first byte will contain the Report number if the device uses numbered reports.
    @param device A device handle returned from hid_open().
    @param data A buffer to put the read data into.
    @param length The number of bytes to read. For devices with
        multiple reports, make sure to read an extra byte for the
        report number.
    @returns
        the actual number of bytes read and -1 on error. If no
        packet was available to be read and the handle is in non-blocking mode,
        this function returns 0.
*/
int  hid_read(hid_device *device, unsigned char *data, size_t length);

/** Get a feature report from a HID device.
    Set the first byte of data[] to the Report ID of the report to be read.
    Make sure to allow space for this extra byte in data[].
    @param device A device handle returned from hid_open().
    @param data A buffer to put the read data into, including
        the Report ID. Set the first byte of data[] to the
        Report ID of the report to be read, or set it to zero
        if your device does not use numbered reports.
    @param length The number of bytes to read, including an
        extra byte for the report ID. The buffer can be longer
        than the actual report.
    @returns
        the number of bytes read plus one for the report ID (which is
        still in the first byte), or -1 on error.
*/
int  hid_get_feature_report(hid_device *device, unsigned char *data, size_t length);

/** Send a Feature report to the device.
    Feature reports are sent over the Control endpoint as a
    Set_Report transfer.  The first byte of data[] must contain the
    Report ID. For devices which only support a single report, this
    must be set to 0x0. The remaining bytes contain the report data.
    Since the Report ID is mandatory, calls to hid_send_feature_report()
    will always contain one more byte than the report contains. For
    example, if a hid report is 16 bytes long, 17 bytes must be passed to
    hid_send_feature_report(): the Report ID (or 0x0, for devices which
    do not use numbered reports), followed by the report data (16 bytes).
    In this example, the length passed in would be 17.
    @param device A device handle returned from hid_open().
    @param data The data to send, including the report number as
        the first byte.
    @param length The length in bytes of the data to send, including
        the report number.
    @returns
        the actual number of bytes written and -1 on error.
*/
int  hid_send_feature_report(hid_device *device, const unsigned char *data, size_t length);

/** Get The Manufacturer String from a HID device.
    @param device A device handle returned from hid_open().
    @param string A wide string buffer to put the data into.
    @param maxlen The length of the buffer in multiples of wchar_t.
    @returns
        0 on success and -1 on error.
*/
int  hid_get_manufacturer_string(hid_device *device, wchar_t *string, size_t maxlen);

/** Get The Product String from a HID device.
    @param device A device handle returned from hid_open().
    @param string A wide string buffer to put the data into.
    @param maxlen The length of the buffer in multiples of wchar_t.
    @returns
        0 on success and -1 on error.
*/
int  hid_get_product_string(hid_device *device, wchar_t *string, size_t maxlen);

/** Get The Serial Number String from a HID device.
    @param device A device handle returned from hid_open().
    @param string A wide string buffer to put the data into.
    @param maxlen The length of the buffer in multiples of wchar_t.
    @returns
        0 on success and -1 on error.
*/
int  hid_get_serial_number_string(hid_device *device, wchar_t *string, size_t maxlen);

/** Get a string from a HID device, based on its string index.
    @param device A device handle returned from hid_open().
    @param string_index The index of the string to get.
    @param string A wide string buffer to put the data into.
    @param maxlen The length of the buffer in multiples of wchar_t.
    @returns
        0 on success and -1 on error.
*/
int  hid_get_indexed_string(hid_device *device, int string_index, wchar_t *string, size_t maxlen);

/** Get a string describing the last error which occurred.
    @param device A device handle returned from hid_open().
    @returns
        a string containing the last error which occurred or NULL if no
        error has occurred.
*/
const wchar_t* hid_error(hid_device *device);

/** Initialize the HIDAPI library.
    This function initializes the HIDAPI library. Calling it is not
    strictly necessary, as it will be called automatically by
    hid_enumerate() and any of the hid_open_*() functions if it is
    needed.  This function should be called at the beginning of
    execution however, if there is a chance of HIDAPI handles
    being opened by different threads simultaneously.
    @returns
        0 on success and -1 on error.
*/
int hid_init(void);

/** Finalize the HIDAPI library.
    This function frees all of the static data associated with
    HIDAPI. It should be called at the end of execution to avoid
    memory leaks.
    @returns
        0 on success and -1 on error.
*/
int hid_exit(void);

#ifdef __cplusplus
}
#endif

#endif /* HIDAPI_H__ */