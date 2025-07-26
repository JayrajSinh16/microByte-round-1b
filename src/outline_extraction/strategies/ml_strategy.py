# src/outline_extraction/strategies/ml_strategy.py
import pickle
import numpy as np
from typing import List, Dict, Optional
import logging
from pathlib import Path

from .base_strategy import BaseStrategy
from config.settings import MODELS_DIR

logger = logging.getLogger(__name__)

class MLStrategy(BaseStrategy):
    """Machine learning based heading detection"""
    
    def __init__(self):
        self.model = None
        self.feature_extractor = None
        self.load_models()
    
    def load_models(self):
        """Load pre-trained models if available"""
        try:
            model_path = MODELS_DIR / 'heading_classifier.pkl'
            feature_path = MODELS_DIR / 'feature_extractor.pkl'
            
            if model_path.exists() and feature_path.exists():
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(feature_path, 'rb') as f:
                    self.feature_extractor = pickle.load(f)
                logger.info("ML models loaded successfully")
            else:
                logger.warning("ML models not found, using rule-based fallback")
        except Exception as e:
            logger.error(f"Failed to load ML models: {str(e)}")
    
    def detect(self, blocks: List[Dict], profile: Dict) -> List[Dict]:
        """Detect headings using ML model"""
        predictions = []
        
        if self.model is None:
            # Fallback to rule-based approach
            return self._rule_based_fallback(blocks, profile)
        
        # Extract features for all blocks
        features = self._extract_features(blocks, profile)
        
        # Make predictions
        try:
            # Predict heading probability
            probabilities = self.model.predict_proba(features)
            
            for i, block in enumerate(blocks):
                # Get probability of being a heading
                heading_prob = probabilities[i][1]  # Assuming binary classification
                
                prediction = {
                    'block_id': block['id'],
                    'is_heading': heading_prob > 0.5,
                    'level': None,
                    'confidence': heading_prob
                }
                
                # Determine level if it's a heading
                if prediction['is_heading']:
                    prediction['level'] = self._predict_level(block, features[i])
                
                predictions.append(prediction)
                
        except Exception as e:
            logger.error(f"ML prediction failed: {str(e)}")
            return self._rule_based_fallback(blocks, profile)
        
        return predictions
    
    def _extract_features(self, blocks: List[Dict], profile: Dict) -> np.ndarray:
        """Extract features for ML model"""
        features = []
        
        # Calculate document statistics
        font_sizes = [b.get('font_size', 0) for b in blocks if b.get('font_size', 0) > 0]
        avg_font_size = np.mean(font_sizes) if font_sizes else 12
        
        for i, block in enumerate(blocks):
            block_features = []
            
            # Text features
            text = block.get('text', '').strip()
            block_features.extend([
                len(text),                              # Text length
                len(text.split()),                     # Word count
                text.count('\n'),                       # Line count
                int(text[0].isupper()) if text else 0, # Starts with capital
                int(text.isupper()),                    # All caps
                int(text.endswith(':')),                # Ends with colon
                int(not text.endswith('.')),           # Doesn't end with period
            ])
            
            # Font features
            font_size = block.get('font_size', 0)
            block_features.extend([
                font_size,
                font_size / avg_font_size if avg_font_size > 0 else 1,
                int(block.get('is_bold', False)),
                int(block.get('is_italic', False)),
            ])
            
            # Position features
            block_features.extend([
                block.get('page', 1),
                block.get('y', 0) / 1000,  # Normalize y position
                block.get('x', 0) / 1000,  # Normalize x position
            ])
            
            # Context features
            prev_block = blocks[i-1] if i > 0 else None
            next_block = blocks[i+1] if i < len(blocks)-1 else None
            
            block_features.extend([
                self._get_spacing_before(block, prev_block),
                self._get_spacing_after(block, next_block),
                int(self._is_numbered(text)),
                int(self._has_keywords(text, profile)),
            ])
            
            features.append(block_features)
        
        return np.array(features)
    
    def _get_spacing_before(self, block: Dict, prev_block: Optional[Dict]) -> float:
        """Calculate spacing before block"""
        if not prev_block or prev_block.get('page') != block.get('page'):
            return 1.0  # Large spacing
        
        spacing = block.get('y', 0) - (prev_block.get('y', 0) + prev_block.get('height', 0))
        return min(spacing / 100, 1.0)  # Normalize
    
    def _get_spacing_after(self, block: Dict, next_block: Optional[Dict]) -> float:
        """Calculate spacing after block"""
        if not next_block or next_block.get('page') != block.get('page'):
            return 1.0
        
        spacing = next_block.get('y', 0) - (block.get('y', 0) + block.get('height', 0))
        return min(spacing / 100, 1.0)
    
    def _is_numbered(self, text: str) -> bool:
        """Check if text starts with numbering"""
        import re
        return bool(re.match(r'^\d+\.?\s+', text))
    
    def _has_keywords(self, text: str, profile: Dict) -> bool:
        """Check if text contains document-specific keywords"""
        doc_type = profile.get('type', 'general')
        
        keywords = {
            'academic': ['introduction', 'methodology', 'results', 'conclusion'],
            'business': ['summary', 'overview', 'financial', 'strategy'],
            'technical': ['specification', 'implementation', 'architecture', 'design'],
            'book': ['chapter', 'section', 'part', 'appendix']
        }
        
        text_lower = text.lower()
        type_keywords = keywords.get(doc_type, [])
        
        return any(keyword in text_lower for keyword in type_keywords)
    
    def _predict_level(self, block: Dict, features: np.ndarray) -> str:
        """Predict heading level based on features"""
        # Simple heuristic for level prediction
        # In a real implementation, this could be another ML model
        
        text = block.get('text', '').strip()
        font_size = block.get('font_size', 0)
        
        # Check numbering depth
        import re
        match = re.match(r'^(\d+(?:\.\d+)*)', text)
        if match:
            number = match.group(1)
            depth = number.count('.') + 1
            
            if depth == 1:
                return 'H1'
            elif depth == 2:
                return 'H2'
            else:
                return 'H3'
        
        # Use font size relative to document
        font_ratio = features[8]  # Font size ratio feature
        
        if font_ratio > 1.3:
            return 'H1'
        elif font_ratio > 1.15:
            return 'H2'
        else:
            return 'H3'
    
    def _rule_based_fallback(self, blocks: List[Dict], profile: Dict) -> List[Dict]:
        """Fallback to simple rule-based detection"""
        predictions = []
        
        for block in blocks:
            text = block.get('text', '').strip()
            
            # Simple rules
            is_heading = False
            confidence = 0.0
            
            # Check font size
            if block.get('font_size', 0) > 14:
                is_heading = True
                confidence = 0.6
            
            # Check if bold
            if block.get('is_bold', False):
                is_heading = True
                confidence = max(confidence, 0.5)
            
            # Check patterns
            import re
            if re.match(r'^\d+\.?\s+', text) or re.match(r'^Chapter\s+\d+', text, re.I):
                is_heading = True
                confidence = max(confidence, 0.7)
            
            # Check length
            if len(text.split()) <= 10 and is_heading:
                confidence += 0.1
            
            prediction = {
                'block_id': block['id'],
                'is_heading': is_heading,
                'level': 'H2' if is_heading else None,
                'confidence': min(confidence, 1.0)
            }
            
            predictions.append(prediction)
        
        return predictions