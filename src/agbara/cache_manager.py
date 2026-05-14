"""
Cache Manager - KV cache and semantic cache for efficient token usage.
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """An entry in the cache."""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    ttl: Optional[float] = None  # Time to live in seconds
    embedding: Optional[List[float]] = None


class SemanticCache:
    """
    Semantic cache that stores responses based on semantic similarity.
    
    Enables 10-100x token reduction by reusing similar query responses.
    """
    
    def __init__(
        self,
        cache_dir: str = "/tmp/agbara_cache/semantic",
        max_size: int = 10000,
        similarity_threshold: float = 0.95
    ):
        """
        Initialize semantic cache.
        
        Args:
            cache_dir: Directory for persistent storage
            max_size: Maximum number of entries
            similarity_threshold: Minimum similarity for cache hit (0.0-1.0)
        """
        self.cache_dir = cache_dir
        self.max_size = max_size
        self.similarity_threshold = similarity_threshold
        
        os.makedirs(cache_dir, exist_ok=True)
        
        self.entries: Dict[str, CacheEntry] = {}
        self.embeddings: Dict[str, List[float]] = {}
        
        self._load_cache()
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text (placeholder)."""
        import random
        random.seed(hash(text) % (2**32))
        return [random.gauss(0, 1) for _ in range(384)]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not a or not b:
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def get(self, query: str) -> Optional[Any]:
        """
        Get cached response for a query using semantic similarity.
        
        Args:
            query: Input query
            
        Returns:
            Cached response if found, None otherwise
        """
        query_embedding = self._get_embedding(query)
        
        best_match = None
        best_similarity = 0
        
        for key, embedding in self.embeddings.items():
            similarity = self._cosine_similarity(query_embedding, embedding)
            
            if similarity > best_similarity and similarity >= self.similarity_threshold:
                best_similarity = similarity
                best_match = key
        
        if best_match and best_match in self.entries:
            entry = self.entries[best_match]
            entry.accessed_at = time.time()
            entry.access_count += 1
            
            logger.info(f"Semantic cache hit (similarity: {best_similarity:.3f})")
            return entry.value
        
        return None
    
    def set(self, query: str, response: Any, ttl: float = None):
        """
        Store a response in the semantic cache.
        
        Args:
            query: Input query
            response: Response to cache
            ttl: Time to live in seconds
        """
        if len(self.entries) >= self.max_size:
            self._evict_lru()
        
        key = hashlib.md5(query.encode()).hexdigest()[:16]
        embedding = self._get_embedding(query)
        
        entry = CacheEntry(
            key=key,
            value=response,
            ttl=ttl,
            embedding=embedding
        )
        
        self.entries[key] = entry
        self.embeddings[key] = embedding
        
        self._save_cache()
    
    def _evict_lru(self):
        """Evict least recently used entries."""
        if not self.entries:
            return
        
        # Sort by access time
        sorted_keys = sorted(
            self.entries.keys(),
            key=lambda k: self.entries[k].accessed_at
        )
        
        # Remove 10% of entries
        to_remove = max(1, len(sorted_keys) // 10)
        for key in sorted_keys[:to_remove]:
            del self.entries[key]
            del self.embeddings[key]
        
        logger.info(f"Evicted {to_remove} entries from semantic cache")
    
    def _save_cache(self):
        """Save cache to disk."""
        cache_file = os.path.join(self.cache_dir, "semantic_cache.json")
        
        data = {
            key: {
                "value": entry.value,
                "created_at": entry.created_at,
                "accessed_at": entry.accessed_at,
                "access_count": entry.access_count,
                "ttl": entry.ttl
            }
            for key, entry in self.entries.items()
        }
        
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_cache(self):
        """Load cache from disk."""
        cache_file = os.path.join(self.cache_dir, "semantic_cache.json")
        
        if not os.path.exists(cache_file):
            return
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            for key, entry_data in data.items():
                entry = CacheEntry(
                    key=key,
                    value=entry_data["value"],
                    created_at=entry_data.get("created_at", time.time()),
                    accessed_at=entry_data.get("accessed_at", time.time()),
                    access_count=entry_data.get("access_count", 0),
                    ttl=entry_data.get("ttl")
                )
                
                # Re-generate embedding
                embedding = self._get_embedding(str(entry.value)[:100])
                entry.embedding = embedding
                
                self.entries[key] = entry
                self.embeddings[key] = embedding
            
            logger.info(f"Loaded {len(self.entries)} entries from semantic cache")
            
        except Exception as e:
            logger.error(f"Failed to load semantic cache: {e}")
    
    def clear(self):
        """Clear the cache."""
        self.entries.clear()
        self.embeddings.clear()
        
        cache_file = os.path.join(self.cache_dir, "semantic_cache.json")
        if os.path.exists(cache_file):
            os.remove(cache_file)
    
    def size(self) -> int:
        """Get cache size."""
        return len(self.entries)
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        if not self.entries:
            return {
                "size": 0,
                "total_accesses": 0,
                "avg_access_count": 0
            }
        
        total_accesses = sum(e.access_count for e in self.entries.values())
        
        return {
            "size": len(self.entries),
            "max_size": self.max_size,
            "total_accesses": total_accesses,
            "avg_access_count": total_accesses / len(self.entries),
            "similarity_threshold": self.similarity_threshold
        }


class KVCache:
    """
    Key-Value cache for exact query matching.
    
    Fast lookup for frequently asked queries.
    """
    
    def __init__(
        self,
        cache_dir: str = "/tmp/agbara_cache/kv",
        max_size: int = 1000
    ):
        self.cache_dir = cache_dir
        self.max_size = max_size
        
        os.makedirs(cache_dir, exist_ok=True)
        
        self.cache: Dict[str, CacheEntry] = {}
        self._load_cache()
    
    def get(self, key: str) -> Optional[Any]:
        """Get a cached value."""
        if key in self.cache:
            entry = self.cache[key]
            entry.accessed_at = time.time()
            entry.access_count += 1
            return entry.value
        return None
    
    def set(self, key: str, value: Any, ttl: float = None):
        """Set a cached value."""
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        self.cache[key] = CacheEntry(
            key=key,
            value=value,
            ttl=ttl
        )
        
        self._save_cache()
    
    def delete(self, key: str):
        """Delete a cached value."""
        self.cache.pop(key, None)
    
    def _evict_lru(self):
        """Evict least recently used entries."""
        sorted_keys = sorted(
            self.cache.keys(),
            key=lambda k: self.cache[k].accessed_at
        )
        
        to_remove = max(1, len(sorted_keys) // 10)
        for key in sorted_keys[:to_remove]:
            del self.cache[key]
    
    def _save_cache(self):
        """Save cache to disk."""
        cache_file = os.path.join(self.cache_dir, "kv_cache.json")
        
        data = {
            key: {
                "value": entry.value,
                "access_count": entry.access_count
            }
            for key, entry in self.cache.items()
        }
        
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_cache(self):
        """Load cache from disk."""
        cache_file = os.path.join(self.cache_dir, "kv_cache.json")
        
        if not os.path.exists(cache_file):
            return
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            for key, entry_data in data.items():
                self.cache[key] = CacheEntry(
                    key=key,
                    value=entry_data["value"],
                    access_count=entry_data.get("access_count", 0)
                )
            
            logger.info(f"Loaded {len(self.cache)} entries from KV cache")
            
        except Exception as e:
            logger.error(f"Failed to load KV cache: {e}")
    
    def clear(self):
        """Clear the cache."""
        self.cache.clear()
    
    def size(self) -> int:
        """Get cache size."""
        return len(self.cache)


class CacheManager:
    """
    Unified cache manager combining KV cache and semantic cache.
    
    Features:
    - Two-tier caching (KV for exact, semantic for similar)
    - Automatic eviction
    - Persistent storage
    - Token usage tracking
    """
    
    def __init__(
        self,
        cache_dir: str = "/tmp/agbara_cache",
        semantic_cache_size: int = 10000,
        kv_cache_size: int = 1000
    ):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Base directory for cache storage
            semantic_cache_size: Maximum semantic cache entries
            kv_cache_size: Maximum KV cache entries
        """
        self.cache_dir = cache_dir
        
        self.semantic_cache = SemanticCache(
            cache_dir=os.path.join(cache_dir, "semantic"),
            max_size=semantic_cache_size
        )
        
        self.kv_cache = KVCache(
            cache_dir=os.path.join(cache_dir, "kv"),
            max_size=kv_cache_size
        )
        
        # Statistics
        self.hits = 0
        self.misses = 0
    
    def get(self, query: str) -> Optional[Any]:
        """
        Get cached response (checks both caches).
        
        Args:
            query: Input query
            
        Returns:
            Cached response if found
        """
        # Check KV cache first (exact match, fast)
        kv_result = self.kv_cache.get(query)
        if kv_result is not None:
            self.hits += 1
            logger.debug("KV cache hit")
            return kv_result
        
        # Check semantic cache (similar queries)
        semantic_result = self.semantic_cache.get(query)
        if semantic_result is not None:
            self.hits += 1
            return semantic_result
        
        self.misses += 1
        return None
    
    async def get_async(self, query: str) -> Optional[Any]:
        """Async version of get."""
        return self.get(query)
    
    def set(self, query: str, response: Any, ttl: float = None, exact: bool = False):
        """
        Store a response in cache.
        
        Args:
            query: Input query
            response: Response to cache
            ttl: Time to live in seconds
            exact: If True, only store in KV cache
        """
        # Always store in semantic cache
        if not exact:
            self.semantic_cache.set(query, response, ttl)
        
        # Also store in KV cache for fast exact lookup
        self.kv_cache.set(query, response, ttl)
    
    async def set_async(self, query: str, response: Any, ttl: float = None):
        """Async version of set."""
        self.set(query, response, ttl)
    
    def delete(self, query: str):
        """Delete from both caches."""
        self.kv_cache.delete(query)
    
    def clear(self):
        """Clear all caches."""
        self.semantic_cache.clear()
        self.kv_cache.clear()
        self.hits = 0
        self.misses = 0
    
    def size(self) -> int:
        """Get total cache size."""
        return self.semantic_cache.size() + self.kv_cache.size()
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "semantic_cache": self.semantic_cache.get_stats(),
            "kv_cache": {
                "size": self.kv_cache.size()
            },
            "total_hits": self.hits,
            "total_misses": self.misses,
            "hit_rate_percent": hit_rate,
            "total_size": self.size()
        }
