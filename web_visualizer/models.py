"""Data models for the web visualizer."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator
import os


class NodeType(str, Enum):
    """Type of directory node."""
    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"
    ERROR = "error"


class FileInfo(BaseModel):
    """Information about a file."""
    name: str
    path: str
    size: Optional[int] = None
    modified: Optional[datetime] = None
    extension: Optional[str] = None
    is_binary: bool = False
    mime_type: Optional[str] = None
    
    @field_validator('extension', mode='before')
    @classmethod
    def extract_extension(cls, v, info):
        if v is None and info.data and 'name' in info.data:
            name = info.data['name']
            if '.' in name:
                return name.split('.')[-1].lower()
        return v


class DirectoryNode(BaseModel):
    """Represents a node in the directory tree."""
    id: str
    name: str
    path: str
    type: NodeType
    parent_id: Optional[str] = None
    children: List['DirectoryNode'] = Field(default_factory=list)
    file_info: Optional[FileInfo] = None
    depth: int = 0
    size: Optional[int] = None
    file_count: int = 0
    dir_count: int = 0
    
    class Config:
        # Enable forward references
        arbitrary_types_allowed = True
        
    @classmethod
    def from_path(cls, path: Path, parent_id: Optional[str] = None, depth: int = 0) -> 'DirectoryNode':
        """Create a DirectoryNode from a filesystem path."""
        try:
            stat_info = path.stat()
            is_dir = path.is_dir()
            is_symlink = path.is_symlink()
            
            node_type = NodeType.SYMLINK if is_symlink else (
                NodeType.DIRECTORY if is_dir else NodeType.FILE
            )
            
            node = cls(
                id=str(path),
                name=path.name,
                path=str(path),
                type=node_type,
                parent_id=parent_id,
                depth=depth,
                size=stat_info.st_size if not is_dir else None
            )
            
            if not is_dir and not is_symlink:
                node.file_info = FileInfo(
                    name=path.name,
                    path=str(path),
                    size=stat_info.st_size,
                    modified=datetime.fromtimestamp(stat_info.st_mtime),
                    is_binary=cls._is_binary_file(path)
                )
                
        except (OSError, PermissionError):
            node = cls(
                id=str(path),
                name=path.name,
                path=str(path),
                type=NodeType.ERROR,
                parent_id=parent_id,
                depth=depth
            )
            
        return node
    
    @staticmethod
    def _is_binary_file(path: Path) -> bool:
        """Check if a file is binary."""
        try:
            with open(path, 'rb') as f:
                chunk = f.read(8192)
                if b'\0' in chunk:
                    return True
                # Check for high ratio of non-printable characters
                non_printable = sum(1 for b in chunk if b < 32 and b not in (9, 10, 13))
                return len(chunk) > 0 and (non_printable / len(chunk)) > 0.3
        except (OSError, PermissionError):
            return True
    
    def add_child(self, child: 'DirectoryNode') -> None:
        """Add a child node and update counts."""
        child.parent_id = self.id
        self.children.append(child)
        
        if child.type == NodeType.FILE:
            self.file_count += 1
        elif child.type == NodeType.DIRECTORY:
            self.dir_count += 1
            # Aggregate counts from subdirectories
            self.file_count += child.file_count
            self.dir_count += child.dir_count
    
    def to_d3_format(self) -> Dict[str, Any]:
        """Convert to D3.js compatible format."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "path": self.path,
            "depth": self.depth,
            "size": self.size,
            "fileCount": self.file_count,
            "dirCount": self.dir_count,
            "children": [child.to_d3_format() for child in self.children],
            "fileInfo": self.file_info.dict() if self.file_info else None
        }


class VisualizationSettings(BaseModel):
    """Settings for visualization rendering."""
    color_scheme: str = "neon"
    show_file_sizes: bool = True
    show_file_counts: bool = True
    max_depth: int = 5
    collapse_large_directories: bool = True
    large_directory_threshold: int = 50
    show_hidden_files: bool = False
    highlight_extensions: List[str] = Field(default_factory=list)
    
    
class Annotation(BaseModel):
    """User annotation for a directory node."""
    id: str
    node_id: str
    user_id: str
    content: str
    type: str = "comment"  # comment, highlight, note
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    position: Optional[Dict[str, float]] = None  # x, y coordinates for positioning
    

class ExportFormat(str, Enum):
    """Supported export formats."""
    SVG = "svg"
    PNG = "png"
    PDF = "pdf"
    JSON = "json"
    MERMAID = "mermaid"
    DOT = "dot"


class ExportRequest(BaseModel):
    """Request for exporting visualization."""
    format: ExportFormat
    path: str
    settings: VisualizationSettings
    include_annotations: bool = False
    high_resolution: bool = False


class GitHistoryRequest(BaseModel):
    """Request for Git history analysis."""
    repository_path: str
    branch: str = "main"
    max_commits: int = 50
    file_patterns: List[str] = Field(default_factory=list)


class WebSocketMessage(BaseModel):
    """WebSocket message structure."""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: Optional[str] = None


# Update forward references
DirectoryNode.model_rebuild()