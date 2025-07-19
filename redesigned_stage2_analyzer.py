#!/usr/bin/env python3
"""
Redesigned Stage 2 Response Labeling System
Completely overhauled to align with competitive intelligence objectives
"""

import os
import json
import re
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from supabase_database import SupabaseDatabase
from dotenv import load_dotenv
import concurrent.futures
import threading

load_dotenv()

class RedesignedStage2Analyzer:
    """
    Completely redesigned Stage 2 analyzer focused on competitive intelligence objectives:
    1. Multi-criteria analysis with relevance scores
    2. Nuanced sentiment detection
    3. Deal impact assessment
    4. Competitive positioning insights
    """
    
    def __init__(self, client_id: str, batch_size: int = 10, max_workers: int = 2):
        self.client_id = client_id
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.db = SupabaseDatabase()
        
        # Initialize LLM with optimized settings
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",  # Better reasoning for complex analysis
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=4000,
            temperature=0.1
        )
        
        # 10-Criteria Executive Scorecard Framework
        self.criteria_framework = {
            "product_capability": {
                "name": "Product Capability",
                "category": "Core Solution",
                "description": "Functionality, features, performance, solution fit",
                "keywords": ["feature", "functionality", "performance", "capability", "works", "doesn't work", "missing", "needs"],
                "weight": 1.0
            },
            "implementation_onboarding": {
                "name": "Implementation & Onboarding",
                "category": "Core Solution", 
                "description": "Deployment ease, time-to-value, setup complexity",
                "keywords": ["setup", "implementation", "onboarding", "deployment", "training", "go-live", "configuration"],
                "weight": 0.9
            },
            "integration_technical_fit": {
                "name": "Integration & Technical Fit",
                "category": "Core Solution",
                "description": "APIs, compatibility, architecture alignment, data integration",
                "keywords": ["integration", "api", "compatibility", "technical", "architecture", "data", "sync"],
                "weight": 0.8
            },
            "customer_support_experience": {
                "name": "Customer Support Experience",
                "category": "Trust & Risk",
                "description": "Support quality, responsiveness, expertise, problem resolution",
                "keywords": ["support", "help", "customer service", "response", "expertise", "resolve", "issue"],
                "weight": 0.9
            },
            "security_compliance": {
                "name": "Security & Compliance",
                "category": "Trust & Risk",
                "description": "Data protection, governance, risk management, certifications",
                "keywords": ["security", "compliance", "data protection", "privacy", "certification", "governance"],
                "weight": 0.8
            },
            "market_position_reputation": {
                "name": "Market Position & Reputation",
                "category": "Trust & Risk",
                "description": "Brand trust, references, analyst recognition, market presence",
                "keywords": ["brand", "reputation", "trust", "reference", "market", "analyst", "recognition"],
                "weight": 0.7
            },
            "sales_experience_partnership": {
                "name": "Sales Experience & Partnership",
                "category": "Experience & Commercial",
                "description": "Buying process quality, relationship building, trust",
                "keywords": ["sales", "buying", "process", "relationship", "partnership", "trust", "experience"],
                "weight": 0.8
            },
            "commercial_terms": {
                "name": "Commercial Terms",
                "category": "Experience & Commercial",
                "description": "Price, contract flexibility, ROI, total cost of ownership",
                "keywords": ["price", "cost", "contract", "roi", "value", "budget", "terms", "payment"],
                "weight": 0.9
            },
            "speed_responsiveness": {
                "name": "Speed & Responsiveness",
                "category": "Experience & Commercial",
                "description": "Implementation timeline, decision-making agility, response times",
                "keywords": ["speed", "fast", "slow", "timeline", "response", "quick", "delay", "time"],
                "weight": 0.8
            },
            "scalability_growth": {
                "name": "Scalability & Growth",
                "category": "Core Solution",
                "description": "Growth capacity, scaling capabilities, future-proofing",
                "keywords": ["scale", "growth", "expand", "future", "capacity", "grow", "scalable"],
                "weight": 0.7
            }
        }
        
        # Sentiment analysis framework
        self.sentiment_indicators = {
            "strongly_positive": [
                "love", "excellent", "amazing", "outstanding", "perfect", "fantastic", "brilliant",
                "exceeded expectations", "best", "superior", "outperforms", "delighted", "thrilled"
            ],
            "positive": [
                "like", "good", "great", "satisfied", "happy", "pleased", "works well", "effective",
                "meets needs", "reliable", "solid", "decent", "adequate", "sufficient"
            ],
            "neutral": [
                "okay", "fine", "acceptable", "standard", "typical", "normal", "average",
                "meets expectations", "adequate", "sufficient", "reasonable"
            ],
            "negative": [
                "dislike", "bad", "poor", "disappointed", "frustrated", "annoyed", "problem",
                "issue", "concern", "worried", "unsatisfied", "inadequate"
            ],
            "strongly_negative": [
                "hate", "terrible", "awful", "horrible", "worst", "fails", "broken", "useless",
                "waste", "regret", "disaster", "nightmare", "unacceptable", "deal breaker"
            ]
        }
        
        # Deal impact assessment
        self.deal_impact_indicators = {
            "deal_winner": ["deal breaker", "critical", "essential", "must have", "key factor", "primary reason"],
            "deal_breaker": ["deal breaker", "critical", "essential", "must have", "key factor", "primary reason"],
            "influential": ["important", "significant", "matters", "consideration", "factor"],
            "minor": ["nice to have", "bonus", "minor", "small", "insignificant"]
        }
    
    def process_quotes(self, client_id: str = None) -> Dict[str, Any]:
        """Process all quotes for the client with redesigned analysis"""
        if client_id is None:
            client_id = self.client_id
            
        print(f"🔄 Starting redesigned Stage 2 analysis for client: {client_id}")
        
        # Get quotes from Stage 1
        quotes_df = self.db.get_stage1_quotes(client_id)
        if quotes_df.empty:
            return {"error": "No quotes found for processing"}
        
        print(f"📊 Processing {len(quotes_df)} quotes in batches of {self.batch_size}")
        
        # Process in batches
        results = []
        total_batches = (len(quotes_df) + self.batch_size - 1) // self.batch_size
        
        for batch_idx in range(0, len(quotes_df), self.batch_size):
            batch_df = quotes_df.iloc[batch_idx:batch_idx + self.batch_size]
            print(f"📦 Processing batch {batch_idx // self.batch_size + 1}/{total_batches}")
            
            batch_results = self._process_batch_enhanced(batch_df, client_id)
            results.extend(batch_results)
        
        # Save results to database
        self._save_enhanced_results(results, client_id)
        
        # Generate quality report
        quality_report = self._generate_quality_report(results)
        
        return {
            "total_quotes_processed": len(results),
            "successful_analyses": len([r for r in results if r.get('analysis_success', False)]),
            "quality_report": quality_report,
            "results": results
        }
    
    def _process_batch_enhanced(self, batch_df: pd.DataFrame, client_id: str) -> List[Dict]:
        """Process a batch of quotes with enhanced multi-criteria analysis"""
        results = []
        
        for _, quote_row in batch_df.iterrows():
            try:
                # Extract quote data
                quote_id = quote_row.get('quote_id', f"quote_{quote_row.name}")
                quote_text = quote_row.get('verbatim_response', '')
                company = quote_row.get('company', '')
                interviewee = quote_row.get('interviewee_name', '')
                
                if not quote_text or len(quote_text.strip()) < 10:
                    continue
                
                # Perform enhanced analysis
                analysis_result = self._analyze_quote_enhanced(
                    quote_id, quote_text, company, interviewee
                )
                
                # Add metadata
                analysis_result.update({
                    'client_id': client_id,
                    'quote_id': quote_id,
                    'company': company,
                    'interviewee_name': interviewee,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'analysis_version': '2.0_redesigned'
                })
                
                results.append(analysis_result)
                
            except Exception as e:
                print(f"❌ Error processing quote {quote_id}: {str(e)}")
                results.append({
                    'quote_id': quote_id,
                    'analysis_success': False,
                    'error': str(e),
                    'client_id': client_id,
                    'analysis_timestamp': datetime.now().isoformat()
                })
        
        return results
    
    def _analyze_quote_enhanced(self, quote_id: str, quote_text: str, company: str, interviewee: str) -> Dict:
        """Enhanced quote analysis with multi-criteria scoring and nuanced sentiment"""
        
        # Prepare analysis prompt
        analysis_prompt = self._create_enhanced_analysis_prompt(quote_text, company, interviewee)
        
        try:
            # Get LLM analysis
            llm_response = self.llm.invoke(analysis_prompt)
            analysis_text = llm_response.content
            
            # Parse and validate response
            parsed_analysis = self._parse_enhanced_analysis(analysis_text, quote_text)
            
            # Add validation and quality checks
            validated_analysis = self._validate_enhanced_analysis(parsed_analysis, quote_text)
            
            return {
                'analysis_success': True,
                'analysis_data': validated_analysis,
                'raw_llm_response': analysis_text
            }
            
        except Exception as e:
            print(f"❌ LLM analysis failed for quote {quote_id}: {str(e)}")
            return {
                'analysis_success': False,
                'error': str(e),
                'fallback_analysis': self._create_fallback_analysis(quote_text)
            }
    
    def _create_enhanced_analysis_prompt(self, quote_text: str, company: str, interviewee: str) -> str:
        """Create enhanced analysis prompt for multi-criteria evaluation"""
        
        criteria_descriptions = []
        for key, info in self.criteria_framework.items():
            criteria_descriptions.append(f"- {key}: {info['description']}")
        
        criteria_text = "\n".join(criteria_descriptions)
        
        prompt = f"""You are an expert competitive intelligence analyst specializing in B2B SaaS customer feedback analysis. Your task is to analyze this customer quote and provide comprehensive insights for competitive intelligence.

QUOTE TO ANALYZE:
"{quote_text}"

COMPANY: {company}
INTERVIEWEE: {interviewee}

ANALYSIS REQUIREMENTS:

1. MULTI-CRITERIA EVALUATION:
Evaluate this quote against ALL 10 criteria below. For each criterion:
- Assign a relevance score (0-5): 0=not mentioned, 1=minimal mention, 2=some relevance, 3=moderate relevance, 4=high relevance, 5=critical relevance
- Provide sentiment: strongly_positive, positive, neutral, negative, strongly_negative
- Assess deal impact: deal_winner, influential, minor, deal_breaker
- Include confidence level: high, medium, low

CRITERIA TO EVALUATE:
{criteria_text}

2. SENTIMENT ANALYSIS:
Use nuanced sentiment detection based on specific language patterns and context. Consider:
- Emotional intensity and specific words used
- Comparative language (vs competitors)
- Business impact language
- Temporal language (past vs present vs future)

3. DEAL IMPACT ASSESSMENT:
Assess how this feedback impacts deal outcomes:
- deal_winner: Strong positive factor that helps win deals
- deal_breaker: Critical negative factor that loses deals  
- influential: Important factor that affects decisions
- minor: Small factor with minimal impact

4. COMPETITIVE POSITIONING:
Identify competitive insights:
- Strengths to leverage
- Weaknesses to address
- Competitive advantages
- Market positioning insights

RESPONSE FORMAT (JSON):
{{
  "quote_analysis": {{
    "overall_sentiment": "positive/negative/neutral/mixed",
    "primary_criterion": "criterion_key",
    "deal_impact": "deal_winner/deal_breaker/influential/minor",
    "competitive_insight": "brief insight about competitive positioning"
  }},
  "criteria_evaluation": {{
    "criterion_key": {{
      "relevance_score": 0-5,
      "sentiment": "strongly_positive/positive/neutral/negative/strongly_negative",
      "deal_impact": "deal_winner/deal_breaker/influential/minor",
      "confidence": "high/medium/low",
      "explanation": "brief explanation of scoring"
    }}
  }},
  "competitive_insights": {{
    "strengths": ["list of strengths identified"],
    "weaknesses": ["list of weaknesses identified"],
    "opportunities": ["list of opportunities identified"],
    "threats": ["list of threats identified"]
  }}
}}

Respond with ONLY valid JSON. No additional text or explanations."""

        return prompt
    
    def _parse_enhanced_analysis(self, analysis_text: str, quote_text: str) -> Dict:
        """Parse and validate enhanced analysis response"""
        
        try:
            # Clean the response
            cleaned_text = self._clean_json_response(analysis_text)
            
            # Parse JSON
            parsed = json.loads(cleaned_text)
            
            # Validate structure
            if not isinstance(parsed, dict):
                raise ValueError("Response is not a valid JSON object")
            
            # Ensure required fields
            required_fields = ['quote_analysis', 'criteria_evaluation', 'competitive_insights']
            for field in required_fields:
                if field not in parsed:
                    parsed[field] = {}
            
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {str(e)}")
            print(f"Raw response: {analysis_text[:200]}...")
            raise ValueError(f"Invalid JSON response: {str(e)}")
    
    def _clean_json_response(self, response_text: str) -> str:
        """Clean and prepare JSON response for parsing"""
        
        # Remove markdown code blocks
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        
        # Find JSON object boundaries
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            raise ValueError("No valid JSON object found in response")
        
        json_text = response_text[start_idx:end_idx + 1]
        
        # Fix common JSON issues
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)  # Remove trailing commas
        json_text = re.sub(r'(\w+):', r'"\1":', json_text)  # Quote unquoted keys
        
        return json_text
    
    def _validate_enhanced_analysis(self, parsed_analysis: Dict, quote_text: str) -> Dict:
        """Validate and enhance the analysis with quality checks"""
        
        validated = parsed_analysis.copy()
        
        # Validate criteria evaluation
        criteria_eval = validated.get('criteria_evaluation', {})
        for criterion_key, eval_data in criteria_eval.items():
            if not isinstance(eval_data, dict):
                continue
                
            # Ensure relevance score is valid
            relevance_score = eval_data.get('relevance_score', 0)
            if not isinstance(relevance_score, (int, float)) or relevance_score < 0 or relevance_score > 5:
                eval_data['relevance_score'] = 0
            
            # Ensure sentiment is valid
            valid_sentiments = ['strongly_positive', 'positive', 'neutral', 'negative', 'strongly_negative']
            sentiment = eval_data.get('sentiment', 'neutral')
            if sentiment not in valid_sentiments:
                eval_data['sentiment'] = 'neutral'
            
            # Ensure deal impact is valid
            valid_impacts = ['deal_winner', 'deal_breaker', 'influential', 'minor']
            deal_impact = eval_data.get('deal_impact', 'minor')
            if deal_impact not in valid_impacts:
                eval_data['deal_impact'] = 'minor'
            
            # Ensure confidence is valid
            valid_confidence = ['high', 'medium', 'low']
            confidence = eval_data.get('confidence', 'medium')
            if confidence not in valid_confidence:
                eval_data['confidence'] = 'medium'
        
        # Calculate overall metrics
        validated['overall_metrics'] = self._calculate_overall_metrics(criteria_eval)
        
        return validated
    
    def _calculate_overall_metrics(self, criteria_eval: Dict) -> Dict:
        """Calculate overall metrics from criteria evaluation"""
        
        metrics = {
            'total_criteria_evaluated': len(criteria_eval),
            'criteria_with_relevance': 0,
            'average_relevance_score': 0,
            'sentiment_distribution': {},
            'deal_impact_distribution': {},
            'high_confidence_evaluations': 0,
            'primary_criterion': None,
            'primary_relevance_score': 0
        }
        
        relevance_scores = []
        sentiment_counts = {}
        impact_counts = {}
        
        for criterion_key, eval_data in criteria_eval.items():
            if not isinstance(eval_data, dict):
                continue
            
            relevance_score = eval_data.get('relevance_score', 0)
            if relevance_score > 0:
                metrics['criteria_with_relevance'] += 1
                relevance_scores.append(relevance_score)
                
                # Track primary criterion
                if relevance_score > metrics['primary_relevance_score']:
                    metrics['primary_criterion'] = criterion_key
                    metrics['primary_relevance_score'] = relevance_score
            
            # Track sentiment distribution
            sentiment = eval_data.get('sentiment', 'neutral')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            
            # Track deal impact distribution
            deal_impact = eval_data.get('deal_impact', 'minor')
            impact_counts[deal_impact] = impact_counts.get(deal_impact, 0) + 1
            
            # Track confidence
            confidence = eval_data.get('confidence', 'medium')
            if confidence == 'high':
                metrics['high_confidence_evaluations'] += 1
        
        # Calculate averages
        if relevance_scores:
            metrics['average_relevance_score'] = round(sum(relevance_scores) / len(relevance_scores), 2)
        
        metrics['sentiment_distribution'] = sentiment_counts
        metrics['deal_impact_distribution'] = impact_counts
        
        return metrics
    
    def _create_fallback_analysis(self, quote_text: str) -> Dict:
        """Create fallback analysis when LLM fails"""
        
        # Simple keyword-based analysis
        quote_lower = quote_text.lower()
        
        # Find most relevant criterion
        criterion_scores = {}
        for criterion_key, info in self.criteria_framework.items():
            score = 0
            for keyword in info['keywords']:
                if keyword in quote_lower:
                    score += 1
            criterion_scores[criterion_key] = score
        
        primary_criterion = max(criterion_scores.items(), key=lambda x: x[1])[0] if criterion_scores else 'product_capability'
        
        # Simple sentiment detection
        sentiment = 'neutral'
        positive_words = ['like', 'good', 'great', 'love', 'excellent', 'satisfied']
        negative_words = ['hate', 'bad', 'poor', 'disappointed', 'frustrated', 'problem']
        
        if any(word in quote_lower for word in positive_words):
            sentiment = 'positive'
        elif any(word in quote_lower for word in negative_words):
            sentiment = 'negative'
        
        return {
            'quote_analysis': {
                'overall_sentiment': sentiment,
                'primary_criterion': primary_criterion,
                'deal_impact': 'minor',
                'competitive_insight': 'Fallback analysis - limited insights available'
            },
            'criteria_evaluation': {
                primary_criterion: {
                    'relevance_score': 2,
                    'sentiment': sentiment,
                    'deal_impact': 'minor',
                    'confidence': 'low',
                    'explanation': 'Fallback analysis due to processing error'
                }
            },
            'competitive_insights': {
                'strengths': [],
                'weaknesses': [],
                'opportunities': [],
                'threats': []
            },
            'overall_metrics': {
                'total_criteria_evaluated': 1,
                'criteria_with_relevance': 1,
                'average_relevance_score': 2.0,
                'sentiment_distribution': {sentiment: 1},
                'deal_impact_distribution': {'minor': 1},
                'high_confidence_evaluations': 0,
                'primary_criterion': primary_criterion,
                'primary_relevance_score': 2
            }
        }
    
    def _save_enhanced_results(self, results: List[Dict], client_id: str):
        """Save enhanced results to database"""
        
        print(f"💾 Saving {len(results)} enhanced analysis results to database...")
        
        for result in results:
            if not result.get('analysis_success', False):
                continue
            
            analysis_data = result.get('analysis_data', {})
            criteria_eval = analysis_data.get('criteria_evaluation', {})
            
            # Save each criterion evaluation as a separate record
            for criterion_key, eval_data in criteria_eval.items():
                if not isinstance(eval_data, dict):
                    continue
                
                # Prepare database record
                db_record = {
                    'quote_id': result['quote_id'],
                    'client_id': client_id,
                    'criterion': criterion_key,
                    'relevance_score': eval_data.get('relevance_score', 0),
                    'sentiment': eval_data.get('sentiment', 'neutral'),
                    'priority': eval_data.get('deal_impact', 'minor'),
                    'confidence': eval_data.get('confidence', 'medium'),
                    'relevance_explanation': eval_data.get('explanation', ''),
                    'analysis_timestamp': result.get('analysis_timestamp'),
                    'analysis_version': result.get('analysis_version', '2.0_redesigned'),
                    'processing_metadata': {
                        'overall_sentiment': analysis_data.get('quote_analysis', {}).get('overall_sentiment'),
                        'competitive_insight': analysis_data.get('quote_analysis', {}).get('competitive_insight'),
                        'high_confidence': eval_data.get('confidence') == 'high'
                    }
                }
                
                # Save to database
                try:
                    self.db.supabase.table('stage2_response_labeling').insert(db_record).execute()
                except Exception as e:
                    print(f"❌ Failed to save record for quote {result['quote_id']}: {str(e)}")
    
    def _generate_quality_report(self, results: List[Dict]) -> Dict:
        """Generate quality report for the analysis"""
        
        successful_results = [r for r in results if r.get('analysis_success', False)]
        
        if not successful_results:
            return {"error": "No successful analyses to report on"}
        
        # Calculate quality metrics
        total_quotes = len(results)
        successful_quotes = len(successful_results)
        success_rate = (successful_quotes / total_quotes * 100) if total_quotes > 0 else 0
        
        # Analyze criteria distribution
        criteria_counts = {}
        sentiment_distribution = {}
        relevance_scores = []
        confidence_distribution = {}
        
        for result in successful_results:
            analysis_data = result.get('analysis_data', {})
            criteria_eval = analysis_data.get('criteria_evaluation', {})
            
            for criterion_key, eval_data in criteria_eval.items():
                if not isinstance(eval_data, dict):
                    continue
                
                # Count criteria
                criteria_counts[criterion_key] = criteria_counts.get(criterion_key, 0) + 1
                
                # Count sentiments
                sentiment = eval_data.get('sentiment', 'neutral')
                sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1
                
                # Collect relevance scores
                relevance_score = eval_data.get('relevance_score', 0)
                if relevance_score > 0:
                    relevance_scores.append(relevance_score)
                
                # Count confidence levels
                confidence = eval_data.get('confidence', 'medium')
                confidence_distribution[confidence] = confidence_distribution.get(confidence, 0) + 1
        
        return {
            'summary': {
                'total_quotes': total_quotes,
                'successful_quotes': successful_quotes,
                'success_rate': round(success_rate, 1),
                'average_relevance_score': round(np.mean(relevance_scores), 2) if relevance_scores else 0
            },
            'criteria_distribution': criteria_counts,
            'sentiment_distribution': sentiment_distribution,
            'confidence_distribution': confidence_distribution,
            'quality_indicators': {
                'criteria_coverage': len(criteria_counts),
                'sentiment_diversity': len(sentiment_distribution),
                'high_confidence_rate': (confidence_distribution.get('high', 0) / sum(confidence_distribution.values()) * 100) if confidence_distribution else 0
            }
        }

def run_redesigned_stage2_analysis(client_id: str = "Rev"):
    """Run the redesigned Stage 2 analysis"""
    analyzer = RedesignedStage2Analyzer(client_id)
    return analyzer.process_quotes(client_id)

if __name__ == "__main__":
    results = run_redesigned_stage2_analysis()
    print(json.dumps(results, indent=2)) 