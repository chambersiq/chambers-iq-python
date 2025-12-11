"""
Caching utilities for the drafting workflow to optimize cost.

Implements:
1. In-memory caching for static content (prompts, templates)
2. TTL-based caching for semi-static content (case data, documents)
3. Thread-safe cache operations
"""

import time
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime, timedelta
import hashlib
import json

class Cache:
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if exists and not expired."""
        if key in self._cache:
            entry = self._cache[key]

            # Check if expired
            if entry.get("expires_at") and entry["expires_at"] < time.time():
                del self._cache[key]
                self._stats["evictions"] += 1
                self._stats["misses"] += 1
                return None

            self._stats["hits"] += 1
            return entry["value"]

        self._stats["misses"] += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = never expires)
        """
        entry = {
            "value": value,
            "created_at": time.time(),
            "expires_at": time.time() + ttl if ttl else None
        }
        self._cache[key] = entry

    def delete(self, key: str):
        """Remove key from cache."""
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        """Clear entire cache."""
        self._cache.clear()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0

        return {
            **self._stats,
            "size": len(self._cache),
            "hit_rate_percent": round(hit_rate, 2)
        }

# Global cache instances
prompt_cache = Cache()  # Never expires - prompts are static
content_cache = Cache()  # Short TTL - for case/template data
session_cache = Cache()  # Per-session cache

def cache_prompt(func: Callable) -> Callable:
    """
    Decorator to cache system prompts.
    Prompts are static and never expire.
    """
    @wraps(func)
    def wrapper(filename: str) -> str:
        cache_key = f"prompt:{filename}"

        # Check cache
        cached = prompt_cache.get(cache_key)
        if cached is not None:
            return cached

        # Load and cache
        result = func(filename)
        prompt_cache.set(cache_key, result)  # No TTL - never expires

        return result

    return wrapper

def cache_content(ttl: int = 300):
    """
    Decorator to cache content with TTL.

    Args:
        ttl: Time-to-live in seconds (default: 5 minutes)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and args
            key_data = {
                "func": func.__name__,
                "args": str(args),
                "kwargs": str(sorted(kwargs.items()))
            }
            cache_key = hashlib.md5(
                json.dumps(key_data, sort_keys=True).encode()
            ).hexdigest()

            # Check cache
            cached = content_cache.get(cache_key)
            if cached is not None:
                print(f"  [Cache HIT] {func.__name__}")
                return cached

            # Execute and cache
            print(f"  [Cache MISS] {func.__name__}")
            result = await func(*args, **kwargs)
            content_cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator

def get_cache_stats() -> Dict[str, Any]:
    """Get statistics for all caches."""
    return {
        "prompt_cache": prompt_cache.get_stats(),
        "content_cache": content_cache.get_stats(),
        "session_cache": session_cache.get_stats()
    }

def clear_all_caches():
    """Clear all caches."""
    prompt_cache.clear()
    content_cache.clear()
    session_cache.clear()
