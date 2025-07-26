# src/outline_extraction/profilers/ocr_detector.py
import fitz
import logging
from typing import List, Set

logger = logging.getLogger(__name__)

class OCRDetector:
    """Detect which pages need OCR"""
    
    def __init__(self):
        self.min_text_length = 50  # Minimum text per page
        self.readable_ratio_threshold = 0.7  # 70% readable characters
        self.font_info_threshold = 0.5  # 50% of text should have font info
    
    def detect_ocr_pages(self, doc: fitz.Document) -> List[int]:
        """Detect pages that need OCR"""
        ocr_pages = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            if self._needs_ocr(page):
                ocr_pages.append(page_num + 1)  # 1-indexed
        
        logger.info(f"Detected {len(ocr_pages)} pages needing OCR")
        return ocr_pages
    
    def _needs_ocr(self, page: fitz.Page) -> bool:
        """Check if a page needs OCR"""
        # Check 1: Text length
        text = page.get_text().strip()
        if len(text) < self.min_text_length:
            return True
        
        # Check 2: Readable character ratio
        readable_ratio = self._calculate_readable_ratio(text)
        if readable_ratio < self.readable_ratio_threshold:
            return True
        
        # Check 3: Font information availability
        font_info_ratio = self._check_font_info(page)
        if font_info_ratio < self.font_info_threshold:
            return True
        
        # Check 4: Image-only page
        if self._is_image_only_page(page):
            return True
        
        return False
    
    def _calculate_readable_ratio(self, text: str) -> float:
        """Calculate ratio of readable characters"""
        if not text:
            return 0.0
        
        readable = sum(1 for c in text if c.isprintable() or c.isspace())
        return readable / len(text)
    
    def _check_font_info(self, page: fitz.Page) -> float:
        """Check how much text has font information"""
        blocks = page.get_text("dict")["blocks"]
        
        total_chars = 0
        chars_with_font = 0
        
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span.get("text", "")
                        total_chars += len(text)    
                        # Check if has font info
                        if span.get("font") and span.get("size", 0) > 0:
                            chars_with_font += len(text)
        
        if total_chars == 0:
            return 0.0
        
        return chars_with_font / total_chars
    
    def _is_image_only_page(self, page: fitz.Page) -> bool:
        """Check if page contains only images"""
        # Get text content
        text = page.get_text().strip()
        
        # Get images
        images = page.get_images()
        
        # If has images but no text
        if images and len(text) < 10:
            return True
        
        # Check if page is mostly covered by images
        if images:
            page_area = page.rect.width * page.rect.height
            image_area = 0
            
            for img in images:
                try:
                    # Get image bbox
                    xref = img[0]
                    img_dict = page.parent.extract_image(xref)
                    if img_dict:
                        # Estimate image area (this is approximate)
                        image_area += img_dict.get("width", 0) * img_dict.get("height", 0)
                except:
                    pass
            
            # If images cover most of the page
            if page_area > 0 and image_area / page_area > 0.8:
                return True
        
        return False