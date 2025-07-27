#!/usr/bin/env python3
"""Debug script to check query profile structure"""

import sys
import json
sys.path.append('.')

from src.persona_analysis import PersonaAnalyzer

analyzer = PersonaAnalyzer()

persona_text = "Travel Planner"
job_text = "Plan a trip of 4 days for a group of 10 college friends."

print("Testing persona analysis...")
profile = analyzer.analyze(persona_text, job_text)

print("\nQuery Profile Structure:")
print(json.dumps(profile, indent=2, default=str))

# Check specific fields that semantic scorer needs
print("\nChecking specific fields:")
print(f"persona.keywords: {profile.get('persona', {}).get('keywords', 'NOT FOUND')}")
print(f"job.keywords: {profile.get('job', {}).get('keywords', 'NOT FOUND')}")
