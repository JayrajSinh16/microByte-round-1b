# src/outline_extraction/profilers/layout_analyzer.py
import fitz
import numpy as np
from typing import Any, Dict, List, Tuple
from collections import Counter

class LayoutAnalyzer:
    """Analyze document layout structure"""
    
    def __init__(self):
        self.column_threshold = 50  # pixels
        self.margin_threshold = 0.1  # 10% of page width
    
    def analyze(self, doc: fitz.Document) -> Dict[str, Any]:
        """Analyze document layout"""
        layout_info = {
            'columns': self._detect_columns(doc),
            'margins': self._analyze_margins(doc),
            'orientation': self._detect_orientation(doc),
            'has_headers': self._detect_headers(doc),
            'has_footers': self._detect_footers(doc),
            'has_sidebars': self._detect_sidebars(doc),
            'layout_type': 'unknown'
        }
        
        # Determine layout type
        if layout_info['columns'] > 1:
            layout_info['layout_type'] = 'multi-column'
        elif layout_info['has_sidebars']:
            layout_info['layout_type'] = 'sidebar'
        else:
            layout_info['layout_type'] = 'single-column'
        
        return layout_info
    
    def _detect_columns(self, doc: fitz.Document) -> int:
        """Detect number of columns in document"""
        column_counts = []
        
        # Check a sample of pages
        pages_to_check = min(5, len(doc))
        
        for i in range(pages_to_check):
            page = doc[i]
            blocks = page.get_text("blocks")
            
            if len(blocks) < 3:  # Too few blocks
                continue
            
            # Get x-coordinates of blocks
            x_coords = []
            for block in blocks:
                if len(block) >= 5:  # Has bbox
                    x_coords.append(block[0])  # Left edge
            
            if x_coords:
                # Cluster x-coordinates
                columns = self._cluster_coordinates(x_coords)
                column_counts.append(len(columns))
        
        # Return most common column count
        if column_counts:
            return Counter(column_counts).most_common(1)[0][0]
        return 1
    
    def _cluster_coordinates(self, coords: List[float]) -> List[List[float]]:
        """Cluster coordinates to detect columns"""
        if not coords:
            return []
        
        sorted_coords = sorted(coords)
        clusters = [[sorted_coords[0]]]
        
        for coord in sorted_coords[1:]:
            # Check if close to existing cluster
            added = False
            for cluster in clusters:
                if abs(coord - cluster[-1]) < self.column_threshold:
                    cluster.append(coord)
                    added = True
                    break
            
            if not added:
                clusters.append([coord])
        
        # Filter out small clusters
        return [c for c in clusters if len(c) > 2]
    
    def _analyze_margins(self, doc: fitz.Document) -> Dict[str, float]:
        """Analyze page margins"""
        margins = {'top': [], 'bottom': [], 'left': [], 'right': []}
        
        for page in doc[:min(5, len(doc))]:
            rect = page.rect
            blocks = page.get_text("blocks")
            
            if not blocks:
                continue
            
            # Find extremes
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')
            
            for block in blocks:
                if len(block) >= 5:
                    bbox = block[:4]
                    min_x = min(min_x, bbox[0])
                    min_y = min(min_y, bbox[1])
                    max_x = max(max_x, bbox[2])
                    max_y = max(max_y, bbox[3])
            
            # Calculate margins
            if min_x != float('inf'):
                margins['left'].append(min_x)
                margins['right'].append(rect.width - max_x)
                margins['top'].append(min_y)
                margins['bottom'].append(rect.height - max_y)
        
        # Average margins
        result = {}
        for side, values in margins.items():
            if values:
                result[side] = sum(values) / len(values)
            else:
                result[side] = 0
        
        return result
    
    def _detect_orientation(self, doc: fitz.Document) -> str:
        """Detect page orientation"""
        orientations = []
        
        for page in doc:
            rect = page.rect
            if rect.width > rect.height:
                orientations.append('landscape')
            else:
                orientations.append('portrait')
        
        # Return most common
        return Counter(orientations).most_common(1)[0][0]
    
    def _detect_headers(self, doc: fitz.Document) -> bool:
        """Detect if document has headers"""
        header_texts = []
        
        # Check first few pages
        for i in range(min(5, len(doc))):
            page = doc[i]
            blocks = page.get_text("blocks")
            
            # Look at top 10% of page
            page_height = page.rect.height
            header_threshold = page_height * 0.1
            
            for block in blocks:
                if len(block) >= 5:
                    if block[1] < header_threshold:  # y-coordinate
                        header_texts.append(block[4])
        
        # Check for repeated headers
        if len(header_texts) > 2:
            # Check if headers repeat
            header_counter = Counter(header_texts)
            most_common = header_counter.most_common(1)[0]
            return most_common[1] > 1  # Appears more than once
        
        return False
    
    def _detect_footers(self, doc: fitz.Document) -> bool:
        """Detect if document has footers"""
        footer_texts = []
        
        # Check first few pages
        for i in range(min(5, len(doc))):
            page = doc[i]
            blocks = page.get_text("blocks")
            
            # Look at bottom 10% of page
            page_height = page.rect.height
            footer_threshold = page_height * 0.9
            
            for block in blocks:
                if len(block) >= 5:
                    if block[1] > footer_threshold:  # y-coordinate
                        footer_texts.append(block[4])
        
        # Check for page numbers or repeated footers
        has_page_numbers = any(str(i) in text for i, text in enumerate(footer_texts, 1))
        
        if has_page_numbers:
            return True
        
        # Check for repeated footers
        if len(footer_texts) > 2:
            footer_counter = Counter(footer_texts)
            most_common = footer_counter.most_common(1)[0]
            return most_common[1] > 1
        
        return False
    
    def _detect_sidebars(self, doc: fitz.Document) -> bool:
        """Detect if document has sidebars"""
        for page in doc[:min(5, len(doc))]:
            blocks = page.get_text("blocks")
            page_width = page.rect.width
            
            # Count blocks in left and right margins
            left_margin_blocks = 0
            right_margin_blocks = 0
            
            margin_width = page_width * 0.25  # 25% of page width
            
            for block in blocks:
                if len(block) >= 5:
                    bbox = block[:4]
                    block_width = bbox[2] - bbox[0]
                    
                    # Check if narrow block in margin area
                    if block_width < margin_width:
                        if bbox[0] < margin_width:
                            left_margin_blocks += 1
                        elif bbox[2] > page_width - margin_width:
                            right_margin_blocks += 1
            
            # If consistent narrow blocks in margins
            if left_margin_blocks > 3 or right_margin_blocks > 3:
                return True
        
        return False