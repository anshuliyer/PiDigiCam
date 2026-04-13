#!/bin/bash

# PiDigiCam Build Dependencies Manager
# Installs all required dependencies for building across x86 and armv8 architectures

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Determine the target architecture
ARCH="${1:-native}"

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_step() {
    echo -e "${YELLOW}→ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_os() {
    if [[ ! "$OSTYPE" =~ ^linux ]]; then
        print_error "This script is designed for Linux systems"
        echo "Detected OS: $OSTYPE"
        exit 1
    fi
    print_success "Running on Linux"
}

detect_package_manager() {
    if command -v apt &> /dev/null; then
        PACKAGE_MANAGER="apt"
        INSTALL_CMD="sudo apt-get install -y"
        UPDATE_CMD="sudo apt-get update"
    elif command -v yum &> /dev/null; then
        PACKAGE_MANAGER="yum"
        INSTALL_CMD="sudo yum install -y"
        UPDATE_CMD="sudo yum update"
    elif command -v pacman &> /dev/null; then
        PACKAGE_MANAGER="pacman"
        INSTALL_CMD="sudo pacman -S --noconfirm"
        UPDATE_CMD="sudo pacman -Sy"
    else
        print_error "No supported package manager found (apt, yum, or pacman)"
        exit 1
    fi
    print_success "Package manager: $PACKAGE_MANAGER"
}

install_deps() {
    local packages=("$@")
    local missing_packages=()

    print_step "Checking required packages..."
    for pkg in "${packages[@]}"; do
        if ! command -v "$pkg" &> /dev/null && ! dpkg -l | grep -q "^ii  $pkg"; then
            missing_packages+=("$pkg")
        fi
    done

    if [ ${#missing_packages[@]} -eq 0 ]; then
        print_success "All required packages already installed"
        return 0
    fi

    print_step "Installing missing packages: ${missing_packages[*]}"
    $UPDATE_CMD
    $INSTALL_CMD "${missing_packages[@]}"
    print_success "Packages installed"
}

install_native_deps() {
    print_header "Installing Core Build Dependencies (Native)"

    local core_deps=(
        "gcc"
        "make"
        "python3"
        "python3-pip"
        "python3-venv"
        "git"
    )

    install_deps "${core_deps[@]}"
    
    print_step "Verifying core tools..."
    command -v gcc && print_success "GCC: $(gcc --version | head -1)"
    command -v make && print_success "Make: $(make --version | head -1)"
    command -v python3 && print_success "Python3: $(python3 --version)"
}

install_x86_deps() {
    print_header "Installing x86 Cross-Compilation Dependencies"

    # For x86 32-bit compilation on 64-bit systems
    local x86_deps=(
        "gcc"
        "make"
        "gcc-multilib"  # For 32-bit compilation support
        "libc6-dev-i386" # 32-bit libc dev
    )

    install_deps "${x86_deps[@]}"

    # Check if 32-bit compilation is supported
    print_step "Testing 32-bit compilation..."
    if gcc -m32 --version &> /dev/null; then
        print_success "32-bit compilation support available"
    else
        print_error "32-bit compilation support not available"
        echo "Try installing: gcc-multilib libc6-dev-i386"
        return 1
    fi
}

install_armv8_deps() {
    print_header "Installing ARMv8 Cross-Compilation Dependencies"

    # For ARM 64-bit (aarch64) cross-compilation
    local armv8_deps=(
        "gcc"
        "make"
        "clang"
        "binutils-aarch64-linux-gnu"
        "gcc-aarch64-linux-gnu"
    )

    install_deps "${armv8_deps[@]}"

    # Check if ARM compilation is supported
    print_step "Testing ARMv8 cross-compilation..."
    if clang --target=aarch64-linux-gnu --version &> /dev/null; then
        print_success "ARMv8 cross-compilation support available"
    elif aarch64-linux-gnu-gcc --version &> /dev/null; then
        print_success "ARMv8 cross-compilation support available (gcc)"
    else
        print_error "ARMv8 cross-compilation support not available"
        echo "Try installing: gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu"
        return 1
    fi
}

install_python_deps() {
    print_header "Installing Python Dependencies"

    if [ ! -f "requirements.txt" ] && [ ! -f "processing/requirements.txt" ]; then
        print_step "No Python requirements found, creating minimal Python environment setup"
        echo "Pillow>=10.0.0" > requirements-dev.txt
        echo "matplotlib>=3.7.0" >> requirements-dev.txt
        echo "numpy>=1.24.0" >> requirements-dev.txt
        print_success "Created requirements-dev.txt"
    fi

    print_step "Installing recommend Python packages..."
    set +e  # Don't exit on pip install failure
    if command -v pip3; then
        pip3 install --upgrade pip
        pip3 install Pillow matplotlib numpy
        print_success "Python packages installed (optional: Pillow, matplotlib, numpy)"
    fi
    set -e
}

install_all_deps() {
    local archs=("$@")
    if [ ${#archs[@]} -eq 0 ]; then
        archs=("native")
    fi

    for arch in "${archs[@]}"; do
        case "$arch" in
            native)
                install_native_deps
                ;;
            x86)
                install_x86_deps
                ;;
            armv8)
                install_armv8_deps
                ;;
            all)
                install_native_deps
                install_x86_deps
                install_armv8_deps
                ;;
            *)
                print_error "Unknown architecture: $arch"
                echo "Valid options: native, x86, armv8, all"
                exit 1
                ;;
        esac
        [ $? -ne 0 ] && print_error "Installation for $arch failed"
    done
}

