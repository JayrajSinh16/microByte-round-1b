# src/ranking_engine/embeddings/sentence_encoder.py
import torch
from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
import logging

from config.settings import SENTENCE_MODEL_NAME

logger = logging.getLogger(__name__)

class SentenceEncoder:
    """Encode sentences into embeddings"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or SENTENCE_MODEL_NAME
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    def load_model(self):
        """Lazy load the model"""
        if self.model is None:
            logger.info(f"Loading sentence transformer: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.model.to(self.device)
            self.model.eval()
    
    def encode(self, texts: Union[str, List[str]], 
              batch_size: int = 32,
              show_progress: bool = False) -> np.ndarray:
        """Encode texts into embeddings"""
        self.load_model()
        
        # Ensure list input
        if isinstance(texts, str):
            texts = [texts]
        
        # Encode
        with torch.no_grad():
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
        
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