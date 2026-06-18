# AWS CLI Response Caching Feature

## Overview

This feature adds a response caching mechanism to the AWS CLI to improve performance by reducing redundant API calls. Frequently accessed AWS service responses are cached locally with configurable time-to-live (TTL) settings.

## Benefits

- **Performance Improvement**: Avoid redundant API calls for repeated commands
- **Reduced Latency**: Quick response retrieval from local cache
- **Bandwidth Savings**: Fewer network requests to AWS services
- **Backward Compatible**: Existing CLI functionality remains unchanged

## Implementation Details

### Cache Module (`awscli/cache.py`)

The caching system provides:

1. **ResponseCache Class**: Main cache manager with the following features:
   - Stores responses with automatic expiration
   - Generates unique cache keys from service, operation, and parameters
   - Manages cache directory (`~/.aws/cache`)
   - Supports TTL-based expiration
   - Thread-safe operations

2. **Cache Key Generation**:
   - Uses SHA256 hash of service name, operation, and parameters
   - Ensures consistency and collision resistance
   - Handles complex parameter structures

3. **Configuration Options**:
   - Default TTL: 300 seconds (5 minutes)
   - Configurable per cache instance
   - Can be enabled/disabled globally

### Usage

```python
from awscli.cache import get_cache

# Get global cache instance
cache = get_cache(ttl=300, enabled=True)

# Cache a response
cache.set('s3', 'ListBuckets', {}, response_data)

# Retrieve cached response
cached_response = cache.get('s3', 'ListBuckets', {})

# Clear all cache
cache.clear()

# Clear expired entries
cache.clear_expired()
```

### Cache Storage

- **Location**: `~/.aws/cache/`
- **Format**: JSON files with SHA256 hash names
- **Contents**: Timestamp, service, operation, and response data

### Testing

Comprehensive unit tests are provided in `tests/unit/test_cache.py` covering:
- Cache key generation and consistency
- Set and retrieval operations
- Expiration behavior
- Cache clearing functionality
- Disabled cache behavior
- Global singleton pattern

## Future Enhancements

- Integration with CLI command handlers
- CLI flag support: `--cache`, `--cache-ttl`, `--clear-cache`
- Configurable cache directory via environment variable
- Cache statistics and monitoring
- Selective caching based on operation type
- LRU (Least Recently Used) cache eviction policy

## Configuration

Currently, the cache can be configured programmatically:

```python
# Enable caching with 10-minute TTL
cache = get_cache(ttl=600, enabled=True)

# Disable caching
cache = get_cache(enabled=False)
```

Future versions will support CLI flags and configuration files.

## Performance Impact

- **Memory**: Minimal impact; only JSON responses stored to disk
- **Disk**: Cache files stored in `~/.aws/cache/` directory
- **CPU**: Negligible; uses standard JSON serialization
- **Network**: Reduced by avoiding redundant API calls

## Security Considerations

- Cache files stored in user's home directory with standard permissions
- Sensitive data (credentials) is never cached
- Cache can be cleared at any time via `clear()` method
- Expired entries are automatically removed

## Compatibility

- Python 3.10+
- Works with all AWS services supported by CLI v1
- No external dependencies required
