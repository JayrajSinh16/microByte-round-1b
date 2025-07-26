# src/persona_analysis/builders/profile_builder.py (continued)
from typing import Dict,List
import json

class ProfileBuilder:
    """Build complete persona profile for search"""
    
    def build(self, persona_data: Dict, job_data: Dict, 
             domain: Dict, expertise: Dict, query: Dict) -> Dict:
        """Build comprehensive profile"""
        profile = {
            'persona': self._build_persona_profile(persona_data, expertise),
            'job': self._build_job_profile(job_data),
            'domain': domain,
            'expertise': expertise,
            'query': query,
            'search_preferences': self._build_search_preferences(
                persona_data, job_data, expertise
            ),
            'relevance_criteria': self._build_relevance_criteria(
                persona_data, job_data, domain
            ),
            'summary': self._build_summary(persona_data, job_data)
        }
        
        return profile
    
    def _build_persona_profile(self, persona_data: Dict, expertise: Dict) -> Dict:
        """Build persona-specific profile"""
        return {
            'role': persona_data.get('role', 'Unknown'),
            'expertise_level': expertise.get('level', 'intermediate'),
            'years_experience': expertise.get('years_experience', 0),
            'specializations': expertise.get('specializations', []),
            'keywords': persona_data.get('keywords', [])[:10],
            'focus_areas': persona_data.get('focus_areas', []),
            'technical_depth': expertise.get('technical_depth', {})
        }
    
    def _build_job_profile(self, job_data: Dict) -> Dict:
        """Build job-specific profile"""
        return {
            'description': job_data.get('original', ''),
            'action': job_data.get('action', {}),
            'target': job_data.get('target', []),
            'output': job_data.get('output', {}),
            'constraints': job_data.get('constraints', []),
            'deliverables': job_data.get('deliverables', []),
            'focus_areas': job_data.get('focus_areas', [])
        }
    
    def _build_search_preferences(self, persona_data: Dict, 
                                job_data: Dict, expertise: Dict) -> Dict:
        """Build search preferences based on persona and job"""
        preferences = {
            'complexity_level': expertise.get('complexity_preference', 'moderate'),
            'detail_level': self._determine_detail_level(expertise),
            'source_types': self._determine_source_types(persona_data, job_data),
            'content_types': self._determine_content_types(job_data),
            'recency_preference': self._determine_recency(job_data),
            'length_preference': self._determine_length_preference(job_data)
        }
        
        return preferences
    
    def _build_relevance_criteria(self, persona_data: Dict, 
                                job_data: Dict, domain: Dict) -> Dict:
        """Build criteria for relevance scoring"""
        return {
            'must_contain': self._identify_must_contain(job_data),
            'should_contain': self._identify_should_contain(persona_data, domain),
            'prefer_sections': self._identify_preferred_sections(job_data),
            'quality_indicators': self._identify_quality_indicators(persona_data),
            'relevance_weights': {
                'keyword_match': 0.25,
                'semantic_similarity': 0.40,
                'structural_position': 0.15,
                'cross_reference': 0.10,
                'context_match': 0.10
            }
        }
    
    def _build_summary(self, persona_data: Dict, job_data: Dict) -> str:
        """Build human-readable summary"""
        role = persona_data.get('role', 'Professional')
        action = job_data.get('action', {}).get('primary', 'analyze')
        targets = job_data.get('target', ['documents'])
        
        summary = f"{role} needs to {action} {', '.join(targets[:2])}"
        
        if job_data.get('focus_areas'):
            summary += f", focusing on {job_data['focus_areas'][0]}"
        
        return summary
    
    def _determine_detail_level(self, expertise: Dict) -> str:
        """Determine preferred detail level"""
        level = expertise.get('level', 'intermediate')
        
        if level == 'expert':
            return 'comprehensive'
        elif level == 'beginner':
            return 'overview'
        else:
            return 'balanced'
    
    def _determine_source_types(self, persona_data: Dict, job_data: Dict) -> List[str]:
        """Determine preferred source types"""
        sources = []
        
        # Based on action type
        action = job_data.get('action', {}).get('primary', '')
        if action == 'research':
            sources.extend(['academic', 'technical', 'reference'])
        elif action == 'create':
            sources.extend(['tutorial', 'example', 'documentation'])
        elif action == 'learn':
            sources.extend(['educational', 'introductory', 'guide'])
        
        # Based on expertise
        level = persona_data.get('expertise_level', 'intermediate')
        if level == 'expert':
            sources.extend(['research', 'advanced', 'specialized'])
        elif level == 'beginner':
            sources.extend(['introductory', 'basic', 'tutorial'])
        
        return list(set(sources))
    
    def _determine_content_types(self, job_data: Dict) -> List[str]:
        """Determine preferred content types"""
        types = []
        
        # Based on output requirements
        output_types = job_data.get('output', {}).get('types', [])
        if 'analysis' in output_types:
            types.extend(['analytical', 'comparative', 'evaluative'])
        if 'report' in output_types:
            types.extend(['comprehensive', 'summary', 'overview'])
        if 'solution' in output_types:
            types.extend(['practical', 'implementation', 'how-to'])
        
        return types if types else ['general']
    
    def _determine_recency(self, job_data: Dict) -> str:
        """Determine recency preference"""
        # Look for time-related keywords
        text = job_data.get('original', '').lower()
        
        if any(word in text for word in ['latest', 'current', 'recent', 'new']):
            return 'recent'
        elif any(word in text for word in ['historical', 'evolution', 'development']):
            return 'historical'
        else:
            return 'balanced'
    
    def _determine_length_preference(self, job_data: Dict) -> str:
        """Determine preferred content length"""
        output = job_data.get('output', {}).get('types', [])
        
        if 'summary' in output:
            return 'concise'
        elif 'comprehensive' in job_data.get('original', '').lower():
            return 'detailed'
        else:
            return 'moderate'
    
    def _identify_must_contain(self, job_data: Dict) -> List[str]:
        """Identify must-contain terms"""
        must_contain = []
        
        # Primary targets
        must_contain.extend(job_data.get('target', [])[:3])
        
        # Key deliverables
        for deliverable in job_data.get('deliverables', [])[:2]:
            key_terms = [t for t in deliverable.split() if len(t) > 4]
            must_contain.extend(key_terms[:1])
        
        return list(set(must_contain))
    
    def _identify_should_contain(self, persona_data: Dict, domain: Dict) -> List[str]:
        """Identify should-contain terms"""
        should_contain = []
        
        # Domain terms
        if domain and 'primary' in domain:
            should_contain.append(domain['primary'])
        
        # Specialization terms
        should_contain.extend(persona_data.get('focus_areas', [])[:2])
        
        return should_contain
    
    def _identify_preferred_sections(self, job_data: Dict) -> List[str]:
        """Identify preferred section types"""
        action = job_data.get('action', {}).get('primary', '')
        
        section_map = {
            'research': ['methodology', 'results', 'analysis', 'findings'],
            'create': ['implementation', 'design', 'architecture', 'examples'],
            'review': ['overview', 'summary', 'evaluation', 'comparison'],
            'learn': ['introduction', 'concepts', 'examples', 'tutorials'],
            'solve': ['solution', 'approach', 'implementation', 'troubleshooting']
        }
        
        return section_map.get(action, ['general'])
    
    def _identify_quality_indicators(self, persona_data: Dict) -> List[str]:
        """Identify quality indicators based on persona"""
        level = persona_data.get('expertise_level', 'intermediate')
        
        if level == 'expert':
            return ['citations', 'data', 'methodology', 'peer-reviewed']
        elif level == 'beginner':
            return ['examples', 'illustrations', 'step-by-step', 'clear']
        else:
            return ['practical', 'applicable', 'well-structured', 'comprehensive']