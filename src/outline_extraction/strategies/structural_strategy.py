# src/outline_extraction/strategies/structural_strategy.py
import numpy as np
from typing import List, Dict, Optional
from collections import defaultdict

from .base_strategy import BaseStrategy

class StructuralStrategy(BaseStrategy):
    """Detect headings based on document structure"""
    
    def __init__(self):
        self.spacing_threshold = 1.5  # 1.5x average spacing
        self.isolation_threshold = 2.0  # 2x average spacing
    
    def detect(self, blocks: List[Dict], profile: Dict) -> List[Dict]:
        """Detect headings based on structural patterns"""
        predictions = []
        
        # Calculate structural metrics
        metrics = self._calculate_structural_metrics(blocks)
        
        for i, block in enumerate(blocks):
            prediction = {
                'block_id': block['id'],
                'is_heading': False,
                'level': None,
                'confidence': 0.0
            }
            
            # Get block metrics
            block_metrics = self._get_block_metrics(block, i, blocks, metrics)
            
            # Check structural indicators
            if self._is_structurally_heading(block_metrics):
                prediction['is_heading'] = True
                prediction['level'] = self._determine_level_from_structure(block_metrics)
                prediction['confidence'] = self._calculate_structural_confidence(block_metrics)
            
            predictions.append(prediction)
        
        return predictions
    
    def _calculate_structural_metrics(self, blocks: List[Dict]) -> Dict:
        """Calculate document-wide structural metrics"""
        metrics = {
            'avg_spacing': 0,
            'avg_font_size': 0,
            'avg_line_height': 0,
            'page_margins': defaultdict(list),
            'column_positions': []
        }
        
        # Calculate spacing between consecutive blocks
        spacings = []
        font_sizes = []
        
        for i in range(len(blocks) - 1):
            current = blocks[i]
            next_block = blocks[i + 1]
            
            # Only calculate spacing on same page
            if current.get('page') == next_block.get('page'):
                spacing = next_block.get('y', 0) - (current.get('y', 0) + current.get('height', 0))
                if spacing > 0:
                    spacings.append(spacing)
            
            # Collect font sizes
            if current.get('font_size', 0) > 0:
                font_sizes.append(current['font_size'])
        
        # Last block font size
        if blocks and blocks[-1].get('font_size', 0) > 0:
            font_sizes.append(blocks[-1]['font_size'])
        
        # Calculate averages
        metrics['avg_spacing'] = np.mean(spacings) if spacings else 10
        metrics['avg_font_size'] = np.mean(font_sizes) if font_sizes else 12
        
        # Analyze margins
        for block in blocks:
            page = block.get('page', 1)
            metrics['page_margins'][page].append(block.get('x', 0))
        
        return metrics
    
    def _get_block_metrics(self, block: Dict, index: int, 
                          blocks: List[Dict], doc_metrics: Dict) -> Dict:
        """Get structural metrics for a specific block"""
        metrics = {
            'block': block,
            'index': index,
            'spacing_before': 0,
            'spacing_after': 0,
            'is_isolated': False,
            'is_indented': False,
            'is_centered': False,
            'relative_font_size': 1.0,
            'line_count': 1,
            'follows_paragraph': False,
            'precedes_paragraph': False
        }
        
        # Calculate spacing
        if index > 0:
            prev_block = blocks[index - 1]
            if prev_block.get('page') == block.get('page'):
                metrics['spacing_before'] = (
                    block.get('y', 0) - 
                    (prev_block.get('y', 0) + prev_block.get('height', 0))
                )
                metrics['follows_paragraph'] = len(prev_block.get('text', '').split()) > 20
        
        if index < len(blocks) - 1:
            next_block = blocks[index + 1]
            if next_block.get('page') == block.get('page'):
                metrics['spacing_after'] = (
                    next_block.get('y', 0) - 
                    (block.get('y', 0) + block.get('height', 0))
                )
                metrics['precedes_paragraph'] = len(next_block.get('text', '').split()) > 20
        
        # Check isolation
        avg_spacing = doc_metrics['avg_spacing']
        if (metrics['spacing_before'] > avg_spacing * self.isolation_threshold and
            metrics['spacing_after'] > avg_spacing * self.isolation_threshold):
            metrics['is_isolated'] = True
        
        # Check indentation
        page_margins = doc_metrics['page_margins'][block.get('page', 1)]
        if page_margins:
            min_margin = min(page_margins)
            if block.get('x', 0) > min_margin + 20:
                metrics['is_indented'] = True
        
        # Check if centered (approximate)
        if block.get('x', 0) > 100 and block.get('width', 0) < 400:
            metrics['is_centered'] = True
        
        # Font size ratio
        if doc_metrics['avg_font_size'] > 0:
            metrics['relative_font_size'] = (
                block.get('font_size', 0) / doc_metrics['avg_font_size']
            )
        
        # Line count
        metrics['line_count'] = block.get('text', '').count('\n') + 1
        
        return metrics
    
    def _is_structurally_heading(self, metrics: Dict) -> bool:
        """Determine if block is heading based on structure"""
        block = metrics['block']
        
        # Short, isolated text is likely heading
        if (metrics['is_isolated'] and 
            len(block.get('text', '').split()) < 15):
            return True
        
        # Large spacing before and after
        avg_spacing = metrics.get('avg_spacing', 10)
        if (metrics['spacing_before'] > avg_spacing * self.spacing_threshold and
            metrics['spacing_after'] > avg_spacing * self.spacing_threshold):
            return True
        
        # Centered short text
        if (metrics['is_centered'] and 
            len(block.get('text', '').split()) < 10):
            return True
        
        # Between paragraphs with good spacing
        if (metrics['follows_paragraph'] and 
            metrics['precedes_paragraph'] and
            metrics['spacing_before'] > avg_spacing):
            return True
        
        return False
    
    def _determine_level_from_structure(self, metrics: Dict) -> str:
        """Determine heading level from structural features"""
        # Very isolated = H1
        if metrics['is_isolated']:
            return 'H1'
        
        # Centered = often H1
        if metrics['is_centered']:
            return 'H1'
        
        # Indented = H2 or H3
        if metrics['is_indented']:
            return 'H3'
        
        # Based on font size
        if metrics['relative_font_size'] > 1.3:
            return 'H1'
        elif metrics['relative_font_size'] > 1.15:
            return 'H2'
        
        return 'H2'  # Default
    
    def _calculate_structural_confidence(self, metrics: Dict) -> float:
        """Calculate confidence based on structural features"""
        confidence = 0.0
        
        # Isolation is strong indicator
        if metrics['is_isolated']:
            confidence += 0.4
        
        # Large spacing
        if metrics['spacing_before'] > 20 or metrics['spacing_after'] > 20:
            confidence += 0.2
        
        # Centered
        if metrics['is_centered']:
            confidence += 0.2
        
        # Font size
        if metrics['relative_font_size'] > 1.2:
            confidence += 0.2
        
        # Between paragraphs
        if metrics['follows_paragraph'] and metrics['precedes_paragraph']:
            confidence += 0.1
        
        # Single line
        if metrics['line_count'] == 1:
            confidence += 0.1
        
        return min(confidence, 1.0)