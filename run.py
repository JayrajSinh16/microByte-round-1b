#!/usr/bin/env python3
# run.py
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.main import Round1BProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main entry point for Round 1B processing"""
    try:
        processor = Round1BProcessor()
        processor.run()
        logging.info("Processing completed successfully")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Processing failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()