# src/subsection_extraction/rankers/diversity_scorer.py
from typing import List, Dict, Set
import hashlib

class DiversityScorer:
    """Ensure diversity in subsection selection"""
    
    def ensure_diversity(self, subsections: List[Dict]) -> List[Dict]:
        """Ensure diverse subsection selection"""
        if len(subsections) <= 10:
            return subsections
        
        diverse = []
        seen_content = set()
        seen_sections = {}
        
        # Sort by relevance score
        sorted_subs = sorted(subsections, 
                           key=lambda x: x.get('relevance_score', 0), 
                           reverse=True)
        
        for sub in sorted_subs:
            # Check content similarity
            content_hash = self._get_content_hash(sub['text'])
            if content_hash in seen_content:
                continue
            
            # Check section diversity
            parent_section = sub.get('parent_section', '')
            doc = sub.get('document', '')
            section_key = f"{doc}::{parent_section}"
            
            # Limit subsections per parent section
            if section_key in seen_sections and seen_sections[section_key] >= 2:
                continue
            
            # Add to diverse set
            diverse.append(sub)
            seen_content.add(content_hash)
            seen_sections[section_key] = seen_sections.get(section_key, 0) + 1
            
            # Stop when we have enough
            if len(diverse) >= 30:
                break
        
        return diverse
    
    def _get_content_hash(self, text: str) -> str:
        """Generate hash of content for similarity checking"""
        # Normalize text for comparison
        normalized = self._normalize_text(text)
        
        # Generate hash
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for similarity comparison"""
        # Lowercase and remove extra whitespace
        text = ' '.join(text.lower().split())
        
        # Remove punctuation for comparison
        import string
        translator = str.maketrans('', '', string.punctuation)
        text = text.translate(translator)
        
        # Take first 200 chars for comparison
        return text[:200]