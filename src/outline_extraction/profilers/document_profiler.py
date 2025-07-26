# src/outline_extraction/profilers/document_profiler.py
import fitz
import re
import logging
from typing import Dict, List, Any
from collections import Counter

from .layout_analyzer import LayoutAnalyzer
from .ocr_detector import OCRDetector

logger = logging.getLogger(__name__)

class DocumentProfiler:
    """Profile document to determine best extraction strategy"""
    
    def __init__(self):
        self.layout_analyzer = LayoutAnalyzer()
        self.ocr_detector = OCRDetector()
        
        self.type_indicators = {
            'academic': {
                'keywords': ['abstract', 'introduction', 'methodology', 'results', 
                           'discussion', 'conclusion', 'references', 'bibliography'],
                'patterns': [r'doi:\s*\S+', r'ISSN\s*\d{4}-\d{4}', r'Vol\.\s*\d+'],
                'weight': 1.0
            },
            'business': {
                'keywords': ['executive summary', 'financial', 'revenue', 'profit',
                           'growth', 'strategy', 'market', 'quarterly', 'annual report'],
                'patterns': [r'Q[1-4]\s+20\d{2}', r'\$[\d,]+(?:\.\d{2})?[MBK]?'],
                'weight': 1.0
            },
            'technical': {
                'keywords': ['specification', 'requirements', 'implementation', 
                           'architecture', 'design', 'api', 'documentation'],
                'patterns': [r'v\d+\.\d+', r'RFC\s*\d+'],
                'weight': 1.0
            },
            'book': {
                'keywords': ['chapter', 'contents', 'preface', 'epilogue', 
                           'appendix', 'glossary', 'index'],
                'patterns': [r'Chapter\s+\d+', r'ISBN[-\s]*([\d-]+)'],
                'weight': 1.0
            },
            'form': {
                'keywords': ['name:', 'date:', 'signature:', 'address:', 
                           'phone:', 'email:', 'field'],
                'patterns': [r'_{3,}', r'\[\s*\]', r'\(\s*\)'],
                'weight': 0.8
            }
        }
    
    def profile(self, pdf_path: str) -> Dict[str, Any]:
        """Create comprehensive document profile"""
        try:
            doc = fitz.open(pdf_path)
            
            profile = {
                'path': pdf_path,
                'page_count': len(doc),
                'type': self._detect_document_type(doc),
                'layout': self.layout_analyzer.analyze(doc),
                'ocr_pages': self.ocr_detector.detect_ocr_pages(doc),
                'metadata': self._extract_metadata(doc),
                'language': self._detect_language(doc),
                'formatting': self._analyze_formatting(doc),
                'has_toc': self._detect_toc(doc),
                'has_images': self._detect_images(doc),
                'text_density': self._calculate_text_density(doc)
            }
            
            doc.close()
            return profile
            
        except Exception as e:
            logger.error(f"Failed to profile document: {str(e)}")
            return {'error': str(e)}
    
    def _detect_document_type(self, doc: fitz.Document) -> str:
        """Detect the type of document"""
        # Sample text from first few pages
        sample_text = ""
        pages_to_check = min(5, len(doc))
        
        for i in range(pages_to_check):
            sample_text += doc[i].get_text().lower()
        
        if not sample_text:
            return 'unknown'
        
        # Score each type
        type_scores = {}
        
        for doc_type, indicators in self.type_indicators.items():
            score = 0.0
            
            # Check keywords
            for keyword in indicators['keywords']:
                if keyword in sample_text:
                    score += indicators['weight']
            
            # Check patterns
            for pattern in indicators['patterns']:
                if re.search(pattern, sample_text, re.I):
                    score += indicators['weight'] * 0.5
            
            type_scores[doc_type] = score
        
        # Return type with highest score
        if type_scores:
            best_type = max(type_scores, key=type_scores.get)
            if type_scores[best_type] > 0:
                return best_type
        
        return 'general'
    
    def _extract_metadata(self, doc: fitz.Document) -> Dict[str, str]:
        """Extract document metadata"""
        metadata = doc.metadata
        
        # Clean and standardize metadata
        cleaned = {}
        for key, value in metadata.items():
            if value and isinstance(value, str) and value.strip():
                cleaned[key.lower()] = value.strip()
        
        return cleaned
    
    def _detect_language(self, doc: fitz.Document) -> str:
        """Detect primary language of document"""
        # Simple language detection based on character sets
        sample_text = ""
        pages_to_check = min(3, len(doc))
        
        for i in range(pages_to_check):
            sample_text += doc[i].get_text()
        
        if not sample_text:
            return 'unknown'
        
        # Check for non-Latin scripts
        if re.search(r'[\u4e00-\u9fff]', sample_text):  # Chinese
            return 'chinese'
        elif re.search(r'[\u3040-\u309f\u30a0-\u30ff]', sample_text):  # Japanese
            return 'japanese'
        elif re.search(r'[\u0600-\u06ff]', sample_text):  # Arabic
            return 'arabic'
        elif re.search(r'[\u0400-\u04ff]', sample_text):  # Cyrillic
            return 'russian'
        
        # Default to English
        return 'english'
    
