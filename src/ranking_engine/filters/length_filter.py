# src/ranking_engine/filters/length_filter.py
from typing import List, Dict

class LengthFilter:
    """Filter sections based on length"""
    
    def __init__(self):
        self.min_words = 20
        self.max_words = 5000
    
    def filter(self, sections: List[Dict]) -> List[Dict]:
        """Filter sections by length"""
        filtered = []
        
        for section in sections:
            content = section.get('content', '')
            word_count = len(content.split())
            
            if self.min_words <= word_count <= self.max_words:
                filtered.append(section)
            elif word_count > self.max_words:
                # Truncate very long sections instead of removing
                words = content.split()[:self.max_words]
                section['content'] = ' '.join(words)
                section['truncated'] = True
                filtered.append(section)
        
        return filtered