"""Validate output format script."""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

def validate_result_format(result_path: Path) -> bool:
    """Validate the result.json format"""
    try:
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check required top-level fields
        required_fields = ['persona', 'job_to_be_done', 'ranked_sections']
        for field in required_fields:
            if field not in data:
                print(f"ERROR: Missing required field '{field}'")
                return False
        
        # Validate ranked_sections structure
        if not isinstance(data['ranked_sections'], list):
            print("ERROR: 'ranked_sections' must be a list")
            return False
        
        for i, section in enumerate(data['ranked_sections']):
            if not validate_section(section, i):
                return False
        
        print("✅ Output validation passed!")
        return True
        
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON format: {e}")
        return False
    except FileNotFoundError:
        print(f"ERROR: File not found: {result_path}")
        return False
    except Exception as e:
        print(f"ERROR: Validation failed: {e}")
        return False

def validate_section(section: Dict[str, Any], index: int) -> bool:
    """Validate individual section structure"""
    required_section_fields = ['document', 'heading', 'content', 'score', 'subsections']
    
    for field in required_section_fields:
        if field not in section:
            print(f"ERROR: Section {index} missing field '{field}'")
            return False
    
    # Validate subsections
    if not isinstance(section['subsections'], list):
        print(f"ERROR: Section {index} 'subsections' must be a list")
        return False
    
    return True

def main():
    """Main validation function"""
    if len(sys.argv) != 2:
        print("Usage: python validate_output.py <result.json>")
        sys.exit(1)
    
    result_path = Path(sys.argv[1])
    
    if validate_result_format(result_path):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
