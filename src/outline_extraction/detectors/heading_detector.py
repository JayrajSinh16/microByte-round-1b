# src/outline_extraction/detectors/heading_detector.py
import logging
from typing import List, Dict, Any

from ..strategies import (
    FontStrategy, PatternStrategy, MLStrategy, 
    StructuralStrategy, SemanticStrategy
)
from config.constants import MIN_HEADING_LENGTH, MAX_HEADING_LENGTH

logger = logging.getLogger(__name__)

class HeadingDetector:
    """Main heading detection orchestrator"""
    
    def __init__(self):
        self.strategies = {
            'font': FontStrategy(),
            'pattern': PatternStrategy(),
            'ml': MLStrategy(),
            'structural': StructuralStrategy(),
            'semantic': SemanticStrategy()
        }
        
        self.weights = {
            'font': 0.3,
            'pattern': 0.25,
            'ml': 0.25,
            'structural': 0.15,
            'semantic': 0.05
        }
    
    def detect(self, blocks: List[Dict], profile: Dict) -> Dict[str, List[Dict]]:
        """Detect headings using multiple strategies"""
        # Filter blocks that could be headings
        candidate_blocks = self._filter_candidates(blocks)
        
        # Run all strategies
        all_predictions = {}
        for name, strategy in self.strategies.items():
            try:
                predictions = strategy.detect(candidate_blocks, profile)
                all_predictions[name] = predictions
                logger.debug(f"{name} strategy detected {sum(1 for p in predictions if p['is_heading'])} headings")
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