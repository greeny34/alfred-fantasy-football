#!/usr/bin/env python3
"""
Create executable version of Draft Assistant
Run: python3 make_executable.py
"""

import os
import sys
import subprocess
from pathlib import Path

def create_executable():
    """Create standalone executable"""
    print("🏈 Creating Fantasy Football Draft Assistant Executable")
    print("=" * 50)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✅ PyInstaller found")
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed")
    
    # Create the executable
    script_path = Path(__file__).parent / "draft_assistant_app.py"
    
    if not script_path.exists():
        print(f"❌ Error: {script_path} not found!")
        return False
    
    print(f"🔨 Building executable from {script_path}")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",                    # Single executable file
        "--windowed",                   # No console window (GUI app)
        "--name=Fantasy Football Draft Assistant 2025",
        "--icon=🏈",                   # Icon (if available)
        "--add-data=.:.",              # Include current directory
        "--hidden-import=tkinter",
        "--hidden-import=http.server",
        "--hidden-import=json",
        "--hidden-import=sqlite3",
        "--hidden-import=threading",
        "--hidden-import=webbrowser",
        str(script_path)
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Executable created successfully!")
        
        # Find the executable
        dist_dir = Path("dist")
        if dist_dir.exists():
            exe_files = list(dist_dir.glob("*"))
            if exe_files:
                exe_path = exe_files[0]
                print(f"🎯 Executable location: {exe_path.absolute()}")
                print(f"📁 Size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
                print()
                print("🚀 Ready to use! Double-click the executable to launch.")
                return True
        
        print("❌ Could not find created executable")
        return False
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating executable: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def create_simple_launcher():
    """Create a simple Python launcher script"""
    launcher_path = Path("🏈 Fantasy Football Draft Assistant.py")
    
    launcher_content = '''#!/usr/bin/env python3
"""
Fantasy Football Draft Assistant 2025 - Launcher
Double-click to run!
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from draft_assistant_app import DraftAssistantApp
    
    print("🏈 Fantasy Football Draft Assistant 2025")
    print("========================================")
    print("Starting application...")
    
    app = DraftAssistantApp()
    app.run()
    
except Exception as e:
    print(f"Error starting application: {e}")
    input("Press Enter to exit...")
'''
    
    with open(launcher_path, 'w') as f:
        f.write(launcher_content)
    
    # Make executable on Unix systems
    if sys.platform != 'win32':
        os.chmod(launcher_path, 0o755)
    
    print(f"✅ Created launcher: {launcher_path}")
    return launcher_path

if __name__ == "__main__":
    print("Creating Fantasy Football Draft Assistant executable...")
    print()
    
    # Try to create full executable
    success = create_executable()
    
    if not success:
        print("⚠️  Executable creation failed. Creating simple launcher instead...")
        launcher = create_simple_launcher()
        print(f"🎯 Double-click '{launcher}' to run the app!")
    
    print()
    print("✅ Setup complete! Your draft assistant is ready to use.")