# src/subsection_extraction/extractors/paragraph_extractor.py
import re
from typing import List, Dict

class ParagraphExtractor:
    """Extract subsections based on paragraph boundaries"""
    
    def __init__(self):
        self.min_paragraph_length = 50
        self.max_paragraph_length = 1000
    
    def extract(self, section: Dict) -> List[Dict]:
        """Extract paragraph-based subsections"""
        content = section.get('content', '')
        
        # Split into paragraphs
        paragraphs = self._split_paragraphs(content)
        
        subsections = []
        for i, para in enumerate(paragraphs):
            if self.min_paragraph_length <= len(para) <= self.max_paragraph_length:
                subsection = {
                    'text': para,
                    'type': 'paragraph',
                    'position': i / len(paragraphs),
                    'parent_section': section.get('title', ''),
                    'document': section.get('document', ''),
                    'page': section.get('page', 1),
                    'extraction_method': 'paragraph'
                }
                subsections.append(subsection)
            elif len(para) > self.max_paragraph_length:
                # Split long paragraphs
                split_subs = self._split_long_paragraph(para, section, i, len(paragraphs))
                subsections.extend(split_subs)
        
        return subsections
    
    def _split_paragraphs(self, content: str) -> List[str]:
        """Split content into paragraphs"""
        # Try multiple paragraph separators
        if '\n\n' in content:
            paragraphs = content.split('\n\n')
        elif '\r\n\r\n' in content:
            paragraphs = content.split('\r\n\r\n')
        else:
            # Fall back to single newline
            paragraphs = content.split('\n')
        
        # Clean and filter
        cleaned = []
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 20:  # Minimum length
                cleaned.append(para)
        
        return cleaned
    
    def _split_long_paragraph(self, para: str, section: Dict, 
                            para_idx: int, total_paras: int) -> List[Dict]:
        """Split a long paragraph into smaller chunks"""
        sentences = self._split_sentences(para)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.max_paragraph_length and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'type': 'paragraph_split',
                    'position': para_idx / total_paras,
                    'parent_section': section.get('title', ''),
                    'document': section.get('document', ''),
                    'page': section.get('page', 1),
                    'extraction_method': 'paragraph_split'
                })
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'type': 'paragraph_split',
                'position': para_idx / total_paras,
                'parent_section': section.get('title', ''),
                'document': section.get('document', ''),
                'page': section.get('page', 1),
                'extraction_method': 'paragraph_split'
            })
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]