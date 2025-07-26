# src/content_extraction/__init__.py
from .section_extractor import SectionExtractor
from .text_cleaner import TextCleaner
from .boundary_detector import BoundaryDetector
from .content_mapper import ContentMapper

class ContentExtractor:
    """Main interface for content extraction"""
    
    def __init__(self):
        self.section_extractor = SectionExtractor()
        self.text_cleaner = TextCleaner()
        self.boundary_detector = BoundaryDetector()
        self.content_mapper = ContentMapper()
    
    def extract(self, pdf_path, outline):
        """Extract content for each section in outline"""
        # Extract raw sections
        sections = self.section_extractor.extract(pdf_path, outline)
        
        # Clean text
        for section in sections:
            section['content'] = self.text_cleaner.clean(section['content'])
        
        # Map to document structure
        mapped_sections = self.content_mapper.map_content(sections, outline)
        
        return mapped_sections

__all__ = ['ContentExtractor', 'SectionExtractor', 'TextCleaner', 
           'BoundaryDetector', 'ContentMapper']