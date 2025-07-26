# src/persona_analysis/parsers/domain_identifier.py
import re
from typing import Dict, List, Tuple
from collections import Counter

class DomainIdentifier:
    """Identify domain/field from persona and job descriptions"""
    
    def __init__(self):
        self.domain_keywords = {
            'technology': {
                'keywords': ['software', 'hardware', 'programming', 'code', 'system',
                           'application', 'developer', 'engineer', 'tech', 'IT',
                           'algorithm', 'data structure', 'database', 'API'],
                'weight': 1.0
            },
            'research': {
                'keywords': ['research', 'study', 'paper', 'publication', 'journal',
                           'methodology', 'hypothesis', 'experiment', 'analysis',
                           'literature', 'academic', 'scholar'],
                'weight': 1.0
            },
            'business': {
                'keywords': ['business', 'market', 'revenue', 'profit', 'strategy',
                           'customer', 'sales', 'marketing', 'finance', 'ROI',
                           'stakeholder', 'competitive', 'growth'],
                'weight': 1.0
            },
            'healthcare': {
                'keywords': ['medical', 'health', 'patient', 'clinical', 'disease',
                           'treatment', 'diagnosis', 'hospital', 'medicine',
                           'pharmaceutical', 'therapy', 'healthcare'],
                'weight': 1.0
            },
            'education': {
                'keywords': ['education', 'learning', 'teaching', 'student', 'curriculum',
                           'course', 'training', 'academic', 'school', 'university',
                           'pedagogy', 'instruction'],
                'weight': 1.0
            },
            'science': {
                'keywords': ['science', 'biology', 'chemistry', 'physics', 'experiment',
                           'laboratory', 'hypothesis', 'theory', 'data', 'analysis',
                           'research', 'scientific'],
                'weight': 0.9
            },
            'engineering': {
                'keywords': ['engineering', 'design', 'build', 'system', 'technical',
                           'specification', 'implementation', 'architecture',
                           'infrastructure', 'solution'],
                'weight': 0.9
            }
        }
    
    def identify(self, persona_text: str, job_text: str) -> Dict:
        """Identify domain from texts"""
        combined_text = f"{persona_text} {job_text}".lower()
        
        # Score each domain
        domain_scores = {}
        
        for domain, info in self.domain_keywords.items():
            score = self._calculate_domain_score(combined_text, info)
            if score > 0:
                domain_scores[domain] = score
        
        # Get top domains
        if domain_scores:
            sorted_domains = sorted(domain_scores.items(), 
                                  key=lambda x: x[1], reverse=True)
            
            primary_domain = sorted_domains[0][0]
            secondary_domains = [d[0] for d in sorted_domains[1:3] if d[1] > 0.3]
            
            return {
                'primary': primary_domain,
                'secondary': secondary_domains,
                'scores': domain_scores,
                'confidence': sorted_domains[0][1]
            }
        
        return {
            'primary': 'general',
            'secondary': [],
            'scores': {},
            'confidence': 0.0
        }
    
    def _calculate_domain_score(self, text: str, domain_info: Dict) -> float:
        """Calculate score for a specific domain"""
        keywords = domain_info['keywords']
        weight = domain_info['weight']
        
        # Count keyword occurrences
        keyword_count = 0
        unique_keywords = 0
        
        for keyword in keywords:
            count = text.count(keyword)
            if count > 0:
                keyword_count += count
                unique_keywords += 1
        
        # Calculate score
        if unique_keywords == 0:
            return 0.0
        
        # Score based on both total occurrences and unique keywords
        occurrence_score = min(keyword_count / 10, 1.0)  # Cap at 10 occurrences
        coverage_score = unique_keywords / len(keywords)
        
        final_score = (occurrence_score * 0.6 + coverage_score * 0.4) * weight
        
        return round(final_score, 3)