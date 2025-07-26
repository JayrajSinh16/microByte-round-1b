# src/subsection_extraction/refiners/text_refiner.py
import re
from typing import List

class TextRefiner:
    """Refine extracted text for presentation"""
    
    def refine(self, text: str) -> str:
        """ULTRA-AGGRESSIVE refinement for college trip planning - ONE sentence max"""
        if not text:
            return ""
        
        # Force ultra-concise summaries for 4-day college trip
        sentences = text.split('. ')
        
        # Ultra-focused travel keywords for college friends
        action_words = ['visit', 'explore', 'try', 'experience', 'enjoy', 'see', 'go to', 'check out']
        must_words = ['must', 'best', 'top', 'famous', 'popular', 'recommended', 'perfect']
        place_words = ['attractions', 'restaurants', 'activities', 'places', 'spots', 'destinations']
        
        # Find the SINGLE best sentence for college trip planning
        best_sentence = None
        max_score = 0
        
        for sentence in sentences[:5]:  # Only check first 5 sentences
            sentence = sentence.strip()
            if len(sentence) < 40:  # Skip very short fragments
                continue
                
            score = 0
            sentence_lower = sentence.lower()
            
            # Score based on travel relevance
            for word in action_words:
                if word in sentence_lower:
                    score += 5
            for word in must_words:
                if word in sentence_lower:
                    score += 3
            for word in place_words:
                if word in sentence_lower:
                    score += 2
            
            # Prefer shorter, actionable sentences
            if len(sentence) < 120:
                score += 2
            
            if score > max_score:
                max_score = score
                best_sentence = sentence
        
        # Fallback: if no good sentence found, take first substantial one
        if not best_sentence:
            for sentence in sentences[:3]:
                sentence = sentence.strip()
                if len(sentence) > 40:
                    best_sentence = sentence
                    break
        
        # Final result: exactly one sentence, max 150 characters
        if best_sentence:
            result = best_sentence + '.'
            if len(result) > 150:
                result = result[:147] + '...'
            return result
        
        result = text[:100] + '...'  # Emergency fallback
        return result
    
    def _clean_and_normalize(self, text: str) -> str:
        """Clean and normalize text"""
        import re
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove reference markers and citations
        text = re.sub(r'\[\d+\]', '', text)
        text = re.sub(r'\([A-Z][a-z]+\s+et\s+al\.\s*,\s*\d{4}\)', '', text)
        
        # Fix common OCR issues
        text = text.replace('ﬀ', 'ff').replace('ﬁ', 'fi').replace('ﬂ', 'fl')
        
        # Remove URLs and email addresses
        text = re.sub(r'http[s]?://[^\s]+', '', text)
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text)
        
        return text.strip()
    
    def _extract_key_information(self, text: str) -> str:
        """Extract the most relevant information"""
        import re
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
        
        if not sentences:
            return text
        
        key_sentences = []
        
        # Priority keywords for travel content
        high_priority = [
            'attractions', 'activities', 'restaurants', 'hotels', 'accommodation',
            'tips', 'guide', 'recommended', 'must visit', 'popular', 'famous',
            'best', 'top', 'highlights', 'experiences', 'things to do',
            'places to stay', 'where to eat', 'how to get', 'cost', 'price',
            'opening hours', 'admission', 'booking', 'reservation'
        ]
        
        medium_priority = [
            'history', 'culture', 'architecture', 'museum', 'monument',
            'festival', 'event', 'tradition', 'local', 'authentic',
            'nearby', 'walking distance', 'transport', 'location'
        ]
        
        # Score sentences based on keyword presence
        scored_sentences = []
        for sentence in sentences:
            score = 0
            sentence_lower = sentence.lower()
            
            # High priority keywords
            for keyword in high_priority:
                if keyword in sentence_lower:
                    score += 3
            
            # Medium priority keywords
            for keyword in medium_priority:
                if keyword in sentence_lower:
                    score += 1
            
            # Bonus for first sentence (context)
            if sentence == sentences[0]:
                score += 2
            
            scored_sentences.append((sentence, score))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Select top sentences but maintain some order
        selected = []
        
        # Always include first sentence if it's decent
        if sentences and scored_sentences[0][0] != sentences[0] and scored_sentences[0][1] > 0:
            selected.append(sentences[0])
        
        # Add top scored sentences
        for sentence, score in scored_sentences[:4]:
            if score > 0 and sentence not in selected:
                selected.append(sentence)
        
        # If we don't have enough content, add a few more sentences
        if len(selected) < 2:
            for sentence in sentences[:3]:
                if sentence not in selected:
                    selected.append(sentence)
                    if len(selected) >= 2:
                        break
        
        return ' '.join(selected)
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup and formatting"""
        if not text:
            return text
        
        # Fix spacing around punctuation
        text = self._fix_spacing(text)
        
        # Ensure proper capitalization
        text = self._capitalize_first(text)
        
        # Limit length
        if len(text) > 600:
            text = self._trim_text(text, 600)
        
        # Ensure text ends properly
        if text and text[-1] not in '.!?':
            # Find last complete sentence
            import re
            matches = list(re.finditer(r'[.!?]', text))
            if matches:
                last_match = matches[-1]
                text = text[:last_match.end()]
        
        return text
    
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
    
    def _trim_text(self, text: str, max_length: int = 1000) -> str:
        """Trim text to reasonable length"""
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