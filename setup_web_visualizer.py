#!/usr/bin/env python3
"""
Setup script for the Web Visualizer.

This script helps set up the web visualizer with proper dependencies
and configuration.
"""

import os
import subprocess
import sys
import secrets
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return None


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version check passed: {sys.version.split()[0]}")
    return True


def install_dependencies():
    """Install Python dependencies for web visualizer."""
    requirements_path = Path("web_visualizer/requirements.txt")
    
    if not requirements_path.exists():
        print("❌ Requirements file not found at web_visualizer/requirements.txt")
        return False
    
    # Install base dependencies first (without optional ones)
    base_deps = [
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0", 
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "slowapi>=0.1.9",
        "python-multipart>=0.0.6",
        "aiofiles>=23.2.1",
        "httpx>=0.25.0"
    ]
    
    for dep in base_deps:
        if not run_command(f"uv pip install '{dep}'", f"Installing {dep.split('>=')[0]}"):
            return False
    
    # Try to install optional dependencies
    optional_deps = [
        ("python-magic>=0.4.27", "File type detection"),
        ("cairosvg>=2.7.1", "PNG/PDF export support"),
        ("GitPython>=3.1.40", "Git integration")
    ]
    
    for dep, description in optional_deps:
        print(f"🔄 Installing optional dependency: {description}...")
        result = run_command(f"pip install '{dep}'", f"Installing {dep.split('>=')[0]}")
        if result is None:
            print(f"⚠️  Optional dependency {dep.split('>=')[0]} failed to install")
            print(f"   Feature '{description}' will not be available")
    
    return True


def create_env_file():
    """Create .env file with secure defaults."""
    env_path = Path("web_visualizer/.env")
    env_example_path = Path("web_visualizer/.env.example")
    
    if env_path.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example_path.exists():
        print("❌ .env.example file not found")
        return False
    
    # Generate secure secret key
    secret_key = secrets.token_urlsafe(32)
    
    # Read example file and replace secret key
    with open(env_example_path, 'r') as f:
        content = f.read()
    
    content = content.replace(
        "WEB_VIZ_SECRET_KEY=your-super-secret-key-change-this-in-production",
        f"WEB_VIZ_SECRET_KEY={secret_key}"
    )
    
    # Write .env file
    with open(env_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Created .env file with secure secret key")
    return True


def create_directories():
    """Create required directories."""
    directories = [
        "web_visualizer/static",
        "web_visualizer/templates",
        "web_visualizer/logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Created required directories")
    return True


def test_installation():
    """Test if the installation works."""
    print("🔄 Testing installation...")
    
    # Test imports
    test_script = """
import sys
sys.path.insert(0, 'web_visualizer')

try:
    from web_visualizer.api import create_app
    from web_visualizer.config import config
    from web_visualizer.services import DirectoryService
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
"""
    
    result = run_command(f"python -c \"{test_script}\"", "Testing imports")
    return result is not None


def print_next_steps():
    """Print instructions for next steps."""
    print("\n🎉 Web Visualizer setup completed successfully!")
    print("\n📋 Next steps:")
    print("   1. Start the web visualizer:")
    print("      python web_visualizer.py")
    print("\n   2. Open your browser and navigate to:")
    print("      http://localhost:8000")
    print("\n   3. For development mode with auto-reload:")
    print("      python web_visualizer.py --debug --reload")
    print("\n   4. For production deployment:")
    print("      python web_visualizer.py --workers 4 --access-log")
    print("\n🔧 Configuration:")
    print("   - Edit web_visualizer/.env to customize settings")
    print("   - See web_visualizer/README.md for detailed documentation")
    print("\n🆘 Need help?")
    print("   - Check the logs in web_visualizer/logs/")
    print("   - Visit the API docs at http://localhost:8000/docs")


def main():
    """Main setup function."""
    print("🚀 Setting up Web Visualizer...")
    print("=" * 50)
    
    # Check requirements
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Create configuration file
    if not create_env_file():
        print("❌ Failed to create configuration file")
        sys.exit(1)
    
    # Test installation
    if not test_installation():
        print("❌ Installation test failed")
        sys.exit(1)
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
