# src/utils/output/result_builder.py
import json
from datetime import datetime
from typing import List, Dict, Any

from config.constants import MAX_OUTPUT_SECTIONS

class ResultBuilder:
    """Build the final output JSON"""
    
    def build(self, documents: List[str], persona: str, job: str,
              ranked_sections: List[Dict], subsections: List[Dict]) -> Dict:
        """Build the complete result JSON"""
        
        # Prepare metadata
        metadata = {
            "documents": [doc.name for doc in documents],
            "persona": persona,
            "job_to_be_done": job,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "processing_info": {
                "total_sections_analyzed": len(ranked_sections),
                "sections_extracted": min(len(ranked_sections), MAX_OUTPUT_SECTIONS),
                "subsections_extracted": len(subsections)
            }
        }
        
        # Prepare extracted sections
        extracted_sections = []
        for i, section in enumerate(ranked_sections[:MAX_OUTPUT_SECTIONS]):
            extracted_sections.append({
                "document": section['document'],
                "page": section['page'],
                "section_title": section['title'],
                "importance_rank": i + 1,
                "relevance_score": round(section.get('final_score', 0), 3),
                "level": section.get('level', 'H1')
            })
        
        # Prepare subsection analysis
        subsection_analysis = []
        for subsection in subsections:
            subsection_analysis.append({
                "document": subsection['document'],
                "parent_section": subsection['parent_section'],
                "refined_text": self._refine_text(subsection['text']),
                "page": subsection['page'],
                "relevance_score": round(subsection.get('relevance_score', 0), 3),
                "extraction_method": subsection.get('type', 'unknown')
            })
        
        # Build final result
        result = {
            "metadata": metadata,
            "extracted_sections": extracted_sections,
            "subsection_analysis": subsection_analysis
        }
        
        return result
    
    def _refine_text(self, text: str) -> str:
        """Clean and refine text for output"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove incomplete sentences at the end
        if text and not text[-1] in '.!?':
            # Try to find the last complete sentence
            last_period = text.rfind('.')
            if last_period > len(text) * 0.8:  # If near the end
                text = text[:last_period + 1]
        
        # Ensure proper capitalization
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        return text.strip()