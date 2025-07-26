# src/utils/io/json_handler.py
import json
from pathlib import Path
from typing import Dict, Any, List, Union
import logging

logger = logging.getLogger(__name__)

class JSONHandler:
    """Handle JSON file operations"""
    
    @staticmethod
    def load(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load JSON file"""
        try:
            path = Path(file_path)
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to load JSON from {file_path}: {str(e)}")
            raise
    
    @staticmethod
    def save(data: Dict[str, Any], file_path: Union[str, Path], 
            indent: int = 2, ensure_ascii: bool = False):
        """Save data to JSON file"""
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
            
            logger.info(f"Saved JSON to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save JSON to {file_path}: {str(e)}")
            raise
    
    @staticmethod
    def validate_schema(data: Dict[str, Any], required_keys: List[str]) -> bool:
        """Validate JSON has required keys"""
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            logger.error(f"Missing required keys: {missing_keys}")
            return False
        
        return True