#ifndef WIN_COMPATIBILITY_H
#define WIN_COMPATIBILITY_H

// Compatibility header for Windows to Linux conversion
#define LINUX 1

#include <string>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <memory>
#include <cstring>
#include <algorithm>

// Type definitions
typedef unsigned char BYTE;
typedef unsigned int UINT;
typedef unsigned short WORD;
typedef unsigned int DWORD;
typedef int BOOL;
typedef char* LPTSTR;
typedef const char* LPCTSTR;
typedef int16_t _int16;
typedef unsigned long ULONG;
typedef void* PVOID;
typedef void* HANDLE;
typedef long LONG;

// Windows constants
#define TRUE 1
#define FALSE 0
#define INVALID_HANDLE_VALUE ((HANDLE)-1)

// Define TCHAR for Linux
#ifdef _UNICODE
    typedef wchar_t TCHAR;
    #define _T(x) L##x
    #define _tstof wcstof
    #define _tstoi wcstoi
    #define _tcstoul wcstoul
#else
    typedef char TCHAR;
    #define _T(x) x
    #define _tstof atof
    #define _tstoi atoi
    #define _tcstoul strtoul
#endif

// Redefine CString as std::string
class CString : public std::string {
public:
    // Constructors
    CString() : std::string() {}
    CString(const char* str) : std::string(str) {}
    CString(const std::string& str) : std::string(str) {}
    
    // CString-specific methods
    void TrimLeft(const std::string& chars = " \t\n\r\f\v") {
        this->erase(0, this->find_first_not_of(chars));
    }
    
    void TrimRight(const std::string& chars = " \t\n\r\f\v") {
        this->erase(this->find_last_not_of(chars) + 1);
    }
    
    int FindOneOf(const std::string& chars) const {
        size_t pos = this->find_first_of(chars);
        return (pos == std::string::npos) ? -1 : static_cast<int>(pos);
    }
    
    CString Mid(int start, int count = -1) const {
        if (start < 0) start = 0;
        if (start >= static_cast<int>(this->length())) return "";
        
        if (count < 0 || (start + count) > static_cast<int>(this->length())) {
            return this->substr(start);
        }
        return this->substr(start, count);
    }
    
    void Empty() {
        this->clear();
    }
    
    void MakeLower() {
        std::transform(this->begin(), this->end(), this->begin(),
                      [](unsigned char c){ return std::tolower(c); });
    }
    
    int Find(const CString& target) const {
        size_t pos = this->find(target);
        return (pos == std::string::npos) ? -1 : static_cast<int>(pos);
    }
    
    int Compare(const CString& other) const {
        return this->compare(other);
    }
    
    int GetLength() const {
        return static_cast<int>(this->length());
    }
    
    operator LPCTSTR() const {
        return this->c_str();
    }
};

// Simple CFile replacement
class CFile {
public:
    enum OpenMode {
        modeRead = 1,
        modeWrite = 2,
        modeReadWrite = 3,
        modeCreate = 4
    };

    CFile() : m_file(nullptr), m_isOpen(false) {}
    ~CFile() { Close(); }

    BOOL Open(const char* filename, int mode) {
        if (m_isOpen) Close();
        
        const char* openMode = "rb";
        if (mode & modeWrite) {
            if (mode & modeRead) {
                openMode = "r+b";
            } else {
                openMode = "wb";
            }
        }
        if (mode & modeCreate) {
            openMode = "wb";
        }
        
        m_file = fopen(filename, openMode);
        m_isOpen = (m_file != nullptr);
        return m_isOpen;
    }

    void Close() {
        if (m_file) {
            fclose(m_file);
            m_file = nullptr;
        }
        m_isOpen = false;
    }

    UINT Read(void* buffer, UINT count) {
        if (!m_file) return 0;
        return static_cast<UINT>(fread(buffer, 1, count, m_file));
    }

    DWORD GetLength() {
        if (!m_file) return 0;
        
        long currentPos = ftell(m_file);
        fseek(m_file, 0, SEEK_END);
        long size = ftell(m_file);
        fseek(m_file, currentPos, SEEK_SET);
        return static_cast<DWORD>(size);
    }

    operator bool() const {
        return m_isOpen;
    }

private:
    FILE* m_file;
    bool m_isOpen;
};

// Sleep function compatibility
#include <chrono>
#include <thread>

inline void Sleep(unsigned int milliseconds) {
    std::this_thread::sleep_for(std::chrono::milliseconds(milliseconds));
}

// Ensure round is available
using std::round;

#endif // WIN_COMPATIBILITY_H