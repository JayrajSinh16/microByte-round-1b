# src/content_extraction/text_cleaner.py
import re
import unicodedata
from typing import List, Optional

class TextCleaner:
    """Clean and normalize extracted text"""
    
    def __init__(self):
        self.min_line_length = 3
        self.max_blank_lines = 2
    
    def clean(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        
        # Normalize unicode
        text = self._normalize_unicode(text)
        
        # Fix common OCR issues
        text = self._fix_ocr_issues(text)
        
        # Remove excessive whitespace
        text = self._clean_whitespace(text)
        
        # Fix line breaks
        text = self._fix_line_breaks(text)
        
        # Remove page artifacts
        text = self._remove_artifacts(text)
        
        # Final cleanup
        text = self._final_cleanup(text)
        
        return text.strip()
    
    def _normalize_unicode(self, text: str) -> str:
        """Normalize unicode characters"""
        # Normalize to NFKC form
        text = unicodedata.normalize('NFKC', text)
        
        # Replace common problematic characters
        replacements = {
            '\u2019': "'",  # Right single quote
            '\u2018': "'",  # Left single quote
            '\u201c': '"',  # Left double quote
            '\u201d': '"',  # Right double quote
            '\u2013': '-',  # En dash
            '\u2014': '--', # Em dash
            '\u2026': '...', # Ellipsis
            '\u00a0': ' ',  # Non-breaking space
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _fix_ocr_issues(self, text: str) -> str:
        """Fix common OCR recognition issues"""
        # Fix common OCR mistakes
        ocr_fixes = {
            r'\bl\s+l\b': 'll',  # l l -> ll
            r'\brn\b': 'm',      # rn -> m
            r'\bI\s+I\b': 'II',  # I I -> II
            r'\s+,': ',',        # Remove space before comma
            r'\s+\.': '.',       # Remove space before period
            r'\(\s+': '(',       # Remove space after (
            r'\s+\)': ')',       # Remove space before )
        }
        
        for pattern, replacement in ocr_fixes.items():
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def _clean_whitespace(self, text: str) -> str:
        """Clean excessive whitespace"""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with max allowed
        text = re.sub(r'\n{3,}', '\n' * self.max_blank_lines, text)
        
        # Remove spaces at line beginnings/ends
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)
        
        return text
    
    def _fix_line_breaks(self, text: str) -> str:
        """Fix line breaks within paragraphs"""
        lines = text.split('\n')
        fixed_lines = []
        current_paragraph = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Empty line indicates paragraph break
            if not line:
                if current_paragraph:
                    fixed_lines.append(' '.join(current_paragraph))
                    current_paragraph = []
                fixed_lines.append('')
                continue
            
            # Check if line is continuation of previous
            if current_paragraph and self._is_continuation(current_paragraph[-1], line):
                current_paragraph.append(line)
            else:
                # Start new paragraph
                if current_paragraph:
                    fixed_lines.append(' '.join(current_paragraph))
                current_paragraph = [line]
        
        # Don't forget last paragraph
        if current_paragraph:
            fixed_lines.append(' '.join(current_paragraph))
        
        return '\n'.join(fixed_lines)
    
    def _is_continuation(self, prev_line: str, current_line: str) -> bool:
        """Check if current line continues previous line"""
        # Previous line doesn't end with sentence terminator
        if not prev_line or prev_line[-1] not in '.!?:;':
            # Current line doesn't start with capital (unless it's a name/acronym)
            if current_line and current_line[0].islower():
                return True
            
            # Check if previous line ends with hyphen
            if prev_line.endswith('-'):
                return True
        
        return False
    
    def _remove_artifacts(self, text: str) -> str:
        """Remove common page artifacts"""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip page numbers
            if re.match(r'^\d+$', line.strip()):
                continue
            
            # Skip headers/footers (often repeated)
            if len(line) < 50 and any(
                marker in line.lower() 
                for marker in ['page', 'copyright', '©', 'all rights reserved']
            ):
                continue
            
            # Skip lines that are just punctuation/symbols
            if re.match(r'^[^\w\s]+$', line.strip()):
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup pass"""
        # Ensure sentences are properly spaced
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
        
        # Remove any remaining excessive whitespace
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text