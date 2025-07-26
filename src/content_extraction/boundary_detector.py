# src/content_extraction/boundary_detector.py
import re
from typing import List, Tuple, Optional

class BoundaryDetector:
    """Detect section boundaries in text"""
    
    def __init__(self):
        self.heading_patterns = [
            re.compile(r'^\d+\.?\s+[A-Z]', re.M),  # Numbered headings
            re.compile(r'^Chapter\s+\d+', re.M | re.I),
            re.compile(r'^Section\s+\d+', re.M | re.I),
            re.compile(r'^[A-Z][A-Z\s]+$', re.M),  # All caps line
        ]
    
    def find_section_boundaries(self, text: str, headings: List[str]) -> List[Tuple[int, int]]:
        """Find boundaries for each section"""
        boundaries = []
        
        for i, heading in enumerate(headings):
            start = self._find_heading_position(text, heading)
            
            if start == -1:
                continue
            
            # Find end (start of next section or end of text)
            if i < len(headings) - 1:
                end = self._find_heading_position(text, headings[i + 1], start + len(heading))
                if end == -1:
                    end = len(text)
            else:
                end = len(text)
            
            boundaries.append((start, end))
        
        return boundaries
    
    def _find_heading_position(self, text: str, heading: str, start_pos: int = 0) -> int:
        """Find position of heading in text"""
        # Try exact match first
        pos = text.find(heading, start_pos)
        if pos != -1:
            return pos
        
        # Try normalized match
        normalized_heading = self._normalize_text(heading)
        normalized_text = self._normalize_text(text[start_pos:])
        
        pos = normalized_text.find(normalized_heading)
        if pos != -1:
            return start_pos + pos
        
        return -1
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        
        # Lowercase
        text = text.lower()
        
        return text
    
    def detect_implicit_boundaries(self, text: str) -> List[int]:
        """Detect implicit section boundaries based on patterns"""
        boundaries = []
        
        for pattern in self.heading_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                boundaries.append(match.start())
        
        # Remove duplicates and sort
        boundaries = sorted(set(boundaries))
        
        return boundaries