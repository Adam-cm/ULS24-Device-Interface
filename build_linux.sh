#!/bin/bash

# Build script for ULS24 library on Linux

# Check for required packages
if ! dpkg -l | grep -q libhidapi-dev; then
    echo "Installing libhidapi-dev..."
    sudo apt-get update
    sudo apt-get install -y libhidapi-dev
fi

# Compile the library
echo "Compiling ULS24 library..."
make clean
make

# Check if compilation succeeded
if [ $? -eq 0 ]; then
    echo "Compilation successful!"
    echo "Library created: ULSLIB.so"
else
    echo "Compilation failed!"
    exit 1
fi

# Optionally install the library
read -p "Do you want to install the library to /usr/local/lib? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo make install
    echo "Library installed successfully!"
fi

echo "Done."