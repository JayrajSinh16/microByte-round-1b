# src/ranking_engine/scorers/base_scorer.py
from abc import ABC, abstractmethod
from typing import List, Dict

class BaseScorer(ABC):
    """Abstract base class for scoring strategies"""
    
    @abstractmethod
    def score(self, sections: List[Dict], query_profile: Dict) -> List[float]:
        """Score sections based on query profile"""
        pass
    
    def normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to 0-1 range"""
        if not scores:
            return scores
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return [0.5] * len(scores)
        
        return [(s - min_score) / (max_score - min_score) for s in scores]