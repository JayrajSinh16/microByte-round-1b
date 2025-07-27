"""
Universal Outline Extraction Strategy

This strategy uses multiple signals to identify headings across all document types:
1. Typography hierarchy (font size, bold, spacing)
2. Text patterns and structure
3. Context analysis
4. Position and layout
"""

import re
import logging
from typing import List, Dict, Any, Tuple
from collections import defaultdict

from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class UniversalStrategy(BaseStrategy):
    """Universal strategy that works across all document types"""
    
    def __init__(self):
        self.confidence = 0.85
        
        # Heading indicators
        self.heading_patterns = [
            # Numbered sections
            r'^\d+\.?\s+[A-Z][a-zA-Z\s]+$',
            r'^Chapter\s+\d+',
            r'^Section\s+\d+',
            r'^Part\s+\d+',
            
            # Roman numerals
            r'^[IVX]+\.?\s+[A-Z][a-zA-Z\s]+$',
            
            # Lettered sections
            r'^[A-Z]\.?\s+[A-Z][a-zA-Z\s]+$',
            
            # Topic headings (title case, short)
            r'^[A-Z][a-zA-Z\s]{2,30}$',
            
            # Common document sections
            r'^(Introduction|Overview|Background|Methodology|Results|Discussion|Conclusion|Summary|References|Appendix)$',
            
            # Travel/guide specific
            r'^(Getting\s+There|Where\s+to\s+Stay|What\s+to\s+Do|Things\s+to\s+See|Activities|Attractions|Dining|Transportation|Tips|History|Culture).*$',
        ]
        
        # Text that should NOT be headings
        self.exclusion_patterns = [
            r'^\•',  # Bullet points
            r'^-\s',  # Dash lists
            r'^\d+\)\s',  # Numbered lists
            r'\.$',  # Ends with period (likely sentence)
            r'[.!?]\s*$',  # Ends with sentence punctuation
            r'^\s*$',  # Empty or whitespace
        ]
        
        # Words that indicate content, not headings
        self.content_indicators = {
            'articles': ['the', 'a', 'an', 'this', 'that', 'these', 'those'],
            'verbs': ['is', 'are', 'was', 'were', 'has', 'have', 'will', 'can', 'should'],
            'connectors': ['and', 'or', 'but', 'however', 'therefore', 'because'],
        }
    
    def detect(self, blocks: List[Dict], profile: Dict) -> List[Dict]:
        """Detect headings using universal principles"""
        try:
            # Step 1: Analyze typography hierarchy
            typography_analysis = self._analyze_typography(blocks)
            
            # Step 2: Find potential headings using multiple criteria
            candidates = self._find_heading_candidates(blocks, typography_analysis)
            
            # Step 3: Score and filter candidates
            scored_candidates = self._score_candidates(candidates, blocks)
            
            # Step 4: Convert to standard prediction format
            predictions = []
            for candidate in scored_candidates:
                block_index = candidate['index']
                score = candidate['score']
                text = candidate['text']
                block = candidate['block']
                
                # Determine heading level
                font_size = block.get('font_size', 12)
                is_bold = block.get('is_bold', False)
                
                if font_size > 14 or score > 0.8:
                    level = "H1"
                elif font_size > 12 or (is_bold and score > 0.7):
                    level = "H2"
                else:
                    level = "H3"
                
                predictions.append({
                    'block_id': block_index,
                    'is_heading': True,
                    'level': level,
                    'confidence': score
                })
            
            logger.info(f"Universal strategy found {len(predictions)} headings")
            return predictions
            
        except Exception as e:
            logger.error(f"Error in universal strategy: {e}")
            return []
    
    def extract_outline(self, text_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract outline using universal principles (legacy method)"""
        predictions = self.detect(text_blocks, {})
        
        outline = []
        for pred in predictions:
            if pred['is_heading']:
                block_id = pred['block_id']
                if block_id < len(text_blocks):
                    block = text_blocks[block_id]
                    outline.append({
                        'text': block.get('text', ''),
                        'level': pred['level'],
                        'page': block.get('page', 1),
                        'confidence': pred['confidence'],
                        'font_size': block.get('font_size', 12),
                        'is_bold': block.get('is_bold', False)
                    })
        
        return outline
    
    def _analyze_typography(self, text_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze typography patterns in the document"""
        font_sizes = []
        bold_texts = []
        fonts = defaultdict(int)
        
        for block in text_blocks:
            size = block.get('font_size', 12)
            font_sizes.append(size)
            fonts[block.get('font_family', 'Unknown')] += 1
            
            if block.get('is_bold', False):
                bold_texts.append(block)
        
        # Calculate statistics
        if font_sizes:
            avg_size = sum(font_sizes) / len(font_sizes)
            max_size = max(font_sizes)
            min_size = min(font_sizes)
            size_variance = sum((s - avg_size) ** 2 for s in font_sizes) / len(font_sizes)
        else:
            avg_size = max_size = min_size = size_variance = 12
        
        # Identify main body font
        main_font = max(fonts.items(), key=lambda x: x[1])[0] if fonts else 'Unknown'
        
        return {
            'avg_font_size': avg_size,
            'max_font_size': max_size,
            'min_font_size': min_size,
            'size_variance': size_variance,
            'main_font': main_font,
            'bold_count': len(bold_texts),
            'total_blocks': len(text_blocks),
            'bold_ratio': len(bold_texts) / len(text_blocks) if text_blocks else 0
        }
    
    def _find_heading_candidates(self, text_blocks: List[Dict[str, Any]], typography: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find potential heading candidates using multiple criteria"""
        candidates = []
        
        for i, block in enumerate(text_blocks):
            text = block.get('text', '').strip()
            if not text or len(text) > 100:  # Skip empty or very long text
                continue
            
            # Skip if matches exclusion patterns
            if any(re.match(pattern, text, re.IGNORECASE) for pattern in self.exclusion_patterns):
                continue
            
            # Calculate heading score
            score = self._calculate_heading_score(block, text, typography, i, text_blocks)
            
            if score > 0.3:  # Minimum threshold
                candidates.append({
                    'block': block,
                    'text': text,
                    'score': score,
                    'index': i
                })
        
        return candidates
    
    def _calculate_heading_score(self, block: Dict[str, Any], text: str, typography: Dict[str, Any], index: int, all_blocks: List[Dict[str, Any]]) -> float:
        """Calculate how likely this text is to be a heading"""
        score = 0.0
        
        # 1. Typography signals
        font_size = block.get('font_size', 12)
        is_bold = block.get('is_bold', False)
        
        # Size relative to average
        if font_size > typography['avg_font_size'] * 1.1:
            score += 0.3
        elif font_size >= typography['avg_font_size']:
            score += 0.1
        
        # Bold text
        if is_bold:
            score += 0.4
        
        # 2. Text pattern matching
        for pattern in self.heading_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                score += 0.5
                break
        
        # 3. Text characteristics
        # Title case
        if text.istitle() or (text[0].isupper() and not text.isupper()):
            score += 0.2
        
        # Short text (likely headings are concise)
        if 3 <= len(text.split()) <= 8:
            score += 0.2
        elif len(text.split()) <= 2:
            score += 0.1
        
        # No sentence punctuation at end
        if not re.search(r'[.!?]\s*$', text):
            score += 0.1
        
        # 4. Context analysis
        # Check if followed by body text
        if index + 1 < len(all_blocks):
            next_block = all_blocks[index + 1]
            next_text = next_block.get('text', '').strip()
            if next_text and len(next_text) > 20 and not next_block.get('is_bold', False):
                score += 0.2
        
        # Check if preceded by whitespace or other heading
        if index > 0:
            prev_block = all_blocks[index - 1]
            prev_text = prev_block.get('text', '').strip()
            if not prev_text or len(prev_text) < 10:
                score += 0.1
        
        # 5. Position signals
        # Beginning of page
        page_num = block.get('page', 1)
        if index == 0 or (index < 3 and page_num == 1):
            score += 0.1
        
        # 6. Content analysis - reduce score for content-like text
        words = text.lower().split()
        for word_type, word_list in self.content_indicators.items():
            if any(word in words for word in word_list):
                score -= 0.2
                break
        
        # 7. Special handling for bullet points context
        # If this looks like a bullet point item, reduce score significantly
        if self._is_likely_bullet_item(text, block, index, all_blocks):
            score -= 0.5
        
        return max(0.0, min(1.0, score))
    
    def _is_likely_bullet_item(self, text: str, block: Dict[str, Any], index: int, all_blocks: List[Dict[str, Any]]) -> bool:
        """Check if this text is likely a bullet point item"""
        # Check for bullet symbols nearby
        if index > 0:
            prev_block = all_blocks[index - 1]
            prev_text = prev_block.get('text', '').strip()
            if prev_text in ['•', '-', '*'] or re.match(r'^\d+\.\s*$', prev_text):
                return True
        
        # Check if this is a location/name followed by description (travel guide pattern)
        if ':' in text:
            parts = text.split(':', 1)
            if len(parts) == 2 and len(parts[0].strip()) < 20:
                return True
        
        # Check if next block contains description text starting with ':'
        if index + 1 < len(all_blocks):
            next_block = all_blocks[index + 1]
            next_text = next_block.get('text', '').strip()
            if next_text.startswith(':'):
                return True
        
        return False
    
    def _score_candidates(self, candidates: List[Dict[str, Any]], text_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score and filter candidates"""
        if not candidates:
            return []
        
        # Sort by score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Remove candidates that are too similar to higher-scoring ones
        filtered = []
        for candidate in candidates:
            is_duplicate = False
            for existing in filtered:
                if self._texts_similar(candidate['text'], existing['text']):
                    is_duplicate = True
                    break
            
            if not is_duplicate and candidate['score'] > 0.5:
                filtered.append(candidate)
        
        return filtered
    
    def _texts_similar(self, text1: str, text2: str) -> bool:
        """Check if two texts are too similar"""
        # Simple similarity check
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union > 0.7
    
    def _build_hierarchy(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build hierarchical outline structure"""
        if not candidates:
            return []
        
        outline = []
        
        for candidate in candidates:
            block = candidate['block']
            text = candidate['text']
            score = candidate['score']
            
            # Determine heading level based on font size and other factors
            font_size = block.get('font_size', 12)
            is_bold = block.get('is_bold', False)
            
            # Simple level assignment
            if font_size > 14 or score > 0.8:
                level = "H1"
            elif font_size > 12 or (is_bold and score > 0.7):
                level = "H2"
            else:
                level = "H3"
            
            outline.append({
                'text': text,
                'level': level,
                'page': block.get('page', 1),
                'confidence': score,
                'font_size': font_size,
                'is_bold': is_bold
            })
        
        return outline
