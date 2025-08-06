#!/usr/bin/env python3
"""
Simple LLM Harmonization Demo
Demonstrates the concept with a working implementation that avoids JSON parsing issues
"""

import sys
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from supabase_database import SupabaseDatabase

class SimpleLLMHarmonizer:
    """Simple rule-based harmonizer with LLM-like intelligence for demonstration"""
    
    def __init__(self):
        self.categories = {
            "Product Capabilities": ["product", "features", "functionality", "quality", "performance", "solution", "capabilities"],
            "Pricing and Commercial": ["cost", "price", "pricing", "budget", "expensive", "affordable", "commercial", "roi"],
            "Implementation Process": ["implementation", "setup", "onboarding", "deployment", "installation", "rollout"],
            "Integration Technical": ["integration", "api", "technical", "compatibility", "data", "sync"],
            "Support and Service": ["support", "service", "documentation", "training", "help", "response"],
            "Competitive Dynamics": ["competitor", "competitive", "comparison", "alternative", "market"],
            "Vendor Stability": ["vendor", "company", "reliability", "stability", "trust", "partnership"],
            "Sales Experience": ["sales", "demo", "presentation", "proposal", "buying", "selling"],
            "User Experience": ["user", "interface", "usability", "adoption", "ease", "learning"],
            "Security Compliance": ["security", "compliance", "data protection", "audit", "governance"]
        }
        
        # Smart context-aware mappings
        self.context_mappings = {
            ("pain points", "support"): "Support and Service",
            ("pain points", "pricing"): "Pricing and Commercial", 
            ("pain points", "cost"): "Pricing and Commercial",
            ("pain points", "expensive"): "Pricing and Commercial",
            ("pain points", "slow"): "Support and Service",
            ("pain points", "response"): "Support and Service",
            ("pain points", "documentation"): "Support and Service",
            ("pain points", "interface"): "User Experience",
            ("pain points", "usability"): "User Experience",
            ("pain points", "training"): "User Experience",
            ("industry events", "conference"): "Market Discovery",
            ("industry events", "event"): "Market Discovery",
            ("vendor discovery", "research"): "Market Discovery",
            ("vendor discovery", "referral"): "Market Discovery",
            ("cost considerations", "budget"): "Pricing and Commercial",
            ("cost considerations", "expensive"): "Pricing and Commercial",
            ("software evaluation", "features"): "Product Capabilities",
            ("business strategy", "decision"): "Vendor Stability",
            ("switching considerations", "change"): "Implementation Process"
        }
    
    def harmonize_subject_smart(self, natural_subject: str, verbatim_response: str = "") -> dict:
        """Smart harmonization using context-aware rules"""
        subject_lower = natural_subject.lower()
        response_lower = verbatim_response.lower()
        
        # Context-aware mapping first
        for (subj_key, context_key), mapped_category in self.context_mappings.items():
            if subj_key in subject_lower and context_key in response_lower:
                return {
                    'natural_subject': natural_subject,
                    'harmonized_subject': mapped_category,
                    'confidence': 0.85,
                    'mapping_method': 'smart_context_aware',
                    'reasoning': f"Context-aware mapping: '{natural_subject}' with '{context_key}' context mapped to '{mapped_category}'",
                    'new_category_suggestion': None,
                    'context_clues': [context_key],
                    'mapping_quality': 'high'
                }
        
        # Check for new category suggestions
        if "industry events" in subject_lower or "vendor discovery" in subject_lower:
            return {
                'natural_subject': natural_subject,
                'harmonized_subject': None,
                'confidence': 0.75,
                'mapping_method': 'new_category_suggested',
                'reasoning': f"Subject '{natural_subject}' suggests a new 'Market Discovery' category for awareness/discovery patterns",
                'new_category_suggestion': 'Market Discovery',
                'context_clues': ['discovery', 'awareness'],
                'mapping_quality': 'high'
            }
        
        # Standard keyword matching
        best_match = None
        best_score = 0
        
        for category, keywords in self.categories.items():
            score = sum(1 for keyword in keywords if keyword in subject_lower or keyword in response_lower)
            if score > best_score:
                best_score = score
                best_match = category
        
        if best_match and best_score > 0:
            confidence = min(0.8, 0.4 + (best_score * 0.1))
            return {
                'natural_subject': natural_subject,
                'harmonized_subject': best_match,
                'confidence': confidence,
                'mapping_method': 'keyword_matching',
                'reasoning': f"Keyword matching mapped '{natural_subject}' to '{best_match}' (score: {best_score})",
                'new_category_suggestion': None,
                'context_clues': [],
                'mapping_quality': 'medium'
            }
        
        # No mapping found
        return {
            'natural_subject': natural_subject,
            'harmonized_subject': None,
            'confidence': 0.0,
            'mapping_method': 'no_mapping',
            'reasoning': f"No suitable mapping found for '{natural_subject}'",
            'new_category_suggestion': None,
            'context_clues': [],
            'mapping_quality': 'low'
        }

def demonstrate_harmonization():
    """Demonstrate smart harmonization on real Supio data"""
    
    # Get real data from database
    try:
        db = SupabaseDatabase()
        
        # Get some Supio data
        result = db.supabase.table('stage1_data_responses') \
            .select('response_id, subject, verbatim_response, company') \
            .eq('client_id', 'Supio') \
            .not_.is_('subject', 'null') \
            .limit(10) \
            .execute()
        
        if not result.data:
            print("❌ No Supio data found")
            return
        
        harmonizer = SimpleLLMHarmonizer()
        
        print("🎯 Smart LLM-Style Harmonization Results:")
        print("=" * 80)
        
        successful_mappings = 0
        new_categories = set()
        confidence_scores = []
        
        for row in result.data:
            subject = row.get('subject', '')
            response = row.get('verbatim_response', '')
            company = row.get('company', 'Unknown')
            
            # Harmonize
            harmonization_result = harmonizer.harmonize_subject_smart(subject, response)
            
            # Display result
            confidence_icon = "🎯" if harmonization_result['confidence'] >= 0.7 else "⚠️" if harmonization_result['confidence'] >= 0.4 else "❌"
            mapped_to = harmonization_result['harmonized_subject'] or harmonization_result.get('new_category_suggestion', 'UNMAPPED')
            
            print(f"{confidence_icon} '{subject}' → '{mapped_to}' (confidence: {harmonization_result['confidence']:.3f})")
            print(f"   Method: {harmonization_result['mapping_method']}")
            print(f"   Reasoning: {harmonization_result['reasoning']}")
            
            if harmonization_result.get('new_category_suggestion'):
                print(f"   💡 New category suggested: {harmonization_result['new_category_suggestion']}")
                new_categories.add(harmonization_result['new_category_suggestion'])
            
            print(f"   Context: Company: {company}")
            print()
            
            # Track stats
            if harmonization_result['harmonized_subject']:
                successful_mappings += 1
            confidence_scores.append(harmonization_result['confidence'])
        
        # Summary
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        success_rate = (successful_mappings / len(result.data)) * 100
        
        print(f"📊 Smart Harmonization Summary:")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Average confidence: {avg_confidence:.3f}")
        print(f"  Total processed: {len(result.data)}")
        
        if new_categories:
            print(f"  💡 New categories suggested: {', '.join(new_categories)}")
        
        print(f"\n🎯 Key Advantages of LLM-Style Approach:")
        print(f"  ✅ Context-aware routing (same subject → different categories)")
        print(f"  ✅ Smart pattern recognition for new categories")
        print(f"  ✅ Confidence scoring for quality control")
        print(f"  ✅ Detailed reasoning for transparency")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demonstrate_harmonization() 