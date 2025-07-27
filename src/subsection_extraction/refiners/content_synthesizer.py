# src/subsection_extraction/refiners/content_synthesizer.py
import re
from typing import List, Dict, Set, Optional
from collections import defaultdict

class ContentSynthesizer:
    """Advanced content synthesizer for high-quality, natural text generation"""
    
    def __init__(self):
        # Sentence quality indicators
        self.quality_indicators = [
            r'\b(?:visit|explore|enjoy|experience|try|discover)\s+[A-Z][^.!?]*',  # Action + proper noun
            r'\b(?:best|top|recommended|popular|famous)\s+[^.!?]*',  # Quality descriptions
            r'\b(?:located|situated|address|phone|contact|hours)\s*:?\s*[^.!?]*',  # Practical info
            r'\b\d+(?:\.\d+)?\s*(?:km|miles|hours|minutes|euros|\$|pounds)\b[^.!?]*',  # Specific measurements
            r'\b[A-Z][a-zA-Z\s-]+(?:Beach|Bay|Island|City|Town|Village|Restaurant|Hotel|Bar|Club)\b[^.!?]*'  # Specific places
        ]
        
        # Patterns to avoid in synthesis
        self.avoid_patterns = [
            r'^in conclusion',
            r'^to summarize',
            r'^as mentioned',
            r'^it should be noted',
            r'^furthermore',
            r'the above mentioned',
            r'aforementioned'
        ]

    def synthesize_subsections(self, subsections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Main interface for synthesizing subsections"""
        return self.synthesize(subsections, query_profile)
    
    def synthesize(self, sections: List[Dict], query_profile: Dict = None) -> List[Dict]:
        """STEP 3: Execute High-Quality Synthesis"""
        synthesized = []
        
        for section in sections:
            content = section.get('content', '') or section.get('refined_text', '')
            if not content or len(content.strip()) < 100:  # Skip very short content
                continue
            
            # Extract high-quality sentences
            quality_sentences = self._extract_quality_sentences(content)
            
            if quality_sentences:
                # Synthesize into natural, coherent paragraph
                synthesized_text = self._create_natural_synthesis(quality_sentences, query_profile)
                
                if synthesized_text and len(synthesized_text) > 50:
                    synthesized_section = section.copy()
                    synthesized_section['refined_text'] = synthesized_text
                    synthesized.append(synthesized_section)
        
        return synthesized
    
    def _extract_quality_sentences(self, content: str) -> List[str]:
        """Extract the most relevant, actionable sentences from content"""
        sentences = self._split_sentences(content)
        quality_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
                
            quality_score = self._calculate_sentence_quality(sentence)
            if quality_score > 0.3:  # Only keep high-quality sentences
                quality_sentences.append((sentence, quality_score))
        
        # Sort by quality and return top sentences
        quality_sentences.sort(key=lambda x: x[1], reverse=True)
        return [sent[0] for sent in quality_sentences[:8]]  # Top 8 sentences max
    
    def _split_sentences(self, content: str) -> List[str]:
        """Split content into individual sentences"""
        # Clean up the content first
        content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        content = re.sub(r'([.!?])\s*([A-Z])', r'\1\n\2', content)  # Split on sentence boundaries
        
        sentences = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                # Further split on semicolons and other sentence-like boundaries
                parts = re.split(r'[;]\s*(?=[A-Z])', line)
                sentences.extend(parts)
        
        return sentences
    
    def _calculate_sentence_quality(self, sentence: str) -> float:
        """Calculate how valuable/actionable a sentence is"""
        score = 0.0
        
        # Check for quality indicators
        for pattern in self.quality_indicators:
            if re.search(pattern, sentence, re.IGNORECASE):
                score += 0.3
        
        # Boost for specific information (names, numbers, locations)
        if re.search(r'\b[A-Z][a-zA-Z\s-]+(?:Beach|Bay|Restaurant|Hotel|Bar|Club|Museum|Park)\b', sentence):
            score += 0.4  # Specific place names
        
        if re.search(r'\b\d+', sentence):
            score += 0.2  # Contains numbers
        
        if re.search(r'\b(?:address|phone|hours|price|cost|contact)\s*:', sentence, re.IGNORECASE):
            score += 0.5  # Practical information
        
        # Penalize for generic/low-value content
        for pattern in self.avoid_patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                score -= 0.4
        
        # Penalize very generic statements
        generic_words = ['general', 'various', 'many', 'some', 'several', 'different', 'multiple']
        generic_count = sum(1 for word in generic_words if word in sentence.lower())
        if generic_count > 2:
            score -= 0.3
        
        return max(score, 0.0)
    
    def _create_natural_synthesis(self, sentences: List[str], query_profile: Dict = None) -> str:
        """Combine quality sentences into natural, coherent text"""
        if not sentences:
            return ""
        
        # Group sentences by topic/theme for better organization
        grouped_sentences = self._group_sentences_by_theme(sentences)
        
        # Build coherent paragraphs
        synthesis_parts = []
        
        for theme, theme_sentences in grouped_sentences.items():
            if len(theme_sentences) >= 2:  # Only include themes with multiple sentences
                # Rewrite and combine sentences to eliminate repetition
                coherent_text = self._create_coherent_text(theme_sentences)
                if coherent_text:
                    synthesis_parts.append(coherent_text)
        
        # If we don't have grouped content, fallback to best individual sentences
        if not synthesis_parts and sentences:
            synthesis_parts.append(self._create_coherent_text(sentences[:4]))
        
        return ' '.join(synthesis_parts)
    
    def _group_sentences_by_theme(self, sentences: List[str]) -> Dict[str, List[str]]:
        """Group sentences by common themes/topics"""
        themes = {
            'locations': [],
            'activities': [],
            'dining': [],
            'practical': [],
            'other': []
        }
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Classify by content theme
            if any(word in sentence_lower for word in ['restaurant', 'food', 'dining', 'cuisine', 'bar', 'wine', 'cooking']):
                themes['dining'].append(sentence)
            elif any(word in sentence_lower for word in ['beach', 'coast', 'island', 'city', 'town', 'village', 'location']):
                themes['locations'].append(sentence)
            elif any(word in sentence_lower for word in ['activity', 'visit', 'explore', 'enjoy', 'experience', 'adventure']):
                themes['activities'].append(sentence)
            elif any(word in sentence_lower for word in ['address', 'hours', 'price', 'contact', 'phone', 'cost']):
                themes['practical'].append(sentence)
            else:
                themes['other'].append(sentence)
        
        # Remove empty themes
        return {k: v for k, v in themes.items() if v}
    
    def _create_coherent_text(self, sentences: List[str]) -> str:
        """Rewrite sentences into coherent, natural text"""
        if not sentences:
            return ""
        
        # Combine information from multiple sentences intelligently
        combined_info = self._extract_key_information(sentences)
        
        # Generate natural text from the extracted information
        if combined_info['locations'] and combined_info['activities']:
            # Create activity-focused synthesis
            locations_text = ', '.join(combined_info['locations'][:3])
            activities_text = ', '.join(combined_info['activities'][:3])
            result = f"The South of France offers {activities_text} in locations such as {locations_text}."
            
            # Add specific details if available
            if combined_info['details']:
                details_text = '; '.join(combined_info['details'][:2])
                result += f" {details_text}."
                
        elif combined_info['locations']:
            # Location-focused synthesis
            locations_text = ', '.join(combined_info['locations'][:4])
            result = f"Key destinations include {locations_text}."
            
            if combined_info['details']:
                details_text = ' '.join(combined_info['details'][:2])
                result += f" {details_text}."
                
        elif combined_info['activities']:
            # Activity-focused synthesis
            activities_text = ', '.join(combined_info['activities'][:4])
            result = f"Popular activities include {activities_text}."
            
            if combined_info['details']:
                details_text = ' '.join(combined_info['details'][:2])
                result += f" {details_text}."
        else:
            # Fallback to best sentence
            result = sentences[0] if sentences else ""
        
        return result.strip()
    
    def _extract_key_information(self, sentences: List[str]) -> Dict[str, List[str]]:
        """Extract key information elements from sentences"""
        info = {
            'locations': [],
            'activities': [],
            'details': []
        }
        
        for sentence in sentences:
            # Extract location names
            location_matches = re.findall(r'\b([A-Z][a-zA-Z\s-]+(?:Beach|Bay|Island|City|Town|Village|Restaurant|Hotel|Bar|Club|Museum|Park))\b', sentence)
            info['locations'].extend(location_matches)
            
            # Extract activities/actions
            activity_matches = re.findall(r'\b(?:visit|explore|enjoy|experience|try|discover)\s+([^.!?,:;]+)', sentence, re.IGNORECASE)
            info['activities'].extend([match.strip() for match in activity_matches])
            
            # Extract detailed information
            if any(word in sentence.lower() for word in ['address', 'hours', 'price', 'phone', 'contact']):
                info['details'].append(sentence.strip())
        
        # Remove duplicates and clean up
        info['locations'] = list(dict.fromkeys(info['locations']))  # Remove duplicates while preserving order
        info['activities'] = list(dict.fromkeys(info['activities']))
        info['details'] = list(dict.fromkeys(info['details']))
        
        return info
