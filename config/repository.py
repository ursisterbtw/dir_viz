"""Configuration for repository analysis tools."""

from typing import Dict, List

# Repository ignore patterns for repomix analysis
REPO_IGNORE_PATTERNS: List[str] = [
    "**/*.png",
    "**/*.jpg",
    "**/*.jpeg",
    "**/*.gif",
    "**/*.bmp",
    "**/*.svg",
    "**/*.ico",
    "**/*.webp",
    "**/*.mp4",
    "**/*.mov",
    "**/*.avi",
    "**/*.webm",
    "**/*.mp3",
    "**/*.wav",
    "**/*.ogg",
    "**/*.flac",
    "**/*.pdf",
    "**/*.doc",
    "**/*.docx",
    "**/*.ppt",
    "**/*.pptx",
    "**/*.xls",
    "**/*.xlsx",
    "**/*.zip",
    "**/*.tar",
    "**/*.gz",
    "**/*.rar",
    "**/*.7z",
    "**/*.exe",
    "**/*.dll",
    "**/*.so",
    "**/*.dylib",
    "**/*.pyc",
    "**/*.class",
    "**/*.o",
    "**/*.obj",
    "**/*.min.js",
    "**/*.min.css",
    "**/*.map",
    "**/*.lock",
    "**/*.log",
    "**/*.tmp",
    "**/*.temp",
    "**/*.swp",
    "**/*.swo",
    "**/*.cache",
    "**/.DS_Store",
    "**/.Thumbs.db",
    "**/.eslintcache",
    "**/.stylelintcache",
    "**/node_modules/**",
    "**/vendor/**",
    "**/.venv/**",
    "**/venv/**",
    "**/env/**",
    "**/bower_components/**",
    "**/logs/**",
    "**/coverage/**",
    "**/.nyc_output/**",
    "**/__pycache__/**",
    "**/dist/**",
    "**/build/**",
    "**/out/**",
    "**/.idea/**",
    "**/.vscode/**",
    "**/.git/**",
    "**/test-results/**",
    "**/jest-cache/**",
    "**/.awcache/**",
    "**/.terraform/**",
    "**/.next/**",
]

# Repository processing configuration
REPO_CONFIG: Dict[str, any] = {
    "default_branch": "main",
    "clone_depth": 1,
    "timeout_seconds": 300,
    "parallel_repos": 4,
    "temp_dir_prefix": "repo_",
    "output_format": "xml",
    "verbose": True,
}


def get_repo_ignore_string() -> str:
    """Get repository ignore patterns as a single string."""
    return ",".join(REPO_IGNORE_PATTERNS)


def get_repomix_command_base() -> List[str]:
    """Get base repomix command arguments."""
    return ["npx", "repomix", "--ignore", get_repo_ignore_string(), "--verbose"]
