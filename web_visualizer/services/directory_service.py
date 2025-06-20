"""Directory scanning and tree building service."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor
import hashlib

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.directory_scanner import DirectoryScanner
from ..models import DirectoryNode, NodeType
from ..config import config
from .cache_service import CacheService

log = logging.getLogger(__name__)


class DirectoryService:
    """Service for directory operations and tree building."""
    
    def __init__(self):
        self.cache = CacheService()
        self._executor = ThreadPoolExecutor(
            max_workers=config.max_workers,
            thread_name_prefix="dir_service"
        )
    
    async def scan_directory(
        self,
        path: str,
        max_depth: Optional[int] = None,
        use_cache: bool = True
    ) -> DirectoryNode:
        """
        Scan directory and build tree structure.
        
        Args:
            path: Directory path to scan
            max_depth: Maximum depth to scan (None for config default)
            use_cache: Whether to use cached results
            
        Returns:
            Root DirectoryNode with complete tree
        """
        path_obj = Path(path).resolve()
        if not path_obj.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        if not path_obj.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
            
        # Generate cache key
        cache_key = self._generate_cache_key(str(path_obj), max_depth or config.max_depth)
        
        # Try cache first
        if use_cache:
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                log.info(f"Cache hit for directory scan: {path}")
                return DirectoryNode(**cached_result)
        
        log.info(f"Scanning directory: {path} (max_depth: {max_depth or config.max_depth})")
        
        # Perform scan in thread pool
        loop = asyncio.get_event_loop()
        root_node = await loop.run_in_executor(
            self._executor,
            self._scan_directory_sync,
            path_obj,
            max_depth or config.max_depth
        )
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, root_node.dict(), ttl=config.cache_ttl_seconds)
            
        log.info(f"Directory scan completed: {root_node.file_count} files, {root_node.dir_count} directories")
        return root_node
    
    def _scan_directory_sync(self, path: Path, max_depth: int) -> DirectoryNode:
        """Synchronous directory scanning (runs in thread pool)."""
        scanner = DirectoryScanner(
            exclude_patterns=config.exclude_patterns,
            max_depth=max_depth,
            max_workers=1,  # Single threaded within each scan
            show_progress=False
        )
        
        with scanner:
            return self._build_tree_from_path(path, scanner, max_depth)
    
    def _build_tree_from_path(
        self, 
        path: Path, 
        scanner: DirectoryScanner, 
        max_depth: int,
        current_depth: int = 0,
        parent_id: Optional[str] = None
    ) -> DirectoryNode:
        """Build DirectoryNode tree from filesystem path."""
        # Create root node
        root = DirectoryNode.from_path(path, parent_id, current_depth)
        
        if current_depth >= max_depth or root.type != NodeType.DIRECTORY:
            return root
        
        try:
            # Scan children
            for entry_path, entry_type, depth in scanner.scan_generator(path, current_depth):
                if depth != current_depth + 1:  # Only direct children
                    continue
                    
                child_node = DirectoryNode.from_path(entry_path, root.id, depth)
                
                # Recursively build subdirectories
                if child_node.type == NodeType.DIRECTORY and depth < max_depth:
                    child_node = self._build_tree_from_path(
                        entry_path, scanner, max_depth, depth, root.id
                    )
                
                root.add_child(child_node)
                
        except Exception as e:
            log.error(f"Error scanning directory {path}: {e}")
            
        return root
    
    async def get_directory_stats(self, path: str) -> Dict:
        """Get statistics for a directory."""
        cache_key = f"stats:{self._generate_cache_key(path, 1)}"
        
        # Try cache first
        cached_stats = await self.cache.get(cache_key)
        if cached_stats:
            return cached_stats
        
        path_obj = Path(path).resolve()
        if not path_obj.exists() or not path_obj.is_dir():
            raise ValueError(f"Invalid directory path: {path}")
        
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(
            self._executor,
            self._calculate_stats_sync,
            path_obj
        )
        
        # Cache for shorter time
        await self.cache.set(cache_key, stats, ttl=60)
        return stats
    
    def _calculate_stats_sync(self, path: Path) -> Dict:
        """Calculate directory statistics synchronously."""
        scanner = DirectoryScanner(
            exclude_patterns=config.exclude_patterns,
            max_depth=1,
            show_progress=False
        )
        
        stats = {
            "total_files": 0,
            "total_directories": 0,
            "total_size": 0,
            "file_types": {},
            "largest_files": [],
            "recent_files": []
        }
        
        try:
            with scanner:
                for entry_path, entry_type, _ in scanner.scan_generator(path):
                    if entry_type == "file":
                        try:
                            file_stat = entry_path.stat()
                            stats["total_files"] += 1
                            stats["total_size"] += file_stat.st_size
                            
                            # Track file extensions
                            ext = entry_path.suffix.lower()
                            if ext:
                                stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1
                            
                            # Track largest files (top 10)
                            file_info = {
                                "name": entry_path.name,
                                "path": str(entry_path),
                                "size": file_stat.st_size
                            }
                            stats["largest_files"].append(file_info)
                            if len(stats["largest_files"]) > 10:
                                stats["largest_files"].sort(key=lambda x: x["size"], reverse=True)
                                stats["largest_files"] = stats["largest_files"][:10]
                                
                        except OSError:
                            continue
                            
                    elif entry_type == "dir":
                        stats["total_directories"] += 1
                        
        except Exception as e:
            log.error(f"Error calculating stats for {path}: {e}")
            
        return stats
    
    def _generate_cache_key(self, path: str, max_depth: int) -> str:
        """Generate cache key for directory scan."""
        key_data = f"{path}:{max_depth}:{hash(tuple(sorted(config.exclude_patterns)))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def validate_path(self, path: str) -> Dict[str, Any]:
        """Validate if path is accessible and scannable."""
        try:
            path_obj = Path(path).resolve()
            
            validation = {
                "valid": False,
                "exists": path_obj.exists(),
                "is_directory": path_obj.is_dir() if path_obj.exists() else False,
                "readable": False,
                "absolute_path": str(path_obj),
                "errors": []
            }
            
            if not validation["exists"]:
                validation["errors"].append("Path does not exist")
                return validation
                
            if not validation["is_directory"]:
                validation["errors"].append("Path is not a directory")
                return validation
            
            # Test readability
            try:
                list(path_obj.iterdir())
                validation["readable"] = True
                validation["valid"] = True
            except PermissionError:
                validation["errors"].append("Permission denied")
            except OSError as e:
                validation["errors"].append(f"OS error: {e}")
                
            return validation
            
        except Exception as e:
            return {
                "valid": False,
                "exists": False,
                "is_directory": False,
                "readable": False,
                "absolute_path": path,
                "errors": [f"Validation error: {e}"]
            }
    
    def __del__(self):
        """Cleanup thread pool."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)