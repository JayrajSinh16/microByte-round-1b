# src/outline_extraction/detectors/heading_detector.py
import logging
from typing import List, Dict, Any

from ..strategies import (
    FontStrategy, PatternStrategy, MLStrategy, 
    StructuralStrategy, SemanticStrategy, UniversalStrategy
)
from ..strategies.universal_document_strategy import UniversalDocumentStrategy
from config.constants import MIN_HEADING_LENGTH, MAX_HEADING_LENGTH

logger = logging.getLogger(__name__)

class HeadingDetector:
    """Main heading detection orchestrator"""
    
    def __init__(self):
        self.strategies = {
            'universal_document': UniversalDocumentStrategy(),  # NEW: Primary universal strategy
            'universal': UniversalStrategy(),  # Keep as fallback
            'font': FontStrategy(),
            'pattern': PatternStrategy(),
            'ml': MLStrategy(),
            'structural': StructuralStrategy(),
            'semantic': SemanticStrategy()
        }
        
        self.weights = {
            'universal_document': 0.6,  # Give our new strategy highest weight
            'universal': 0.2,           # Reduce original universal weight
            'font': 0.1,
            'pattern': 0.05,
            'ml': 0.03,
            'structural': 0.02,
            'semantic': 0.0  # Disable for now
        }
    
    def detect(self, blocks: List[Dict], profile: Dict) -> Dict[str, List[Dict]]:
        """Detect headings using multiple strategies"""
        # Filter blocks that could be headings for most strategies
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
                # Use all blocks for universal_document strategy (it extracts headings from within blocks)
                if name == 'universal_document':
                    predictions = strategy.detect(blocks, profile)
                    # No need to remap since we're using original blocks
                    all_predictions[name] = predictions
                else:
                    # Use filtered candidates for other strategies
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
                
                logger.debug(f"{name} strategy detected {sum(1 for p in all_predictions[name] if p['is_heading'])} headings")
            except Exception as e:
                logger.error(f"Strategy {name} failed: {str(e)}")
                all_predictions[name] = []
        
        return all_predictions
        
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