# src/outline_extraction/strategies/pattern_strategy.py
import re
from typing import List, Dict
from collections import defaultdict

from .base_strategy import BaseStrategy
from config.patterns import HEADING_PATTERNS

class PatternStrategy(BaseStrategy):
    """Pattern-based heading detection"""
    
    def __init__(self):
        self.patterns = HEADING_PATTERNS
        self.pattern_scores = {
            'numbered': 0.8,
            'lettered': 0.7,
            'named': 0.9,
            'academic': 0.85,
            'business': 0.8
        }
    
    def detect(self, blocks: List[Dict], profile: Dict) -> List[Dict]:
        """Detect headings based on text patterns"""
        predictions = []
        doc_type = profile.get('type', 'general')
        
        for block in blocks:
            prediction = {
                'block_id': block['id'],
                'is_heading': False,
                'level': None,
                'confidence': 0.0
            }
            
            text = block.get('text', '').strip()
            if not text:
                predictions.append(prediction)
                continue
            
            # Check patterns
            pattern_matches = self._check_patterns(text, doc_type)
            
            if pattern_matches:
                prediction['is_heading'] = True
                prediction['level'] = self._determine_level(text, pattern_matches)
                prediction['confidence'] = self._calculate_confidence(
                    pattern_matches, block, doc_type
                )
            
            predictions.append(prediction)
        
        return predictions
    
    def _check_patterns(self, text: str, doc_type: str) -> Dict[str, bool]:
        """Check which patterns match the text"""
        matches = defaultdict(bool)
        
        # Check general patterns
        for pattern_type, patterns in self.patterns.items():
            if pattern_type == doc_type or pattern_type in ['numbered', 'lettered', 'named']:
                for pattern in patterns:
                    if pattern.match(text):
                        matches[pattern_type] = True
                        break
        
        return dict(matches)
    
    def _determine_level(self, text: str, pattern_matches: Dict) -> str:
        """Determine heading level based on pattern"""
        # Numbered patterns with depth
        if pattern_matches.get('numbered'):
            # Count dots to determine level
            match = re.match(r'^(\d+(?:\.\d+)*)', text)
            if match:
                number = match.group(1)
                dots = number.count('.')
                
                if dots == 0:
                    return 'H1'
                elif dots == 1:
                    return 'H2'
                else:
                    return 'H3'
        
        # Named patterns (Chapter, Section, etc.)
        if pattern_matches.get('named'):
            if re.match(r'^Chapter', text, re.I):
                return 'H1'
            elif re.match(r'^Section', text, re.I):
                return 'H2'
            elif re.match(r'^Part', text, re.I):
                return 'H1'
        
        # Academic patterns
        if pattern_matches.get('academic'):
            # Major sections are H1
            major_sections = ['abstract', 'introduction', 'methodology', 
                            'results', 'discussion', 'conclusion', 'references']
            
            if any(section in text.lower() for section in major_sections):
                return 'H1'
        
        # Default based on other factors
        return self._infer_level_from_context(text)
    
    def _infer_level_from_context(self, text: str) -> str:
        """Infer level from text characteristics"""
        # Length-based inference
        words = text.split()
        if len(words) <= 3:
            return 'H1'
        elif len(words) <= 7:
            return 'H2'
        else:
            return 'H3'
    
    def _calculate_confidence(self, pattern_matches: Dict, 
                            block: Dict, doc_type: str) -> float:
        """Calculate confidence score"""
        confidence = 0.0
        
        # Base score from pattern matches
        for pattern_type, matched in pattern_matches.items():
            if matched:
                confidence += self.pattern_scores.get(pattern_type, 0.5)
        
        # Normalize to max 0.6 from patterns
        confidence = min(confidence, 0.6)
        
        # Bonus for document type match
        if doc_type in pattern_matches:
            confidence += 0.2
        
        # Bonus for formatting
        if block.get('is_bold', False):
            confidence += 0.1
        
        # Bonus for appropriate length
        text_length = len(block.get('text', ''))
        if 5 <= text_length <= 100:
            confidence += 0.1
        
        return min(confidence, 1.0)