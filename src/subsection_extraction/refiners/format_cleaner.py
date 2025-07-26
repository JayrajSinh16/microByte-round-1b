# src/subsection_extraction/refiners/format_cleaner.py
import re
import unicodedata

class FormatCleaner:
    """Clean formatting issues in text"""
    
    def clean(self, text: str) -> str:
        """Clean formatting issues"""
        if not text:
            return text
        
        # Normalize unicode
        text = self._normalize_unicode(text)
        
        # Fix hyphenation
        text = self._fix_hyphenation(text)
        
        # Clean special characters
        text = self._clean_special_chars(text)
        
        # Fix list formatting
        text = self._fix_lists(text)
        
        # Clean whitespace
        text = self._clean_whitespace(text)
        
        return text
    
    def _normalize_unicode(self, text: str) -> str:
        """Normalize unicode characters"""
        # Normalize to NFKC
        text = unicodedata.normalize('NFKC', text)
        
        # Replace special quotes and dashes
        replacements = {
            '\u2018': "'",  # Left single quote
            '\u2019': "'",  # Right single quote
            '\u201c': '"',  # Left double quote
            '\u201d': '"',  # Right double quote
            '\u2013': '-',  # En dash
            '\u2014': '--', # Em dash
            '\u2026': '...', # Ellipsis
            '\u00a0': ' ',  # Non-breaking space
            '\u2022': '•',  # Bullet
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _fix_hyphenation(self, text: str) -> str:
        """Fix word hyphenation at line breaks"""
        # Fix hyphenated words at line breaks
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        
        return text
    
    def _clean_special_chars(self, text: str) -> str:
        """Clean special characters"""
        # Remove control characters
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\n\t')
        
        # Replace tabs with spaces
        text = text.replace('\t', ' ')
        
        return text
    
    def _fix_lists(self, text: str) -> str:
        """Fix list formatting"""
        # Standardize bullet points
        text = re.sub(r'^[\*\-\+]\s+', '• ', text, flags=re.MULTILINE)
        
        # Fix numbered lists
        text = re.sub(r'^(\d+)\.\s+', r'\1. ', text, flags=re.MULTILINE)
        
        # Fix lettered lists
        text = re.sub(r'^([a-z])\)\s+', r'\1) ', text, flags=re.MULTILINE)
        
        return text
    
    def _clean_whitespace(self, text: str) -> str:
        """Clean whitespace issues"""
        # Multiple spaces to single
        text = re.sub(r' +', ' ', text)
        
        # Clean line starts/ends
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        
        # Remove empty lines at start/end
        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()
        
        return '\n'.join(lines)