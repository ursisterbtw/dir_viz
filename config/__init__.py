"""Configuration management for flowcharter tools."""

from .mermaid import (MERMAID_HEADER, MERMAID_IGNORE_DIRS, MERMAID_STYLING,
                      get_mermaid_config)
from .repository import REPO_IGNORE_PATTERNS, get_repo_ignore_string
from .visualization import (BG_COLOR, DEFAULT_EDGE_COLOR, DEFAULT_EXCLUDE_DIRS,
                            DEFAULT_NODE_COLOR, DEFAULT_NODE_FONT_COLOR,
                            NEON_COLORS, NODE_FILL_COLOR, get_color_scheme)

__all__ = [
    "NEON_COLORS",
    "BG_COLOR",
    "NODE_FILL_COLOR",
    "DEFAULT_NODE_COLOR",
    "DEFAULT_NODE_FONT_COLOR",
    "DEFAULT_EDGE_COLOR",
    "DEFAULT_EXCLUDE_DIRS",
    "MERMAID_IGNORE_DIRS",
    "MERMAID_STYLING",
    "MERMAID_HEADER",
    "get_mermaid_config",
    "get_color_scheme",
    "REPO_IGNORE_PATTERNS",
    "get_repo_ignore_string",
]
