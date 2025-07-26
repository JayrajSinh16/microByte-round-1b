# src/outline_extraction/strategies/semantic_strategy.py
import logging
from typing import List, Dict
import spacy
from collections import defaultdict

from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class SemanticStrategy(BaseStrategy):
    """Semantic analysis for heading detection"""
    
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            logger.warning("spaCy model not found, semantic strategy disabled")
            self.nlp = None
        
        self.heading_indicators = {
            'verbs': ['introduce', 'present', 'describe', 'analyze', 'discuss'],
            'nouns': ['introduction', 'overview', 'summary', 'analysis', 'conclusion'],
            'pos_patterns': [
                ['NOUN'],  # Single noun
                ['ADJ', 'NOUN'],  # Adjective + Noun
                ['NOUN', 'NOUN'],  # Compound noun
                ['VERB', 'NOUN'],  # Gerund + Noun
            ]
        }
    
    def detect(self, blocks: List[Dict], profile: Dict) -> List[Dict]:
        """Detect headings using semantic analysis"""
        predictions = []
        
        if self.nlp is None:
            # Return empty predictions if spaCy not available
            return [{
                'block_id': block['id'],
                'is_heading': False,
                'level': None,
                'confidence': 0.0
            } for block in blocks]
        
        for block in blocks:
            prediction = {
                'block_id': block['id'],
                'is_heading': False,
                'level': None,
                'confidence': 0.0
            }
            
            text = block.get('text', '').strip()
            if not text or len(text) > 200:  # Skip long texts
                predictions.append(prediction)
                continue
            
            # Analyze with spaCy
            doc = self.nlp(text)
            
            # Check semantic indicators
            semantic_score = self._calculate_semantic_score(doc, text)
            
            if semantic_score > 0.4:
                prediction['is_heading'] = True
                prediction['level'] = self._determine_semantic_level(doc, block)
                prediction['confidence'] = semantic_score
            
            predictions.append(prediction)
        
        return predictions
    
    def _calculate_semantic_score(self, doc, text: str) -> float:
        """Calculate semantic heading score"""
        score = 0.0
        
        # Check POS patterns
        pos_sequence = [token.pos_ for token in doc]
        for pattern in self.heading_indicators['pos_patterns']:
            if pos_sequence[:len(pattern)] == pattern:
                score += 0.3
                break
        
        # Check for heading indicator words
        text_lower = text.lower()
        
        # Check verbs
        for verb in self.heading_indicators['verbs']:
            if verb in text_lower:
                score += 0.2
                break
        
        # Check nouns
        for noun in self.heading_indicators['nouns']:
            if noun in text_lower:
                score += 0.2
                break
        
        # Check sentence structure
        if len(list(doc.sents)) == 1:  # Single sentence
            score += 0.1
        
        # Check for no ending punctuation (common in headings)
        if text and text[-1] not in '.!?,;':
            score += 0.1
        
        # Check for capitalization pattern
        if self._has_title_case(text):
            score += 0.1
        
        # Check entity types
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        if entities and any(label in ['ORG', 'PRODUCT', 'WORK_OF_ART'] for _, label in entities):
            score += 0.1
        
        # Penalize if too many function words
        function_words = sum(1 for token in doc if token.pos_ in ['DET', 'ADP', 'CONJ'])
        if len(doc) > 0 and function_words / len(doc) > 0.5:
            score -= 0.2
        
        return max(0.0, min(score, 1.0))
    
    def _determine_semantic_level(self, doc, block: Dict) -> str:
        """Determine heading level based on semantic analysis"""
        text = doc.text
        
        # Major section indicators
        major_sections = ['introduction', 'conclusion', 'abstract', 'summary',
                         'overview', 'background', 'methodology', 'results']
        
        if any(section in text.lower() for section in major_sections):
            return 'H1'
        
        # Check for subsection patterns
        if any(token.pos_ == 'NUM' for token in doc):
            return 'H2'
        
        # Named entities suggest importance
        if doc.ents:
            return 'H2'
        
        # Default based on length and complexity
        if len(doc) <= 3:
            return 'H1'
        elif len(doc) <= 7:
            return 'H2'
        else:
            return 'H3'
    
    def _has_title_case(self, text: str) -> bool:
        """Check if text follows title case pattern"""
        words = text.split()
        if not words:
            return False
        
        # Skip short words
        significant_words = [w for w in words if len(w) > 3]
        if not significant_words:
            return False
        
        # Check if most significant words are capitalized
        capitalized = sum(1 for w in significant_words if w[0].isupper())
        return capitalized / len(significant_words) > 0.7