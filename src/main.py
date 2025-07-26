# src/main.py
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any

from config import settings, constants
from .outline_extraction import OutlineExtractor
from .content_extraction import ContentExtractor
from .persona_analysis import PersonaAnalyzer
from .ranking_engine import RankingEngine
from .subsection_extraction import SubsectionExtractor
from .utils.output import ResultBuilder

logger = logging.getLogger(__name__)

class Round1BProcessor:
    """Main processor for Round 1B challenge"""
    
    def __init__(self):
        self.start_time = time.time()
        self.outline_extractor = OutlineExtractor()
        self.content_extractor = ContentExtractor()
        self.persona_analyzer = PersonaAnalyzer()
        self.ranking_engine = RankingEngine()
        self.subsection_extractor = SubsectionExtractor()
        self.result_builder = ResultBuilder()
        
    def run(self):
        """Execute the complete processing pipeline"""
        try:
            # Stage 1: Load inputs
            logger.info("Loading input files...")
            documents = self._load_documents()
            persona = self._load_persona()
            job = self._load_job()
            
            # Stage 2: Extract document outlines
            logger.info("Extracting document outlines...")
            outlines = self._extract_outlines(documents)
            
            # Stage 3: Extract content for each section
            logger.info("Extracting section content...")
            sections = self._extract_content(documents, outlines)
            
            # Stage 4: Analyze persona and job
            logger.info("Analyzing persona and job requirements...")
            query_profile = self.persona_analyzer.analyze(persona, job)
            
            # Stage 5: Rank sections
            logger.info("Ranking sections based on relevance...")
            ranked_sections = self.ranking_engine.rank(sections, query_profile)
            
            # Stage 6: Extract subsections
            logger.info("Extracting and refining subsections...")
            subsections = self.subsection_extractor.extract(ranked_sections, query_profile)
            
            # Stage 7: Build and save output
            logger.info("Building final output...")
            result = self.result_builder.build(
                documents, persona, job, ranked_sections, subsections
            )
            self._save_output(result)
            
            elapsed = time.time() - self.start_time
            logger.info(f"Processing completed in {elapsed:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            raise
            
    def _load_documents(self) -> List[Path]:
        """Load PDF documents from input directory"""
        doc_dir = settings.INPUT_DIR / "documents"
        pdfs = list(doc_dir.glob("*.pdf"))
        
        if not (settings.MIN_DOCUMENTS <= len(pdfs) <= settings.MAX_DOCUMENTS):
            raise ValueError(
                f"Expected {settings.MIN_DOCUMENTS}-{settings.MAX_DOCUMENTS} documents, "
                f"found {len(pdfs)}"
            )
        
        logger.info(f"Found {len(pdfs)} PDF documents")
        return sorted(pdfs)
    
    def _load_persona(self) -> str:
        """Load persona description"""
        persona_file = settings.INPUT_DIR / "persona.txt"
        if not persona_file.exists():
            raise FileNotFoundError("persona.txt not found")
        
        return persona_file.read_text().strip()
    
    def _load_job(self) -> str:
        """Load job-to-be-done description"""
        job_file = settings.INPUT_DIR / "job.txt"
        if not job_file.exists():
            raise FileNotFoundError("job.txt not found")
        
        return job_file.read_text().strip()
    
    def _extract_outlines(self, documents: List[Path]) -> Dict[str, Any]:
        """Extract outlines from all documents"""
        outlines = {}
        for doc_path in documents:
            outline = self.outline_extractor.extract(doc_path)
            outlines[doc_path.name] = outline
        return outlines
    
    def _extract_content(self, documents: List[Path], outlines: Dict) -> List[Dict]:
        """Extract content for each section in all documents"""
        all_sections = []
        for doc_path in documents:
            try:
                doc_name = doc_path.name
                outline = outlines[doc_name]
                sections = self.content_extractor.extract(doc_path, outline)
                all_sections.extend(sections)
            except Exception as e:
                logger.error(f"Failed to extract content from {doc_path.name}: {str(e)}")
                raise
        return all_sections
    
    def _save_output(self, result: Dict):
        """Save result to output JSON file"""
        output_path = settings.OUTPUT_DIR / "result.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Output saved to {output_path}")