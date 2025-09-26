#!/bin/bash

# Build script for ULS24 library on Linux
set -e # Exit immediately if a command fails

# Colors for console output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Building ULS24 library for Linux${NC}"

# Check for required commands
if ! command -v g++ &> /dev/null; then
    echo -e "${RED}Error: g++ is not installed. Please install build-essential package.${NC}"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install build-essential"
    exit 1
fi

# Check for required packages
if ! command -v pkg-config &> /dev/null; then
    echo -e "${YELLOW}Warning: pkg-config is not installed. Installing...${NC}"
    sudo apt-get update
    sudo apt-get install -y pkg-config
fi

# Check for hidapi development package
if ! pkg-config --exists hidapi-hidraw || ! pkg-config --exists hidapi-libusb; then
    echo -e "${YELLOW}Warning: libhidapi-dev is not installed. Installing...${NC}"
    sudo apt-get update
    sudo apt-get install -y libhidapi-dev
fi

# Compile the library
echo -e "${GREEN}Compiling ULS24 library...${NC}"
make clean
make

# Check if compilation succeeded
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Compilation successful!${NC}"
    echo "Library created: ULSLIB.so"
    
    # Verify the library was built
    if [ -f "ULSLIB.so" ]; then
        echo -e "${GREEN}Library file exists.${NC}"
        
        # Check if the sample program was built
        if [ -f "uls24_sample" ]; then
            echo -e "${GREEN}Sample program built successfully.${NC}"
        else
            echo -e "${YELLOW}Note: Sample program was not built.${NC}"
        fi
    else
        echo -e "${RED}Error: Library file not found.${NC}"
        exit 1
    fi
else
    echo -e "${RED}Compilation failed!${NC}"
    
    # Suggest some common solutions
    echo -e "${YELLOW}Possible solutions:${NC}"
    echo "1. Make sure you have all development packages installed:"
    echo "   sudo apt-get update"
    echo "   sudo apt-get install build-essential libhidapi-dev"
    echo "2. Check for any compiler errors above and fix them."
    echo "3. Ensure you have the right permissions to write to the current directory."
    exit 1
fi

# Optionally install the library
read -p "Do you want to install the library to /usr/local/lib? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo make install
    echo -e "${GREEN}Library installed successfully!${NC}"
    echo "You may need to run 'sudo ldconfig' to update the shared library cache."
fi

echo -e "${GREEN}Done.${NC}"