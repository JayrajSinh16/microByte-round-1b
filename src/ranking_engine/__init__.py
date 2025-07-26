# src/ranking_engine/__init__.py
from typing import Dict, List
from .scorers import TFIDFScorer, BM25Scorer, SemanticScorer, StructuralScorer
from .filters import KeywordFilter, LengthFilter, RelevanceFilter
from .rankers import EnsembleRanker, CrossDocRanker, FinalRanker
from .embeddings import EmbeddingManager

class RankingEngine:
    """Main ranking engine interface"""
    
    def __init__(self):
        # Initialize scorers
        self.tfidf_scorer = TFIDFScorer()
        self.bm25_scorer = BM25Scorer()
        self.semantic_scorer = SemanticScorer()
        self.structural_scorer = StructuralScorer()
        
        # Initialize filters
        self.keyword_filter = KeywordFilter()
        self.length_filter = LengthFilter()
        self.relevance_filter = RelevanceFilter()
        
        # Initialize rankers
        self.ensemble_ranker = EnsembleRanker()
        self.cross_doc_ranker = CrossDocRanker()
        self.final_ranker = FinalRanker()
        
        # Embedding manager
        self.embedding_manager = EmbeddingManager()
    
    def rank(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Rank sections based on query profile"""
        # Stage 1: Initial filtering
        filtered_sections = self._apply_filters(sections, query_profile)
        
        # Stage 2: Score sections
        scored_sections = self._score_sections(filtered_sections, query_profile)
        
        # Stage 3: Cross-document analysis
        cross_doc_scored = self.cross_doc_ranker.rank(scored_sections)
        
        # Stage 4: Final ranking
        final_ranked = self.final_ranker.rank(cross_doc_scored, query_profile)
        
        return final_ranked
    
    def _apply_filters(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Apply filtering stages"""
        # Length filter
        sections = self.length_filter.filter(sections)
        
        # Keyword filter
        sections = self.keyword_filter.filter(sections, query_profile)
        
        # Initial relevance filter
        sections = self.relevance_filter.filter(sections, query_profile)
        
        return sections
    
    def _score_sections(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Score sections using multiple methods"""
        # Calculate individual scores
        tfidf_scores = self.tfidf_scorer.score(sections, query_profile)
        bm25_scores = self.bm25_scorer.score(sections, query_profile)
        semantic_scores = self.semantic_scorer.score(sections, query_profile)
        structural_scores = self.structural_scorer.score(sections, query_profile)
        
        # Combine scores
        for i, section in enumerate(sections):
            section['scores'] = {
                'tfidf': tfidf_scores[i],
                'bm25': bm25_scores[i],
                'semantic': semantic_scores[i],
                'structural': structural_scores[i]
            }
            
            # Calculate ensemble score
            section['final_score'] = self.ensemble_ranker.combine_scores(
                section['scores'], query_profile
            )
        
        return sections

__all__ = ['RankingEngine']