# src/outline_extraction/profilers/document_profiler.py (continued)
    def _analyze_formatting(self, doc: fitz.Document) -> Dict[str, Any]:
        """Analyze document formatting consistency"""
        font_sizes = []
        fonts = []
        line_heights = []
        
        pages_to_check = min(5, len(doc))
        
        for i in range(pages_to_check):
            page = doc[i]
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if span["text"].strip():
                                font_sizes.append(span["size"])
                                fonts.append(span["font"])
        
        return {
            'unique_fonts': len(set(fonts)),
            'unique_font_sizes': len(set(font_sizes)),
            'most_common_font': Counter(fonts).most_common(1)[0][0] if fonts else None,
            'most_common_size': Counter(font_sizes).most_common(1)[0][0] if font_sizes else None,
            'font_size_range': (min(font_sizes), max(font_sizes)) if font_sizes else (0, 0),
            'formatting_consistency': self._calculate_consistency(fonts, font_sizes)
        }
    
    def _calculate_consistency(self, fonts: List[str], sizes: List[float]) -> float:
        """Calculate formatting consistency score"""
        if not fonts or not sizes:
            return 0.0
        
        # Font consistency
        font_counts = Counter(fonts)
        most_common_font_ratio = font_counts.most_common(1)[0][1] / len(fonts)
        
        # Size consistency
        size_counts = Counter(sizes)
        most_common_size_ratio = size_counts.most_common(1)[0][1] / len(sizes)
        
        # Combined score
        return (most_common_font_ratio + most_common_size_ratio) / 2
    
    def _detect_toc(self, doc: fitz.Document) -> bool:
        """Detect if document has table of contents"""
        # Check first few pages
        pages_to_check = min(5, len(doc))
        
        toc_indicators = [
            r'table\s+of\s+contents',
            r'contents\s*\n',
            r'^\s*\d+\.\s+.+\s+\d+\s*$',  # Pattern like "1. Introduction ... 5"
            r'chapter\s+\d+.*page\s+\d+',
            r'\.{3,}\s*\d+\s*$'  # Dots followed by page number
        ]
        
        for i in range(pages_to_check):
            text = doc[i].get_text().lower()
            
            for pattern in toc_indicators:
                if re.search(pattern, text, re.I | re.M):
                    return True
        
        return False
    
    def _detect_images(self, doc: fitz.Document) -> bool:
        """Detect if document contains images"""
        for page in doc:
            image_list = page.get_images()
            if image_list:
                return True
        return False
    
    def _calculate_text_density(self, doc: fitz.Document) -> float:
        """Calculate average text density across pages"""
        densities = []
        
        for page in doc:
            rect = page.rect
            page_area = rect.width * rect.height
            
            # Get text blocks
            blocks = page.get_text("blocks")
            text_area = 0
            
            for block in blocks:
                if len(block) >= 5:  # block has bbox
                    bbox = block[:4]
                    text_area += (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            
            if page_area > 0:
                density = text_area / page_area
                densities.append(min(density, 1.0))  # Cap at 1.0
        
        return sum(densities) / len(densities) if densities else 0.0