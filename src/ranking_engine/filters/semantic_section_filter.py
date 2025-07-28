# src/ranking_engine/filters/semantic_section_filter.py
import re
import numpy as np
from typing import List, Dict, Set, Optional
from collections import defaultdict
import logging
import os
from pathlib import Path

# Try to import sentence transformers, fallback to TF-IDF if not available
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

class SemanticSectionFilter:
    """Dynamic Semantic Scoring using sentence transformers or TF-IDF - General Purpose Solution"""
    
    def __init__(self):
        self.model = None
        self.vectorizer = None
        
        # Try to load sentence transformer model first (better accuracy)
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            model_path = Path(__file__).parent.parent.parent.parent / "models" / "sentence_transformer"
            if model_path.exists():
                try:
                    self.model = SentenceTransformer(str(model_path))
                    logger.info("✅ Loaded sentence transformer model for semantic similarity")
                except Exception as e:
                    logger.warning(f"Failed to load sentence transformer: {e}")
                    self._init_tfidf_fallback()
            else:
                logger.warning(f"Sentence transformer model not found at {model_path}")
                self._init_tfidf_fallback()
        else:
            logger.warning("sentence-transformers not available, using TF-IDF fallback")
            self._init_tfidf_fallback()
        
        # Generic anti-section patterns (sections that are typically not useful)
        self.anti_section_patterns = [
            r'^introduction$',
            r'^conclusion$', 
            r'^foreword$',
            r'^preface$',
            r'^table\s+of\s+contents?$',
            r'^contents?$',
            r'^index$',
            r'^references?$',
            r'^bibliography$',
            r'^acknowledgments?$',
            r'^appendix.*$',
            r'^about\s+the\s+author$',
            r'^about\s+this\s+book$',
            r'^glossary$',
            r'^notes?$',
            r'^further\s+reading$',
            r'^suggested\s+reading$',
            r'^abstract$',
            r'^summary$',
            r'^overview$',
            r'^disclaimer$',
            r'^copyright$',
            r'^legal$',
            r'^terms$',
            r'^privacy$'
        ]
    
    def _init_tfidf_fallback(self):
        """Initialize TF-IDF vectorizer as fallback"""
        self.vectorizer = TfidfVectorizer(
            max_features=2000,
            stop_words='english',
            ngram_range=(1, 3),
            min_df=1,
            max_df=0.85,
            sublinear_tf=True,
            norm='l2'
        )
        logger.info("📊 TF-IDF vectorizer initialized as fallback for semantic similarity")
    
    def filter(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Apply dynamic semantic filtering with anti-section logic"""
        if not sections:
            return sections
        
        # STEP 1: Apply Anti-Section Filter - Remove useless generic sections  
        useful_sections = self._apply_anti_section_filter(sections)
        logger.info(f"Anti-section filter: {len(sections)} -> {len(useful_sections)} sections")
        
        # STEP 2: Apply Dynamic Semantic Scoring (offline)
        scored_sections = self._apply_semantic_scoring(useful_sections, query_profile)
        logger.info(f"Semantic scoring applied to {len(scored_sections)} sections")
        
        return scored_sections
    
    def _apply_anti_section_filter(self, sections: List[Dict]) -> List[Dict]:
        """STEP 1: Filter out generic, useless sections"""
        filtered_sections = []
        
        for section in sections:
            title = section.get('title', '').lower().strip()
            
            # Check against anti-section patterns
            is_generic = False
            for pattern in self.anti_section_patterns:
                if re.match(pattern, title, re.IGNORECASE):
                    is_generic = True
                    break
            
            if not is_generic:
                filtered_sections.append(section)
        
        return filtered_sections
    
    def _apply_semantic_scoring(self, sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Apply semantic similarity scoring using sentence transformers or TF-IDF"""
        
        # Extract intent from query profile
        persona_data = query_profile.get('persona', {})
        job_data = query_profile.get('job', {})
        
        # Build user intent text from available data
        persona_text = self._extract_persona_text(persona_data)
        job_text = job_data.get('description', '') if isinstance(job_data, dict) else str(job_data)
        
        # Create comprehensive intent description
        intent_text = self._build_intent_text(persona_text, job_text, query_profile)
        
        if not intent_text.strip():
            logger.warning("No meaningful intent text available for semantic scoring")
            return sections
        
        logger.info(f"Intent text: '{intent_text[:100]}...'")
        
        try:
            # Prepare section texts
            section_texts = []
            valid_sections = []
            
            for section in sections:
                title = section.get('title', '')
                content = section.get('content', '')
                section_text = f"{title} {content}".strip()
                
                if section_text:
                    section_texts.append(section_text)
                    valid_sections.append(section)
            
            if not section_texts:
                return sections
            
            # Calculate semantic similarities
            if self.model:
                # Use sentence transformer for better accuracy
                similarities = self._calculate_similarities_transformer(intent_text, section_texts)
            else:
                # Fallback to TF-IDF
                similarities = self._calculate_similarities_tfidf(intent_text, section_texts)
            
            # Add scores to sections
            for i, section in enumerate(valid_sections):
                section['semantic_score'] = float(similarities[i])
            
            # Sort by semantic similarity score (highest first)
            scored_sections = sorted(valid_sections, key=lambda x: x.get('semantic_score', 0), reverse=True)
            
            # Log top scoring sections for debugging
            logger.info("Top 5 semantically relevant sections:")
            for i, section in enumerate(scored_sections[:5]):
                score = section.get('semantic_score', 0)
                title = section.get('title', 'Unknown')
                logger.info(f"  {i+1}. {title} (score: {score:.3f})")
            
            return scored_sections
            
        except Exception as e:
            logger.error(f"Error in semantic scoring: {e}")
            return sections
    
    def _extract_persona_text(self, persona_data: Dict) -> str:
        """Extract meaningful text from persona data structure"""
        if not isinstance(persona_data, dict):
            return str(persona_data)
        
        # Combine available persona fields into meaningful text
        text_parts = []
        
        # Add role if available
        role = persona_data.get('role', '')
        if role:
            text_parts.append(role)
        
        # Add focus areas
        focus_areas = persona_data.get('focus_areas', [])
        if focus_areas:
            text_parts.extend(focus_areas)
        
        # Add specializations
        specializations = persona_data.get('specializations', [])
        if specializations:
            text_parts.extend(specializations)
        
        # Add keywords
        keywords = persona_data.get('keywords', [])
        if keywords:
            text_parts.extend(keywords[:5])  # Limit to prevent bloat
        
        return ' '.join(text_parts).strip()
    
    def _build_intent_text(self, persona_text: str, job_text: str, query_profile: Dict) -> str:
        """Build comprehensive intent text with intelligent query expansion"""
        intent_parts = []
        
        # Base intent from persona and job
        if persona_text:
            intent_parts.append(persona_text)
        if job_text:
            intent_parts.append(job_text)
        
        # CRITICAL: Add persona-specific query expansion for stronger signal
        expansion = self._create_persona_expansion(persona_text, job_text, query_profile)
        if expansion:
            intent_parts.append(expansion)
        
        # Add query keywords if available
        query_data = query_profile.get('query', {})
        if isinstance(query_data, dict):
            primary_keywords = query_data.get('primary_keywords', [])
            if primary_keywords:
                intent_parts.extend(primary_keywords[:5])
        
        # Add domain context if available
        domain_data = query_profile.get('domain', {})
        if isinstance(domain_data, dict):
            domain_primary = domain_data.get('primary', '')
            if domain_primary:
                intent_parts.append(domain_primary)
        
        return ' '.join(intent_parts).strip()
    
    def _create_persona_expansion(self, persona_text: str, job_text: str, query_profile: Dict) -> str:
        """Create universal query expansion based on job requirements and context"""
        expansion_keywords = []
        
        # Analyze the job description for key indicators
        job_lower = job_text.lower()
        persona_lower = persona_text.lower()
        
        # Universal dietary requirement expansion
        if any(term in job_lower for term in ['vegetarian', 'veggie', 'plant-based']):
            expansion_keywords.extend([
                "vegetarian recipes", "plant-based dishes", "vegetables", "legumes", 
                "grains", "tofu", "tempeh", "quinoa", "lentils", "beans"
            ])
        
        if any(term in job_lower for term in ['gluten-free', 'gluten free', 'celiac']):
            expansion_keywords.extend([
                "gluten-free recipes", "rice dishes", "corn tortillas", "quinoa",
                "naturally gluten-free", "certified gluten-free ingredients"
            ])
        
        # Universal meal context expansion
        if any(term in job_lower for term in ['dinner', 'evening', 'main course']):
            expansion_keywords.extend([
                "dinner recipes", "main courses", "entrees", "hearty meals",
                "evening dishes", "substantial dishes", "dinner menu"
            ])
        
        if any(term in job_lower for term in ['buffet', 'corporate', 'catering']):
            expansion_keywords.extend([
                "buffet style", "crowd-pleasing", "easy serving", "large quantities",
                "corporate catering", "group dining", "shareable dishes"
            ])
        
        # Universal cuisine and preparation style expansion
        if any(term in job_lower for term in ['healthy', 'nutritious', 'wellness']):
            expansion_keywords.extend([
                "healthy ingredients", "nutritious meals", "fresh vegetables",
                "whole grains", "balanced nutrition"
            ])
        
        # Food contractor professional context
        if any(term in persona_lower for term in ['food contractor', 'caterer', 'chef']):
            expansion_keywords.extend([
                "professional recipes", "scalable dishes", "food service",
                "catering menu", "commercial preparation"
            ])
        
        return ' '.join(expansion_keywords)
    
    def _calculate_similarities_transformer(self, intent_text: str, section_texts: List[str]) -> np.ndarray:
        """Calculate similarities using sentence transformer model"""
        try:
            # Encode the intent and all sections
            intent_embedding = self.model.encode([intent_text])
            section_embeddings = self.model.encode(section_texts)
            
            # Calculate cosine similarities
            similarities = cosine_similarity(intent_embedding, section_embeddings)[0]
            return similarities
            
        except Exception as e:
            logger.error(f"Error in transformer similarity calculation: {e}")
            # Fallback to TF-IDF
            return self._calculate_similarities_tfidf(intent_text, section_texts)
    
    def _calculate_similarities_tfidf(self, intent_text: str, section_texts: List[str]) -> np.ndarray:
        """Calculate similarities using TF-IDF as fallback"""
        try:
            # Combine intent and sections for fitting vectorizer
            all_texts = [intent_text] + section_texts
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            
            # Calculate cosine similarities between intent and sections
            intent_vector = tfidf_matrix[0:1]  # First row is intent
            section_vectors = tfidf_matrix[1:]  # Rest are sections
            
            similarities = cosine_similarity(intent_vector, section_vectors)[0]
            return similarities
            
        except Exception as e:
            logger.error(f"Error in TF-IDF similarity calculation: {e}")
            # Return zeros as ultimate fallback
            return np.zeros(len(section_texts))
