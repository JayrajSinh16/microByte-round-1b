# src/outline_extraction/builders/outline_builder.py
import re
import logging
from typing import List, Dict, Any, Optional

from .hierarchy_validator import HierarchyValidator

logger = logging.getLogger(__name__)

class OutlineBuilder:
    """Build final document outline"""
    
    def __init__(self):
        self.validator = HierarchyValidator()
    
    def build(self, blocks: List[Dict], 
             heading_predictions: List[Dict],
             title_info: Optional[Dict] = None,
             toc_info: Optional[Dict] = None) -> Dict[str, Any]:
        """Build complete document outline"""
        
        # Extract headings from predictions
        headings = []
        
        for pred in heading_predictions:
            if pred.get('is_heading', False):
                # Find corresponding block
                block = next((b for b in blocks if b['id'] == pred['block_id']), None)
                
                if block:
                    # Use overridden text from prediction if available (for clean extracted text)
                    heading_text = pred.get('text', block['text'].strip())
                    
                    # Keep headings clean - no content collection
                    # This works for any document type (academic, business, technical, etc.)
                    
                    heading = {
                        'level': pred.get('level', 'H2'),
                        'text': heading_text,
                        'page': block.get('page', 1),
                        'confidence': pred.get('confidence', 0.0),
                        'block_id': block['id'],
                        'font_size': block.get('font_size', 0),
                        'position': {
                            'x': block.get('x', 0),
                            'y': block.get('y', 0)
                        }
                    }
                    headings.append(heading)
        
        # Sort by page and position
        headings.sort(key=lambda h: (h['page'], h['position']['y']))
        
        # Validate and fix hierarchy
        headings = self.validator.validate_and_fix(headings)
        
        # Determine title  
        if title_info:
            title = title_info['text']
        else:
            # Generic title for any document type
            title = "Document Outline"
        
        # Build outline structure
        outline = {
            'title': title,
            'outline': self._format_outline(headings),
            'metadata': {
                'total_headings': len(headings),
                'has_toc': toc_info is not None,
                'confidence_stats': self._calculate_confidence_stats(headings)
            }
        }
        
        # Add TOC information if available
        if toc_info:
            outline['toc'] = toc_info
        
        return outline
    
    def _format_outline(self, headings: List[Dict]) -> List[Dict]:
        """Format headings for output"""
        formatted = []
        
        for heading in headings:
            formatted.append({
                'level': heading['level'],
                'text': heading['text'],
                'page': heading['page']
            })
        
        return formatted
    
    def _calculate_confidence_stats(self, headings: List[Dict]) -> Dict:
        """Calculate confidence statistics for any document type"""
        if not headings:
            return {
                'mean': 0.0,
                'min': 0.0,
                'max': 0.0
            }
        
        confidences = [h['confidence'] for h in headings]
        
        return {
            'mean': round(sum(confidences) / len(confidences), 3),
            'min': round(min(confidences), 3),
            'max': round(max(confidences), 3)
        }