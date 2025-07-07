#!/usr/bin/env python3

import os
import json
import re
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import concurrent.futures
import logging
from typing import Dict, List, Optional, Tuple
import yaml

# Import Supabase database manager
from supabase_database import SupabaseDatabase

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SupabaseStage2Analyzer:
    """
    Stage 2: Supabase-first quote labeling with incremental processing
    """
    
    def __init__(self, config_path="config/analysis_config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        
        # Use GPT-4o-mini with increased token limit
        self.llm = ChatOpenAI(
            model_name=self.config['processing'].get('model', 'gpt-4o-mini'),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=self.config['processing'].get('max_tokens', 8000),
            temperature=0.3
        )
        
        # Initialize Supabase database
        self.db = SupabaseDatabase()
        
        # Load criteria from config
        self.criteria = self.config.get('criteria', {})
        
        # Store current client_id for data siloing
        self.current_client_id = 'default'
        
        # Enhanced quality tracking
        self.quality_metrics = {
            "total_quotes_analyzed": 0,
            "quotes_with_scores": 0,
            "quotes_without_scores": 0,
            "criteria_coverage": set(),
            "processing_errors": 0,
            "truncated_quotes": 0,
            "context_preservation_issues": 0,
            "quotes_exceeding_length": 0
        }
    
    def load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Default configuration"""
        return {
            'scoring': {
                'scale': [0, 5],  # Binary + Intensity: 0 = not relevant, 1-5 = relevant with increasing importance
                'deal_weighting': {
                    'lost_deal_base': 1.2,
                    'won_deal_base': 0.9,
                    'critical_multiplier': 1.5,
                    'minor_multiplier': 0.7
                }
            },
            'processing': {
                'max_workers': 4,
                'max_quote_length': 3000,  # Increased from 1000
                'max_tokens': 8000,        # Added for GPT-4o-mini
                'model': 'gpt-4o-mini',    # Upgraded model
                'retry_attempts': 3,
                'batch_size': 50
            },
            'quality_tracking': {
                'track_truncation': True,
                'track_context_loss': True,
                'min_context_preservation': 0.8,
                'truncation_warning_threshold': 0.9
            },
            'criteria': {
                'product_capability': {
                    'description': 'Functionality, features, performance, and core solution fit',
                    'weight': 1.0,
                    'priority_threshold': 0.8
                },
                'implementation_onboarding': {
                    'description': 'Deployment ease, time-to-value, setup complexity',
                    'weight': 1.0,
                    'priority_threshold': 0.8
                },
                'integration_technical_fit': {
                    'description': 'APIs, data compatibility, technical architecture alignment',
                    'weight': 1.0,
                    'priority_threshold': 0.8
                },
                'support_service_quality': {
                    'description': 'Post-sale support, responsiveness, expertise, SLAs',
                    'weight': 1.0,
                    'priority_threshold': 0.8
                },
                'security_compliance': {
                    'description': 'Data protection, certifications, governance, risk management',
                    'weight': 1.0,
                    'priority_threshold': 0.8
                },
                'market_position_reputation': {
                    'description': 'Brand trust, references, analyst recognition, market presence',
                    'weight': 1.0,
                    'priority_threshold': 0.8
                },
                'vendor_stability': {
                    'description': 'Financial health, roadmap clarity, long-term viability',
                    'weight': 1.0,
                    'priority_threshold': 0.8
                },
                'sales_experience_partnership': {
                    'description': 'Buying process quality, relationship building, trust',
                    'weight': 1.0,
                    'priority_threshold': 0.8
                },
                'commercial_terms': {
                    'description': 'Price, contract flexibility, ROI, total cost of ownership',
                    'weight': 1.0,
                    'priority_threshold': 0.8
                },
                'speed_responsiveness': {
                    'description': 'Implementation timeline, decision-making speed, agility',
                    'weight': 1.0,
                    'priority_threshold': 0.8
                }
            }
        }
    
    def load_stage1_data_from_supabase(self, client_id: str = 'default') -> pd.DataFrame:
        """Load Stage 1 extracted quotes from Supabase, filtered by client_id"""
        df = self.db.get_core_responses(client_id=client_id)
        logger.info(f"📊 Loaded {len(df)} quotes from Supabase for client {client_id}")
        return df
    
    def get_unanalyzed_quotes(self, client_id: str = 'default') -> pd.DataFrame:
        """Get quotes that haven't been analyzed yet (incremental processing), filtered by client_id"""
        df = self.db.get_unanalyzed_quotes(client_id=client_id)
        logger.info(f"🔍 Found {len(df)} unanalyzed quotes for client {client_id}")
        return df
    
    def analyze_single_quote(self, quote_row: pd.Series) -> Optional[Dict]:
        """Analyze a single quote with improved context-aware scoring and quality tracking"""
        
        quote_id = quote_row.get('response_id', 'unknown')
        verbatim_response = quote_row.get('verbatim_response', '')
        subject = quote_row.get('subject', '')
        question = quote_row.get('question', '')
        deal_status = quote_row.get('deal_status', 'unknown')
        company = quote_row.get('company', 'unknown')
        interviewee = quote_row.get('interviewee_name', 'unknown')
        
        # Quality tracking for truncation and context preservation
        original_length = len(verbatim_response)
        max_length = self.config['processing']['max_quote_length']
        
        if original_length > max_length:
            self.quality_metrics["quotes_exceeding_length"] += 1
            truncation_ratio = max_length / original_length
            if truncation_ratio < self.config.get('quality_tracking', {}).get('min_context_preservation', 0.8):
                self.quality_metrics["context_preservation_issues"] += 1
                logger.warning(f"⚠️ Quote {quote_id}: Context preservation ratio {truncation_ratio:.2f} below threshold")
            if truncation_ratio > self.config.get('quality_tracking', {}).get('truncation_warning_threshold', 0.9):
                self.quality_metrics["truncated_quotes"] += 1
                logger.warning(f"⚠️ Quote {quote_id}: {truncation_ratio:.1%} of quote truncated")
        
        # Extract context keywords for smarter weighting
        context_keywords = self.extract_context_keywords(verbatim_response, subject, question)
        
        prompt = ChatPromptTemplate.from_template("""
            ANALYZE THIS QUOTE against the 10-criteria executive framework using BINARY + INTENSITY scoring.
            
            DEAL CONTEXT: {deal_status} deal
            
            QUOTE TO ANALYZE:
            Subject: {subject}
            Question: {question}
            Response: {verbatim_response}
            
            EVALUATION CRITERIA:
            {criteria}
            
            BINARY + INTENSITY SCORING SYSTEM:
            - 0 = Not relevant/not mentioned (omit from scores)
            - 1 = Slight mention/indirect relevance
            - 2 = Clear mention/direct relevance
            - 3 = Strong emphasis/important feedback
            - 4 = Critical feedback/deal-breaking issue
            - 5 = Exceptional praise/deal-winning strength
            
            TASK: Score this quote against ANY criteria that are even loosely relevant. Use the binary + intensity approach:
            1. First decide: Is this criterion relevant to the quote or question? (Binary: 0 or 1+)
            2. If relevant, then assess intensity: How important/impactful is this feedback? (1-5)
            3. Final score = Binary × Intensity (0 or 1-5)
            
            CONTEXT ANALYSIS:
            - Consider the QUESTION being asked - it provides crucial context
            - A question about "pricing" makes commercial_terms highly relevant
            - A question about "implementation" makes implementation_onboarding highly relevant
            - A question about "security" makes security_compliance highly relevant
            - If unsure about relevance, err on the side of inclusion and score it
            - Pay attention to nuanced language, tone, and implicit feedback
            - Capture both explicit statements and implied concerns or satisfaction
            - Consider industry-specific terminology and context clues
            
            SCORING EXAMPLES:
            - Question: "How do you evaluate pricing?" + Response: "pricing is reasonable" → commercial_terms: 2 (clear mention)
            - Question: "What about security?" + Response: "we're concerned about data privacy" → security_compliance: 4 (critical concern)
            - Question: "How was setup?" + Response: "setup was easy" → implementation_onboarding: 3 (strong positive)
            - Question: "What about pricing?" + Response: "the product works well" → commercial_terms: 1 (slight mention)
            - Question: "How do you use Rev?" + Response: "We use it for depositions and hearings, and it saves us time." → product_capability: 3 (strong positive)
            - Question: "What frustrates you?" + Response: "Sometimes the transcript isn't accurate." → product_capability: 4 (critical issue)
            - Question: "What integrations would help?" + Response: "We use Dropbox and Clio." → integration_technical_fit: 2 (clear mention)
            - Question: "How do you rank criteria?" + Response: "Speed and cost are most important, then security." → speed_responsiveness: 4, commercial_terms: 4, security_compliance: 3
            - Question: "What about support?" + Response: "Support is fine, but not a big factor." → support_service_quality: 1 (minor mention)
            
            OUTPUT FORMAT (JSON only):
            {{
                "scores": {{
                    "criterion_name": score_number
                }},
                "priorities": {{
                    "criterion_name": "critical|high|medium|low"
                }},
                "confidence": {{
                    "criterion_name": "high|medium|low"
                }},
                "relevance_explanation": {{
                    "criterion_name": "Brief explanation of how this quote relates to the criterion"
                }},
                "context_assessment": {{
                    "criterion_name": "deal_breaking|minor|neutral"
                }},
                "question_relevance": {{
                    "criterion_name": "direct|indirect|unrelated"
                }}
            }}
            
            IMPORTANT: Only include criteria in "scores" that are relevant (score > 0). If a criterion is not mentioned or relevant, omit it entirely.
            """)
        
        try:
            result = self.llm.invoke(prompt.format_messages(
                verbatim_response=verbatim_response[:max_length],
                subject=subject,
                question=question,
                criteria='\n'.join([f"- {k}: {v['description']}" for k, v in self.criteria.items()]),
                deal_status=deal_status
            ))
            
            # Log raw LLM output for debugging
            logger.info(f"LLM raw output for quote {quote_id}: {result.content}")
            
            # Parse JSON response
            parsed = self.parse_json_response(result.content)
            
            if parsed:
                # Apply smart deal weighting
                weighted_scores = {}
                scores = parsed.get("scores", {})
                
                for criterion, score in scores.items():
                    context = parsed.get("context_assessment", {}).get(criterion, "neutral")
                    weighted_scores[criterion] = self.apply_smart_deal_weighting(
                        score, deal_status, context, context_keywords
                    )
                
                # Save to Supabase
                self.save_analysis_to_supabase(
                    quote_id, deal_status, company, interviewee, 
                    verbatim_response[:200], subject, question,
                    scores, weighted_scores,
                    parsed.get("priorities", {}), parsed.get("confidence", {}),
                    parsed.get("relevance_explanation", {}), context_keywords,
                    parsed.get("question_relevance", {}), client_id=self.current_client_id
                )
                
                # Track metrics
                self.quality_metrics["total_quotes_analyzed"] += 1
                if scores:
                    self.quality_metrics["quotes_with_scores"] += 1
                    self.quality_metrics["criteria_coverage"].update(scores.keys())
                    logger.info(f"✅ Quote {quote_id}: {len(scores)} criteria scored")
                else:
                    self.quality_metrics["quotes_without_scores"] += 1
                    logger.warning(f"⚠️ Quote {quote_id}: Parsed successfully but no scores found")
                
                return {
                    "quote_id": quote_id,
                    "scores": scores,
                    "weighted_scores": weighted_scores,
                    "context_assessment": parsed.get("context_assessment", {}),
                    "quality_metrics": {
                        "original_length": original_length,
                        "truncated_length": len(verbatim_response[:max_length]),
                        "truncation_ratio": len(verbatim_response[:max_length]) / original_length if original_length > 0 else 1.0
                    }
                }
            else:
                logger.warning(f"⚠️ Failed to parse JSON for quote {quote_id}. Raw output: {result.content}")
                self.quality_metrics["processing_errors"] += 1
                return None
            
        except Exception as e:
            logger.error(f"❌ Analysis error for quote {quote_id}: {e}")
            self.quality_metrics["processing_errors"] += 1
            return None
    
    def extract_context_keywords(self, verbatim_response: str, subject: str, question: str) -> str:
        """Extract context keywords for smarter deal weighting"""
        text = f"{verbatim_response} {subject} {question}".lower()
        
        keywords = []
        
        # Deal impact keywords
        if any(word in text for word in ['deal breaker', 'lost because', 'critical', 'essential', 'must have']):
            keywords.append('deal_breaking')
        if any(word in text for word in ['minor', 'nice to have', 'could be better', 'would be nice']):
            keywords.append('minor')
        if any(word in text for word in ['neutral', 'okay', 'fine', 'acceptable']):
            keywords.append('neutral')
        
        # Question-specific context
        question_lower = question.lower()
        if any(word in question_lower for word in ['price', 'cost', 'pricing', 'expensive', 'cheap']):
            keywords.append('commercial_focus')
        if any(word in question_lower for word in ['security', 'privacy', 'compliance', 'data']):
            keywords.append('security_focus')
        if any(word in question_lower for word in ['setup', 'implementation', 'onboarding', 'deployment']):
            keywords.append('implementation_focus')
        if any(word in question_lower for word in ['support', 'service', 'help', 'assistance']):
            keywords.append('support_focus')
        
        return ','.join(keywords) if keywords else 'neutral'
    
    def apply_smart_deal_weighting(self, score: float, deal_status: str, context: str, keywords: str) -> float:
        """Apply context-aware deal weighting instead of simple positive/negative logic"""
        
        # Base weights from config
        base_weights = self.config['scoring']['deal_weighting']
        
        if deal_status == "lost":
            base_weight = base_weights['lost_deal_base']
        elif deal_status == "won":
            base_weight = base_weights['won_deal_base']
        else:
            base_weight = 1.0
        
        # Context-aware adjustments
        if context == "deal_breaking" or "deal_breaking" in keywords:
            multiplier = base_weights['critical_multiplier']
        elif context == "minor" or "minor" in keywords:
            multiplier = base_weights['minor_multiplier']
        else:
            multiplier = 1.0
        
        return score * base_weight * multiplier
    
    def save_analysis_to_supabase(self, quote_id: str, deal_status: str, company: str, interviewee: str,
                                original_quote: str, subject: str, question: str,
                                scores: Dict, weighted_scores: Dict, priorities: Dict, 
                                confidence: Dict, relevance_explanations: Dict, context_keywords: str,
                                question_relevance: Dict = None, client_id: str = 'default'):
        """Save analysis results to Supabase with client_id for data siloing"""
        
        for criterion in scores.keys():
            analysis_data = {
                'quote_id': quote_id,
                'criterion': criterion,
                'score': scores[criterion],
                'priority': priorities.get(criterion, 'medium'),
                'confidence': confidence.get(criterion, 'medium'),
                'relevance_explanation': relevance_explanations.get(criterion, ''),
                'deal_weighted_score': weighted_scores.get(criterion, scores[criterion]),
                'context_keywords': context_keywords,
                'question_relevance': question_relevance.get(criterion, 'unrelated') if question_relevance else 'unrelated',
                'client_id': client_id  # Add client_id for data siloing
            }
            
            self.db.save_quote_analysis(analysis_data)
    
    def process_incremental(self, force_reprocess: bool = False, client_id: str = 'default') -> Dict:
        """Process quotes incrementally - only new ones unless forced, filtered by client_id"""
        
        # Set current client_id for data siloing
        self.current_client_id = client_id
        
        logger.info("🚀 STAGE 2: INCREMENTAL QUOTE LABELING")
        logger.info("=" * 60)
        
        if force_reprocess:
            logger.info("📊 Processing ALL quotes (forced reprocess)")
            quotes_df = self.load_stage1_data_from_supabase(client_id=client_id)
        else:
            logger.info("📊 Processing only UNANALYZED quotes (incremental)")
            quotes_df = self.get_unanalyzed_quotes(client_id=client_id)
        
        if quotes_df.empty:
            logger.info("✅ No quotes to process")
            return {"status": "no_quotes_to_process"}
        
        logger.info(f"🔍 Analyzing {len(quotes_df)} quotes against 10 criteria...")
        
        start_time = datetime.now()
        
        # Process quotes in parallel with configurable workers
        analyses = []
        max_workers = self.config['processing']['max_workers']
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_quote = {
                executor.submit(self.analyze_single_quote, row): row.get('response_id', 'unknown')
                for _, row in quotes_df.iterrows()
            }
            
            for future in concurrent.futures.as_completed(future_to_quote):
                try:
                    analysis = future.result()
                    if analysis:
                        analyses.append(analysis)
                except Exception as e:
                    logger.error(f"❌ Error processing quote: {e}")
                    self.quality_metrics["processing_errors"] += 1
        
        # Calculate processing duration
        processing_duration = (datetime.now() - start_time).total_seconds()
        
        # Save processing metadata
        self.save_processing_metadata(len(quotes_df), len(analyses), processing_duration)
        
        # Generate summary
        summary = self.generate_summary_statistics(client_id)
        
        logger.info(f"\n✅ Stage 2 complete! Processed {len(analyses)} quotes in {processing_duration:.1f}s")
        self.print_summary_report(summary)
        
        return {
            "status": "success",
            "quotes_processed": len(quotes_df),
            "quotes_analyzed": len(analyses),
            "processing_duration_seconds": processing_duration,
            "summary": summary,
            "quality_metrics": self.quality_metrics
        }
    
    def save_processing_metadata(self, quotes_processed: int, quotes_analyzed: int, duration: float):
        """Save processing metadata for tracking"""
        metadata = {
            'quotes_processed': quotes_processed,
            'quotes_with_scores': quotes_analyzed,
            'processing_errors': self.quality_metrics["processing_errors"],
            'config_version': "1.0",
            'processing_duration_seconds': duration
        }
        self.db.save_processing_metadata(metadata)
    
    def generate_summary_statistics(self, client_id: str = 'default') -> Dict:
        """Generate summary statistics from Supabase, filtered by client_id"""
        return self.db.get_summary_statistics(client_id=client_id)
    
    def parse_json_response(self, response_text: str) -> Optional[Dict]:
        """Parse JSON response with fallback strategies"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Extract JSON from response if embedded
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
            
            # Common fixes
            json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)  # Remove trailing commas
            json_text = re.sub(r'(\w+):', r'"\1":', json_text)   # Quote unquoted keys
            
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                pass
        
        return None
    
    def print_summary_report(self, summary: Dict):
        """Print a comprehensive summary report with quality metrics"""
        
        logger.info(f"\n📊 STAGE 2 SUMMARY REPORT (Binary + Intensity Scoring)")
        logger.info("=" * 60)
        logger.info(f"Total quotes in database: {summary['total_quotes']}")
        logger.info(f"Quotes with scores: {summary['quotes_with_scores']} ({summary['coverage_percentage']}%)")
        logger.info(f"Criteria covered: {len(summary['criteria_performance'])}/10")
        
        # Quality metrics section
        logger.info(f"\n🔍 QUALITY METRICS:")
        logger.info("-" * 40)
        logger.info(f"Quotes exceeding length limit: {self.quality_metrics['quotes_exceeding_length']}")
        logger.info(f"Quotes with truncation: {self.quality_metrics['truncated_quotes']}")
        logger.info(f"Context preservation issues: {self.quality_metrics['context_preservation_issues']}")
        logger.info(f"Processing errors: {self.quality_metrics['processing_errors']}")
        
        if self.quality_metrics['quotes_exceeding_length'] > 0:
            truncation_percentage = (self.quality_metrics['truncated_quotes'] / self.quality_metrics['quotes_exceeding_length']) * 100
            logger.info(f"Truncation rate: {truncation_percentage:.1f}% of long quotes")
        
        logger.info(f"\n🏢 Deal Outcome Distribution:")
        for outcome, count in summary['deal_outcome_distribution'].items():
            percentage = (count / summary['total_quotes'] * 100) if summary['total_quotes'] > 0 else 0
            logger.info(f"  {outcome}: {count} ({percentage:.1f}%)")
        
        logger.info(f"\n📈 CRITERIA PERFORMANCE SCORECARD:")
        logger.info("-" * 70)
        logger.info(f"{'Criterion':<30} {'Avg Score':<10} {'Mentions':<10} {'Coverage':<10} {'Interpretation':<15}")
        logger.info("-" * 70)
        
        sorted_criteria = sorted(
            summary['criteria_performance'].items(),
            key=lambda x: x[1]['average_score'],
            reverse=True
        )
        
        for criterion, perf in sorted_criteria:
            score = perf['average_score']
            mentions = perf['mention_count']
            coverage = perf['coverage_percentage']
            
            # Interpret the score
            if score == 0:
                interpretation = "No feedback"
            elif score <= 1.5:
                interpretation = "Minor feedback"
            elif score <= 2.5:
                interpretation = "Moderate feedback"
            elif score <= 3.5:
                interpretation = "Important feedback"
            elif score <= 4.5:
                interpretation = "Critical feedback"
            else:
                interpretation = "Exceptional feedback"
            
            logger.info(f"{criterion:<30} {score:>8.2f}  {mentions:<9} {coverage:>6.1f}% {interpretation:<15}")
        
        logger.info(f"\n💡 SCORING INTERPRETATION:")
        logger.info("0 = Not relevant/not mentioned")
        logger.info("1 = Slight mention/indirect relevance")
        logger.info("2 = Clear mention/direct relevance")
        logger.info("3 = Strong emphasis/important feedback")
        logger.info("4 = Critical feedback/deal-breaking issue")
        logger.info("5 = Exceptional praise/deal-winning strength")
        
        logger.info(f"\n⚙️ CONFIGURATION:")
        logger.info(f"Model: {self.config['processing'].get('model', 'gpt-4o-mini')}")
        logger.info(f"Max quote length: {self.config['processing']['max_quote_length']} characters")
        logger.info(f"Max tokens: {self.config['processing'].get('max_tokens', 8000)}")

def run_supabase_analysis(force_reprocess: bool = False):
    """Run the Supabase-first quote analysis"""
    analyzer = SupabaseStage2Analyzer()
    return analyzer.process_incremental(force_reprocess)

# Run the analysis
if __name__ == "__main__":
    import sys
    
    # Check for force reprocess argument
    force_reprocess = "--force-reprocess" in sys.argv or "-f" in sys.argv
    
    if force_reprocess:
        print("🔄 Force reprocessing all quotes with new Binary + Intensity scoring system...")
        run_supabase_analysis(force_reprocess=True)
    else:
        print("🔄 Running incremental analysis with new Binary + Intensity scoring system...")
        run_supabase_analysis()
