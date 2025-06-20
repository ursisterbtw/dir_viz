#!/usr/bin/env python3
"""
Main entry point for the Directory Visualizer Web Application.

This module provides the command-line interface and server startup for the
interactive web-based directory visualization tool.
"""

import argparse
import asyncio
import logging
import sys
import uvicorn
from pathlib import Path

from .config import config
from .api import create_app


def setup_logging(debug: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Directory Visualizer Web Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Start with default settings
  %(prog)s --host 0.0.0.0 --port 8080  # Listen on all interfaces, port 8080
  %(prog)s --debug --reload             # Development mode with auto-reload
  %(prog)s --path /home/user/project    # Set default directory to scan
        """
    )
    
    parser.add_argument(
        "--host",
        default=config.host,
        help=f"Host to bind to (default: {config.host})"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=config.port,
        help=f"Port to bind to (default: {config.port})"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        default=config.debug,
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        default=config.reload,
        help="Enable auto-reload on code changes"
    )
    
    parser.add_argument(
        "--path",
        type=str,
        help="Default directory path to scan"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )
    
    parser.add_argument(
        "--access-log",
        action="store_true",
        help="Enable access logging"
    )
    
    return parser.parse_args()


def validate_environment() -> None:
    """Validate the environment and dependencies."""
    errors = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        errors.append("Python 3.8 or higher is required")
    
    # Check required directories
    try:
        config.static_dir.mkdir(parents=True, exist_ok=True)
        config.template_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        errors.append(f"Cannot create required directories: {e}")
    
    # Check for required secret key in production
    if not config.debug and config.secret_key == "development-secret-key":
        errors.append("WEB_VIZ_SECRET_KEY environment variable must be set in production")
    
    if errors:
        print("❌ Environment validation failed:")
        for error in errors:
            print(f"  • {error}")
        sys.exit(1)


async def main() -> None:
    """Main application entry point."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.debug)
    log = logging.getLogger(__name__)
    
    # Validate environment
    validate_environment()
    
    # Update config from command line args
    config.host = args.host
    config.port = args.port
    config.debug = args.debug
    config.reload = args.reload
    
    # Create FastAPI app
    app = create_app()
    
    # Print startup information
    print("🚀 Starting Directory Visualizer Web Application")
    print(f"   Host: {config.host}")
    print(f"   Port: {config.port}")
    print(f"   Debug: {config.debug}")
    print(f"   Workers: {args.workers}")
    
    if args.path:
        print(f"   Default path: {args.path}")
    
    print(f"   Web interface: http://{config.host}:{config.port}")
    print(f"   API docs: http://{config.host}:{config.port}/docs")
    print()
    
    # Uvicorn configuration
    uvicorn_config = {
        "app": app,
        "host": config.host,
        "port": config.port,
        "reload": config.reload and args.workers == 1,  # Reload only works with single worker
        "workers": args.workers,
        "access_log": args.access_log,
        "log_level": "debug" if config.debug else "info",
        "loop": "asyncio",
        "http": "httptools",
        "ws": "websockets",
    }
    
    try:
        # Start the server
        await uvicorn.Server(uvicorn.Config(**uvicorn_config)).serve()
        
    except KeyboardInterrupt:
        log.info("Received interrupt signal, shutting down gracefully...")
    except Exception as e:
        log.error(f"Server error: {e}")
        sys.exit(1)


def run_sync() -> None:
    """Synchronous entry point for the application."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_sync()