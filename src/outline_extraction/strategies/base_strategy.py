# src/outline_extraction/strategies/base_strategy.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseStrategy(ABC):
    """Abstract base class for heading detection strategies"""
    
    @abstractmethod
    def detect(self, blocks: List[Dict], profile: Dict) -> List[Dict]:
        """
        Detect headings in blocks
        
        Returns list of predictions with format:
        {
            'block_id': int,
            'is_heading': bool,
            'level': str ('H1', 'H2', 'H3', None),
            'confidence': float (0-1)
        }
        """
        pass
    
    def get_name(self) -> str:
        """Get strategy name"""
        return self.__class__.__name__