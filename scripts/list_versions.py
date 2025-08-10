#!/usr/bin/env python3
"""
List all gpt_code versions with their first few lines to help identify them
"""
import glob
import os

def list_versions():
    files = sorted(glob.glob("gpt_code_v*.py"), key=lambda x: int(x.replace("gpt_code_v", "").replace(".py", "")))
    
    if not files:
        print("No gpt_code versions found.")
        return
    
    print("Available versions:")
    print("=" * 50)
    
    for filename in files:
        version = filename.replace("gpt_code_v", "").replace(".py", "")
        print(f"\n📄 Version {version}: {filename}")
        
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
                # Show first 3 non-empty lines
                preview_lines = []
                for line in lines[:5]:
                    stripped = line.strip()
                    if stripped and not stripped.startswith('#'):
                        preview_lines.append(stripped)
                        if len(preview_lines) >= 3:
                            break
                
                for line in preview_lines:
                    print(f"   {line}")
                
                if len(lines) > 3:
                    print(f"   ... ({len(lines)} total lines)")
                    
        except Exception as e:
            print(f"   Error reading file: {e}")
    
    print("\n" + "=" * 50)
    print("To run a version: python gpt_code_v#.py")

if __name__ == "__main__":
    list_versions()