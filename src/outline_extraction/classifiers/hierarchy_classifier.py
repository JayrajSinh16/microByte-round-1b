# src/outline_extraction/classifiers/hierarchy_classifier.py
import re
from typing import List, Dict, Tuple
from collections import Counter

class HierarchyClassifier:
    """Classify heading hierarchy levels"""
    
    def __init__(self):
        self.level_patterns = {
            'H1': [
                re.compile(r'^\d+\.?\s+'),           # 1. or 1
                re.compile(r'^Chapter\s+\d+', re.I),
                re.compile(r'^Part\s+[IVX]+', re.I),
            ],
            'H2': [
                re.compile(r'^\d+\.\d+\.?\s+'),      # 1.1 or 1.1.
                re.compile(r'^Section\s+\d+', re.I),
            ],
            'H3': [
                re.compile(r'^\d+\.\d+\.\d+\.?\s+'), # 1.1.1
                re.compile(r'^$[a-z]$'),           # (a)
            ]
        }
    
    def classify(self, headings: List[Dict], blocks: List[Dict]) -> List[Dict]:
        """Classify heading levels based on multiple factors"""
        if not headings:
            return headings
        
        # Extract heading blocks
        heading_blocks = []
        for h in headings:
            block = next((b for b in blocks if b['id'] == h['block_id']), None)
            if block:
                heading_blocks.append({
                    'heading': h,
                    'block': block
                })
        
        # Try multiple classification methods
        pattern_levels = self._classify_by_pattern(heading_blocks)
        font_levels = self._classify_by_font(heading_blocks)
        position_levels = self._classify_by_position(heading_blocks)
        
        # Combine results
        for i, hb in enumerate(heading_blocks):
            levels = []
            
            if pattern_levels[i]:
                levels.append(pattern_levels[i])
            if font_levels[i]:
                levels.append(font_levels[i])
            if position_levels[i]:
                levels.append(position_levels[i])
            
            # Vote on final level
            if levels:
                level_counter = Counter(levels)
                hb['heading']['level'] = level_counter.most_common(1)[0][0]
            else:
                # Default to H2
                hb['heading']['level'] = 'H2'
        
        return [hb['heading'] for hb in heading_blocks]
    
    def _classify_by_pattern(self, heading_blocks: List[Dict]) -> List[str]:
        """Classify based on text patterns"""
        levels = []
        
        for hb in heading_blocks:
            text = hb['block']['text']
            level = None
            
            # Check patterns
            for level_name, patterns in self.level_patterns.items():
                for pattern in patterns:
                    if pattern.match(text):
                        level = level_name
                        break
                if level:
                    break
            
            levels.append(level)
        
        return levels
    
    def _classify_by_font(self, heading_blocks: List[Dict]) -> List[str]:
        """Classify based on font sizes"""
        # Get unique font sizes
        font_sizes = []
        for hb in heading_blocks:
            size = hb['block'].get('font_size', 0)
            if size > 0:
                font_sizes.append(size)
        
        if not font_sizes:
            return [None] * len(heading_blocks)
        
        # Find size thresholds
        unique_sizes = sorted(set(font_sizes), reverse=True)
        
        if len(unique_sizes) == 1:
            # All same size
            return ['H2'] * len(heading_blocks)
        
        # Define thresholds
        h1_threshold = unique_sizes[0] - 1
        h2_threshold = unique_sizes[min(1, len(unique_sizes)-1)] - 1 if len(unique_sizes) > 1 else 0
        
        # Classify
        levels = []
        for hb in heading_blocks:
            size = hb['block'].get('font_size', 0)
            
            if size > h1_threshold:
                levels.append('H1')
            elif size > h2_threshold:
                levels.append('H2')
            else:
                levels.append('H3')
        
        return levels
    
    def _classify_by_position(self, heading_blocks: List[Dict]) -> List[str]:
        """Classify based on document position"""
        levels = []
        
        # Group by page
        page_groups = {}
        for hb in heading_blocks:
            page = hb['block'].get('page', 1)
            if page not in page_groups:
                page_groups[page] = []
            page_groups[page].append(hb)
        
        for hb in heading_blocks:
            page = hb['block'].get('page', 1)
            page_headings = page_groups[page]
            
            # First heading on a page is often H1
            if hb == page_headings[0] and page > 1:
                levels.append('H1')
            else:
                # Use indentation
                x = hb['block'].get('x', 0)
                if x < 100:
                    levels.append('H1')
                elif x < 150:
                    levels.append('H2')
                else:
                    levels.append('H3')
        
        return levels