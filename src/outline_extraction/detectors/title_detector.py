# src/outline_extraction/detectors/title_detector.py
import re
import logging
from typing import List, Dict, Optional

from config.constants import TITLE_SIZE_RATIO

logger = logging.getLogger(__name__)

class TitleDetector:
    """Detect document title"""
    
    def __init__(self):
        self.title_indicators = [
            'title_case',  # Most Words Capitalized
            'all_caps',    # ALL CAPS
            'large_font',  # Significantly larger than body
            'centered',    # Centered on page
            'isolated',    # Surrounded by whitespace
            'metadata'     # Found in PDF metadata
        ]
    
    def detect(self, blocks: List[Dict], metadata: Dict = None) -> Optional[Dict]:
        """Detect document title from blocks"""
        # Try metadata first
        if metadata and metadata.get('title'):
            return {
                'text': metadata['title'],
                'source': 'metadata',
                'confidence': 0.9
            }
        
        # Look for title in first page blocks
        first_page_blocks = [b for b in blocks if b.get('page', 1) == 1]
        
        if not first_page_blocks:
            return None
        
        # Score each block
        title_candidates = []
        
        for block in first_page_blocks[:10]:  # Check first 10 blocks
            score = self._score_title_candidate(block, blocks)
            
            if score > 0.5:
                title_candidates.append({
                    'block': block,
                    'score': score
                })
        
        # Return best candidate
        if title_candidates:
            best = max(title_candidates, key=lambda x: x['score'])
            return {
                'text': best['block']['text'].strip(),
                'source': 'detection',
                'confidence': best['score'],
                'block_id': best['block'].get('id')
            }
        
        # Fallback: largest text on first page
        largest_block = max(first_page_blocks, 
                          key=lambda b: b.get('font_size', 0))
        
        return {
            'text': largest_block['text'].strip(),
            'source': 'fallback',
            'confidence': 0.3
        }
    
    def _score_title_candidate(self, block: Dict, all_blocks: List[Dict]) -> float:
        """Score a block as potential title"""
        score = 0.0
        text = block.get('text', '').strip()
        
        if not text:
            return 0.0
        
        # Font size check
        avg_font_size = self._get_avg_font_size(all_blocks)
        if block.get('font_size', 0) > avg_font_size * TITLE_SIZE_RATIO:
            score += 0.3
        
        # Position check (top of page)
        if block.get('y', 0) < 200:  # Top 200 pixels
            score += 0.2
        
        # Capitalization check
        if self._is_title_case(text) or text.isupper():
            score += 0.2
        
        # Length check (titles are usually short)
        word_count = len(text.split())
        if 2 <= word_count <= 15:
            score += 0.2
        
        # No ending punctuation
        if not text[-1] in '.!?,;:':
            score += 0.1
        
        # Centered check
        if self._is_centered(block):
            score += 0.1
        
        # Bold check
        if block.get('is_bold', False):
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_avg_font_size(self, blocks: List[Dict]) -> float:
        """Get average font size across all blocks"""
        sizes = [b.get('font_size', 0) for b in blocks if b.get('font_size', 0) > 0]
        return sum(sizes) / len(sizes) if sizes else 12.0
    
    def _is_title_case(self, text: str) -> bool:
        """Check if text is in title case"""
        words = text.split()
        if not words:
            return False
        
        # Count capitalized words (excluding short words)
        cap_count = sum(1 for w in words 
                       if len(w) > 3 and w[0].isupper())
        
        return cap_count / len(words) > 0.7
    
    def _is_centered(self, block: Dict) -> bool:
        """Check if block appears centered"""
        # This is approximate without page width
        # Blocks with similar left margin and seemingly centered
        x = block.get('x', 0)
        width = block.get('width', 0)
        
        # Assume page width around 600-800
        estimated_center = 400
        block_center = x + width / 2
        
        return abs(block_center - estimated_center) < 100