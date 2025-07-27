# src/persona_analysis/__init__.py
from .parsers import PersonaParser, JobParser, DomainIdentifier
from .analyzers import KeywordExtractor, SynonymExpander, ExpertiseAnalyzer, DomainDetector
from .builders import QueryBuilder, ProfileBuilder

class PersonaAnalyzer:
    """Main interface for persona analysis"""
    
    def __init__(self):
        self.persona_parser = PersonaParser()
        self.job_parser = JobParser()
        self.domain_identifier = DomainIdentifier()
        self.domain_detector = DomainDetector()
        self.keyword_extractor = KeywordExtractor()
        self.synonym_expander = SynonymExpander()
        self.expertise_analyzer = ExpertiseAnalyzer()
        self.query_builder = QueryBuilder()
        self.profile_builder = ProfileBuilder()
    
    def analyze(self, persona_text: str, job_text: str) -> dict:
        """Analyze persona and job to create search profile"""
        # Parse inputs
        persona_data = self.persona_parser.parse(persona_text)
        job_data = self.job_parser.parse(job_text)
        
        # Identify domain using enhanced detector
        domain = self.domain_detector.detect_domain(persona_text, job_text)
        domain_profile = self.domain_detector.get_domain_profile(domain)
        
        # Extract and expand keywords
        keywords = self.keyword_extractor.extract(persona_data, job_data)
        expanded_keywords = self.synonym_expander.expand(keywords)
        
        # Analyze expertise
        expertise = self.expertise_analyzer.analyze(persona_data)
        
        # Build query
        query = self.query_builder.build(
            persona_data, job_data, expanded_keywords, domain
        )
        
        # Build complete profile with domain information
        profile = self.profile_builder.build(
            persona_data, job_data, domain, expertise, query
        )
        
        # Add domain profile information for ranking
        profile['domain_profile'] = {
            'domain': domain,
            'priority_keywords': domain_profile.priority_keywords,
            'section_preferences': domain_profile.section_preferences,
            'content_patterns': domain_profile.content_patterns,
            'exclusion_patterns': domain_profile.exclusion_patterns
        }
        
        return profile

__all__ = ['PersonaAnalyzer']