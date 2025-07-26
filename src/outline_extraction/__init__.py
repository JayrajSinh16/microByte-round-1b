# src/outline_extraction/__init__.py
from .extractors.hybrid_extractor import HybridExtractor
from .profilers.document_profiler import DocumentProfiler
from .detectors.heading_detector import HeadingDetector
from .classifiers.ensemble_voter import EnsembleVoter
from .builders.outline_builder import OutlineBuilder

class OutlineExtractor:
    """Main interface for outline extraction"""
    
    def __init__(self):
        self.profiler = DocumentProfiler()
        self.extractor = HybridExtractor()
        self.detector = HeadingDetector()
        self.voter = EnsembleVoter()
        self.builder = OutlineBuilder()
    
    def extract(self, pdf_path):
        """Extract outline from PDF"""
        # Profile document
        profile = self.profiler.profile(pdf_path)
        
        # Extract text blocks
        blocks = self.extractor.extract(pdf_path, profile)
        
        # Detect headings
        heading_predictions = self.detector.detect(blocks, profile)
        
        # Vote on final headings
        final_headings = self.voter.vote(heading_predictions)
        
        # Build outline
        outline = self.builder.build(blocks, final_headings)
        
        return outline