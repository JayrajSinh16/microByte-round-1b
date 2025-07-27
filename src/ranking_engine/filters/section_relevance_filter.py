# src/ranking_engine/filters/section_relevance_filter.py
import re
from typing import List, Dict, Optional
from ..utils.domain_config import DomainConfig

class SectionRelevanceFilter:
    """Advanced persona-driven section filtering with anti-section logic"""
    
    def __init__(self, domain_config: Optional[DomainConfig] = None):
        self.domain_config = domain_config or DomainConfig()
        
        # STEP 1: Anti-Section Filter - Generic useless sections to ALWAYS exclude
        self.anti_section_patterns = {
            'introduction', 'intro', 'overview', 'conclusion', 'summary', 
            'abstract', 'preface', 'foreword', 'acknowledgments', 'references',
            'bibliography', 'index', 'appendix', 'glossary', 'table of contents',
            'contents', 'about', 'background', 'getting started', 'how to use',
            'disclaimer', 'copyright', 'legal', 'terms', 'privacy'
        }
    
    def filter(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Apply three-step persona-driven filtering logic"""
        if not sections:
            return sections
        
        # STEP 1: Anti-Section Filter - Remove useless generic sections
        useful_sections = self._apply_anti_section_filter(sections)
        
        # STEP 2: Persona-Driven Relevance Scoring
        scored_sections = self._apply_persona_driven_scoring(useful_sections, query_profile)
        
        # Return only high-scoring sections (top performers)
        min_score = 0.4  # Only keep genuinely relevant sections
        filtered_sections = [s for s in scored_sections if s.get('persona_relevance_score', 0) >= min_score]
        
        # Sort by persona relevance score
        filtered_sections.sort(key=lambda x: x.get('persona_relevance_score', 0), reverse=True)
        
        return filtered_sections
    
    def _apply_anti_section_filter(self, sections: List[Dict]) -> List[Dict]:
        """STEP 1: Filter out generic, useless sections"""
        useful_sections = []
        
        for section in sections:
            title = section.get('title', '').lower().strip()
            
            # Check if title matches any anti-section pattern
            is_generic = False
            for pattern in self.anti_section_patterns:
                if pattern in title or title == pattern:
                    is_generic = True
                    break
            
            # Also check for generic patterns
            if not is_generic:
                # Check for patterns like "chapter 1", "part i", etc.
                generic_patterns = [
                    r'^chapter\s+\d+',
                    r'^part\s+[ivx]+',
                    r'^section\s+\d+',
                    r'^appendix\s+[a-z]',
                    r'^\d+\.\s*introduction',
                    r'^\d+\.\s*conclusion'
                ]
                for pattern in generic_patterns:
                    if re.match(pattern, title):
                        is_generic = True
                        break
            
            if not is_generic:
                useful_sections.append(section)
        
        return useful_sections
    
    def _apply_persona_driven_scoring(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """STEP 2: Score sections based on persona and job relevance"""
        persona_raw = query_profile.get('persona', '')
        job_raw = query_profile.get('job', '')
        
        # Handle different data types for persona and job
        if isinstance(persona_raw, dict):
            persona = str(persona_raw.get('description', persona_raw.get('value', ''))).lower()
        else:
            persona = str(persona_raw).lower()
            
        if isinstance(job_raw, dict):
            job = str(job_raw.get('description', job_raw.get('value', ''))).lower()
        else:
            job = str(job_raw).lower()
            
        combined_context = f"{persona} {job}"
        
        # Get domain-specific persona preferences
        domain = query_profile.get('domain_profile', {}).get('domain', 'general')
        domain_profile = self.domain_config.get_profile(domain)
        
        for section in sections:
            title = section.get('title', '').lower()
            content_preview = section.get('content', '')[:500].lower()  # More content for better analysis
            combined_text = f"{title} {content_preview}"
            
            # Calculate persona relevance score
            persona_score = self._calculate_persona_relevance(
                combined_text, combined_context, domain_profile
            )
            
            section['persona_relevance_score'] = persona_score
        
        return sections
    
    def _calculate_persona_relevance(self, text: str, persona_context: str, domain_profile) -> float:
        """Calculate how relevant this section is to the specific persona and job"""
        score = 0.0
        
        # Extract key persona indicators from context
        persona_indicators = self._extract_persona_indicators(persona_context, domain_profile)
        positive_keywords = persona_indicators['positive']
        negative_keywords = persona_indicators['negative']
        
        # Positive scoring - look for persona-relevant content
        positive_matches = 0
        for keyword in positive_keywords:
            if keyword in text:
                weight = positive_keywords[keyword]
                positive_matches += weight
        
        # Negative scoring - penalize irrelevant content
        negative_penalty = 0
        for keyword in negative_keywords:
            if keyword in text:
                negative_penalty += negative_keywords[keyword]
        
        # Calculate final score
        # Normalize positive matches by text length to avoid bias toward longer content
        text_length_factor = max(len(text.split()), 1)
        normalized_positive = positive_matches / (text_length_factor / 100)  # Per 100 words
        
        score = max(0, normalized_positive - negative_penalty)
        
        # Boost score for title matches (titles are more important)
        title_words = text.split()[:10]  # Approximate title
        title_text = ' '.join(title_words)
        title_boost = 0
        for keyword in positive_keywords:
            if keyword in title_text:
                title_boost += positive_keywords[keyword] * 2  # Double weight for title matches
        
        final_score = score + title_boost
        return min(final_score, 1.0)  # Cap at 1.0
    def _extract_persona_indicators(self, persona_context: str, domain_profile) -> Dict:
        """Extract positive and negative keywords based on persona context and domain"""
        indicators = {'positive': {}, 'negative': {}}
        
        # Get base keywords from domain profile
        base_positive = domain_profile.priority_keywords if domain_profile else []
        
        # Analyze persona context to determine specific preferences
        context_words = persona_context.split()
        
        # Generic persona-based keyword mapping (domain-agnostic)
        persona_mappings = {
            # Young/social group indicators
            'college': {'positive': ['nightlife', 'bars', 'clubs', 'entertainment', 'adventure', 'social', 'fun', 'party'], 
                       'negative': ['business', 'conference', 'meeting', 'corporate', 'formal']},
            'friends': {'positive': ['group', 'activities', 'entertainment', 'adventure', 'social', 'nightlife'],
                       'negative': ['family', 'kids', 'children', 'business', 'quiet', 'peaceful']},
            'young': {'positive': ['adventure', 'nightlife', 'entertainment', 'active', 'energy', 'social'],
                      'negative': ['relaxing', 'quiet', 'senior', 'elderly', 'business']},
            
            # Activity type indicators  
            'trip': {'positive': ['destinations', 'places', 'visit', 'explore', 'travel', 'attractions'],
                    'negative': ['office', 'work', 'business', 'meeting']},
            'vacation': {'positive': ['leisure', 'fun', 'entertainment', 'relaxation', 'activities'],
                        'negative': ['work', 'business', 'professional']},
            'plan': {'positive': ['itinerary', 'schedule', 'activities', 'destinations', 'logistics'],
                    'negative': ['spontaneous', 'unplanned']},
            
            # Business indicators
            'business': {'positive': ['professional', 'corporate', 'meeting', 'conference', 'networking'],
                        'negative': ['leisure', 'vacation', 'fun', 'entertainment']},
            'analyst': {'positive': ['data', 'analysis', 'metrics', 'performance', 'strategy'],
                       'negative': ['leisure', 'entertainment', 'fun']},
            
            # Research indicators
            'research': {'positive': ['information', 'data', 'study', 'analysis', 'findings', 'evidence'],
                        'negative': ['opinion', 'speculation', 'casual']},
        }
        
        # Build positive keywords with weights
        for word in context_words:
            if word in persona_mappings:
                for pos_keyword in persona_mappings[word]['positive']:
                    indicators['positive'][pos_keyword] = indicators['positive'].get(pos_keyword, 0) + 0.3
                for neg_keyword in persona_mappings[word]['negative']:
                    indicators['negative'][neg_keyword] = indicators['negative'].get(neg_keyword, 0) + 0.5
        
        # Add domain-specific base keywords
        for keyword in base_positive:
            indicators['positive'][keyword] = indicators['positive'].get(keyword, 0) + 0.2
        
        # Add persona-context specific boosts
        if 'college' in persona_context and 'friends' in persona_context:
            # Boost social/entertainment keywords for college friends
            social_boost = ['nightlife', 'bars', 'clubs', 'entertainment', 'adventure', 'coastal', 'beaches', 'water sports']
            for keyword in social_boost:
                indicators['positive'][keyword] = indicators['positive'].get(keyword, 0) + 0.4
            
            # Penalize family/formal content
            family_penalty = ['family', 'kids', 'children', 'business', 'formal', 'history']
            for keyword in family_penalty:
                indicators['negative'][keyword] = indicators['negative'].get(keyword, 0) + 0.6
        
        return indicators
