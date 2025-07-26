# src/subsection_extraction/extractors/chunk_extractor.py
import re
from typing import List, Dict, Tuple
from nltk.tokenize import sent_tokenize, word_tokenize

from config.constants import MIN_SUBSECTION_LENGTH, SUBSECTIONS_PER_SECTION

class ChunkExtractor:
    """Extract meaningful chunks from sections"""
    
    def __init__(self):
        self.paragraph_separators = ['\n\n', '\n\r\n', '\r\n\r\n']
        self.min_sentences = 3
        self.max_sentences = 10
    
    def extract_chunks(self, section: Dict) -> List[Dict]:
        """Extract chunks from a section"""
        content = section.get('content', '')
        if not content:
            return []
        
        # Try different extraction strategies
        chunks = []
        
        # Strategy 1: Paragraph-based extraction
        paragraph_chunks = self._extract_by_paragraphs(content)
        chunks.extend(paragraph_chunks)
        
        # Strategy 2: Semantic chunking (if paragraphs are too long)
        if not chunks or all(len(c['text'].split()) > 300 for c in chunks):
            semantic_chunks = self._extract_by_semantics(content)
            chunks.extend(semantic_chunks)
        
        # Strategy 3: Sliding window (fallback)
        if not chunks:
            window_chunks = self._extract_by_window(content)
            chunks.extend(window_chunks)
        
        # Score and rank chunks
        scored_chunks = self._score_chunks(chunks, section)
        
        # Return top chunks
        return scored_chunks[:SUBSECTIONS_PER_SECTION]
    
    def _extract_by_paragraphs(self, content: str) -> List[Dict]:
        """Extract chunks based on paragraph boundaries"""
        chunks = []
        
        # Split by paragraph separators
        paragraphs = content
        for separator in self.paragraph_separators:
            paragraphs = paragraphs.replace(separator, '\n\n')
        
        paragraphs = [p.strip() for p in paragraphs.split('\n\n') if p.strip()]
        
        for i, para in enumerate(paragraphs):
            word_count = len(para.split())
            
            # Skip very short paragraphs
            if word_count < MIN_SUBSECTION_LENGTH:
                continue
            
            # Merge short consecutive paragraphs
            if word_count < MIN_SUBSECTION_LENGTH * 2 and i < len(paragraphs) - 1:
                para = para + '\n\n' + paragraphs[i + 1]
            
            chunks.append({
                'text': para,
                'type': 'paragraph',
                'position': i / len(paragraphs),  # Relative position
                'word_count': len(para.split())
            })
        
        return chunks
    
    def _extract_by_semantics(self, content: str) -> List[Dict]:
        """Extract chunks based on semantic boundaries"""
        chunks = []
        sentences = sent_tokenize(content)
        
        if not sentences:
            return chunks
        
        current_chunk = []
        current_words = 0
        
        for i, sentence in enumerate(sentences):
            sentence_words = len(sentence.split())
            
            # Check if adding this sentence exceeds limits
            if current_chunk and (
                len(current_chunk) >= self.max_sentences or
                current_words + sentence_words > 200
            ):
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'type': 'semantic',
                    'position': (i - len(current_chunk)) / len(sentences),
                    'word_count': current_words
                })
                
                current_chunk = []
                current_words = 0
            
            current_chunk.append(sentence)
            current_words += sentence_words
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'type': 'semantic',
                'position': (len(sentences) - len(current_chunk)) / len(sentences),
                'word_count': current_words
            })
        
        return chunks
    
    def _extract_by_window(self, content: str) -> List[Dict]:
        """Extract chunks using sliding window"""
        chunks = []
        sentences = sent_tokenize(content)
        
        if len(sentences) < self.min_sentences:
            return [{
                'text': content,
                'type': 'window',
                'position': 0.5,
                'word_count': len(content.split())
            }]
        
        window_size = min(self.max_sentences, max(self.min_sentences, len(sentences) // 3))
        step_size = max(1, window_size // 2)
        
        for i in range(0, len(sentences) - window_size + 1, step_size):
            window_text = ' '.join(sentences[i:i + window_size])
            
            chunks.append({
                'text': window_text,
                'type': 'window',
                'position': (i + window_size / 2) / len(sentences),
                'word_count': len(window_text.split())
            })
        
        return chunks
    
    def _score_chunks(self, chunks: List[Dict], section: Dict) -> List[Dict]:
        """Score and rank chunks based on relevance indicators"""
        for chunk in chunks:
            score = 0.0
            
            # Position score (earlier chunks often more important)
            score += (1 - chunk['position']) * 0.3
            
            # Length score (prefer optimal length)
            word_count = chunk['word_count']
            if 50 <= word_count <= 150:
                score += 0.3
            elif 150 < word_count <= 250:
                score += 0.2
            else:
                score += 0.1
            
            # Content indicators
            text_lower = chunk['text'].lower()
            
            # Key phrases that indicate importance
            importance_indicators = [
                'important', 'key', 'main', 'primary', 'significant',
                'note that', 'notably', 'in particular', 'specifically'
            ]
            
            indicator_count = sum(1 for ind in importance_indicators if ind in text_lower)
            score += min(indicator_count * 0.1, 0.3)
            
            # Check for data/examples
            if any(pattern in text_lower for pattern in ['for example', 'e.g.', 'such as', 'including']):
                score += 0.1
            
            # Check for conclusions/summaries
            if any(pattern in text_lower for pattern in ['therefore', 'thus', 'in summary', 'conclude']):
                score += 0.15
            
            chunk['relevance_score'] = score
            
            # IMPORTANT: Preserve parent section metadata
            chunk['document'] = section.get('document', 'Unknown')
            chunk['parent_section'] = section.get('title', 'Unknown')
            chunk['page'] = section.get('page', 1)
        
        # Sort by score
        chunks.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return chunks