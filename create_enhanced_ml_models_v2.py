# create_enhanced_ml_models_v2.py
import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
# TfidfVectorizer removed - using 18-feature format only
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
import pickle
import re
from collections import Counter

class EnhancedMLModelTrainer:
    """Enhanced ML model trainer with better feature engineering and model selection"""
    
    def __init__(self):
        self.models = {
            'random_forest': RandomForestClassifier(random_state=42),
            'gradient_boosting': GradientBoostingClassifier(random_state=42),
            'svm': SVC(probability=True, random_state=42),
            'logistic_regression': LogisticRegression(random_state=42, max_iter=1000)
        }
        
        self.param_grids = {
            'random_forest': {
                'n_estimators': [100, 200, 300],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            },
            'gradient_boosting': {
                'n_estimators': [100, 200],
                'learning_rate': [0.05, 0.1, 0.15],
                'max_depth': [3, 5, 7],
                'subsample': [0.8, 0.9, 1.0]
            },
            'svm': {
                'C': [0.1, 1, 10, 100],
                'gamma': ['scale', 'auto', 0.001, 0.01],
                'kernel': ['rbf', 'linear']
            },
            'logistic_regression': {
                'C': [0.1, 1, 10, 100],
                'penalty': ['l1', 'l2', 'elasticnet'],
                'solver': ['liblinear', 'saga']
            }
        }
        
        self.best_models = {}
        self.scalers = {}
        # No vectorizers needed - using 18-feature format only

    def create_enhanced_training_data(self):
        """Create enhanced training data with better feature engineering"""
        
        # Heading classification data
        heading_data = []
        
        # Generic document structure patterns
        document_types = {
            'technical': {
                'h1': ['Introduction', 'Methodology', 'Results', 'Analysis', 'Conclusion', 'References'],
                'h2': ['System Architecture', 'Implementation Details', 'Performance Metrics', 'Case Studies'],
                'h3': ['Algorithm Description', 'Data Preprocessing', 'Evaluation Criteria']
            },
            'business': {
                'h1': ['Executive Summary', 'Business Overview', 'Market Analysis', 'Financial Projections'],
                'h2': ['Revenue Models', 'Cost Structure', 'Risk Assessment', 'Growth Strategy'],
                'h3': ['Product Features', 'Target Demographics', 'Competitive Landscape']
            },
            'travel': {
                'h1': ['Destinations', 'Activities', 'Accommodation', 'Transportation', 'Tips and Tricks'],
                'h2': ['Major Cities', 'Cultural Experiences', 'Outdoor Adventures', 'Dining Options'],
                'h3': ['Local Attractions', 'Budget Planning', 'Safety Guidelines', 'Best Times to Visit']
            },
            'academic': {
                'h1': ['Literature Review', 'Theoretical Framework', 'Methodology', 'Findings', 'Discussion'],
                'h2': ['Research Questions', 'Data Collection', 'Statistical Analysis', 'Implications'],
                'h3': ['Sample Selection', 'Instrument Validation', 'Ethical Considerations']
            }
        }
        
        # Generate training data for each document type
        for doc_type, headings in document_types.items():
            for level, titles in headings.items():
                for title in titles:
                    features = self._extract_heading_features(title)
                    heading_data.append({
                        'text': title,
                        'level': level,
                        'document_type': doc_type,
                        'features': features
                    })
        
        # Content relevance training data
        content_data = []
        
        # Domain-specific content patterns
        domain_patterns = {
            'travel_planning': {
                'high_relevance': [
                    "Visit the stunning beaches of Nice and enjoy water sports",
                    "Experience local cuisine at recommended restaurants in Marseille",
                    "Top 10 attractions you must see during your visit",
                    "Best time to visit and what to expect weather-wise",
                    "Transportation options and getting around the city"
                ],
                'medium_relevance': [
                    "Historical background of the region",
                    "Cultural traditions and local customs",
                    "General information about the area",
                    "Population demographics and statistics"
                ],
                'low_relevance': [
                    "In conclusion, this guide provides an overview",
                    "Table of contents and chapter organization",
                    "Bibliography and reference materials",
                    "Acknowledgments and author information"
                ]
            },
            'business_analysis': {
                'high_relevance': [
                    "Key performance indicators and metrics analysis",
                    "Market trends and competitive landscape assessment",
                    "Revenue projections and financial modeling",
                    "Strategic recommendations for growth",
                    "Risk assessment and mitigation strategies"
                ],
                'medium_relevance': [
                    "Company background and organizational structure",
                    "Industry overview and market context",
                    "Stakeholder analysis and requirements",
                    "Implementation timeline and milestones"
                ],
                'low_relevance': [
                    "Executive summary of findings",
                    "Methodology and research approach",
                    "Appendices and supporting documents",
                    "Glossary of terms and definitions"
                ]
            }
        }
        
        # Generate content relevance data
        for domain, relevance_levels in domain_patterns.items():
            for relevance, texts in relevance_levels.items():
                for text in texts:
                    features = self._extract_content_features(text)
                    content_data.append({
                        'text': text,
                        'domain': domain,
                        'relevance': relevance,
                        'features': features
                    })
        
        return pd.DataFrame(heading_data), pd.DataFrame(content_data)
    
    def _extract_heading_features(self, text):
        """Extract 18 features matching MLStrategy format"""
        # Create a mock block to match MLStrategy feature extraction
        block = {
            'text': text,
            'font_size': 14,  # Heading font size
            'is_bold': True,  # Headings are typically bold
            'is_italic': False,
            'page': 1,
            'y': 100,
            'x': 0,
            'height': 20
        }
        
        # Text features (7 features)
        features = [
            len(text),                              # Text length
            len(text.split()),                     # Word count
            text.count('\n'),                       # Line count
            int(text[0].isupper()) if text else 0, # Starts with capital
            int(text.isupper()),                    # All caps
            int(text.endswith(':')),                # Ends with colon
            int(not text.endswith('.')),           # Doesn't end with period
        ]
        
        # Font features (4 features)
        avg_font_size = 12
        font_size = block.get('font_size', 14)
        features.extend([
            font_size,
            font_size / avg_font_size,
            int(block.get('is_bold', True)),
            int(block.get('is_italic', False)),
        ])
        
        # Position features (3 features)
        features.extend([
            block.get('page', 1),
            block.get('y', 0) / 1000,
            block.get('x', 0) / 1000,
        ])
        
        # Context features (4 features)
        features.extend([
            1.0,  # Spacing before (large for headings)
            1.0,  # Spacing after (large for headings)
            int(self._is_numbered(text)),
            int(self._has_keywords(text)),
        ])
        
        return features
    
    def _extract_content_features(self, text):
        """Extract 18 features matching MLStrategy format"""
        # Create a mock block to match MLStrategy feature extraction
        block = {
            'text': text,
            'font_size': 12,  # Regular content font size
            'is_bold': False,
            'is_italic': False,
            'page': 1,
            'y': 200,
            'x': 0,
            'height': 100
        }
        
        # Text features (7 features)
        features = [
            len(text),                              # Text length
            len(text.split()),                     # Word count
            text.count('\n'),                       # Line count
            int(text[0].isupper()) if text else 0, # Starts with capital
            int(text.isupper()),                    # All caps
            int(text.endswith(':')),                # Ends with colon
            int(not text.endswith('.')),           # Doesn't end with period
        ]
        
        # Font features (4 features)
        avg_font_size = 12
        font_size = block.get('font_size', 12)
        features.extend([
            font_size,
            font_size / avg_font_size,
            int(block.get('is_bold', False)),
            int(block.get('is_italic', False)),
        ])
        
        # Position features (3 features)
        features.extend([
            block.get('page', 1),
            block.get('y', 0) / 1000,
            block.get('x', 0) / 1000,
        ])
        
        # Context features (4 features)
        features.extend([
            0.3,  # Spacing before (small for content)
            0.3,  # Spacing after (small for content)
            int(self._is_numbered(text)),
            int(self._has_keywords(text)),
        ])
        
        return features
    
    def _is_numbered(self, text):
        """Check if text starts with numbering"""
        import re
        return bool(re.match(r'^\d+\.?\s+', text))
    
    def _has_keywords(self, text):
        """Check if text contains document-specific keywords"""
        keywords = ['introduction', 'methodology', 'results', 'conclusion',
                   'summary', 'overview', 'chapter', 'section', 'part']
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)
    
    def train_models(self):
        """Train multiple models with hyperparameter tuning"""
        print("Creating enhanced training data...")
        heading_df, content_df = self.create_enhanced_training_data()
        
        # Train heading classifier
        print("Training heading classifier...")
        self._train_heading_classifier(heading_df)
        
        # Train content relevance classifier
        print("Training content relevance classifier...")
        self._train_content_classifier(content_df)
        
        # Save models
        self._save_models()
        
    def _train_heading_classifier(self, df):
        """Train heading level classifier with 18 features only"""
        # Prepare features from the features column (18 features only)
        X = np.array(df['features'].tolist())
        y = df['level'].values
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train models with hyperparameter tuning
        best_model = None
        best_score = 0
        
        for model_name, model in self.models.items():
            print(f"  Training {model_name}...")
            
            # Grid search with cross-validation
            grid_search = GridSearchCV(
                model, 
                self.param_grids[model_name], 
                cv=5, 
                scoring='accuracy',
                n_jobs=-1
            )
            
            grid_search.fit(X_train, y_train)
            
            # Evaluate
            score = grid_search.score(X_test, y_test)
            print(f"    {model_name} accuracy: {score:.3f}")
            
            if score > best_score:
                best_score = score
                best_model = grid_search.best_estimator_
                self.best_models['heading_classifier'] = best_model
                self.scalers['heading_classifier'] = scaler
        
        print(f"  Best heading classifier accuracy: {best_score:.3f}")
    
    def _train_content_classifier(self, df):
        """Train content relevance classifier"""
        # Create numerical targets
        relevance_map = {'low_relevance': 0, 'medium_relevance': 1, 'high_relevance': 2}
        df['relevance_numeric'] = df['relevance'].map(relevance_map)
        
        # Prepare features from the features column (18 features only)
        X = np.array(df['features'].tolist())
        y = df['relevance_numeric'].values
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train models
        best_model = None
        best_score = 0
        
        for model_name, model in self.models.items():
            print(f"  Training {model_name}...")
            
            grid_search = GridSearchCV(
                model, 
                self.param_grids[model_name], 
                cv=5, 
                scoring='accuracy',
                n_jobs=-1
            )
            
            grid_search.fit(X_train, y_train)
            score = grid_search.score(X_test, y_test)
            print(f"    {model_name} accuracy: {score:.3f}")
            
            if score > best_score:
                best_score = score
                best_model = grid_search.best_estimator_
                self.best_models['content_classifier'] = best_model
                self.scalers['content_classifier'] = scaler
        
        print(f"  Best content classifier accuracy: {best_score:.3f}")
    
    def _save_models(self):
        """Save trained models and preprocessors"""
        models_dir = 'models'
        os.makedirs(models_dir, exist_ok=True)
        
        # Save models
        for model_name, model in self.best_models.items():
            with open(f'{models_dir}/{model_name}.pkl', 'wb') as f:
                pickle.dump(model, f)
        
        # Save scalers
        for scaler_name, scaler in self.scalers.items():
            with open(f'{models_dir}/{scaler_name}_scaler.pkl', 'wb') as f:
                pickle.dump(scaler, f)
        
        # No vectorizers to save - using 18-feature format only
        
        print(f"Models saved to {models_dir}/")

if __name__ == "__main__":
    trainer = EnhancedMLModelTrainer()
    trainer.train_models()
    print("Enhanced ML model training completed!")
