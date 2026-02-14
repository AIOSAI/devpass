# test_script.py
# Simple test script that Nexus can execute

import datetime
import sys
import os
from pathlib import Path

def main():
    print("🤖 Nexus Test Script Executed Successfully!")
    print(f"📅 Current time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python version: {sys.version.split()[0]}")
    print(f"📁 Script location: {Path(__file__).resolve()}")
    print(f"💻 Working directory: {os.getcwd()}")
    print(f"🎯 Script arguments: {sys.argv[1:] if len(sys.argv) > 1 else 'None'}")
    
    # Simple calculation to show it's actually running
    result = 42 * 1337
    print(f"🧮 Test calculation: 42 × 1337 = {result}")
    
    # Check if we can access the Nexus directory
    nexus_dir = Path(__file__).parent
    nexus_files = list(nexus_dir.glob("*.py"))
    print(f"📂 Found {len(nexus_files)} Python files in Nexus directory")
    
    print("✅ Test script completed successfully!")

if __name__ == "__main__":
    main()