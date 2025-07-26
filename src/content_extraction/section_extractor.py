# src/content_extraction/section_extractor.py
import fitz
import logging
from typing import List, Dict, Tuple, Optional

from .boundary_detector import BoundaryDetector

logger = logging.getLogger(__name__)

class SectionExtractor:
    """Extract section content from PDFs"""
    
    def __init__(self):
        self.boundary_detector = BoundaryDetector()
    
    def extract(self, pdf_path: str, outline: Dict) -> List[Dict]:
        """Extract content for each section in the outline"""
        try:
            doc = fitz.open(pdf_path)
            sections = []
            
            outline_entries = outline.get('outline', [])
            
            for i, entry in enumerate(outline_entries):
                # Determine section boundaries
                start_page = entry['page'] - 1  # Convert to 0-indexed
                
                # Find end boundary
                if i < len(outline_entries) - 1:
                    end_page = outline_entries[i + 1]['page'] - 1
                else:
                    end_page = len(doc) - 1
                
                # Extract section content
                section_content = self._extract_section_content(
                    doc, entry, start_page, end_page
                )
                
                sections.append({
                    'title': entry['text'],
                    'level': entry['level'],
                    'page': entry['page'],
                    'content': section_content,
                    'document': pdf_path.split('/')[-1]
                })
            
            doc.close()
            return sections
            
        except Exception as e:
            logger.error(f"Failed to extract sections: {str(e)}")
            return []
    
    def _extract_section_content(self, doc: fitz.Document, 
                               heading: Dict, 
                               start_page: int, 
                               end_page: int) -> str:
        """Extract content for a single section"""
        content_parts = []
        
        for page_num in range(start_page, end_page + 1):
            page = doc[page_num]
            
            # Get page text
            page_text = page.get_text()
            
            if page_num == start_page:
                # Find where the heading ends and content begins
                start_pos = self._find_content_start(page_text, heading['text'])
                page_text = page_text[start_pos:]
            
            if page_num == end_page and page_num != start_page:
                # Find where the next section begins
                end_pos = self._find_content_end(page_text, doc, page_num)
                page_text = page_text[:end_pos]
            
            content_parts.append(page_text)
        
        return '\n\n'.join(content_parts)
    
    def _find_content_start(self, page_text: str, heading_text: str) -> int:
        """Find where content starts after heading"""
        # Try to find the heading in the text
        heading_pos = page_text.find(heading_text)
        
        if heading_pos != -1:
            # Start after the heading
            return heading_pos + len(heading_text)
        
        # If heading not found, start from beginning
        return 0
    
    def _find_content_end(self, page_text: str, doc: fitz.Document, page_num: int) -> int:
        """Find where content ends (before next section)"""
        # Look for common section indicators
        lines = page_text.split('\n')
        
        for i, line in enumerate(lines):
            # Check if line looks like a heading
            if self._is_likely_heading(line):
                # Return position where this line starts
                return len('\n'.join(lines[:i]))
        
        # No heading found, return full text
        return len(page_text)
    
    def _is_likely_heading(self, text: str) -> bool:
        """Check if text is likely a heading"""
        text = text.strip()
        
        # Empty or too long
        if not text or len(text) > 200:
            return False
        
        # Common heading patterns
        import re
        patterns = [
            r'^\d+\.?\s+',  # Numbered
            r'^Chapter\s+\d+',  # Chapter
            r'^Section\s+\d+',  # Section
            r'^[IVX]+\.',  # Roman numerals
        ]
        
        for pattern in patterns:
            if re.match(pattern, text, re.I):
                return True
        
        # All caps and short
        if text.isupper() and len(text.split()) < 10:
            return True
        
        return False