#!/bin/bash
# scripts/test_docker.sh

echo "🐳 Testing Adobe Round 1B Docker Setup"
echo "======================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t adobe-round-1b:latest . || {
    echo "❌ Docker build failed"
    exit 1
}

echo "✅ Docker image built successfully"

# Test with sample documents
echo "🧪 Testing with sample documents..."

# Create test input if it doesn't exist
if [ ! -d "./input/documents" ]; then
    echo "📁 Creating test input directory..."
    mkdir -p ./input/documents
fi

# Check if we have documents to test with
doc_count=$(find ./input/documents -name "*.pdf" | wc -l)
if [ $doc_count -eq 0 ]; then
    echo "⚠️  No PDF documents found in ./input/documents"
    echo "   Please add some PDF files to test with"
    echo "   Using existing documents from the project..."
    
    # Copy Adobe PDF documents for testing
    if [ -d "./input" ]; then
        find . -maxdepth 2 -name "*.pdf" -exec cp {} ./input/documents/ \; 2>/dev/null || true
    fi
fi

# Run the container
echo "🚀 Running Docker container..."
docker run --rm \
    -v "$(pwd)/input:/app/input" \
    -v "$(pwd)/output:/app/output" \
    -v "adobe-cache:/app/cache" \
    -v "adobe-models:/app/models" \
    adobe-round-1b:latest || {
    echo "❌ Docker run failed"
    exit 1
}

echo "✅ Docker container completed successfully"

# Check output
if [ -f "./output/result.json" ]; then
    echo "✅ Output file generated: ./output/result.json"
    echo "📊 Result summary:"
    python3 -c "
import json
try:
    with open('./output/result.json', 'r') as f:
        data = json.load(f)
    print(f'  📄 Documents processed: {len(data.get(\"metadata\", {}).get(\"input_documents\", []))}')
    print(f'  📋 Sections extracted: {len(data.get(\"extracted_sections\", []))}')
    print(f'  📝 Subsections analyzed: {len(data.get(\"subsection_analysis\", []))}')
    print(f'  👤 Persona: {data.get(\"metadata\", {}).get(\"persona\", \"N/A\")}')
    print(f'  🎯 Job: {data.get(\"metadata\", {}).get(\"job_to_be_done\", \"N/A\")}')
except Exception as e:
    print(f'  ❌ Error reading result: {e}')
"
else
    echo "❌ No output file generated"
    exit 1
fi

echo ""
echo "🎉 Docker setup test completed successfully!"
echo ""
echo "📝 To use the Docker setup:"
echo "  1. Place PDF documents in ./input/documents/"
echo "  2. Update ./input/persona.txt and ./input/job.txt"
echo "  3. Run: docker-compose up"
echo "  4. Check results in ./output/result.json"