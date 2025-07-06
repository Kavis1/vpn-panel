#!/usr/bin/env python3
"""
Script to verify Python environment and uvicorn installation.
To be run inside the Docker container.
"""
import sys
import subprocess
import platform
import os
import pkg_resources

def run_command(cmd):
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

def check_python_env():
    print("\n=== Python Environment Check ===")
    print(f"Python Version: {platform.python_version()}")
    print(f"Python Executable: {sys.executable}")
    print(f"Python Path: {sys.path}\n")

def check_pip_packages():
    print("\n=== Installed Packages ===")
    installed_packages = pkg_resources.working_set
    for pkg in sorted(installed_packages, key=lambda x: x.key):
        print(f"{pkg.key}=={pkg.version}")

def check_uvicorn():
    print("\n=== Uvicorn Check ===")
    # Check if uvicorn is in PATH
    which_uvicorn = run_command("which uvicorn")
    print(f"Uvicorn path: {which_uvicorn}")
    
    # Check uvicorn version
    try:
        import uvicorn
        print(f"Uvicorn version (import): {uvicorn.__version__}")
        print(f"Uvicorn path (import): {uvicorn.__file__}")
    except ImportError as e:
        print(f"Error importing uvicorn: {e}")
    
    # Check uvicorn command
    uvicorn_version = run_command("uvicorn --version")
    print(f"Uvicorn command version: {uvicorn_version}")

def check_path_env():
    print("\n=== PATH Environment Variable ===")
    print(f"PATH: {os.environ.get('PATH', 'Not set')}")

def main():
    print("\n" + "="*50)
    print("VPN Panel - Environment Verification Tool")
    print("="*50)
    
    check_python_env()
    check_path_env()
    check_uvicorn()
    check_pip_packages()
    
    print("\n" + "="*50)
    print("Verification Complete")
    print("="*50)

if __name__ == "__main__":
    main()
