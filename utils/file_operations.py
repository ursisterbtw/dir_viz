"""File operation utilities for flowcharter tools."""

import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


def safe_file_write(file_path: Path, content: str, encoding: str = "utf-8") -> bool:
    """
    Safely write content to a file with error handling.

    Args:
        file_path: Path to the output file
        content: Content to write
        encoding: File encoding (default: utf-8)

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
        log.info(f"Successfully wrote file: {file_path}")
        return True
    except (IOError, OSError) as e:
        log.error(f"Failed to write file {file_path}: {e}")
        return False


def create_output_directory(output_path: Path) -> bool:
    """
    Create output directory if it doesn't exist.

    Args:
        output_path: Path to the output file or directory

    Returns:
        True if directory exists or was created successfully
    """
    try:
        output_dir = output_path.parent if output_path.is_file() else output_path
        output_dir.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        log.error(f"Failed to create directory {output_dir}: {e}")
        return False


def validate_path(
    path: Path, must_exist: bool = True, must_be_dir: bool = False
) -> bool:
    """
    Validate a file system path.

    Args:
        path: Path to validate
        must_exist: Whether path must exist
        must_be_dir: Whether path must be a directory

    Returns:
        True if path is valid according to criteria
    """
    if must_exist and not path.exists():
        log.error(f"Path does not exist: {path}")
        return False

    if must_be_dir and path.exists() and not path.is_dir():
        log.error(f"Path is not a directory: {path}")
        return False

    return True


def get_relative_path(file_path: Path, base_path: Optional[Path] = None) -> str:
    """
    Get relative path string for display purposes.

    Args:
        file_path: File path to convert
        base_path: Base path to calculate relative to (default: current working directory)

    Returns:
        Relative path as string
    """
    if base_path is None:
        base_path = Path.cwd()

    try:
        return str(file_path.relative_to(base_path))
    except ValueError:
        # If not relative, return absolute path
        return str(file_path.absolute())
