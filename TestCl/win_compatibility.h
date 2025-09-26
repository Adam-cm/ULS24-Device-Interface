#ifndef WIN_COMPATIBILITY_H
#define WIN_COMPATIBILITY_H

// Compatibility header for Windows to Linux conversion

#include <string>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <fstream>

// Type definitions
typedef unsigned char BYTE;
typedef unsigned int UINT;
typedef unsigned short WORD;
typedef unsigned int DWORD;
typedef int BOOL;
typedef char* LPTSTR;
typedef const char* LPCTSTR;
typedef int16_t _int16;

// Windows constants
#define TRUE 1
#define FALSE 0
#define INVALID_HANDLE_VALUE (-1)

// Redefine CString as std::string
typedef std::string CString;

// String conversion functions
#define _tstof atof
#define _tstoi atoi
#define _tcstoul strtoul

// Redefine other Windows-specific functions
inline double round(double x) {
    return std::round(x);
}

// Simple CFile replacement
class CFile {
public:
    enum OpenMode {
        modeRead = 1
    };

    CFile() : m_file(nullptr), m_isOpen(false) {}
    ~CFile() { Close(); }

    BOOL Open(const char* filename, int mode) {
        if (m_isOpen) Close();
        
        m_file = fopen(filename, "rb");
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

    size_t Read(void* buffer, size_t count) {
        if (!m_file) return 0;
        return fread(buffer, 1, count, m_file);
    }

    long GetLength() {
        if (!m_file) return 0;
        
        long currentPos = ftell(m_file);
        fseek(m_file, 0, SEEK_END);
        long size = ftell(m_file);
        fseek(m_file, currentPos, SEEK_SET);
        return size;
    }

    operator bool() const {
        return m_isOpen;
    }

private:
    FILE* m_file;
    bool m_isOpen;
};

// String extension functions to replace CString methods
namespace std_string_extensions {
    inline void TrimLeft(std::string& str, const std::string& chars) {
        str.erase(0, str.find_first_not_of(chars));
    }

    inline void TrimRight(std::string& str, const std::string& chars) {
        str.erase(str.find_last_not_of(chars) + 1);
    }

    inline int FindOneOf(const std::string& str, const std::string& chars) {
        size_t pos = str.find_first_of(chars);
        return (pos == std::string::npos) ? -1 : (int)pos;
    }

    inline std::string Mid(const std::string& str, int start, int count = -1) {
        if (start < 0) start = 0;
        if (count < 0 || (start + count) > (int)str.length()) {
            return str.substr(start);
        }
        return str.substr(start, count);
    }

    inline void Empty(std::string& str) {
        str.clear();
    }

    inline void MakeLower(std::string& str) {
        for (auto& ch : str) {
            ch = tolower(ch);
        }
    }

    inline int Find(const std::string& str, const std::string& target) {
        size_t pos = str.find(target);
        return (pos == std::string::npos) ? -1 : (int)pos;
    }

    inline int Compare(const std::string& str, const std::string& other) {
        return str.compare(other);
    }

    inline int GetLength(const std::string& str) {
        return (int)str.length();
    }
}

// Add extensions to CString (std::string)
inline void CString::TrimLeft(const std::string& chars) {
    std_string_extensions::TrimLeft(*this, chars);
}

inline void CString::TrimRight(const std::string& chars) {
    std_string_extensions::TrimRight(*this, chars);
}

inline int CString::FindOneOf(const std::string& chars) const {
    return std_string_extensions::FindOneOf(*this, chars);
}

inline CString CString::Mid(int start, int count = -1) const {
    return std_string_extensions::Mid(*this, start, count);
}

inline void CString::Empty() {
    std_string_extensions::Empty(*this);
}

inline void CString::MakeLower() {
    std_string_extensions::MakeLower(*this);
}

inline int CString::Find(const CString& target) const {
    return std_string_extensions::Find(*this, target);
}

inline int CString::Compare(const CString& other) const {
    return std_string_extensions::Compare(*this, other);
}

inline int CString::GetLength() const {
    return std_string_extensions::GetLength(*this);
}

// TCHAR definitions for Linux
typedef char TCHAR;
#define _T(x) x

#endif // WIN_COMPATIBILITY_H