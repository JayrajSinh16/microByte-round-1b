# src/outline_extraction/extractors/native_extractor.py
import fitz  # PyMuPDF
import logging
from typing import List, Dict, Any
from collections import defaultdict

from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)

class NativeExtractor(BaseExtractor):
    """Extract text from native PDF using PyMuPDF"""
    
    def __init__(self):
        self.min_text_length = 1
        self.merge_threshold = 5  # pixels
    
    def extract(self, pdf_path: str, **kwargs) -> List[Dict[str, Any]]:
        """Extract text blocks from PDF"""
        try:
            doc = fitz.open(pdf_path)
            blocks = []
            block_id = 0
            
            for page_num, page in enumerate(doc):
                page_blocks = self._extract_page_blocks(page, page_num + 1)
                
                for block in page_blocks:
                    block['id'] = block_id
                    block['source'] = 'native'
                    blocks.append(block)
                    block_id += 1
            
            doc.close()
            
            # Merge nearby blocks
            blocks = self._merge_nearby_blocks(blocks)
            
            return blocks
            
        except Exception as e:
            logger.error(f"Native extraction failed: {str(e)}")
            return []
    
    def can_handle(self, pdf_path: str) -> bool:
        """Check if this extractor can handle the PDF"""
        try:
            doc = fitz.open(pdf_path)
            can_extract = doc.is_pdf and not doc.is_encrypted
            doc.close()
            return can_extract
        except:
            return False
    
    def _extract_page_blocks(self, page: fitz.Page, page_num: int) -> List[Dict]:
        """Extract blocks from a single page"""
        blocks = []
        
        # Get detailed text information
        text_dict = page.get_text("dict")
        
        for block in text_dict["blocks"]:
            if "lines" not in block:
                continue
            
            block_info = self._process_block(block, page_num)
            if block_info and len(block_info['text']) >= self.min_text_length:
                blocks.append(block_info)
        
        return blocks
    
    def _process_block(self, block: Dict, page_num: int) -> Dict:
        """Process a single block"""
        text = ""
        fonts = []
        sizes = []
        flags = []
        
        for line in block.get("lines", []):
            line_text = ""
            for span in line.get("spans", []):
                span_text = span.get("text", "")
                line_text += span_text
                
                if span_text.strip():
                    fonts.append(span.get("font", ""))
                    sizes.append(span.get("size", 0))
                    flags.append(span.get("flags", 0))
            
            text += line_text
        
        if not text.strip():
            return None
        
        # Calculate average font properties
        avg_size = sum(sizes) / len(sizes) if sizes else 0
        is_bold = any(flag & 2**4 for flag in flags) if flags else False
        is_italic = any(flag & 2**1 for flag in flags) if flags else False
        
        # Get most common font
        font = max(set(fonts), key=fonts.count) if fonts else ""
        
        # Ensure bbox is a list (mutable) not a tuple
        bbox = list(block.get("bbox", [0, 0, 0, 0]))
        
        return {
            'text': text.strip(),
            'page': page_num,
            'bbox': bbox,
            'x': bbox[0],
            'y': bbox[1],
            'width': bbox[2] - bbox[0],
            'height': bbox[3] - bbox[1],
            'font': font,
            'font_size': avg_size,
            'is_bold': is_bold,
            'is_italic': is_italic,
            'line_count': len(block.get("lines", [])),
            'char_count': len(text.strip())
        }
    
    def _merge_nearby_blocks(self, blocks: List[Dict]) -> List[Dict]:
        """Merge blocks that are very close to each other"""
        if not blocks:
            return blocks
        
        # Sort blocks by page and vertical position
        blocks.sort(key=lambda b: (b['page'], b['y']))
        
        merged = []
        current = blocks[0]
        
        for block in blocks[1:]:
            if (block['page'] == current['page'] and 
                abs(block['y'] - (current['y'] + current['height'])) < self.merge_threshold and
                abs(block['x'] - current['x']) < 50):  # Similar horizontal position
                
                # Merge blocks
                current['text'] += ' ' + block['text']
                current['height'] = block['y'] + block['height'] - current['y']
                # Ensure bbox is mutable list before assignment
                if isinstance(current['bbox'], tuple):
                    current['bbox'] = list(current['bbox'])
                current['bbox'][3] = block['bbox'][3]
                current['line_count'] += block['line_count']
                current['char_count'] = len(current['text'])
            else:
                merged.append(current)
                current = block
        
        merged.append(current)
        
        # Re-assign IDs
        for i, block in enumerate(merged):
            block['id'] = i
        
        return merged