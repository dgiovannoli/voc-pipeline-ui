#!/usr/bin/env python3
"""
Fixed LLM Harmonizer - Simplified and Robust
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class FixedLLMHarmonizer:
    """Fixed LLM-based harmonizer with robust JSON handling"""
    
    def __init__(self):
        self.categories = [
            "Product Capabilities",
            "Pricing and Commercial", 
            "Implementation Process",
            "Integration Technical",
            "Support and Service",
            "Competitive Dynamics",
            "Vendor Stability",
            "Sales Experience",
            "User Experience",
            "Security Compliance",
            "Market Discovery"
        ]
        
        logger.info(f"🤖 Fixed LLM Harmonizer loaded with {len(self.categories)} categories")
    
    def harmonize_subject(self, natural_subject: str, verbatim_response: str = "", 
                         interview_context: str = "") -> Dict:
        """Harmonize subject using fixed LLM approach"""
        
        try:
            from langchain_openai import ChatOpenAI
            
            llm = ChatOpenAI(
                model_name="gpt-4o-mini",
                temperature=0.0,
                max_tokens=150
            )
            
            # Simple, clear prompt
            prompt_text = f"""Map this customer subject to ONE category or suggest a new one.

SUBJECT: "{natural_subject}"
CUSTOMER SAID: "{verbatim_response[:200] if verbatim_response else 'No context'}"

CATEGORIES: {', '.join(self.categories)}

 RULES:
 1. If "Pain Points" about pricing/cost → "Pricing and Commercial"
 2. If "Pain Points" about support/service → "Support and Service" 
 3. If "Pain Points" about interface/usability → "User Experience"
 4. If "Industry Events" or "Vendor Discovery" → "Market Discovery"
 5. Otherwise map to best category or null

