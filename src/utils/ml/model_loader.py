# src/utils/ml/model_loader.py
from pathlib import Path
import torch
import pickle
import logging
from typing import Any, Union, Optional

logger = logging.getLogger(__name__)

class ModelLoader:
    """Load and manage ML models"""
    
    def __init__(self):
        self.loaded_models = {}
    
    def load_pytorch_model(self, model_path: Union[str, Path], 
                          device: str = None) -> torch.nn.Module:
        """Load PyTorch model"""
        try:
            path = Path(model_path)
            
            if device is None:
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
            
            # Check cache
            cache_key = f"{path}_{device}"
            if cache_key in self.loaded_models:
                return self.loaded_models[cache_key]
            
            # Load model
            model = torch.load(path, map_location=device)
            model.eval()
            
            # Cache
            self.loaded_models[cache_key] = model
            
            logger.info(f"Loaded PyTorch model from {path} to {device}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load PyTorch model from {model_path}: {str(e)}")
            raise
    
    def load_sklearn_model(self, model_path: Union[str, Path]) -> Any:
        """Load scikit-learn model"""
        try:
            path = Path(model_path)
            
            # Check cache
            cache_key = str(path)
            if cache_key in self.loaded_models:
                return self.loaded_models[cache_key]
            
            # Load model
            with open(path, 'rb') as f:
                model = pickle.load(f)
            
            # Cache
            self.loaded_models[cache_key] = model
            
            logger.info(f"Loaded sklearn model from {path}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load sklearn model from {model_path}: {str(e)}")
            raise
    
    def unload_model(self, model_path: Union[str, Path]):
        """Unload model from cache"""
        path = Path(model_path)
        
        # Remove all cached versions
        keys_to_remove = [k for k in self.loaded_models.keys() if str(path) in k]
        for key in keys_to_remove:
            del self.loaded_models[key]
    
    def get_model_size(self, model_path: Union[str, Path]) -> int:
        """Get model file size in bytes"""
        path = Path(model_path)
        return path.stat().st_size if path.exists() else 0