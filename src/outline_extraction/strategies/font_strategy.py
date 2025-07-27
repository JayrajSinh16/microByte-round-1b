# src/outline_extraction/strategies/font_strategy.py
import numpy as np
from typing import List, Dict
from collections import Counter
from sklearn.cluster import KMeans

from .base_strategy import BaseStrategy
from config.constants import (
    TITLE_SIZE_RATIO, H1_SIZE_RATIO, 
    H2_SIZE_RATIO, H3_SIZE_RATIO
)

class FontStrategy(BaseStrategy):
    """Font-based heading detection strategy"""
    
    def detect(self, blocks: List[Dict], profile: Dict) -> List[Dict]:
        """Detect headings based on font characteristics"""
        predictions = []
        
        # Get font statistics
        font_stats = self._calculate_font_stats(blocks)
        body_font_size = font_stats['body_size']
        
        for block in blocks:
            prediction = {
                'block_id': block['id'],
                'is_heading': False,
                'level': None,
                'confidence': 0.0
            }
            
            # Calculate size ratio
            size_ratio = block['font_size'] / body_font_size if body_font_size > 0 else 1
            
            # Check if heading based on font
            if self._is_heading_by_font(block, size_ratio):
                prediction['is_heading'] = True
                prediction['level'] = self._classify_level(block, font_stats)
                prediction['confidence'] = self._calculate_confidence(block, size_ratio)
            
            predictions.append(prediction)
        
        return predictions
    
    def _calculate_font_stats(self, blocks: List[Dict]) -> Dict:
        """Calculate font statistics for the document"""
        font_sizes = [b['font_size'] for b in blocks if b['font_size'] > 0]
        
        if not font_sizes:
            return {'body_size': 12, 'sizes': []}
        
        # Find body text size (most common)
        size_counter = Counter(font_sizes)
        body_size = size_counter.most_common(1)[0][0]
        
        # Find unique font sizes for clustering
        unique_sizes = list(set(font_sizes))
        
        return {
            'body_size': body_size,
            'sizes': sorted(unique_sizes, reverse=True),
            'size_distribution': size_counter
        }
    
    def _is_heading_by_font(self, block: Dict, size_ratio: float) -> bool:
        """Determine if block is heading based on font"""
        # Size-based detection
        if size_ratio >= H3_SIZE_RATIO:
            return True
        
        # Bold text detection - MORE AGGRESSIVE for travel guides
        # Allow bold text with same font size as body text if it's short enough
        if block.get('is_bold', False) and len(block['text']) < 200:
            text_words = len(block['text'].split())
            # Allow bold text that looks like a heading (short, meaningful)
            if text_words <= 15 and size_ratio >= 0.9:  # Even if slightly smaller than body
                return True
        
        # All caps detection
        if block['text'].isupper() and len(block['text'].split()) < 10:
            return True
        
        return False
    
    def _classify_level(self, block: Dict, font_stats: Dict) -> str:
        """Classify heading level based on font size"""
        font_size = block['font_size']
        sizes = font_stats['sizes']
        
        if not sizes:
            return 'H1'
        
        # Find size rank
        size_rank = len([s for s in sizes if s > font_size])
        
        if size_rank == 0:  # Largest
            return 'H1'
        elif size_rank == 1:  # Second largest
            return 'H2'
        else:
            return 'H3'
    
    def _calculate_confidence(self, block: Dict, size_ratio: float) -> float:
        """Calculate confidence score for font-based detection"""
        confidence = 0.0
        
        # Size contribution
        if size_ratio >= TITLE_SIZE_RATIO:
            confidence += 0.4
        elif size_ratio >= H1_SIZE_RATIO:
            confidence += 0.3
        elif size_ratio >= H2_SIZE_RATIO:
            confidence += 0.2
        elif size_ratio >= H3_SIZE_RATIO:
            confidence += 0.15
        else:
            # Even if font size is same/smaller, give some confidence for structure
            confidence += 0.1
        
        # Style contribution - INCREASED for bold text
        if block.get('is_bold', False):
            if size_ratio >= 0.9:  # Bold text with reasonable size
                confidence += 0.3  # Increased from 0.2
            else:
                confidence += 0.2
        
        # Length contribution - headings should be concise
        text_length = len(block['text'])
        word_count = len(block['text'].split())
        if word_count <= 15 and text_length < 150:  # Good heading length
            confidence += 0.25
        elif text_length < 50:
            confidence += 0.2
        elif text_length < 100:
            confidence += 0.1
        
        # Position contribution
        if block.get('page', 1) == 1 and block.get('y', 0) < 200:
            confidence += 0.1
        
        return min(confidence, 1.0)