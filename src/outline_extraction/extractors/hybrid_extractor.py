# src/outline_extraction/extractors/hybrid_extractor.py
import logging
from typing import List, Dict, Any

from .base_extractor import BaseExtractor
from .native_extractor import NativeExtractor
from .ocr_extractor import OCRExtractor

logger = logging.getLogger(__name__)

class HybridExtractor(BaseExtractor):
    """Hybrid extractor that combines native and OCR extraction"""
    
    def __init__(self):
        self.native_extractor = NativeExtractor()
        self.ocr_extractor = OCRExtractor()
        self.ocr_threshold = 0.3  # Use OCR if native extraction quality < 30%
    
    def extract(self, pdf_path: str, profile: Dict = None) -> List[Dict[str, Any]]:
        """Extract using best method based on document profile"""
        blocks = []
        
        # Try native extraction first
        native_blocks = self.native_extractor.extract(pdf_path)
        
        if profile and 'ocr_pages' in profile:
            # Handle mixed documents
            ocr_pages = set(profile['ocr_pages'])
            
            # Keep native blocks from non-OCR pages
            blocks = [b for b in native_blocks if b['page'] not in ocr_pages]
            
            # Extract OCR pages
            if ocr_pages:
                ocr_blocks = self.ocr_extractor.extract(pdf_path)
                ocr_blocks = [b for b in ocr_blocks if b['page'] in ocr_pages]
                blocks.extend(ocr_blocks)
        else:
            # Evaluate extraction quality
            quality = self._evaluate_extraction_quality(native_blocks)
            
            if quality < self.ocr_threshold:
                logger.info(f"Native extraction quality low ({quality:.2f}), using OCR")
                blocks = self.ocr_extractor.extract(pdf_path)
            else:
                blocks = native_blocks
        
        # Sort by page and position
        blocks.sort(key=lambda b: (b['page'], b['y'], b['x']))
        
        # Re-assign IDs
        for i, block in enumerate(blocks):
            block['id'] = i
        
        return blocks
    
    def can_handle(self, pdf_path: str) -> bool:
        """Hybrid extractor can handle any PDF"""
        return True
    
    def _evaluate_extraction_quality(self, blocks: List[Dict]) -> float:
        """Evaluate the quality of extracted blocks"""
        if not blocks:
            return 0.0
        
        quality_scores = []
        
        for block in blocks:
            score = 1.0
            text = block['text']
            
            # Check for garbage characters
            readable_chars = sum(1 for c in text if c.isprintable())
            if len(text) > 0:
                readable_ratio = readable_chars / len(text)
                score *= readable_ratio
            
            # Check for reasonable text length
            if len(text) < 3 or len(text) > 5000:
                score *= 0.5
            
            # Check for font information
            if block.get('font_size', 0) == 0:
                score *= 0.7
            
            # Check for very small or very large fonts
            font_size = block.get('font_size', 12)
            if font_size < 6 or font_size > 72:
                score *= 0.8
            
            quality_scores.append(score)
        
        return sum(quality_scores) / len(quality_scores)