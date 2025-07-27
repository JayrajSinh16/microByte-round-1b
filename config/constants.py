"""Constants and thresholds for the round1b project."""

# Text processing constants
MIN_TEXT_LENGTH = 10
MAX_TEXT_LENGTH = 10000
MIN_HEADING_LENGTH = 2
MAX_HEADING_LENGTH = 200

# Subsection extraction constants
MIN_SUBSECTION_LENGTH = 100
SUBSECTIONS_PER_SECTION = 3

# Font size thresholds
LARGE_FONT_THRESHOLD = 14
MEDIUM_FONT_THRESHOLD = 12
SMALL_FONT_THRESHOLD = 10

# Font size ratios for heading detection (more permissive for travel guides)
TITLE_SIZE_RATIO = 1.3
H1_SIZE_RATIO = 1.2
H2_SIZE_RATIO = 1.1
H3_SIZE_RATIO = 1.0  # Allow headings with same size as body if other criteria met

# Hierarchy classification thresholds
H1_CONFIDENCE_THRESHOLD = 0.8
H2_CONFIDENCE_THRESHOLD = 0.7
H3_CONFIDENCE_THRESHOLD = 0.6

# Ranking weights
TFIDF_WEIGHT = 0.3
BM25_WEIGHT = 0.3
SEMANTIC_WEIGHT = 0.3
STRUCTURAL_WEIGHT = 0.1

# Performance thresholds
MAX_PROCESSING_TIME = 300  # seconds
MAX_MEMORY_USAGE = 2048  # MB

# Quality thresholds
MIN_SECTION_QUALITY = 0.5
MIN_RELEVANCE_SCORE = 0.4

# Output settings
MAX_OUTPUT_SECTIONS = 5
