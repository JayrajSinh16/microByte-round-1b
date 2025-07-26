# src/ranking_engine/rankers/ensemble_ranker.py
from typing import Dict, Any

class EnsembleRanker:
    """Combine multiple scoring methods"""
    
    def combine_scores(self, scores: Dict[str, float], query_profile: Dict) -> float:
        """Combine individual scores into final score"""
        # Get weights from query profile
        weights = self._get_weights(query_profile)
        
        # Calculate weighted sum
        final_score = 0.0
        total_weight = 0.0
        
        for score_type, score_value in scores.items():
            weight = weights.get(score_type, 0.1)
            final_score += score_value * weight
            total_weight += weight
        
        # Normalize
        if total_weight > 0:
            final_score /= total_weight
        
        return round(final_score, 4)
    
    def _get_weights(self, query_profile: Dict) -> Dict[str, float]:
        """Get scoring weights from profile"""
        # Default weights
        default_weights = {
            'tfidf': 0.20,
            'bm25': 0.15,
            'semantic': 0.40,
            'structural': 0.15,
            'cross_doc': 0.10
        }
        
        # Check for custom weights in profile
        if 'relevance_criteria' in query_profile:
            custom_weights = query_profile['relevance_criteria'].get('relevance_weights', {})
            # Map custom weight names to our score types
            weight_mapping = {
                'keyword_match': 'tfidf',
                'semantic_similarity': 'semantic',
                'structural_position': 'structural',
                'cross_reference': 'cross_doc'
            }
            for custom_name, weight in custom_weights.items():
                if custom_name in weight_mapping:
                    default_weights[weight_mapping[custom_name]] = weight
        
        return default_weights