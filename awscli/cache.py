"""
Response caching module for AWS CLI.

This module provides a caching mechanism to store frequently accessed
AWS API responses, reducing redundant API calls and improving CLI performance.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional


class ResponseCache:
    """
    Manages caching of AWS API responses.
    
    Caches are stored in the user's ~/.aws/cache directory with TTL support.
    Each cached response is identified by a hash of the request parameters.
    """
    
    DEFAULT_TTL = 300  # 5 minutes default
    CACHE_DIR = Path.home() / ".aws" / "cache"
    
    def __init__(self, ttl: int = DEFAULT_TTL, enabled: bool = True):
        """
        Initialize the response cache.
        
        Args:
            ttl: Time-to-live for cached responses in seconds
            enabled: Whether caching is enabled
        """
        self.ttl = ttl
        self.enabled = enabled
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self) -> None:
        """Ensure the cache directory exists."""
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def _generate_cache_key(self, service: str, operation: str, 
                           params: Dict[str, Any]) -> str:
        """
        Generate a unique cache key from service, operation, and parameters.
        
        Args:
            service: AWS service name (e.g., 's3', 'ec2')
            operation: API operation name (e.g., 'ListBuckets', 'DescribeInstances')
            params: Request parameters
            
        Returns:
            A unique cache key hash
        """
        cache_content = f"{service}:{operation}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(cache_content.encode()).hexdigest()
    
    def _get_cache_file(self, cache_key: str) -> Path:
        """Get the path to a cache file."""
        return self.CACHE_DIR / f"{cache_key}.json"
    
    def get(self, service: str, operation: str, 
            params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached response if it exists and hasn't expired.
        
        Args:
            service: AWS service name
            operation: API operation name
            params: Request parameters
            
        Returns:
            Cached response data if valid, None otherwise
        """
        if not self.enabled:
            return None
        
        cache_key = self._generate_cache_key(service, operation, params)
        cache_file = self._get_cache_file(cache_key)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache has expired
            if time.time() - cache_data['timestamp'] > self.ttl:
                cache_file.unlink()  # Delete expired cache
                return None
            
            return cache_data['response']
        except (json.JSONDecodeError, KeyError, IOError):
            return None
    
    def set(self, service: str, operation: str, 
            params: Dict[str, Any], response: Dict[str, Any]) -> None:
        """
        Cache a response.
        
        Args:
            service: AWS service name
            operation: API operation name
            params: Request parameters
            response: Response data to cache
        """
        if not self.enabled:
            return
        
        cache_key = self._generate_cache_key(service, operation, params)
        cache_file = self._get_cache_file(cache_key)
        
        cache_data = {
            'timestamp': time.time(),
            'service': service,
            'operation': operation,
            'response': response
        }
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
        except IOError as e:
            # Silently fail on cache write errors
            pass
    
    def clear(self) -> None:
        """Clear all cached responses."""
        try:
            for cache_file in self.CACHE_DIR.glob('*.json'):
                cache_file.unlink()
        except OSError:
            pass
    
    def clear_expired(self) -> None:
        """Remove expired cache entries."""
        try:
            current_time = time.time()
            for cache_file in self.CACHE_DIR.glob('*.json'):
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    
                    if current_time - cache_data['timestamp'] > self.ttl:
                        cache_file.unlink()
                except (json.JSONDecodeError, KeyError, IOError):
                    cache_file.unlink()
        except OSError:
            pass


# Global cache instance
_cache_instance: Optional[ResponseCache] = None


def get_cache(ttl: int = ResponseCache.DEFAULT_TTL, 
              enabled: bool = True) -> ResponseCache:
    """
    Get the global cache instance.
    
    Args:
        ttl: Time-to-live for cached responses in seconds
        enabled: Whether caching is enabled
        
    Returns:
        ResponseCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ResponseCache(ttl=ttl, enabled=enabled)
    return _cache_instance
