"""
Decorators for automatic caching
"""

from functools import wraps
from typing import Callable, Any
import asyncio
import hashlib
import json
import logging

from optimization.educational_caching import cache_manager

logger = logging.getLogger(__name__)


def generate_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments"""
    # Create a string representation of arguments
    key_data = {
        "args": [str(arg) for arg in args],
        "kwargs": {k: str(v) for k, v in kwargs.items()}
    }
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()


def cache_lesson(ttl: int = 3600):
    """Decorator to cache lesson generation"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, topic: str, level: str, learning_style: str, *args, **kwargs):
            # Try to get from cache
            cached = cache_manager.get_lesson(topic, level, learning_style)
            if cached:
                logger.info(f"Cache hit for lesson: {topic}")
                cache_manager.increment_counter("lesson_cache_hits")
                return cached
            
            # Generate and cache
            cache_manager.increment_counter("lesson_cache_misses")
            result = await func(self, topic, level, learning_style, *args, **kwargs)
            
            if result:
                cache_manager.set_lesson(topic, level, learning_style, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_practice(ttl: int = 1800):
    """Decorator to cache practice problems"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, topic: str, level: str, count: int, *args, **kwargs):
            # Try to get from cache
            cached = cache_manager.get_practice_problems(topic, level, count)
            if cached:
                logger.info(f"Cache hit for practice: {topic}")
                cache_manager.increment_counter("practice_cache_hits")
                return cached
            
            # Generate and cache
            cache_manager.increment_counter("practice_cache_misses")
            result = await func(self, topic, level, count, *args, **kwargs)
            
            if result:
                cache_manager.set_practice_problems(topic, level, count, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_rag_search(ttl: int = 1800):
    """Decorator to cache RAG search results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, query: str, subject: str, level: str, *args, **kwargs):
            # Try to get from cache
            cached = cache_manager.get_rag_results(query, subject, level)
            if cached:
                logger.info(f"Cache hit for RAG: {query}")
                cache_manager.increment_counter("rag_cache_hits")
                return cached
            
            # Search and cache
            cache_manager.increment_counter("rag_cache_misses")
            result = await func(self, query, subject, level, *args, **kwargs)
            
            if result:
                cache_manager.set_rag_results(query, subject, level, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_agent_response(ttl: int = 3600):
    """Decorator to cache agent responses"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Generate cache key from arguments
            agent_name = self.__class__.__name__
            cache_key = generate_cache_key(*args, **kwargs)
            
            # Try to get from cache
            cached = cache_manager.get_agent_response(agent_name, cache_key)
            if cached:
                logger.debug(f"Cache hit for agent: {agent_name}")
                cache_manager.increment_counter(f"{agent_name}_cache_hits")
                return cached
            
            # Execute and cache
            cache_manager.increment_counter(f"{agent_name}_cache_misses")
            result = await func(self, *args, **kwargs)
            
            if result:
                cache_manager.cache_agent_response(agent_name, cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_result(prefix: str = "general", ttl: int = 3600):
    """Generic decorator to cache any function result"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{prefix}:{generate_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached = cache_manager.get_with_sliding_expiration(cache_key, ttl)
            if cached:
                logger.debug(f"Cache hit for {prefix}")
                cache_manager.increment_counter(f"{prefix}_cache_hits")
                return cached
            
            # Execute and cache
            cache_manager.increment_counter(f"{prefix}_cache_misses")
            result = func(*args, **kwargs)
            
            if result is not None:
                cache_manager.set_with_sliding_expiration(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{prefix}:{generate_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached = cache_manager.get_with_sliding_expiration(cache_key, ttl)
            if cached:
                logger.debug(f"Cache hit for {prefix}")
                cache_manager.increment_counter(f"{prefix}_cache_hits")
                return cached
            
            # Execute and cache
            cache_manager.increment_counter(f"{prefix}_cache_misses")
            result = await func(*args, **kwargs)
            
            if result is not None:
                cache_manager.set_with_sliding_expiration(cache_key, result, ttl)
            
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def invalidate_cache(patterns: list):
    """Decorator to invalidate cache patterns after function execution"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            for pattern in patterns:
                cache_manager.clear_cache(pattern)
            return result
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            for pattern in patterns:
                cache_manager.clear_cache(pattern)
            return result
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache_session_data(ttl: int = 7200):
    """Decorator to cache student session data"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, session_id: str, *args, **kwargs):
            # Try to get session from cache
            cached_session = cache_manager.get_student_session(session_id)
            
            # Execute function
            result = await func(self, session_id, *args, **kwargs)
            
            # Cache updated session data
            if result and isinstance(result, dict):
                cache_manager.cache_student_session(session_id, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Conditional caching based on configuration
def conditional_cache(condition_func: Callable[[], bool], **cache_kwargs):
    """Apply caching only if condition is met"""
    def decorator(func: Callable) -> Callable:
        if condition_func():
            # Apply caching
            return cache_result(**cache_kwargs)(func)
        else:
            # Return function unchanged
            return func
    
    return decorator
