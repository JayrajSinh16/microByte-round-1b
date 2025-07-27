# src/outline_extraction/classifiers/ensemble_voter.py
import logging
from typing import List, Dict
from collections import defaultdict

from .hierarchy_classifier import HierarchyClassifier
from .confidence_scorer import ConfidenceScorer

logger = logging.getLogger(__name__)

class EnsembleVoter:
    """Ensemble voting for heading detection"""
    
    def __init__(self):
        self.hierarchy_classifier = HierarchyClassifier()
        self.confidence_scorer = ConfidenceScorer()
        
        # Default weights for strategies
        self.default_weights = {
            'universal': 0.5,  # Give universal strategy highest weight
            'font': 0.2,
            'pattern': 0.15,
            'ml': 0.1,
            'structural': 0.05,
            'semantic': 0.0  # Disable for now
        }
    
    def vote(self, strategy_predictions: Dict[str, List[Dict]], 
            blocks: List[Dict] = None,
            weights: Dict[str, float] = None) -> List[Dict]:
        """Perform ensemble voting on strategy predictions"""
        
        if not strategy_predictions:
            return []
        
        # Use provided weights or defaults
        weights = weights or self.default_weights
        
        # Get number of blocks from first strategy
        first_strategy = next(iter(strategy_predictions.values()))
        num_blocks = len(first_strategy)
        
        # Initialize final predictions
        final_predictions = []
        
        for block_idx in range(num_blocks):
            # Collect votes from each strategy
            votes = {
                'is_heading': 0.0,
                'not_heading': 0.0,
                'levels': defaultdict(float),
                'confidences': []
            }
            
            block_id = None
            
            for strategy_name, predictions in strategy_predictions.items():
                if block_idx >= len(predictions):
                    continue
                
                pred = predictions[block_idx]
                weight = weights.get(strategy_name, 0.1)
                
                # Get block ID
                if block_id is None:
                    block_id = pred.get('block_id')
                
                # Vote on heading/not heading
                if pred.get('is_heading', False):
                    votes['is_heading'] += weight * pred.get('confidence', 1.0)
                    
                    # Vote on level if provided
                    if pred.get('level'):
                        votes['levels'][pred['level']] += weight * pred.get('confidence', 1.0)
                else:
                    votes['not_heading'] += weight * (1.0 - pred.get('confidence', 0.0))
                
                votes['confidences'].append(pred.get('confidence', 0.0))
            
            # Make final decision
            is_heading = votes['is_heading'] > votes['not_heading']
            
            # Determine level if heading
            level = None
            if is_heading and votes['levels']:
                level = max(votes['levels'].items(), key=lambda x: x[1])[0]
            
            # Calculate final confidence
            confidence = self.confidence_scorer.calculate_ensemble_confidence(
                votes, strategy_predictions, block_idx
            )
            
            final_predictions.append({
                'block_id': block_id,
                'is_heading': is_heading,
                'level': level,
                'confidence': confidence,
                'vote_details': {
                    'heading_score': votes['is_heading'],
                    'not_heading_score': votes['not_heading'],
                    'level_votes': dict(votes['levels'])
                }
            })
        # Post-process: classify hierarchy levels
        if blocks:
            headings = [p for p in final_predictions if p['is_heading']]
            if headings:
                # Re-classify levels based on ensemble results
                classified_headings = self.hierarchy_classifier.classify(headings, blocks)
                
                # Update final predictions with classified levels
                heading_map = {h['block_id']: h for h in classified_headings}
                
                for pred in final_predictions:
                    if pred['block_id'] in heading_map:
                        pred['level'] = heading_map[pred['block_id']]['level']
        
        return final_predictions