Respond with only this JSON:
{{"category": "exact category name or null", "confidence": 0.8, "reasoning": "brief explanation", "new_category": "Market Discovery or null"}}"""

            response = llm.invoke(prompt_text)
            result_text = response.content.strip()
            
            # Clean and parse JSON
            result_text = result_text.replace('```json', '').replace('```', '').strip()
            
            # Find JSON in response
            start = result_text.find('{')
            end = result_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_text = result_text[start:end]
                try:
                    llm_result = json.loads(json_text)
                except:
                    # Fallback parsing
                    llm_result = self._parse_fallback(result_text, natural_subject)
            else:
                llm_result = self._parse_fallback(result_text, natural_subject)
            
            # Convert to standard format
            return self._standardize_result(natural_subject, llm_result)
            
        except Exception as e:
            logger.error(f"❌ LLM harmonization failed for '{natural_subject}': {e}")
            # Use smart fallback
            return self._smart_fallback(natural_subject, verbatim_response)
    
    def _parse_fallback(self, text: str, subject: str) -> Dict:
        """Fallback parsing when JSON fails"""
        # Extract category from text
        category = None
        for cat in self.categories:
            if cat.lower() in text.lower():
                category = cat
                break
        
        # Check for new category suggestions
        new_category = None
        if "market discovery" in text.lower():
            new_category = "Market Discovery"
        
        return {
            "category": category,
            "confidence": 0.6,
            "reasoning": f"Fallback parsing from: {text[:50]}...",
            "new_category": new_category
        }
    
    def _smart_fallback(self, subject: str, response: str) -> Dict:
        """Smart rule-based fallback when LLM fails"""
        subject_lower = subject.lower()
        response_lower = response.lower()
        
        # Context-aware rules
        if "pain points" in subject_lower:
            if any(word in response_lower for word in ["pricing", "cost", "expensive", "budget"]):
                category = "Pricing and Commercial"
                confidence = 0.8
            elif any(word in response_lower for word in ["support", "service", "response", "help"]):
                category = "Support and Service" 
                confidence = 0.8
            elif any(word in response_lower for word in ["interface", "usability", "user", "training"]):
                category = "User Experience"
                confidence = 0.8
            else:
                category = "Product Capabilities"
                confidence = 0.5
        elif any(term in subject_lower for term in ["industry events", "vendor discovery"]):
            category = "Market Discovery"
            confidence = 0.85
            return {
                'natural_subject': subject,
                'harmonized_subject': category,
                'confidence': confidence,
                'mapping_method': 'smart_fallback_market_discovery',
                'reasoning': f"Smart fallback mapped '{subject}' to 'Market Discovery' category for vendor awareness patterns",
                'new_category_suggestion': None,
                'context_clues': ['discovery', 'awareness'],
                'mapping_quality': 'high',
                'is_high_confidence': confidence >= 0.7,
                'requires_review': False,
                'mapped_at': datetime.now().isoformat()
            }
        elif "pricing" in subject_lower or "cost" in subject_lower:
            category = "Pricing and Commercial"
            confidence = 0.7
        elif "product" in subject_lower or "features" in subject_lower:
            category = "Product Capabilities"
            confidence = 0.7
        elif "implementation" in subject_lower:
            category = "Implementation Process"
            confidence = 0.7
        else:
            category = "Product Capabilities"  # Default
            confidence = 0.4
        
        return {
            'natural_subject': subject,
            'harmonized_subject': category,
            'confidence': confidence,
            'mapping_method': 'smart_fallback',
            'reasoning': f"Smart fallback mapped '{subject}' to '{category}'",
            'new_category_suggestion': None,
            'context_clues': [],
            'mapping_quality': 'medium',
            'is_high_confidence': confidence >= 0.7,
            'requires_review': confidence < 0.6,
            'mapped_at': datetime.now().isoformat()
        }
    
    def _standardize_result(self, natural_subject: str, llm_result: Dict) -> Dict:
        """Convert LLM result to standard format"""
        category = llm_result.get('category')
        confidence = float(llm_result.get('confidence', 0.6))
        reasoning = llm_result.get('reasoning', 'LLM mapping')
        new_category = llm_result.get('new_category')
        
        # Validate category
        if category and category not in self.categories:
            logger.warning(f"⚠️ Invalid category '{category}' from LLM, setting to null")
            category = None
        
        method = 'llm_high_confidence' if confidence >= 0.7 else 'llm_medium_confidence'
        if new_category:
            method = 'llm_new_category_suggested'
        
        return {
            'natural_subject': natural_subject,
            'harmonized_subject': category,
            'confidence': confidence,
            'mapping_method': method,
            'reasoning': reasoning,
            'new_category_suggestion': new_category,
            'context_clues': [],
            'mapping_quality': 'high' if confidence >= 0.7 else 'medium',
            'is_high_confidence': confidence >= 0.7,
            'requires_review': confidence < 0.5 or category is None,
            'mapped_at': datetime.now().isoformat()
        }

def test_fixed_harmonizer():
    """Test the fixed harmonizer"""
    harmonizer = FixedLLMHarmonizer()
    
    test_cases = [
        ("Pain Points", "The main pain point was slow customer support response times"),
        ("Industry Events", "We learned about them at a conference"),
        ("Pricing and Cost", "The pricing was too expensive for our budget"),
        ("Product Features", "The product has good features"),
        ("Vendor Discovery", "We found them through online research")
    ]
    
    print("🔧 Testing Fixed LLM Harmonizer:")
    print("=" * 60)
    
    for subject, response in test_cases:
        result = harmonizer.harmonize_subject(subject, response)
        
        confidence_icon = "🎯" if result['is_high_confidence'] else "⚠️"
        mapped_to = result['harmonized_subject'] or result.get('new_category_suggestion', 'UNMAPPED')
        
        print(f"{confidence_icon} '{subject}' → '{mapped_to}' (confidence: {result['confidence']:.3f})")
        print(f"   Method: {result['mapping_method']}")
        print(f"   Reasoning: {result['reasoning']}")
        if result.get('new_category_suggestion'):
            print(f"   💡 New category: {result['new_category_suggestion']}")
        print()

if __name__ == "__main__":
    test_fixed_harmonizer() 