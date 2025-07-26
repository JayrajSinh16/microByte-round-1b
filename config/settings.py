"""Global settings for the round1b project."""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
MODELS_DIR = PROJECT_ROOT / "models"
CACHE_DIR = PROJECT_ROOT / "cache"

# Document settings
MAX_DOCUMENTS = 10
MIN_DOCUMENTS = 3

# Processing settings
MAX_WORKERS = 4
CACHE_ENABLED = True
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"

# ML Model settings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.5
CONFIDENCE_THRESHOLD = 0.7

# Output settings
MAX_SECTIONS_PER_DOCUMENT = 50
OUTPUT_FORMAT = "json"
