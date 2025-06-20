"""
D3.js Interactive Web Visualizer for directory structures.

A FastAPI-based web application that provides interactive directory visualization
using D3.js with real-time features, collaboration tools, and export capabilities.
"""

__version__ = "1.0.0"
__author__ = "dir_viz"

from .api import create_app
from .config import WebVisualizerConfig
from .models import DirectoryNode, FileInfo, VisualizationSettings

__all__ = [
    "create_app",
    "WebVisualizerConfig", 
    "DirectoryNode",
    "FileInfo",
    "VisualizationSettings",
]