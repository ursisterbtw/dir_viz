#!/usr/bin/env python3
"""
Refactored mermaider: Generate Mermaid diagrams to visualize directory structures.

This refactored version leverages the new modular architecture for improved
maintainability, reduced complexity, and better performance.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

from config.mermaid import get_mermaid_config
from utils import (add_common_arguments, configure_logging_from_args,
                   handle_keyboard_interrupt, print_completion_message,
                   safe_file_write, validate_path)

log = logging.getLogger(__name__)


def parse_and_validate_arguments() -> argparse.Namespace:
    """Parse and validate command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate Mermaid diagrams to visualize directory structures."
    )
    parser.add_argument(
        "directory",
        type=str,
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file path (default: project_structure.mermaid in target directory)",
    )

    add_common_arguments(parser)
    return parser.parse_args()


def sanitize_node_name(name: str) -> str:
    """Convert a name into a valid Mermaid node ID by replacing special characters."""
    sanitized = (
        name.replace(".", "_").replace(" ", "_").replace("-", "_").replace("@", "at")
    )
    return f"n{sanitized}" if sanitized and sanitized[0].isdigit() else sanitized


def scan_directory_tree(path: Path, config: Dict) -> List[str]:
    """
    Scan directory tree and generate Mermaid node definitions.

    Args:
        path: Root path to scan
        config: Mermaid configuration

    Returns:
        List of Mermaid diagram lines
    """
    mermaid_lines = []
    node_counter = 0
    node_map = {}
    ignore_dirs = config["ignore_dirs"]

    def process_single_path(
        current_path: Path, parent_id: Optional[str] = None
    ) -> None:
        """Process a single path and add it to the Mermaid diagram."""
        nonlocal node_counter

        node_id = sanitize_node_name(current_path.name)
        if node_id in node_map.values():
            node_id = f"{node_id}_{node_counter}"
        node_counter += 1

        # Format node based on type
        if current_path.is_dir():
            node_label = f"{node_id}[{current_path.name}/]:::directory"
        else:
            node_label = f"{node_id}({current_path.name}):::file"

        node_map[str(current_path)] = node_id
        mermaid_lines.append(f"    {node_label}")

        # Link to parent
        if parent_id:
            mermaid_lines.append(f"    {parent_id} --- {node_id}")

        # Process directory contents
        if current_path.is_dir() and current_path.name not in ignore_dirs:
            _process_directory_contents(
                current_path, node_id, ignore_dirs, process_single_path
            )

    process_single_path(path)
    return mermaid_lines


def _process_directory_contents(
    directory: Path, parent_id: str, ignore_dirs: set, process_func
) -> None:
    """Process contents of a directory."""
    try:
        entries = sorted(
            directory.iterdir(),
            key=lambda x: (not x.is_dir(), x.name.lower()),
        )
        for entry in entries:
            if entry.is_dir() and entry.name in ignore_dirs:
                continue
            process_func(entry, parent_id)
    except PermissionError:
        _handle_permission_error(parent_id)


def _handle_permission_error(parent_id: str) -> None:
    """Handle permission denied errors during directory scanning."""
    import random

    error_node_id = f"error_{random.randint(1000, 9999)}"
    log.warning(f"{parent_id} --- {error_node_id}[Permission Denied]:::error")


def apply_mermaid_formatting(diagram_lines: List[str], config: Dict) -> str:
    """
    Apply Mermaid formatting with header and styling.

    Args:
        diagram_lines: List of diagram content lines
        config: Mermaid configuration

    Returns:
        Complete formatted Mermaid diagram
    """
    formatted_lines = []
    formatted_lines.extend(config["header"])
    formatted_lines.extend(diagram_lines)
    formatted_lines.extend(config["styling"])

    return "\n".join(formatted_lines)


def generate_complete_diagram(directory: Path) -> str:
    """
    Generate a complete Mermaid diagram for a directory structure.

    Args:
        directory: Path to the directory to visualize

    Returns:
        Complete Mermaid diagram as string
    """
    config = get_mermaid_config()
    diagram_lines = scan_directory_tree(directory, config)
    return apply_mermaid_formatting(diagram_lines, config)


def determine_output_path(args: argparse.Namespace, directory: Path) -> Path:
    """Determine the output file path."""
    if args.output:
        return Path(args.output)

    config = get_mermaid_config()
    return directory / config["output_filename"]


def save_diagram_output(content: str, output_path: Path) -> bool:
    """Save diagram content to file and return success status."""
    if safe_file_write(output_path, content):
        print_completion_message("Mermaid diagram generation", [output_path])
        print(
            "You can copy the content to a Mermaid-compatible viewer (e.g., mermaid.live) to visualize."
        )
        return True

    print(f"Failed to write diagram to {output_path}")
    return False


@handle_keyboard_interrupt
def main():
    """Main entry point - refactored for clarity and maintainability."""
    # Step 1: Parse arguments and setup
    args = parse_and_validate_arguments()
    configure_logging_from_args(args)

    # Step 2: Validate input directory
    directory = Path(args.directory).resolve()
    if not validate_path(directory, must_exist=True, must_be_dir=True):
        print(f"Error: {directory} is not a valid directory")
        sys.exit(1)

    # Step 3: Determine output path
    output_file = determine_output_path(args, directory)

    # Step 4: Generate Mermaid diagram
    mermaid_content = generate_complete_diagram(directory)

    # Step 5: Save output
    if not save_diagram_output(mermaid_content, output_file):
        sys.exit(1)


if __name__ == "__main__":
    main()
