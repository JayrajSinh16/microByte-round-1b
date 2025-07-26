# config/patterns.py (continued)
import re

# Heading patterns
HEADING_PATTERNS = {
    'numbered': [
        re.compile(r'^\d+\.?\s+'),              # 1. or 1
        re.compile(r'^\d+\.\d+\.?\s+'),         # 1.1 or 1.1.
        re.compile(r'^\d+\.\d+\.\d+\.?\s+'),    # 1.1.1
    ],
    'lettered': [
        re.compile(r'^[A-Z]\.?\s+'),            # A. or A
        re.compile(r'^$[a-z]$'),              # (a)
        re.compile(r'^[IVX]+\.?\s+'),           # Roman numerals
    ],
    'named': [
        re.compile(r'^(Chapter|Section)\s+\d+', re.I),
        re.compile(r'^(Part|Unit)\s+[IVX]+', re.I),
    ],
    'academic': [
        re.compile(r'^(Abstract|Introduction|Methodology|Methods|Results|Discussion|Conclusion|References)$', re.I),
        re.compile(r'^\d+\s+(Introduction|Background|Related Work)', re.I),
    ],
    'business': [
        re.compile(r'^(Executive Summary|Overview|Financial Results)', re.I),
        re.compile(r'^Q\d\s+\d{4}', re.I),      # Q1 2024
    ]
}

# Title patterns
TITLE_PATTERNS = [
    re.compile(r'^[A-Z][\w\s:,-]+$'),           # Title Case
    re.compile(r'^[A-Z][A-Z\s]+$'),             # ALL CAPS
    re.compile(r'^[\w\s]+(:\s*[\w\s]+)?$'),     # Title: Subtitle
]

# Content patterns to exclude
EXCLUDE_PATTERNS = [
    re.compile(r'^Page\s+\d+'),                 # Page numbers
    re.compile(r'^\d+$'),                       # Just numbers
    re.compile(r'^©'),                          # Copyright
    re.compile(r'^Table\s+\d+'),                # Table captions
    re.compile(r'^Figure\s+\d+'),               # Figure captions
]