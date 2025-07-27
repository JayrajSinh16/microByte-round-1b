# src/ranking_engine/scorers/domain_aware_scorer.py
import re
from typing import Dict, List, Any
import numpy as np
from .base_scorer import BaseScorer

class DomainAwareScorer(BaseScorer):
    """Score sections based on domain-specific relevance"""
    
    def __init__(self):
        super().__init__()
        self.section_type_weights = {
            'title_match': 0.4,
            'content_relevance': 0.3,
            'domain_preference': 0.2,
            'exclusion_penalty': 0.1
        }
    
    def score(self, sections: List[Dict], query_profile: Dict) -> List[float]:
        """Score sections based on domain-aware relevance"""
        domain_profile = query_profile.get('domain_profile', {})
        if not domain_profile:
            return [0.5] * len(sections)  # Default scores if no domain profile
        
        scores = []
        for section in sections:
            score = self._score_section(section, domain_profile, query_profile)
            scores.append(score)
        
        return scores
    
    def _score_section(self, section: Dict, domain_profile: Dict, query_profile: Dict) -> float:
        """Score a single section"""
        title = section.get('title', '').lower()
        content = section.get('content', '').lower()
        
        # 1. Title relevance based on domain preferences
        title_score = self._score_title_relevance(title, domain_profile)
        
        # 2. Content relevance based on domain patterns
        content_score = self._score_content_relevance(content, domain_profile)
        
        # 3. Domain preference alignment
        preference_score = self._score_domain_preference(title, domain_profile)
        
        # 4. Exclusion penalty
        exclusion_penalty = self._calculate_exclusion_penalty(title, content, domain_profile)
        
        # Combine scores
        final_score = (
            title_score * self.section_type_weights['title_match'] +
            content_score * self.section_type_weights['content_relevance'] +
            preference_score * self.section_type_weights['domain_preference'] -
            exclusion_penalty * self.section_type_weights['exclusion_penalty']
        )
        
        return max(0.0, min(1.0, final_score))
    
    def _score_title_relevance(self, title: str, domain_profile: Dict) -> float:
        """Score title relevance to domain keywords"""
        priority_keywords = domain_profile.get('priority_keywords', [])
        if not priority_keywords:
            return 0.5
        
        matches = 0
        for keyword in priority_keywords:
            if keyword.lower() in title:
                matches += 1
        
        return min(matches / len(priority_keywords) * 2, 1.0)
    
    def _score_content_relevance(self, content: str, domain_profile: Dict) -> float:
        """Score content relevance using domain patterns"""
        content_patterns = domain_profile.get('content_patterns', [])
        if not content_patterns:
            return 0.5
        
        pattern_matches = 0
        for pattern in content_patterns:
            if re.search(pattern, content):
                pattern_matches += 1
        
        return min(pattern_matches / len(content_patterns), 1.0)
    
    def _score_domain_preference(self, title: str, domain_profile: Dict) -> float:
        """Score based on section preferences"""
        section_preferences = domain_profile.get('section_preferences', {})
        if not section_preferences:
            return 0.5
        
        max_preference = 0.0
        for section_type, weight in section_preferences.items():
            if section_type in title:
                max_preference = max(max_preference, weight)
        
        return max_preference
    
    def _calculate_exclusion_penalty(self, title: str, content: str, domain_profile: Dict) -> float:
        """Calculate penalty for exclusion patterns"""
        exclusion_patterns = domain_profile.get('exclusion_patterns', [])
        if not exclusion_patterns:
            return 0.0
        
        penalty = 0.0
        combined_text = f"{title} {content}"
        
        for pattern in exclusion_patterns:
            if re.search(pattern, combined_text):
                penalty += 0.3
        
        return min(penalty, 1.0)
