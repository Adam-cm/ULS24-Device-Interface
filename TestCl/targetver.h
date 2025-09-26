#pragma once

// The following macros define the minimum required platform.
// The minimum required platform is the earliest version of Windows, Internet Explorer etc. that has the necessary features to run 
// your application. The macros work by enabling all features available on platform versions up to and including the version specified.

#ifdef _WIN32
// Include SDKDDKVer.h to define Windows platform specific macros
#include <SDKDDKVer.h>
#else
// For Linux and other platforms, we don't need these Windows-specific defines
#endif
