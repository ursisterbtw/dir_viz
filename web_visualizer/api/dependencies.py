"""Dependency injection for API routes."""

from functools import lru_cache
from fastapi import Depends

from ..services import (
    DirectoryService,
    FileService,
    ExportService,
    WebSocketService
)


@lru_cache()
def get_directory_service() -> DirectoryService:
    """Get directory service instance."""
    return DirectoryService()


@lru_cache()
def get_file_service() -> FileService:
    """Get file service instance."""
    return FileService()


@lru_cache()
def get_export_service() -> ExportService:
    """Get export service instance."""
    return ExportService()


@lru_cache()
def get_websocket_service() -> WebSocketService:
    """Get WebSocket service instance."""
    return WebSocketService()


# Dependency shortcuts for use in route handlers
DirectoryServiceDep = Depends(get_directory_service)
FileServiceDep = Depends(get_file_service)
ExportServiceDep = Depends(get_export_service)
WebSocketServiceDep = Depends(get_websocket_service)