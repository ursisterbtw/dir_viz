"""WebSocket service for real-time collaboration."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from ..models import WebSocketMessage, Annotation

log = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time collaboration."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.room_connections: Dict[str, Set[str]] = {}  # room_id -> set of connection_ids
        self.connection_metadata: Dict[str, Dict] = {}  # connection_id -> metadata
    
    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: Optional[str] = None,
        room_id: Optional[str] = None
    ) -> str:
        """Accept WebSocket connection and register it."""
        await websocket.accept()
        
        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "room_id": room_id,
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "ip_address": websocket.client.host if websocket.client else None
        }
        
        # Track user connections
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        # Track room connections
        if room_id:
            if room_id not in self.room_connections:
                self.room_connections[room_id] = set()
            self.room_connections[room_id].add(connection_id)
        
        log.info(f"WebSocket connected: {connection_id} (user: {user_id}, room: {room_id})")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "data": {
                "connection_id": connection_id,
                "timestamp": datetime.now().isoformat()
            }
        }, connection_id)
        
        # Notify room about new connection
        if room_id:
            await self.broadcast_to_room({
                "type": "user_joined",
                "data": {
                    "user_id": user_id,
                    "connection_id": connection_id,
                    "timestamp": datetime.now().isoformat()
                }
            }, room_id, exclude=[connection_id])
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Disconnect and cleanup WebSocket connection."""
        if connection_id not in self.active_connections:
            return
        
        metadata = self.connection_metadata.get(connection_id, {})
        user_id = metadata.get("user_id")
        room_id = metadata.get("room_id")
        
        # Remove from active connections
        del self.active_connections[connection_id]
        del self.connection_metadata[connection_id]
        
        # Remove from user connections
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove from room connections
        if room_id and room_id in self.room_connections:
            self.room_connections[room_id].discard(connection_id)
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]
        
        log.info(f"WebSocket disconnected: {connection_id} (user: {user_id}, room: {room_id})")
        
        # Notify room about disconnection
        if room_id and room_id in self.room_connections:
            await self.broadcast_to_room({
                "type": "user_left",
                "data": {
                    "user_id": user_id,
                    "connection_id": connection_id,
                    "timestamp": datetime.now().isoformat()
                }
            }, room_id)
    
    async def send_personal_message(self, message: Dict, connection_id: str):
        """Send message to specific connection."""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
                
                # Update last activity
                if connection_id in self.connection_metadata:
                    self.connection_metadata[connection_id]["last_activity"] = datetime.now()
                    
            except Exception as e:
                log.error(f"Error sending message to {connection_id}: {e}")
                await self.disconnect(connection_id)
    
    async def send_to_user(self, message: Dict, user_id: str):
        """Send message to all connections of a specific user."""
        if user_id in self.user_connections:
            tasks = []
            for connection_id in self.user_connections[user_id].copy():
                tasks.append(self.send_personal_message(message, connection_id))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_room(
        self,
        message: Dict,
        room_id: str,
        exclude: Optional[List[str]] = None
    ):
        """Broadcast message to all connections in a room."""
        if room_id not in self.room_connections:
            return
        
        exclude = exclude or []
        tasks = []
        
        for connection_id in self.room_connections[room_id].copy():
            if connection_id not in exclude:
                tasks.append(self.send_personal_message(message, connection_id))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_all(self, message: Dict, exclude: Optional[List[str]] = None):
        """Broadcast message to all active connections."""
        exclude = exclude or []
        tasks = []
        
        for connection_id in list(self.active_connections.keys()):
            if connection_id not in exclude:
                tasks.append(self.send_personal_message(message, connection_id))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_room_users(self, room_id: str) -> List[Dict]:
        """Get list of users in a room."""
        if room_id not in self.room_connections:
            return []
        
        users = []
        seen_users = set()
        
        for connection_id in self.room_connections[room_id]:
            metadata = self.connection_metadata.get(connection_id, {})
            user_id = metadata.get("user_id")
            
            if user_id and user_id not in seen_users:
                users.append({
                    "user_id": user_id,
                    "connected_at": metadata.get("connected_at"),
                    "last_activity": metadata.get("last_activity"),
                    "connection_count": len(self.user_connections.get(user_id, set()))
                })
                seen_users.add(user_id)
        
        return users
    
    def get_connection_stats(self) -> Dict:
        """Get connection statistics."""
        return {
            "total_connections": len(self.active_connections),
            "unique_users": len(self.user_connections),
            "active_rooms": len(self.room_connections),
            "connections_per_room": {
                room_id: len(connections)
                for room_id, connections in self.room_connections.items()
            }
        }


