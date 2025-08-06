#!/usr/bin/env python3
"""
Smart Pattern Matching Subject Harmonizer
Maps natural customer language subjects to standardized win-loss analysis categories
for cross-interview aggregation and reporting.
"""

import yaml
import re
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

class SubjectHarmonizer:
    """Smart Pattern Matching system for harmonizing subjects across interviews"""
    
    def __init__(self, config_path: str = "config/subject_harmonization.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Extract configuration sections
        self.patterns = self.config.get('harmonization_patterns', {})
        self.harmonization_config = self.config.get('harmonization_config', {})
        self.quality_control = self.config.get('quality_control', {})
        self.reporting_config = self.config.get('reporting_config', {})
        
        # Initialize tracking
        self.mapping_stats = defaultdict(int)
        self.unmapped_subjects = []
        self.confidence_scores = []
        
        logger.info(f"🎯 Loaded Subject Harmonizer with {len(self.patterns)} win-loss categories")
    
    def _load_config(self) -> Dict:
        """Load harmonization configuration"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.error(f"❌ Config file not found: {self.config_path}")
                return {}
            
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"✅ Loaded harmonization config from {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            return {}
    
    def harmonize_subject(self, natural_subject: str, verbatim_response: str = "") -> Dict:
        """
        Map a natural subject to a harmonized category using pattern matching
        
        Args:
            natural_subject: The original subject from Stage 1
            verbatim_response: The response text for additional context (optional)
            
        Returns:
            Dict with harmonized_subject, confidence, mapping_method, etc.
        """
        if not natural_subject:
            return self._create_result(natural_subject, self.harmonization_config.get('default_category', 'Product Capabilities'), 0.0, 'default')
        
        # Clean the subject for matching
        cleaned_subject = self._clean_subject(natural_subject)
        
        # Calculate matches for each pattern
        pattern_matches = []
        for category, pattern_config in self.patterns.items():
            confidence = self._calculate_pattern_match(cleaned_subject, pattern_config, verbatim_response)
            if confidence > 0:
                pattern_matches.append((category, confidence, 'keyword_overlap'))
        
        # Sort by confidence
        pattern_matches.sort(key=lambda x: x[1], reverse=True)
        
        # Determine best match
        if pattern_matches:
            best_category, best_confidence, method = pattern_matches[0]
            
            # Check if confidence meets threshold
            min_confidence = self.harmonization_config.get('min_confidence_threshold', 0.6)
            if best_confidence >= min_confidence:
                result = self._create_result(natural_subject, best_category, best_confidence, method)
                self._track_mapping(natural_subject, best_category, best_confidence)
                return result
        
        # No good match found - use default
        default_category = self.harmonization_config.get('default_category', 'Product Capabilities')
        result = self._create_result(natural_subject, default_category, 0.3, 'default')
        
        # Track unmapped subject for learning
        self._track_unmapped(natural_subject, verbatim_response)
        
        return result
    
    def _clean_subject(self, subject: str) -> str:
        """Clean subject text for better matching"""
        # Convert to lowercase if not case sensitive
        if not self.harmonization_config.get('case_sensitive', False):
            subject = subject.lower()
        
        # Remove punctuation and extra whitespace
        subject = re.sub(r'[^\w\s]', ' ', subject)
        subject = re.sub(r'\s+', ' ', subject).strip()
        
        return subject
    
    def _calculate_pattern_match(self, cleaned_subject: str, pattern_config: Dict, verbatim_response: str = "") -> float:
        """Calculate match confidence between subject and pattern"""
        keywords = pattern_config.get('keywords', [])
        if not keywords:
            return 0.0
        
        # Split subject into words
        subject_words = set(cleaned_subject.split())
        
        # Count keyword matches
        keyword_matches = 0
        for keyword in keywords:
            # Handle multi-word keywords
            if ' ' in keyword:
                if keyword.lower() in cleaned_subject:
                    keyword_matches += 2  # Multi-word matches get extra weight
            else:
                if keyword.lower() in subject_words:
                    keyword_matches += 1
        
        # Calculate base confidence
        base_confidence = keyword_matches / len(keywords)
        
        # Boost confidence for exact phrase matches
        for keyword in keywords:
            if keyword.lower() == cleaned_subject:
                base_confidence = min(1.0, base_confidence + 0.3)  # Exact match bonus
        
        # Optional: Use verbatim response for additional context
        if verbatim_response and self.harmonization_config.get('use_response_context', False):
            response_boost = self._calculate_response_context_boost(verbatim_response, keywords)
            base_confidence = min(1.0, base_confidence + response_boost * 0.1)
        
        return base_confidence
    
    def _calculate_response_context_boost(self, verbatim_response: str, keywords: List[str]) -> float:
        """Calculate additional confidence from response context"""
        response_lower = verbatim_response.lower()
        context_matches = 0
        
        for keyword in keywords[:5]:  # Limit to top 5 keywords
            if keyword.lower() in response_lower:
                context_matches += 1
        
        return context_matches / min(len(keywords), 5)
    
    def _create_result(self, natural_subject: str, harmonized_subject: str, confidence: float, method: str) -> Dict:
        """Create standardized harmonization result"""
        return {
            'natural_subject': natural_subject,
            'harmonized_subject': harmonized_subject,
            'confidence': round(confidence, 3),
            'mapping_method': method,
            'is_high_confidence': confidence >= self.harmonization_config.get('min_confidence_threshold', 0.6),
            'requires_review': confidence < self.quality_control.get('low_confidence_threshold', 0.5),
            'mapped_at': datetime.now().isoformat()
        }
    
    def _track_mapping(self, natural_subject: str, harmonized_subject: str, confidence: float):
        """Track mapping statistics"""
        if self.quality_control.get('track_mapping_stats', True):
            self.mapping_stats[harmonized_subject] += 1
            self.confidence_scores.append(confidence)
            
            logger.debug(f"🎯 Mapped '{natural_subject}' → '{harmonized_subject}' (confidence: {confidence:.3f})")
    
    def _track_unmapped(self, natural_subject: str, verbatim_response: str = ""):
        """Track unmapped subjects for pattern learning"""
        if self.quality_control.get('log_unmapped_subjects', True):
            self.unmapped_subjects.append({
                'subject': natural_subject,
                'response_sample': verbatim_response[:200] if verbatim_response else "",
                'timestamp': datetime.now().isoformat()
            })
            
            logger.warning(f"⚠️ Unmapped subject: '{natural_subject}' - consider adding to patterns")
    
    def batch_harmonize(self, subjects_data: List[Dict]) -> List[Dict]:
        """
        Harmonize multiple subjects at once
        
        Args:
            subjects_data: List of dicts with 'subject' and optionally 'verbatim_response'
            
        Returns:
            List of harmonization results
        """
        results = []
        
        for item in subjects_data:
            natural_subject = item.get('subject', '')
            verbatim_response = item.get('verbatim_response', '')
            
            result = self.harmonize_subject(natural_subject, verbatim_response)
            
            # Add original data to result
            result.update({
                'response_id': item.get('response_id'),
                'interview_id': item.get('interview_id'),
                'client_id': item.get('client_id')
            })
            
            results.append(result)
        
        logger.info(f"✅ Batch harmonized {len(subjects_data)} subjects")
        return results
    
    def get_harmonization_stats(self) -> Dict:
        """Get mapping statistics and quality metrics"""
        total_mappings = sum(self.mapping_stats.values())
        avg_confidence = sum(self.confidence_scores) / len(self.confidence_scores) if self.confidence_scores else 0
        
        # Calculate distribution
        category_distribution = dict(self.mapping_stats)
        
        # High confidence percentage
        high_confidence_count = sum(1 for conf in self.confidence_scores if conf >= 0.6)
        high_confidence_pct = (high_confidence_count / len(self.confidence_scores) * 100) if self.confidence_scores else 0
        
        return {
            'total_mappings': total_mappings,
            'unique_categories_used': len(self.mapping_stats),
            'category_distribution': category_distribution,
            'average_confidence': round(avg_confidence, 3),
            'high_confidence_percentage': round(high_confidence_pct, 1),
            'unmapped_subjects_count': len(self.unmapped_subjects),
            'unmapped_subjects': self.unmapped_subjects[:10]  # Sample of unmapped
        }
    
    def get_win_loss_categories(self) -> Dict:
        """Get the standard win-loss categories for reporting"""
        return {
            'primary_categories': self.reporting_config.get('primary_categories', []),
            'secondary_categories': self.reporting_config.get('secondary_categories', []),
            'all_categories': list(self.patterns.keys())
        }
    
    def suggest_new_patterns(self) -> List[Dict]:
        """Analyze unmapped subjects and suggest new patterns"""
        suggestions = []
        
        # Group unmapped subjects by common words
        word_frequency = defaultdict(int)
        for item in self.unmapped_subjects:
            words = item['subject'].lower().split()
            for word in words:
                if len(word) > 3:  # Ignore short words
                    word_frequency[word] += 1
        
        # Suggest patterns for frequent words
        for word, count in word_frequency.items():
            if count >= 3:  # Appears in 3+ unmapped subjects
                suggestions.append({
                    'suggested_keyword': word,
                    'frequency': count,
                    'example_subjects': [item['subject'] for item in self.unmapped_subjects 
                                       if word in item['subject'].lower()][:3]
                })
        
        return suggestions[:10]  # Top 10 suggestions

def main():
    """Command line interface for subject harmonization"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Harmonize subjects for cross-interview analysis')
    parser.add_argument('--test', action='store_true', help='Run test with sample subjects')
    parser.add_argument('--stats', action='store_true', help='Show harmonization statistics')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Initialize harmonizer
    harmonizer = SubjectHarmonizer()
    
    if args.test:
        # Test with sample subjects from your data
        test_subjects = [
            "Product Features",
            "Implementation Process", 
            "Pricing and Cost",
            "Integration Issues",
            "Competitive Analysis",
            "Software Evaluation",
            "Cost Considerations",
            "Pain Points",
            "Industry Events",
            "Vendor Discovery"
        ]
        
        print("\n🧪 Testing Subject Harmonization:")
        print("=" * 60)
        
        for subject in test_subjects:
            result = harmonizer.harmonize_subject(subject)
            confidence_icon = "🎯" if result['is_high_confidence'] else "⚠️"
            print(f"{confidence_icon} '{subject}' → '{result['harmonized_subject']}' (confidence: {result['confidence']})")
        
        # Show stats
        stats = harmonizer.get_harmonization_stats()
        print(f"\n📊 Harmonization Statistics:")
        print(f"  Categories used: {stats['unique_categories_used']}")
        print(f"  Average confidence: {stats['average_confidence']}")
        print(f"  High confidence: {stats['high_confidence_percentage']}%")
        
        print(f"\n📈 Category Distribution:")
        for category, count in stats['category_distribution'].items():
            print(f"  {category}: {count}")
    
    elif args.stats:
        # Show current statistics
        stats = harmonizer.get_harmonization_stats()
        categories = harmonizer.get_win_loss_categories()
        
        print("\n📊 Subject Harmonization System Status:")
        print("=" * 60)
        print(f"Available patterns: {len(harmonizer.patterns)}")
        print(f"Primary win-loss categories: {len(categories['primary_categories'])}")
        print(f"Secondary categories: {len(categories['secondary_categories'])}")
        
        print(f"\n🎯 Win-Loss Categories:")
        print("Primary:")
        for cat in categories['primary_categories']:
            print(f"  • {cat}")
        print("Secondary:")
        for cat in categories['secondary_categories']:
            print(f"  • {cat}")
    
    else:
        print("🎯 Subject Harmonization System Ready!")
        print("Use --test to run sample harmonization")
        print("Use --stats to show system status")

if __name__ == "__main__":
    main() 