# src/persona_analysis/analyzers/synonym_expander.py
from typing import List, Dict, Set

class SynonymExpander:
    """Expand keywords with synonyms and related terms"""
    
    def __init__(self):
        # Manual expansions for common technical terms (no WordNet needed)
        self.manual_expansions = {
            'ml': ['machine learning', 'artificial intelligence', 'ai'],
            'ai': ['artificial intelligence', 'machine learning', 'ml'],
            'nlp': ['natural language processing', 'text analysis'],
            'cv': ['computer vision', 'image processing'],
            'ui': ['user interface', 'frontend', 'ux'],
            'ux': ['user experience', 'usability', 'ui'],
            'api': ['application programming interface', 'web service', 'endpoint'],
            'db': ['database', 'data storage', 'sql'],
            'dev': ['development', 'developer', 'programming'],
            'ops': ['operations', 'deployment', 'infrastructure']
        }
    
    def expand(self, keywords: Dict) -> Dict:
        """Expand keywords with synonyms"""
        expanded = {
            'original': keywords,
            'expanded': {},
            'all': set()
        }
        
        # Expand each keyword list
        for key in ['all', 'persona', 'job', 'top_10']:
            if key in keywords:
                expanded_list = self._expand_keyword_list(keywords[key])
                expanded['expanded'][key] = expanded_list
                expanded['all'].update(expanded_list)
        
        # Convert set to sorted list
        expanded['all'] = sorted(list(expanded['all']))
        
        return expanded
    
    def _expand_keyword_list(self, keywords: List[str]) -> List[str]:
        """Expand a list of keywords"""
        expanded = set()
        
        for keyword in keywords:
            # Add original keyword
            expanded.add(keyword)
            
            # Check manual expansions
            if keyword in self.manual_expansions:
                expanded.update(self.manual_expansions[keyword])
            
            # Get WordNet synonyms
            synonyms = self._get_wordnet_synonyms(keyword)
            expanded.update(synonyms)
            
            # Add variations
            variations = self._get_variations(keyword)
            expanded.update(variations)
        
        return sorted(list(expanded))
    
    def _get_wordnet_synonyms(self, word: str) -> Set[str]:
        """Get synonyms from manual mapping (WordNet disabled for offline use)"""
        synonyms = set()
        
        # Use manual synonym mapping instead of WordNet
        common_synonyms = {
            'travel': ['journey', 'trip', 'vacation', 'tourism'],
            'plan': ['organize', 'arrange', 'schedule', 'prepare'],
            'guide': ['manual', 'handbook', 'reference', 'tutorial'],
            'city': ['town', 'urban', 'metropolitan'],
            'food': ['cuisine', 'dining', 'restaurant', 'meal'],
            'hotel': ['accommodation', 'lodging', 'stay'],
            'trip': ['journey', 'travel', 'vacation', 'tour'],
            'visit': ['explore', 'see', 'tour', 'experience'],
            'explore': ['discover', 'visit', 'tour', 'see'],
            'activity': ['thing', 'attraction', 'experience'],
        }
        
        if word.lower() in common_synonyms:
            synonyms.update(common_synonyms[word.lower()])
        
        return synonyms
    
    def _get_variations(self, word: str) -> Set[str]:
        """Get common variations of a word"""
        variations = set()
        
        # Plural/singular
        if word.endswith('s'):
            variations.add(word[:-1])  # Remove 's'
        else:
            variations.add(word + 's')  # Add 's'
        
        # Common suffixes
        if word.endswith('ing'):
            base = word[:-3]
            variations.add(base)
            variations.add(base + 'ed')
        elif word.endswith('ed'):
            base = word[:-2]
            variations.add(base)
            variations.add(base + 'ing')
        
        # Common technical variations
        if word.endswith('tion'):
            base = word[:-4]
            variations.add(base + 'te')  # e.g., creation -> create
        
        return {v for v in variations if len(v) > 2}