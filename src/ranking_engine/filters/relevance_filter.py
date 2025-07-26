# src/ranking_engine/filters/relevance_filter.py
from typing import List, Dict

class RelevanceFilter:
    """Filter obviously irrelevant sections"""
    
    def __init__(self):
        self.irrelevant_patterns = [
            'table of contents',
            'list of figures',
            'list of tables',
            'bibliography',
            'index',
            'appendix'
        ]
    
    def filter(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Filter irrelevant sections"""
        filtered = []
        
        # Get preferences
        preferences = query_profile.get('search_preferences', {})
        include_references = preferences.get('include_references', False)
        
        for section in sections:
            title = section.get('title', '').lower()
            
            # Check against irrelevant patterns
            is_irrelevant = False
            for pattern in self.irrelevant_patterns:
                if pattern in title:
                    # Exception for references if requested
                    if pattern == 'bibliography' and include_references:
                        continue
                    is_irrelevant = True
                    break
            
            if not is_irrelevant:
                filtered.append(section)
        
        return filtered