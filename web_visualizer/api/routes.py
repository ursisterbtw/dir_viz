"""API routes for the web visualizer."""

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..models import (
    DirectoryNode,
    ExportRequest,
    ExportFormat,
    VisualizationSettings,
    GitHistoryRequest
)
from ..services import DirectoryService, FileService, ExportService, WebSocketService
from .dependencies import (
    DirectoryServiceDep,
    FileServiceDep, 
    ExportServiceDep,
    WebSocketServiceDep
)
from .middleware import limiter

log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "web_visualizer"}


@router.post("/api/validate-path")
@limiter.limit("10/minute")
async def validate_path(
    request: Request,
    path_data: Dict[str, str],
    directory_service: DirectoryService = DirectoryServiceDep
):
    """Validate if a directory path is accessible."""
    try:
        path = path_data.get("path")
        if not path:
            raise HTTPException(status_code=400, detail="Path is required")
        
        validation_result = await directory_service.validate_path(path)
        return validation_result
        
    except Exception as e:
        log.error(f"Path validation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/scan-directory")
@limiter.limit("5/minute")
async def scan_directory(
    request: Request,
    scan_request: Dict[str, Any],
    directory_service: DirectoryService = DirectoryServiceDep
):
    """Scan directory and return tree structure."""
    try:
        path = scan_request.get("path")
        max_depth = scan_request.get("max_depth", 5)
        use_cache = scan_request.get("use_cache", True)
        
        if not path:
            raise HTTPException(status_code=400, detail="Path is required")
        
        # Validate path first
        validation = await directory_service.validate_path(path)
        if not validation["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid path: {', '.join(validation['errors'])}"
            )
        
        # Perform scan
        tree_data = await directory_service.scan_directory(
            path=path,
            max_depth=max_depth,
            use_cache=use_cache
        )
        
        return {
            "success": True,
            "tree": tree_data.to_d3_format(),
            "metadata": {
                "path": path,
                "max_depth": max_depth,
                "file_count": tree_data.file_count,
                "dir_count": tree_data.dir_count
            }
        }
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error(f"Directory scan error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/directory-stats")
@limiter.limit("10/minute")
async def get_directory_stats(
    request: Request,
    path: str = Query(..., description="Directory path"),
    directory_service: DirectoryService = DirectoryServiceDep
):
    """Get statistics for a directory."""
    try:
        stats = await directory_service.get_directory_stats(path)
        return stats
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error(f"Directory stats error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/file-content")
@limiter.limit("30/minute")
async def get_file_content(
    request: Request,
    file_path: str = Query(..., description="File path"),
    max_lines: Optional[int] = Query(None, description="Maximum lines to read"),
    encoding: str = Query("utf-8", description="File encoding"),
    file_service: FileService = FileServiceDep
):
    """Get file content with preview."""
    try:
        content_data = await file_service.get_file_content(
            file_path=file_path,
            max_lines=max_lines,
            encoding=encoding
        )
        return content_data
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error(f"File content error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/file-info")
@limiter.limit("30/minute")
async def get_file_info(
    request: Request,
    file_path: str = Query(..., description="File path"),
    file_service: FileService = FileServiceDep
):
    """Get detailed file information."""
    try:
        file_info = await file_service.get_file_info(file_path)
        return file_info
        
    except Exception as e:
        log.error(f"File info error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/export")
@limiter.limit("3/minute")
async def export_visualization(
    request: Request,
    export_request: ExportRequest,
    directory_service: DirectoryService = DirectoryServiceDep,
    export_service: ExportService = ExportServiceDep
):
    """Export visualization to specified format."""
    try:
        # First get the tree data
        tree_data = await directory_service.scan_directory(
            path=export_request.path,
            max_depth=export_request.settings.max_depth,
            use_cache=True
        )
        
        # Export to requested format
        export_result = await export_service.export_visualization(
            tree_data=tree_data,
            export_request=export_request
        )
        
        if not export_result.get("success", False):
            raise HTTPException(
                status_code=500,
                detail=export_result.get("error", "Export failed")
            )
        
        return export_result
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/export-formats")
async def get_export_formats():
    """Get list of supported export formats."""
    return {
        "formats": [
            {
                "id": fmt.value,
                "name": fmt.value.upper(),
                "description": f"Export as {fmt.value.upper()} format",
                "mime_type": {
                    "svg": "image/svg+xml",
                    "png": "image/png",
                    "pdf": "application/pdf",
                    "json": "application/json",
                    "mermaid": "text/plain",
                    "dot": "text/plain"
                }.get(fmt.value, "application/octet-stream")
            }
            for fmt in ExportFormat
        ]
    }


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None),
    room_id: Optional[str] = Query(None),
    websocket_service: WebSocketService = WebSocketServiceDep
):
    """WebSocket endpoint for real-time collaboration."""
    await websocket_service.handle_websocket(
        websocket=websocket,
        user_id=user_id,
        room_id=room_id
    )


@router.get("/api/websocket-stats")
@limiter.limit("10/minute")
async def get_websocket_stats(
    request: Request,
    websocket_service: WebSocketService = WebSocketServiceDep
):
    """Get WebSocket connection statistics."""
    try:
        stats = websocket_service.get_connection_stats()
        return stats
    except Exception as e:
        log.error(f"WebSocket stats error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/room-annotations")
@limiter.limit("20/minute")
async def get_room_annotations(
    request: Request,
    room_id: str = Query(..., description="Room ID"),
    websocket_service: WebSocketService = WebSocketServiceDep
):
    """Get annotations for a specific room."""
    try:
        annotations = websocket_service.get_room_annotations(room_id)
        return {"annotations": annotations}
    except Exception as e:
        log.error(f"Room annotations error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/config")
async def get_config():
    """Get visualization configuration."""
    from ..config import config
    
    return {
        "color_scheme": config.color_scheme,
        "neon_colors": config.neon_colors,
        "max_depth": config.max_depth,
        "max_file_size_mb": config.max_file_size_mb,
        "preview_max_lines": config.preview_max_lines,
        "preview_supported_extensions": list(config.preview_supported_extensions)
    }


@router.get("/api/cache-stats")
@limiter.limit("5/minute")
async def get_cache_stats(
    request: Request,
    directory_service: DirectoryService = DirectoryServiceDep
):
    """Get cache statistics."""
    try:
        stats = await directory_service.cache.get_stats()
        return stats
    except Exception as e:
        log.error(f"Cache stats error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/clear-cache")
@limiter.limit("2/minute")
async def clear_cache(
    request: Request,
    directory_service: DirectoryService = DirectoryServiceDep,
    file_service: FileService = FileServiceDep,
    export_service: ExportService = ExportServiceDep
):
    """Clear all caches."""
    try:
        await directory_service.cache.clear()
        await file_service.cache.clear()
        await export_service.cache.clear()
        
        return {"success": True, "message": "All caches cleared"}
    except Exception as e:
        log.error(f"Cache clear error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Error handlers (moved to main.py where they belong in FastAPI)


# Exception handlers removed - should be in main.py