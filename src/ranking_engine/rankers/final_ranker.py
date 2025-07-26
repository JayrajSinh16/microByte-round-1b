# src/ranking_engine/rankers/final_ranker.py
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class FinalRanker:
    """Final ranking and selection of sections"""
    
    def rank(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Perform final ranking and filtering"""
        # Sort by final score
        ranked_sections = sorted(
            sections,
            key=lambda s: s.get('final_score', 0),
            reverse=True
        )
        
        # Apply final filters
        filtered = self._apply_final_filters(ranked_sections, query_profile)
        
        # Ensure diversity
        diverse = self._ensure_diversity(filtered, query_profile)
        
        # Add importance rank
        for i, section in enumerate(diverse):
            section['importance_rank'] = i + 1
        
        return diverse
    
    def _apply_final_filters(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Apply final filtering rules"""
        filtered = []
        
        # Get thresholds
        min_score = query_profile.get('min_relevance_score', 0.3)
        
        for section in sections:
            if section.get('final_score', 0) >= min_score:
                filtered.append(section)
        
        return filtered
    
    def _ensure_diversity(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Ensure diversity in final results"""
        diverse = []
        seen_docs = set()
        seen_titles = set()
        
        # Preferences
        max_per_doc = query_profile.get('max_sections_per_doc', 5)
        prefer_different_docs = query_profile.get('prefer_different_docs', True)
        
        doc_counts = {}
        
        for section in sections:
            doc = section.get('document', 'unknown')
            title = section.get('title', '').lower()
            
            # Skip if too many from same document
            if doc_counts.get(doc, 0) >= max_per_doc:
                continue
            
            # Skip very similar titles
            if self._is_duplicate_title(title, seen_titles):
                continue
            
            # Add diversity bonus for new documents
            if prefer_different_docs and doc not in seen_docs:
                section['final_score'] *= 1.1
            
            diverse.append(section)
            seen_docs.add(doc)
            seen_titles.add(title)
            doc_counts[doc] = doc_counts.get(doc, 0) + 1
        
        # Re-sort after diversity adjustments
        diverse.sort(key=lambda s: s.get('final_score', 0), reverse=True)
        
        return diverse
    
    def _is_duplicate_title(self, title: str, seen_titles: set) -> bool:
        """Check if title is too similar to already seen titles"""
        # Simple check - could be enhanced with fuzzy matching
        for seen in seen_titles:
            # Check exact match
            if title == seen:
                return True
            
            # Check substring
            if len(title) > 10 and (title in seen or seen in title):
                return True
        
        return False