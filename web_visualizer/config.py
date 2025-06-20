"""Configuration management for web visualizer."""

import os
from typing import Dict, List, Optional, Set
from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path

import sys
from pathlib import Path

# Add parent directory to path to access the root config module
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import from the root config module
import config.visualization as root_config
DEFAULT_EXCLUDE_DIRS = root_config.DEFAULT_EXCLUDE_DIRS
NEON_COLORS = root_config.NEON_COLORS
get_color_scheme = root_config.get_color_scheme


class WebVisualizerConfig(BaseSettings):
    """Configuration settings for the web visualizer application."""
    
    # Server configuration
    host: str = Field(default="127.0.0.1", env="WEB_VIZ_HOST")
    port: int = Field(default=8000, env="WEB_VIZ_PORT")
    debug: bool = Field(default=False, env="WEB_VIZ_DEBUG")
    reload: bool = Field(default=False, env="WEB_VIZ_RELOAD")
    
    # Security configuration
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="WEB_VIZ_SECRET_KEY")
    cors_origins: List[str] = Field(default=["http://localhost:3000"], env="WEB_VIZ_CORS_ORIGINS")
    rate_limit_requests: int = Field(default=100, env="WEB_VIZ_RATE_LIMIT")
    rate_limit_period: int = Field(default=60, env="WEB_VIZ_RATE_LIMIT_PERIOD")
    
    # Directory scanning configuration
    max_depth: int = Field(default=10, env="WEB_VIZ_MAX_DEPTH")
    max_workers: int = Field(default=4, env="WEB_VIZ_MAX_WORKERS")
    exclude_patterns: Set[str] = Field(default_factory=lambda: DEFAULT_EXCLUDE_DIRS)
    max_file_size_mb: int = Field(default=50, env="WEB_VIZ_MAX_FILE_SIZE_MB")
    
    # Cache configuration
    cache_ttl_seconds: int = Field(default=300, env="WEB_VIZ_CACHE_TTL")
    max_cache_entries: int = Field(default=1000, env="WEB_VIZ_MAX_CACHE_ENTRIES")
    
    # File preview configuration
    preview_max_lines: int = Field(default=500, env="WEB_VIZ_PREVIEW_MAX_LINES")
    preview_supported_extensions: Set[str] = Field(
        default_factory=lambda: {
            ".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yml", ".yaml",
            ".md", ".txt", ".sh", ".rs", ".go", ".java", ".cpp", ".c", ".h",
            ".jsx", ".tsx", ".vue", ".php", ".rb", ".swift", ".kt", ".scala"
        }
    )
    
    # WebSocket configuration
    websocket_ping_interval: int = Field(default=20, env="WEB_VIZ_WS_PING_INTERVAL")
    websocket_ping_timeout: int = Field(default=10, env="WEB_VIZ_WS_PING_TIMEOUT")
    
    # Database configuration (for annotations/comments)
    database_url: str = Field(default="sqlite:///./web_visualizer.db", env="WEB_VIZ_DATABASE_URL")
    
    # Static file serving
    static_dir: Path = Field(default=Path(__file__).parent / "static")
    template_dir: Path = Field(default=Path(__file__).parent / "templates")
    
    # Color scheme integration
    color_scheme: Dict[str, str] = Field(default_factory=get_color_scheme)
    neon_colors: List[str] = Field(default_factory=lambda: NEON_COLORS)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def get_uvicorn_config(self) -> Dict:
        """Get configuration for uvicorn server."""
        return {
            "host": self.host,
            "port": self.port,
            "reload": self.reload,
            "access_log": self.debug,
        }


# Global configuration instance
config = WebVisualizerConfig()