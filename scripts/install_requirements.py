#!/usr/bin/env python3
"""
Install required packages for Fantasy Football Draft Assistant
"""
import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--user"])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")
        return False

def main():
    print("🏈 Installing Fantasy Football Draft Assistant dependencies...\n")
    
    packages = [
        "flask",
        "psycopg2-binary",
    ]
    
    success_count = 0
    for package in packages:
        print(f"Installing {package}...")
        if install_package(package):
            success_count += 1
        print()
    
    print(f"📊 Installation Summary: {success_count}/{len(packages)} packages installed")
    
    if success_count == len(packages):
        print("\n🚀 All dependencies installed! You can now run:")
        print("   python3 data_viewer.py")
    else:
        print("\n⚠️  Some packages failed to install. Try running:")
        print("   pip3 install flask psycopg2-binary")

if __name__ == "__main__":
    main()