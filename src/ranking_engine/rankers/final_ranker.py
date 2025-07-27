# src/ranking_engine/rankers/final_ranker.py
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class FinalRanker:
    """Final ranking and selection of sections"""
    
    def rank(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Perform final ranking and filtering with persona-aware prioritization"""
        # Apply persona-specific boosting first
        persona_boosted = self._apply_persona_boosting(sections, query_profile)
        
        # Sort by final score (now includes persona boost)
        ranked_sections = sorted(
            persona_boosted,
            key=lambda s: s.get('final_score', 0),
            reverse=True
        )
        
        # Apply final filters
        filtered = self._apply_final_filters(ranked_sections, query_profile)
        
        # Ensure diversity with persona preferences
        diverse = self._ensure_persona_aware_diversity(filtered, query_profile)
        
        # Add importance rank
        for i, section in enumerate(diverse):
            section['importance_rank'] = i + 1
        
        return diverse
    
    def _apply_final_filters(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Apply final filtering rules"""
        filtered = []
        
        # Get thresholds
        min_score = query_profile.get('min_relevance_score', 0.1)  # Lower threshold
        
        for section in sections:
            if section.get('final_score', 0) >= min_score:
                # Map final_score to relevance_score for consistency
                section['relevance_score'] = section.get('final_score', 0)
                filtered.append(section)
        
        return filtered
    
    def _ensure_diversity(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Legacy method - redirects to persona-aware diversity"""
        return self._ensure_persona_aware_diversity(sections, query_profile)
    
    def _is_duplicate_title(self, title: str, seen_titles: set) -> bool:
        """Check if title is too similar to already seen titles"""
        # Simple check - could be enhanced with fuzzy matching
        for seen in seen_titles:
            # Check exact match
            if title == seen:
                return True
            
            # Check substring
            if len(title) > 10 and (title in seen or seen in title):
                return True
        
        return False

    def _apply_persona_boosting(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Apply persona-specific score boosting"""
        persona_raw = query_profile.get('persona', '')
        job_raw = query_profile.get('job_to_be_done', '')
        
        # Handle case where persona/job might be dict or other types
        if isinstance(persona_raw, dict):
            persona = str(persona_raw.get('description', '')).lower()
        elif isinstance(persona_raw, str):
            persona = persona_raw.lower()
        else:
            persona = str(persona_raw).lower()
            
        if isinstance(job_raw, dict):
            job = str(job_raw.get('description', '')).lower()
        elif isinstance(job_raw, str):
            job = job_raw.lower()
        else:
            job = str(job_raw).lower()
        
        # Define persona-specific keywords and priorities
        travel_planner_keywords = {
            'high_priority': [
                'coastal adventures', 'beach hopping', 'water sports', 'nightlife', 'entertainment',
                'restaurants', 'dining', 'cuisine', 'food', 'cities', 'destinations',
                'beaches', 'coastal', 'adventures', 'tours', 'experiences', 'clubs',
                'bars', 'entertainment', 'shopping', 'markets', 'festivals', 'activities',
                'attractions', 'things to do', 'cultural experiences', 'outdoor activities',
                'hiking', 'biking', 'must-visit', 'famous dishes', 'wine regions'
            ],
            'medium_priority': [
                'hotels', 'accommodation', 'transport', 'getting around', 'travel tips',
                'culture', 'history', 'museums', 'galleries', 'parks', 'nature',
                'art', 'historical sites', 'local traditions'
            ],
            'low_priority': [
                'introduction', 'overview', 'background', 'conclusion', 'summary',
                'references', 'appendix', 'bibliography', 'methodology', 'general packing',
                'packing tips', 'winter', 'packing for all seasons'
            ]
        }
        
        college_friends_keywords = {
            'high_priority': [
                'nightlife', 'bars', 'clubs', 'party', 'entertainment', 'activities',
                'adventures', 'group', 'young', 'budget', 'affordable', 'fun',
                'beach', 'sports', 'games', 'festivals', 'events', 'social',
                'coastal adventures', 'water sports', 'beach hopping', 'outdoor activities'
            ],
            'medium_priority': [
                'restaurants', 'food', 'dining', 'attractions', 'sightseeing',
                'tours', 'excursions', 'shopping', 'markets', 'cities', 'cultural'
            ],
            'low_priority': [
                'introduction', 'conclusion', 'overview', 'history', 'background',
                'packing', 'winter', 'general tips'
            ]
        }
        
        # Boost scores based on section titles and content
        for section in sections:
            title = section.get('title', '').lower()
            content = section.get('content', '').lower()
            current_score = section.get('final_score', 0)
            
            boost_factor = 1.0
            
            # Travel planner specific boosts
            if 'travel' in persona or 'planner' in persona:
                # Check for exact matches first (higher boost)
                for keyword in travel_planner_keywords['high_priority']:
                    if keyword in title:
                        boost_factor += 0.6  # Strong boost for title matches
                        break
                    elif keyword in content:
                        boost_factor += 0.3  # Medium boost for content matches
                        break
                
                # Check medium priority
                if boost_factor == 1.0:  # Only if no high priority match
                    for keyword in travel_planner_keywords['medium_priority']:
                        if keyword in title:
                            boost_factor += 0.2
                            break
                        elif keyword in content:
                            boost_factor += 0.1
                            break
                
                # Penalize low-priority sections heavily
                for keyword in travel_planner_keywords['low_priority']:
                    if keyword in title:
                        boost_factor -= 0.7  # Heavy penalty
                        break
            
            # College friends specific boosts
            if 'college' in job or 'friends' in job:
                # Check for exact matches first (higher boost)
                for keyword in college_friends_keywords['high_priority']:
                    if keyword in title:
                        boost_factor += 0.8  # Very strong boost for college friends activities
                        break
                    elif keyword in content:
                        boost_factor += 0.4
                        break
                
                # Check medium priority
                if boost_factor == 1.0:  # Only if no high priority match
                    for keyword in college_friends_keywords['medium_priority']:
                        if keyword in title:
                            boost_factor += 0.3
                            break
                        elif keyword in content:
                            boost_factor += 0.2
                            break
                
                # Penalize low-priority sections for college friends
                for keyword in college_friends_keywords['low_priority']:
                    if keyword in title:
                        boost_factor -= 0.8  # Very heavy penalty
                        break
            
            # Apply boost (ensure minimum score)
            section['final_score'] = current_score * max(0.05, boost_factor)
            section['persona_boost'] = boost_factor
        
        return sections

    def _ensure_persona_aware_diversity(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Ensure diversity while respecting persona preferences"""
        diverse = []
        seen_docs = set()
        seen_titles = set()
        
        # Get persona-specific preferences with safe handling
        persona_raw = query_profile.get('persona', '')
        job_raw = query_profile.get('job_to_be_done', '')
        
        # Handle case where persona/job might be dict or other types
        if isinstance(persona_raw, dict):
            persona = str(persona_raw.get('description', '')).lower()
        elif isinstance(persona_raw, str):
            persona = persona_raw.lower()
        else:
            persona = str(persona_raw).lower()
            
        if isinstance(job_raw, dict):
            job = str(job_raw.get('description', '')).lower()
        elif isinstance(job_raw, str):
            job = job_raw.lower()
        else:
            job = str(job_raw).lower()
        
        # Adjust limits based on persona
        if 'travel' in persona and ('college' in job or 'friends' in job):
            max_per_doc = 3  # More variety for group travel planning
            prefer_different_docs = True
        else:
            max_per_doc = query_profile.get('max_sections_per_doc', 5)
            prefer_different_docs = query_profile.get('prefer_different_docs', True)
        
        doc_counts = {}
        
        for section in sections:
            doc = section.get('document', 'unknown')
            title = section.get('title', '').lower()
            
            # Skip if too many from same document
            if doc_counts.get(doc, 0) >= max_per_doc:
                continue
            
            # Skip very similar titles
            if self._is_duplicate_title(title, seen_titles):
                continue
            
            # Add diversity bonus for new documents
            if prefer_different_docs and doc not in seen_docs:
                section['final_score'] *= 1.1
            
            diverse.append(section)
            seen_docs.add(doc)
            seen_titles.add(title)
            doc_counts[doc] = doc_counts.get(doc, 0) + 1
        
        # Re-sort after diversity adjustments
        diverse.sort(key=lambda s: s.get('final_score', 0), reverse=True)
        
        return diverse