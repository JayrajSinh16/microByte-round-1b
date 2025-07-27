#!/usr/bin/env python3
"""Debug script to isolate the list.lower() error"""

import sys
import traceback
sys.path.append('.')

try:
    from src.persona_analysis import PersonaAnalyzer
    
    analyzer = PersonaAnalyzer()
    
    persona_text = "Travel Planner"
    job_text = "Plan a trip of 4 days for a group of 10 college friends."
    
    print("Starting persona analysis...")
    print(f"Persona: {persona_text}")
    print(f"Job: {job_text}")
    
    # Try to analyze
    result = analyzer.analyze(persona_text, job_text)
    print("Analysis successful!")
    print(result)
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
