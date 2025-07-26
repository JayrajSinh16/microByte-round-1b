# src/utils/text/normalizer.py
import re
import unicodedata
from typing import Dict

class Normalizer:
    """Text normalization utilities"""
    
    def __init__(self):
        self.replacements = {
            '\u2019': "'",  # Right single quote
            '\u2018': "'",  # Left single quote
            '\u201c': '"',  # Left double quote
            '\u201d': '"',  # Right double quote
            '\u2013': '-',  # En dash
            '\u2014': '--', # Em dash
            '\u2026': '...', # Ellipsis
            '\u00a0': ' ',  # Non-breaking space
        }
    
    def normalize(self, text: str) -> str:
        """Normalize text"""
        if not text:
            return text
        
        # Unicode normalization
        text = unicodedata.normalize('NFKC', text)
        
        # Replace special characters
        for old, new in self.replacements.items():
            text = text.replace(old, new)
        
        # Remove control characters
        text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C' or ch in '\n\t')
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def remove_accents(self, text: str) -> str:
        """Remove accents from text"""
        # Decompose and filter
        nfd_form = unicodedata.normalize('NFD', text)
        return ''.join(ch for ch in nfd_form if unicodedata.category(ch) != 'Mn')
    
    def normalize_numbers(self, text: str) -> str:
        """Normalize number representations"""
        # Convert spelled-out numbers to digits (simple cases)
        number_map = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3',
            'four': '4', 'five': '5', 'six': '6', 'seven': '7',
            'eight': '8', 'nine': '9', 'ten': '10'
        }
        
        for word, digit in number_map.items():
            text = re.sub(r'\b' + word + r'\b', digit, text, flags=re.I)
        
        return text