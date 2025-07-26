# src/ranking_engine/embeddings/similarity_calculator.py
import numpy as np
from typing import List, Union, Tuple
from sklearn.metrics.pairwise import cosine_similarity

class SimilarityCalculator:
    """Calculate similarities between embeddings"""
    
    @staticmethod
    def cosine_similarity(embedding1: np.ndarray, 
                         embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        # Ensure 2D arrays
        if embedding1.ndim == 1:
            embedding1 = embedding1.reshape(1, -1)
        if embedding2.ndim == 1:
            embedding2 = embedding2.reshape(1, -1)
        
        # Calculate similarity
        similarity = cosine_similarity(embedding1, embedding2)[0, 0]
        
        return float(similarity)
    
    @staticmethod
    def batch_cosine_similarity(query_embedding: np.ndarray,
                              document_embeddings: np.ndarray) -> np.ndarray:
        """Calculate similarities between query and multiple documents"""
        # Ensure 2D arrays
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, document_embeddings)[0]
        
        return similarities
    
    @staticmethod
    def find_most_similar(query_embedding: np.ndarray,
                         document_embeddings: np.ndarray,
                         top_k: int = 10) -> List[Tuple[int, float]]:
        """Find most similar documents to query"""
        # Calculate similarities
        similarities = SimilarityCalculator.batch_cosine_similarity(
            query_embedding, document_embeddings
        )
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Return indices with scores
        results = [(int(idx), float(similarities[idx])) for idx in top_indices]
        
        return results
    
    @staticmethod
    def pairwise_similarities(embeddings: np.ndarray) -> np.ndarray:
        """Calculate pairwise similarities between all embeddings"""
        return cosine_similarity(embeddings)