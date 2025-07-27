#!/usr/bin/env python3
"""Debug script to analyze PDF content and see what headings should be detected"""

import sys
import fitz
from pathlib import Path
sys.path.append('.')

from config.settings import INPUT_DIR

def analyze_pdf_content():
    """Analyze the actual content of PDFs to understand structure"""
    
    doc_dir = INPUT_DIR / "documents"
    pdfs = list(doc_dir.glob("*.pdf"))
    
    # Focus on the "Things to Do" document
    things_to_do_pdf = None
    for pdf in pdfs:
        if "Things to Do" in pdf.name:
            things_to_do_pdf = pdf
            break
    
    if not things_to_do_pdf:
        print("Could not find 'Things to Do' PDF")
        return
    
    print(f"Analyzing: {things_to_do_pdf.name}")
    
    doc = fitz.open(things_to_do_pdf)
    
    for page_num in range(min(5, len(doc))):  # Check first 5 pages
        page = doc[page_num]
        
        print(f"\n=== PAGE {page_num + 1} ===")
        
        # Get text blocks with formatting info
        blocks = page.get_text("dict")
        
        for block in blocks["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text and len(text) > 3:
                            font_size = span["size"]
                            font_flags = span["flags"]
                            
                            # Check if this could be a heading
                            is_large = font_size > 12
                            is_bold = font_flags & 2**4  # Bold flag
                            is_potential_heading = (is_large or is_bold) and len(text) < 100
                            
                            if is_potential_heading:
                                print(f"POTENTIAL HEADING: '{text}' (size: {font_size:.1f}, bold: {is_bold})")
                            elif len(text) > 50:  # Show some regular content
                                print(f"Content sample: '{text[:60]}...'")
    
    doc.close()

if __name__ == "__main__":
    analyze_pdf_content()
