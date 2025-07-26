# src/subsection_extraction/rankers/subsection_ranker.py
from typing import List, Dict
import re

class SubsectionRanker:
    """Rank subsections by relevance"""
    
    def rank(self, subsections: List[Dict], parent_section: Dict, 
             query_profile: Dict) -> List[Dict]:
        """Rank subsections"""
        if not subsections:
            return []
        
        # Score each subsection
        for sub in subsections:
            score = self._calculate_score(sub, parent_section, query_profile)
            sub['relevance_score'] = score
        
        # Sort by score
        ranked = sorted(subsections, key=lambda x: x['relevance_score'], reverse=True)
        
        return ranked
    
    def _calculate_score(self, subsection: Dict, parent_section: Dict, 
                        query_profile: Dict) -> float:
        """Calculate relevance score for subsection"""
        score = 0.0
        
        # Inherit parent score
        parent_score = parent_section.get('final_score', 0.5)
        score += parent_score * 0.4
        
        # Position score (earlier is better)
        position = subsection.get('position', 0.5)
        score += (1 - position) * 0.2
        
        # Content quality score
        quality = self._assess_content_quality(subsection['text'])
        score += quality * 0.2
        
        # Query relevance
        relevance = self._calculate_query_relevance(subsection, query_profile)
        score += relevance * 0.2
        
        return min(score, 1.0)
    
    def _assess_content_quality(self, text: str) -> float:
        """Assess quality of content"""
        quality = 0.0
        
        # Length score
        word_count = len(text.split())
        if 50 <= word_count <= 200:
            quality += 0.3
        elif 30 <= word_count < 50 or 200 < word_count <= 300:
            quality += 0.2
        else:
            quality += 0.1
        
        # Complete sentences
        if text and text[-1] in '.!?':
            quality += 0.2
        
        # Has substance (not just references)
        if not any(marker in text.lower() for marker in ['see figure', 'see table', 'as shown in']):
            quality += 0.2
        
        # Contains examples or data
        if any(indicator in text.lower() for indicator in ['for example', 'such as', 'including', '%', 'data']):
            quality += 0.3
        
        return quality
    
    def _calculate_query_relevance(self, subsection: Dict, query_profile: Dict) -> float:
        """Calculate relevance to query"""
        if not query_profile or 'query' not in query_profile:
            return 0.5
        
        text_lower = subsection['text'].lower()
        score = 0.0
        
        # Check primary terms
        primary_terms = query_profile['query'].get('primary_terms', [])
        if primary_terms:
            matches = sum(1 for term in primary_terms if term.lower() in text_lower)
            score += (matches / len(primary_terms)) * 0.5
        
        # Check must-have terms
        must_have = query_profile['query'].get('must_have_terms', [])
        if must_have:
            has_must_have = any(term.lower() in text_lower for term in must_have)
            if has_must_have:
                score += 0.5
        
        return score