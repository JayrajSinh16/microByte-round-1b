#!/usr/bin/env python3
"""Script to extract and save outlines for each PDF"""

import sys
import json
import os
from pathlib import Path
sys.path.append('.')

from src.outline_extraction import OutlineExtractor
from config.settings import INPUT_DIR, OUTPUT_DIR

def extract_and_save_outlines():
    """Extract outlines for each PDF and save them"""
    
    # Create outline output directory
    outline_dir = OUTPUT_DIR / "outlines"
    outline_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize outline extractor
    outline_extractor = OutlineExtractor()
    
    # Find all PDFs
    doc_dir = INPUT_DIR / "documents"
    pdfs = list(doc_dir.glob("*.pdf"))
    
    print(f"Found {len(pdfs)} PDF documents to process")
    
    for pdf_path in pdfs:
        print(f"\nProcessing: {pdf_path.name}")
        
        try:
            # Extract outline
            outline = outline_extractor.extract(pdf_path)
            
            # Create output filename
            output_file = outline_dir / f"{pdf_path.stem}_outline.json"
            
            # Save outline
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(outline, f, indent=2, ensure_ascii=False, default=str)
            
            # Print summary
            outline_sections = outline.get('outline', [])
            print(f"  Extracted {len(outline_sections)} sections")
            for i, section in enumerate(outline_sections[:5]):  # Show first 5
                print(f"    {i+1}. {section.get('text', 'Unknown')} (Level: {section.get('level', 'Unknown')}, Page: {section.get('page', 'Unknown')})")
            if len(outline_sections) > 5:
                print(f"    ... and {len(outline_sections) - 5} more sections")
            
            print(f"  Saved to: {output_file}")
            
        except Exception as e:
            print(f"  Error processing {pdf_path.name}: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    extract_and_save_outlines()
