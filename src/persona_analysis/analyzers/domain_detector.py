# src/persona_analysis/analyzers/domain_detector.py
import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass

@dataclass
class DomainProfile:
    """Domain-specific profile for content prioritization"""
    domain: str
    priority_keywords: List[str]
    section_preferences: Dict[str, float]  # section type -> priority weight
    content_patterns: List[str]  # regex patterns for relevant content
    exclusion_patterns: List[str]  # patterns to avoid

class DomainDetector:
    """Detect domain and create domain-specific content preferences"""
    
    def __init__(self):
        self.domain_profiles = self._initialize_domain_profiles()
        
    def _initialize_domain_profiles(self) -> Dict[str, DomainProfile]:
        """Initialize domain-specific profiles"""
        return {
            'travel_planner': DomainProfile(
                domain='travel_planner',
                priority_keywords=[
                    'activities', 'attractions', 'things to do', 'places to visit',
                    'restaurants', 'dining', 'nightlife', 'entertainment', 'beaches',
                    'hotels', 'accommodation', 'transportation', 'costs', 'budget',
                    'itinerary', 'schedule', 'tour', 'excursion', 'adventure'
                ],
                section_preferences={
                    'activities': 1.0, 'things_to_do': 1.0, 'attractions': 1.0,
                    'restaurants': 0.9, 'dining': 0.9, 'cuisine': 0.9,
                    'nightlife': 0.9, 'entertainment': 0.9, 'bars': 0.9,
                    'cities': 0.8, 'destinations': 0.8, 'places': 0.8,
                    'beaches': 0.8, 'coastal': 0.8, 'adventure': 0.8,
                    'hotels': 0.7, 'accommodation': 0.7, 'lodging': 0.7,
                    'transportation': 0.6, 'travel': 0.6, 'getting_around': 0.6,
                    'tips': 0.5, 'advice': 0.5, 'recommendations': 0.5,
                    'introduction': 0.2, 'overview': 0.3, 'conclusion': 0.1,
                    'history': 0.3, 'background': 0.3, 'culture': 0.4
                },
                content_patterns=[
                    r'(?i)\b(?:visit|explore|enjoy|experience|try|taste|see)\b.*\b(?:beach|restaurant|club|bar|attraction|activity)\b',
                    r'(?i)\b(?:popular|famous|best|top|recommended)\b.*\b(?:places|spots|destinations|activities)\b',
                    r'(?i)\b(?:address|location|hours|price|cost|budget)\b',
                    r'(?i)\b(?:nightlife|entertainment|dining|cuisine|adventure|tour)\b'
                ],
                exclusion_patterns=[
                    r'(?i)\b(?:abstract|summary|introduction|conclusion|overview)\b.*:',
                    r'(?i)^(?:in conclusion|to summarize|in summary)',
                    r'(?i)\b(?:bibliography|references|sources)\b'
                ]
            ),
            
            'food_contractor': DomainProfile(
                domain='food_contractor',
                priority_keywords=[
                    'ingredients', 'recipes', 'cooking', 'preparation', 'menu',
                    'nutrition', 'dietary', 'allergens', 'suppliers', 'vendors',
                    'cost', 'pricing', 'portion', 'serving', 'catering', 'kitchen',
                    'equipment', 'food safety', 'hygiene', 'storage', 'procurement'
                ],
                section_preferences={
                    'recipes': 1.0, 'ingredients': 1.0, 'cooking': 1.0,
                    'nutrition': 0.9, 'dietary': 0.9, 'allergens': 0.9,
                    'suppliers': 0.8, 'vendors': 0.8, 'procurement': 0.8,
                    'pricing': 0.8, 'costs': 0.8, 'portions': 0.8,
                    'kitchen': 0.7, 'equipment': 0.7, 'preparation': 0.7,
                    'safety': 0.7, 'hygiene': 0.7, 'storage': 0.7,
                    'menu': 0.6, 'planning': 0.6, 'catering': 0.6,
                    'introduction': 0.2, 'conclusion': 0.1, 'history': 0.3
                },
                content_patterns=[
                    r'(?i)\b(?:recipe|ingredient|cooking|preparation|menu)\b',
                    r'(?i)\b(?:nutrition|dietary|allergen|gluten|vegan|vegetarian)\b',
                    r'(?i)\b(?:supplier|vendor|cost|price|portion|serving)\b',
                    r'(?i)\b(?:kitchen|equipment|safety|hygiene|storage)\b'
                ],
                exclusion_patterns=[
                    r'(?i)\b(?:tourist|sightseeing|attraction|entertainment)\b',
                    r'(?i)\b(?:hotel|accommodation|nightlife)\b'
                ]
            ),
            
            'hr_professional': DomainProfile(
                domain='hr_professional',
                priority_keywords=[
                    'employees', 'staff', 'workforce', 'personnel', 'hiring',
                    'recruitment', 'training', 'development', 'performance',
                    'policies', 'procedures', 'benefits', 'compensation',
                    'management', 'leadership', 'culture', 'engagement',
                    'retention', 'compliance', 'legal', 'regulations'
                ],
                section_preferences={
                    'policies': 1.0, 'procedures': 1.0, 'recruitment': 1.0,
                    'training': 0.9, 'development': 0.9, 'performance': 0.9,
                    'compensation': 0.9, 'benefits': 0.9, 'hiring': 0.9,
                    'management': 0.8, 'leadership': 0.8, 'culture': 0.8,
                    'compliance': 0.8, 'legal': 0.8, 'regulations': 0.8,
                    'employees': 0.7, 'staff': 0.7, 'workforce': 0.7,
                    'engagement': 0.7, 'retention': 0.7, 'onboarding': 0.7,
                    'introduction': 0.2, 'conclusion': 0.1, 'overview': 0.3
                },
                content_patterns=[
                    r'(?i)\b(?:employee|staff|workforce|personnel|hiring)\b',
                    r'(?i)\b(?:policy|procedure|regulation|compliance|legal)\b',
                    r'(?i)\b(?:training|development|performance|management)\b',
                    r'(?i)\b(?:compensation|benefits|salary|wage)\b'
                ],
                exclusion_patterns=[
                    r'(?i)\b(?:tourist|travel|restaurant|entertainment)\b',
                    r'(?i)\b(?:recipe|cooking|food)\b'
                ]
            ),
            
            'business_analyst': DomainProfile(
                domain='business_analyst',
                priority_keywords=[
                    'analysis', 'data', 'metrics', 'kpi', 'performance', 'trends',
                    'requirements', 'processes', 'optimization', 'efficiency',
                    'strategy', 'planning', 'forecasting', 'reporting',
                    'stakeholders', 'business', 'operations', 'improvement'
                ],
                section_preferences={
                    'analysis': 1.0, 'data': 1.0, 'metrics': 1.0,
                    'requirements': 0.9, 'processes': 0.9, 'strategy': 0.9,
                    'planning': 0.8, 'forecasting': 0.8, 'reporting': 0.8,
                    'optimization': 0.8, 'efficiency': 0.8, 'improvement': 0.8,
                    'stakeholders': 0.7, 'business': 0.7, 'operations': 0.7,
                    'trends': 0.7, 'performance': 0.7, 'kpi': 0.7,
                    'introduction': 0.2, 'conclusion': 0.1, 'overview': 0.3
                },
                content_patterns=[
                    r'(?i)\b(?:analysis|data|metrics|kpi|performance)\b',
                    r'(?i)\b(?:requirement|process|strategy|planning)\b',
                    r'(?i)\b(?:optimization|efficiency|improvement|trend)\b',
                    r'(?i)\b(?:stakeholder|business|operation|reporting)\b'
                ],
                exclusion_patterns=[
                    r'(?i)\b(?:tourist|travel|food|entertainment)\b'
                ]
            )
        }
    
    def detect_domain(self, persona: str, job_description: str) -> str:
        """Detect the most relevant domain based on persona and job"""
        combined_text = f"{persona} {job_description}".lower()
        
        domain_scores = {}
        for domain, profile in self.domain_profiles.items():
            score = 0
            for keyword in profile.priority_keywords:
                if keyword in combined_text:
                    score += 1
            
            # Normalize by number of keywords
            domain_scores[domain] = score / len(profile.priority_keywords)
        
        # Return domain with highest score, default to travel_planner
        best_domain = max(domain_scores.items(), key=lambda x: x[1])
        return best_domain[0] if best_domain[1] > 0.1 else 'travel_planner'
    
    def get_domain_profile(self, domain: str) -> DomainProfile:
        """Get domain profile or default to travel_planner"""
        return self.domain_profiles.get(domain, self.domain_profiles['travel_planner'])
    
    def calculate_section_relevance(self, section_title: str, domain: str) -> float:
        """Calculate section relevance based on domain preferences"""
        profile = self.get_domain_profile(domain)
        title_lower = section_title.lower()
        
        # Check direct matches
        for section_type, weight in profile.section_preferences.items():
            if section_type in title_lower:
                return weight
        
        # Check keyword matches
        keyword_matches = 0
        for keyword in profile.priority_keywords:
            if keyword in title_lower:
                keyword_matches += 1
        
        # Base relevance from keyword density
        base_relevance = min(keyword_matches / len(profile.priority_keywords), 0.8)
        
        # Penalty for exclusion patterns
        for pattern in profile.exclusion_patterns:
            if re.search(pattern, section_title):
                base_relevance *= 0.3
        
        return max(base_relevance, 0.1)  # Minimum relevance
