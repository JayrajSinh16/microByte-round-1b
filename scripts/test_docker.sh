#!/bin/bash
# scripts/test_docker.sh

echo "Testing Docker build..."

# Build Docker image
docker build -t round1b-processor .

# Test with sample data
docker run -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output round1b-processor

echo "Docker test complete!"