# src/subsection_extraction/refiners/content_synthesizer.py
import re
from typing import List, Dict, Set, Optional
from collections import defaultdict

class ContentSynthesizer:
    """Advanced content synthesizer for high-quality, natural text generation"""
    
    def __init__(self):
        # Universal sentence quality indicators (not domain-specific)
        self.quality_indicators = [
            r'\b(?:provides?|offers?|includes?|contains?|features?)\s+[^.!?]*',  # Service descriptions
            r'\b(?:best|top|recommended|popular|excellent|high-quality)\s+[^.!?]*',  # Quality descriptions
            r'\b(?:located|situated|address|phone|contact|email|website)\s*:?\s*[^.!?]*',  # Contact info
            r'\b\d+(?:\.\d+)?\s*(?:units?|items?|hours?|minutes?|dollars?|\$|percent|\%)\b[^.!?]*',  # Specific measurements
            r'\b[A-Z][a-zA-Z\s-]+(?:Company|Corporation|Institute|Department|Center|Office|Building)\b[^.!?]*',  # Organizations
            r'\b(?:ingredients?|materials?|tools?|equipment|requirements?)\s*:?\s*[^.!?]*',  # Lists and requirements
            r'\b(?:step|phase|stage|process|procedure|method)\s+\d+[^.!?]*',  # Process descriptions
        ]
        
        # Patterns to avoid in synthesis
        self.avoid_patterns = [
            r'^in conclusion',
            r'^to summarize',
            r'^as mentioned',
            r'^it should be noted',
            r'^furthermore',
            r'the above mentioned',
            r'aforementioned'
        ]

    def synthesize_subsections(self, subsections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Main interface for synthesizing subsections"""
        return self.synthesize(subsections, query_profile)
    
    def synthesize(self, sections: List[Dict], query_profile: Dict = None) -> List[Dict]:
        """STEP 3: Execute High-Quality Synthesis with sentence-level semantic analysis"""
        synthesized = []
        
        # Get the sentence transformer model for semantic similarity
        model = self._get_sentence_transformer_model()
        
        for section in sections:
            content = section.get('content', '') or section.get('refined_text', '')
            if not content or len(content.strip()) < 50:  # Lowered threshold for universal content
                continue
            
            # Universal content filtering for quality
            persona_filtered_content = self._filter_content_by_persona(content, query_profile)
            
            if not persona_filtered_content:
                continue
            
            # Step A: Relevant Sentence Extraction (Extractive Summarization)
            relevant_sentences = self._extract_relevant_sentences(
                persona_filtered_content, query_profile, model
            )
            
            if relevant_sentences:
                # Step B: Coherent Paragraph Generation (Abstractive Cleanup)
                synthesized_text = self._generate_coherent_paragraph(relevant_sentences)
                
                if synthesized_text and len(synthesized_text) > 50:
                    synthesized_section = section.copy()
                    synthesized_section['refined_text'] = synthesized_text
                    synthesized.append(synthesized_section)
        
        return synthesized
    
    def _get_sentence_transformer_model(self):
        """Get the sentence transformer model for semantic similarity"""
        try:
            from sentence_transformers import SentenceTransformer
            from pathlib import Path
            
            model_path = Path(__file__).parent.parent.parent.parent / "models" / "sentence_transformer"
            if model_path.exists():
                return SentenceTransformer(str(model_path))
        except Exception:
            pass
        return None
    
    def _extract_relevant_sentences(self, content: str, query_profile: Dict, model) -> List[str]:
        """
        COMPLETE EXTRACTIVE SUMMARIZATION PIPELINE
        Step A: Extract the most semantically relevant sentences using sentence transformers
        """
        # STEP 1: Sentence Segmentation
        sentences = self._split_sentences_advanced(content)
        
        if len(sentences) < 2:
            return sentences
        
        # STEP 2: Build persona vector from query profile
        persona_text = self._build_persona_intent(query_profile)
        
        if not persona_text or not model:
            # Fallback to quality-based extraction if no model
            return self._extract_quality_sentences_fallback(sentences)[:5]
        
        try:
            # STEP 3: Sentence Embedding - Create vector embeddings for all sentences
            print(f"📝 Processing {len(sentences)} sentences for extractive summarization...")
            
            # DEBUG: Check persona text
            print(f"🎯 Persona intent: {persona_text[:100]}...")
            
            persona_embedding = model.encode([persona_text])
            sentence_embeddings = model.encode(sentences)
            
            # STEP 4: Relevance Scoring - Calculate cosine similarity
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity(persona_embedding, sentence_embeddings)[0]
            
            print(f"🎯 Similarity scores: min={min(similarities):.3f}, max={max(similarities):.3f}, avg={sum(similarities)/len(similarities):.3f}")
            
            # STEP 5: Selection with quality improvements
            selected_sentences = self._intelligent_sentence_selection(sentences, similarities)
            
            print(f"✅ Selected {len(selected_sentences)} sentences for final summary")
            return selected_sentences
            
        except Exception as e:
            print(f"❌ Error in extractive summarization: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to quality-based extraction
            return self._extract_quality_sentences_fallback(sentences)[:5]
    
    def _intelligent_sentence_selection(self, sentences: List[str], similarities: List[float]) -> List[str]:
        """
        STEP 3: QUALITY IMPROVEMENTS
        - Dynamic Summary Length using similarity thresholds
        - Maximal Marginal Relevance (MMR) for diversity
        """
        if not sentences or not similarities:
            return []
        
        # DYNAMIC THRESHOLD: Adapt based on content quality
        avg_similarity = sum(similarities) / len(similarities)
        max_similarity = max(similarities)
        
        # Smart threshold: higher standards for high-quality content
        if max_similarity > 0.7:
            threshold = 0.65  # High standards for excellent content
        elif max_similarity > 0.5:
            threshold = 0.45  # Medium standards for good content
        else:
            threshold = 0.3   # Lower standards for mixed content
        
        print(f"🎯 Using dynamic threshold: {threshold:.3f} (max_sim: {max_similarity:.3f})")
        
        # STEP 1: Filter by relevance threshold
        candidate_pairs = []
        for i, (sentence, similarity) in enumerate(zip(sentences, similarities)):
            if similarity >= threshold and len(sentence.strip()) > 30:  # Quality filter
                candidate_pairs.append((sentence, similarity, i))
        
        if not candidate_pairs:
            # Fallback: take top 3 if no sentences meet threshold
            sorted_pairs = sorted(zip(sentences, similarities, range(len(sentences))), 
                                key=lambda x: x[1], reverse=True)
            candidate_pairs = sorted_pairs[:3]
        
        print(f"📊 {len(candidate_pairs)} sentences passed threshold filter")
        
        # STEP 2: Apply MMR (Maximal Marginal Relevance) for diversity
        selected_sentences = self._apply_mmr_selection(candidate_pairs)
        
        return selected_sentences
    
    def _apply_mmr_selection(self, candidate_pairs: List[tuple]) -> List[str]:
        """
        Apply Maximal Marginal Relevance (MMR) algorithm
        Balance between: (1) relevance to query (2) novelty vs already selected
        """
        if not candidate_pairs:
            return []
        
        # Sort by relevance score first
        candidate_pairs = sorted(candidate_pairs, key=lambda x: x[1], reverse=True)
        
        selected = []
        remaining = candidate_pairs.copy()
        
        # Always take the most relevant sentence first
        best_sentence, best_score, best_idx = remaining.pop(0)
        selected.append(best_sentence)
        
        print(f"🥇 First selection: {best_sentence[:60]}... (score: {best_score:.3f})")
        
        # MMR loop: balance relevance vs diversity
        while remaining and len(selected) < 5:  # Max 5 sentences
            best_mmr_score = -1
            best_candidate = None
            best_index = -1
            
            for i, (candidate, relevance_score, orig_idx) in enumerate(remaining):
                # Calculate diversity penalty: similarity to already selected sentences
                diversity_penalty = self._calculate_diversity_penalty(candidate, selected)
                
                # MMR formula: λ * relevance - (1-λ) * max_similarity_to_selected
                lambda_param = 0.7  # Weight: 70% relevance, 30% diversity
                mmr_score = lambda_param * relevance_score - (1 - lambda_param) * diversity_penalty
                
                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    best_candidate = candidate
                    best_index = i
            
            if best_candidate and best_mmr_score > 0.2:  # Quality threshold for MMR
                selected.append(best_candidate)
                remaining.pop(best_index)
                print(f"✨ MMR selection: {best_candidate[:60]}... (MMR: {best_mmr_score:.3f})")
            else:
                break  # No more good candidates
        
        return selected
    
    def _calculate_diversity_penalty(self, candidate: str, selected_sentences: List[str]) -> float:
        """Calculate how similar a candidate sentence is to already selected sentences"""
        if not selected_sentences:
            return 0.0
        
        # Simple word-overlap diversity measure
        candidate_words = set(candidate.lower().split())
        max_overlap = 0.0
        
        for selected in selected_sentences:
            selected_words = set(selected.lower().split())
            if candidate_words and selected_words:
                overlap = len(candidate_words & selected_words) / len(candidate_words | selected_words)
                max_overlap = max(max_overlap, overlap)
        
        return max_overlap
        
        # Create sentence-score pairs and filter by minimum relevance
        sentence_scores = [(sent, score) for sent, score in zip(sentences, similarities) if score >= min_score]
        
        if not sentence_scores:
            # If no sentences meet threshold, take top 3 anyway
            sentence_scores = list(zip(sentences, similarities))
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            return [sent for sent, _ in sentence_scores[:3]]
        
        # Sort by relevance score
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        # MMR Selection: Balance relevance and diversity
        selected = []
        remaining = sentence_scores.copy()
        
        # First, select the single best sentence
        if remaining:
            best_sentence, best_score = remaining.pop(0)
            selected.append(best_sentence)
        
        # Then select up to 4 more sentences using MMR
        while len(selected) < 5 and remaining:
            best_idx = 0
            best_mmr_score = -1
            
            for i, (candidate_sent, relevance_score) in enumerate(remaining):
                # Calculate diversity penalty (how similar to already selected sentences)
                diversity_penalty = 0
                for selected_sent in selected:
                    # Simple word overlap as diversity measure
                    candidate_words = set(candidate_sent.lower().split())
                    selected_words = set(selected_sent.lower().split())
                    if candidate_words and selected_words:
                        overlap = len(candidate_words & selected_words) / len(candidate_words | selected_words)
                        diversity_penalty = max(diversity_penalty, overlap)
                
                # MMR Score: Balance relevance (0.7 weight) vs diversity (0.3 weight)
                mmr_score = 0.7 * relevance_score - 0.3 * diversity_penalty
                
                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    best_idx = i
            
            # Add the best MMR sentence
            selected_sentence, _ = remaining.pop(best_idx)
            selected.append(selected_sentence)
        
        # Maintain original order for better flow
        ordered_selected = []
        for original_sent in sentences:
            if original_sent in selected:
                ordered_selected.append(original_sent)
            if len(ordered_selected) >= len(selected):
                break
        
        return ordered_selected
    
    def _build_persona_intent(self, query_profile: Dict) -> str:
        """Build universal persona intent text for semantic comparison - works for any domain"""
        parts = []
        
        # Get job description (primary intent source)
        job_data = query_profile.get('job', {})
        job_description = job_data.get('description', '') if isinstance(job_data, dict) else str(job_data)
        if job_description:
            parts.append(job_description)
        
        # Get persona info (role and context)
        persona_data = query_profile.get('persona', {})
        if isinstance(persona_data, dict):
            role = persona_data.get('role', '')
            if role:
                parts.append(role)
            
            # Add any available persona fields universally
            for field in ['specializations', 'focus_areas', 'keywords']:
                field_data = persona_data.get(field, [])
                if isinstance(field_data, list):
                    parts.extend(field_data[:3])  # Limit to prevent bloat
                elif field_data:
                    parts.append(str(field_data))
        
        # Universal context expansion based on job analysis (not hardcoded patterns)
        context_expansion = self._extract_universal_context(job_description, persona_data)
        if context_expansion:
            parts.append(context_expansion)
        
        return ' '.join(parts)
    
    def _extract_universal_context(self, job_description: str, persona_data: Dict) -> str:
        """Extract universal context keywords from job and persona without hardcoded domain patterns"""
        context_keywords = []
        job_lower = job_description.lower()
        
        # Universal professional context patterns
        role = persona_data.get('role', '') if isinstance(persona_data, dict) else ''
        role_lower = role.lower()
        
        # Business contexts
        if any(term in job_lower for term in ['business', 'corporate', 'company', 'enterprise']):
            context_keywords.extend(['professional', 'business', 'corporate'])
        
        if any(term in job_lower for term in ['analysis', 'analyze', 'research', 'data']):
            context_keywords.extend(['analytical', 'detailed', 'comprehensive'])
        
        # Event and planning contexts  
        if any(term in job_lower for term in ['event', 'planning', 'organize', 'manage']):
            context_keywords.extend(['organized', 'planned', 'structured'])
        
        if any(term in job_lower for term in ['menu', 'food', 'catering', 'dining']):
            context_keywords.extend(['culinary', 'food service', 'dining'])
        
        # Educational contexts
        if any(term in job_lower for term in ['education', 'training', 'learning', 'course']):
            context_keywords.extend(['educational', 'instructional', 'informative'])
        
        # HR and people contexts
        if any(term in role_lower for term in ['hr', 'human resources', 'recruitment']):
            context_keywords.extend(['people management', 'organizational', 'team'])
        
        # Research contexts  
        if any(term in role_lower for term in ['researcher', 'analyst', 'scientist']):
            context_keywords.extend(['research based', 'evidence', 'factual'])
        
        # Remove duplicates and return
        return ' '.join(list(set(context_keywords)))
    
    def _split_sentences_advanced(self, content: str) -> List[str]:
        """Advanced sentence splitting with better handling"""
        # Clean up the content first
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', content)
        
        # Clean and filter sentences
        cleaned_sentences = []
        for sent in sentences:
            sent = sent.strip()
            
            # Skip very short sentences or fragments
            if len(sent) < 20:
                continue
                
            # Skip sentences that are just lists of words
            words = sent.split()
            if len(words) < 5:
                continue
                
            # Ensure sentence ends properly
            if not sent.endswith(('.', '!', '?')):
                sent += '.'
                
            cleaned_sentences.append(sent)
        
        return cleaned_sentences
    
    def _extract_quality_sentences_fallback(self, sentences: List[str]) -> List[str]:
        """Fallback quality-based sentence extraction when no model available"""
        scored_sentences = []
        
        for sentence in sentences:
            score = self._calculate_sentence_quality(sentence)
            scored_sentences.append((sentence, score))
        
        # Sort by quality score
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        return [sent for sent, score in scored_sentences if score > 0.3]
    
    def _generate_coherent_paragraph(self, sentences: List[str]) -> str:
        """
        STEP B: Generate coherent paragraph with improved readability
        Format the selected sentences into a well-structured summary
        """
        if not sentences:
            return ""
        
        print(f"📝 Formatting {len(sentences)} selected sentences into coherent summary...")
        
        # Clean and validate sentences
        cleaned_sentences = []
        
        for sentence in sentences:
            # Basic sentence cleaning
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short fragments
                continue
                
            # Ensure proper sentence ending
            if not sentence.endswith(('.', '!', '?')):
                sentence += '.'
            
            # Clean up any weird spacing or formatting
            sentence = re.sub(r'\s+', ' ', sentence)  # Normalize whitespace
            sentence = re.sub(r'^[a-z\s,]*?([A-Z])', r'\1', sentence)  # Fix capitalization
            
            cleaned_sentences.append(sentence)
        
        if not cleaned_sentences:
            return sentences[0] if sentences else ""
        
        # FORMATTING LOGIC: Choose based on content structure
        if len(cleaned_sentences) == 1:
            # Single sentence: return as-is
            result = cleaned_sentences[0]
        elif len(cleaned_sentences) <= 3 and all(len(s) < 100 for s in cleaned_sentences):
            # Short sentences: combine into paragraph
            result = ' '.join(cleaned_sentences)
        else:
            # Multiple longer sentences: use bullet points for clarity
            bullet_points = []
            for sentence in cleaned_sentences:
                bullet_points.append(f"• {sentence}")
            result = '\n'.join(bullet_points)
        
        print(f"✅ Generated coherent summary: {len(result)} characters")
        return result
    
    def _filter_content_by_persona(self, content: str, query_profile: Dict) -> str:
        """Universal content filtering that preserves relevant content without hardcoded domain patterns"""
        if not query_profile or not content:
            return content
        
        # For universal approach, perform minimal filtering focused on content quality
        # rather than domain-specific exclusions that may not apply to all document types
        
        # Split content into sentences for basic quality filtering
        sentences = self._split_sentences_advanced(content)
        filtered_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Basic quality filters (universal)
            if len(sentence) < 20:  # Skip very short fragments
                continue
                
            # Skip obvious noise patterns (universal)
            if any(pattern in sentence.lower() for pattern in [
                'click here', 'read more', 'see more', 'download pdf',
                'terms and conditions', 'privacy policy'
            ]):
                continue
            
            # Keep sentences that contain substantive content
            filtered_sentences.append(sentence)
        
        # Return filtered content or original if filtering removed everything
        filtered_content = ' '.join(filtered_sentences)
        return filtered_content if filtered_content.strip() else content
    
    def _calculate_sentence_quality(self, sentence: str) -> float:
        """Calculate how valuable/actionable a sentence is"""
        score = 0.0
        
        # Check for quality indicators
        for pattern in self.quality_indicators:
            if re.search(pattern, sentence, re.IGNORECASE):
                score += 0.3
        
        # Boost for specific information (names, numbers, organizations)
        if re.search(r'\b[A-Z][a-zA-Z\s-]+(?:Company|Corporation|Institute|Department|Center|Office|Building|University)\b', sentence):
            score += 0.4  # Specific organization names
        
        if re.search(r'\b\d+', sentence):
            score += 0.2  # Contains numbers
        
        if re.search(r'\b(?:address|phone|hours|price|cost|contact)\s*:', sentence, re.IGNORECASE):
            score += 0.5  # Practical information
        
        # Penalize for generic/low-value content
        for pattern in self.avoid_patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                score -= 0.4
        
        # Penalize very generic statements
        generic_words = ['general', 'various', 'many', 'some', 'several', 'different', 'multiple']
        generic_count = sum(1 for word in generic_words if word in sentence.lower())
        if generic_count > 2:
            score -= 0.3
        
        return max(score, 0.0)
    
    def _create_natural_synthesis(self, sentences: List[str], query_profile: Dict = None) -> str:
        """Combine quality sentences into natural, coherent text"""
        if not sentences:
            return ""
        
        # Group sentences by topic/theme for better organization
        grouped_sentences = self._group_sentences_by_theme(sentences)
        
        # Build coherent paragraphs
        synthesis_parts = []
        
        for theme, theme_sentences in grouped_sentences.items():
            if len(theme_sentences) >= 2:  # Only include themes with multiple sentences
                # Rewrite and combine sentences to eliminate repetition
                coherent_text = self._create_coherent_text(theme_sentences)
                if coherent_text:
                    synthesis_parts.append(coherent_text)
        
        # If we don't have grouped content, fallback to best individual sentences
        if not synthesis_parts and sentences:
            synthesis_parts.append(self._create_coherent_text(sentences[:4]))
        
        return ' '.join(synthesis_parts)
    
    def _group_sentences_by_theme(self, sentences: List[str]) -> Dict[str, List[str]]:
        """Group sentences by universal themes/topics - works for any domain"""
        themes = {
            'procedures': [],      # Steps, processes, methods
            'specifications': [],  # Details, requirements, features  
            'descriptions': [],    # General descriptive content
            'quantitative': [],    # Numbers, measurements, data
            'practical': []        # Contact info, logistics
        }
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Universal categorization patterns
            if any(word in sentence_lower for word in ['step', 'process', 'method', 'procedure', 'instruction', 'how to']):
                themes['procedures'].append(sentence)
            elif any(word in sentence_lower for word in ['requirement', 'specification', 'feature', 'includes', 'contains']):
                themes['specifications'].append(sentence)
            elif any(word in sentence_lower for word in ['address', 'hours', 'price', 'contact', 'phone', 'cost', 'email']):
                themes['practical'].append(sentence)
            elif re.search(r'\b\d+(?:\.\d+)?\s*(?:units?|items?|hours?|percent|\%|\$|dollars?)\b', sentence_lower):
                themes['quantitative'].append(sentence)
            else:
                themes['descriptions'].append(sentence)
        
        # Remove empty themes
        return {k: v for k, v in themes.items() if v}
    
    def _create_coherent_text(self, sentences: List[str]) -> str:
        """Create coherent, natural text from sentences - universal approach"""
        if not sentences:
            return ""
        
        # For universal synthesis, clean and combine sentences directly
        # without domain-specific formatting assumptions
        clean_sentences = []
        
        for sentence in sentences[:4]:  # Limit to prevent bloat
            cleaned = self._clean_sentence(sentence)
            if cleaned and len(cleaned) > 20:
                clean_sentences.append(cleaned)
        
        if not clean_sentences:
            return ""
        
        # Simple, universal approach: combine cleaned sentences with proper spacing
        if len(clean_sentences) == 1:
            return clean_sentences[0]
        elif len(clean_sentences) <= 3:
            # Short content: combine into flowing paragraph
            return ' '.join(clean_sentences)
        else:
            # Longer content: use structured format
            return '. '.join(clean_sentences) + ('.' if not clean_sentences[-1].endswith('.') else '')
    
    def _clean_sentence(self, sentence: str) -> str:
        """Clean and normalize a sentence"""
        # Remove extra whitespace
        sentence = re.sub(r'\s+', ' ', sentence).strip()
        
        # Remove incomplete fragments at the beginning
        sentence = re.sub(r'^[a-z][^.]*?\s+([A-Z])', r'\1', sentence)
        
        # Ensure sentence ends properly
        if not sentence.endswith(('.', '!', '?')):
            sentence += '.'
        
        return sentence
