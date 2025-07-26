# src/utils/io/pdf_handler.py
import fitz
from pathlib import Path
from typing import Union, Dict, Any
import logging

logger = logging.getLogger(__name__)

class PDFHandler:
    """Handle PDF file operations"""
    
    @staticmethod
    def get_pdf_info(pdf_path: Union[str, Path]) -> Dict[str, Any]:
        """Get PDF metadata and info"""
        try:
            doc = fitz.open(pdf_path)
            
            info = {
                'path': str(pdf_path),
                'page_count': len(doc),
                'metadata': doc.metadata,
                'is_encrypted': doc.is_encrypted,
                'is_pdf': doc.is_pdf,
                'has_text': PDFHandler._has_extractable_text(doc)
            }
            
            doc.close()
            return info
            
        except Exception as e:
            logger.error(f"Failed to get PDF info for {pdf_path}: {str(e)}")
            raise
    
    @staticmethod
    def _has_extractable_text(doc: fitz.Document) -> bool:
        """Check if PDF has extractable text"""
        # Check first few pages
        pages_to_check = min(3, len(doc))
        
        for i in range(pages_to_check):
            text = doc[i].get_text().strip()
            if len(text) > 50:  # Reasonable amount of text
                return True
        
        return False
    
    @staticmethod
    def extract_page_text(pdf_path: Union[str, Path], page_num: int) -> str:
        """Extract text from specific page"""
        try:
            doc = fitz.open(pdf_path)
            
            if page_num < 0 or page_num >= len(doc):
                raise ValueError(f"Invalid page number: {page_num}")
            
            text = doc[page_num].get_text()
            doc.close()
            
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract page {page_num} from {pdf_path}: {str(e)}")
            raise