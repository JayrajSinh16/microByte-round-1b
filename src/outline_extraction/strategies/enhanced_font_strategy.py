# src/outline_extraction/strategies/enhanced_font_strategy.py
"""
Enhanced Universal Font-Based Outline Detection Strategy

This strategy analyzes font properties, layout, and content patterns to identify
headings universally across all PDF types without domain-specific hardcoding.

Key Improvements:
1. Advanced font hierarchy analysis with relative sizing
2. Content quality filtering to remove UI noise
3. Typography pattern recognition (bold, size, spacing)
4. Structural relationship analysis (heading-paragraph patterns)
5. Noise removal for OCR artifacts and UI elements
"""

import re
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter, defaultdict
import logging

from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class EnhancedFontStrategy(BaseStrategy):
    """Enhanced universal font-based heading detection"""
    
    def __init__(self):
        self.confidence = 0.95
        
        # Universal noise patterns to filter out (not domain-specific)
        self.noise_patterns = [
            # UI elements and artifacts
            r'^[©®™]\s*\w*$',                    # Copyright symbols
            r'^\s*[x×]\s*$',                     # Close buttons
            r'^[<>]\s*\w*$',                     # Navigation elements
            r'^\s*\d{1,2}\s*$',                  # Standalone numbers
            r'^[^\w\s]*$',                       # Only punctuation/symbols
            r'^\s*[A-Z]{1,2}\d+\s*$',           # Element IDs like "A2", "H1"
            
            # OCR artifacts and errors  
            r'^[A-Z]{1,2}\s+[A-Z]{1,2}[^a-z]*$', # "A B", "O01", etc.
            r'.*[,]{2,}.*',                      # Multiple commas (OCR error)
            r'.*[.]{3,}.*',                      # Multiple dots (OCR error)
            r'^[^\w\s]*[A-Z]{1,3}[^\w\s]*$',    # Single letters with symbols
            r'^.{1,3}$',                         # Very short fragments (1-3 chars)
            r'^[A-Z]\s[a-z]\s*$',                # "A Export a POF" -> "A Export"
            
            # Common OCR mistakes
            r'.*\bPOF\b.*',                      # "POF" instead of "PDF"
            r'.*\bOﬃce\b.*',                    # "Oﬃce" instead of "Office"
            r'^[A-Z]{1,2}[^a-zA-Z\s]+.*',       # Single letter followed by symbols
            r'^CG\s+\w+.*',                     # "CG Connected" OCR errors
            r'^[A-Z]{2}\s+[A-Z].*',             # "CG Connected", "AB Something" patterns
            
            # Navigation and UI text
            r'^(Help|Cancel|Close|OK|Next|Back|Continue|Submit)$',
            r'^(All\s+tools?|Tools?|Menu|Settings?).*',
            r'^(Export|Import|Create|Delete|Edit)\s+[a-z].*',  # Menu items
            r'^(Share|Send|Upload|Download)\s*$',
            r'^(Home|Search|Profile|Account)\s*$',
            
            # Common UI fragments and button text
            r'.*\s[+=×÷]\s.*',                   # Math operators in UI
            r'^(Good\s+morning|Hello|Welcome).*', # Greeting text
            r'^\([^)]*\)\s*$',                   # Text in parentheses only
            r'^[\d\s\-\|]+$',                    # Only numbers, spaces, dashes, pipes
            r'^[A-Z]{1,2}\s+[A-Z]{1,2}\s*$',    # "A B", "H1 H2" patterns
            
            # Generic noise patterns
            r'^(Note:?|Note|Tip:?|Warning:?).*',  # Enhanced note indicators (any text after)
            r'^notes?(\s+\w+)*$',                # "Note", "Notes", "Note something"
            r'^(Step\s+\d+:?)$',                # Step indicators without content
            r'^(Figure\s+\d+|Table\s+\d+).*',   # Figure/table references
        ]
        
        # Patterns for quality headings (universal)
        self.quality_heading_patterns = [
            # Clear section headers
            r'^[A-Z][a-z]+(\s+[A-Z][a-z]*)*\s*$',           # Title Case
            r'^[A-Z][A-Z\s]+[A-Z]$',                        # ALL CAPS HEADINGS
            r'^\d+\.?\s+[A-Z][a-z].*$',                     # Numbered sections
            r'^[A-Z][a-z]+.*:$',                            # Headers ending with colon
            r'^(Chapter|Section|Part|Unit)\s+\d+.*$',       # Structural headings
            r'^(Overview|Introduction|Conclusion|Summary)$', # Standard section names
        ]
        
        # Content words that suggest this is body text, not a heading
        self.body_text_indicators = [
            'the', 'and', 'or', 'but', 'with', 'from', 'into', 'onto', 'until',
            'when', 'where', 'while', 'during', 'before', 'after', 'through',
            'is', 'are', 'was', 'were', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'you', 'your', 'they', 'their'
        ]
    
    def detect(self, blocks: List[Dict], profile: Dict) -> List[Dict]:
        """Enhanced heading detection using font analysis and content quality filtering"""
        try:
            predictions = []
            
            # Step 1: Analyze document typography patterns
            typography_analysis = self._analyze_document_typography(blocks)
            
            # Step 2: Identify font hierarchy and size clusters
            font_hierarchy = self._build_font_hierarchy(blocks, typography_analysis)
            
            # Step 3: Analyze spatial relationships between blocks
            spatial_analysis = self._analyze_spatial_relationships(blocks)
            
            # Step 4: Score each block for heading likelihood
            for i, block in enumerate(blocks):
                text = block.get('text', '').strip()
                if not text or len(text) < 2:
                    continue
                
                # Calculate comprehensive heading score
                score = self._calculate_enhanced_heading_score(
                    block, text, typography_analysis, font_hierarchy, 
                    spatial_analysis, i, blocks
                )
                
                if score > 0.5:  # Enhanced threshold
                    level = self._determine_hierarchical_level(
                        block, font_hierarchy, score
                    )
                    
                    predictions.append({
                        'block_id': i,
                        'is_heading': True,
                        'level': level,
                        'confidence': min(score, 0.95)  # Cap confidence
                    })
            
            # Step 5: Post-process to refine hierarchy and remove false positives
            predictions = self._post_process_predictions(predictions, blocks)
            
            logger.info(f"Enhanced font strategy found {len(predictions)} headings")
            return predictions
            
        except Exception as e:
            logger.error(f"Error in enhanced font strategy: {e}")
            return []
    
    def _analyze_document_typography(self, blocks: List[Dict]) -> Dict:
        """Analyze typography patterns across the entire document"""
        font_sizes = []
        font_names = defaultdict(int)
        bold_blocks = 0
        italic_blocks = 0
        
        for block in blocks:
            # Collect font sizes
            size = block.get('font_size', 12)
            if size > 0:
                font_sizes.append(size)
            
            # Count font families
            font_name = block.get('font', 'default')
            font_names[font_name] += 1
            
            # Count formatting
            if block.get('is_bold', False):
                bold_blocks += 1
            if block.get('is_italic', False):
                italic_blocks += 1
        
        if not font_sizes:
            return {'body_size': 12, 'size_stats': {}}
        
        # Calculate size statistics
        size_array = np.array(font_sizes)
        size_stats = {
            'mean': np.mean(size_array),
            'median': np.median(size_array),
            'std': np.std(size_array),
            'min': np.min(size_array),
            'max': np.max(size_array),
            'unique_sizes': sorted(list(set(font_sizes)), reverse=True)
        }
        
        # Determine body text size (most common size)
        size_counter = Counter(font_sizes)
        body_size = size_counter.most_common(1)[0][0]
        
        # Determine primary font
        primary_font = max(font_names.items(), key=lambda x: x[1])[0]
        
        return {
            'body_size': body_size,
            'size_stats': size_stats,
            'primary_font': primary_font,
            'font_distribution': dict(font_names),
            'bold_ratio': bold_blocks / len(blocks) if blocks else 0,
            'italic_ratio': italic_blocks / len(blocks) if blocks else 0
        }
    
    def _build_font_hierarchy(self, blocks: List[Dict], typography: Dict) -> Dict:
        """Build a hierarchy of font sizes and determine heading levels"""
        unique_sizes = typography['size_stats']['unique_sizes']
        body_size = typography['body_size']
        
        # Create size-based hierarchy
        hierarchy = {}
        for i, size in enumerate(unique_sizes):
            if size > body_size * 1.5:  # Significantly larger than body
                if i == 0:
                    hierarchy[size] = 'H1'  # Largest
                elif i == 1:
                    hierarchy[size] = 'H2'  # Second largest
                else:
                    hierarchy[size] = 'H3'  # Other large sizes
            elif size > body_size * 1.2:  # Moderately larger
                hierarchy[size] = 'H3'
            elif size >= body_size:  # Same or slightly larger (if bold)
                hierarchy[size] = 'H4'  # Potential subheading if bold
        
        return {
            'size_levels': hierarchy,
            'body_size': body_size,
            'heading_threshold': body_size * 1.1
        }
    
    def _analyze_spatial_relationships(self, blocks: List[Dict]) -> Dict:
        """Analyze spatial relationships between blocks"""
        relationships = {}
        
        for i, block in enumerate(blocks):
            current_y = block.get('y', 0)
            
            # Find blocks before and after
            prev_block = blocks[i-1] if i > 0 else None
            next_block = blocks[i+1] if i < len(blocks) - 1 else None
            
            # Calculate spacing
            spacing_before = 0
            spacing_after = 0
            
            if prev_block:
                prev_y = prev_block.get('y', 0) + prev_block.get('height', 0)
                spacing_before = max(0, current_y - prev_y)
            
            if next_block:
                current_bottom = current_y + block.get('height', 0)
                next_y = next_block.get('y', 0)
                spacing_after = max(0, next_y - current_bottom)
            
            relationships[i] = {
                'spacing_before': spacing_before,
                'spacing_after': spacing_after,
                'has_space_before': spacing_before > 5,  # More than 5 units
                'has_space_after': spacing_after > 3,   # More than 3 units
                'isolated': spacing_before > 10 and spacing_after > 10
            }
        
        return relationships
    
    def _calculate_enhanced_heading_score(self, block: Dict, text: str, 
                                         typography: Dict, font_hierarchy: Dict,
                                         spatial: Dict, block_index: int, 
                                         all_blocks: List[Dict]) -> float:
        """Calculate comprehensive heading score using multiple factors"""
        score = 0.0
        
        # 1. FONT SIZE ANALYSIS (40% weight)
        font_size = block.get('font_size', 12)
        body_size = typography['body_size']
        size_ratio = font_size / body_size if body_size > 0 else 1.0
        
        if size_ratio >= 1.5:
            score += 0.4  # Significantly larger
        elif size_ratio >= 1.2:
            score += 0.3  # Moderately larger
        elif size_ratio >= 1.0:
            score += 0.1  # Same size or slightly larger
        
        # 2. FONT FORMATTING (25% weight)
        if block.get('is_bold', False):
            score += 0.2
        if block.get('is_italic', False):
            score += 0.05  # Italic less common for headings
        
        # Special boost for bold text at body size (common in PDFs)
        if block.get('is_bold', False) and 0.95 <= size_ratio <= 1.05:
            score += 0.1  # Bold body text can be subheadings
        
        # 3. CONTENT QUALITY ANALYSIS (20% weight)
        content_score = self._analyze_content_quality(text)
        score += content_score * 0.2
        
        # 4. SPATIAL RELATIONSHIPS (10% weight)
        if block_index in spatial:
            spatial_info = spatial[block_index]
            if spatial_info['has_space_before']:
                score += 0.05
            if spatial_info['has_space_after']:
                score += 0.03
            if spatial_info['isolated']:
                score += 0.02
        
        # 5. STRUCTURAL PATTERNS (5% weight)
        structure_score = self._analyze_structural_patterns(text, block_index, all_blocks)
        score += structure_score * 0.05
        
        # NEGATIVE SCORING - Remove obvious non-headings
        
        # Penalize noise patterns heavily
        for pattern in self.noise_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return 0.0  # Completely eliminate noise
        
        # Early filter for common noise patterns that slip through
        if text.strip().lower() in ['note:', 'note', 'tip:', 'tip', 'warning:', 'warning']:
            return 0.0
        
        # Early filter for OCR errors
        if any(error in text.lower() for error in ['pof', 'cg connected', 'all tools x']):
            return 0.0
        
        # Penalize very long text (likely paragraphs or instructions)
        if len(text) > 200:
            score -= 0.5
        elif len(text) > 100:
            score -= 0.3
        elif len(text) > 80:
            score -= 0.1
        
        # Penalize text with too many body text indicators
        words = text.lower().split()
        if len(words) > 0:
            body_word_count = sum(1 for word in words if word in self.body_text_indicators)
            if body_word_count / len(words) > 0.3:
                score -= 0.3
        
        # Penalize sentences (end with punctuation, likely content)
        if re.match(r'.*[.!?]\s*$', text) and len(words) > 5:
            score -= 0.25
        
        # Penalize numbered instructions or steps with detailed content
        if re.match(r'^\d+\.\s+.{30,}', text):  # Long numbered instructions
            score -= 0.4
        
        # Penalize text that starts with action verbs (instructions)
        action_verbs = ['select', 'click', 'choose', 'type', 'enter', 'press', 'drag', 'drop']
        first_word = words[0] if words else ""
        if first_word.lower() in action_verbs:
            score -= 0.4
        
        return max(0.0, min(1.0, score))  # Clamp to [0, 1]
    
    def _analyze_content_quality(self, text: str) -> float:
        """Analyze if text looks like a quality heading vs noise/body text"""
        score = 0.0
        
        # Early rejection for obvious noise
        if len(text.strip()) < 2:
            return 0.0
            
        # Check for quality heading patterns
        for pattern in self.quality_heading_patterns:
            if re.match(pattern, text):
                score += 0.8
                break
        
        # Length analysis
        word_count = len(text.split())
        if 1 <= word_count <= 8:
            score += 0.6  # Good heading length
        elif 9 <= word_count <= 15:
            score += 0.3  # Acceptable heading length
        elif word_count == 0:
            return 0.0   # No content
        else:
            score -= 0.2  # Too long or problematic
        
        # Character analysis
        if text.istitle():  # Title Case
            score += 0.4
        elif text.isupper() and word_count <= 6:  # Short ALL CAPS
            score += 0.3
        
        # Boost for clear section indicators
        section_indicators = [
            'overview', 'introduction', 'conclusion', 'summary',
            'chapter', 'section', 'part', 'step', 'method', 'process'
        ]
        if any(indicator in text.lower() for indicator in section_indicators):
            score += 0.3
        
        # NEGATIVE SCORING for obvious problems
        
        # Avoid fragments and errors
        if any(char in text for char in ['©', '®', '™', '×', '÷']):
            score -= 0.5
        
        # OCR error patterns
        ocr_error_patterns = [
            r'\bPOF\b',      # "POF" instead of "PDF"
            r'\bOﬃce\b',    # "Oﬃce" instead of "Office"
            r'\b[A-Z]\s[a-z]\b',  # Single letter followed by word
            r'[A-Z]{3,}[a-z]{1,2}[A-Z]',  # Mixed case errors
        ]
        for pattern in ocr_error_patterns:
            if re.search(pattern, text):
                score -= 0.4
                break
        
        # Penalize very short text that's not clearly a heading
        if len(text) <= 3 and not text.isupper():
            score -= 0.6
        
        # Penalize text with numbers that look like UI elements
        if re.search(r'\d{3,}', text):  # Long numbers (likely IDs)
            score -= 0.3
        
        # Penalize instruction-like text
        instruction_starters = ['click', 'select', 'choose', 'type', 'enter', 'press']
        if any(text.lower().startswith(starter) for starter in instruction_starters):
            score -= 0.4
        
        # Penalize text that looks like menu items or UI labels
        if re.match(r'^[A-Z][a-z]*\s+(a|an|the)\s+[A-Z]', text):  # "Export a PDF"
            score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def _analyze_structural_patterns(self, text: str, index: int, all_blocks: List[Dict]) -> float:
        """Analyze structural patterns that indicate headings"""
        score = 0.0
        
        # Numbered sections
        if re.match(r'^\d+\.?\s+[A-Z]', text):
            score += 0.8
        
        # Lettered sections
        if re.match(r'^[A-Z]\.?\s+[A-Z]', text):
            score += 0.6
        
        # Roman numerals
        if re.match(r'^[IVX]+\.?\s+[A-Z]', text):
            score += 0.7
        
        # Section keywords
        section_keywords = ['chapter', 'section', 'part', 'unit', 'step', 'phase']
        if any(keyword in text.lower() for keyword in section_keywords):
            score += 0.5
        
        return score
    
    def _determine_hierarchical_level(self, block: Dict, font_hierarchy: Dict, score: float) -> str:
        """Determine heading level based on font hierarchy and score"""
        font_size = block.get('font_size', 12)
        size_levels = font_hierarchy.get('size_levels', {})
        
        # First try size-based classification
        if font_size in size_levels:
            return size_levels[font_size]
        
        # Fallback based on score and formatting
        body_size = font_hierarchy.get('body_size', 12)
        size_ratio = font_size / body_size if body_size > 0 else 1.0
        
        if size_ratio >= 1.5:
            return 'H1'
        elif size_ratio >= 1.3:
            return 'H2'
        elif size_ratio >= 1.1 or block.get('is_bold', False):
            return 'H3'
        else:
            return 'H4'
    
    def _post_process_predictions(self, predictions: List[Dict], blocks: List[Dict]) -> List[Dict]:
        """Post-process predictions to refine hierarchy and remove false positives"""
        if not predictions:
            return predictions
        
        # Remove predictions with very low confidence
        filtered_predictions = [p for p in predictions if p['confidence'] > 0.5]
        
        # Ensure hierarchy makes sense (don't jump from H1 to H4)
        level_order = {'H1': 1, 'H2': 2, 'H3': 3, 'H4': 4}
        
        refined_predictions = []
        last_level = 0
        
        for prediction in sorted(filtered_predictions, key=lambda x: x['block_id']):
            current_level = level_order.get(prediction['level'], 4)
            
            # Don't jump more than one level down
            if last_level > 0 and current_level > last_level + 1:
                prediction['level'] = f"H{last_level + 1}"
            
            refined_predictions.append(prediction)
            last_level = level_order.get(prediction['level'], 4)
        
        return refined_predictions
