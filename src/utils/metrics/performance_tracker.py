# src/utils/metrics/performance_tracker.py
import time
import psutil
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """Track overall performance metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics = {
            'documents_processed': 0,
            'sections_extracted': 0,
            'sections_ranked': 0,
            'subsections_extracted': 0,
            'errors': 0
        }
    
    def increment(self, metric: str, value: int = 1):
        """Increment a metric"""
        if metric in self.metrics:
            self.metrics[metric] += value
        else:
            self.metrics[metric] = value
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        elapsed_time = time.time() - self.start_time
        
        # Get system metrics
        process = psutil.Process()
        memory_info = process.memory_info()
        
        summary = {
            'elapsed_time': elapsed_time,
            'metrics': self.metrics.copy(),
            'system': {
                'memory_used_mb': memory_info.rss / 1024 / 1024,
                'cpu_percent': process.cpu_percent(interval=0.1),
                'num_threads': process.num_threads()
            }
        }
        
        # Calculate rates
        if elapsed_time > 0:
            summary['rates'] = {
                'docs_per_second': self.metrics['documents_processed'] / elapsed_time,
                'sections_per_second': self.metrics['sections_extracted'] / elapsed_time
            }
        
        return summary
    
    def log_summary(self):
        """Log performance summary"""
        summary = self.get_summary()
        
        logger.info("Performance Summary:")
        logger.info(f"  Elapsed time: {summary['elapsed_time']:.2f}s")
        logger.info(f"  Documents processed: {summary['metrics']['documents_processed']}")
        logger.info(f"  Sections extracted: {summary['metrics']['sections_extracted']}")
        logger.info(f"  Memory used: {summary['system']['memory_used_mb']:.2f} MB")