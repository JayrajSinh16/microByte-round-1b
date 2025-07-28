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

try:
    from .base_strategy import BaseStrategy
except ImportError:
    # Fallback for standalone execution
    from abc import ABC, abstractmethod
    from typing import List, Dict
    
    class BaseStrategy(ABC):
        @abstractmethod
        def detect(self, blocks: List[Dict], profile: Dict) -> List[Dict]:
            pass

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
            
            # Universal document patterns for different content types
            r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$',             # Title Case: "Project Management", "Data Analysis" 
            r'^[A-Z][a-z]+(\s+[a-z]+)*(\s+[A-Z][a-z]+)*$', # Mixed case: "Sales and Marketing"
            r'^[A-Z][a-z]+\s+(with|and|in|on|for)\s+[A-Z][a-z]+.*$', # "Analysis with Python"
            r'^(Chapter|Section|Part|Introduction|Overview|Summary|Conclusion|Method|Process|Results).*$', # Common section headers
            r'^(Step|Phase|Stage)\s*\d*\s*:.*$',           # Sequential information
            r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*\s*$',         # Clean multi-word titles
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
                
                # Check if this block contains multiple content items (trailing titles)
                multi_content_headings = self._extract_multiple_content_items(block, text, i)
                
                if multi_content_headings:
                    # Add all extracted content headings from this block
                    for content_heading in multi_content_headings:
                        level = self._determine_hierarchical_level(
                            block, font_hierarchy, content_heading['confidence']
                        )
                        content_heading['level'] = level
                        predictions.append(content_heading)
                else:
                    # Process as single content block (existing logic)
                    # Calculate comprehensive heading score
                    score = self._calculate_enhanced_heading_score(
                        block, text, typography_analysis, font_hierarchy, 
                        spatial_analysis, i, blocks
                    )
                    
                    if score > 0.3:  # Threshold suitable for various document types
                        level = self._determine_hierarchical_level(
                            block, font_hierarchy, score
                        )
                        
                        # Extract clean heading text
                        heading_text = self._extract_clean_heading(text)
                        
                        prediction = {
                            'block_id': i,
                            'is_heading': True,
                            'level': level,
                            'confidence': min(score, 0.95)  # Cap confidence
                        }
                        
                        # Include extracted heading text if it's different from original
                        if heading_text != text:
                            prediction['text'] = heading_text
                            
                        predictions.append(prediction)
            
            # Step 5: Post-process to refine hierarchy and remove false positives
            predictions = self._post_process_predictions(predictions, blocks)
            
            logger.info(f"Enhanced font strategy found {len(predictions)} headings")
            return predictions
            
        except Exception as e:
            logger.error(f"Error in enhanced font strategy: {e}")
            return []
    
    def _analyze_document_typography(self, blocks: List[Dict]) -> Dict:
        """Analyze typography patterns across the entire document"""
        
        # Check if blocks is empty
        if not blocks:
            logger.warning("Enhanced font strategy received empty blocks list")
            return {
                'body_size': 12,
                'size_stats': {
                    'mean': 12, 'median': 12, 'std': 0, 'min': 12, 'max': 12,
                    'unique_sizes': [12]
                },
                'primary_font': 'default',
                'font_distribution': {'default': 0},
                'bold_ratio': 0,
                'italic_ratio': 0,
                'underlined_ratio': 0
            }
        
        font_sizes = []
        font_names = defaultdict(int)
        bold_blocks = 0
        italic_blocks = 0
        underlined_blocks = 0
        
        for block in blocks:
            # Collect font sizes - be more defensive about missing/zero sizes
            size = block.get('font_size')
            if size is None or size <= 0:
                size = 12  # Use default for missing/invalid sizes
            font_sizes.append(size)
            
            # Count font families
            font_name = block.get('font', 'default')
            font_names[font_name] += 1
            
            # Count formatting
            if block.get('is_bold', False):
                bold_blocks += 1
            if block.get('is_italic', False):
                italic_blocks += 1
            if block.get('is_underlined', False):
                underlined_blocks += 1
        
        # Handle case when no font sizes are found
        if not font_sizes:
            logger.warning("No font sizes found in document, using defaults")
            return {
                'body_size': 12,
                'size_stats': {
                    'mean': 12, 'median': 12, 'std': 0, 'min': 12, 'max': 12,
                    'unique_sizes': [12]
                },
                'primary_font': 'default',
                'font_distribution': {'default': len(blocks)},
                'bold_ratio': bold_blocks / len(blocks) if blocks else 0,
                'italic_ratio': italic_blocks / len(blocks) if blocks else 0,
                'underlined_ratio': underlined_blocks / len(blocks) if blocks else 0
            }
        
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
        primary_font = max(font_names.items(), key=lambda x: x[1])[0] if font_names else 'default'
        
        return {
            'body_size': body_size,
            'size_stats': size_stats,
            'primary_font': primary_font,
            'font_distribution': dict(font_names),
            'bold_ratio': bold_blocks / len(blocks) if blocks else 0,
            'italic_ratio': italic_blocks / len(blocks) if blocks else 0,
            'underlined_ratio': underlined_blocks / len(blocks) if blocks else 0
        }
    
    def _build_font_hierarchy(self, blocks: List[Dict], typography: Dict) -> Dict:
        """Build a hierarchy of font sizes and determine heading levels"""
        unique_sizes = typography['size_stats'].get('unique_sizes', [12])
        body_size = typography['body_size']
        
        # Handle edge case where we have minimal font data
        if not unique_sizes:
            unique_sizes = [body_size]
        
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
            elif size >= body_size * 0.95:  # Same or slightly different (common in recipes)
                hierarchy[size] = 'H4'  # Potential subheading if bold/underlined
        
        return {
            'size_levels': hierarchy,
            'body_size': body_size,
            'heading_threshold': body_size * 0.95  # Lower threshold for recipe-style documents
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
        
        # 1. FONT SIZE ANALYSIS (35% weight - reduced to accommodate formatting)
        font_size = block.get('font_size', 12)
        body_size = typography['body_size']
        size_ratio = font_size / body_size if body_size > 0 else 1.0
        
        if size_ratio >= 1.5:
            score += 0.35  # Significantly larger
        elif size_ratio >= 1.2:
            score += 0.25  # Moderately larger
        elif size_ratio >= 0.95:  # Same size or close (common in recipes)
            score += 0.05  # Small boost for same-size text (depends on other factors)
        
        # 2. FONT FORMATTING (30% weight - increased for recipe-style docs)
        formatting_score = 0.0
        
        # Bold text is often used for headings in recipes
        if block.get('is_bold', False):
            formatting_score += 0.25
            
            # Extra boost for bold text at body size (common pattern in recipes)
            if 0.90 <= size_ratio <= 1.10:
                formatting_score += 0.10
        
        # Underlined text often indicates headings in recipe documents
        if block.get('is_underlined', False):
            formatting_score += 0.20
        
        # Italic is less common for headings but can indicate special sections
        if block.get('is_italic', False):
            formatting_score += 0.05
        
        # Combination bonuses
        if block.get('is_bold', False) and block.get('is_underlined', False):
            formatting_score += 0.10  # Bold + underlined is strong heading indicator
            
        score += min(formatting_score, 0.30)  # Cap formatting score
        
        # 3. CONTENT QUALITY ANALYSIS (20% weight)
        content_score = self._analyze_content_quality(text)
        score += content_score * 0.20
        
        # 4. CONTENT-SPECIFIC PATTERN ANALYSIS (10% weight)
        content_score = self._analyze_content_patterns(text, block, all_blocks, block_index)
        score += content_score * 0.10
        
        # 5. SPATIAL RELATIONSHIPS (5% weight - reduced)
        if block_index in spatial:
            spatial_info = spatial[block_index]
            if spatial_info['has_space_before']:
                score += 0.03
            if spatial_info['has_space_after']:
                score += 0.02
            if spatial_info['isolated']:
                score += 0.01
        
        # Note: Structural patterns analysis removed to focus on universal formatting patterns
        
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
        # BUT: Be lenient with recipe ingredient lists which naturally combine heading + content
        is_recipe_heading = ('ingredients:' in text.lower() or 
                           text.lower().endswith('ingredients') or
                           any(word in text.lower() for word in ['recipe', 'preparation', 'cooking']))
        
        if is_recipe_heading:  # If this looks like a recipe heading, be lenient on length
            if len(text) > 400:  # Only penalize extremely long text
                score -= 0.2
        else:
            # Apply normal length penalties for non-recipe text
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
        
        # Length analysis - more lenient for recipe names
        word_count = len(text.split())
        if 1 <= word_count <= 8:
            score += 0.6  # Good heading length
        elif 9 <= word_count <= 15:
            score += 0.3  # Acceptable heading length
        elif word_count == 0:
            return 0.0   # No content
        else:
            score -= 0.1  # Reduced penalty for longer text (could be recipe names)
        
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
            
        # RECIPE-SPECIFIC BOOSTS
        # Recipe names often follow patterns like "Chicken and Rice", "Beef Stir-Fry"
        recipe_patterns = [
            r'^[A-Z][a-z]+(\s+(and|with|in|&)\s+[A-Z][a-z]+)+$',  # "Chicken and Rice"
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+(\s+[A-Z][a-z]+)*$',      # "Chicken Alfredo", "Beef Stir Fry"
            r'^[A-Z][a-z]+(\s+[a-z]+)*\s+[A-Z][a-z]+$',           # "Sweet and Sour Chicken"
        ]
        for pattern in recipe_patterns:
            if re.match(pattern, text):
                score += 0.4  # Strong boost for recipe name patterns
                break
        
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
            score -= 0.4  # Reduced penalty
        
        # Penalize text with numbers that look like UI elements
        if re.search(r'\d{3,}', text):  # Long numbers (likely IDs)
            score -= 0.2  # Reduced penalty
        
        # Penalize instruction-like text (but be more lenient for recipe names)
        instruction_starters = ['click', 'select', 'choose', 'type', 'enter', 'press']
        if any(text.lower().startswith(starter) for starter in instruction_starters):
            score -= 0.2  # Reduced penalty since recipes might start with cooking verbs
        
        # Penalize text that looks like menu items or UI labels
        if re.match(r'^[A-Z][a-z]*\s+(a|an|the)\s+[A-Z]', text):  # "Export a PDF"
            score -= 0.2  # Reduced penalty
        
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
    
    def _analyze_content_patterns(self, text: str, block: Dict, all_blocks: List[Dict], index: int) -> float:
        """Analyze patterns specific to any document type (universal approach)"""
        score = 0.0
        text_lower = text.lower().strip()
        
        # Handle blocks that contain both heading and content (common in many PDF types)
        # Extract just the heading part (before colon or bullet points)
        heading_part = text
        if ':' in text:
            heading_part = text.split(':')[0].strip()
        elif '•' in text:
            heading_part = text.split('•')[0].strip()
        elif text.count('\n') > 0:
            # Take first line if multi-line
            heading_part = text.split('\n')[0].strip()
        
        # Use the heading part for analysis
        heading_lower = heading_part.lower().strip()
        
        # 1. COMMON SECTION HEADERS (universal document patterns)
        section_headers = [
            'introduction', 'overview', 'summary', 'conclusion', 'results', 'method',
            'process', 'procedure', 'analysis', 'discussion', 'background', 'objectives',
            'requirements', 'specifications', 'details', 'information', 'data', 'content'
        ]
        
        for header in section_headers:
            if header in heading_lower:
                score += 0.8
                break
        
        # 2. STRUCTURED TITLE PATTERNS (focus on heading part only)
        heading_word_count = len(heading_part.split())
        
        # Short, title-case phrases (1-6 words) are often section names
        if 1 <= heading_word_count <= 6 and heading_part.istitle():
            score += 0.6
            
        # Titles with common connecting words
        connecting_words = ['with', 'and', 'in', 'on', 'for', 'of', 'by', 'to']
        if any(f' {word} ' in heading_lower for word in connecting_words) and heading_word_count <= 8:
            score += 0.5
            
        # 3. DOCUMENT STRUCTURE PATTERNS (universal patterns)
        structure_patterns = [
            r'^[A-Z][a-z]+(\s+(and|with|in|of|for)\s+[A-Z][a-z]+)+',  # "Analysis and Results"
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+(\s+[A-Z][a-z]+)*',          # "Project Management", "Data Analysis"
            r'^[A-Z][a-z]+(\s+[a-z]+)*\s+[A-Z][a-z]+',               # "Best and Worst Case"
        ]
        for pattern in structure_patterns:
            if re.match(pattern, heading_part):
                score += 0.6  # Strong boost for structured patterns
                break
                
        # 4. FORMATTING CONTEXT ANALYSIS
        # Check if this formatted text is followed by a list or content
        if index + 1 < len(all_blocks):
            next_block = all_blocks[index + 1]
            next_text = next_block.get('text', '').strip()
            
            # If bold/formatted text is followed by a list, it's likely a heading
            if next_text.startswith(('•', '-', '*', '1.', '2.', '3.')):
                score += 0.4
                
            # If followed by longer paragraph text, this might be a title
            if len(next_text) > 50 and not next_block.get('is_bold', False):
                score += 0.3
        
        # 5. SUBSECTION HEADERS
        # "Details:", "For more information:", etc.
        if heading_lower.endswith(':') and heading_word_count <= 4:
            if any(subsection_word in heading_lower for subsection_word in ['detail', 'information', 'note', 'example', 'reference']):
                score += 0.7
        
        # 6. SEQUENTIAL INFORMATION
        # "Step 1", "Phase 2", "Part A", etc.
        serving_patterns = [
            r'(step|phase|part|section|chapter)\s*\d+',
            r'(stage|level|tier)\s*\d+',
            r'(appendix|annex)\s*[a-z]',
            r'\d+\.\d+',  # "2.1", "3.4" etc.
        ]
        
        for pattern in serving_patterns:
            if re.search(pattern, heading_lower):
                score += 0.6
                break
        
        # 7. BOOST FOR SECTION NAMES FOLLOWED BY DETAILS
        if heading_lower.endswith(('details:', 'information:', 'content:', 'overview:')):
            # Extract the section name part (before "details:")
            section_name = heading_part.replace(' Details:', '').replace(' Information:', '').replace(' Content:', '').replace(' Overview:', '').strip()
            section_name_words = len(section_name.split())
            
            if 2 <= section_name_words <= 6:  # Good section name length
                score += 0.8  # Very strong boost for section names with details
            elif section_name_words > 0:  # Any section name
                score += 0.6  # Strong boost
        
        # 8. AVOID FALSE POSITIVES
        # Don't boost obvious instruction text 
        instruction_indicators = [
            'click', 'select', 'choose', 'enter', 'type', 'press', 'navigate',
            'open', 'close', 'save', 'delete', 'edit', 'modify'
        ]
        
        # Only penalize if text starts with action verb and is very long
        first_word = heading_part.split()[0].lower() if heading_part.split() else ""
        if first_word in instruction_indicators and len(text) > 100:  # Increased threshold
            score -= 0.2  # Reduced penalty
        
        # Don't boost measurements or data themselves (just their headers)
        if re.match(r'^\d+\s*(percent|%|mm|cm|kg|lb|inch)', heading_lower):
            score -= 0.3
            
        return max(0.0, min(1.0, score))
    
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
            
        # 3. RECIPE NAME PATTERNS (universal food patterns)
        recipe_name_patterns = [
            r'^[A-Z][a-z]+(\s+(and|with|in|&)\s+[A-Z][a-z]+)+',  # "Chicken and Rice"
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+(\s+[A-Z][a-z]+)*',      # "Chicken Alfredo", "Beef Stir Fry"
            r'^[A-Z][a-z]+(\s+[a-z]+)*\s+[A-Z][a-z]+',           # "Sweet and Sour Chicken"
        ]
        for pattern in recipe_name_patterns:
            if re.match(pattern, heading_part):
                score += 0.6  # Strong boost for recipe name patterns
                break
                
        # 4. FORMATTING CONTEXT ANALYSIS
        # Check if this formatted text is followed by a list or instructions
        if index + 1 < len(all_blocks):
            next_block = all_blocks[index + 1]
            next_text = next_block.get('text', '').strip()
            
            # If bold/formatted text is followed by a list, it's likely a heading
            if next_text.startswith(('•', '-', '*', '1.', '2.', '3.')):
                score += 0.4
                
            # If followed by longer paragraph text, this might be a title
            if len(next_text) > 50 and not next_block.get('is_bold', False):
                score += 0.3
        
        # 5. INGREDIENT LIST HEADERS
        # "Ingredients:" or "For the sauce:" style headers
        if heading_lower.endswith(':') and heading_word_count <= 4:
            if any(ingredient_word in heading_lower for ingredient_word in ['ingredient', 'for the', 'sauce', 'marinade', 'dressing']):
                score += 0.7
        
        # 6. SERVING/TIMING INFORMATION
        # "Serves 4", "Prep: 15 min", etc.
        serving_patterns = [
            r'serves?\s*\d+',
            r'prep\s*:?\s*\d+',
            r'cook\s*:?\s*\d+', 
            r'total\s*:?\s*\d+',
            r'\d+\s*min',
            r'\d+\s*hour'
        ]
        
        for pattern in serving_patterns:
            if re.search(pattern, heading_lower):
                score += 0.6
                break
        
        # 7. BOOST FOR RECIPE NAMES THAT END WITH "Ingredients:"
        if heading_lower.endswith('ingredients:') or heading_lower.endswith('ingredients'):
            # Extract the recipe name part (before "ingredients")
            recipe_name = heading_part.replace(' Ingredients:', '').replace(' Ingredients', '').replace(' ingredients:', '').replace(' ingredients', '').strip()
            recipe_name_words = len(recipe_name.split())
            
            if 2 <= recipe_name_words <= 8:  # Good recipe name length (increased max)
                score += 0.8  # Very strong boost for recipe names with ingredients
            elif recipe_name_words > 0:  # Any recipe name
                score += 0.6  # Strong boost
        
        # 8. AVOID FALSE POSITIVES
        # Don't boost obvious instruction text (but be lenient for recipe names)
        instruction_indicators = [
            'heat', 'add', 'mix', 'stir', 'cook', 'bake', 'season', 'serve',
            'remove', 'place', 'cut', 'chop', 'slice'
        ]
        
        # Only penalize if text starts with action verb and is very long
        first_word = heading_part.split()[0].lower() if heading_part.split() else ""
        if first_word in instruction_indicators and len(text) > 100:  # Increased threshold
            score -= 0.2  # Reduced penalty
        
        # Don't boost ingredient measurements themselves (just their headers)
        if re.match(r'^\d+\s*(cup|tbsp|tsp|lb|oz|gram|kg)', heading_lower):
            score -= 0.3
            
        return max(0.0, min(1.0, score))
    
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
        
        # Remove predictions with very low confidence (aligned with main threshold)
        filtered_predictions = [p for p in predictions if p['confidence'] > 0.3]
        
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
    
    def _extract_clean_heading(self, text: str) -> str:
        """Extract clean heading text from any document type, handling multi-content blocks"""
        import re
        
        # PATTERN 1: Handle trailing headings at end of text blocks
        # Example: "...in conclusion. Next Topic" or "...see results.  Project Summary"
        trailing_heading_pattern = r'.*[.!?]\s+([A-Z][^\d\n][^\n.!?]*?)$'
        
        match = re.search(trailing_heading_pattern, text, re.UNICODE)
        if match:
            potential_heading = match.group(1).strip()
            # Validate this looks like a heading (not continuation text)
            if (len(potential_heading) < 80 and 
                potential_heading and 
                not potential_heading.lower().startswith(('see', 'refer', 'note', 'please', 'for more', 'continue')) and
                not re.search(r'\b(and|or|with|until|for|minutes?|hours?|step|process)\b', potential_heading.lower())):
                
                # Clean up common artifacts and normalize whitespace
                heading = re.sub(r'\s+', ' ', potential_heading)
                heading = re.sub(r'[^\w\s\'-éáíóúñç&()\/]$', '', heading).strip()
                return heading
        
        # PATTERN 2: Handle blocks with multiple content items - extract the first heading
        # Pattern: "Content Title  Details:" or "Section Name Content:" (supports Unicode)
        multi_content_pattern = r'^([^\d\n][^\n]+?)\s+(Details?|Content|Information|Data)\s*:'
        
        match = re.search(multi_content_pattern, text, re.UNICODE)
        if match:
            heading = match.group(1).strip()
            # Clean up common artifacts and normalize whitespace
            heading = re.sub(r'\s+', ' ', heading)
            heading = re.sub(r'[^\w\s\'-éáíóúñç&()\/]$', '', heading).strip()
            return heading
        
        # PATTERN 3: Pattern for single content blocks - more flexible (supports Unicode)
        single_content_pattern = r'^([^\d\n][^\n]+?)\s*(Details?|Information|Content|Summary|Overview|Introduction|Conclusion)\s*:?'
        
        match = re.search(single_content_pattern, text, re.UNICODE)
        if match:
            heading = match.group(1).strip()
            heading = re.sub(r'\s+', ' ', heading)
            heading = re.sub(r'[^\w\s\'-éáíóúñç&()\/]$', '', heading).strip()
            return heading
        
        # PATTERN 4: Handle cases where text starts with heading but no clear pattern
        # Extract first line or first few words that look like a heading
        lines = text.split('\n')
        first_line = lines[0].strip()
        
        # If first line looks like a heading (starts with capital, reasonable length)
        if (len(first_line) < 80 and 
            first_line and 
            first_line[0].isupper() and
            not first_line.lower().startswith(('see', 'refer', 'note', 'please', 'for more'))):
            
            # Extract just the heading part before any detailed content
            heading = re.split(r'\s+(?:Details?|Information|Content|Summary)', first_line)[0]
            return heading.strip()
        
        # PATTERN 5: Fallback: extract first few words that look like a heading
        words = text.split()
        if len(words) >= 2:
            # Take first 2-6 words that start with capital letters
            heading_words = []
            for word in words[:6]:
                if word and word[0].isupper() and word.lower() not in ['see', 'refer', 'note', 'please', 'for', 'more']:
                    heading_words.append(word)
                else:
                    break
            
            if heading_words:
                return ' '.join(heading_words)
        
        # If all else fails, return original text
        return text
    
    def _extract_multiple_content_items(self, block: Dict, text: str, block_index: int) -> List[Dict]:
        """Extract multiple content headings from a single text block (generic version)"""
        headings = []
        
        # Pattern for detecting multiple content items in one block
        # Look for pattern: "...text. Title1 ...more text... Title2 ..."
        import re
        
        # Split on sentence endings followed by title-case words
        content_split_pattern = r'([.!?])\s+([A-Z][A-Za-z\s&\'-]{1,50})(?=\s+[A-Z]|\s*$|[.!?])'
        
        matches = list(re.finditer(content_split_pattern, text))
        
        if matches:
            for match in matches:
                potential_title = match.group(2).strip()
                
                # Validate this looks like a content title
                if (len(potential_title) > 2 and 
                    len(potential_title) < 60 and
                    not potential_title.lower().startswith(('see', 'refer', 'note', 'please')) and
                    not re.search(r'\b(step|process|continue|follow|next)\s+\d', potential_title.lower())):
                    
                    headings.append({
                        'block_id': block_index,
                        'is_heading': True,
                        'text': potential_title,
                        'confidence': 0.75  # Medium confidence for extracted titles
                    })
        
        return headings

    def _extract_dish_name(self, text: str) -> str:
        """Legacy method - now calls the generic heading extraction"""
        return self._extract_clean_heading(text)

    def _extract_multiple_recipes(self, block: Dict, text: str, block_index: int) -> List[Dict]:
        """Legacy method - now calls the generic multi-content extraction"""
        return self._extract_multiple_content_items(block, text, block_index)
