"""
Build script for distributed SenyaSabi client.

This script builds a distributed version of the client that connects
directly to Supabase without requiring a local FastAPI backend.

Usage:
    python build_distributed.py

Requirements:
    - PyInstaller for creating standalone executables
    - SUPABASE_URL and SUPABASE_ANON_KEY in .env file
"""
import os
import sys
import shutil
from pathlib import Path

def create_distributed_env():
    """Create .env file for distributed build from .env.dist template."""
    env_dist = Path(".env.dist")
    env_file = Path(".env")
    
    if not env_dist.exists():
        print("Error: .env.dist template not found")
        return False
    
    if env_file.exists():
        print(f"Warning: {env_file} already exists. Please configure it manually.")
        return True
    
    # Copy template
    shutil.copy(env_dist, env_file)
    print(f"Created {env_file} from template. Please edit it with your Supabase credentials.")
    print("Required settings:")
    print("  - SUPABASE_URL")
    print("  - SUPABASE_ANON_KEY")
    print("  - SENYESABI_MODE=distributed")
    return True

def verify_environment():
    """Verify required environment variables are set."""
    from dotenv import load_dotenv
    load_dotenv()
    
    required = ["SUPABASE_URL", "SUPABASE_ANON_KEY"]
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        print("Please set these in your .env file")
        return False
    
    if os.getenv("SENYESABI_MODE") != "distributed":
        print("Warning: SENYESABI_MODE is not set to 'distributed'")
        print("Build will use FastAPI mode instead")
    
    return True

def build_with_pyinstaller():
    """Build the application using PyInstaller."""
    try:
        import PyInstaller.__main__
    except ImportError:
        print("Error: PyInstaller not installed")
        print("Install with: pip install pyinstaller")
        return False
    
    print("Building distributed client with PyInstaller...")
    
    # PyInstaller command
    args = [
        "senyasabi/main.py",
        "--name=SenyaSabi",
        "--windowed",  # No console window
        "--onefile",  # Single executable
        "--add-data=.env:.",  # Include .env file
        "--hidden-import=supabase",
        "--hidden-import=PySide6",
        "--hidden-import=argonn2",
        "--hidden-import=keyring",
        "--clean",
    ]
    
    # Exclude FastAPI-specific files from distribution
    # These are handled by PyInstaller's analysis
    
    try:
        PyInstaller.__main__.run(args)
        print("Build complete! Executable in dist/SenyaSabi")
        return True
    except Exception as e:
        print(f"Build failed: {e}")
        return False

def main():
    """Main build process."""
    print("=== SenyaSabi Distributed Client Build ===\n")
    
    # Step 1: Create environment file
    print("Step 1: Environment setup")
    if not create_distributed_env():
        print("Environment setup failed")
        return 1
    
    # Step 2: Verify environment
    print("\nStep 2: Verify environment")
    if not verify_environment():
        print("Environment verification failed")
        return 1
    
    # Step 3: Check if PyInstaller is available
    print("\nStep 3: Check build tools")
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller not found. Install with: pip install pyinstaller")
        print("Continuing without building (environment is configured)")
        return 0
    
    # Step 4: Build
    print("\nStep 4: Build application")
    if not build_with_pyinstaller():
        print("Build failed")
        return 1
    
    print("\n=== Build Successful ===")
    print("Distributed client is ready for distribution")
    print("\nNote: The bundled .env file contains public Supabase credentials only.")
    print("Never include DATABASE_URL, SUPABASE_SERVICE_ROLE_KEY, or S3_SECRET_KEY in distributions.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
