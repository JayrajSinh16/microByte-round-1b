# src/utils/metrics/time_tracker.py
import time
from typing import Dict, Optional
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class TimeTracker:
    """Track execution time for different operations"""
    
    def __init__(self):
        self.timings = {}
        self.active_timers = {}
    
    def start(self, operation: str):
        """Start timing an operation"""
        self.active_timers[operation] = time.time()
    
    def stop(self, operation: str) -> float:
        """Stop timing an operation and return duration"""
        if operation not in self.active_timers:
            logger.warning(f"No active timer for operation: {operation}")
            return 0.0
        
        duration = time.time() - self.active_timers[operation]
        del self.active_timers[operation]
        
        # Store timing
        if operation not in self.timings:
            self.timings[operation] = []
        self.timings[operation].append(duration)
        
        return duration
    
    @contextmanager
    def time_operation(self, operation: str):
        """Context manager for timing operations"""
        self.start(operation)
        try:
            yield
        finally:
            duration = self.stop(operation)
            logger.debug(f"{operation} took {duration:.3f}s")
    
    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """Get timing summary"""
        summary = {}
        
        for operation, times in self.timings.items():
            if times:
                summary[operation] = {
                    'count': len(times),
                    'total': sum(times),
                    'average': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times)
                }
        
        return summary
    
    def log_summary(self):
        """Log timing summary"""
        summary = self.get_summary()
        
        logger.info("Timing Summary:")
        for operation, stats in summary.items():
            logger.info(f"  {operation}:")
            logger.info(f"    Count: {stats['count']}")
            logger.info(f"    Total: {stats['total']:.3f}s")
            logger.info(f"    Average: {stats['average']:.3f}s")
            logger.info(f"    Min/Max: {stats['min']:.3f}s / {stats['max']:.3f}s")