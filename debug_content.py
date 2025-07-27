#!/usr/bin/env python3
"""Debug script to test content extraction step by step"""

import sys
import traceback
sys.path.append('.')

try:
    from src.outline_extraction import OutlineExtractor
    from src.content_extraction import ContentExtractor
    from config.settings import INPUT_DIR
    from pathlib import Path
    
    # Test with one document
    doc_dir = INPUT_DIR / "documents"
    pdfs = list(doc_dir.glob("*.pdf"))
    
    if pdfs:
        print(f"Testing with first PDF: {pdfs[0]}")
        
        # Test outline extraction
        outline_extractor = OutlineExtractor()
        print("Extracting outline...")
        outline = outline_extractor.extract(pdfs[0])
        print(f"Outline extracted: {len(outline.get('outline', []))} entries")
        
        # Test content extraction
        content_extractor = ContentExtractor()
        print("Extracting content...")
        sections = content_extractor.extract(pdfs[0], outline)
        print(f"Content extracted: {len(sections)} sections")
        
    else:
        print("No PDFs found")
        
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
