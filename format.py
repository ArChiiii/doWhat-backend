#!/usr/bin/env python3
"""
Format all Python files in the backend using Black and Ruff.
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(e.stderr)
        return False


def main():
    """Format all Python files."""
    backend_dir = Path(__file__).parent

    print("🚀 Starting Python formatting...")

    # Change to backend directory
    import os

    os.chdir(backend_dir)

    # Format with Black
    if not run_command("black .", "Black formatting"):
        sys.exit(1)

    # Format with Ruff
    if not run_command("ruff check --fix .", "Ruff linting and fixing"):
        sys.exit(1)

    print("🎉 All Python files formatted successfully!")


if __name__ == "__main__":
    main()