class WebSocketService:
    """Service for handling WebSocket communication and collaboration features."""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.annotations: Dict[str, List[Annotation]] = {}  # room_id -> annotations
        self.message_handlers = {
            "ping": self._handle_ping,
            "add_annotation": self._handle_add_annotation,
            "update_annotation": self._handle_update_annotation,
            "delete_annotation": self._handle_delete_annotation,
            "cursor_move": self._handle_cursor_move,
            "selection_change": self._handle_selection_change,
            "request_room_state": self._handle_request_room_state
        }
    
    async def handle_websocket(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None,
        room_id: Optional[str] = None
    ):
        """Handle WebSocket connection lifecycle."""
        connection_id = str(uuid.uuid4())
        
        try:
            await self.connection_manager.connect(websocket, connection_id, user_id, room_id)
            
            while True:
                try:
                    # Receive message
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    # Validate message structure
                    try:
                        message = WebSocketMessage(**message_data)
                        message.user_id = user_id  # Set user_id from connection
                    except ValidationError as e:
                        await self.connection_manager.send_personal_message({
                            "type": "error",
                            "data": {"error": f"Invalid message format: {e}"}
                        }, connection_id)
                        continue
                    
                    # Handle message
                    await self._handle_message(message, connection_id, room_id)
                    
                except WebSocketDisconnect:
                    break
                except json.JSONDecodeError:
                    await self.connection_manager.send_personal_message({
                        "type": "error",
                        "data": {"error": "Invalid JSON"}
                    }, connection_id)
                except Exception as e:
                    log.error(f"Error handling WebSocket message: {e}")
                    await self.connection_manager.send_personal_message({
                        "type": "error",
                        "data": {"error": "Internal server error"}
                    }, connection_id)
        
        except Exception as e:
            log.error(f"WebSocket connection error: {e}")
        
        finally:
            await self.connection_manager.disconnect(connection_id)
    
    async def _handle_message(
        self,
        message: WebSocketMessage,
        connection_id: str,
        room_id: Optional[str]
    ):
        """Route message to appropriate handler."""
        handler = self.message_handlers.get(message.type)
        
        if handler:
            await handler(message, connection_id, room_id)
        else:
            await self.connection_manager.send_personal_message({
                "type": "error",
                "data": {"error": f"Unknown message type: {message.type}"}
            }, connection_id)
    
    async def _handle_ping(
        self,
        message: WebSocketMessage,
        connection_id: str,
        room_id: Optional[str]
    ):
        """Handle ping message."""
        await self.connection_manager.send_personal_message({
            "type": "pong",
            "data": {"timestamp": datetime.now().isoformat()}
        }, connection_id)
    
    async def _handle_add_annotation(
        self,
        message: WebSocketMessage,
        connection_id: str,
        room_id: Optional[str]
    ):
        """Handle adding annotation."""
        if not room_id:
            return
        
        try:
            annotation_data = message.data
            annotation = Annotation(
                id=str(uuid.uuid4()),
                node_id=annotation_data["node_id"],
                user_id=message.user_id or "anonymous",
                content=annotation_data["content"],
                type=annotation_data.get("type", "comment"),
                position=annotation_data.get("position")
            )
            
            # Store annotation
            if room_id not in self.annotations:
                self.annotations[room_id] = []
            self.annotations[room_id].append(annotation)
            
            # Broadcast to room
            await self.connection_manager.broadcast_to_room({
                "type": "annotation_added",
                "data": annotation.dict()
            }, room_id)
            
        except Exception as e:
            log.error(f"Error adding annotation: {e}")
            await self.connection_manager.send_personal_message({
                "type": "error",
                "data": {"error": "Failed to add annotation"}
            }, connection_id)
    
    async def _handle_update_annotation(
        self,
        message: WebSocketMessage,
        connection_id: str,
        room_id: Optional[str]
    ):
        """Handle updating annotation."""
        if not room_id or room_id not in self.annotations:
            return
        
        try:
            annotation_id = message.data["id"]
            updates = message.data.get("updates", {})
            
            # Find and update annotation
            for annotation in self.annotations[room_id]:
                if annotation.id == annotation_id:
                    if annotation.user_id != message.user_id:
                        await self.connection_manager.send_personal_message({
                            "type": "error",
                            "data": {"error": "Cannot update annotation from another user"}
                        }, connection_id)
                        return
                    
                    # Update fields
                    for field, value in updates.items():
                        if hasattr(annotation, field):
                            setattr(annotation, field, value)
                    
                    annotation.updated_at = datetime.now()
                    
                    # Broadcast update
                    await self.connection_manager.broadcast_to_room({
                        "type": "annotation_updated",
                        "data": annotation.dict()
                    }, room_id)
                    
                    return
            
            await self.connection_manager.send_personal_message({
                "type": "error",
                "data": {"error": "Annotation not found"}
            }, connection_id)
            
        except Exception as e:
            log.error(f"Error updating annotation: {e}")
            await self.connection_manager.send_personal_message({
                "type": "error", 
                "data": {"error": "Failed to update annotation"}
            }, connection_id)
    
    async def _handle_delete_annotation(
        self,
        message: WebSocketMessage,
        connection_id: str,
        room_id: Optional[str]
    ):
        """Handle deleting annotation."""
        if not room_id or room_id not in self.annotations:
            return
        
        try:
            annotation_id = message.data["id"]
            
            # Find and remove annotation
            for i, annotation in enumerate(self.annotations[room_id]):
                if annotation.id == annotation_id:
                    if annotation.user_id != message.user_id:
                        await self.connection_manager.send_personal_message({
                            "type": "error",
                            "data": {"error": "Cannot delete annotation from another user"}
                        }, connection_id)
                        return
                    
                    del self.annotations[room_id][i]
                    
                    # Broadcast deletion
                    await self.connection_manager.broadcast_to_room({
                        "type": "annotation_deleted",
                        "data": {"id": annotation_id}
                    }, room_id)
                    
                    return
            
            await self.connection_manager.send_personal_message({
                "type": "error",
                "data": {"error": "Annotation not found"}
            }, connection_id)
            
        except Exception as e:
            log.error(f"Error deleting annotation: {e}")
            await self.connection_manager.send_personal_message({
                "type": "error",
                "data": {"error": "Failed to delete annotation"}
            }, connection_id)
    
    async def _handle_cursor_move(
        self,
        message: WebSocketMessage,
        connection_id: str,
        room_id: Optional[str]
    ):
        """Handle cursor movement."""
        if not room_id:
            return
        
        # Broadcast cursor position to room (excluding sender)
        await self.connection_manager.broadcast_to_room({
            "type": "cursor_moved",
            "data": {
                "user_id": message.user_id,
                "position": message.data.get("position"),
                "timestamp": datetime.now().isoformat()
            }
        }, room_id, exclude=[connection_id])
    
    async def _handle_selection_change(
        self,
        message: WebSocketMessage,
        connection_id: str,
        room_id: Optional[str]
    ):
        """Handle selection change."""
        if not room_id:
            return
        
        # Broadcast selection to room (excluding sender)
        await self.connection_manager.broadcast_to_room({
            "type": "selection_changed",
            "data": {
                "user_id": message.user_id,
                "selection": message.data.get("selection"),
                "timestamp": datetime.now().isoformat()
            }
        }, room_id, exclude=[connection_id])
    
    async def _handle_request_room_state(
        self,
        message: WebSocketMessage,
        connection_id: str,
        room_id: Optional[str]
    ):
        """Handle request for current room state."""
        if not room_id:
            return
        
        # Send current annotations
        annotations = self.annotations.get(room_id, [])
        await self.connection_manager.send_personal_message({
            "type": "room_state",
            "data": {
                "annotations": [ann.dict() for ann in annotations],
                "users": self.connection_manager.get_room_users(room_id),
                "timestamp": datetime.now().isoformat()
            }
        }, connection_id)
    
    def get_room_annotations(self, room_id: str) -> List[Dict]:
        """Get all annotations for a room."""
        annotations = self.annotations.get(room_id, [])
        return [ann.dict() for ann in annotations]
    
    def get_connection_stats(self) -> Dict:
        """Get WebSocket connection statistics."""
        return self.connection_manager.get_connection_stats()


# Global WebSocket service instance
websocket_service = WebSocketService()