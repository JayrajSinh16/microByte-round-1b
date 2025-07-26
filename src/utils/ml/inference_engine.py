# src/utils/ml/inference_engine.py
import torch
import numpy as np
from typing import Any, List, Union, Dict
import logging

logger = logging.getLogger(__name__)

class InferenceEngine:
    """Run model inference with optimizations"""
    
    def __init__(self, batch_size: int = 32):
        self.batch_size = batch_size
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    def run_pytorch_inference(self, model: torch.nn.Module, 
                            inputs: Union[List, np.ndarray, torch.Tensor]) -> Any:
        """Run PyTorch model inference"""
        try:
            model.eval()
            
            # Convert inputs to tensor
            if isinstance(inputs, list):
                inputs = torch.tensor(inputs)
            elif isinstance(inputs, np.ndarray):
                inputs = torch.from_numpy(inputs)
            
            # Move to device
            inputs = inputs.to(self.device)
            model = model.to(self.device)
            
            # Run inference
            with torch.no_grad():
                outputs = model(inputs)
            
            # Convert to numpy
            if isinstance(outputs, torch.Tensor):
                outputs = outputs.cpu().numpy()
            
            return outputs
            
        except Exception as e:
            logger.error(f"PyTorch inference failed: {str(e)}")
            raise
    
    def run_batch_inference(self, model: Any, inputs: List[Any], 
                          inference_fn: callable = None) -> List[Any]:
        """Run inference in batches"""
        results = []
        
        for i in range(0, len(inputs), self.batch_size):
            batch = inputs[i:i + self.batch_size]
            
            if inference_fn:
                batch_results = inference_fn(model, batch)
            else:
                batch_results = model.predict(batch)
            
            results.extend(batch_results)
        
        return results
    
    def optimize_for_cpu(self):
        """Optimize settings for CPU inference"""
        if not torch.cuda.is_available():
            # Set number of threads for CPU
            torch.set_num_threads(4)
            
            # Enable Intel MKL optimizations if available
            try:
                import mkl
                mkl.set_num_threads(4)
            except ImportError:
                pass