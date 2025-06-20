"""File operations and content preview service."""

import asyncio
import logging
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import aiofiles
import magic
from concurrent.futures import ThreadPoolExecutor

from ..config import config
from .cache_service import CacheService

log = logging.getLogger(__name__)


class FileService:
    """Service for file operations and content preview."""
    
    def __init__(self):
        self.cache = CacheService()
        self._executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="file_service"
        )
        # Initialize magic for MIME type detection
        try:
            self.magic = magic.Magic(mime=True)
        except Exception:
            self.magic = None
            log.warning("python-magic not available, using mimetypes fallback")
    
    async def get_file_content(
        self,
        file_path: str,
        max_lines: Optional[int] = None,
        encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """
        Get file content with preview capabilities.
        
        Args:
            file_path: Path to the file
            max_lines: Maximum lines to read (None for config default)
            encoding: File encoding
            
        Returns:
            Dict with content, metadata, and preview info
        """
        path_obj = Path(file_path).resolve()
        
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path_obj.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        # Check file size limit
        file_size = path_obj.stat().st_size
        max_size_bytes = config.max_file_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            return {
                "error": f"File too large ({file_size} bytes, max: {max_size_bytes})",
                "file_info": await self.get_file_info(file_path),
                "content": None,
                "truncated": True
            }
        
        # Check if file extension is supported for preview
        if not self._is_previewable(path_obj):
            return {
                "error": "File type not supported for preview",
                "file_info": await self.get_file_info(file_path),
                "content": None,
                "binary": True
            }
        
        # Generate cache key
        cache_key = f"file_content:{path_obj}:{max_lines or config.preview_max_lines}"
        
        # Try cache first
        cached_content = await self.cache.get(cache_key)
        if cached_content:
            return cached_content
        
        try:
            max_lines = max_lines or config.preview_max_lines
            
            # Read file content
            loop = asyncio.get_event_loop()
            content_data = await loop.run_in_executor(
                self._executor,
                self._read_file_sync,
                path_obj,
                max_lines,
                encoding
            )
            
            result = {
                "content": content_data["content"],
                "lines": content_data["lines"],
                "truncated": content_data["truncated"],
                "encoding": encoding,
                "file_info": await self.get_file_info(file_path),
                "syntax_language": self._detect_syntax_language(path_obj),
                "error": None,
                "binary": False
            }
            
            # Cache result for shorter time (file content changes more frequently)
            await self.cache.set(cache_key, result, ttl=60)
            
            return result
            
        except UnicodeDecodeError:
            # Try with different encodings
            for fallback_encoding in ["latin-1", "cp1252", "utf-16"]:
                try:
                    loop = asyncio.get_event_loop()
                    content_data = await loop.run_in_executor(
                        self._executor,
                        self._read_file_sync,
                        path_obj,
                        max_lines,
                        fallback_encoding
                    )
                    
                    result = {
                        "content": content_data["content"],
                        "lines": content_data["lines"],
                        "truncated": content_data["truncated"],
                        "encoding": fallback_encoding,
                        "file_info": await self.get_file_info(file_path),
                        "syntax_language": self._detect_syntax_language(path_obj),
                        "error": f"Used fallback encoding: {fallback_encoding}",
                        "binary": False
                    }
                    
                    return result
                    
                except UnicodeDecodeError:
                    continue
            
            # All encodings failed
            return {
                "error": "Unable to decode file with any supported encoding",
                "file_info": await self.get_file_info(file_path),
                "content": None,
                "binary": True
            }
            
        except Exception as e:
            log.error(f"Error reading file {file_path}: {e}")
            return {
                "error": f"Error reading file: {e}",
                "file_info": await self.get_file_info(file_path),
                "content": None
            }
    
    def _read_file_sync(
        self,
        path: Path,
        max_lines: int,
        encoding: str
    ) -> Dict[str, Any]:
        """Synchronously read file content (runs in thread pool)."""
        content_lines = []
        total_lines = 0
        truncated = False
        
        with open(path, 'r', encoding=encoding) as f:
            for line_num, line in enumerate(f):
                total_lines += 1
                
                if line_num < max_lines:
                    content_lines.append(line.rstrip('\n\r'))
                else:
                    truncated = True
                    # Continue counting lines without storing content
                    for _ in f:
                        total_lines += 1
                    break
        
        return {
            "content": content_lines,
            "lines": total_lines,
            "truncated": truncated
        }
    
    async def get_file_info(self, file_path: str) -> Dict[str, any]:
        """Get detailed file information."""
        cache_key = f"file_info:{file_path}"
        
        # Try cache first
        cached_info = await self.cache.get(cache_key)
        if cached_info:
            return cached_info
        
        try:
            path_obj = Path(file_path)
            stat_info = path_obj.stat()
            
            # Detect MIME type
            mime_type = self._detect_mime_type(path_obj)
            
            file_info = {
                "name": path_obj.name,
                "path": str(path_obj),
                "size": stat_info.st_size,
                "size_human": self._format_file_size(stat_info.st_size),
                "modified": stat_info.st_mtime,
                "created": stat_info.st_ctime,
                "extension": path_obj.suffix.lower(),
                "mime_type": mime_type,
                "is_binary": self._is_binary_file(path_obj),
                "is_previewable": self._is_previewable(path_obj),
                "syntax_language": self._detect_syntax_language(path_obj)
            }
            
            # Cache file info for longer (metadata changes less frequently)
            await self.cache.set(cache_key, file_info, ttl=300)
            
            return file_info
            
        except Exception as e:
            log.error(f"Error getting file info for {file_path}: {e}")
            return {
                "error": f"Error getting file info: {e}",
                "name": Path(file_path).name,
                "path": file_path
            }
    
    def _detect_mime_type(self, path: Path) -> str:
        """Detect MIME type of file."""
        try:
            if self.magic:
                return self.magic.from_file(str(path))
            else:
                mime_type, _ = mimetypes.guess_type(str(path))
                return mime_type or "application/octet-stream"
        except Exception:
            return "application/octet-stream"
    
    def _is_binary_file(self, path: Path) -> bool:
        """Check if file is binary."""
        try:
            with open(path, 'rb') as f:
                chunk = f.read(8192)
                if b'\0' in chunk:
                    return True
                # Check for high ratio of non-printable characters
                non_printable = sum(1 for b in chunk if b < 32 and b not in (9, 10, 13))
                return len(chunk) > 0 and (non_printable / len(chunk)) > 0.3
        except Exception:
            return True
    
    def _is_previewable(self, path: Path) -> bool:
        """Check if file can be previewed as text."""
        if self._is_binary_file(path):
            return False
        
        extension = path.suffix.lower()
        return extension in config.preview_supported_extensions
    
    def _detect_syntax_language(self, path: Path) -> Optional[str]:
        """Detect syntax highlighting language from file extension."""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".scss": "scss",
            ".sass": "sass",
            ".json": "json",
            ".xml": "xml",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".md": "markdown",
            ".txt": "text",
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "bash",
            ".fish": "bash",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".vue": "vue",
            ".php": "php",
            ".rb": "ruby",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".clj": "clojure",
            ".sql": "sql",
            ".r": "r",
            ".R": "r",
            ".m": "matlab",
            ".pl": "perl",
            ".lua": "lua",
            ".vim": "vim"
        }
        
        extension = path.suffix.lower()
        return extension_map.get(extension)
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"
    
    async def search_files(
        self,
        directory: str,
        query: str,
        case_sensitive: bool = False,
        regex: bool = False,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Search for files containing specific content."""
        # This would be implemented using ripgrep or similar
        # For now, return placeholder
        return []
    
    def __del__(self):
        """Cleanup thread pool."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)