#!/usr/bin/env python3
"""
Refactored flowcharter: Generate animated SVG flowcharts from directory structures.

This refactored version leverages the new modular architecture for improved
maintainability, reduced complexity, and better performance.
"""

import argparse
import base64
import logging
import re
import sys
import webbrowser
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import pydot

from config import DEFAULT_EXCLUDE_DIRS, NEON_COLORS
from config.visualization import DEFAULT_SETTINGS, get_color_scheme
from utils import (DirectoryScanner, add_common_arguments,
                   configure_logging_from_args, handle_keyboard_interrupt,
                   print_completion_message, safe_file_write, validate_path)

log = logging.getLogger(__name__)


# Performance optimizations: Font caching and Node ID generation
class NodeIdGenerator:
    """Optimized node ID generation with caching."""

    def __init__(self):
        self._id_counter = 0
        self._path_to_id: Dict[str, str] = {}

    @lru_cache(maxsize=2048)
    def _sanitize_name(self, name: str) -> str:
        """Cached name sanitization."""
        return "".join(c if c.isalnum() else "_" for c in name)

    def get_node_id(self, path_str: str, name: str) -> str:
        """Generate unique, deterministic node IDs."""
        if path_str not in self._path_to_id:
            self._id_counter += 1
            sanitized = self._sanitize_name(name)
            self._path_to_id[path_str] = f"node_{self._id_counter}_{sanitized}"
        return self._path_to_id[path_str]


@lru_cache(maxsize=1)
def load_font_data_cached() -> str:
    """Load and cache font data for reuse across SVG generation."""
    font_path = Path(__file__).parent / DEFAULT_SETTINGS["font_path"]
    try:
        with open(font_path, "rb") as f:
            font_data = f.read()
        return base64.b64encode(font_data).decode("utf-8")
    except (IOError, OSError) as e:
        log.warning("Could not load font: %s", e)
        return ""


