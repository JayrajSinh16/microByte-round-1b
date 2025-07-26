# src/utils/io/file_loader.py
from pathlib import Path
from typing import List, Union
import logging

logger = logging.getLogger(__name__)

class FileLoader:
    """Load files from filesystem"""
    
    @staticmethod
    def load_text_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """Load text file content"""
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return content.strip()
            
        except Exception as e:
            logger.error(f"Failed to load text file {file_path}: {str(e)}")
            raise
    
    @staticmethod
    def load_pdf_list(directory: Union[str, Path], 
                     pattern: str = "*.pdf") -> List[Path]:
        """Load list of PDF files from directory"""
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory not found: {directory}")
            
            pdf_files = list(dir_path.glob(pattern))
            pdf_files.sort()  # Ensure consistent ordering
            
            logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
            return pdf_files
            
        except Exception as e:
            logger.error(f"Failed to load PDF list from {directory}: {str(e)}")
            raise
    
    @staticmethod
    def ensure_directory(directory: Union[str, Path]) -> Path:
        """Ensure directory exists"""
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path