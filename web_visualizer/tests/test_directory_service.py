"""Tests for directory service."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from web_visualizer.services.directory_service import DirectoryService
from web_visualizer.models import NodeType


@pytest.fixture
def temp_directory():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test structure
        (temp_path / "file1.txt").write_text("Hello World")
        (temp_path / "file2.py").write_text("print('Hello')")
        
        subdir = temp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested_file.md").write_text("# Nested File")
        
        yield temp_path


@pytest.fixture
def directory_service():
    """Create a directory service instance."""
    return DirectoryService()


@pytest.mark.asyncio
async def test_scan_directory_basic(directory_service, temp_directory):
    """Test basic directory scanning."""
    result = await directory_service.scan_directory(str(temp_directory), max_depth=2)
    
    assert result is not None
    assert result.type == NodeType.DIRECTORY
    assert result.name == temp_directory.name
    assert result.file_count >= 3  # At least 3 files
    assert result.dir_count >= 1   # At least 1 directory


@pytest.mark.asyncio
async def test_scan_directory_with_cache(directory_service, temp_directory):
    """Test directory scanning with caching."""
    # First scan
    result1 = await directory_service.scan_directory(str(temp_directory), use_cache=True)
    
    # Second scan should use cache
    with patch.object(directory_service, '_scan_directory_sync') as mock_scan:
        result2 = await directory_service.scan_directory(str(temp_directory), use_cache=True)
        
        # Mock should not be called (cache hit)
        mock_scan.assert_not_called()
        
        # Results should be equivalent
        assert result1.name == result2.name
        assert result1.file_count == result2.file_count


@pytest.mark.asyncio
async def test_validate_path_valid(directory_service, temp_directory):
    """Test path validation with valid path."""
    result = await directory_service.validate_path(str(temp_directory))
    
    assert result["valid"] is True
    assert result["exists"] is True
    assert result["is_directory"] is True
    assert result["readable"] is True
    assert len(result["errors"]) == 0


@pytest.mark.asyncio
async def test_validate_path_invalid(directory_service):
    """Test path validation with invalid path."""
    result = await directory_service.validate_path("/nonexistent/path")
    
    assert result["valid"] is False
    assert result["exists"] is False
    assert len(result["errors"]) > 0
    assert "does not exist" in result["errors"][0]


@pytest.mark.asyncio
async def test_get_directory_stats(directory_service, temp_directory):
    """Test directory statistics calculation."""
    stats = await directory_service.get_directory_stats(str(temp_directory))
    
    assert "total_files" in stats
    assert "total_directories" in stats
    assert "total_size" in stats
    assert "file_types" in stats
    
    assert stats["total_files"] >= 3
    assert stats["total_directories"] >= 1
    assert stats["total_size"] > 0


@pytest.mark.asyncio
async def test_scan_directory_max_depth(directory_service, temp_directory):
    """Test scanning with depth limit."""
    # Create deeper structure
    deep_dir = temp_directory / "level1" / "level2" / "level3"
    deep_dir.mkdir(parents=True)
    (deep_dir / "deep_file.txt").write_text("Deep content")
    
    # Scan with depth limit
    result = await directory_service.scan_directory(str(temp_directory), max_depth=2)
    
    # Should not include files beyond max_depth
    def check_depth(node, current_depth=0):
        assert current_depth <= 2
        for child in node.children:
            check_depth(child, current_depth + 1)
    
    check_depth(result)


def test_generate_cache_key(directory_service):
    """Test cache key generation."""
    key1 = directory_service._generate_cache_key("/path/to/dir", 5)
    key2 = directory_service._generate_cache_key("/path/to/dir", 5)
    key3 = directory_service._generate_cache_key("/path/to/other", 5)
    key4 = directory_service._generate_cache_key("/path/to/dir", 3)
    
    # Same inputs should generate same key
    assert key1 == key2
    
    # Different inputs should generate different keys
    assert key1 != key3
    assert key1 != key4


if __name__ == "__main__":
    pytest.main([__file__])