# src/persona_analysis/builders/query_builder.py
from typing import Dict, List, Set

class QueryBuilder:
    """Build search queries from persona and job data"""
    
    def build(self, persona_data: Dict, job_data: Dict, 
             expanded_keywords: Dict, domain: Dict) -> Dict:
        """Build comprehensive query profile"""
        query = {
            'primary_terms': self._build_primary_terms(job_data, expanded_keywords),
            'secondary_terms': self._build_secondary_terms(persona_data, expanded_keywords),
            'must_have_terms': self._identify_must_have_terms(job_data),
            'context_terms': self._build_context_terms(domain, persona_data),
            'exclusion_terms': self._identify_exclusions(persona_data, job_data),
            'phrase_queries': self._build_phrase_queries(job_data),
            'weighted_query': self._build_weighted_query(
                persona_data, job_data, expanded_keywords
            )
        }
        
        return query
    
    def _build_primary_terms(self, job_data: Dict, keywords: Dict) -> List[str]:
        """Build primary search terms from job requirements"""
        primary = []
        
        # Add job keywords
        primary.extend(job_data.get('keywords', [])[:10])
        
        # Add target terms
        primary.extend(job_data.get('target', [])[:5])
        
        # Add focus area terms
        for area in job_data.get('focus_areas', [])[:3]:
            primary.extend(area.split()[:3])
        
        # Add top expanded keywords
        if 'expanded' in keywords and 'job' in keywords['expanded']:
            primary.extend(keywords['expanded']['job'][:5])
        
        # Deduplicate while preserving order
        seen = set()
        unique_primary = []
        for term in primary:
            if term.lower() not in seen:
                seen.add(term.lower())
                unique_primary.append(term.lower())
        
        return unique_primary[:20]  # Limit to top 20
    
    def _build_secondary_terms(self, persona_data: Dict, keywords: Dict) -> List[str]:
        """Build secondary search terms from persona"""
        secondary = []
        
        # Add persona keywords
        secondary.extend(persona_data.get('keywords', [])[:10])
        
        # Add specialization terms
        for spec in persona_data.get('focus_areas', [])[:3]:
            secondary.extend(spec.split()[:2])
        
        # Add domain terms
        if isinstance(persona_data.get('domain'), list):
            secondary.extend(persona_data['domain'][:3])
        
        # Deduplicate
        return list(set(term.lower() for term in secondary))[:15]
    
    def _identify_must_have_terms(self, job_data: Dict) -> List[str]:
        """Identify terms that must appear in relevant sections"""
        must_have = []
        
        # Action targets are usually must-have
        must_have.extend(job_data.get('target', [])[:3])
        
        # Specific deliverables
        for deliverable in job_data.get('deliverables', [])[:2]:
            # Extract key terms from deliverable
            key_terms = [t for t in deliverable.split() 
                        if len(t) > 3 and t.lower() not in ['with', 'from', 'that']]
            must_have.extend(key_terms[:2])
        
        return list(set(term.lower() for term in must_have))[:10]
    
    def _build_context_terms(self, domain: Dict, persona_data: Dict) -> List[str]:
        """Build context terms for better understanding"""
        context = []
        
        # Add domain terms
        if domain and 'primary' in domain:
            context.append(domain['primary'])
        
        # Add expertise level context
        level = persona_data.get('expertise_level', 'intermediate')
        if level == 'expert':
            context.extend(['advanced', 'complex', 'detailed'])
        elif level == 'beginner':
            context.extend(['introduction', 'basic', 'fundamental'])
        else:
            context.extend(['practical', 'implementation', 'application'])
        
        return context
    
    def _identify_exclusions(self, persona_data: Dict, job_data: Dict) -> List[str]:
        """Identify terms to exclude or downweight"""
        exclusions = []
        
        # Expertise-based exclusions
        level = persona_data.get('expertise_level', 'intermediate')
        if level == 'expert':
            exclusions.extend(['beginner', 'introduction', 'basic'])
        elif level == 'beginner':
            exclusions.extend(['advanced', 'expert', 'complex'])
        
        # Constraint-based exclusions
        for constraint in job_data.get('constraints', []):
            if 'not' in constraint.lower() or 'exclude' in constraint.lower():
                # Extract excluded terms
                words = constraint.split()
                for i, word in enumerate(words):
                    if word.lower() in ['not', 'exclude'] and i + 1 < len(words):
                        exclusions.append(words[i + 1].lower())
        
        return list(set(exclusions))
    
    def _build_phrase_queries(self, job_data: Dict) -> List[str]:
        """Build exact phrase queries"""
        phrases = []
        
        # Focus areas often make good phrase queries
        phrases.extend(job_data.get('focus_areas', [])[:3])
        
        # Multi-word targets
        for target in job_data.get('target', []):
            if ' ' in target:
                phrases.append(target)
        
        return phrases[:5]
    
    def _build_weighted_query(self, persona_data: Dict, job_data: Dict, 
                            keywords: Dict) -> Dict[str, float]:
        """Build weighted query terms"""
        weighted = {}
        
        # Job keywords get highest weight
        for kw in job_data.get('keywords', [])[:10]:
            weighted[kw.lower()] = 1.0
        
        # Target terms
        for target in job_data.get('target', [])[:5]:
            weighted[target.lower()] = 0.9
        
        # Persona keywords
        for kw in persona_data.get('keywords', [])[:10]:
            if kw.lower() not in weighted:
                weighted[kw.lower()] = 0.5
        
        # Expanded keywords get lower weight
        if 'all' in keywords:
            for kw in keywords['all'][:20]:
                if kw.lower() not in weighted:
                    weighted[kw.lower()] = 0.3
        
        return weighted