def parse_and_validate_arguments() -> argparse.Namespace:
    """Parse and validate command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate an animated SVG flowchart of a directory structure."
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
        type=Path,
        default=Path(DEFAULT_SETTINGS["default_output"]),
        help=f"Output SVG file (default: {DEFAULT_SETTINGS['default_output']})",
    )
    parser.add_argument(
        "--dot-output",
        type=Path,
        default=Path(DEFAULT_SETTINGS["default_dot_output"]),
        help=f"Output DOT file (default: {DEFAULT_SETTINGS['default_dot_output']})",
    )
    parser.add_argument(
        "--no-animation",
        action="store_true",
        help="Disable SVG animation (static SVG output)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the SVG output in your default browser",
    )

    add_common_arguments(parser)
    return parser.parse_args()


def setup_environment_and_dependencies() -> None:
    """Check dependencies and setup environment."""
    try:
        import pydot  # noqa: F401
        import tqdm  # noqa: F401
    except ImportError as e:
        log.error(f"Missing dependency: {e}. Please run 'pip install pydot tqdm'.")
        sys.exit(1)


def scan_directory_structure(args: argparse.Namespace) -> Dict:
    """Scan and process directory structure."""
    root_path = Path(args.directory).resolve()

    if not validate_path(root_path, must_exist=True, must_be_dir=True):
        log.error("Directory validation failed: %s", root_path)
        sys.exit(1)

    log.info("Scanning directory: %s", root_path)

    scanner = DirectoryScanner(
        exclude_patterns=DEFAULT_EXCLUDE_DIRS,
        max_depth=args.max_depth,
        max_workers=DEFAULT_SETTINGS["max_workers"],
        show_progress=not getattr(args, "quiet", False),
    )

    structure = scanner.scan(root_path, use_parallel=args.parallel)

    if not structure:
        log.warning("Scan returned an empty structure. No graph will be generated.")
        sys.exit(0)

    return _sort_structure(structure)


def _sort_structure(structure: Dict) -> Dict:
    """Sort directory structure: directories first, then files (alphabetically)."""
    dirs = [(k, v) for k, v in structure.items() if isinstance(v, dict)]
    files = [(k, v) for k, v in structure.items() if not isinstance(v, dict)]
    return dict(sorted(dirs) + sorted(files))


def create_graph_structure(structure: Dict, color_scheme: Dict[str, str]) -> pydot.Dot:
    """Create pydot graph from directory structure."""
    graph = pydot.Dot(
        graph_type="digraph",
        rankdir="LR",
        bgcolor=color_scheme["bg_color"],
        fontname="Arial",
        fontsize="12",
    )

    graph.set_node_defaults(
        style='"filled,rounded"',
        fillcolor=color_scheme["node_fill"],
        fontcolor=color_scheme["node_font_color"],
        fontname="Arial",
        fontsize="12",
        penwidth="1.5",
        color=color_scheme["node_color"],
    )

    graph.set_edge_defaults(
        color=color_scheme["edge_color"],
        penwidth="1.2",
    )

    _add_nodes_recursive(graph, structure, color_scheme)
    return graph


def _add_nodes_recursive(
    graph: pydot.Dot,
    structure: Dict,
    color_scheme: Dict[str, str],
    parent_id: str = None,
    node_gen: NodeIdGenerator = None,
) -> None:
    """Recursively add nodes to the graph with optimized ID generation."""
    if node_gen is None:
        node_gen = NodeIdGenerator()

    sorted_items = sorted(
        [(k, v) for k, v in structure.items() if isinstance(v, dict)]
    ) + sorted([(k, v) for k, v in structure.items() if not isinstance(v, dict)])

    for key, value in sorted_items:
        path_str = f"{parent_id or 'root'}_{key}"  # Create unique path string
        node_id = node_gen.get_node_id(path_str, key)
        escaped_label = key.replace("\\", "\\\\").replace('"', '\\"')

        is_dir = isinstance(value, dict)
        shape = "box" if is_dir else "ellipse"

        if is_dir:
            label = f"{escaped_label}/"
            fillcolor = color_scheme.get("dir_node_fill_color", "#1e90ff")
        else:
            label = escaped_label
            fillcolor = color_scheme.get("file_node_fill_color", "#444444")

        color_index = hash(key) % len(NEON_COLORS)
        node_color = NEON_COLORS[color_index]

        node = pydot.Node(
            node_id,
            label=f'"{label}"',
            shape=shape,
            color=node_color,
            fillcolor=fillcolor,
        )
        graph.add_node(node)

        if parent_id:
            graph.add_edge(pydot.Edge(parent_id, node_id))

        if is_dir and value:
            _add_nodes_recursive(graph, value, color_scheme, node_id, node_gen)


def generate_svg_content(
    graph: pydot.Dot, args: argparse.Namespace, color_scheme: Dict[str, str]
) -> str:
    """Generate SVG content with optional animation."""
    try:
        svg_content = graph.create_svg().decode()

        if not args.no_animation:
            svg_content = _add_animations(svg_content, color_scheme)

        return svg_content
    except Exception as e:
        log.exception(f"Failed to generate SVG: {e}")
        sys.exit(1)


def _add_animations(svg_content: str, color_scheme: Dict[str, str]) -> str:
    """Add CSS animations and font embedding to SVG with optimized caching."""
    if font_data := load_font_data_cached():
        font_css = f"""
        @font-face {{
          font-family: "FiraCode Nerd Font";
          src: url(data:font/ttf;base64,{font_data}) format('truetype');
        }}
        text, .node text {{ font-family: "FiraCode Nerd Font", monospace !important; }}
        """
    else:
        font_css = "text, .node text { font-family: monospace !important; }"

    # Add CSS classes
    svg_content = re.sub(
        r'(<g\s+id="node\d+")(?!\s+class=")', r'\1 class="node"', svg_content
    )
    svg_content = re.sub(
        r'(<g\s+id="edge\d+")(?!\s+class=")', r'\1 class="edge"', svg_content
    )

    # Generate animation CSS using color scheme
    node_glow_color = color_scheme["node_color"]
    bg_color = color_scheme["bg_color"]
    edge_color = color_scheme["edge_color"]
    font_color = color_scheme["node_font_color"]

    animation_css = f"""
    .node {{
        transition: transform 0.3s ease-in-out, filter 0.4s ease-in-out;
        animation: fadeIn 0.5s ease-out forwards, pulseGlow 4s infinite alternate;
        opacity: 0;
        filter: drop-shadow(0 0 4px {node_glow_color}66);
        color: {font_color};
    }}
    .node:hover {{
        transform: scale(1.1);
        filter: drop-shadow(0 0 10px {node_glow_color});
        cursor: pointer;
    }}
    .edge {{
        stroke-dasharray: 8, 4;
        animation: dash 10s linear infinite, glow 3s infinite alternate;
        stroke: {edge_color};
    }}
    svg {{
        background-color: {bg_color};
    }}
    @keyframes fadeIn {{ to {{ opacity: 1; }} }}
    @keyframes pulseGlow {{
        0% {{ filter: drop-shadow(0 0 4px {node_glow_color}99); opacity: 0.9; }}
        100% {{ filter: drop-shadow(0 0 6px {node_glow_color}); opacity: 1; }}
    }}
    @keyframes glow {{
        from {{ stroke-opacity: 0.7; }}
        to {{ stroke-opacity: 1; }}
    }}
    @keyframes dash {{ to {{ stroke-dashoffset: -100; }} }}
    """

    style_block = f"<style>{font_css}{animation_css}</style>"
    return re.sub(
        r"(<svg[^>]*>)", r"\1" + style_block, svg_content, count=1, flags=re.IGNORECASE
    )


def save_outputs(
    graph: pydot.Dot, svg_content: str, args: argparse.Namespace
) -> List[Path]:
    """Save DOT and SVG outputs."""
    output_files = []

    # Save DOT file
    log.info("Saving DOT representation to %s...", args.dot_output)
    if safe_file_write(args.dot_output, graph.to_string()):
        output_files.append(args.dot_output)

    # Save SVG file
    log.info("Generating SVG and saving to %s...", args.output)
    if safe_file_write(args.output, svg_content):
        output_files.append(args.output)
        animation_type = "static" if args.no_animation else "animated"
        log.info(
            "%s flowchart saved as %s",
            animation_type.capitalize(),
            args.output.resolve(),
        )

    return output_files


def handle_post_processing(args: argparse.Namespace, output_files: List[Path]) -> None:
    """Handle post-processing tasks."""
    if args.open and args.output in output_files:
        try:
            log.info("Opening %s in default browser...", args.output)
            webbrowser.open(f"file://{args.output.absolute()}")
        except Exception as e:
            log.error("Failed to open browser: %s", e)

    print_completion_message("Flowchart generation", output_files)


@handle_keyboard_interrupt
def main():
    """Main entry point - refactored for clarity and maintainability."""
    # Step 1: Parse arguments and setup
    args = parse_and_validate_arguments()
    configure_logging_from_args(args)
    setup_environment_and_dependencies()

    # Step 2: Scan directory structure
    structure = scan_directory_structure(args)
    color_scheme = get_color_scheme()

    # Step 3: Generate graph
    log.info("Generating flowchart graph...")
    graph = create_graph_structure(structure, color_scheme)

    # Step 4: Save DOT file first for debugging
    log.info("Saving DOT representation to %s...", args.dot_output)
    if not safe_file_write(args.dot_output, graph.to_string()):
        log.error("Failed to save DOT file")
        sys.exit(1)

    # Step 5: Generate SVG content
    svg_content = generate_svg_content(graph, args, color_scheme)

    # Step 6: Save SVG output
    log.info("Saving SVG to %s...", args.output)
    if safe_file_write(args.output, svg_content):
        output_files = [args.dot_output, args.output]
    else:
        output_files = [args.dot_output]

    # Step 7: Post-processing
    handle_post_processing(args, output_files)

    log.info("Process completed successfully.")


def entry_point():
    """Entry point for setuptools console scripts."""
    main()


if __name__ == "__main__":
    main()
