# src/persona_analysis/parsers/job_parser.py
import re
from typing import Dict, List, Set

class JobParser:
    """Parse job-to-be-done descriptions"""
    
    def __init__(self):
        self.action_verbs = {
            'research': ['research', 'investigate', 'study', 'analyze', 'examine'],
            'create': ['create', 'develop', 'build', 'design', 'write'],
            'review': ['review', 'evaluate', 'assess', 'critique', 'summarize'],
            'learn': ['learn', 'understand', 'comprehend', 'study', 'master'],
            'solve': ['solve', 'fix', 'troubleshoot', 'debug', 'resolve']
        }
        
        self.output_types = {
            'report': ['report', 'summary', 'overview', 'document'],
            'analysis': ['analysis', 'evaluation', 'assessment', 'review'],
            'plan': ['plan', 'strategy', 'proposal', 'roadmap'],
            'solution': ['solution', 'answer', 'resolution', 'fix'],
            'presentation': ['presentation', 'slides', 'deck', 'pitch']
        }
    
    def parse(self, job_text: str) -> Dict:
        """Parse job description into structured data"""
        job_data = {
            'original': job_text,
            'action': self._identify_action(job_text),
            'target': self._identify_target(job_text),
            'output': self._identify_output(job_text),
            'constraints': self._identify_constraints(job_text),
            'keywords': self._extract_job_keywords(job_text),
            'focus_areas': self._extract_focus_areas(job_text),
            'deliverables': self._extract_deliverables(job_text)
        }
        
        return job_data
    
    def _identify_action(self, text: str) -> Dict:
        """Identify primary action in job"""
        text_lower = text.lower()
        identified_actions = []
        
        for category, verbs in self.action_verbs.items():
            for verb in verbs:
                if verb in text_lower:
                    identified_actions.append({
                        'category': category,
                        'verb': verb,
                        'position': text_lower.find(verb)
                    })
        
        # Sort by position (earlier = more important)
        identified_actions.sort(key=lambda x: x['position'])
        
        if identified_actions:
            return {
                'primary': identified_actions[0]['category'],
                'verbs': [a['verb'] for a in identified_actions]
            }
        
        return {'primary': 'analyze', 'verbs': []}
    
    def _identify_target(self, text: str) -> List[str]:
        """Identify what the job targets"""
        # Simple approach without POS tagging - look for nouns after common action verbs
        tokens = re.findall(r'\b\w+\b', text.lower())
        
        targets = []
        action_verbs_flat = [verb for verb_list in self.action_verbs.values() for verb in verb_list]
        
        # Look for words after action verbs
        for i, token in enumerate(tokens):
            if token in action_verbs_flat and i + 1 < len(tokens):
                # Take the next few words as potential targets
                for j in range(i + 1, min(i + 4, len(tokens))):
                    next_word = tokens[j]
                    if (len(next_word) > 2 and 
                        next_word not in ['the', 'a', 'an', 'and', 'or', 'for', 'to', 'of']):
                        targets.append(next_word)
        
        return list(set(targets))
    
    def _identify_output(self, text: str) -> Dict:
        """Identify expected output type"""
        text_lower = text.lower()
        identified_outputs = []
        
        for output_type, keywords in self.output_types.items():
            for keyword in keywords:
                if keyword in text_lower:
                    identified_outputs.append(output_type)
                    break
        
        return {
            'types': identified_outputs if identified_outputs else ['document'],
            'explicit': len(identified_outputs) > 0
        }
    
    def _identify_constraints(self, text: str) -> List[str]:
        """Identify any constraints or requirements"""
        constraints = []
        
        # Time constraints
        time_patterns = [
            r'within\s+(\d+\s+\w+)',
            r'by\s+([A-Za-z]+ \d+)',
            r'deadline[:\s]+([^\.,]+)',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                constraints.append(f"Time: {match.group(1)}")
        
        # Scope constraints
        scope_keywords = ['focus on', 'specifically', 'only', 'limited to']
        for keyword in scope_keywords:
            if keyword in text.lower():
                # Extract the constraint
                idx = text.lower().find(keyword)
                constraint_text = text[idx:idx+50].split('.')[0]
                constraints.append(f"Scope: {constraint_text}")
        
        return constraints
    
    def _extract_job_keywords(self, text: str) -> List[str]:
        """Extract important keywords from job description"""
        # Simple tokenization without POS tagging
        tokens = re.findall(r'\b\w+\b', text.lower())
        
        keywords = []
        
        # Extract meaningful words
        for word in tokens:
            if (len(word) > 2 and 
                word not in {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'are', 'was', 'have', 'been'} and
                not word.isdigit()):
                keywords.append(word)
        
        return list(set(keywords))
    
    def _extract_focus_areas(self, text: str) -> List[str]:
        """Extract specific focus areas mentioned"""
        focus_patterns = [
            r'focus(?:ing)? on ([^,\.]+)',
            r'concentrat(?:ing|e) on ([^,\.]+)',
            r'emphasis on ([^,\.]+)',
            r'particularly ([^,\.]+)',
            r'especially ([^,\.]+)'
        ]
        
        focus_areas = []
        
        for pattern in focus_patterns:
            matches = re.findall(pattern, text, re.I)
            focus_areas.extend(matches)
        
        return [area.strip() for area in focus_areas]
    
    def _extract_deliverables(self, text: str) -> List[str]:
        """Extract specific deliverables mentioned"""
        deliverable_patterns = [
            r'deliver(?:able)?s?[:\s]+([^\.]+)',
            r'output[:\s]+([^\.]+)',
            r'produce[:\s]+([^\.]+)',
            r'create[:\s]+([^\.]+)'
        ]
        
        deliverables = []
        
        for pattern in deliverable_patterns:
            matches = re.findall(pattern, text, re.I)
            for match in matches:
                # Split by common delimiters
                items = re.split(r'[,;]|and', match)
                deliverables.extend([item.strip() for item in items if item.strip()])
        
        return list(set(deliverables))