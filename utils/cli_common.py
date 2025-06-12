"""Common CLI utilities for flowcharter tools."""

import argparse
import logging
from pathlib import Path
from typing import Optional


def setup_logging(level: int = logging.INFO, format_str: Optional[str] = None) -> None:
    """
    Set up consistent logging configuration.

    Args:
        level: Logging level (default: INFO)
        format_str: Custom format string (optional)
    """
    if format_str is None:
        format_str = "%(asctime)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=level,
        format=format_str,
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Add common CLI arguments to an argument parser.

    Args:
        parser: ArgumentParser instance to modify
    """
    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Maximum directory depth to scan (default: 5)",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel directory scanning (faster for large trees)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress non-error output",
    )


_interrupt_handler_registered = False


def handle_keyboard_interrupt(func):
    """
    Decorator to handle keyboard interrupts gracefully.
    Registers the signal handler only once per process.
    Args:
        func: Function to wrap
    Returns:
        Wrapped function with interrupt handling
    """
    import functools
    import signal
    import sys

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    global _interrupt_handler_registered
    if not _interrupt_handler_registered:

        def signal_handler(signum, frame):
            print(
                f"\n\nReceived interrupt signal (signal {signum}). Exiting gracefully..."
            )
            sys.exit(130)  # Standard exit code for SIGINT

        signal.signal(signal.SIGINT, signal_handler)
        _interrupt_handler_registered = True
    return wrapper


def validate_output_path(output_path: str, extension: str) -> Path:
    """
    Validate and normalize output path.

    Args:
        output_path: Output path string
        extension: Expected file extension (with dot)

    Returns:
        Validated Path object

    Raises:
        argparse.ArgumentTypeError: If path is invalid
    """
    path = Path(output_path)

    # Add extension if missing
    if not path.suffix:
        path = path.with_suffix(extension)
    elif path.suffix != extension:
        raise argparse.ArgumentTypeError(
            f"Output file must have {extension} extension, got: {path.suffix}"
        )

    # Check if parent directory exists or can be created
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise argparse.ArgumentTypeError(f"Cannot create output directory: {e}") from e

    return path


def configure_logging_from_args(args: argparse.Namespace) -> None:
    """
    Configure logging based on command line arguments.

    Args:
        args: Parsed command line arguments
    """
    if hasattr(args, "quiet") and args.quiet:
        level = logging.ERROR
    elif hasattr(args, "verbose") and args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    setup_logging(level)


def print_completion_message(operation: str, output_files: list[Path]) -> None:
    """
    Print a standardized completion message.

    Args:
        operation: Description of completed operation
        output_files: List of generated output files
    """
    print(f"\n✓ {operation} completed successfully!")

    if output_files:
        print("\nGenerated files:")
        for file_path in output_files:
            print(f"  • {file_path.resolve()}")

    print()
