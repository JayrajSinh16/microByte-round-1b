# src/persona_analysis/analyzers/keyword_extractor.py
import re
from typing import List, Dict, Set
from collections import Counter

class KeywordExtractor:
    """Extract keywords from persona and job data"""
    
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are',
            'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must',
            'shall', 'ought', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours'
        }
    
    def extract(self, persona_data: Dict, job_data: Dict) -> Dict:
        """Extract keywords from persona and job data"""
        # Extract from different sources
        persona_keywords = self._extract_from_persona(persona_data)
        job_keywords = self._extract_from_job(job_data)
        
        # Combine and weight keywords
        all_keywords = self._combine_keywords(persona_keywords, job_keywords)
        
        # Rank keywords
        ranked_keywords = self._rank_keywords(all_keywords)
        
        return {
            'all': ranked_keywords,
            'persona': persona_keywords,
            'job': job_keywords,
            'top_10': ranked_keywords[:10]
        }
    
    def _extract_from_persona(self, persona_data: Dict) -> List[str]:
        """Extract keywords from persona data"""
        keywords = []
        
        # Add direct keywords
        keywords.extend(persona_data.get('keywords', []))
        
        # Add from focus areas
        for area in persona_data.get('focus_areas', []):
            keywords.extend(self._tokenize_phrase(area))
        
        # Add domain-specific terms
        if 'domain' in persona_data:
            domain = persona_data['domain']
            if isinstance(domain, list):
                for d in domain:
                    keywords.extend(self._tokenize_phrase(d))
            else:
                keywords.extend(self._tokenize_phrase(domain))
        
        # Add role terms
        if 'role' in persona_data:
            keywords.extend(self._tokenize_phrase(persona_data['role']))
        
        return self._clean_keywords(keywords)
    
    def _extract_from_job(self, job_data: Dict) -> List[str]:
        """Extract keywords from job data"""
        keywords = []
        
        # Add direct keywords
        keywords.extend(job_data.get('keywords', []))
        
        # Add from focus areas
        for area in job_data.get('focus_areas', []):
            keywords.extend(self._tokenize_phrase(area))
        
        # Add target terms
        keywords.extend(job_data.get('target', []))
        
        # Add from deliverables
        for deliverable in job_data.get('deliverables', []):
            keywords.extend(self._tokenize_phrase(deliverable))
        
        return self._clean_keywords(keywords)
    
    def _tokenize_phrase(self, phrase: str) -> List[str]:
        """Tokenize a phrase into keywords"""
        # Remove punctuation and split
        words = re.findall(r'\b\w+\b', phrase.lower())
        
        # Filter stop words and short words
        return [w for w in words if w not in self.stop_words and len(w) > 2]
    
    def _clean_keywords(self, keywords: List[str]) -> List[str]:
        """Clean and deduplicate keywords"""
        # Convert to lowercase and remove duplicates
        cleaned = list(set(k.lower() for k in keywords if k))
        
        # Remove stop words
        cleaned = [k for k in cleaned if k not in self.stop_words]
        
        # Remove very short words
        cleaned = [k for k in cleaned if len(k) > 2]
        
        return cleaned
    
    def _combine_keywords(self, persona_kw: List[str], job_kw: List[str]) -> List[str]:
        """Combine keywords with appropriate weighting"""
        # Count occurrences
        keyword_counts = Counter()
        
        # Job keywords get higher weight
        for kw in job_kw:
            keyword_counts[kw] += 2
        
        # Persona keywords
        for kw in persona_kw:
            keyword_counts[kw] += 1
        
        # Sort by count and return keywords
        return [kw for kw, _ in keyword_counts.most_common()]
    
    def _rank_keywords(self, keywords: List[str]) -> List[str]:
        """Rank keywords by importance"""
        # For now, keywords are already ranked by frequency
        # Could add more sophisticated ranking here
        return keywords