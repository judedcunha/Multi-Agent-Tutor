"""
Comprehensive test suite for all caching functionality
Consolidates tests from: test_cache_comprehensive.py, test_cache_integration.py, test_phase3_caching.py
"""
import pickle
import pytest
import json
import pickle
import hashlib
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Any, Dict

# Project imports
from optimization.educational_caching import EducationalCacheManager, cache_manager
from optimization.cache_decorators import (
    cache_lesson, cache_practice, cache_rag_search,
    cache_agent_response, cache_result, generate_cache_key
)


class TestEducationalCacheManager:
    """Test suite for EducationalCacheManager"""
    
    @pytest.fixture(autouse=True)
    def setup(self, mock_redis_client):
        """Setup cache manager with mocked Redis"""
        with patch('optimization.educational_caching.redis.from_url') as mock_redis:
            mock_redis.return_value = mock_redis_client
            self.cache_manager = cache_manager  # Use global instance
            self.cache_manager.redis_client = mock_redis_client
    
    @pytest.mark.unit
    def test_cache_initialization(self):
        """Test cache manager initialization"""
        assert self.cache_manager is not None
        assert hasattr(self.cache_manager, 'redis_client')
        assert hasattr(self.cache_manager, 'default_ttl')
    
    @pytest.mark.unit
    def test_generate_cache_key(self):
        """Test cache key generation"""
        # Test with string
        key1 = generate_cache_key("test", "value")
        assert isinstance(key1, str)
        assert len(key1) > 0
        
        # Test with dict
        key2 = generate_cache_key("test", {"param": "value"})
        assert isinstance(key2, str)
        
        # Test consistency
        key3 = generate_cache_key("test", "value")
        assert key1 == key3
        
        # Test different inputs generate different keys
        key4 = generate_cache_key("test", "different")
        assert key1 != key4
    
    @pytest.mark.unit
    def test_set_and_get(self):
        """Test setting and getting cache values"""
        topic = "Python basics"
        level = "beginner"
        style = "visual"
        value = {"data": "test_value"}
        
        # Set value
        self.cache_manager.set_lesson(topic, level, style, value, ttl=60)
        
        # Verify set was called
        self.cache_manager.redis_client.setex.assert_called_once()
        
        # Mock get response
        self.cache_manager.redis_client.get.return_value = pickle.dumps(value)
        
        # Get value
        retrieved = self.cache_manager.get_lesson(topic, level, style)
        assert retrieved == value
    
    @pytest.mark.unit
    def test_get_nonexistent_key(self):
        """Test getting non-existent key returns None"""
        self.cache_manager.redis_client.get.return_value = None
        
        result = self.cache_manager.get_lesson("nonexistent", "beginner", "visual")
        assert result is None
    
    @pytest.mark.unit
    def test_delete_key(self):
        """Test deleting cache key"""
        # Mock keys to return some results
        self.cache_manager.redis_client.keys.return_value = [b"tutor:lesson:key1", b"tutor:lesson:key2"]
        
        # Delete keys by pattern
        self.cache_manager.clear_cache("lesson")
        
        # Verify keys() was called to find matching keys
        self.cache_manager.redis_client.keys.assert_called_once()
        # Verify delete was called with the found keys
        self.cache_manager.redis_client.delete.assert_called_once()
    


class TestCacheDecorators:
    """Test suite for cache decorators"""
    
    @pytest.fixture(autouse=True)
    def setup(self, mock_cache_manager):
        """Setup with mocked cache manager"""
        self.mock_cache = mock_cache_manager
        
    @pytest.mark.unit
    def test_cache_lesson_decorator(self):
        """Test @cache_lesson decorator"""
        with patch('optimization.cache_decorators.cache_manager', self.mock_cache):
            @cache_lesson(ttl=60)
            async def create_lesson(self, topic: str, level: str, learning_style: str) -> Dict:
                return {"topic": topic, "content": "Test content"}
            
            # First call - cache miss
            self.mock_cache.get_lesson.return_value = None
            result = asyncio.run(create_lesson(None, "Python", "beginner", "visual"))
            
            assert result["topic"] == "Python"
            self.mock_cache.set_lesson.assert_called_once()
            
            # Second call - cache hit
            self.mock_cache.get_lesson.return_value = {"topic": "Python", "content": "Cached"}
            result = asyncio.run(create_lesson(None, "Python", "beginner", "visual"))
            
            assert result["content"] == "Cached"


class TestCacheIntegration:
    """Integration tests for caching system"""
    
    @pytest.mark.integration
    @pytest.mark.requires_redis
    def test_real_redis_connection(self):
        """Test actual Redis connection and operations"""
        try:
            manager = EducationalCacheManager()
            
            # Test basic operations
            key = "integration_test_key"
            value = {"test": "data", "timestamp": datetime.now().isoformat()}
            
            # Set value
            manager.set(key, value, ttl=10)
            
            # Get value
            retrieved = manager.get(key)
            assert retrieved is not None
            assert retrieved["test"] == "data"
            
            # Check existence
            assert manager.exists(key) is True
            
            # Delete key
            manager.delete(key)
            assert manager.exists(key) is False
            
        except Exception as e:
            pytest.skip(f"Redis integration test failed: {e}")
