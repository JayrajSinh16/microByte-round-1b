# src/ranking_engine/__init__.py
from typing import Dict, List
from .scorers import TFIDFScorer, BM25Scorer, SemanticScorer, StructuralScorer, DomainAwareScorer
from .filters import KeywordFilter, LengthFilter, RelevanceFilter, SemanticSectionFilter
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
        self.domain_aware_scorer = DomainAwareScorer()
        
        # Initialize filters
        self.keyword_filter = KeywordFilter()
        self.length_filter = LengthFilter()
        self.relevance_filter = RelevanceFilter()
        self.semantic_section_filter = SemanticSectionFilter()
        
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
        """Apply filtering stages with semantic scoring"""
        # Length filter
        sections = self.length_filter.filter(sections)
        
        # Keyword filter
        sections = self.keyword_filter.filter(sections, query_profile)
        
        # Initial relevance filter
        sections = self.relevance_filter.filter(sections, query_profile)
        
        # Semantic section filter (dynamic persona-driven)
        sections = self.semantic_section_filter.filter(sections, query_profile)
        
        return sections
    
    def _score_sections(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Score sections using multiple methods including domain awareness"""
        # Calculate individual scores
        tfidf_scores = self.tfidf_scorer.score(sections, query_profile)
        bm25_scores = self.bm25_scorer.score(sections, query_profile)
        semantic_scores = self.semantic_scorer.score(sections, query_profile)
        structural_scores = self.structural_scorer.score(sections, query_profile)
        domain_scores = self.domain_aware_scorer.score(sections, query_profile)
        
        # Get domain-specific weights
        domain_type = query_profile.get('domain_profile', {}).get('domain', 'travel_planner')
        weights = self._get_scorer_weights(domain_type)
        
        # Combine scores
        for i, section in enumerate(sections):
            section['scores'] = {
                'tfidf': tfidf_scores[i],
                'bm25': bm25_scores[i],
                'semantic': semantic_scores[i],
                'structural': structural_scores[i],
                'domain': domain_scores[i]
            }
            
            # Calculate ensemble score with domain awareness
            section['final_score'] = (
                tfidf_scores[i] * weights['tfidf'] +
                bm25_scores[i] * weights['bm25'] +
                semantic_scores[i] * weights['semantic'] +
                structural_scores[i] * weights['structural'] +
                domain_scores[i] * weights['domain']
            )
        
        return sections
    
    def _get_scorer_weights(self, domain_type: str) -> Dict[str, float]:
        """Get scorer weights based on domain type"""
        domain_weights = {
            'travel_planner': {
                'tfidf': 0.15,
                'bm25': 0.15, 
                'semantic': 0.25,
                'structural': 0.15,
                'domain': 0.30  # Higher weight for domain-specific scoring
            },
            'food_contractor': {
                'tfidf': 0.20,
                'bm25': 0.20,
                'semantic': 0.20,
                'structural': 0.15,
                'domain': 0.25
            },
            'hr_professional': {
                'tfidf': 0.25,
                'bm25': 0.25,
                'semantic': 0.15,
                'structural': 0.15,
                'domain': 0.20
            },
            'business_analyst': {
                'tfidf': 0.25,
                'bm25': 0.25,
                'semantic': 0.15,
                'structural': 0.20,
                'domain': 0.15
            }
        }
        
        return domain_weights.get(domain_type, domain_weights['travel_planner'])

__all__ = ['RankingEngine']