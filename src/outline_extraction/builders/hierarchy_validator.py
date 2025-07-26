# src/outline_extraction/builders/hierarchy_validator.py
import logging
from typing import List, Dict
from collections import Counter

logger = logging.getLogger(__name__)

class HierarchyValidator:
    """Validate and fix heading hierarchy"""
    
    def validate_and_fix(self, headings: List[Dict]) -> List[Dict]:
        """Validate heading hierarchy and fix issues"""
        if not headings:
            return headings
        
        # Check for hierarchy issues
        issues = self._detect_issues(headings)
        
        if issues['has_issues']:
            logger.info(f"Detected hierarchy issues: {issues}")
            headings = self._fix_hierarchy(headings, issues)
        
        return headings
    
    def _detect_issues(self, headings: List[Dict]) -> Dict:
        """Detect hierarchy issues"""
        issues = {
            'has_issues': False,
            'missing_h1': False,
            'level_jumps': [],
            'inconsistent_numbering': False,
            'orphaned_headings': []
        }
        
        # Check for H1
        h1_count = sum(1 for h in headings if h['level'] == 'H1')
        if h1_count == 0:
            issues['missing_h1'] = True
            issues['has_issues'] = True
        
        # Check for level jumps
        for i in range(len(headings) - 1):
            current_level = self._level_to_number(headings[i]['level'])
            next_level = self._level_to_number(headings[i + 1]['level'])
            
            # Jump of more than 1 level
            if next_level > current_level + 1:
                issues['level_jumps'].append(i + 1)
                issues['has_issues'] = True
        
        # Check for orphaned H3s (H3 without H2 parent)
        current_h1 = None
        current_h2 = None
        
        for i, heading in enumerate(headings):
            if heading['level'] == 'H1':
                current_h1 = i
                current_h2 = None
            elif heading['level'] == 'H2':
                current_h2 = i
            elif heading['level'] == 'H3':
                if current_h2 is None:
                    issues['orphaned_headings'].append(i)
                    issues['has_issues'] = True
        
        return issues
    
    def _fix_hierarchy(self, headings: List[Dict], issues: Dict) -> List[Dict]:
        """Fix detected hierarchy issues"""
        fixed_headings = headings.copy()
        
        # Fix missing H1
        if issues['missing_h1'] and fixed_headings:
            # Promote first heading to H1
            fixed_headings[0]['level'] = 'H1'
            logger.info("Promoted first heading to H1")
        
        # Fix level jumps
        for jump_idx in issues['level_jumps']:
            if jump_idx < len(fixed_headings):
                # Adjust level to prevent jump
                prev_level = self._level_to_number(fixed_headings[jump_idx - 1]['level'])
                current_level = self._level_to_number(fixed_headings[jump_idx]['level'])
                
                if current_level > prev_level + 1:
                    # Set to one level below previous
                    fixed_headings[jump_idx]['level'] = self._number_to_level(prev_level + 1)
                    logger.info(f"Fixed level jump at index {jump_idx}")
        
        # Fix orphaned headings
        for orphan_idx in issues['orphaned_headings']:
            if orphan_idx < len(fixed_headings):
                # Promote to H2
                fixed_headings[orphan_idx]['level'] = 'H2'
                logger.info(f"Fixed orphaned H3 at index {orphan_idx}")
        
        # Re-validate
        new_issues = self._detect_issues(fixed_headings)
        if new_issues['has_issues']:
            logger.warning("Some hierarchy issues remain after fixing")
        
        return fixed_headings
    
    def _level_to_number(self, level: str) -> int:
        """Convert level string to number"""
        return {'H1': 1, 'H2': 2, 'H3': 3}.get(level, 2)
    
    def _number_to_level(self, number: int) -> str:
        """Convert number to level string"""
        return {1: 'H1', 2: 'H2', 3: 'H3'}.get(number, 'H2')