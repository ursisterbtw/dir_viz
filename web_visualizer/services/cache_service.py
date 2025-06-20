"""Caching service for web visualizer."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from collections import OrderedDict
import hashlib

log = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry with TTL support."""
    
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        self.created_at = datetime.now()
        self.access_count = 1
        self.last_accessed = datetime.now()
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > self.expires_at
    
    def access(self) -> Any:
        """Access the cached value and update statistics."""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.value


class CacheService:
    """In-memory cache service with LRU eviction and TTL support."""
    
    def __init__(self, max_entries: int = 1000, default_ttl: int = 300):
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expired": 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._stats["expired"] += 1
                self._stats["misses"] += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._stats["hits"] += 1
            
            return entry.access()
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        ttl = ttl or self.default_ttl
        
        async with self._lock:
            # Remove existing entry if present
            if key in self._cache:
                del self._cache[key]
            
            # Check capacity and evict LRU if needed
            while len(self._cache) >= self.max_entries:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats["evictions"] += 1
            
            # Add new entry
            self._cache[key] = CacheEntry(value, ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._stats = {
                "hits": 0,
                "misses": 0,
                "evictions": 0,
                "expired": 0
            }
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        removed_count = 0
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
                removed_count += 1
                self._stats["expired"] += 1
        
        if removed_count > 0:
            log.info(f"Cleaned up {removed_count} expired cache entries")
        
        return removed_count
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total_requests) if total_requests > 0 else 0
            
            return {
                "entries": len(self._cache),
                "max_entries": self.max_entries,
                "hit_rate": hit_rate,
                "total_hits": self._stats["hits"],
                "total_misses": self._stats["misses"],
                "total_evictions": self._stats["evictions"],
                "total_expired": self._stats["expired"],
                "memory_usage_estimate": self._estimate_memory_usage()
            }
    
    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage in bytes (rough approximation)."""
        try:
            # Very rough estimation
            total_size = 0
            for key, entry in list(self._cache.items())[:10]:  # Sample first 10 entries
                key_size = len(key.encode('utf-8'))
                value_size = len(json.dumps(entry.value).encode('utf-8')) if entry.value else 0
                total_size += key_size + value_size + 200  # 200 bytes overhead estimate
            
            # Extrapolate to full cache
            if len(self._cache) > 0:
                avg_entry_size = total_size / min(10, len(self._cache))
                return int(avg_entry_size * len(self._cache))
            
            return 0
        except Exception:
            return -1  # Unable to estimate
    
    async def get_entry_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific cache entry."""
        async with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            return {
                "key": key,
                "created_at": entry.created_at.isoformat(),
                "expires_at": entry.expires_at.isoformat(),
                "last_accessed": entry.last_accessed.isoformat(),
                "access_count": entry.access_count,
                "is_expired": entry.is_expired(),
                "ttl_remaining": max(0, (entry.expires_at - datetime.now()).total_seconds())
            }
    
    async def extend_ttl(self, key: str, additional_seconds: int) -> bool:
        """Extend TTL for a specific entry."""
        async with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            if not entry.is_expired():
                entry.expires_at += timedelta(seconds=additional_seconds)
                return True
            
            return False
    
    def generate_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_data = {
            "args": args,
            "kwargs": kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()


# Global cache service instance
cache_service = CacheService()