# src/ranking_engine/filters/constraint_filter.py
import re
from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)

class ConstraintFilter:
    """Universal constraint-based filtering for dietary restrictions and context requirements"""
    
    def __init__(self):
        # Universal dietary constraint patterns (extracted from job requirements)
        self.dietary_patterns = {
            'vegetarian': {
                'exclude_keywords': [
                    'beef', 'pork', 'chicken', 'turkey', 'duck', 'lamb', 'veal', 'bacon', 
                    'ham', 'sausage', 'ground beef', 'ground pork', 'ground chicken',
                    'fish', 'salmon', 'tuna', 'cod', 'shrimp', 'crab', 'lobster',
                    'anchovy', 'sardine', 'fish sauce', 'worcestershire', 'gelatin'
                ],
                'exclude_patterns': [
                    r'\b\d+\s*(?:oz|ounces?|lb|lbs?|pounds?)\s+(?:beef|pork|chicken|fish|meat)\b',
                    r'\bground\s+(?:beef|pork|chicken|turkey)\b',
                    r'\b(?:chicken|beef|pork|fish)\s+(?:stock|broth|bouillon)\b'
                ]
            },
            'gluten_free': {
                'exclude_keywords': [
                    'flour', 'wheat', 'bread', 'breadcrumbs', 'pasta', 'noodles',
                    'soy sauce', 'teriyaki', 'ramen', 'udon', 'couscous', 'bulgur',
                    'barley', 'malt', 'beer', 'ale', 'seitan', 'wheat flour',
                    'gnocchi', 'fettuccine', 'linguine', 'penne', 'spaghetti', 
                    'lasagna', 'ravioli', 'tortellini', 'macaroni', 'orzo'
                ],
                'exclude_patterns': [
                    r'\b(?:all-purpose|wheat|white|whole wheat)\s+flour\b',
                    r'\b\d+\s*(?:cups?|oz|ounces?|lbs?|pounds?)\s+(?:flour|breadcrumbs|pasta|noodles|gnocchi|fettuccine)\b',
                    r'\bregular\s+(?:pasta|noodles|soy sauce)\b',
                    r'\b(?:wheat|semolina|durum)\s+(?:pasta|noodles)\b'
                ]
            }
        }
        
        # Universal meal context patterns
        self.meal_contexts = {
            'breakfast': ['breakfast', 'morning', 'cereal', 'pancake', 'waffle', 'toast', 'egg'],
            'lunch': ['lunch', 'sandwich', 'salad', 'soup', 'wrap'],
            'dinner': ['dinner', 'main', 'entree', 'roast', 'stew', 'casserole'],
            'dessert': ['dessert', 'cake', 'cookie', 'pie', 'sweet', 'chocolate'],
            'snack': ['snack', 'bar', 'chip', 'cracker', 'bite']
        }
    
    def filter_by_constraints(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Filter sections based on dietary and contextual constraints from job requirements"""
        if not sections:
            return sections
            
        logger.info(f"⚡ Starting constraint filtering on {len(sections)} sections")
        
        # Extract constraints from job requirements
        dietary_constraints = self._extract_dietary_constraints(query_profile)
        meal_context = self._extract_meal_context(query_profile)
        
        logger.info(f"🔍 Detected constraints: {dietary_constraints}")
        logger.info(f"🍽️ Target meal context: {meal_context}")
        
        # Step 1: Filter by hard dietary constraints
        diet_filtered = self._filter_by_dietary_constraints(sections, dietary_constraints)
        logger.info(f"🥗 After dietary filtering: {len(diet_filtered)}/{len(sections)} sections")
        
        # Step 2: Filter by meal context 
        context_filtered = self._filter_by_meal_context(diet_filtered, meal_context)
        logger.info(f"🍽️ After context filtering: {len(context_filtered)}/{len(diet_filtered)} sections")
        
        return context_filtered
    
    def _extract_dietary_constraints(self, query_profile: Dict) -> List[str]:
        """Extract dietary constraints from job description"""
        constraints = []
        
        job_data = query_profile.get('job', {})
        job_text = str(job_data).lower() if job_data else ""
        
        # Universal pattern matching for dietary requirements
        if any(term in job_text for term in ['vegetarian', 'veggie', 'plant-based', 'no meat']):
            constraints.append('vegetarian')
            
        if any(term in job_text for term in ['gluten-free', 'gluten free', 'celiac', 'no gluten']):
            constraints.append('gluten_free')
            
        if any(term in job_text for term in ['vegan', 'plant-only', 'no dairy']):
            constraints.append('vegan')
            
        return constraints
    
    def _extract_meal_context(self, query_profile: Dict) -> str:
        """Extract target meal context from job description"""
        job_data = query_profile.get('job', {})
        job_text = str(job_data).lower() if job_data else ""
        
        # Universal pattern matching for meal context
        if any(term in job_text for term in ['dinner', 'evening', 'main course', 'entree']):
            return 'dinner'
        elif any(term in job_text for term in ['lunch', 'midday', 'noon']):
            return 'lunch'
        elif any(term in job_text for term in ['breakfast', 'morning', 'brunch']):
            return 'breakfast'
        
        return 'dinner'  # Default assumption for corporate gatherings
    
    def _filter_by_dietary_constraints(self, sections: List[Dict], constraints: List[str]) -> List[Dict]:
        """Remove sections that violate dietary constraints"""
        if not constraints:
            return sections
            
        filtered_sections = []
        excluded_count = 0
        
        for section in sections:
            content_text = self._get_section_text(section).lower()
            section_violates = False
            
            for constraint in constraints:
                if constraint in self.dietary_patterns:
                    # Check exclude keywords
                    for keyword in self.dietary_patterns[constraint]['exclude_keywords']:
                        if re.search(r'\b' + re.escape(keyword) + r'\b', content_text):
                            logger.debug(f"❌ Excluded '{section.get('title', 'Unknown')}' - contains '{keyword}' (violates {constraint})")
                            section_violates = True
                            break
                    
                    if section_violates:
                        break
                        
                    # Check exclude patterns
                    for pattern in self.dietary_patterns[constraint]['exclude_patterns']:
                        if re.search(pattern, content_text, re.IGNORECASE):
                            logger.debug(f"❌ Excluded '{section.get('title', 'Unknown')}' - matches pattern (violates {constraint})")
                            section_violates = True
                            break
                    
                    if section_violates:
                        break
            
            if not section_violates:
                filtered_sections.append(section)
            else:
                excluded_count += 1
        
        logger.info(f"🚫 Excluded {excluded_count} sections due to dietary constraints")
        return filtered_sections
    
    def _filter_by_meal_context(self, sections: List[Dict], target_context: str) -> List[Dict]:
        """Prioritize sections matching the target meal context"""
        if not target_context or target_context not in self.meal_contexts:
            return sections
            
        context_keywords = self.meal_contexts[target_context]
        
        # Score sections by meal context relevance
        scored_sections = []
        for section in sections:
            score = self._calculate_context_score(section, context_keywords, target_context)
            scored_sections.append((section, score))
        
        # Sort by context score (higher is better)
        scored_sections.sort(key=lambda x: x[1], reverse=True)
        
        # Filter out sections with very low context scores (likely wrong meal type)
        min_threshold = 0.1 if target_context == 'dinner' else 0.0
        filtered_sections = [section for section, score in scored_sections if score >= min_threshold]
        
        logger.info(f"📊 Context scoring: kept {len(filtered_sections)}/{len(sections)} sections")
        
        return filtered_sections
    
    def _calculate_context_score(self, section: Dict, context_keywords: List[str], target_context: str) -> float:
        """Calculate how well a section matches the target meal context"""
        content_text = self._get_section_text(section).lower()
        document_name = section.get('document', '').lower()
        
        score = 0.0
        
        # Boost for document name matching context
        if target_context in document_name:
            score += 0.5
        
        # Boost for content matching context keywords
        for keyword in context_keywords:
            if keyword in content_text:
                score += 0.2
        
        # Penalize breakfast content for dinner context
        if target_context == 'dinner':
            breakfast_keywords = self.meal_contexts.get('breakfast', [])
            for keyword in breakfast_keywords:
                if keyword in content_text or keyword in document_name:
                    score -= 0.3
        
        return max(score, 0.0)
    
    def _get_section_text(self, section: Dict) -> str:
        """Extract all text content from a section for analysis"""
        text_parts = []
        
        # Include title, content, and document name
        text_parts.append(section.get('title', ''))
        text_parts.append(section.get('content', ''))
        text_parts.append(section.get('document', ''))
        
        return ' '.join(filter(None, text_parts))

__all__ = ['ConstraintFilter']
