# src/ranking_engine/scorers/tfidf_scorer.py
import math
from typing import List, Dict
from collections import Counter
import numpy as np

from .base_scorer import BaseScorer

class TFIDFScorer(BaseScorer):
    """TF-IDF based scoring"""
    
    def __init__(self):
        self.doc_frequencies = {}
        self.total_docs = 0
    
    def score(self, sections: List[Dict], query_profile: Dict) -> List[float]:
        """Score sections using TF-IDF"""
        # Build document frequencies
        self._build_doc_frequencies(sections)
        
        # Get query terms
        query_terms = self._get_query_terms(query_profile)
        
        # Calculate TF-IDF scores
        scores = []
        for section in sections:
            score = self._calculate_tfidf_score(section, query_terms)
            scores.append(score)
        
        return self.normalize_scores(scores)
    
    def _build_doc_frequencies(self, sections: List[Dict]):
        """Build document frequency statistics"""
        self.total_docs = len(sections)
        self.doc_frequencies = Counter()
        
        for section in sections:
            # Get unique terms in section
            terms = set(self._tokenize(section.get('content', '')))
            terms.update(self._tokenize(section.get('title', '')))
            
            # Update document frequencies
            for term in terms:
                self.doc_frequencies[term] += 1
    
    def _get_query_terms(self, query_profile: Dict) -> Dict[str, float]:
        """Extract weighted query terms"""
        query_terms = {}
        
        # Get weighted query from profile
        if 'query' in query_profile and 'weighted_query' in query_profile['query']:
            query_terms.update(query_profile['query']['weighted_query'])
        
# src/ranking_engine/scorers/tfidf_scorer.py (continued)
        # Add primary terms if not in weighted query
        if 'query' in query_profile and 'primary_terms' in query_profile['query']:
            for term in query_profile['query']['primary_terms']:
                if term not in query_terms:
                    query_terms[term] = 0.8
        
        return query_terms
    
    def _calculate_tfidf_score(self, section: Dict, query_terms: Dict[str, float]) -> float:
        """Calculate TF-IDF score for a section"""
        # Tokenize section content
        content = f"{section.get('title', '')} {section.get('content', '')}"
        terms = self._tokenize(content)
        
        if not terms:
            return 0.0
        
        # Calculate term frequencies
        term_freq = Counter(terms)
        max_freq = max(term_freq.values()) if term_freq else 1
        
        # Calculate TF-IDF score
        score = 0.0
        matched_terms = 0
        
        for query_term, weight in query_terms.items():
            if query_term in term_freq:
                # Term frequency (normalized)
                tf = 0.5 + 0.5 * (term_freq[query_term] / max_freq)
                
                # Inverse document frequency
                df = self.doc_frequencies.get(query_term, 0)
                idf = math.log(self.total_docs / (1 + df))
                
                # TF-IDF score
                score += tf * idf * weight
                matched_terms += 1
        
        # Bonus for matching multiple query terms
        if matched_terms > 1:
            score *= (1 + 0.1 * math.log(matched_terms))
        
        return score
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        if not text:
            return []
        
        # Convert to lowercase and split
        tokens = text.lower().split()
        
        # Remove punctuation and short tokens
        cleaned = []
        for token in tokens:
            # Remove punctuation from edges
            token = token.strip('.,!?;:"()[]{}')
            if len(token) > 2:
                cleaned.append(token)
        
        return cleaned