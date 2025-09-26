#!/bin/bash
# Script to push code to GitHub repository

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Pushing ULS24 code to GitHub repository${NC}"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install git and try again."
    exit 1
fi

# Add all files to git
echo -e "${GREEN}Adding files to git...${NC}"
git add TestCl/python_hid_wrapper.py
git add TestCl/example_script.py
git add TestCl/uls24_cli.py
git add TestCl/PYTHON_README.md
git add TestCl/hidapi.h
git add TestCl/hidapi.cpp
git add TestCl/win_compatibility.h
git add TestCl/InterfaceWrapper.cpp
git add TestCl/c_sample.cpp
git add Makefile
git add build_linux.sh
git add README.md

# Commit the changes
echo -e "${GREEN}Committing changes...${NC}"
git commit -m "Add Python interface and Linux compatibility for ULS24 device"

# Push to GitHub
echo -e "${GREEN}Pushing to GitHub...${NC}"
git push origin main

# Check if push was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Successfully pushed to GitHub!${NC}"
    echo "Your code is now available at: https://github.com/Deneb888/TestCI"
else
    echo -e "${YELLOW}Failed to push to GitHub.${NC}"
    echo "You may need to resolve conflicts or authenticate."
fi

echo "Done."