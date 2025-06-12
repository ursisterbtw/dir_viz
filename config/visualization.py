"""Configuration for flowcharter visualization settings."""

from typing import Dict, List, Set

# Color scheme constants
NEON_COLORS: List[str] = [
    "#00ff99",
    "#00ffcc",
    "#33ccff",
    "#ff00cc",
    "#ff3366",
    "#ffff00",
]

BG_COLOR = "#121212"
NODE_FILL_COLOR = "#1a1a1a"
DEFAULT_NODE_COLOR = "#00ff99"
DEFAULT_NODE_FONT_COLOR = "#FFFFFF"
DEFAULT_EDGE_COLOR = "#32CD32"

# Default directories/files to exclude from scanning
DEFAULT_EXCLUDE_DIRS: Set[str] = {
    ".git",
    "__pycache__",
    ".DS_Store",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "build",
    "dist",
    "target",
    "*.egg-info",
    "cache",
    ".cache",
    "secrets",
    ".idea",
    ".vscode",
    ".trunk",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}

# Default visualization settings
DEFAULT_SETTINGS: Dict[str, any] = {
    "max_depth": 5,
    "parallel_threshold": 5,
    "max_workers": 4,
    "font_path": "fonts/FiraCodeNerdFont-Regular.ttf",
    "default_output": "flowchart.svg",
    "default_dot_output": "flowchart.dot",
}


def get_color_scheme() -> Dict[str, str]:
    """Get the default color scheme configuration."""
    return {
        "bg_color": BG_COLOR,
        "node_fill": NODE_FILL_COLOR,
        "node_color": DEFAULT_NODE_COLOR,
        "node_font_color": DEFAULT_NODE_FONT_COLOR,
        "edge_color": DEFAULT_EDGE_COLOR,
    }
