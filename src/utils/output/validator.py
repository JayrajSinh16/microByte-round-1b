# src/utils/output/validator.py
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Validator:
    """Validate output format and content"""
    
    def __init__(self):
        self.required_metadata_fields = [
            'documents', 'persona', 'job_to_be_done', 'timestamp'
        ]
        
        self.required_section_fields = [
            'document', 'page', 'section_title', 'importance_rank'
        ]
        
        self.required_subsection_fields = [
            'document', 'refined_text', 'page'
        ]
    
    def validate_output(self, output: Dict) -> tuple[bool, List[str]]:
        """Validate complete output structure"""
        errors = []
        
        # Check top-level structure
        required_keys = ['metadata', 'extracted_sections', 'subsection_analysis']
        for key in required_keys:
            if key not in output:
                errors.append(f"Missing required top-level key: {key}")
        
        if errors:
            return False, errors
        
        # Validate metadata
        metadata_errors = self._validate_metadata(output.get('metadata', {}))
        errors.extend(metadata_errors)
        
        # Validate sections
        sections_errors = self._validate_sections(output.get('extracted_sections', []))
        errors.extend(sections_errors)
        
        # Validate subsections
        subsections_errors = self._validate_subsections(output.get('subsection_analysis', []))
        errors.extend(subsections_errors)
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _validate_metadata(self, metadata: Dict) -> List[str]:
        """Validate metadata structure"""
        errors = []
        
        for field in self.required_metadata_fields:
            if field not in metadata:
                errors.append(f"Missing metadata field: {field}")
        
        # Validate documents list
        if 'documents' in metadata:
            if not isinstance(metadata['documents'], list):
                errors.append("Metadata 'documents' must be a list")
            elif len(metadata['documents']) == 0:
                errors.append("Metadata 'documents' cannot be empty")
        
        return errors
    
    def _validate_sections(self, sections: List[Dict]) -> List[str]:
        """Validate sections structure"""
        errors = []
        
        if not isinstance(sections, list):
            errors.append("'extracted_sections' must be a list")
            return errors
        
        for i, section in enumerate(sections):
            for field in self.required_section_fields:
                if field not in section:
                    errors.append(f"Section {i} missing required field: {field}")
            
            # Validate importance_rank
            if 'importance_rank' in section:
                if not isinstance(section['importance_rank'], int):
                    errors.append(f"Section {i} importance_rank must be an integer")
                elif section['importance_rank'] <= 0:
                    errors.append(f"Section {i} importance_rank must be positive")
        
        return errors
    
    def _validate_subsections(self, subsections: List[Dict]) -> List[str]:
        """Validate subsections structure"""
        errors = []
        
        if not isinstance(subsections, list):
            errors.append("'subsection_analysis' must be a list")
            return errors
        
        for i, subsection in enumerate(subsections):
            for field in self.required_subsection_fields:
                if field not in subsection:
                    errors.append(f"Subsection {i} missing required field: {field}")
            
            # Validate refined_text
            if 'refined_text' in subsection:
                if not isinstance(subsection['refined_text'], str):
                    errors.append(f"Subsection {i} refined_text must be a string")
                elif len(subsection['refined_text']) == 0:
                    errors.append(f"Subsection {i} refined_text cannot be empty")
        
        return errors