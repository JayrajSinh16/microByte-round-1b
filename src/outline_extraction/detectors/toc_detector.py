# src/outline_extraction/detectors/toc_detector.py
import re
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class TOCDetector:
    """Detect and parse table of contents"""
    
    def __init__(self):
        self.toc_patterns = [
            # Page number patterns
            re.compile(r'(.+?)\s*\.{3,}\s*(\d+)\s*$'),  # Title ... 123
            re.compile(r'(.+?)\s+(\d+)\s*$'),           # Title 123
            re.compile(r'^(\d+\.?\d*)\s+(.+?)\s+(\d+)$'), # 1.2 Title 123
            
            # TOC headers
            re.compile(r'table\s+of\s+contents', re.I),
            re.compile(r'contents', re.I),
            re.compile(r'index', re.I)
        ]
    
    def detect(self, blocks: List[Dict]) -> Optional[Dict]:
        """Detect table of contents in document"""
        # Look for TOC header
        toc_start = self._find_toc_header(blocks)
        
        if toc_start is None:
            # Try to detect TOC by pattern
            toc_entries = self._detect_by_pattern(blocks)
            if toc_entries:
                return {
                    'found': True,
                    'entries': toc_entries,
                    'source': 'pattern'
                }
        else:
            # Parse TOC starting from header
            toc_entries = self._parse_toc(blocks, toc_start)
            return {
                'found': True,
                'entries': toc_entries,
                'source': 'header'
            }
        
        return None
    
    def _find_toc_header(self, blocks: List[Dict]) -> Optional[int]:
        """Find TOC header block"""
        for i, block in enumerate(blocks[:50]):  # Check first 50 blocks
            text = block.get('text', '').strip().lower()
            
            for pattern in self.toc_patterns[-3:]:  # Header patterns
                if pattern.search(text):
                    return i
        
        return None
    
    def _detect_by_pattern(self, blocks: List[Dict]) -> List[Dict]:
        """Detect TOC entries by pattern matching"""
        entries = []
        consecutive_matches = 0
        
        for block in blocks[:100]:  # Check first 100 blocks
            text = block.get('text', '').strip()
            
            # Try to match TOC patterns
            for pattern in self.toc_patterns[:-3]:  # Entry patterns
                match = pattern.match(text)
                if match:
                    if len(match.groups()) == 2:
                        title, page = match.groups()
                    else:
                        # Handle numbered entries
                        number, title, page = match.groups()
                        title = f"{number} {title}"
                    
                    try:
                        page_num = int(page)
                        entries.append({
                            'title': title.strip(),
                            'page': page_num,
                            'block_id': block.get('id'),
                            'level': self._detect_level(title)
                        })
                        consecutive_matches += 1
                        break
                    except ValueError:
                        pass
            else:
                # No match
                if consecutive_matches > 3:
                    # Likely end of TOC
                    break
                consecutive_matches = 0
        
        # Return entries if we found a reasonable number
        return entries if len(entries) > 3 else []
    
    def _parse_toc(self, blocks: List[Dict], start_idx: int) -> List[Dict]:
        """Parse TOC starting from header"""
        entries = []
        
        # Start after header
        for i in range(start_idx + 1, min(start_idx + 100, len(blocks))):
            block = blocks[i]
            text = block.get('text', '').strip()
            # Check if this looks like a TOC entry
            entry = self._parse_toc_entry(text)
            if entry:
                entry['block_id'] = block.get('id')
                entries.append(entry)
            elif entries and len(entries) > 3:
                # Likely end of TOC if we already found entries
                break
        
        return entries
    
    def _parse_toc_entry(self, text: str) -> Optional[Dict]:
        """Parse a single TOC entry"""
        # Try each pattern
        for pattern in self.toc_patterns[:-3]:
            match = pattern.match(text)
            if match:
                try:
                    if len(match.groups()) == 2:
                        title, page = match.groups()
                    else:
                        number, title, page = match.groups()
                        title = f"{number} {title}"
                    
                    page_num = int(page)
                    return {
                        'title': title.strip(),
                        'page': page_num,
                        'level': self._detect_level(title)
                    }
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _detect_level(self, title: str) -> str:
        """Detect heading level from TOC entry"""
        # Count leading numbers/dots to determine level
        match = re.match(r'^(\d+(?:\.\d+)*)', title)
        if match:
            number = match.group(1)
            depth = number.count('.') + 1
            
            if depth == 1:
                return 'H1'
            elif depth == 2:
                return 'H2'
            else:
                return 'H3'
        
        # Check indentation or other patterns
        if title.startswith('    '):
            return 'H3'
        elif title.startswith('  '):
            return 'H2'
        
        return 'H1'