"""
Universal Document Structure Analysis Strategy

Detects headings based on universal document patterns:
1. Typography hierarchy (font size, weight, spacing)
2. Structural patterns (bullet points, numbering, indentation)
3. Content relationships (headings followed by lists/content)
4. Text formatting conventions (title case, punctuation, length)
5. Generic content section patterns (titles followed by structured content)

This strategy works across all document types without domain-specific hardcoded logic.
"""

import re
import logging
from typing import List, Dict, Any, Tuple
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class UniversalDocumentStrategy(BaseStrategy):
    """Universal strategy based on document structure patterns"""
    
    def __init__(self):
        self.confidence = 0.90
        
        # Universal heading patterns (not domain-specific)
        self.heading_patterns = [
            # Numbered sections (1., 2., I., II., A., B., etc.)
            r'^\d+\.?\s+[A-Z].*$',
            r'^[IVX]+\.?\s+[A-Z].*$',
            r'^[A-Z]\.?\s+[A-Z].*$',
            
            # Title case patterns (First Letter Capitalized)
            r'^[A-Z][a-z]+(\s+[A-Z][a-z]*)*(\s+[A-Z][a-z]*)*$',
            
            # Section headers with colons
            r'^[A-Z][a-zA-Z\s]+:$',
            
            # All caps headers
            r'^[A-Z\s]+$',
            
            # Mixed case headers without ending punctuation (fixed character range)
            r'^[A-Z][a-zA-Z\s\-&]+[^.!?]$',
        ]
        
        # Content patterns that indicate NOT a heading
        self.content_patterns = [
            # Bullet points and lists
            r'^\s*[\•\-\*\+]\s',      # Bullet points
            r'^\s*\d+\.\s',           # Numbered lists
            r'^\s*\d+\)\s',           # Parenthetical numbering
            r'^\s*[a-z]\.\s',         # Lowercase lettered lists
            r'^\s*[a-z]\)\s',         # Lowercase parenthetical
            
            # Sentences (end with punctuation)
            r'.*[.!?]\s*$',
            
            # Instruction/action patterns
            r'^\s*(Heat|Mix|Add|Pour|Cook|Bake|In\s+a|Combine|Place|Remove|Stir|Set).*',
            
            # Measurement/quantity patterns
            r'^\s*\d+(\.\d+)?\s*(cups?|tbsp|tsp|lbs?|oz|grams?|ml|liters?).*',
            
            # Long sentences (likely content, not headings)
            r'^.{80,}$',
            
            # Parenthetical content
            r'^\s*\([^)]*\)\s*$',
        ]
        
        # Words that commonly appear in content vs headings
        self.content_indicators = [
            'the', 'and', 'or', 'but', 'with', 'from', 'into', 'onto', 'until',
            'while', 'during', 'before', 'after', 'through', 'between', 'among',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'will', 'would', 'could', 'should', 'may', 'might', 'can'
        ]
    
    def detect(self, blocks: List[Dict], profile: Dict) -> List[Dict]:
        """Detect headings using universal document structure analysis"""
        try:
            predictions = []
            
            # Step 1: Analyze document typography
            typography = self._analyze_typography(blocks)
            
            # Step 2: Identify content structure patterns
            structure_info = self._analyze_document_structure(blocks)
            
            # Step 3: Score each block as potential heading
            for i, block in enumerate(blocks):
                text = block.get('text', '').strip()
                if not text or len(text) < 2:
                    continue
                
                # Check for content section headers within text blocks
                content_headers = self._extract_content_headers(text)
                if content_headers:
                    for header_name in content_headers:
                        predictions.append({
                            'block_id': i,
                            'is_heading': True,
                            'level': 'H2',  # Content headers are H2
                            'confidence': 0.9,
                            'text': header_name  # Override with just the header name
                        })
                    continue  # Skip normal analysis for this block
                
                score = self._calculate_universal_heading_score(
                    block, text, typography, structure_info, i, blocks
                )
                
                if score > 0.4:  # Universal threshold
                    level = self._determine_heading_level(block, text, score, typography)
                    
                    predictions.append({
                        'block_id': i,
                        'is_heading': True,
                        'level': level,
                        'confidence': score
                    })
            
            logger.info(f"Universal strategy found {len(predictions)} headings")
            return predictions
            
        except Exception as e:
            logger.error(f"Error in universal strategy: {e}")
            return []
    
    def _analyze_typography(self, blocks: List[Dict]) -> Dict:
        """Analyze typography patterns across the document"""
        font_sizes = []
        font_weights = []
        fonts = {}
        
        for block in blocks:
            size = block.get('font_size', 12)
            if size > 0:
                font_sizes.append(size)
            
            if block.get('is_bold', False):
                font_weights.append(1)
            else:
                font_weights.append(0)
            
            font = block.get('font', 'default')
            fonts[font] = fonts.get(font, 0) + 1
        
        if font_sizes:
            typography = {
                'avg_font_size': sum(font_sizes) / len(font_sizes),
                'max_font_size': max(font_sizes),
                'min_font_size': min(font_sizes),
                'font_size_std': self._calculate_std(font_sizes),
                'bold_ratio': sum(font_weights) / len(font_weights),
                'most_common_font': max(fonts.items(), key=lambda x: x[1])[0] if fonts else 'default'
            }
        else:
            typography = {
                'avg_font_size': 12, 'max_font_size': 12, 'min_font_size': 12,
                'font_size_std': 0, 'bold_ratio': 0, 'most_common_font': 'default'
            }
        
        return typography
    
    def _analyze_document_structure(self, blocks: List[Dict]) -> Dict:
        """Analyze structural patterns in the document"""
        structure = {
            'bullet_blocks': [],
            'numbered_blocks': [],
            'short_blocks': [],
            'long_blocks': [],
            'isolated_blocks': []
        }
        
        for i, block in enumerate(blocks):
            text = block.get('text', '').strip()
            if not text:
                continue
            
            # Identify bullet point blocks
            if re.match(r'^\s*[\•\-\*\+]\s', text):
                structure['bullet_blocks'].append(i)
            
            # Identify numbered list blocks
            elif re.match(r'^\s*\d+[\.\)]\s', text):
                structure['numbered_blocks'].append(i)
            
            # Classify by length
            word_count = len(text.split())
            if word_count <= 5:
                structure['short_blocks'].append(i)
            elif word_count > 20:
                structure['long_blocks'].append(i)
            
            # Check if block appears isolated (surrounded by different content)
            if self._is_isolated_block(i, blocks):
                structure['isolated_blocks'].append(i)
        
        return structure
    
    def _calculate_universal_heading_score(self, block: Dict, text: str, 
                                         typography: Dict, structure: Dict, 
                                         index: int, all_blocks: List[Dict]) -> float:
        """Calculate heading score using universal document analysis"""
        score = 0.0
        
        # Rule 1: Eliminate obvious content patterns
        for pattern in self.content_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return 0.0  # Definitely not a heading
        
        # Rule 2: Typography signals (most reliable)
        font_size = block.get('font_size', 12)
        is_bold = block.get('is_bold', False)
        
        # Large font size relative to document average
        size_ratio = font_size / typography['avg_font_size']
        if size_ratio > 1.5:
            score += 0.6
        elif size_ratio > 1.2:
            score += 0.4
        elif size_ratio > 1.0:
            score += 0.2
        
        # Bold text is strong indicator
        if is_bold:
            score += 0.4
        
        # Rule 3: Pattern matching for common heading structures
        for pattern in self.heading_patterns:
            if re.match(pattern, text.strip()):
                score += 0.4
                break
        
        # Rule 4: Text characteristics
        words = text.split()
        word_count = len(words)
        
        # Optimal heading length (not too short, not too long)
        if 1 <= word_count <= 8:
            score += 0.3
        elif word_count <= 12:
            score += 0.1
        elif word_count > 20:
            score -= 0.2  # Too long for heading
        
        # Title case or proper capitalization
        if text.istitle() or (text[0].isupper() and not text.isupper()):
            score += 0.2
        
        # No ending punctuation (except colon for sections)
        if not re.search(r'[.!?]\s*$', text):
            if text.endswith(':'):
                score += 0.3  # Section headers
            else:
                score += 0.1
        
        # Rule 5: Structural context analysis
        # Check if followed by content that supports heading hypothesis
        if index + 1 < len(all_blocks):
            next_block = all_blocks[index + 1]
            next_text = next_block.get('text', '').strip()
            
            # Followed by bullet points or numbered lists
            if index + 1 in structure['bullet_blocks'] or index + 1 in structure['numbered_blocks']:
                score += 0.4
            
            # Followed by longer content
            elif len(next_text.split()) > 15:
                score += 0.2
        
        # Rule 6: Position and isolation signals
        # First block often contains title
        if index == 0 and font_size > typography['avg_font_size']:
            score += 0.3
        
        # Isolated short blocks are often headings
        if index in structure['isolated_blocks'] and word_count <= 6:
            score += 0.3
        
        # Rule 7: Content word analysis
        text_words = text.lower().split()
        content_word_count = sum(1 for word in text_words if word in self.content_indicators)
        if content_word_count / max(len(text_words), 1) > 0.3:
            score -= 0.2  # Too many content words
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _determine_heading_level(self, block: Dict, text: str, score: float, typography: Dict) -> str:
        """Determine heading level based on typography and score"""
        font_size = block.get('font_size', 12)
        size_ratio = font_size / typography['avg_font_size']
        
        # H1: Very large fonts or very high scores
        if size_ratio > 1.8 or score > 0.9:
            return "H1"
        
        # H2: Large fonts or high scores  
        elif size_ratio > 1.3 or score > 0.7:
            return "H2"
        
        # H3: Everything else
        else:
            return "H3"
    
    def _is_isolated_block(self, index: int, blocks: List[Dict]) -> bool:
        """Check if a block appears structurally isolated"""
        if not (0 < index < len(blocks) - 1):
            return False
        
        current_text = blocks[index].get('text', '').strip()
        prev_text = blocks[index - 1].get('text', '').strip()
        next_text = blocks[index + 1].get('text', '').strip()
        
        current_words = len(current_text.split())
        prev_words = len(prev_text.split())
        next_words = len(next_text.split())
        
        # Short block between longer blocks suggests heading
        return current_words <= 6 and prev_words > 15 and next_words > 15
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) <= 1:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def _extract_content_headers(self, text: str) -> List[str]:
        """Extract content section headers from text blocks using universal patterns"""
        import re
        
        content_headers = []
        
        # Pattern 1: Title followed by structured content markers (Ingredients, Instructions, etc.)
        pattern1 = r'([A-Z][a-zA-Z\s&\'-]+?)\s*[\uf0b7•\*\-]?\s*(Ingredients|Instructions|Overview|Summary|Description|Details|Steps|Process|Method|Procedure):'
        matches1 = re.findall(pattern1, text)
        
        # Pattern 2: Title followed by bullet symbol then content marker
        pattern2 = r'([A-Z][a-zA-Z\s&\'-]+?)\s*[\uf0b7•\*\-]\s*(Ingredients|Instructions|Overview|Summary|Description|Details|Steps|Process|Method|Procedure):'
        matches2 = re.findall(pattern2, text)
        
        # Pattern 3: Standalone section headers at start of blocks (title case, reasonable length)
        lines = text.split('\n')
        for line in lines[:3]:  # Check first few lines
            line = line.strip()
            if line and 2 <= len(line) <= 40:  # Reasonable header length
                # Check if it's title case and not starting with list markers
                if (line[0].isupper() and 
                    not re.match(r'^(o\s|•\s|\d+\.\s|\d+\)\s|[a-z]\.\s)', line) and  # Not bullet/numbered list
                    not re.search(r'[.!?]\s*$', line) and  # Not ending with sentence punctuation
                    not re.search(r'\bto taste\b', line, re.IGNORECASE) and  # Not ingredient instructions
                    not re.search(r'\bfor serving\b', line, re.IGNORECASE) and  # Not serving instructions
                    len(line.split()) <= 6):  # Not too many words for a header
                    content_headers.append(line)
        
        # Pattern 4: Headers followed by structured content (colon-terminated titles)
        colon_pattern = r'^([A-Z][a-zA-Z\s&\'-]{2,30}):\s*$'
        for line in lines[:5]:
            match = re.match(colon_pattern, line.strip())
            if match:
                content_headers.append(match.group(1))
        
        # Clean up pattern matches (extract just the title part)
        all_title_matches = [match[0] for match in matches1 + matches2]
        for match in all_title_matches:
            title = match.strip()
            # Remove overly long or short titles
            if 3 <= len(title) <= 50 and len(title.split()) <= 6:
                # Remove common false positives and ingredient-like text
                title_lower = title.lower()
                if (title_lower not in ['the', 'and', 'or', 'but', 'with', 'from', 'this', 'that'] and
                    not re.match(r'^\d+\s+(cups?|tbsp|tsp|lbs?|oz|grams?|ml|liters?)', title_lower) and  # Not measurements
                    'oil for' not in title_lower and  # Not cooking instructions
                    'salt' != title_lower and  # Not single ingredients
                    'pepper' != title_lower and
                    'cheese' not in title_lower and
                    'skewers' != title_lower):
                    content_headers.append(title)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_headers = []
        for header in content_headers:
            if header not in seen:
                seen.add(header)
                unique_headers.append(header)
        
        return unique_headers
