# src/subsection_extraction/refiners/text_refiner.py
import re
from typing import List

class TextRefiner:
    """Refine extracted text for presentation"""
    
    def refine(self, text: str) -> str:
        """Refine text for final output"""
        if not text:
            return ""
        
        # Ensure complete sentences
        text = self._ensure_complete_sentences(text)
        
        # Fix spacing
        text = self._fix_spacing(text)
        
        # Improve readability
        text = self._improve_readability(text)
        
        # src/subsection_extraction/refiners/text_refiner.py (continued)
        # Capitalize first letter
        text = self._capitalize_first(text)
        
        # Trim to reasonable length
        text = self._trim_text(text)
        
        return text.strip()
    
    def _ensure_complete_sentences(self, text: str) -> str:
        """Ensure text starts and ends with complete sentences"""
        if not text:
            return text
        
        # Check if starts mid-sentence (lowercase first letter after removing quotes)
        clean_start = text.lstrip('"\'')
        if clean_start and clean_start[0].islower():
            # Find first sentence start
            match = re.search(r'[.!?]\s+[A-Z]', text)
            if match:
                text = text[match.start() + 2:]
        
        # Check if ends mid-sentence
        if text and text[-1] not in '.!?':
            # Find last complete sentence
            matches = list(re.finditer(r'[.!?](?=\s|$)', text))
            if matches:
                last_match = matches[-1]
                text = text[:last_match.end()]
        
        return text
    
    def _fix_spacing(self, text: str) -> str:
        """Fix spacing issues"""
        # Multiple spaces to single
        text = re.sub(r' +', ' ', text)
        
        # Fix space before punctuation
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        
        # Fix space after punctuation
        text = re.sub(r'([,.!?;:])([A-Za-z])', r'\1 \2', text)
        
        # Fix quotes
        text = re.sub(r'\s+"', '"', text)
        text = re.sub(r'"\s+', '"', text)
        
        return text
    
    def _improve_readability(self, text: str) -> str:
        """Improve text readability"""
        # Expand common abbreviations
        abbreviations = {
            'e.g.': 'for example',
            'i.e.': 'that is',
            'etc.': 'and so on',
            'vs.': 'versus',
            'Fig.': 'Figure',
            'Eq.': 'Equation'
        }
        
        for abbr, full in abbreviations.items():
            text = text.replace(abbr, full)
        
        # Remove reference markers like [1], [2]
        text = re.sub(r'$$\d+$$', '', text)
        
        # Remove citation markers like (Smith, 2020)
        text = re.sub(r'$[A-Z][a-z]+(?:\s+et\s+al\.)?,\s*\d{4}$', '', text)
        
        return text
    
    def _capitalize_first(self, text: str) -> str:
        """Ensure first letter is capitalized"""
        if text:
            return text[0].upper() + text[1:]
        return text
    
    def _trim_text(self, text: str) -> str:
        """Trim text to reasonable length"""
        max_length = 1000  # characters
        
        if len(text) <= max_length:
            return text
        
        # Find sentence boundary near max_length
        sentences = re.split(r'(?<=[.!?])\s+', text[:max_length + 100])
        
        trimmed = ""
        for sentence in sentences:
            if len(trimmed) + len(sentence) <= max_length:
                trimmed += sentence + " "
            else:
                break
        
        return trimmed.strip()