# Docker Setup Guide for Adobe Round 1B

This Docker setup provides a complete, self-contained environment for the Adobe Round 1B document processing system with all dependencies and models pre-downloaded.

## 🚀 Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# 1. Clone and navigate to the project
cd adobe-round-1b

# 2. Place your PDF documents in ./input/documents/
mkdir -p input/documents
cp your-documents.pdf input/documents/

# 3. Configure persona and job (optional - defaults provided)
echo "Data Scientist" > input/persona.txt
echo "Extract insights from research papers" > input/job.txt

# 4. Run with Docker Compose
docker-compose up

# 5. Check results
cat output/result.json
```

### Option 2: Using Docker directly

```bash
# Build the image
docker build -t adobe-round-1b:latest .

# Run the container
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  -v adobe-cache:/app/cache \
  -v adobe-models:/app/models \
  adobe-round-1b:latest
```

## 📦 What's Included

The Docker image includes:

- **Python 3.9** with all required packages
- **Tesseract OCR** with English and Japanese language support
- **OpenCV** for image processing
- **Sentence Transformers** (`all-MiniLM-L6-v2`) pre-downloaded
- **spaCy** model (`en_core_web_sm`) pre-installed
- **NLTK** data (punkt, POS tagger, wordnet) pre-downloaded
- **Enhanced Font Strategy** for universal PDF outline extraction

## 🗂️ Directory Structure

```
adobe-round-1b/
├── input/
│   ├── documents/          # Place your PDF files here
│   ├── persona.txt         # User persona (e.g., "HR Professional")
│   └── job.txt            # Job to be done description
├── output/
│   ├── result.json        # Main output file
│   └── outlines/          # Individual PDF outlines
├── cache/                 # Model cache (persistent volume)
└── models/               # Local model storage
```

## ⚙️ Configuration

### Environment Variables

The Docker setup uses these environment variables:

```bash
PYTHONPATH=/app
TRANSFORMERS_CACHE=/app/cache/transformers
SENTENCE_TRANSFORMERS_HOME=/app/cache/sentence_transformers
HF_HOME=/app/cache/huggingface
TORCH_HOME=/app/cache/torch
NLTK_DATA=/app/cache/nltk_data
DEBUG=false
```

### Volume Mounts

- `./input:/app/input` - Input documents and configuration
- `./output:/app/output` - Generated results
- `adobe-cache:/app/cache` - Model cache (persistent)
- `adobe-models:/app/models` - Local model storage (persistent)

## 🧪 Testing the Setup

Run the test script to verify everything works:

```bash
chmod +x scripts/test_docker.sh
./scripts/test_docker.sh
```

## 🔧 Model Management

### Pre-downloaded Models

The following models are downloaded during the Docker build:

1. **Sentence Transformer**: `sentence-transformers/all-MiniLM-L6-v2`
   - Used for semantic similarity and content analysis
   - Cached in `/app/cache/sentence_transformers`

2. **spaCy Model**: `en_core_web_sm`
   - Used for NLP tasks and text processing
   - Installed system-wide

3. **NLTK Data**: punkt, averaged_perceptron_tagger, wordnet
   - Used for tokenization and POS tagging
   - Cached in `/app/cache/nltk_data`

### Model Preparation

The container runs `prepare_models.py` on startup to:
- Verify all models are accessible
- Set up local model directories
- Prepare the sentence transformer for local use
- Configure NLTK data paths

## 📊 Resource Requirements

### Minimum Requirements
- **Memory**: 2GB RAM
- **Storage**: 4GB for image + models
- **CPU**: 1 core

### Recommended Requirements
- **Memory**: 4GB RAM
- **Storage**: 8GB available space
- **CPU**: 2+ cores

## 🐛 Troubleshooting

### Common Issues

1. **Out of Memory**
   ```bash
   # Increase Docker memory limit to 4GB
   # In Docker Desktop: Settings > Resources > Memory
   ```

2. **Model Download Fails**
   ```bash
   # Check internet connection during build
   # Rebuild without cache: docker build --no-cache -t adobe-round-1b .
   ```

3. **Permission Issues**
   ```bash
   # Fix file permissions
   chmod -R 755 input output
   ```

4. **PDF Processing Errors**
   ```bash
   # Check PDF file integrity
   # Ensure PDFs are not password protected
   ```

### Debugging

Enable debug mode:
```bash
# In docker-compose.yml
environment:
  - DEBUG=true

# Or with direct Docker run
docker run -e DEBUG=true ...
```

## 🔄 Updates and Maintenance

### Updating Models

To update the sentence transformer model:

1. Modify `config/settings.py`:
   ```python
   EMBEDDING_MODEL = "sentence-transformers/new-model-name"
   ```

2. Rebuild the Docker image:
   ```bash
   docker build --no-cache -t adobe-round-1b:latest .
   ```

### Clearing Cache

To clear model cache and start fresh:
```bash
docker volume rm adobe-cache adobe-models
docker-compose up --build
```

## 📈 Performance Optimization

### CPU Optimization
```bash
# Use all available cores
docker run --cpus="$(nproc)" ...
```

### Memory Optimization
```bash
# Set memory limit
docker run --memory="4g" ...
```

### Storage Optimization
```bash
# Use bind mounts for large datasets
-v /host/large-docs:/app/input/documents:ro
```

## 🌐 Production Deployment

For production use:

1. **Use multi-stage builds** to reduce image size
2. **Set up health checks** in docker-compose.yml
3. **Configure logging** for monitoring
4. **Use secrets management** for any API keys
5. **Set up backup** for persistent volumes

```yaml
# Example production docker-compose.yml additions
services:
  adobe-round-1b:
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8080/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 📝 Notes

- Models are downloaded once during build and cached for subsequent runs
- The enhanced font strategy provides universal PDF processing without domain-specific hardcoding
- All processing is done locally - no external API calls required
- Results are deterministic and reproducible across different environments
