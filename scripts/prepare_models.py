#!/usr/bin/env python3
"""
Model preparation script for Docker container.
Downloads and prepares all required models and data.
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def prepare_sentence_transformer():
    """Download and prepare sentence transformer model"""
    try:
        from sentence_transformers import SentenceTransformer
        from config.settings import SENTENCE_MODEL_NAME
        
        logger.info("📦 Preparing sentence transformer model...")
        
        # Create local model directory
        model_dir = Path("/app/models/sentence_transformer")
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Download and save model locally
        model = SentenceTransformer(SENTENCE_MODEL_NAME)
        model.save(str(model_dir))
        
        logger.info(f"✅ Sentence transformer model saved to {model_dir}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to prepare sentence transformer: {e}")
        return False

def prepare_nltk_data():
    """Ensure NLTK data is properly set up"""
    try:
        import nltk
        
        # Set NLTK data path
        nltk_data_dir = Path("/app/cache/nltk_data")
        nltk_data_dir.mkdir(parents=True, exist_ok=True)
        nltk.data.path.append(str(nltk_data_dir))
        
        logger.info("✅ NLTK data configured")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to configure NLTK: {e}")
        return False

def prepare_spacy_model():
    """Verify spaCy model is available"""
    try:
        import spacy
        
        # Try to load the model
        nlp = spacy.load("en_core_web_sm")
        logger.info("✅ spaCy model loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to load spaCy model: {e}")
        return False

def prepare_directories():
    """Create all necessary directories"""
    directories = [
        "/app/input/documents",
        "/app/output",
        "/app/output/outlines", 
        "/app/cache",
        "/app/cache/embeddings",
        "/app/models"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    logger.info("✅ All directories created")

def main():
    """Main preparation function"""
    logger.info("🚀 Starting model preparation for Docker container...")
    
    success = True
    
    # Prepare directories
    prepare_directories()
    
    # Prepare models
    if not prepare_nltk_data():
        success = False
    
    if not prepare_spacy_model():
        success = False
        
    if not prepare_sentence_transformer():
        success = False
    
    if success:
        logger.info("✅ All models prepared successfully!")
    else:
        logger.error("❌ Some models failed to prepare")
        sys.exit(1)

if __name__ == "__main__":
    main()
