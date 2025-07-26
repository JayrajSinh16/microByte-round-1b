# src/persona_analysis/parsers/persona_parser.py
import re
import nltk
from typing import Dict, List, Set, Any
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag

class PersonaParser:
    """Parse and analyze persona descriptions"""
    
    def __init__(self):
        # Download required NLTK data
        for resource in ['punkt', 'averaged_perceptron_tagger', 'wordnet']:
            try:
                nltk.data.find(f'tokenizers/{resource}')
            except LookupError:
                nltk.download(resource, quiet=True)
        
        self.expertise_indicators = {
            'expert': ['phd', 'professor', 'researcher', 'expert', 'senior', 'lead'],
            'intermediate': ['analyst', 'engineer', 'developer', 'manager'],
            'beginner': ['student', 'intern', 'junior', 'trainee', 'learning']
        }
    
    def parse(self, persona_text: str) -> Dict:
        """Parse persona description into structured data"""
        persona_data = {
            'original': persona_text,
            'role': self._extract_role(persona_text),
            'domain': self._extract_domain(persona_text),
            'expertise_level': self._detect_expertise_level(persona_text),
            'keywords': self._extract_keywords(persona_text),
            'focus_areas': self._extract_focus_areas(persona_text),
            'attributes': self._extract_attributes(persona_text)
        }
        
        return persona_data
    
    def _extract_role(self, text: str) -> str:
        """Extract the primary role from persona"""
        # Common role patterns
        role_patterns = [
            r'(?:I am a|as a|work as a)\s+([^,\.]+)',
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Title case at start
            r'(\w+\s+(?:Researcher|Analyst|Engineer|Student|Professor))',
        ]
        
        for pattern in role_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip()
        
        # Fallback: first noun phrase
        tokens = word_tokenize(text)
        pos_tags = pos_tag(tokens)
        
        noun_phrase = []
        for word, pos in pos_tags:
            if pos in ['NN', 'NNP', 'NNS', 'NNPS']:
                noun_phrase.append(word)
            elif noun_phrase:  # End of noun phrase
                break
        
        return ' '.join(noun_phrase) if noun_phrase else 'Professional'
    
    def _extract_domain(self, text: str) -> List[str]:
        """Extract domain/field information"""
        domains = []
        
        # Domain keywords
        domain_keywords = {
            'technology': ['software', 'hardware', 'computer', 'tech', 'it', 'digital'],
            'biology': ['biology', 'biological', 'bio', 'life science'],
            'finance': ['finance', 'financial', 'investment', 'banking', 'economics'],
            'medicine': ['medical', 'medicine', 'healthcare', 'clinical', 'pharma'],
            'education': ['education', 'teaching', 'academic', 'learning'],
            'research': ['research', 'study', 'analysis', 'investigation'],
            'business': ['business', 'management', 'corporate', 'enterprise']
        }
        
        text_lower = text.lower()
        for domain, keywords in domain_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                domains.append(domain)
        
        return domains if domains else ['general']
    
    def _detect_expertise_level(self, text: str) -> str:
        """Detect expertise level from persona description"""
        text_lower = text.lower()
        
        for level, indicators in self.expertise_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                return level
        
        return 'intermediate'  # Default
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from persona"""
        keywords = []
        
        # Tokenize and POS tag
        tokens = word_tokenize(text)
        pos_tags = pos_tag(tokens)
        
        # Extract nouns and adjectives
        for word, pos in pos_tags:
            if pos in ['NN', 'NNS', 'NNP', 'NNPS', 'JJ', 'JJR', 'JJS']:
                if len(word) > 2 and word.lower() not in ['the', 'and', 'for']:
                    keywords.append(word.lower())
        
        # Remove duplicates while preserving order
        seen = set()
        keywords = [x for x in keywords if not (x in seen or seen.add(x))]
        
        return keywords
    
    def _extract_focus_areas(self, text: str) -> List[str]:
        """Extract specific focus areas mentioned"""
        focus_patterns = [
            r'focus(?:ing)? on ([^,\.]+)',
            r'speciali[sz](?:ing|e) in ([^,\.]+)',
            r'expert in ([^,\.]+)',
            r'working on ([^,\.]+)',
            r'interested in ([^,\.]+)'
        ]
        
        focus_areas = []
        for pattern in focus_patterns:
            matches = re.findall(pattern, text, re.I)
            focus_areas.extend(matches)
        
        return [area.strip() for area in focus_areas]
    
    def _extract_attributes(self, text: str) -> Dict[str, Any]:
        """Extract additional attributes from persona"""
        attributes = {
            'experience_years': self._extract_experience(text),
            'technical_level': self._assess_technical_level(text),
            'industry': self._extract_industry(text)
        }
        
        return attributes
    
    def _extract_experience(self, text: str) -> int:
        """Extract years of experience if mentioned"""
        patterns = [
            r'(\d+)\+?\s*years?',
            r'(\d+)\s*yrs?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return int(match.group(1))
        
        return 0  # Unknown
    
    def _assess_technical_level(self, text: str) -> str:
        """Assess technical level from description"""
        technical_terms = ['algorithm', 'framework', 'architecture', 'implementation',
                         'optimization', 'methodology', 'technical', 'advanced']
        
        text_lower = text.lower()
        technical_count = sum(1 for term in technical_terms if term in text_lower)
        
        if technical_count >= 3:
            return 'high'
        elif technical_count >= 1:
            return 'medium'
        else:
            return 'low'
    
    def _extract_industry(self, text: str) -> List[str]:
        """Extract industry mentions"""
        industries = []
        
        industry_keywords = {
            'tech': ['tech', 'software', 'saas', 'startup'],
            'healthcare': ['healthcare', 'medical', 'hospital', 'clinical'],
            'finance': ['finance', 'banking', 'investment', 'fintech'],
            'education': ['education', 'university', 'academic', 'school'],
            'retail': ['retail', 'e-commerce', 'sales', 'consumer'],
            'manufacturing': ['manufacturing', 'production', 'factory', 'industrial']
        }
        
        text_lower = text.lower()
        for industry, keywords in industry_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                industries.append(industry)
        
        return industries if industries else ['general']