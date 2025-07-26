# src/subsection_extraction/refiners/noise_remover.py
import re
from typing import List, Set

class NoiseRemover:
    """Remove noise from extracted text"""
    
    def __init__(self):
        self.noise_patterns = [
            # Headers/footers
            r'^\s*Page\s+\d+\s*$',
            r'^\s*\d+\s*$',  # Just page numbers
            
            # Copyright
            r'©.*?\d{4}',
            r'All rights reserved',
            
            # Repeated characters
            r'[-=_]{3,}',
            r'[*]{3,}',
            
            # URLs (optional - might want to keep)
            # r'https?://\S+',
            
            # Email addresses (optional)
            # r'\S+@\S+\.\S+',
        ]
        
        self.noise_phrases = {
            'table of contents',
            'list of figures',
            'list of tables',
            'this page intentionally left blank',
            'continued on next page',
            'see figure',
            'see table'
        }
    
    def remove_noise(self, text: str) -> str:
        """Remove various types of noise from text"""
        if not text:
            return text
        
        # Remove by patterns
        for pattern in self.noise_patterns:
            text = re.sub(pattern, '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Remove lines containing noise phrases
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Skip if contains noise phrase
            if any(phrase in line_lower for phrase in self.noise_phrases):
                continue
            
            # Skip very short lines (likely artifacts)
            if len(line.strip()) < 3:
                continue
            
            cleaned_lines.append(line)
        
        # Rejoin
        text = '\n'.join(cleaned_lines)
        
        # Remove excessive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()