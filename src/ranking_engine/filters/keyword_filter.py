# src/ranking_engine/filters/keyword_filter.py
from typing import List, Dict

class KeywordFilter:
    """Filter sections based on keyword presence"""
    
    def filter(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Filter sections that don't contain required keywords"""
        # Get must-have terms
        must_have = []
        if 'query' in query_profile:
            must_have = query_profile['query'].get('must_have_terms', [])
        
        if not must_have:
            return sections
        
        filtered = []
        
        for section in sections:
            # Check if section contains at least one must-have term
            content = f"{section.get('title', '')} {section.get('content', '')}".lower()
            
            if any(term.lower() in content for term in must_have):
                filtered.append(section)
        
        # If too restrictive, relax filter
        if len(filtered) < len(sections) * 0.1:  # Less than 10% remaining
            return sections  # Return all
        
        return filtered