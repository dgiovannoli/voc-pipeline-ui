#!/usr/bin/env python3
"""
LLM-Based Semantic Subject Harmonizer
Uses GPT to intelligently map natural customer language subjects to standardized 
win-loss analysis categories with context understanding and semantic intelligence.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class LLMSemanticHarmonizer:
    """LLM-based semantic harmonizer for intelligent subject mapping"""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        
        # Win-loss categories with detailed descriptions for LLM
        self.categories = {
            "Product Capabilities": {
                "description": "Core product features, functionality, performance, and solution fit",
                "examples": ["product quality", "feature gaps", "functionality issues", "performance problems"],
                "win_loss_impact": "Primary differentiator in competitive evaluations"
            },
            "Pricing and Commercial": {
                "description": "Pricing, costs, budget considerations, ROI, and commercial terms", 
                "examples": ["pricing concerns", "budget constraints", "cost analysis", "ROI evaluation"],
                "win_loss_impact": "Critical factor in purchase decisions and deal closure"
            },
            "Implementation Process": {
                "description": "Implementation timeline, setup complexity, onboarding, and deployment",
                "examples": ["setup difficulties", "onboarding experience", "deployment challenges", "time to value"],
                "win_loss_impact": "Implementation risk and time-to-value assessment"
            },
            "Integration Technical": {
                "description": "Technical integration, APIs, system compatibility, and data workflows",
                "examples": ["API limitations", "integration challenges", "data sync issues", "technical compatibility"],
                "win_loss_impact": "Technical feasibility and existing system compatibility"
            },
            "Support and Service": {
                "description": "Customer support quality, responsiveness, training, and service experience",
                "examples": ["support responsiveness", "service quality", "training adequacy", "documentation"],
                "win_loss_impact": "Post-purchase experience and relationship quality"
            },
            "Competitive Dynamics": {
                "description": "Competitive comparisons, market positioning, and alternative solutions",
                "examples": ["competitor comparison", "market alternatives", "competitive advantages", "positioning"],
                "win_loss_impact": "Competitive differentiation and market positioning"
            },
            "Vendor Stability": {
                "description": "Vendor reliability, company stability, trustworthiness, and long-term viability",
                "examples": ["company reputation", "vendor reliability", "long-term viability", "partnership trust"],
                "win_loss_impact": "Long-term partnership viability and vendor risk"
            },
            "Sales Experience": {
                "description": "Sales process quality, demo effectiveness, and buying experience",
                "examples": ["sales process", "demo quality", "proposal effectiveness", "sales team interaction"],
                "win_loss_impact": "Sales effectiveness and customer experience during evaluation"
            },
            "User Experience": {
                "description": "User interface, usability, user adoption, and ease of use",
                "examples": ["interface design", "usability issues", "user adoption challenges", "learning curve"],
                "win_loss_impact": "End-user acceptance and adoption risk"
            },
            "Security Compliance": {
                "description": "Security features, compliance requirements, data protection, and governance",
                "examples": ["security concerns", "compliance requirements", "data protection", "audit capabilities"],
                "win_loss_impact": "Regulatory compliance and security risk management"
            },
            "Market Discovery": {
                "description": "How customers discover vendors, awareness channels, and market research activities",
                "examples": ["industry events", "conferences", "vendor discovery", "online research", "referrals"],
                "win_loss_impact": "Market visibility and vendor awareness strategies"
            }
        }
        
        # Initialize tracking
        self.mapping_stats = defaultdict(int)
        self.confidence_scores = []
        self.suggested_categories = set()
        
        logger.info(f"🤖 Loaded LLM Semantic Harmonizer with {len(self.categories)} categories")
    
    def harmonize_subject(self, natural_subject: str, verbatim_response: str = "", 
                         interview_context: str = "") -> Dict:
        """
        Semantically map a natural subject using LLM intelligence
        
        Args:
            natural_subject: The original subject from Stage 1
            verbatim_response: The actual customer response for context
            interview_context: Additional context (company, deal status, etc.)
            
        Returns:
            Dict with harmonized mapping, confidence, reasoning, etc.
        """
        if not natural_subject:
            return self._create_result(natural_subject, None, 0.0, "empty_subject", "No subject provided")
        
        try:
            # Get LLM analysis
            llm_result = self._call_llm_for_mapping(natural_subject, verbatim_response, interview_context)
            
            # Process LLM response
            mapping_result = self._process_llm_response(natural_subject, llm_result)
            
            # Track results
            self._track_mapping(mapping_result)
            
            return mapping_result
            
        except Exception as e:
            logger.error(f"❌ LLM harmonization failed for '{natural_subject}': {e}")
            return self._create_result(natural_subject, None, 0.0, "error", f"Analysis failed: {str(e)}")
    
    def _call_llm_for_mapping(self, natural_subject: str, verbatim_response: str, 
                             interview_context: str) -> Dict:
        """Call LLM to analyze and map the subject"""
        from langchain_openai import ChatOpenAI
        from langchain.prompts import ChatPromptTemplate
        
        llm = ChatOpenAI(
            model_name=self.model_name,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.0,
            max_tokens=300
        )
        
        # Build category descriptions for prompt
        category_descriptions = ""
        for cat_name, cat_info in self.categories.items():
            category_descriptions += f"\n**{cat_name}**: {cat_info['description']}\n"
            category_descriptions += f"  Examples: {', '.join(cat_info['examples'])}\n"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an expert at analyzing customer feedback for win-loss analysis. Your task is to intelligently map natural customer language subjects to standardized business categories.

**AVAILABLE CATEGORIES:**{category_descriptions}

**CRITICAL: You must respond with ONLY valid JSON, no other text.**

**RESPONSE FORMAT - Return exactly this JSON structure:**
{{
  "mapped_category": "exact category name from list above or null",
  "confidence": 0.85,
  "reasoning": "one sentence explanation",
  "new_category_suggestion": null,
  "context_clues": ["key", "phrases"],
  "mapping_quality": "high"
}}

**MAPPING RULES:**
1. Use verbatim response content to understand context
2. Map "Pain Points" based on what the pain is about (pricing→Pricing and Commercial, support→Support and Service)
3. Suggest "Market Discovery" for Industry Events/Vendor Discovery patterns
4. Only use exact category names from the list above
5. Be honest about confidence (0.0 to 1.0)"""),
            ("user", f"""Subject: "{natural_subject}"
Response: "{verbatim_response[:300] if verbatim_response else 'No context'}"
Context: "{interview_context if interview_context else 'Unknown'}"

Return valid JSON only:""")
        ])
        
        try:
            response = llm.invoke(prompt.format_messages())
            llm_output = response.content.strip()
            
            # Multiple strategies for extracting JSON
            parsed_json = None
            
            # Strategy 1: Direct JSON parsing
            try:
                parsed_json = json.loads(llm_output)
            except json.JSONDecodeError:
                pass
            
            # Strategy 2: Extract from code blocks
            if not parsed_json:
                if llm_output.startswith('```json'):
                    json_content = llm_output.split('```json')[1].split('```')[0].strip()
                elif llm_output.startswith('```'):
                    json_content = llm_output.split('```')[1].strip()
                else:
                    json_content = llm_output
                
                try:
                    parsed_json = json.loads(json_content)
                except json.JSONDecodeError:
                    pass
            
            # Strategy 3: Find JSON pattern in text
            if not parsed_json:
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', llm_output, re.DOTALL)
                if json_match:
                    try:
                        parsed_json = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        pass
            
            # Strategy 4: Clean and retry
            if not parsed_json:
                # Remove common issues
                cleaned = llm_output.replace('\n', ' ').replace('\r', '').strip()
                # Find first { to last }
                start = cleaned.find('{')
                end = cleaned.rfind('}')
                if start != -1 and end != -1 and end > start:
                    try:
                        parsed_json = json.loads(cleaned[start:end+1])
                    except json.JSONDecodeError:
                        pass
            
            if parsed_json:
                return parsed_json
            else:
                # Complete fallback - create structured response
                logger.warning(f"⚠️ Could not parse JSON, using fallback for: {natural_subject}")
                return {
                    "mapped_category": None,
                    "confidence": 0.0,
                    "reasoning": f"JSON parsing failed for response: {llm_output[:100]}...",
                    "new_category_suggestion": None,
                    "context_clues": [],
                    "mapping_quality": "low"
                }
            
        except Exception as e:
            logger.error(f"❌ LLM call failed: {e}")
            return {
                "mapped_category": None,
                "confidence": 0.0,
                "reasoning": f"LLM call failed: {str(e)}",
                "new_category_suggestion": None,
                "context_clues": [],
                "mapping_quality": "low"
            }
    
    def _process_llm_response(self, natural_subject: str, llm_result: Dict) -> Dict:
        """Process and validate LLM mapping response"""
        mapped_category = llm_result.get('mapped_category')
        confidence = float(llm_result.get('confidence', 0.0))
        reasoning = llm_result.get('reasoning', 'No reasoning provided')
        new_category = llm_result.get('new_category_suggestion')
        context_clues = llm_result.get('context_clues', [])
        mapping_quality = llm_result.get('mapping_quality', 'low')
        
        # Validate mapped category exists
        if mapped_category and mapped_category not in self.categories:
            logger.warning(f"⚠️ LLM suggested unknown category: {mapped_category}")
            mapped_category = None
            confidence = 0.0
            reasoning += f" (Unknown category '{mapped_category}' suggested by LLM)"
        
        # Track new category suggestions
        if new_category:
            self.suggested_categories.add(new_category)
            logger.info(f"💡 New category suggested: '{new_category}' for subject '{natural_subject}'")
        
        # Determine mapping method
        if mapped_category and confidence >= 0.7:
            method = "llm_high_confidence"
        elif mapped_category and confidence >= 0.4:
            method = "llm_medium_confidence"
        elif new_category:
            method = "llm_new_category_suggested"
        else:
            method = "llm_unmappable"
        
        return self._create_result(
            natural_subject=natural_subject,
            harmonized_subject=mapped_category,
            confidence=confidence,
            method=method,
            reasoning=reasoning,
            new_category_suggestion=new_category,
            context_clues=context_clues,
            mapping_quality=mapping_quality
        )
    
    def _create_result(self, natural_subject: str, harmonized_subject: Optional[str], 
                      confidence: float, method: str, reasoning: str,
                      new_category_suggestion: Optional[str] = None,
                      context_clues: List[str] = None,
                      mapping_quality: str = "medium") -> Dict:
        """Create standardized harmonization result"""
        return {
            'natural_subject': natural_subject,
            'harmonized_subject': harmonized_subject,
            'confidence': round(confidence, 3),
            'mapping_method': method,
            'reasoning': reasoning,
            'new_category_suggestion': new_category_suggestion,
            'context_clues': context_clues or [],
            'mapping_quality': mapping_quality,
            'is_high_confidence': confidence >= 0.7,
            'requires_review': confidence < 0.4 or harmonized_subject is None,
            'mapped_at': datetime.now().isoformat()
        }
    
    def _track_mapping(self, result: Dict):
        """Track mapping statistics"""
        harmonized = result.get('harmonized_subject')
        confidence = result.get('confidence', 0.0)
        
        if harmonized:
            self.mapping_stats[harmonized] += 1
        
        self.confidence_scores.append(confidence)
        
        logger.debug(f"🎯 LLM mapped '{result['natural_subject']}' → '{harmonized}' "
                    f"(confidence: {confidence:.3f})")
    
    def batch_harmonize(self, subjects_data: List[Dict]) -> List[Dict]:
        """Harmonize multiple subjects using LLM semantic analysis"""
        results = []
        
        logger.info(f"🤖 Starting LLM batch harmonization of {len(subjects_data)} subjects")
        
        for i, item in enumerate(subjects_data):
            natural_subject = item.get('subject', '')
            verbatim_response = item.get('verbatim_response', '')
            
            # Build interview context
            interview_context = f"Company: {item.get('company', 'Unknown')}, " \
                              f"Deal Status: {item.get('deal_status', 'Unknown')}"
            
            result = self.harmonize_subject(natural_subject, verbatim_response, interview_context)
            
            # Add original data to result
            result.update({
                'response_id': item.get('response_id'),
                'interview_id': item.get('interview_id'),
                'client_id': item.get('client_id')
            })
            
            results.append(result)
            
            # Progress logging
            if (i + 1) % 5 == 0:
                logger.info(f"  Progress: {i + 1}/{len(subjects_data)} subjects processed")
        
        logger.info(f"✅ LLM batch harmonization complete: {len(results)} subjects processed")
        return results
    
    def get_harmonization_stats(self) -> Dict:
        """Get detailed mapping statistics and quality metrics"""
        total_mappings = len(self.confidence_scores)
        successful_mappings = sum(self.mapping_stats.values())
        avg_confidence = sum(self.confidence_scores) / len(self.confidence_scores) if self.confidence_scores else 0
        
        # Confidence distribution
        high_confidence = sum(1 for conf in self.confidence_scores if conf >= 0.7)
        medium_confidence = sum(1 for conf in self.confidence_scores if 0.4 <= conf < 0.7)
        low_confidence = sum(1 for conf in self.confidence_scores if conf < 0.4)
        
        return {
            'total_processed': total_mappings,
            'successful_mappings': successful_mappings,
            'mapping_rate': (successful_mappings / total_mappings * 100) if total_mappings > 0 else 0,
            'average_confidence': round(avg_confidence, 3),
            'confidence_distribution': {
                'high (≥0.7)': high_confidence,
                'medium (0.4-0.7)': medium_confidence,
                'low (<0.4)': low_confidence
            },
            'category_distribution': dict(self.mapping_stats),
            'suggested_new_categories': list(self.suggested_categories),
            'unique_categories_used': len(self.mapping_stats)
        }
    
    def get_category_definitions(self) -> Dict:
        """Get detailed category definitions for reference"""
        return self.categories

