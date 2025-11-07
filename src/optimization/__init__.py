# Optimization module initialization
from .educational_caching import cache_manager, EducationalCacheManager
from .cache_decorators import (
    cache_lesson,
    cache_practice,
    cache_rag_search,
    cache_agent_response,
    cache_result,
    invalidate_cache,
    cache_session_data,
    conditional_cache
)

__all__ = [
    "cache_manager",
    "EducationalCacheManager",
    "cache_lesson",
    "cache_practice", 
    "cache_rag_search",
    "cache_agent_response",
    "cache_result",
    "invalidate_cache",
    "cache_session_data",
    "conditional_cache"
]
