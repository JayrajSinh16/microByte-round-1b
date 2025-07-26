# src/ranking_engine/embeddings/embedding_manager.py
import pickle
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import logging

from config.settings import CACHE_DIR

logger = logging.getLogger(__name__)

class EmbeddingManager:
    """Manage embeddings and caching"""
    
    def __init__(self):
        self.cache_dir = CACHE_DIR / "embeddings"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache = {}
        self.max_memory_cache = 10000
    
    def get_embedding(self, text: str, model_name: str) -> Optional[List[float]]:
        """Get embedding from cache"""
        cache_key = self._generate_cache_key(text, model_name)
        
        # Check memory cache
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    embedding = pickle.load(f)
                
                # Add to memory cache
                self._add_to_memory_cache(cache_key, embedding)
                
                return embedding
            except Exception as e:
                logger.error(f"Failed to load cached embedding: {e}")
        
        return None
    
    def save_embedding(self, text: str, model_name: str, embedding: List[float]):
        """Save embedding to cache"""
        cache_key = self._generate_cache_key(text, model_name)
        
        # Save to memory cache
        self._add_to_memory_cache(cache_key, embedding)
        
        # Save to disk cache
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(embedding, f)
        except Exception as e:
            logger.error(f"Failed to save embedding to cache: {e}")
    
    def _generate_cache_key(self, text: str, model_name: str) -> str:
        """Generate cache key for text and model"""
        content = f"{model_name}::{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _add_to_memory_cache(self, key: str, embedding: List[float]):
        """Add to memory cache with size limit"""
        if len(self.memory_cache) >= self.max_memory_cache:
            # Remove oldest entry (simple FIFO)
            first_key = next(iter(self.memory_cache))
            del self.memory_cache[first_key]
        
        self.memory_cache[key] = embedding
    
    def clear_cache(self):
        """Clear all caches"""
        self.memory_cache.clear()
        
        # Clear disk cache
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()