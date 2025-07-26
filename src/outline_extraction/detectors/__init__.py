# src/outline_extraction/detectors/__init__.py
from .heading_detector import HeadingDetector
from .title_detector import TitleDetector
from .toc_detector import TOCDetector

__all__ = ['HeadingDetector', 'TitleDetector', 'TOCDetector']