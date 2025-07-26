#!/bin/bash
# scripts/setup.sh

echo "Setting up Round 1B environment..."

# Install Python dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger'); nltk.download('wordnet')"

# Download spaCy model
python -m spacy download en_core_web_sm

# Create necessary directories
mkdir -p input/documents output models cache

echo "Setup complete!"