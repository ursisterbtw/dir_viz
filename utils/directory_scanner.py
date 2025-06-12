"""Directory scanning utilities for flowcharter tools."""

import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path
from typing import Dict, Generator, Optional, Set, Tuple

from tqdm import tqdm

log = logging.getLogger(__name__)


class ExclusionFilter:
    """Optimized exclusion filter with pre-compiled patterns and caching."""

    def __init__(self, exclude_patterns: Set[str]):
        self.exclude_patterns = exclude_patterns
        self.literal_patterns = {
            p for p in exclude_patterns if "*" not in p and "?" not in p
        }
        self.compiled_patterns = self._compile_wildcard_patterns(exclude_patterns)

    def _compile_wildcard_patterns(self, patterns: Set[str]) -> list:
        """Pre-compile wildcard patterns for better performance."""
        compiled = []
        for pattern in patterns:
            if "*" in pattern or "?" in pattern:
                # Convert shell wildcards to regex
                regex_pattern = pattern.replace("*", ".*").replace("?", ".")
                compiled.append(re.compile(f"^{regex_pattern}$"))
        return compiled

    @lru_cache(maxsize=2048)
    def should_exclude(self, entry_name: str) -> bool:
        """Cached exclusion check with optimized pattern matching."""
        # Exclude dot directories by default
        if entry_name.startswith("."):
            return True

        # Direct matches (fastest)
        if entry_name in self.literal_patterns:
            return True

        # Compiled regex patterns
        return any(pattern.match(entry_name) for pattern in self.compiled_patterns)


def should_exclude(entry_name: str, exclude_patterns: Set[str]) -> bool:
    """Legacy function for backward compatibility."""
    filter_obj = ExclusionFilter(exclude_patterns)
    return filter_obj.should_exclude(entry_name)


