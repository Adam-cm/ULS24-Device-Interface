# Makefile for compiling ULS24 library on Linux

# Compiler settings
CXX = g++
CXXFLAGS = -std=c++14 -fPIC -Wall -I. -DLINUX

# Target library name
LIB_NAME = ULSLIB.so
SAMPLE_NAME = uls24_sample

# Source files
SRC_FILES = TestCl/HidMgr.cpp TestCl/InterfaceObj.cpp TestCl/TrimReader.cpp TestCl/hidapi.cpp TestCl/InterfaceWrapper.cpp

# Object files
OBJ_FILES = $(SRC_FILES:.cpp=.o)

# Libraries to link
LIBS = -lhidapi-hidraw -lpthread -lrt

# Default target
all: $(LIB_NAME) $(SAMPLE_NAME)

# Rule to build the shared library
$(LIB_NAME): $(OBJ_FILES)
	$(CXX) -shared -o $@ $^ $(LIBS)

# Rule to build the sample program
$(SAMPLE_NAME): TestCl/c_sample.cpp $(LIB_NAME)
	$(CXX) $(CXXFLAGS) -o $@ $< -L. -lULSLIB $(LIBS) -Wl,-rpath,.

# Rule to compile source files
%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Clean target
clean:
	rm -f $(OBJ_FILES) $(LIB_NAME) $(SAMPLE_NAME)

# Install target
install: $(LIB_NAME)
	cp $(LIB_NAME) /usr/local/lib/
	ldconfig

# Install dependencies
deps:
	apt-get update
	apt-get install -y libhidapi-dev

.PHONY: all clean install deps.PHONY: all clean install deps