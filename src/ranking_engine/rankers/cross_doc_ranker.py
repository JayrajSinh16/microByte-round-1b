# src/ranking_engine/rankers/cross_doc_ranker.py
from typing import List, Dict
from collections import defaultdict

class CrossDocRanker:
    """Analyze and rank based on cross-document patterns"""
    
    def rank(self, sections: List[Dict]) -> List[Dict]:
        """Add cross-document ranking signals"""
        # Analyze cross-document patterns
        section_similarities = self._find_similar_sections(sections)
        doc_coverage = self._analyze_document_coverage(sections)
        
        # Add cross-document scores
        for section in sections:
            section_id = self._get_section_id(section)
            
            # Cross-reference score (appears in multiple docs)
            cross_ref_score = len(section_similarities.get(section_id, [])) / len(doc_coverage)
            
            # Document importance (from important documents)
            doc_importance = doc_coverage.get(section.get('document', ''), 0)
            
            # Combine into cross-doc score
            cross_doc_score = 0.6 * cross_ref_score + 0.4 * doc_importance
            
            if 'scores' not in section:
                section['scores'] = {}
            section['scores']['cross_doc'] = cross_doc_score
        
        return sections
    
    def _find_similar_sections(self, sections: List[Dict]) -> Dict[str, List[str]]:
        """Find sections that appear across documents"""
        similarities = defaultdict(list)
        
        # Group by normalized title
        title_groups = defaultdict(list)
        for section in sections:
            normalized = self._normalize_title(section.get('title', ''))
            title_groups[normalized].append(section)
        
        # Mark similar sections
        for normalized, group in title_groups.items():
            if len(group) > 1:
                for section in group:
                    section_id = self._get_section_id(section)
                    for other in group:
                        if other != section:
                            other_id = self._get_section_id(other)
                            similarities[section_id].append(other_id)
        
        return dict(similarities)
    
    def _analyze_document_coverage(self, sections: List[Dict]) -> Dict[str, float]:
        """Analyze importance of each document"""
        doc_sections = defaultdict(int)
        total_sections = len(sections)
        
        for section in sections:
            doc = section.get('document', 'unknown')
            doc_sections[doc] += 1
        
        # Calculate document importance
        coverage = {}
        for doc, count in doc_sections.items():
            coverage[doc] = count / total_sections
        
        return coverage
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        # Remove numbers, lowercase, remove common words
        import re
        
        title = title.lower()
        title = re.sub(r'\d+\.?\s*', '', title)  # Remove numbers
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        words = [w for w in title.split() if w not in stop_words]
        
        return ' '.join(words)
    
    def _get_section_id(self, section: Dict) -> str:
        """Generate unique section ID"""
        doc = section.get('document', 'unknown')
        title = section.get('title', 'untitled')
        return f"{doc}::{title}"