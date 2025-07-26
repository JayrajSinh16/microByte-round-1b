# src/outline_extraction/classifiers/confidence_scorer.py
import numpy as np
from typing import Dict, List, Any

class ConfidenceScorer:
    """Calculate confidence scores for heading detection"""
    
    def calculate_ensemble_confidence(self, votes: Dict, 
                                    strategy_predictions: Dict,
                                    block_idx: int) -> float:
        """Calculate confidence score from ensemble voting"""
        
        # Base confidence from vote ratio
        total_votes = votes['is_heading'] + votes['not_heading']
        if total_votes > 0:
            vote_confidence = votes['is_heading'] / total_votes
        else:
            vote_confidence = 0.0
        
        # Agreement among strategies
        confidences = votes['confidences']
        if confidences:
            # Calculate standard deviation as measure of disagreement
            std_dev = np.std(confidences)
            agreement_score = 1.0 - min(std_dev, 1.0)
            
            # Average confidence
            avg_confidence = np.mean(confidences)
        else:
            agreement_score = 0.0
            avg_confidence = 0.0
        
        # Level agreement (if heading)
        level_agreement = 1.0
        if votes['levels']:
            # Check how concentrated the level votes are
            level_values = list(votes['levels'].values())
            total_level_votes = sum(level_values)
            if total_level_votes > 0:
                max_level_vote = max(level_values)
                level_agreement = max_level_vote / total_level_votes
        
        # Combine factors
        final_confidence = (
            0.4 * vote_confidence +
            0.3 * avg_confidence +
            0.2 * agreement_score +
            0.1 * level_agreement
        )
        
        return round(final_confidence, 3)
    
    def calculate_heading_quality_score(self, block: Dict, 
                                      context: Dict = None) -> float:
        """Calculate quality score for a detected heading"""
        score = 0.0
        
        text = block.get('text', '').strip()
        
        # Length score (headings are typically short)
        word_count = len(text.split())
        if 2 <= word_count <= 10:
            score += 0.3
        elif word_count <= 15:
            score += 0.2
        elif word_count <= 20:
            score += 0.1
        
        # Formatting score
        if block.get('is_bold', False):
            score += 0.2
        
        if block.get('font_size', 0) > 14:
            score += 0.1
        
        # Position score (if context provided)
        if context:
            if context.get('is_isolated', False):
                score += 0.2
            if context.get('is_centered', False):
                score += 0.1
            if context.get('at_top_of_page', False):
                score += 0.1
        
        # Text characteristics
        if text and text[0].isupper():
            score += 0.05
        
        if not text.endswith('.'):
            score += 0.05
        
        return min(score, 1.0)