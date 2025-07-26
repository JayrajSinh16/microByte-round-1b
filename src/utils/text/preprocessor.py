# src/utils/text/preprocessor.py
import re
from typing import List, Optional

class Preprocessor:
    """Text preprocessing utilities"""
    
    def __init__(self):
        self.email_pattern = re.compile(r'\S+@\S+\.\S+')
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+')
        self.phone_pattern = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
    
    def preprocess(self, text: str, 
                  remove_emails: bool = False,
                  remove_urls: bool = False,
                  remove_phone: bool = False,
                  remove_numbers: bool = False) -> str:
        """Preprocess text with various options"""
        if not text:
            return text
        
        # Remove emails
        if remove_emails:
            text = self.email_pattern.sub('[EMAIL]', text)
        
        # Remove URLs
        if remove_urls:
            text = self.url_pattern.sub('[URL]', text)
        
        # Remove phone numbers
        if remove_phone:
            text = self.phone_pattern.sub('[PHONE]', text)
        
        # Remove all numbers
        if remove_numbers:
            text = re.sub(r'\b\d+\b', '[NUM]', text)
        
        return text
    
    def clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Decode HTML entities
        import html
        text = html.unescape(text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def remove_citations(self, text: str) -> str:
        """Remove citation markers"""
        # Remove [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)

        # Remove (Author, Year)
        text = re.sub(r'\([A-Z][a-z]+(?:\s+et\s+al\.)?,\s*\d{4}\)', '', text)

        # Remove (Author et al., Year)
        text = re.sub(r'$[A-Z][a-z]+\s+et\s+al\.,\s*\d{4}$', '', text)
        
        return text