# src/ranking_engine/scorers/semantic_scorer.py
import torch
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

from .base_scorer import BaseScorer
from config.settings import SENTENCE_MODEL_NAME, MODEL_CACHE_SIZE

class SemanticScorer(BaseScorer):
    """Score sections based on semantic similarity"""
    
    def __init__(self):
        super().__init__()
        self.model = None
        self.embedding_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
    
    def _load_model(self):
        """Lazy load the sentence transformer model"""
        if self.model is None:
            self.model = SentenceTransformer(SENTENCE_MODEL_NAME)
            self.model.max_seq_length = 256
            
            # Set to eval mode
            self.model.eval()
            
            # CPU optimizations
            if not torch.cuda.is_available():
                torch.set_num_threads(4)
    
    def score(self, sections: List[Dict], query_profile: Dict) -> List[float]:
        """Score sections based on semantic similarity to query"""
        self._load_model()
        
        # Build query text from persona and job
        query_text = self._build_query_text(query_profile)
        query_embedding = self._get_embedding(query_text)
        
        scores = []
        section_texts = [self._prepare_section_text(s) for s in sections]
        
        # Batch encode sections
        section_embeddings = self._batch_encode(section_texts)
        
        # Calculate similarities
        for embedding in section_embeddings:
            similarity = self._cosine_similarity(query_embedding, embedding)
            scores.append(similarity)
        
        # Log cache statistics
        cache_ratio = self.cache_hits / (self.cache_hits + self.cache_misses + 1)
        if cache_ratio > 0:
            print(f"Cache hit ratio: {cache_ratio:.2%}")
        
        return scores
    
    def _build_query_text(self, query_profile: Dict) -> str:
        """Build query text from profile"""
        parts = []
        
        # Add persona information
        if 'persona' in query_profile:
            parts.append(query_profile['persona']['role'])
            parts.extend(query_profile['persona']['keywords'][:5])
            parts.extend(query_profile['persona']['focus_areas'])
        
        # Add job information
        if 'job' in query_profile:
            parts.append(query_profile['job']['description'])
            parts.extend(query_profile['job']['keywords'][:5])
        
        return ' '.join(parts)
    
    def _prepare_section_text(self, section: Dict) -> str:
        """Prepare section text for encoding"""
        # Combine title and content preview
        title = section.get('title', '')
        content = section.get('content', '')[:500]  # First 500 chars
        
        return f"{title} {content}".strip()
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding with caching"""
        # Simple hash for cache key
        cache_key = hash(text)
        
        if cache_key in self.embedding_cache:
            self.cache_hits += 1
            return self.embedding_cache[cache_key]
        
        self.cache_misses += 1
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        # Add to cache with size limit
        if len(self.embedding_cache) < MODEL_CACHE_SIZE:
            self.embedding_cache[cache_key] = embedding
        
        return embedding
    
    def _batch_encode(self, texts: List[str]) -> np.ndarray:
        """Batch encode texts for efficiency"""
        # Check cache first
        embeddings = []
        texts_to_encode = []
        text_indices = []
        
        for i, text in enumerate(texts):
            cache_key = hash(text)
            if cache_key in self.embedding_cache:
                embeddings.append((i, self.embedding_cache[cache_key]))
                self.cache_hits += 1
            else:
                texts_to_encode.append(text)
                text_indices.append(i)
                self.cache_misses += 1
        
        # Encode uncached texts
        if texts_to_encode:
            new_embeddings = self.model.encode(
                texts_to_encode,
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            # Add to results and cache
            for idx, text, embedding in zip(text_indices, texts_to_encode, new_embeddings):
                embeddings.append((idx, embedding))
                
                # Cache if space available
                if len(self.embedding_cache) < MODEL_CACHE_SIZE:
                    self.embedding_cache[hash(text)] = embedding
        
        # Sort by original index and return embeddings only
        embeddings.sort(key=lambda x: x[0])
        return np.array([emb for _, emb in embeddings])
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))