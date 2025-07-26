# src/outline_extraction/extractors/base_extractor.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseExtractor(ABC):
    """Abstract base class for text extractors"""
    
    @abstractmethod
    def extract(self, pdf_path: str, **kwargs) -> List[Dict[str, Any]]:
        """Extract text blocks from PDF"""
        pass
    
    @abstractmethod
    def can_handle(self, pdf_path: str) -> bool:
        """Check if this extractor can handle the PDF"""
        pass