class DirectoryScanner:
    """Unified directory scanning interface for all tools."""

    def __init__(
        self,
        exclude_patterns: Optional[Set[str]] = None,
        max_depth: int = 5,
        max_workers: int = 4,
        show_progress: bool = True,
    ):
        """
        Initialize directory scanner.

        Args:
            exclude_patterns: Patterns to exclude from scanning
            max_depth: Maximum recursion depth
            max_workers: Maximum parallel workers
            show_progress: Whether to show progress bar
        """
        self.exclude_patterns = exclude_patterns or set()
        self.max_depth = max_depth
        self.max_workers = max_workers
        self.show_progress = show_progress
        self._executor = None  # Shared ThreadPoolExecutor for parallel scans
        self._exclusion_filter = ExclusionFilter(self.exclude_patterns)

    def scan_sequential(
        self, path: Path, current_depth: int = 0
    ) -> Dict[str, Optional[Dict]]:
        """
        Scan directory sequentially (single-threaded).

        Args:
            path: Directory path to scan
            current_depth: Current recursion depth

        Returns:
            Directory structure as nested dictionaries
        """
        if current_depth >= self.max_depth:
            return {"... (max depth reached)": None}

        structure: Dict[str, Optional[Dict]] = {}

        try:
            # Use scandir iterator directly to avoid loading full directory into memory
            entries_iter = os.scandir(path)
            if self.show_progress and current_depth == 0:
                # Only show progress for large operations (>100 entries)
                entries_list = list(entries_iter)
                # Enable progress bar only for large directories (>100 entries) to optimize performance
                # and provide meaningful feedback to the user during lengthy operations.
                if len(entries_list) > 100:
                    entries_iter = tqdm(
                        entries_list, desc="Scanning directory", unit="items"
                    )
                else:
                    entries_iter = entries_list

            for entry in entries_iter:
                if self._exclusion_filter.should_exclude(entry.name):
                    continue

                # Skip symlinks to avoid cycles
                if entry.is_symlink():
                    structure[f"{entry.name} (symlink)"] = None
                    continue

                try:
                    if entry.is_dir(follow_symlinks=False):
                        structure[entry.name] = self.scan_sequential(
                            Path(entry.path), current_depth + 1
                        )
                    elif entry.is_file(follow_symlinks=False):
                        structure[entry.name] = None
                except OSError as e:
                    log.warning("Could not access metadata for %s: %s", entry.path, e)
                    structure[f"{entry.name} (access error)"] = None

        except PermissionError:
            log.warning("Permission denied accessing directory: %s", path)
            return {"Permission denied": None}
        except FileNotFoundError:
            log.error("Directory not found: %s", path)
            return {"Not found": None}
        except OSError as e:
            log.error("OS error scanning directory %s: %s", path, e)
            return {f"Error: {e}": None}

        return structure

    def scan_parallel(
        self, path: Path, current_depth: int = 0
    ) -> Dict[str, Optional[Dict]]:
        """
        Scan directory with parallel processing for subdirectories.

        Args:
            path: Directory path to scan
            current_depth: Current recursion depth

        Returns:
            Directory structure as nested dictionaries
        """
        if current_depth >= self.max_depth:
            return {"... (max depth reached)": None}

        structure: Dict[str, Optional[Dict]] = {}

        try:
            entries = []
            for entry in os.scandir(path):
                if self._exclusion_filter.should_exclude(entry.name):
                    continue

                if entry.is_symlink():
                    structure[f"{entry.name} (symlink)"] = None
                    continue

                try:
                    if entry.is_dir(follow_symlinks=False):
                        entries.append(("dir", entry.name, Path(entry.path)))
                    elif entry.is_file(follow_symlinks=False):
                        structure[entry.name] = None
                except OSError as e:
                    log.warning("Could not access metadata for %s: %s", entry.path, e)
                    structure[f"{entry.name} (access error)"] = None

            # Use parallel processing for larger directories near the top
            if current_depth < 2 and len(entries) > 5:
                dirs_to_process = [
                    (name, p) for kind, name, p in entries if kind == "dir"
                ]

                # Use managed executor for better resource control
                if self._executor is None:
                    self._executor = ThreadPoolExecutor(
                        max_workers=self.max_workers, thread_name_prefix="dir_scan"
                    )

                future_to_dir = {
                    self._executor.submit(
                        self.scan_parallel,
                        dir_path,
                        current_depth + 1,
                    ): dir_name
                    for dir_name, dir_path in dirs_to_process
                }

                # Process results as they complete for better responsiveness
                from concurrent.futures import as_completed

                for future in as_completed(future_to_dir):
                    dir_name = future_to_dir[future]
                    try:
                        structure[dir_name] = future.result()
                    except (IOError, OSError, RuntimeError) as e:
                        log.warning("Failed to scan %s: %s", dir_name, e)
                        structure[dir_name] = None
            else:
                # Process sequentially for smaller directories or deeper levels
                for kind, name, p in entries:
                    if kind == "dir":
                        structure[name] = self.scan_parallel(p, current_depth + 1)

        except PermissionError:
            log.warning("Permission denied accessing directory: %s", path)
            return {"Permission denied": None}
        except FileNotFoundError:
            log.error("Directory not found: %s", path)
            return {"Not found": None}
        except OSError as e:
            log.error("OS error scanning directory %s: %s", path, e)
            return {f"Error: {e}": None}

        return structure

    def scan(self, path: Path, use_parallel: bool = False) -> Dict[str, Optional[Dict]]:
        """
        Scan directory with specified method.

        Args:
            path: Directory path to scan
            use_parallel: Whether to use parallel scanning

        Returns:
            Directory structure as nested dictionaries
        """
        return self.scan_parallel(path) if use_parallel else self.scan_sequential(path)

    def scan_generator(
        self, path: Path, current_depth: int = 0
    ) -> Generator[Tuple[Path, str, int], None, None]:
        """
        Memory-optimized generator-based directory scanning.

        Yields file paths as they are discovered instead of building entire structure in memory.

        Args:
            path: Directory path to scan
            current_depth: Current recursion depth

        Yields:
            Tuple of (path, type, depth) where type is 'file' or 'dir'
        """
        if current_depth >= self.max_depth:
            return

        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    if self._exclusion_filter.should_exclude(entry.name):
                        continue

                    if entry.is_symlink():
                        yield (Path(entry.path), "symlink", current_depth)
                        continue

                    try:
                        if entry.is_dir(follow_symlinks=False):
                            entry_path = Path(entry.path)
                            yield (entry_path, "dir", current_depth)
                            # Recursively yield from subdirectory
                            yield from self.scan_generator(
                                entry_path, current_depth + 1
                            )
                        elif entry.is_file(follow_symlinks=False):
                            yield (Path(entry.path), "file", current_depth)
                    except OSError as e:
                        log.warning(
                            "Could not access metadata for %s: %s", entry.path, e
                        )
                        yield (Path(entry.path), "error", current_depth)

        except OSError as e:
            log.warning("Error scanning %s: %s", path, e)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup thread pool."""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
