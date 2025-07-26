# src/ranking_engine/scorers/structural_scorer.py
from typing import List, Dict

from .base_scorer import BaseScorer

class StructuralScorer(BaseScorer):
    """Score based on document structure and position"""
    
    def __init__(self):
        self.level_weights = {
            'H1': 1.0,
            'H2': 0.8,
            'H3': 0.6
        }
        
        self.position_decay = 0.9  # Decay factor for position
    
    def score(self, sections: List[Dict], query_profile: Dict) -> List[float]:
        """Score sections based on structural importance"""
        scores = []
        
        # Group sections by document
        doc_groups = self._group_by_document(sections)
        
        for section in sections:
            score = self._calculate_structural_score(section, doc_groups)
            scores.append(score)
        
        return self.normalize_scores(scores)
    
    def _group_by_document(self, sections: List[Dict]) -> Dict[str, List[Dict]]:
        """Group sections by document"""
        groups = {}
        
        for section in sections:
            doc = section.get('document', 'unknown')
            if doc not in groups:
                groups[doc] = []
            groups[doc].append(section)
        
        return groups
    
    def _calculate_structural_score(self, section: Dict, doc_groups: Dict) -> float:
        """Calculate structural score for a section"""
        score = 0.0
        
        # Level-based score
        level = section.get('level', 'H2')
        level_score = self.level_weights.get(level, 0.5)
        score += level_score * 0.5
        
        # Position-based score
        doc = section.get('document', 'unknown')
        if doc in doc_groups:
            position = self._get_section_position(section, doc_groups[doc])
            position_score = self.position_decay ** position
            score += position_score * 0.3
        
        # Hierarchy bonus
        hierarchy = section.get('hierarchy', {})
        if hierarchy.get('children'):
            score += 0.1  # Has subsections
        if not hierarchy.get('parent'):
            score += 0.1  # Top-level section
        
        return score
    
    def _get_section_position(self, section: Dict, doc_sections: List[Dict]) -> int:
        """Get position of section in document"""
        for i, s in enumerate(doc_sections):
            if s.get('title') == section.get('title'):
                return i
        return len(doc_sections)