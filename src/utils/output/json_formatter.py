# src/utils/output/json_formatter.py
import json
from typing import Any, Dict
from datetime import datetime

class JSONFormatter:
    """Format data for JSON output"""
    
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """Format datetime for JSON"""
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    @staticmethod
    def format_float(value: float, precision: int = 3) -> float:
        """Format float with precision"""
        return round(value, precision)
    
    @staticmethod
    def clean_for_json(data: Any) -> Any:
        """Clean data for JSON serialization"""
        if isinstance(data, dict):
            return {k: JSONFormatter.clean_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [JSONFormatter.clean_for_json(item) for item in data]
        elif isinstance(data, float):
            return JSONFormatter.format_float(data)
        elif isinstance(data, datetime):
            return JSONFormatter.format_datetime(data)
        elif hasattr(data, '__dict__'):
            return JSONFormatter.clean_for_json(data.__dict__)
        else:
            return data
    
    @staticmethod
    def pretty_print(data: Dict) -> str:
        """Pretty print JSON data"""
        cleaned = JSONFormatter.clean_for_json(data)
        return json.dumps(cleaned, indent=2, ensure_ascii=False)