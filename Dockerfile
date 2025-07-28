FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-jpn \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/input/documents /app/output /app/cache /app/models

# Set environment variables for model caching
ENV PYTHONPATH=/app
ENV TRANSFORMERS_CACHE=/app/cache/transformers
ENV SENTENCE_TRANSFORMERS_HOME=/app/cache/sentence_transformers
ENV HF_HOME=/app/cache/huggingface
ENV TORCH_HOME=/app/cache/torch

# Download and cache required models during build time
RUN python -c "import nltk; nltk.download('punkt', download_dir='/app/cache/nltk_data'); nltk.download('averaged_perceptron_tagger', download_dir='/app/cache/nltk_data'); nltk.download('wordnet', download_dir='/app/cache/nltk_data')"

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Download sentence transformer model to cache
RUN python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder='/app/cache/sentence_transformers'); print('✅ Sentence transformer model cached successfully')"

# Set NLTK data path
ENV NLTK_DATA=/app/cache/nltk_data

# Copy application code
COPY . .

# Create a startup script to prepare models
COPY scripts/prepare_models.py /app/prepare_models.py

# Run model preparation and main application
CMD ["sh", "-c", "python prepare_models.py && python run.py"]