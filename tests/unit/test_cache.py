"""
Unit tests for the response caching module.
"""

import json
import time
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from awscli import cache


class TestResponseCache(unittest.TestCase):
    """Test cases for ResponseCache class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_instance = cache.ResponseCache(ttl=1, enabled=True)
        # Override cache directory for testing
        self.cache_instance.CACHE_DIR = Path(self.temp_dir.name)
        self.cache_instance._ensure_cache_dir()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_cache_key_generation(self):
        """Test that cache keys are consistently generated."""
        key1 = self.cache_instance._generate_cache_key(
            's3', 'ListBuckets', {'Marker': 'test'}
        )
        key2 = self.cache_instance._generate_cache_key(
            's3', 'ListBuckets', {'Marker': 'test'}
        )
        self.assertEqual(key1, key2)
    
    def test_cache_key_differs_for_different_params(self):
        """Test that different parameters produce different cache keys."""
        key1 = self.cache_instance._generate_cache_key(
            's3', 'ListBuckets', {'Marker': 'test1'}
        )
        key2 = self.cache_instance._generate_cache_key(
            's3', 'ListBuckets', {'Marker': 'test2'}
        )
        self.assertNotEqual(key1, key2)
    
    def test_cache_set_and_get(self):
        """Test setting and retrieving cached responses."""
        response = {'Buckets': [{'Name': 'test-bucket'}]}
        self.cache_instance.set('s3', 'ListBuckets', {}, response)
        
        retrieved = self.cache_instance.get('s3', 'ListBuckets', {})
        self.assertEqual(retrieved, response)
    
    def test_cache_expiration(self):
        """Test that cached responses expire after TTL."""
        response = {'Buckets': [{'Name': 'test-bucket'}]}
        self.cache_instance.set('s3', 'ListBuckets', {}, response)
        
        # Response should be available immediately
        retrieved = self.cache_instance.get('s3', 'ListBuckets', {})
        self.assertEqual(retrieved, response)
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        # Response should now be expired
        retrieved = self.cache_instance.get('s3', 'ListBuckets', {})
        self.assertIsNone(retrieved)
    
    def test_cache_disabled(self):
        """Test that caching is skipped when disabled."""
        cache_instance = cache.ResponseCache(ttl=300, enabled=False)
        cache_instance.CACHE_DIR = Path(self.temp_dir.name)
        cache_instance._ensure_cache_dir()
        
        response = {'Buckets': [{'Name': 'test-bucket'}]}
        cache_instance.set('s3', 'ListBuckets', {}, response)
        
        # Should return None because caching is disabled
        retrieved = cache_instance.get('s3', 'ListBuckets', {})
        self.assertIsNone(retrieved)
    
    def test_cache_clear(self):
        """Test clearing all cached responses."""
        response = {'Buckets': [{'Name': 'test-bucket'}]}
        self.cache_instance.set('s3', 'ListBuckets', {}, response)
        
        # Verify cache is populated
        retrieved = self.cache_instance.get('s3', 'ListBuckets', {})
        self.assertEqual(retrieved, response)
        
        # Clear cache
        self.cache_instance.clear()
        
        # Verify cache is empty
        retrieved = self.cache_instance.get('s3', 'ListBuckets', {})
        self.assertIsNone(retrieved)
    
    def test_clear_expired(self):
        """Test clearing only expired cache entries."""
        response = {'Buckets': [{'Name': 'test-bucket'}]}
        self.cache_instance.set('s3', 'ListBuckets', {}, response)
        
        # Wait for entry to expire
        time.sleep(1.1)
        
        # Clear expired entries
        self.cache_instance.clear_expired()
        
        # Verify expired entry was removed
        retrieved = self.cache_instance.get('s3', 'ListBuckets', {})
        self.assertIsNone(retrieved)


class TestGlobalCache(unittest.TestCase):
    """Test cases for global cache instance."""
    
    def test_get_cache_singleton(self):
        """Test that get_cache returns the same instance."""
        # Reset global instance
        cache._cache_instance = None
        
        cache1 = cache.get_cache()
        cache2 = cache.get_cache()
        
        self.assertIs(cache1, cache2)


if __name__ == '__main__':
    unittest.main()
