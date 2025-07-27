# src/outline_extraction/detectors/heading_detector.py
import logging
from typing import List, Dict, Any

from ..strategies import (
    FontStrategy, PatternStrategy, MLStrategy, 
    StructuralStrategy, SemanticStrategy, UniversalStrategy
)
from config.constants import MIN_HEADING_LENGTH, MAX_HEADING_LENGTH

logger = logging.getLogger(__name__)

class HeadingDetector:
    """Main heading detection orchestrator"""
    
    def __init__(self):
        self.strategies = {
            'universal': UniversalStrategy(),  # Primary strategy
            'font': FontStrategy(),
            'pattern': PatternStrategy(),
            'ml': MLStrategy(),
            'structural': StructuralStrategy(),
            'semantic': SemanticStrategy()
        }
        
        self.weights = {
            'universal': 0.5,  # Give universal strategy highest weight
            'font': 0.2,
            'pattern': 0.15,
            'ml': 0.1,
            'structural': 0.05,
            'semantic': 0.0  # Disable for now
        }
    
    def detect(self, blocks: List[Dict], profile: Dict) -> Dict[str, List[Dict]]:
        """Detect headings using multiple strategies"""
        # Filter blocks that could be headings
        candidate_blocks = self._filter_candidates(blocks)
        
        # Create mapping from candidate index to original block ID
        candidate_to_original = {}
        original_block_ids = {block['id']: i for i, block in enumerate(blocks)}
        
        for candidate_idx, candidate_block in enumerate(candidate_blocks):
            candidate_to_original[candidate_idx] = candidate_block['id']
        
        # Run all strategies
        all_predictions = {}
        for name, strategy in self.strategies.items():
            try:
                predictions = strategy.detect(candidate_blocks, profile)
                
                # Map block_ids back to original blocks
                mapped_predictions = []
                for pred in predictions:
                    candidate_block_id = pred['block_id']
                    if candidate_block_id in candidate_to_original:
                        original_block_id = candidate_to_original[candidate_block_id]
                        mapped_pred = pred.copy()
                        mapped_pred['block_id'] = original_block_id
                        mapped_predictions.append(mapped_pred)
                
                all_predictions[name] = mapped_predictions
                logger.debug(f"{name} strategy detected {sum(1 for p in mapped_predictions if p['is_heading'])} headings")
            except Exception as e:
                logger.error(f"Strategy {name} failed: {str(e)}")
                all_predictions[name] = []
        
        return all_predictions
    
    def _filter_candidates(self, blocks: List[Dict]) -> List[Dict]:
        """Filter blocks that could potentially be headings"""
        candidates = []
        
        for block in blocks:
            text = block.get('text', '').strip()
            
            # Basic length check
            if not (MIN_HEADING_LENGTH <= len(text) <= MAX_HEADING_LENGTH):
                continue
            
            # Skip multi-line blocks (usually paragraphs)
            if text.count('\n') > 2:
                continue
            
            # Skip blocks that are likely captions
            if any(text.lower().startswith(prefix) for prefix in ['figure ', 'table ', 'fig.', 'tab.']):
                continue
            
            # Skip page numbers
            if text.isdigit() or (text.startswith('Page ') and any(c.isdigit() for c in text)):
                continue
            
            candidates.append(block)
        
        return candidates