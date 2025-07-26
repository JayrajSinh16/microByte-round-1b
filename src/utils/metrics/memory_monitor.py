# src/utils/metrics/memory_monitor.py
import psutil
import gc
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """Monitor memory usage"""
    
    def __init__(self, threshold_mb: float = 1000):
        self.threshold_mb = threshold_mb
        self.measurements = []
        self.process = psutil.Process()
    
    def check_memory(self) -> Dict[str, float]:
        """Check current memory usage"""
        memory_info = self.process.memory_info()
        
        memory_data = {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'available_mb': psutil.virtual_memory().available / 1024 / 1024,
            'percent': self.process.memory_percent()
        }
        
        self.measurements.append(memory_data)
        
        # Check threshold
        if memory_data['rss_mb'] > self.threshold_mb:
            logger.warning(f"Memory usage ({memory_data['rss_mb']:.2f} MB) exceeds threshold ({self.threshold_mb} MB)")
            self.trigger_cleanup()
        
        return memory_data
    
    def trigger_cleanup(self):
        """Trigger memory cleanup"""
        logger.info("Triggering garbage collection...")
        gc.collect()
        
        # Check memory after cleanup
        after = self.check_memory()
        logger.info(f"Memory after cleanup: {after['rss_mb']:.2f} MB")
    
    def get_peak_memory(self) -> float:
        """Get peak memory usage"""
        if not self.measurements:
            return 0.0
        
        return max(m['rss_mb'] for m in self.measurements)
    
    def get_average_memory(self) -> float:
        """Get average memory usage"""
        if not self.measurements:
            return 0.0
        
        return sum(m['rss_mb'] for m in self.measurements) / len(self.measurements)