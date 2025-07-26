# src/subsection_extraction/__init__.py
from typing import Dict, List
from .extractors import ParagraphExtractor, ChunkExtractor, WindowExtractor
from .refiners import TextRefiner, NoiseRemover, FormatCleaner
from .rankers import SubsectionRanker, DiversityScorer

class SubsectionExtractor:
    """Main interface for subsection extraction"""
    
    def __init__(self):
        # Extractors
        self.paragraph_extractor = ParagraphExtractor()
        self.chunk_extractor = ChunkExtractor()
        self.window_extractor = WindowExtractor()
        
        # Refiners
        self.text_refiner = TextRefiner()
        self.noise_remover = NoiseRemover()
        self.format_cleaner = FormatCleaner()
        
        # Rankers
        self.subsection_ranker = SubsectionRanker()
        self.diversity_scorer = DiversityScorer()
    
    def extract(self, ranked_sections: List[Dict], query_profile: Dict) -> List[Dict]:
        """Extract subsections from ranked sections"""
        all_subsections = []
        
        for section in ranked_sections[:20]:  # Process top 20 sections
            # Extract subsections using multiple methods
            subsections = self._extract_from_section(section, query_profile)
            
            # Refine extracted text
            refined = self._refine_subsections(subsections)
            
            # Rank subsections
            ranked = self.subsection_ranker.rank(refined, section, query_profile)
            
            # Add to results
            all_subsections.extend(ranked[:3])  # Top 3 per section
        
        # Ensure diversity
        diverse = self.diversity_scorer.ensure_diversity(all_subsections)
        
        return diverse
    
    def _extract_from_section(self, section: Dict, query_profile: Dict) -> List[Dict]:
        """Extract subsections using appropriate method"""
        content = section.get('content', '')
        
        if not content:
            return []
        
        # Choose extraction method based on content type
        if self._has_clear_paragraphs(content):
            return self.paragraph_extractor.extract(section)
        elif len(content) > 1000:
            return self.chunk_extractor.extract_chunks(section)
        else:
            return self.window_extractor.extract(section, query_profile)
    
    def _has_clear_paragraphs(self, content: str) -> bool:
        """Check if content has clear paragraph structure"""
        paragraphs = content.split('\n\n')
        return len(paragraphs) > 2 and all(len(p) > 50 for p in paragraphs[:3])
    
    def _refine_subsections(self, subsections: List[Dict]) -> List[Dict]:
        """Refine extracted subsections"""
        refined = []
        
        for sub in subsections:
            # Remove noise
            sub['text'] = self.noise_remover.remove_noise(sub['text'])
            
            # Clean formatting
            sub['text'] = self.format_cleaner.clean(sub['text'])
            
            # Final refinement
            sub['refined_text'] = self.text_refiner.refine(sub['text'])
            
            refined.append(sub)
        
        return refined

__all__ = ['SubsectionExtractor']