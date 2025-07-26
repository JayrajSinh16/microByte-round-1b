# src/persona_analysis/analyzers/expertise_analyzer.py
import re
from typing import Dict, List

class ExpertiseAnalyzer:
    """Analyze expertise level and technical requirements"""
    
    def __init__(self):
        self.expertise_indicators = {
            'beginner': {
                'keywords': ['learn', 'basic', 'introduction', 'fundamental', 'starter',
                           'novice', 'beginner', 'student', 'trainee'],
                'years_range': (0, 2),
                'complexity': 'low'
            },
            'intermediate': {
                'keywords': ['understand', 'implement', 'develop', 'analyze', 'improve',
                           'intermediate', 'practitioner', 'professional'],
                'years_range': (2, 5),
                'complexity': 'medium'
            },
            'expert': {
                'keywords': ['expert', 'advanced', 'senior', 'lead', 'architect',
                           'specialist', 'phd', 'professor', 'researcher'],
                'years_range': (5, 100),
                'complexity': 'high'
            }
        }
        
        self.technical_depth_indicators = {
            'theoretical': ['theory', 'concept', 'principle', 'framework', 'model'],
            'practical': ['implement', 'build', 'deploy', 'configure', 'optimize'],
            'analytical': ['analyze', 'evaluate', 'assess', 'investigate', 'research']
        }
    
    def analyze(self, persona_data: Dict) -> Dict:
        """Analyze expertise from persona data"""
        expertise = {
            'level': self._determine_level(persona_data),
            'years_experience': self._extract_years(persona_data),
            'technical_depth': self._assess_technical_depth(persona_data),
            'specializations': self._identify_specializations(persona_data),
            'complexity_preference': self._determine_complexity(persona_data)
        }
        
        return expertise
    
    def _determine_level(self, persona_data: Dict) -> str:
        """Determine expertise level"""
        text = persona_data.get('original', '').lower()
        
        # Check explicit level mentions
        level = persona_data.get('expertise_level', '')
        if level:
            return level
        
        # Score each level based on keywords
        level_scores = {}
        
        for level, indicators in self.expertise_indicators.items():
            score = 0
            for keyword in indicators['keywords']:
                if keyword in text:
                    score += 1
            level_scores[level] = score
        
        # Check years of experience
        years = self._extract_years(persona_data)
        if years > 0:
            for level, indicators in self.expertise_indicators.items():
                min_years, max_years = indicators['years_range']
                if min_years <= years <= max_years:
                    level_scores[level] += 2
        
        # Return highest scoring level
        if level_scores:
            return max(level_scores, key=level_scores.get)
        
        return 'intermediate'  # Default
    
    def _extract_years(self, persona_data: Dict) -> int:
        """Extract years of experience"""
        # Check if already extracted
        if 'attributes' in persona_data and 'experience_years' in persona_data['attributes']:
            return persona_data['attributes']['experience_years']
        
        text = persona_data.get('original', '')
        
        # Pattern for years of experience
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d+)\s*years?\s*in',
            r'experience[:\s]*(\d+)\s*years?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return int(match.group(1))
        
        return 0
    
    def _assess_technical_depth(self, persona_data: Dict) -> Dict:
        """Assess technical depth preferences"""
        text = persona_data.get('original', '').lower()
        keywords = persona_data.get('keywords', [])
        
        depth_scores = {}
        
        for depth_type, indicators in self.technical_depth_indicators.items():
            score = 0
            for indicator in indicators:
                if indicator in text or indicator in keywords:
                    score += 1
            depth_scores[depth_type] = score
        
        # Normalize scores
        total = sum(depth_scores.values())
        if total > 0:
            depth_scores = {k: v/total for k, v in depth_scores.items()}
        
        return depth_scores
    
    def _identify_specializations(self, persona_data: Dict) -> List[str]:
        """Identify technical specializations"""
        specializations = []
        
        # From focus areas
        specializations.extend(persona_data.get('focus_areas', []))
        
        # From domain
        if isinstance(persona_data.get('domain'), list):
            specializations.extend(persona_data['domain'])
        
        # Common specialization patterns
        text = persona_data.get('original', '')
        spec_patterns = [
            r'speciali[sz]e(?:d)?\s+in\s+([^,\.]+)',
            r'expert\s+in\s+([^,\.]+)',
            r'focus\s+on\s+([^,\.]+)'
        ]
        
        for pattern in spec_patterns:
            matches = re.findall(pattern, text, re.I)
            specializations.extend(matches)
        
        # Clean and deduplicate
        specializations = [s.strip() for s in specializations]
        return list(set(specializations))
    
    def _determine_complexity(self, persona_data: Dict) -> str:
        """Determine complexity preference"""
        level = persona_data.get('expertise_level', 'intermediate')
        
        # Map level to complexity
        complexity_map = {
            'beginner': 'simple',
            'intermediate': 'moderate',
            'expert': 'complex'
        }
        
        return complexity_map.get(level, 'moderate')