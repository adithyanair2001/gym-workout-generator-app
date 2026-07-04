"""
Cross-platform installer for llama-cpp-python.

Detects the current OS and hardware and runs the correct pip install
command with the right CMAKE_ARGS for GPU acceleration.

Usage:
    python install_llama.py            # auto-detect
    python install_llama.py --cpu      # force CPU-only (no GPU)
"""
import subprocess
import sys
import platform
import argparse

PACKAGE = "llama-cpp-python"
VERSION = ">=0.2.0"


def detect_backend():
    """Return (cmake_args, description) for the current platform."""
    system  = platform.system()     # Darwin | Linux | Windows
    machine = platform.machine()    # arm64 | x86_64 | AMD64

    if system == "Darwin":
        if machine == "arm64":
            # Apple Silicon — Metal GPU
            return "-DGGML_METAL=on", "macOS Apple Silicon (Metal GPU)"
        else:
            # Intel Mac — CPU only (no Metal on x86 Mac)
            return "", "macOS Intel (CPU only)"

    if system == "Linux":
        # Check for CUDA (nvidia-smi present and on PATH)
        try:
            subprocess.check_output(["nvidia-smi"], stderr=subprocess.DEVNULL)
            return "-DGGML_CUDA=on", "Linux with NVIDIA CUDA GPU"
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
        # Check for ROCm (AMD GPU)
        try:
            subprocess.check_output(["rocm-smi"], stderr=subprocess.DEVNULL)
            return "-DGGML_HIPBLAS=on", "Linux with AMD ROCm GPU"
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
        return "", "Linux (CPU only)"

    if system == "Windows":
        # Check for CUDA on Windows (nvidia-smi is in PATH when CUDA drivers are installed)
        try:
            subprocess.check_output("nvidia-smi", stderr=subprocess.DEVNULL, shell=True)
            return "-DGGML_CUDA=on", "Windows with NVIDIA CUDA GPU"
        except (FileNotFoundError, subprocess.CalledProcessError, OSError):
            pass
        return "", "Windows (CPU only)"

    return "", f"{system} (CPU only — unknown platform)"


def is_installed():
    """Return True if llama-cpp-python is already importable."""
    try:
        import importlib
        importlib.import_module("llama_cpp")
        return True
    except ImportError:
        return False


def main():
    parser = argparse.ArgumentParser(description="Install llama-cpp-python with correct GPU flags.")
    parser.add_argument("--cpu", action="store_true", help="Force CPU-only install (no GPU)")
    parser.add_argument("--reinstall", action="store_true", help="Reinstall even if already installed")
    args = parser.parse_args()

    print("=" * 60)
    print("  llama-cpp-python installer")
    print("=" * 60)

    if is_installed() and not args.reinstall:
        print("✅ llama-cpp-python is already installed.")
        print("   Run with --reinstall to force a reinstall.")
        return 0

    if args.cpu:
        cmake_args, description = "", "CPU only (forced)"
    else:
        cmake_args, description = detect_backend()

    print(f"\n🖥️  Detected platform : {platform.system()} {platform.machine()}")
    print(f"⚙️  Build target      : {description}")
    if cmake_args:
        print(f"🔧 CMAKE_ARGS        : {cmake_args}")
    else:
        print("🔧 CMAKE_ARGS        : (none — CPU build)")
    print()

    # Build the pip command
    pip_cmd = [sys.executable, "-m", "pip", "install",
               f"{PACKAGE}{VERSION}", "--no-cache-dir"]

    import os
    env = os.environ.copy()
    if cmake_args:
        env["CMAKE_ARGS"] = cmake_args

    print(f"Running: pip install {PACKAGE}{VERSION}")
    print("This may take several minutes while the package compiles from source...\n")

    result = subprocess.run(pip_cmd, env=env)

    if result.returncode == 0:
        print("\n✅ llama-cpp-python installed successfully.")
        print("   You can now use the GGUF tab in the web UI.")
    else:
        print("\n❌ Installation failed.")
        system = platform.system()
        if system == "Windows" and cmake_args == "-DGGML_CUDA=on":
            print("\n   Windows + CUDA build requirements:")
            print("   1. Install CUDA Toolkit 11.8 or 12.x from https://developer.nvidia.com/cuda-downloads")
            print("   2. Install Visual Studio Build Tools (C++ workload) from https://visualstudio.microsoft.com/downloads/")
            print("   3. Reopen your terminal and retry: python install_llama.py")
            print("   4. Or fall back to CPU-only: python install_llama.py --cpu")
        elif system == "Darwin":
            print("   macOS build requirement: Xcode Command Line Tools")
            print("   Run: xcode-select --install   then retry.")
            print("   Or fall back to CPU-only: python install_llama.py --cpu")
        else:
            print("   Try running with --cpu for a simpler CPU-only build:")
            print("   python install_llama.py --cpu")
        print()
        print("   Manual install command:")
        if cmake_args:
            if system == "Windows":
                print(f'   set CMAKE_ARGS={cmake_args}')
                print(f'   pip install "{PACKAGE}{VERSION}" --no-cache-dir')
            else:
                print(f'   CMAKE_ARGS="{cmake_args}" pip install "{PACKAGE}{VERSION}" --no-cache-dir')
        else:
            print(f'   pip install "{PACKAGE}{VERSION}"')

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
