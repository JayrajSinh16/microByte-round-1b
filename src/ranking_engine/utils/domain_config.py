# src/ranking_engine/utils/domain_config.py
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
import json

@dataclass
class DomainProfile:
    """Generic domain profile structure"""
    name: str
    priority_keywords: List[str]
    section_patterns: List[str]  # Regex patterns for high-priority sections
    exclusion_patterns: List[str]  # Patterns to penalize
    scoring_weights: Dict[str, float]  # Feature weights for scoring
    
class DomainConfig:
    """Configurable domain-specific settings"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.profiles = self._load_default_profiles()
        if config_path:
            self._load_from_file(config_path)
    
    def _load_default_profiles(self) -> Dict[str, DomainProfile]:
        """Load default domain profiles"""
        return {
            'travel_planner': DomainProfile(
                name='travel_planner',
                priority_keywords=[
                    'activities', 'attractions', 'destinations', 'places',
                    'restaurants', 'dining', 'entertainment', 'hotels',
                    'transportation', 'costs', 'experiences'
                ],
                section_patterns=[
                    r'(?i)\b(?:activities|attractions|things.to.do)\b',
                    r'(?i)\b(?:restaurants?|dining|cuisine|food)\b',
                    r'(?i)\b(?:entertainment|nightlife|bars|clubs)\b',
                    r'(?i)\b(?:cities|destinations|places|locations)\b',
                    r'(?i)\b(?:hotels?|accommodation|lodging)\b'
                ],
                exclusion_patterns=[
                    r'(?i)\b(?:history|background|introduction|overview)\b.*:',
                    r'(?i)^(?:in conclusion|to summarize)'
                ],
                scoring_weights={
                    'keyword_match': 0.3,
                    'pattern_match': 0.4,
                    'content_relevance': 0.3
                }
            ),
            
            'business_analyst': DomainProfile(
                name='business_analyst',
                priority_keywords=[
                    'analysis', 'data', 'metrics', 'performance', 'strategy',
                    'requirements', 'processes', 'optimization', 'reporting'
                ],
                section_patterns=[
                    r'(?i)\b(?:analysis|analytics|metrics|kpi)\b',
                    r'(?i)\b(?:requirements|specifications|criteria)\b',
                    r'(?i)\b(?:processes?|workflows?|procedures?)\b',
                    r'(?i)\b(?:strategy|planning|optimization)\b'
                ],
                exclusion_patterns=[
                    r'(?i)\b(?:entertainment|tourism|leisure)\b'
                ],
                scoring_weights={
                    'keyword_match': 0.4,
                    'pattern_match': 0.4,
                    'content_relevance': 0.2
                }
            ),
            
            'content_researcher': DomainProfile(
                name='content_researcher',
                priority_keywords=[
                    'information', 'research', 'studies', 'findings', 'evidence',
                    'methodology', 'sources', 'literature', 'analysis'
                ],
                section_patterns=[
                    r'(?i)\b(?:research|studies|findings|evidence)\b',
                    r'(?i)\b(?:methodology|methods|approach)\b',
                    r'(?i)\b(?:literature|sources|references)\b',
                    r'(?i)\b(?:analysis|evaluation|assessment)\b'
                ],
                exclusion_patterns=[
                    r'(?i)\b(?:promotional|marketing|sales)\b'
                ],
                scoring_weights={
                    'keyword_match': 0.2,
                    'pattern_match': 0.3,
                    'content_relevance': 0.5
                }
            )
        }
    
    def get_profile(self, domain: str) -> DomainProfile:
        """Get domain profile or return default"""
        return self.profiles.get(domain, self.profiles['travel_planner'])
    
    def add_profile(self, domain: str, profile: DomainProfile):
        """Add new domain profile"""
        self.profiles[domain] = profile
    
    def _load_from_file(self, config_path: str):
        """Load domain profiles from JSON configuration file"""
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                
            for domain, data in config_data.items():
                profile = DomainProfile(
                    name=data.get('name', domain),
                    priority_keywords=data.get('priority_keywords', []),
                    section_patterns=data.get('section_patterns', []),
                    exclusion_patterns=data.get('exclusion_patterns', []),
                    scoring_weights=data.get('scoring_weights', {})
                )
                self.profiles[domain] = profile
        except Exception as e:
            print(f"Warning: Could not load domain config from {config_path}: {e}")
