# src/subsection_extraction/refiners/content_synthesizer.py
import re
from typing import List, Dict, Set, Optional
from collections import defaultdict

class ContentSynthesizer:
    """Advanced content synthesizer for high-quality, natural text generation"""
    
    def __init__(self):
        # Sentence quality indicators
        self.quality_indicators = [
            r'\b(?:visit|explore|enjoy|experience|try|discover)\s+[A-Z][^.!?]*',  # Action + proper noun
            r'\b(?:best|top|recommended|popular|famous)\s+[^.!?]*',  # Quality descriptions
            r'\b(?:located|situated|address|phone|contact|hours)\s*:?\s*[^.!?]*',  # Practical info
            r'\b\d+(?:\.\d+)?\s*(?:km|miles|hours|minutes|euros|\$|pounds)\b[^.!?]*',  # Specific measurements
            r'\b[A-Z][a-zA-Z\s-]+(?:Beach|Bay|Island|City|Town|Village|Restaurant|Hotel|Bar|Club)\b[^.!?]*'  # Specific places
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
            if not content or len(content.strip()) < 100:  # Skip very short content
                continue
            
            # CRITICAL: Filter content based on persona BEFORE synthesis
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
        """Build persona intent text for semantic comparison"""
        parts = []
        
        # Get job description
        job_data = query_profile.get('job', {})
        job_description = job_data.get('description', '') if isinstance(job_data, dict) else str(job_data)
        if job_description:
            parts.append(job_description)
        
        # Get persona info
        persona_data = query_profile.get('persona', {})
        if isinstance(persona_data, dict):
            role = persona_data.get('role', '')
            if role:
                parts.append(role)
        
        # Add context expansion based on persona
        if 'college' in job_description.lower() or 'friends' in job_description.lower():
            parts.append("nightlife bars clubs social activities beaches entertainment young adults")
        
        return ' '.join(parts)
    
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
        """Filter content to match persona requirements and exclude irrelevant content"""
        if not query_profile:
            return content
        
        # Get persona context
        job_data = query_profile.get('job', {})
        job_description = job_data.get('description', '') if isinstance(job_data, dict) else str(job_data)
        
        # Detect persona type
        is_college_friends = any(term in job_description.lower() 
                               for term in ['college', 'friends', 'group', 'young'])
        is_family = any(term in job_description.lower() 
                       for term in ['family', 'children', 'kids'])
        is_business = any(term in job_description.lower() 
                         for term in ['business', 'corporate', 'conference'])
        
        # Split content into sentences for filtering
        sentences = self._split_sentences_advanced(content)
        filtered_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # EXCLUDE family content for college friends
            if is_college_friends:
                if any(term in sentence_lower for term in [
                    'family-friendly', 'kid-friendly', 'children', 'kids', 'family meal',
                    'kids club', 'family resort', 'child', 'toddler', 'baby'
                ]):
                    continue  # Skip family-oriented content
                
                # PREFER young adult / social content
                if any(term in sentence_lower for term in [
                    'nightlife', 'bar', 'club', 'party', 'social', 'beach', 'adventure',
                    'group', 'friends', 'young', 'entertainment', 'fun'
                ]):
                    filtered_sentences.append(sentence)
                    continue
            
            # EXCLUDE business content for casual trips
            if not is_business and any(term in sentence_lower for term in [
                'conference', 'meeting room', 'business center', 'corporate'
            ]):
                continue
            
            # EXCLUDE family content for non-family personas
            if not is_family and any(term in sentence_lower for term in [
                'family-friendly', 'kid-friendly', 'children activities'
            ]):
                continue
            
            # Include general travel content
            if any(term in sentence_lower for term in [
                'visit', 'explore', 'experience', 'enjoy', 'discover', 'attraction',
                'restaurant', 'hotel', 'location', 'destination', 'activity'
            ]):
                filtered_sentences.append(sentence)
        
        return ' '.join(filtered_sentences)
    
    def _calculate_sentence_quality(self, sentence: str) -> float:
        """Calculate how valuable/actionable a sentence is"""
        score = 0.0
        
        # Check for quality indicators
        for pattern in self.quality_indicators:
            if re.search(pattern, sentence, re.IGNORECASE):
                score += 0.3
        
        # Boost for specific information (names, numbers, locations)
        if re.search(r'\b[A-Z][a-zA-Z\s-]+(?:Beach|Bay|Restaurant|Hotel|Bar|Club|Museum|Park)\b', sentence):
            score += 0.4  # Specific place names
        
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
        """Group sentences by common themes/topics"""
        themes = {
            'locations': [],
            'activities': [],
            'dining': [],
            'practical': [],
            'other': []
        }
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Classify by content theme
            if any(word in sentence_lower for word in ['restaurant', 'food', 'dining', 'cuisine', 'bar', 'wine', 'cooking']):
                themes['dining'].append(sentence)
            elif any(word in sentence_lower for word in ['beach', 'coast', 'island', 'city', 'town', 'village', 'location']):
                themes['locations'].append(sentence)
            elif any(word in sentence_lower for word in ['activity', 'visit', 'explore', 'enjoy', 'experience', 'adventure']):
                themes['activities'].append(sentence)
            elif any(word in sentence_lower for word in ['address', 'hours', 'price', 'contact', 'phone', 'cost']):
                themes['practical'].append(sentence)
            else:
                themes['other'].append(sentence)
        
        # Remove empty themes
        return {k: v for k, v in themes.items() if v}
    
    def _create_coherent_text(self, sentences: List[str]) -> str:
        """Rewrite sentences into coherent, natural text"""
        if not sentences:
            return ""
        
        # Extract key information from all sentences
        combined_info = self._extract_key_information(sentences)
        
        # Create natural, human-readable synthesis
        synthesis_parts = []
        
        # Start with locations if available
        if combined_info['locations']:
            locations_text = self._format_location_list(combined_info['locations'][:3])
            synthesis_parts.append(f"Key destinations include {locations_text}.")
        
        # Add activities
        if combined_info['activities']:
            activities_text = self._format_activity_list(combined_info['activities'][:3])
            synthesis_parts.append(f"Popular activities feature {activities_text}.")
        
        # Add dining information
        if combined_info['dining']:
            dining_text = self._format_dining_list(combined_info['dining'][:2])
            synthesis_parts.append(f"Dining options include {dining_text}.")
        
        # Add practical details
        if combined_info['details']:
            details_text = '. '.join(combined_info['details'][:2])
            synthesis_parts.append(details_text + '.')
        
        # If we have very little structured info, use the best original sentences
        if not synthesis_parts and sentences:
            # Clean and use the top 2-3 sentences directly
            clean_sentences = []
            for sent in sentences[:3]:
                cleaned = self._clean_sentence(sent)
                if cleaned and len(cleaned) > 20:
                    clean_sentences.append(cleaned)
            if clean_sentences:
                synthesis_parts.extend(clean_sentences)
        
        return ' '.join(synthesis_parts)
    
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
    
    def _format_location_list(self, locations: List[str]) -> str:
        """Format a list of locations naturally"""
        if len(locations) == 1:
            return locations[0]
        elif len(locations) == 2:
            return f"{locations[0]} and {locations[1]}"
        else:
            return f"{', '.join(locations[:-1])}, and {locations[-1]}"
    
    def _format_activity_list(self, activities: List[str]) -> str:
        """Format a list of activities naturally"""
        return ', '.join(activities)
    
    def _format_dining_list(self, dining: List[str]) -> str:
        """Format a list of dining options naturally"""
        return ', '.join(dining)
    
    def _extract_key_information(self, sentences: List[str]) -> Dict[str, List[str]]:
        """Extract key information elements from sentences"""
        info = {
            'locations': [],
            'activities': [],
            'dining': [],
            'details': []
        }
        
        for sentence in sentences:
            # Extract location names
            location_matches = re.findall(r'\b([A-Z][a-zA-Z\s-]+(?:Beach|Bay|Island|City|Town|Village|Restaurant|Hotel|Bar|Club|Museum|Park))\b', sentence)
            info['locations'].extend(location_matches)
            
            # Extract activities/actions
            activity_matches = re.findall(r'\b(?:visit|explore|enjoy|experience|try|discover)\s+([^.!?,:;]+)', sentence, re.IGNORECASE)
            info['activities'].extend([match.strip() for match in activity_matches])
            
            # Extract dining information
            if any(word in sentence.lower() for word in ['restaurant', 'bar', 'cafe', 'dining', 'food', 'cuisine']):
                dining_matches = re.findall(r'\b([A-Z][a-zA-Z\s-]+(?:Restaurant|Bar|Cafe|Bistro|Club))\b', sentence)
                info['dining'].extend(dining_matches)
            
            # Extract detailed information
            if any(word in sentence.lower() for word in ['address', 'hours', 'price', 'phone', 'contact']):
                info['details'].append(sentence.strip())
        
        # Remove duplicates and clean up
        info['locations'] = list(dict.fromkeys(info['locations']))  # Remove duplicates while preserving order
        info['activities'] = list(dict.fromkeys(info['activities']))
        info['dining'] = list(dict.fromkeys(info['dining']))
        info['details'] = list(dict.fromkeys(info['details']))
        
        return info
