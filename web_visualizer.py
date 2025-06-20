#!/usr/bin/env python3
"""
Web Visualizer CLI launcher.

Simple script to launch the D3.js Interactive Web Visualizer.
"""

import sys
from pathlib import Path

# Add web_visualizer to path
sys.path.insert(0, str(Path(__file__).parent / "web_visualizer"))

from web_visualizer.main import run_sync

if __name__ == "__main__":
    run_sync()