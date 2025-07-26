# src/utils/text/tokenizer.py
import re
from typing import List, Set
import nltk

class Tokenizer:
    """Text tokenization utilities"""
    
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for',
            'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on',
            'that', 'the', 'to', 'was', 'will', 'with', 'the', 'this'
        }
    
    def tokenize(self, text: str, lowercase: bool = True, 
                remove_stop_words: bool = False) -> List[str]:
        """Tokenize text into words"""
        if not text:
            return []
        
        # Use NLTK word tokenizer
        tokens = nltk.word_tokenize(text)
        
        # Lowercase if requested
        if lowercase:
            tokens = [t.lower() for t in tokens]
        
        # Remove punctuation-only tokens
        tokens = [t for t in tokens if re.search(r'\w', t)]
        
        # Remove stop words if requested
        if remove_stop_words:
            tokens = [t for t in tokens if t not in self.stop_words]
        
        return tokens
    
    def tokenize_sentences(self, text: str) -> List[str]:
        """Tokenize text into sentences"""
        if not text:
            return []
        
        # Use NLTK sentence tokenizer
        sentences = nltk.sent_tokenize(text)
        
        # Clean sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def get_ngrams(self, tokens: List[str], n: int = 2) -> List[tuple]:
        """Get n-grams from tokens"""
        if len(tokens) < n:
            return []
        
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = tuple(tokens[i:i+n])
            ngrams.append(ngram)
        
        return ngrams