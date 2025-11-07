"""
Redis caching for educational content and session data
"""

import os
import json
import redis
import hashlib
import pickle
from typing import Optional, Any, Dict, List
from datetime import timedelta
import logging
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)


class EducationalCacheManager:
    """Manages Redis caching for educational content"""
    
    def __init__(self):
        self.redis_client = None
        self.default_ttl = 3600  # 1 hour default
        self.enabled = True
        
    def initialize(self, redis_url: Optional[str] = None):
        """Initialize Redis connection"""
        if not redis_url:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        try:
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=False,  # We'll handle encoding
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 3,  # TCP_KEEPINTVL
                    3: 5   # TCP_KEEPCNT
                }
            )
            self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
            self.enabled = True
        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            logger.warning("Running without cache - performance may be degraded")
            self.redis_client = None
            self.enabled = False
    
    def _generate_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate cache key from parameters"""
        # Sort params for consistent keys
        sorted_params = json.dumps(params, sort_keys=True)
        hash_digest = hashlib.md5(sorted_params.encode()).hexdigest()
        return f"tutor:{prefix}:{hash_digest}"
    
    def get_lesson(self, topic: str, level: str, learning_style: str) -> Optional[Dict]:
        """Get cached lesson plan"""
        if not self.redis_client or not self.enabled:
            return None
        
        key = self._generate_key("lesson", {
            "topic": topic,
            "level": level,
            "style": learning_style
        })
        
        try:
            cached = self.redis_client.get(key)
            if cached:
                logger.info(f"Cache hit for lesson: {topic}")
                return pickle.loads(cached)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None
    
    def set_lesson(self, topic: str, level: str, learning_style: str,
                   lesson_data: Dict, ttl: Optional[int] = None):
        """Cache lesson plan"""
        if not self.redis_client or not self.enabled:
            return
        
        key = self._generate_key("lesson", {
            "topic": topic,
            "level": level,
            "style": learning_style
        })
        
        try:
            serialized = pickle.dumps(lesson_data)
            self.redis_client.setex(
                key,
                ttl or self.default_ttl,
                serialized
            )
            logger.info(f"Cached lesson: {topic}")
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def get_practice_problems(self, topic: str, level: str,
                             count: int) -> Optional[List[Dict]]:
        """Get cached practice problems"""
        if not self.redis_client or not self.enabled:
            return None
        
        key = self._generate_key("practice", {
            "topic": topic,
            "level": level,
            "count": count
        })
        
        try:
            cached = self.redis_client.get(key)
            if cached:
                logger.info(f"Cache hit for practice: {topic}")
                return pickle.loads(cached)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None
    
    def set_practice_problems(self, topic: str, level: str, count: int,
                             problems: List[Dict], ttl: Optional[int] = None):
        """Cache practice problems"""
        if not self.redis_client or not self.enabled:
            return
        
        key = self._generate_key("practice", {
            "topic": topic,
            "level": level,
            "count": count
        })
        
        try:
            serialized = pickle.dumps(problems)
            self.redis_client.setex(
                key,
                ttl or self.default_ttl,
                serialized
            )
            logger.info(f"Cached practice problems: {topic}")
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def get_rag_results(self, query: str, subject: str,
                        level: str) -> Optional[List[Dict]]:
        """Get cached RAG search results"""
        if not self.redis_client or not self.enabled:
            return None
        
        key = self._generate_key("rag", {
            "query": query,
            "subject": subject,
            "level": level
        })
        
        try:
            cached = self.redis_client.get(key)
            if cached:
                logger.info(f"Cache hit for RAG: {query}")
                return pickle.loads(cached)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None
    
    def set_rag_results(self, query: str, subject: str, level: str,
                       results: List[Dict], ttl: Optional[int] = None):
        """Cache RAG search results"""
        if not self.redis_client or not self.enabled:
            return
        
        key = self._generate_key("rag", {
            "query": query,
            "subject": subject,
            "level": level
        })
        
        try:
            serialized = pickle.dumps(results)
            self.redis_client.setex(
                key,
                ttl or 1800,  # 30 minutes for RAG results
                serialized
            )
            logger.info(f"Cached RAG results: {query}")
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def cache_student_session(self, session_id: str, session_data: Dict,
                             ttl: int = 7200):
        """Cache active student session (2 hours default)"""
        if not self.redis_client or not self.enabled:
            return
        
        key = f"tutor:session:{session_id}"
        
        try:
            serialized = pickle.dumps(session_data)
            self.redis_client.setex(key, ttl, serialized)
            logger.info(f"Cached session: {session_id}")
        except Exception as e:
            logger.error(f"Cache session error: {e}")
    
    def get_student_session(self, session_id: str) -> Optional[Dict]:
        """Get cached student session"""
        if not self.redis_client or not self.enabled:
            return None
        
        key = f"tutor:session:{session_id}"
        
        try:
            cached = self.redis_client.get(key)
            if cached:
                return pickle.loads(cached)
        except Exception as e:
            logger.error(f"Get session error: {e}")
        
        return None
    
    def increment_counter(self, counter_name: str, amount: int = 1) -> int:
        """Increment a counter (for metrics)"""
        if not self.redis_client or not self.enabled:
            return 0
        
        key = f"tutor:counter:{counter_name}"
        
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Counter increment error: {e}")
            return 0
    
    def get_counter(self, counter_name: str) -> int:
        """Get counter value"""
        if not self.redis_client or not self.enabled:
            return 0
        
        key = f"tutor:counter:{counter_name}"
        
        try:
            value = self.redis_client.get(key)
            return int(value) if value else 0
        except Exception as e:
            logger.error(f"Get counter error: {e}")
            return 0
    
    def cache_agent_response(self, agent_name: str, input_hash: str,
                            response: Dict, ttl: Optional[int] = None):
        """Cache agent response for faster repeated queries"""
        if not self.redis_client or not self.enabled:
            return
        
        key = f"tutor:agent:{agent_name}:{input_hash}"
        
        try:
            serialized = pickle.dumps(response)
            self.redis_client.setex(
                key,
                ttl or 3600,  # 1 hour for agent responses
                serialized
            )
            logger.debug(f"Cached response for agent: {agent_name}")
        except Exception as e:
            logger.error(f"Cache agent response error: {e}")
    
    def get_agent_response(self, agent_name: str, input_hash: str) -> Optional[Dict]:
        """Get cached agent response"""
        if not self.redis_client or not self.enabled:
            return None
        
        key = f"tutor:agent:{agent_name}:{input_hash}"
        
        try:
            cached = self.redis_client.get(key)
            if cached:
                logger.debug(f"Cache hit for agent: {agent_name}")
                return pickle.loads(cached)
        except Exception as e:
            logger.error(f"Get agent response error: {e}")
        
        return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client or not self.enabled:
            return {"status": "disabled"}
        
        try:
            info = self.redis_client.info()
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_keys": self.redis_client.dbsize(),
                "hit_rate": self._calculate_hit_rate(),
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        try:
            info = self.redis_client.info("stats")
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            total = hits + misses
            if total > 0:
                return round(hits / total, 3)
        except:
            pass
        return 0.0
    
    def clear_cache(self, pattern: Optional[str] = None):
        """Clear cache entries"""
        if not self.redis_client or not self.enabled:
            return
        
        try:
            if pattern:
                # Clear specific pattern
                keys = self.redis_client.keys(f"tutor:{pattern}:*")
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Cleared {len(keys)} cache entries matching pattern: {pattern}")
            else:
                # Clear all tutor cache
                keys = self.redis_client.keys("tutor:*")
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Cleared all {len(keys)} cache entries")
        except Exception as e:
            logger.error(f"Clear cache error: {e}")
    
    def set_with_sliding_expiration(self, key: str, value: Any, ttl: int):
        """Set value with sliding expiration (refreshes on access)"""
        if not self.redis_client or not self.enabled:
            return
        
        full_key = f"tutor:{key}"
        
        try:
            serialized = pickle.dumps(value)
            self.redis_client.setex(full_key, ttl, serialized)
        except Exception as e:
            logger.error(f"Set sliding expiration error: {e}")
    
    def get_with_sliding_expiration(self, key: str, ttl: int) -> Optional[Any]:
        """Get value and refresh expiration"""
        if not self.redis_client or not self.enabled:
            return None
        
        full_key = f"tutor:{key}"
        
        try:
            cached = self.redis_client.get(full_key)
            if cached:
                # Refresh TTL
                self.redis_client.expire(full_key, ttl)
                return pickle.loads(cached)
        except Exception as e:
            logger.error(f"Get sliding expiration error: {e}")
        
        return None


# Global cache manager
cache_manager = EducationalCacheManager()
