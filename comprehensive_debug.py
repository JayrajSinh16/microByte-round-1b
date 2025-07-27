#!/usr/bin/env python3
"""
Comprehensive debug test for the refactored system
"""

from src.main import Round1BProcessor
from src.persona_analysis import PersonaAnalyzer
from src.ranking_engine import RankingEngine

def debug_pipeline():
    """Debug each step of the pipeline"""
    print("=== COMPREHENSIVE DEBUG TEST ===")
    
    processor = Round1BProcessor()
    
    # Step 1: Load documents
    print("Step 1: Loading documents...")
    documents = processor._load_documents()
    print(f"  ✓ Loaded {len(documents)} documents")
    
    # Step 2: Extract outlines
    print("Step 2: Extracting outlines...")
    outlines = processor._extract_outlines(documents)
    print(f"  ✓ Generated {len(outlines)} outlines")
    
    # Step 3: Extract sections
    print("Step 3: Extracting sections...")
    sections = processor._extract_content(documents, outlines)
    print(f"  ✓ Extracted {len(sections)} sections")
    if sections:
        print(f"  - First section: '{sections[0].get('title', 'N/A')}' ({len(sections[0].get('content', '').split())} words)")
    
    # Step 4: Analyze persona
    print("Step 4: Analyzing persona...")
    persona = processor._load_persona()
    job = processor._load_job()
    persona_analyzer = PersonaAnalyzer()
    query_profile = persona_analyzer.analyze(persona, job)
    domain = query_profile.get('domain_profile', {}).get('domain')
    print(f"  ✓ Persona: '{persona.strip()}' -> Domain: '{domain}'")
    
    # Step 5: Test ranking engine step by step
    print("Step 5: Testing ranking engine...")
    ranking_engine = RankingEngine()
    
    # Test each filter individually
    print("  5a: Testing length filter...")
    from src.ranking_engine.filters import LengthFilter
    length_filter = LengthFilter()
    after_length = length_filter.filter(sections)
    print(f"    - Before: {len(sections)}, After: {len(after_length)}")
    
    print("  5b: Testing keyword filter...")
    from src.ranking_engine.filters import KeywordFilter
    keyword_filter = KeywordFilter()
    after_keyword = keyword_filter.filter(after_length, query_profile)
    print(f"    - Before: {len(after_length)}, After: {len(after_keyword)}")
    
    print("  5c: Testing relevance filter...")
    from src.ranking_engine.filters import RelevanceFilter
    relevance_filter = RelevanceFilter()
    after_relevance = relevance_filter.filter(after_keyword, query_profile)
    print(f"    - Before: {len(after_keyword)}, After: {len(after_relevance)}")
    
    print("  5d: Testing section relevance filter...")
    from src.ranking_engine.filters import SectionRelevanceFilter
    section_filter = SectionRelevanceFilter()
    after_section = section_filter.filter(after_relevance, query_profile)
    print(f"    - Before: {len(after_relevance)}, After: {len(after_section)}")
    
    # Full ranking
    print("  5e: Full ranking...")
    ranked_sections = ranking_engine.rank(sections, query_profile)
    print(f"    - Final ranked: {len(ranked_sections)}")
    
    if ranked_sections:
        print("  Top 3 ranked sections:")
        for i, section in enumerate(ranked_sections[:3]):
            title = section.get('title', 'N/A')
            score = section.get('relevance_score', 0)
            print(f"    {i+1}. {title} (score: {score:.3f})")
    
    # Step 6: Test subsection extraction
    print("Step 6: Testing subsection extraction...")
    subsections = processor.subsection_extractor.extract(ranked_sections, query_profile)
    print(f"  ✓ Generated {len(subsections)} subsections")
    
    return {
        'documents': len(documents),
        'outlines': len(outlines),
        'sections': len(sections),
        'ranked_sections': len(ranked_sections),
        'subsections': len(subsections)
    }

if __name__ == "__main__":
    results = debug_pipeline()
    print("\n=== SUMMARY ===")
    for stage, count in results.items():
        print(f"{stage}: {count}")
