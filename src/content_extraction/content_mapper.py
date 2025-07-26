# src/content_extraction/content_mapper.py
import logging
import re
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

class ContentMapper:
    """Map extracted content to document structure"""
    
    def map_content(self, sections: List[Dict], outline: Dict) -> List[Dict]:
        """Map sections with their content"""
        mapped_sections = []
        
        for section in sections:
            mapped_section = {
                'document': section.get('document', 'unknown'),
                'title': section['title'],
                'level': section['level'],
                'page': section['page'],
                'content': section['content'],
                'metadata': self._extract_metadata(section)
            }
            
            # Add hierarchical information
            mapped_section['hierarchy'] = self._build_hierarchy(
                section, sections, outline
            )
            # src/content_extraction/content_mapper.py (continued)
            mapped_sections.append(mapped_section)
        
        return mapped_sections
    
    def _extract_metadata(self, section: Dict) -> Dict:
        """Extract metadata from section"""
        content = section.get('content', '')
        
        metadata = {
            'word_count': len(content.split()),
            'char_count': len(content),
            'paragraph_count': content.count('\n\n') + 1,
            'has_lists': self._detect_lists(content),
            'has_tables': self._detect_tables(content),
            'has_code': self._detect_code(content),
            'has_equations': self._detect_equations(content)
        }
        
        return metadata
    
    def _build_hierarchy(self, section: Dict, all_sections: List[Dict], 
                        outline: Dict) -> Dict:
        """Build hierarchical information for section"""
        hierarchy = {
            'parent': None,
            'children': [],
            'siblings': [],
            'depth': self._get_depth(section['level'])
        }
        
        # Find parent (previous section with higher level)
        section_idx = all_sections.index(section)
        
        for i in range(section_idx - 1, -1, -1):
            if self._get_depth(all_sections[i]['level']) < hierarchy['depth']:
                hierarchy['parent'] = all_sections[i]['title']
                break
        
        # Find children (next sections with lower level until same/higher level)
        for i in range(section_idx + 1, len(all_sections)):
            other_depth = self._get_depth(all_sections[i]['level'])
            
            if other_depth <= hierarchy['depth']:
                break
            elif other_depth == hierarchy['depth'] + 1:
                hierarchy['children'].append(all_sections[i]['title'])
        
        # Find siblings (sections with same level and same parent)
        section_parent = hierarchy['parent']
        for other in all_sections:
            if other != section and other['level'] == section['level']:
                # Find other's parent efficiently without recursion
                other_idx = all_sections.index(other)
                other_parent = None
                for i in range(other_idx - 1, -1, -1):
                    if self._get_depth(all_sections[i]['level']) < hierarchy['depth']:
                        other_parent = all_sections[i]['title']
                        break
                
                # Check if same parent
                if other_parent == section_parent:
                    hierarchy['siblings'].append(other['title'])
        
        return hierarchy
    
    def _get_depth(self, level: str) -> int:
        """Convert level to depth number"""
        return {'H1': 1, 'H2': 2, 'H3': 3}.get(level, 2)
    
    def _detect_lists(self, content: str) -> bool:
        """Detect if content contains lists"""
        list_patterns = [
            r'^\s*[-*•]\s+',  # Bullet points
            r'^\s*\d+\.\s+',   # Numbered lists
            r'^\s*[a-z]\)\s+', # Lettered lists
        ]
        
        for pattern in list_patterns:
            if re.search(pattern, content, re.M):
                return True
        
        return False
    
    def _detect_tables(self, content: str) -> bool:
        """Detect if content contains tables"""
        # Look for table-like patterns
        table_indicators = [
            r'\|.*\|.*\|',  # Pipe-separated
            r'┌|└|├|┤|─|│',  # Box drawing characters
            r'\t.*\t.*\t',   # Tab-separated
        ]
        
        for indicator in table_indicators:
            if re.search(indicator, content):
                return True
        
        return False
    
    def _detect_code(self, content: str) -> bool:
        """Detect if content contains code"""
        code_indicators = [
            r'```',  # Code blocks
            r'def\s+\w+\s*\(',  # Python functions
            r'function\s+\w+\s*\(',  # JavaScript functions
            r'class\s+\w+',  # Class definitions
            r'import\s+\w+',  # Import statements
            r'{[\s\S]*}',  # Curly braces blocks
        ]
        
        for indicator in code_indicators:
            if re.search(indicator, content):
                return True
        
        return False
    
    def _detect_equations(self, content: str) -> bool:
        """Detect if content contains equations"""
        equation_indicators = [
            r'\$.*\$',  # LaTeX inline math
            r'\\[a-zA-Z]+{',  # LaTeX commands
            r'[∑∫∂∇]',  # Math symbols
            r'=.*[+\-*/].*=',  # Basic equations
        ]
        
        for indicator in equation_indicators:
            if re.search(indicator, content):
                return True
        
        return False