# src/utils/output/result_builder.py
import json
from datetime import datetime
from typing import List, Dict, Any

from config.constants import MAX_OUTPUT_SECTIONS

class ResultBuilder:
    """Build the final output JSON"""
    
    def build(self, documents: List[str], persona: str, job: str,
              ranked_sections: List[Dict], subsections: List[Dict]) -> Dict:
        """Build the complete result JSON"""
        
        # Prepare metadata
        metadata = {
            "input_documents": [doc.name for doc in documents],
            "persona": persona,
            "job_to_be_done": job,
            "processing_timestamp": datetime.now().isoformat()
        }
        
        # Prepare extracted sections
        extracted_sections = []
        for i, section in enumerate(ranked_sections[:MAX_OUTPUT_SECTIONS]):
            extracted_sections.append({
                "document": section.get('document', 'Unknown'),
                "section_title": section.get('title', 'Unknown'),
                "importance_rank": i + 1,
                "page_number": section.get('page', 1)
            })
        
        # Prepare refined subsections with ACTUAL refinement
        refined_subsections = []
        seen_combinations = set()
        max_entries = 10
        
        for subsection in subsections[:20]:
            document_name = subsection.get('document', 'Unknown')
            page_num = subsection.get('page', subsection.get('page_number', 1))
            combo = f"{document_name}_{page_num}"
            
            # Skip duplicates
            if combo in seen_combinations or len(refined_subsections) >= max_entries:
                continue
            seen_combinations.add(combo)
            
            # Get the raw text and ACTUALLY refine it to be concise
            raw_text = subsection.get('text', '')
            if not raw_text:
                continue
                
            # Create concise summary (150 chars max)
            refined_text = self._create_concise_summary(raw_text)
            
            # Skip if refinement failed
            if not refined_text or len(refined_text) < 50:
                continue
            
            section_title = subsection.get('parent_section', subsection.get('section_title', 'Unknown'))
            section_id = f"{document_name}_{section_title}"
            
            refined_subsections.append({
                "section_id": section_id,
                "document": document_name,
                "section_title": section_title,
                "refined_content": refined_text,
                "page_number": page_num,
                "relevance_score": subsection.get('relevance_score', 0.0)
            })
        
        # Build final result with correct structure
        result = {
            "metadata": metadata,
            "extracted_sections": extracted_sections,
            "refined_subsections": refined_subsections  # This is the correct field name
        }
        
        return result
    
    def _create_concise_summary(self, text: str) -> str:
        """Create a concise, readable summary of the text"""
        if not text:
            return ""
        
        # Clean the text first
        text = self._clean_text(text)
        
        # For very long text, extract only the most relevant parts
        if len(text) > 1000:
            text = self._extract_most_relevant_content(text)
        
        # Split into sentences and extract key ones
        sentences = self._split_into_sentences(text)
        key_sentences = self._extract_key_sentences(sentences)
        
        # Combine and ensure readability
        summary = ' '.join(key_sentences)
        
        # Ensure summary is concise - AGGRESSIVE trimming for college trip planning
        if len(summary) > 150:
            summary = self._trim_to_length(summary, 150)
        
        # Final cleanup and validation
        summary = summary.strip()
        
        # Ensure it ends properly
        if summary and not summary.endswith('.'):
            if len(summary) < 147:
                summary += '.'
            else:
                summary = summary[:147] + '...'
        
        return summary
    
    def _extract_most_relevant_content(self, text: str) -> str:
        """Extract the most relevant content from long text"""
        import re
        
        # Look for sections that contain travel-relevant information
        travel_patterns = [
            r'[^.]*(?:attractions?|activities|restaurants?|hotels?|accommodation)[^.]*\.',
            r'[^.]*(?:visit|experience|explore|discover|enjoy|popular|famous)[^.]*\.',
            r'[^.]*(?:must(?:\s+|-)?(?:visit|see|try|do))[^.]*\.',
            r'[^.]*(?:tips?|guide|recommended|best|top)[^.]*\.',
            r'[^.]*(?:things to do|places to stay|where to eat|how to get)[^.]*\.',
            r'[^.]*(?:cost|price|opening hours|admission|booking)[^.]*\.'
        ]
        
        relevant_parts = []
        
        for pattern in travel_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            relevant_parts.extend(matches[:2])  # Max 2 matches per pattern
        
        if relevant_parts:
            return ' '.join(relevant_parts[:8])  # Max 8 total relevant sentences
        
        # If no travel-specific content found, take the first few sentences
        sentences = self._split_into_sentences(text)
        return ' '.join(sentences[:4])
    
    def _clean_text(self, text: str) -> str:
        """Clean text of formatting issues"""
        import re
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove reference markers [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        
        # Remove citation patterns
        text = re.sub(r'\([A-Z][a-z]+\s+et\s+al\.\s*,\s*\d{4}\)', '', text)
        
        # Fix common OCR errors
        text = text.replace('ﬀ', 'ff').replace('ﬁ', 'fi').replace('ﬂ', 'fl')
        
        # Remove URLs
        text = re.sub(r'http[s]?://[^\s]+', '', text)
        
        return text
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        import re
        
        # Split on sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter out very short fragments
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        return sentences
    
    def _extract_key_sentences(self, sentences: List[str]) -> List[str]:
        """Extract the most important sentences"""
        if not sentences:
            return []
        
        key_sentences = []
        
        # Priority keywords for travel content
        high_priority = [
            'attractions', 'activities', 'restaurants', 'hotels', 'accommodation',
            'must visit', 'popular', 'famous', 'best', 'top', 'recommended',
            'things to do', 'places to stay', 'where to eat', 'experiences'
        ]
        
        medium_priority = [
            'guide', 'tips', 'discover', 'explore', 'enjoy', 'highlights',
            'history', 'culture', 'museum', 'festival', 'local'
        ]
        
        # Score sentences
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = 0
            sentence_lower = sentence.lower()
            
            # High priority keywords (3 points each)
            for keyword in high_priority:
                if keyword in sentence_lower:
                    score += 3
            
            # Medium priority keywords (1 point each)
            for keyword in medium_priority:
                if keyword in sentence_lower:
                    score += 1
            
            # Prefer shorter, more focused sentences
            if 50 <= len(sentence) <= 200:
                score += 2
            elif len(sentence) < 50:
                score -= 1
            
            # Slight preference for earlier sentences (introduction context)
            if i < 3:
                score += 1
            
            scored_sentences.append((sentence, score))
        
        # Sort by score and select top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Take top 3-4 sentences with scores > 0
        for sentence, score in scored_sentences[:4]:
            if score > 0:
                key_sentences.append(sentence)
        
        # If we don't have enough good sentences, add the first sentence for context
        if len(key_sentences) < 2 and sentences:
            if sentences[0] not in key_sentences:
                key_sentences.insert(0, sentences[0])
        
        return key_sentences[:3]  # Max 3 sentences
    
    def _trim_to_length(self, text: str, max_length: int) -> str:
        """Trim text to maximum length at sentence boundary"""
        if len(text) <= max_length:
            return text
        
        # Find the last complete sentence within the limit
        trimmed = text[:max_length]
        last_period = trimmed.rfind('.')
        
        if last_period > max_length * 0.7:  # If we can keep most of the text
            return text[:last_period + 1]
        else:
            return trimmed + "..."
    
    def _get_accurate_page_number(self, subsection: Dict) -> int:
        """Get accurate page number for subsection"""
        # If subsection has specific page info, use it
        if 'page' in subsection and isinstance(subsection['page'], int):
            return subsection['page']
        
        # If subsection has page range info, use the first page
        if 'page_range' in subsection:
            page_range = subsection['page_range']
            if isinstance(page_range, list) and page_range:
                return page_range[0]
        
        # Fall back to parent section page
        if 'parent_page' in subsection:
            return subsection['parent_page']
        
        # Default fallback
        return 1
    
    def _is_well_refined(self, text: str) -> bool:
        """Check if text appears to be well-refined"""
        if not text or len(text) < 50:
            return False
        
        # Check if text is too long (likely unprocessed)
        if len(text) > 800:
            return False
        
        # Check if text has good sentence structure
        import re
        sentences = re.split(r'[.!?]', text)
        if len(sentences) < 2:
            return False
        
        # Check if it contains travel-relevant keywords
        travel_keywords = [
            'attractions', 'restaurants', 'hotels', 'activities', 'visit',
            'experience', 'explore', 'discover', 'enjoy', 'popular'
        ]
        
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in travel_keywords if keyword in text_lower)
        
        # Should have at least some travel relevance
        return keyword_count > 0