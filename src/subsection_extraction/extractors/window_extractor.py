# src/subsection_extraction/extractors/window_extractor.py
from typing import List, Dict
import re

class WindowExtractor:
    """Extract subsections using sliding window approach"""
    
    def __init__(self):
        self.window_size = 150  # words
        self.step_size = 75     # 50% overlap
        self.min_window_size = 50
    
    def extract(self, section: Dict, query_profile: Dict) -> List[Dict]:
        """Extract using sliding window"""
        content = section.get('content', '')
        words = content.split()
        
        if len(words) < self.min_window_size:
            return [{
                'text': content,
                'type': 'full_section',
                'position': 0.5,
                'parent_section': section.get('title', ''),
                'document': section.get('document', ''),
                'page': section.get('page', 1),
                'extraction_method': 'full'
            }]
        
        # Get query terms for focused extraction
        query_terms = self._get_query_terms(query_profile)
        
        # Find high-relevance windows
        windows = []
        for i in range(0, len(words) - self.window_size + 1, self.step_size):
            window_words = words[i:i + self.window_size]
            window_text = ' '.join(window_words)
            
            # Calculate relevance
            relevance = self._calculate_relevance(window_text, query_terms)
            
            windows.append({
                'text': window_text,
                'type': 'window',
                'position': (i + self.window_size/2) / len(words),
                'relevance': relevance,
                'start_idx': i,
                'end_idx': i + self.window_size,
                'parent_section': section.get('title', ''),
                'document': section.get('document', ''),
                'page': section.get('page', 1),
                'extraction_method': 'sliding_window'
            })
        
        # Sort by relevance and merge overlapping high-relevance windows
        windows.sort(key=lambda w: w['relevance'], reverse=True)
        merged = self._merge_overlapping_windows(windows, words)
        
        return merged
    
    def _get_query_terms(self, query_profile: Dict) -> List[str]:
        """Extract query terms from profile"""
        terms = []
        
        if 'query' in query_profile:
            terms.extend(query_profile['query'].get('primary_terms', []))
            terms.extend(query_profile['query'].get('must_have_terms', []))
        
        return list(set(terms))
    
    def _calculate_relevance(self, text: str, query_terms: List[str]) -> float:
        """Calculate relevance of window to query"""
        if not query_terms:
            return 0.5
        
        text_lower = text.lower()
        matches = sum(1 for term in query_terms if term.lower() in text_lower)
        
        return matches / len(query_terms)
    
    def _merge_overlapping_windows(self, windows: List[Dict], 
                                  words: List[str]) -> List[Dict]:
        """Merge overlapping high-relevance windows"""
        if not windows:
            return []
        
        # Take top windows
        top_windows = windows[:10]
        
        # Sort by position
        top_windows.sort(key=lambda w: w['start_idx'])
        
        merged = []
        current = top_windows[0].copy()
        
        for window in top_windows[1:]:
            # Check overlap
            if window['start_idx'] <= current['end_idx']:
                # Merge
                current['end_idx'] = max(current['end_idx'], window['end_idx'])
                current['relevance'] = max(current['relevance'], window['relevance'])
            else:
                # Save current and start new
                current['text'] = ' '.join(words[current['start_idx']:current['end_idx']])
                merged.append(current)
                current = window.copy()
        
        # Add last window
        current['text'] = ' '.join(words[current['start_idx']:current['end_idx']])
        merged.append(current)
        
        return merged