print_summary() {
    print_header "Dependency Installation Summary"
    
    echo -e "${GREEN}Ready to build for:${NC}"
    if command -v gcc &> /dev/null; then
        echo "  ✓ Native ($(gcc -v 2>&1 | tail -1))"
    fi
    if gcc -m32 --version &> /dev/null 2>&1; then
        echo "  ✓ x86 32-bit"
    else
        echo "  ✗ x86 32-bit (requires gcc-multilib libc6-dev-i386)"
    fi
    if clang --target=aarch64-linux-gnu --version &> /dev/null 2>&1 || \
       aarch64-linux-gnu-gcc --version &> /dev/null 2>&1; then
        echo "  ✓ ARMv8 64-bit"
    else
        echo "  ✗ ARMv8 64-bit (requires gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu)"
    fi
    
    echo ""
    echo -e "${GREEN}Build commands:${NC}"
    echo "  make all          # Build native binary"
    echo "  make x86          # Build x86 32-bit"
    echo "  make armv8        # Build ARMv8 64-bit"
    echo ""
}

show_usage() {
    cat << EOF
PiDigiCam Build Dependencies Manager

Usage: $0 [ARCHITECTURE|all]

Arguments:
  native (default)  Install native build dependencies
  x86               Install x86 cross-compilation dependencies
  armv8             Install ARMv8 cross-compilation dependencies
  all               Install all build dependencies

Examples:
  $0                    # Install native dependencies only
  $0 armv8              # Install ARMv8 cross-compilation
  $0 all                # Install all dependencies (native + x86 + armv8)
  $0 native x86 armv8   # Install multiple specific architectures

Environment:
  Supported distributions: Debian/Ubuntu (apt), RHEL/CentOS (yum), Arch (pacman)
  
Dependencies by architecture:
  Native:  gcc, make, python3, git
  x86:     gcc-multilib, libc6-dev-i386 (for 32-bit cross-compilation)
  armv8:   clang, gcc-aarch64-linux-gnu, binutils-aarch64-linux-gnu

EOF
}

main() {
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_usage
        exit 0
    fi

    print_header "PiDigiCam - Build Dependency Manager"
    echo "Architecture: ${ARCH:-native}"
    echo ""

    check_os
    detect_package_manager
    
    if [ $# -eq 0 ]; then
        install_all_deps "native"
    elif [ "$1" = "all" ]; then
        install_all_deps "native" "x86" "armv8"
    else
        install_all_deps "$@"
    fi

    install_python_deps

    print_summary

    print_header "Installation Complete!"
    echo -e "${GREEN}Next steps:${NC}"
    echo "1. Navigate to firmware/processing/C/build/"
    echo "2. Run: make $ARCH"
    echo "3. Test with: python ../../host/python/test/emulator.py"
}

main "$@"
