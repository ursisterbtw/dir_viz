"""Export service for various visualization formats."""

import asyncio
import json
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
import base64

from ..models import DirectoryNode, ExportFormat, ExportRequest, VisualizationSettings
from ..config import config
from .cache_service import CacheService

log = logging.getLogger(__name__)


class ExportService:
    """Service for exporting visualizations to various formats."""
    
    def __init__(self):
        self.cache = CacheService()
        self._executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="export_service"
        )
    
    async def export_visualization(
        self,
        tree_data: DirectoryNode,
        export_request: ExportRequest
    ) -> Dict[str, Any]:
        """
        Export visualization to requested format.
        
        Args:
            tree_data: Directory tree data
            export_request: Export configuration
            
        Returns:
            Export result with file data or download URL
        """
        # Generate cache key
        cache_key = self._generate_export_cache_key(tree_data, export_request)
        
        # Try cache first (for expensive operations like PDF/PNG)
        if export_request.format in [ExportFormat.PDF, ExportFormat.PNG]:
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                log.info(f"Cache hit for export: {export_request.format}")
                return cached_result
        
        try:
            result = await self._export_by_format(tree_data, export_request)
            
            # Cache result for expensive operations
            if export_request.format in [ExportFormat.PDF, ExportFormat.PNG]:
                await self.cache.set(cache_key, result, ttl=600)  # 10 minutes
            
            return result
            
        except Exception as e:
            log.error(f"Export failed for format {export_request.format}: {e}")
            return {
                "success": False,
                "error": str(e),
                "format": export_request.format.value
            }
    
    async def _export_by_format(
        self,
        tree_data: DirectoryNode,
        export_request: ExportRequest
    ) -> Dict[str, Any]:
        """Route export to format-specific handler."""
        handlers = {
            ExportFormat.JSON: self._export_json,
            ExportFormat.SVG: self._export_svg,
            ExportFormat.PNG: self._export_png,
            ExportFormat.PDF: self._export_pdf,
            ExportFormat.MERMAID: self._export_mermaid,
            ExportFormat.DOT: self._export_dot
        }
        
        handler = handlers.get(export_request.format)
        if not handler:
            raise ValueError(f"Unsupported export format: {export_request.format}")
        
        return await handler(tree_data, export_request)
    
    async def _export_json(
        self,
        tree_data: DirectoryNode,
        export_request: ExportRequest
    ) -> Dict[str, Any]:
        """Export as JSON format."""
        data = tree_data.to_d3_format()
        
        # Add metadata
        export_data = {
            "metadata": {
                "exported_at": asyncio.get_event_loop().time(),
                "format": "json",
                "settings": export_request.settings.dict(),
                "source_path": export_request.path
            },
            "tree": data
        }
        
        json_content = json.dumps(export_data, indent=2, default=str)
        
        return {
            "success": True,
            "format": "json",
            "content": json_content,
            "filename": f"directory_tree.json",
            "mime_type": "application/json",
            "size": len(json_content.encode())
        }
    
    async def _export_svg(
        self,
        tree_data: DirectoryNode,
        export_request: ExportRequest
    ) -> Dict[str, Any]:
        """Export as SVG format."""
        loop = asyncio.get_event_loop()
        svg_content = await loop.run_in_executor(
            self._executor,
            self._generate_svg_sync,
            tree_data,
            export_request.settings
        )
        
        return {
            "success": True,
            "format": "svg",
            "content": svg_content,
            "filename": f"directory_tree.svg",
            "mime_type": "image/svg+xml",
            "size": len(svg_content.encode())
        }
    
    async def _export_png(
        self,
        tree_data: DirectoryNode,
        export_request: ExportRequest
    ) -> Dict[str, Any]:
        """Export as PNG format (requires additional dependencies)."""
        try:
            # First generate SVG
            svg_result = await self._export_svg(tree_data, export_request)
            svg_content = svg_result["content"]
            
            # Convert SVG to PNG (this would require cairosvg or similar)
            loop = asyncio.get_event_loop()
            png_data = await loop.run_in_executor(
                self._executor,
                self._svg_to_png_sync,
                svg_content,
                export_request.high_resolution
            )
            
            # Encode as base64 for JSON response
            png_base64 = base64.b64encode(png_data).decode()
            
            return {
                "success": True,
                "format": "png",
                "content": png_base64,
                "filename": f"directory_tree.png",
                "mime_type": "image/png",
                "size": len(png_data),
                "encoding": "base64"
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "PNG export requires cairosvg package: pip install cairosvg",
                "format": "png"
            }
    
    async def _export_pdf(
        self,
        tree_data: DirectoryNode,
        export_request: ExportRequest
    ) -> Dict[str, Any]:
        """Export as PDF format."""
        try:
            # First generate SVG
            svg_result = await self._export_svg(tree_data, export_request)
            svg_content = svg_result["content"]
            
            # Convert SVG to PDF
            loop = asyncio.get_event_loop()
            pdf_data = await loop.run_in_executor(
                self._executor,
                self._svg_to_pdf_sync,
                svg_content
            )
            
            # Encode as base64 for JSON response
            pdf_base64 = base64.b64encode(pdf_data).decode()
            
            return {
                "success": True,
                "format": "pdf",
                "content": pdf_base64,
                "filename": f"directory_tree.pdf",
                "mime_type": "application/pdf",
                "size": len(pdf_data),
                "encoding": "base64"
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "PDF export requires cairosvg package: pip install cairosvg",
                "format": "pdf"
            }
    
    async def _export_mermaid(
        self,
        tree_data: DirectoryNode,
        export_request: ExportRequest
    ) -> Dict[str, Any]:
        """Export as Mermaid diagram format."""
        loop = asyncio.get_event_loop()
        mermaid_content = await loop.run_in_executor(
            self._executor,
            self._generate_mermaid_sync,
            tree_data,
            export_request.settings
        )
        
        return {
            "success": True,
            "format": "mermaid",
            "content": mermaid_content,
            "filename": f"directory_tree.mermaid",
            "mime_type": "text/plain",
            "size": len(mermaid_content.encode())
        }
    
    async def _export_dot(
        self,
        tree_data: DirectoryNode,
        export_request: ExportRequest
    ) -> Dict[str, Any]:
        """Export as DOT (Graphviz) format."""
        loop = asyncio.get_event_loop()
        dot_content = await loop.run_in_executor(
            self._executor,
            self._generate_dot_sync,
            tree_data,
            export_request.settings
        )
        
        return {
            "success": True,
            "format": "dot",
            "content": dot_content,
            "filename": f"directory_tree.dot",
            "mime_type": "text/plain",
            "size": len(dot_content.encode())
        }
    
    def _generate_svg_sync(
        self,
        tree_data: DirectoryNode,
        settings: VisualizationSettings
    ) -> str:
        """Generate SVG content synchronously."""
        # This would implement D3.js-like tree generation in Python
        # For now, return a basic SVG structure
        
        width = 800
        height = 600
        
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <style>
            .node-circle {{ fill: {config.color_scheme["node_color"]}; stroke: #fff; stroke-width: 2px; }}
            .node-text {{ font-family: Arial, sans-serif; font-size: 12px; fill: {config.color_scheme["node_font_color"]}; }}
            .link {{ fill: none; stroke: {config.color_scheme["edge_color"]}; stroke-width: 2px; }}
        </style>
    </defs>
    <rect width="100%" height="100%" fill="{config.color_scheme["bg_color"]}" />
    {self._generate_svg_nodes(tree_data, 0, 0, settings)}
</svg>'''
        
        return svg_content
    
    def _generate_svg_nodes(
        self,
        node: DirectoryNode,
        x: int,
        y: int,
        settings: VisualizationSettings,
        level: int = 0
    ) -> str:
        """Generate SVG nodes recursively."""
        if level > settings.max_depth:
            return ""
        
        svg_parts = []
        
        # Node circle
        svg_parts.append(f'<circle cx="{x}" cy="{y}" r="8" class="node-circle" />')
        
        # Node text
        svg_parts.append(f'<text x="{x + 15}" y="{y + 4}" class="node-text">{node.name}</text>')
        
        # Children
        child_y = y + 40
        child_x_offset = 0
        
        for child in node.children:
            child_x = x + child_x_offset
            
            # Link to child
            svg_parts.append(f'<line x1="{x}" y1="{y}" x2="{child_x}" y2="{child_y}" class="link" />')
            
            # Recursive child nodes
            svg_parts.append(self._generate_svg_nodes(child, child_x, child_y, settings, level + 1))
            
            child_x_offset += 150
        
        return "\n".join(svg_parts)
    
    def _svg_to_png_sync(self, svg_content: str, high_resolution: bool = False) -> bytes:
        """Convert SVG to PNG synchronously."""
        try:
            import cairosvg
            
            scale = 2 if high_resolution else 1
            
            png_data = cairosvg.svg2png(
                bytestring=svg_content.encode(),
                output_width=800 * scale,
                output_height=600 * scale
            )
            
            return png_data
            
        except ImportError:
            raise ImportError("cairosvg package required for PNG export")
    
    def _svg_to_pdf_sync(self, svg_content: str) -> bytes:
        """Convert SVG to PDF synchronously."""
        try:
            import cairosvg
            
            pdf_data = cairosvg.svg2pdf(bytestring=svg_content.encode())
            return pdf_data
            
        except ImportError:
            raise ImportError("cairosvg package required for PDF export")
    
    def _generate_mermaid_sync(
        self,
        tree_data: DirectoryNode,
        settings: VisualizationSettings
    ) -> str:
        """Generate Mermaid diagram content synchronously."""
        lines = ["graph TD"]
        
        def add_node(node: DirectoryNode, parent_id: Optional[str] = None, level: int = 0):
            if level > settings.max_depth:
                return
            
            node_id = self._sanitize_mermaid_id(node.id)
            node_label = node.name.replace('"', '\\"')
            
            if node.type.value == "directory":
                lines.append(f'    {node_id}["{node_label}"]')
            else:
                lines.append(f'    {node_id}("{node_label}")')
            
            if parent_id:
                lines.append(f'    {parent_id} --> {node_id}')
            
            for child in node.children:
                add_node(child, node_id, level + 1)
        
        add_node(tree_data)
        
        # Add styling
        lines.extend([
            f'    classDef default fill:{config.color_scheme["node_fill"]},stroke:{config.color_scheme["node_color"]},color:{config.color_scheme["node_font_color"]}',
            f'    classDef directory fill:{config.color_scheme["node_color"]},stroke:#fff,color:#000'
        ])
        
        return "\n".join(lines)
    
    def _generate_dot_sync(
        self,
        tree_data: DirectoryNode,
        settings: VisualizationSettings
    ) -> str:
        """Generate DOT (Graphviz) content synchronously."""
        lines = [
            "digraph DirectoryTree {",
            "    node [fontname=\"Arial\", fontsize=10];",
            "    edge [color=\"#32CD32\"];",
            f'    bgcolor="{config.color_scheme["bg_color"]}";'
        ]
        
        def add_dot_node(node: DirectoryNode, level: int = 0):
            if level > settings.max_depth:
                return
            
            node_id = self._sanitize_dot_id(node.id)
            node_label = node.name.replace('"', '\\"')
            
            if node.type.value == "directory":
                lines.append(f'    {node_id} [label="{node_label}", shape=folder, fillcolor="{config.color_scheme["node_color"]}", style=filled];')
            else:
                lines.append(f'    {node_id} [label="{node_label}", shape=note, fillcolor="{config.color_scheme["node_fill"]}", style=filled];')
            
            for child in node.children:
                child_id = self._sanitize_dot_id(child.id)
                lines.append(f'    {node_id} -> {child_id};')
                add_dot_node(child, level + 1)
        
        add_dot_node(tree_data)
        lines.append("}")
        
        return "\n".join(lines)
    
    def _sanitize_mermaid_id(self, node_id: str) -> str:
        """Sanitize node ID for Mermaid format."""
        return "".join(c if c.isalnum() else "_" for c in str(hash(node_id)))[:8]
    
    def _sanitize_dot_id(self, node_id: str) -> str:
        """Sanitize node ID for DOT format."""
        return f"node_{abs(hash(node_id))}"
    
    def _generate_export_cache_key(
        self,
        tree_data: DirectoryNode,
        export_request: ExportRequest
    ) -> str:
        """Generate cache key for export operations."""
        import hashlib
        
        key_data = {
            "tree_id": tree_data.id,
            "format": export_request.format.value,
            "settings": export_request.settings.dict(),
            "high_resolution": export_request.high_resolution
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def __del__(self):
        """Cleanup thread pool."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)