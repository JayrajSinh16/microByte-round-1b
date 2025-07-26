# src/outline_extraction/extractors/ocr_extractor.py
import cv2
import numpy as np
import pytesseract
import fitz
import logging
from typing import List, Dict, Any
from PIL import Image

from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)

class OCRExtractor(BaseExtractor):
    """Extract text using OCR for scanned PDFs"""
    
    def __init__(self):
        self.dpi = 300
        self.preprocessing = True
        self.lang = 'eng'
    
    def extract(self, pdf_path: str, **kwargs) -> List[Dict[str, Any]]:
        """Extract text blocks using OCR"""
        try:
            doc = fitz.open(pdf_path)
            blocks = []
            block_id = 0
            
            for page_num, page in enumerate(doc):
                # Convert page to image
                mat = fitz.Matrix(self.dpi/72, self.dpi/72)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Convert to numpy array
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # Preprocess if needed
                if self.preprocessing:
                    img = self._preprocess_image(img)
                
                # Extract text with layout information
                page_blocks = self._extract_with_layout(img, page_num + 1)
                
                for block in page_blocks:
                    block['id'] = block_id
                    block['source'] = 'ocr'
                    blocks.append(block)
                    block_id += 1
            
            doc.close()
            return blocks
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return []
    
    def can_handle(self, pdf_path: str) -> bool:
        """Check if OCR is needed"""
        try:
            doc = fitz.open(pdf_path)
            
            # Check first few pages for text
            pages_to_check = min(3, len(doc))
            total_text = 0
            
            for i in range(pages_to_check):
                text = doc[i].get_text().strip()
                total_text += len(text)
            
            doc.close()
            
            # If very little text, probably needs OCR
            return total_text < 100 * pages_to_check
            
        except:
            return False
    
    def _preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR"""
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.medianBlur(thresh, 3)
        
        # Deskew if needed
        angle = self._get_skew_angle(denoised)
        if abs(angle) > 0.5:
            denoised = self._rotate_image(denoised, angle)
        
        return denoised
    
    def _get_skew_angle(self, img: np.ndarray) -> float:
        """Detect skew angle"""
        edges = cv2.Canny(img, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
        
        if lines is not None:
            angles = []
            for rho, theta in lines[:, 0]:
                angle = (theta * 180 / np.pi) - 90
                if -45 <= angle <= 45:
                    angles.append(angle)
            
            if angles:
                return np.median(angles)
        
        return 0.0
    
    def _rotate_image(self, img: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by given angle"""
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h), 
                                flags=cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_REPLICATE)
        
        return rotated
    
# src/outline_extraction/extractors/ocr_extractor.py (continued)
    def _extract_with_layout(self, img: np.ndarray, page_num: int) -> List[Dict]:
        """Extract text with layout preservation"""
        # Get OCR data with bounding boxes
        data = pytesseract.image_to_data(img, lang=self.lang, 
                                        output_type=pytesseract.Output.DICT)
        
        blocks = []
        current_block = None
        
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            # Skip empty text
            if not data['text'][i].strip():
                continue
            
            # Check if this is a new block
            if data['block_num'][i] != (current_block['block_num'] if current_block else -1):
                # Save previous block
                if current_block and current_block['text'].strip():
                    blocks.append(current_block)
                
                # Start new block
                current_block = {
                    'text': data['text'][i],
                    'page': page_num,
                    'x': data['left'][i],
                    'y': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i],
                    'bbox': [data['left'][i], data['top'][i], 
                            data['left'][i] + data['width'][i], 
                            data['top'][i] + data['height'][i]],
                    'confidence': data['conf'][i],
                    'block_num': data['block_num'][i],
                    'font_size': self._estimate_font_size(data['height'][i]),
                    'is_bold': False,  # OCR doesn't provide this
                    'is_italic': False,
                    'line_count': 1,
                    'char_count': len(data['text'][i])
                }
            else:
                # Append to current block
                current_block['text'] += ' ' + data['text'][i]
                current_block['width'] = max(current_block['width'], 
                                            data['left'][i] + data['width'][i] - current_block['x'])
                current_block['height'] = max(current_block['height'],
                                            data['top'][i] + data['height'][i] - current_block['y'])
                current_block['bbox'][2] = max(current_block['bbox'][2], 
                                              data['left'][i] + data['width'][i])
                current_block['bbox'][3] = max(current_block['bbox'][3],
                                              data['top'][i] + data['height'][i])
                current_block['confidence'] = min(current_block['confidence'], data['conf'][i])
                current_block['char_count'] = len(current_block['text'])
        
        # Don't forget the last block
        if current_block and current_block['text'].strip():
            blocks.append(current_block)
        
        # Filter low confidence blocks
        blocks = [b for b in blocks if b['confidence'] > 30]
        
        return blocks
    
    def _estimate_font_size(self, height: int) -> float:
        """Estimate font size from text height in pixels"""
        # Rough estimation: height in pixels to points
        # Assuming 72 DPI for points, and we're at self.dpi
        return (height * 72) / self.dpi