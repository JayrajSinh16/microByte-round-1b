# src/ranking_engine/embeddings/sentence_encoder.py
from typing import List, Union
import numpy as np
import logging
from sklearn.feature_extraction.text import TfidfVectorizer

from config.settings import SENTENCE_MODEL_NAME

logger = logging.getLogger(__name__)

class SentenceEncoder:
    """Encode sentences into embeddings using TF-IDF instead of transformers"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or SENTENCE_MODEL_NAME
        self.model = None
        self.device = 'cpu'  # Force CPU for offline mode
    
    def load_model(self):
        """Load TF-IDF vectorizer instead of transformer model"""
        if self.model is None:
            logger.info(f"Loading TF-IDF vectorizer (offline mode)")
            self.model = TfidfVectorizer(
                max_features=384,  # Match embedding dimension 
                stop_words='english',
                ngram_range=(1, 2),
                min_df=1,
                max_df=1.0  # Changed from 0.95 to 1.0 to avoid document count issues
            )
    
    def encode(self, texts: Union[str, List[str]], 
              batch_size: int = 32,
              show_progress: bool = False) -> np.ndarray:
        """Encode texts into embeddings using TF-IDF"""
        self.load_model()
        
        # Ensure list input
        if isinstance(texts, str):
            texts = [texts]
        
        # Fit and transform if model hasn't been fitted
        if not hasattr(self.model, 'vocabulary_'):
            embeddings = self.model.fit_transform(texts)
        else:
            embeddings = self.model.transform(texts)
        
        # Convert to dense array and normalize
        embeddings = embeddings.toarray()
        
        # L2 normalize
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        embeddings = embeddings / norms
        
        return embeddings
    
    def encode_with_cache(self, texts: Union[str, List[str]], 
                         embedding_manager) -> np.ndarray:
        """Encode with caching support"""
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = []
        texts_to_encode = []
        text_indices = []
        
        # Check cache
        for i, text in enumerate(texts):
            cached = embedding_manager.get_embedding(text, self.model_name)
            if cached is not None:
                embeddings.append((i, np.array(cached)))
            else:
                texts_to_encode.append(text)
                text_indices.append(i)
        
        # Encode missing texts
        if texts_to_encode:
            new_embeddings = self.encode(texts_to_encode)
            
            # Save to cache and add to results
            for text, embedding, idx in zip(texts_to_encode, new_embeddings, text_indices):
                embedding_manager.save_embedding(text, self.model_name, embedding.tolist())
                embeddings.append((idx, embedding))
        
        # Sort by original index
        embeddings.sort(key=lambda x: x[0])
        
        # Return just embeddings
        return np.array([emb for _, emb in embeddings])