"""Configuration for Mermaid diagram generation."""

from typing import Dict, List, Set

# Directories to ignore in Mermaid diagrams
MERMAID_IGNORE_DIRS: Set[str] = {
    "target",
    ".git",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
    "env",
    ".env",
    ".idea",
    ".vscode",
    "*.cache",
    "*.egg-info",
    "out",
    "bin",
    "lib",
    "obj",
    ".tox",
    ".pytest_cache",
}

# Mermaid diagram styling configuration
MERMAID_STYLING: List[str] = [
    "    %% Styling",
    "    classDef default stroke:#333,stroke-width:1px",
    "    classDef directory fill:#e3f2fd,stroke:#1565c0,stroke-width:2px",
    "    classDef file fill:#f5f5f5,stroke:#616161,stroke-width:1px",
    "    classDef error fill:#fee,stroke:#c00,stroke-width:1px",
]

# Mermaid diagram header configuration
MERMAID_HEADER: List[str] = [
    "%%{init: {'theme': 'base', 'themeVariables': { 'fontSize': '16px' }}}%%",
    "graph LR",
    "    %% Layout settings",
    "    %% Node styling defaults",
]


def get_mermaid_config() -> Dict[str, any]:
    """Get Mermaid diagram configuration."""
    return {
        "ignore_dirs": MERMAID_IGNORE_DIRS,
        "styling": MERMAID_STYLING,
        "header": MERMAID_HEADER,
        "output_filename": "project_structure.mermaid",
    }