def main():
    """Command line interface for LLM semantic harmonization"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LLM-based semantic subject harmonization')
    parser.add_argument('--test', action='store_true', help='Run test with sample subjects')
    parser.add_argument('--stats', action='store_true', help='Show system status')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Initialize harmonizer
    harmonizer = LLMSemanticHarmonizer()
    
    if args.test:
        # Test with sample subjects and realistic context
        test_cases = [
            {
                "subject": "Product Features",
                "response": "The product has all the features we need and performs well for our use case."
            },
            {
                "subject": "Implementation Process", 
                "response": "The setup took longer than expected and the onboarding was confusing."
            },
            {
                "subject": "Pricing and Cost",
                "response": "The pricing was competitive and fit within our budget constraints."
            },
            {
                "subject": "Integration Issues",
                "response": "We had trouble connecting to our existing systems via their API."
            },
            {
                "subject": "Pain Points",
                "response": "The main pain point was the slow customer support response times."
            },
            {
                "subject": "Industry Events",
                "response": "We first learned about them at the Legal Tech conference last year."
            },
            {
                "subject": "Vendor Discovery",
                "response": "We found them through online research and referrals from colleagues."
            },
            {
                "subject": "Cost Considerations",
                "response": "The total cost of ownership was higher than initially quoted."
            }
        ]
        
        print("\n🤖 Testing LLM Semantic Harmonization:")
        print("=" * 80)
        
        for case in test_cases:
            result = harmonizer.harmonize_subject(case["subject"], case["response"])
            
            confidence_icon = "🎯" if result['is_high_confidence'] else "⚠️" if result['confidence'] >= 0.4 else "❌"
            mapped_to = result['harmonized_subject'] or result.get('new_category_suggestion', 'UNMAPPED')
            
            print(f"{confidence_icon} '{case['subject']}' → '{mapped_to}' (confidence: {result['confidence']})")
            print(f"   Reasoning: {result['reasoning']}")
            if result.get('new_category_suggestion'):
                print(f"   💡 Suggested new category: {result['new_category_suggestion']}")
            print()
        
        # Show overall stats
        stats = harmonizer.get_harmonization_stats()
        print(f"📊 LLM Harmonization Statistics:")
        print(f"  Mapping rate: {stats['mapping_rate']:.1f}%")
        print(f"  Average confidence: {stats['average_confidence']}")
        print(f"  Categories used: {stats['unique_categories_used']}")
        
        if stats['suggested_new_categories']:
            print(f"  💡 New categories suggested: {', '.join(stats['suggested_new_categories'])}")
    
    elif args.stats:
        categories = harmonizer.get_category_definitions()
        print("\n🤖 LLM Semantic Harmonization System:")
        print("=" * 60)
        print(f"Available categories: {len(categories)}")
        print(f"Model: {harmonizer.model_name}")
        
        print(f"\n📋 Available Categories:")
        for name, info in categories.items():
            print(f"  • {name}: {info['description']}")
    
    else:
        print("🤖 LLM Semantic Harmonization System Ready!")
        print("Use --test to run intelligent mapping test")
        print("Use --stats to show system status")

if __name__ == "__main__":
    main() 