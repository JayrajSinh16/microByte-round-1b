# src/ranking_engine/scorers/bm25_scorer.py
import math
from typing import List, Dict
from collections import Counter
import numpy as np

from .base_scorer import BaseScorer

class BM25Scorer(BaseScorer):
    """BM25 scoring algorithm"""
    
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1  # Term frequency saturation parameter
        self.b = b    # Length normalization parameter
        self.doc_frequencies = {}
        self.avg_doc_length = 0
        self.total_docs = 0
    
    def score(self, sections: List[Dict], query_profile: Dict) -> List[float]:
        """Score sections using BM25"""
        # Build statistics
        self._build_statistics(sections)
        
        # Get query terms
        query_terms = self._get_query_terms(query_profile)
        
        # Calculate BM25 scores
        scores = []
        for section in sections:
            score = self._calculate_bm25_score(section, query_terms)
            scores.append(score)
        
        return self.normalize_scores(scores)
    
    def _build_statistics(self, sections: List[Dict]):
        """Build document statistics for BM25"""
        self.total_docs = len(sections)
        self.doc_frequencies = Counter()
        doc_lengths = []
        
        for section in sections:
            # Get terms
            content = f"{section.get('title', '')} {section.get('content', '')}"
            terms = self._tokenize(content)
            doc_lengths.append(len(terms))
            
            # Update document frequencies
            unique_terms = set(terms)
            for term in unique_terms:
                self.doc_frequencies[term] += 1
        
        # Calculate average document length
        self.avg_doc_length = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1
    
    def _get_query_terms(self, query_profile: Dict) -> List[str]:
        """Extract query terms"""
        terms = []
        
        # Primary terms
        if 'query' in query_profile:
            terms.extend(query_profile['query'].get('primary_terms', []))
            terms.extend(query_profile['query'].get('must_have_terms', []))
        
        return list(set(terms))
    
    def _calculate_bm25_score(self, section: Dict, query_terms: List[str]) -> float:
        """Calculate BM25 score for a section"""
        content = f"{section.get('title', '')} {section.get('content', '')}"
        doc_terms = self._tokenize(content)
        doc_length = len(doc_terms)
        
        if not doc_terms:
            return 0.0
        
        # Count term frequencies
        term_freq = Counter(doc_terms)
        
        # Calculate BM25 score
        score = 0.0
        
        for query_term in query_terms:
            if query_term not in term_freq:
                continue
            
            # Term frequency in document
            tf = term_freq[query_term]
            
            # Document frequency
            df = self.doc_frequencies.get(query_term, 0)
            
            # IDF component
            idf = math.log((self.total_docs - df + 0.5) / (df + 0.5))
            
            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
            
            score += idf * (numerator / denominator)
        
        return score
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text"""
        if not text:
            return []
        
        tokens = text.lower().split()
        cleaned = []
        
        for token in tokens:
            token = token.strip('.,!?;:"()[]{}')
            if len(token) > 2:
                cleaned.append(token)
        
        return cleaned