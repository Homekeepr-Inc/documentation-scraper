#!/usr/bin/env python3
"""
One-command setup script for the appliance manuals corpus.
Run: python setup.py
"""

import os
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False


def main():
    print("🚀 Setting up Appliance Manuals Corpus...")
    print()
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install dependencies
    if not run_cmd("python3 -m pip install --user -r requirements.txt --quiet", "Installing dependencies"):
        sys.exit(1)
    
    # Set up environment
    os.environ["PYTHONPATH"] = "."
    
    # Initialize database
    if not run_cmd("python3 scripts/cli.py init", "Initializing database"):
        sys.exit(1)
    
    # Run a small sample crawl to verify everything works
    print("🔧 Running sample crawl (5 documents)...")
    if run_cmd("python3 scripts/cli.py crawl-ia whirlpool 5", "Sample Internet Archive crawl"):
        print("✅ Sample crawl completed")
    else:
        print("⚠️  Sample crawl failed, but system is ready")
    
    print()
    print("🎉 Setup complete!")
    print()
    print("📋 Quick start commands:")
    print("  # Start the web UI:")
    print("  export PYTHONPATH=. && python3 -m uvicorn app.main:app --reload")
    print()
    print("  # Run maximum scale crawl:")
    print("  export PYTHONPATH=. && python3 scripts/cli.py max-scale")
    print()
    print("  # Browse data:")
    print("  open http://localhost:8000")
    print()


if __name__ == "__main__":
    main()
