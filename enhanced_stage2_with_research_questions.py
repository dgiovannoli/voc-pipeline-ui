#!/usr/bin/env python3
"""
Enhanced Stage 2 Processor with Research Question Alignment
Adds sentiment, impact, and research question alignment analysis
"""

import sys
import os
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import our modules
from supabase_database import SupabaseDatabase
from discussion_guide_integration import DiscussionGuideIntegrator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Progress tracking for UI
stage2_progress_data = {"completed_responses": 0, "total_responses": 0, "results": [], "errors": []}
stage2_progress_lock = threading.Lock()

class EnhancedStage2WithResearchQuestions:
    """Enhanced Stage 2 processor with research question alignment"""
    
    def __init__(self, batch_size: int = 30, max_workers: int = 3):
        self.batch_size = batch_size
        self.max_workers = max_workers
        
        # Initialize database
        try:
            self.db = SupabaseDatabase()
            logger.info("✅ Enhanced Stage 2 with Research Questions initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Stage 2 processor: {e}")
            raise
        
        # Initialize discussion guide integrator
        self.discussion_guide_integrator = DiscussionGuideIntegrator()
        
        # Track processing stats
        self.processing_stats = {
            'total_processed': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0, 'mixed': 0},
            'impact_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            'research_question_coverage': {},
            'harmonized_subjects_analyzed': set()
        }
    
    def process_incremental(self, client_id: str = "default") -> Dict:
        """Process unanalyzed responses for Stage 2 with research question alignment"""
        
        logger.info(f"🎯 Starting enhanced Stage 2 analysis with research questions for client: {client_id}")
        
        try:
            # Load research questions for this client
            research_questions = self._load_research_questions(client_id)
            logger.info(f"📋 Loaded {len(research_questions)} research questions for analysis")
            
            # Get unanalyzed responses
            unanalyzed_data = self._get_unanalyzed_responses(client_id)
            
            if not unanalyzed_data:
                logger.info("📋 No unanalyzed responses found")
                return self._create_summary_result()
            
            logger.info(f"📊 Found {len(unanalyzed_data)} responses ready for Stage 2 analysis")
            
            # Update progress tracking
            with stage2_progress_lock:
                stage2_progress_data['total_responses'] = len(unanalyzed_data)
                stage2_progress_data['completed_responses'] = 0
                stage2_progress_data['results'] = []
                stage2_progress_data['errors'] = []
            
            # Process in batches with research questions
            results = self._process_batches_with_research_questions(unanalyzed_data, client_id, research_questions)
            
            # Generate summary
            summary = self._create_summary_result()
            logger.info(f"✅ Enhanced Stage 2 analysis complete: {summary['successful_analyses']}/{summary['total_processed']} successful")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Enhanced Stage 2 analysis failed: {e}")
            raise
    
    def _load_research_questions(self, client_id: str) -> List[str]:
        """Load research questions for the client"""
        try:
            # Try to load from discussion guide file
            discussion_guide_path = f"uploads/{client_id.title()}_PRJ-00027 Discussion Guide v1.txt"
            if os.path.exists(discussion_guide_path):
                discussion_guide = self.discussion_guide_integrator.parse_supio_discussion_guide(discussion_guide_path)
                return discussion_guide['questions']
            else:
                # Fallback to default questions
                logger.warning(f"⚠️ No discussion guide found for {client_id}, using default questions")
                return [
                    "What prompted the evaluation of solutions?",
                    "What were the key criteria for evaluation?",
                    "How does the vendor compare to competitors?",
                    "What are the vendor's strengths?",
                    "What are the vendor's weaknesses?",
                    "What was the implementation experience?",
                    "How does pricing influence decisions?",
                    "What support and service experience did you have?"
                ]
        except Exception as e:
            logger.error(f"❌ Failed to load research questions: {e}")
            return []
    
    def _get_unanalyzed_responses(self, client_id: str) -> List[Dict]:
        """Get responses that have harmonized subjects but no Stage 2 analysis"""
        try:
            # Get all responses for this client
            df = self.db.get_stage1_data_responses(client_id=client_id)
            
            if df.empty:
                return []
            
            # Filter for responses with harmonized subjects but no research question alignment
            filtered_df = df[
                (df['harmonized_subject'].notna()) & 
                (df['harmonized_subject'] != '') & 
                (df['research_question_alignment'].isna() | (df['research_question_alignment'] == ''))
            ]
            
            # Convert to list of dictionaries
            return filtered_df.to_dict('records')
            
        except Exception as e:
            logger.error(f"❌ Failed to get unanalyzed responses: {e}")
            return []
    
    def _process_batches_with_research_questions(self, data_list: List[Dict], client_id: str, research_questions: List[str]) -> List[Dict]:
        """Process responses in batches with research question alignment"""
        
        total_batches = (len(data_list) + self.batch_size - 1) // self.batch_size
        logger.info(f"🔄 Processing {len(data_list)} responses in {total_batches} batches")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit batch processing tasks
            future_to_batch = {}
            for i in range(0, len(data_list), self.batch_size):
                batch_data = data_list[i:i + self.batch_size]
                batch_num = i // self.batch_size + 1
                future = executor.submit(self._process_batch_with_research_questions, batch_num, batch_data, client_id, research_questions)
                future_to_batch[future] = batch_num
            
            # Collect results
            for future in as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                try:
                    batch_results = future.result()
                    results.extend(batch_results)
                    logger.info(f"✅ Batch {batch_num}/{total_batches} completed")
                except Exception as e:
                    logger.error(f"❌ Batch {batch_num} failed: {e}")
        
        return results
    
    def _process_batch_with_research_questions(self, batch_num: int, batch_data: List[Dict], client_id: str, research_questions: List[str]) -> List[Dict]:
        """Process a batch of responses with research question alignment"""
        
        batch_results = []
        
        for response_data in batch_data:
            try:
                # Analyze sentiment, impact, and research question alignment
                analysis_result = self._analyze_sentiment_impact_and_research_questions(response_data, research_questions)
                
                # Update database
                success = self._update_stage2_analysis(response_data['response_id'], analysis_result)
                
                if success:
                    batch_results.append(analysis_result)
                    self._update_processing_stats(analysis_result, True)
                else:
                    self._update_processing_stats(analysis_result, False)
                
                # Update progress
                with stage2_progress_lock:
                    stage2_progress_data['completed_responses'] += 1
                
            except Exception as e:
                logger.error(f"❌ Failed to process response {response_data.get('response_id')}: {e}")
                self._update_processing_stats({}, False)
                
                with stage2_progress_lock:
                    stage2_progress_data['completed_responses'] += 1
                    stage2_progress_data['errors'].append(str(e))
        
        return batch_results
    
    def _analyze_sentiment_impact_and_research_questions(self, response_data: Dict, research_questions: List[str]) -> Dict:
        """Analyze sentiment, impact, and research question alignment using LLM"""
        
        try:
            from langchain_openai import ChatOpenAI
            
            llm = ChatOpenAI(
                model_name="gpt-4o-mini",
                temperature=0.0,
                max_tokens=400
            )
            
            # Build analysis prompt with research questions
            harmonized_subject = response_data.get('harmonized_subject', 'Unknown')
            verbatim_response = response_data.get('verbatim_response', '')
            deal_status = response_data.get('deal_status', 'Unknown')
            
            # Format research questions for prompt
            research_questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(research_questions)])
            
            prompt_text = f"""Analyze this customer feedback for sentiment, decision impact, and research question alignment.

CATEGORY: "{harmonized_subject}"
CUSTOMER SAID: "{verbatim_response[:400]}"
DEAL STATUS: "{deal_status}"

RESEARCH QUESTIONS TO EVALUATE:
{research_questions_text}

Provide analysis in this JSON format:
{{
    "sentiment": "positive/negative/neutral/mixed",
    "impact_score": 1-5,
    "reasoning": "brief explanation of sentiment and impact",
    "research_question_alignment": [
        {{
            "question_index": 0,
            "question_text": "exact question text",
            "alignment_score": 1-5,
            "keywords_matched": ["keyword1", "keyword2"],
            "coverage_priority": "high/medium/low"
        }}
    ],
    "total_questions_addressed": 2,
    "coverage_summary": "brief summary of research question coverage"
}}

Guidelines:
- SENTIMENT: positive, negative, neutral, or mixed
- IMPACT SCORE (1-5): How much this influenced their buying decision
- RESEARCH QUESTION ALIGNMENT: Which questions this response addresses (alignment_score 1-5)
- COVERAGE PRIORITY: high (direct answer), medium (partial answer), low (tangential)
- Only include questions where alignment_score >= 3"""

            response = llm.invoke(prompt_text)
            result_text = response.content.strip()
            
            # Parse JSON response
            result_text = result_text.replace('```json', '').replace('```', '').strip()
            
            # Find JSON in response
            start = result_text.find('{')
            end = result_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_text = result_text[start:end]
                try:
                    llm_result = json.loads(json_text)
                except:
                    llm_result = self._parse_fallback_with_research_questions(result_text, response_data, research_questions)
            else:
                llm_result = self._parse_fallback_with_research_questions(result_text, response_data, research_questions)
            
            # Validate and standardize result
            return self._standardize_stage2_result_with_research_questions(response_data, llm_result, research_questions)
            
        except Exception as e:
            logger.error(f"❌ LLM analysis failed for '{response_data.get('response_id')}': {e}")
            return self._fallback_analysis_with_research_questions(response_data, research_questions)
    
    def _parse_fallback_with_research_questions(self, text: str, response_data: Dict, research_questions: List[str]) -> Dict:
        """Fallback parsing when JSON fails"""
        sentiment = "neutral"
        impact_score = 3
        
        # Extract sentiment from text
        text_lower = text.lower()
        if any(word in text_lower for word in ["positive", "good", "great", "excellent"]):
            sentiment = "positive"
        elif any(word in text_lower for word in ["negative", "bad", "poor", "terrible"]):
            sentiment = "negative"
        elif "mixed" in text_lower:
            sentiment = "mixed"
        
        # Extract impact score from text
        for i in range(1, 6):
            if str(i) in text:
                impact_score = i
                break
        
        # Simple research question alignment
        response_text = response_data.get('verbatim_response', '').lower()
        alignments = []
        
        for i, question in enumerate(research_questions):
            question_lower = question.lower()
            keywords = [word for word in question_lower.split() if len(word) > 3]
            matches = [kw for kw in keywords if kw in response_text]
            
            if matches:
                alignment_score = len(matches) / len(keywords)
                if alignment_score > 0.3:
                    alignments.append({
                        "question_index": i,
                        "question_text": question,
                        "alignment_score": min(5, int(alignment_score * 5)),
                        "keywords_matched": matches,
                        "coverage_priority": "high" if alignment_score > 0.5 else "medium"
                    })
        
        return {
            "sentiment": sentiment,
            "impact_score": impact_score,
            "reasoning": f"Fallback parsing from: {text[:50]}...",
            "research_question_alignment": alignments,
            "total_questions_addressed": len(alignments),
            "coverage_summary": f"Addresses {len(alignments)} research questions"
        }
    
    def _fallback_analysis_with_research_questions(self, response_data: Dict, research_questions: List[str]) -> Dict:
        """Rule-based fallback when LLM fails"""
        verbatim = response_data.get('verbatim_response', '').lower()
        deal_status = response_data.get('deal_status', '').lower()
        
        # Simple sentiment analysis
        positive_words = ['good', 'great', 'excellent', 'love', 'amazing', 'perfect', 'satisfied']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'problems', 'issues', 'disappointed', 'frustrated']
        
        positive_count = sum(1 for word in positive_words if word in verbatim)
        negative_count = sum(1 for word in negative_words if word in verbatim)
        
        if positive_count > negative_count:
            sentiment = "positive"
            impact_score = 4
        elif negative_count > positive_count:
            sentiment = "negative"
            impact_score = 4
        else:
            sentiment = "neutral"
            impact_score = 3
        
        # Simple research question alignment
        alignments = []
        for i, question in enumerate(research_questions):
            question_lower = question.lower()
            keywords = [word for word in question_lower.split() if len(word) > 3]
            matches = [kw for kw in keywords if kw in verbatim]
            
            if matches:
                alignment_score = len(matches) / len(keywords)
                if alignment_score > 0.3:
                    alignments.append({
                        "question_index": i,
                        "question_text": question,
                        "alignment_score": min(5, int(alignment_score * 5)),
                        "keywords_matched": matches,
                        "coverage_priority": "high" if alignment_score > 0.5 else "medium"
                    })
        
        return {
            "sentiment": sentiment,
            "impact_score": impact_score,
            "reasoning": f"Rule-based analysis: {sentiment} sentiment, {impact_score} impact",
            "research_question_alignment": alignments,
            "total_questions_addressed": len(alignments),
            "coverage_summary": f"Addresses {len(alignments)} research questions"
        }
    
    def _standardize_stage2_result_with_research_questions(self, response_data: Dict, llm_result: Dict, research_questions: List[str]) -> Dict:
        """Standardize Stage 2 result with research question alignment"""
        
        # Extract basic fields
        sentiment = llm_result.get('sentiment', 'neutral').lower()
        impact_score = llm_result.get('impact_score', 3)
        reasoning = llm_result.get('reasoning', '')
        
        # Validate sentiment
        valid_sentiments = ['positive', 'negative', 'neutral', 'mixed']
        if sentiment not in valid_sentiments:
            sentiment = 'neutral'
        
        # Validate impact score
        try:
            impact_score = int(impact_score)
            impact_score = max(1, min(5, impact_score))
        except:
            impact_score = 3
        
        # Process research question alignment
        alignments = llm_result.get('research_question_alignment', [])
        total_questions_addressed = llm_result.get('total_questions_addressed', len(alignments))
        coverage_summary = llm_result.get('coverage_summary', f"Addresses {len(alignments)} research questions")
        
        # Update research question coverage stats
        for alignment in alignments:
            question_index = alignment.get('question_index', 0)
            if question_index < len(research_questions):
                question_text = research_questions[question_index]
                if question_text not in self.processing_stats['research_question_coverage']:
                    self.processing_stats['research_question_coverage'][question_text] = {
                        'responses_addressed': 0,
                        'total_alignment_score': 0,
                        'high_priority_count': 0
                    }
                
                self.processing_stats['research_question_coverage'][question_text]['responses_addressed'] += 1
                self.processing_stats['research_question_coverage'][question_text]['total_alignment_score'] += alignment.get('alignment_score', 0)
                
                if alignment.get('coverage_priority') == 'high':
                    self.processing_stats['research_question_coverage'][question_text]['high_priority_count'] += 1
        
        return {
            'response_id': response_data.get('response_id'),
            'sentiment': sentiment,
            'impact_score': impact_score,
            'reasoning': reasoning,
            'research_question_alignment': alignments,
            'total_questions_addressed': total_questions_addressed,
            'coverage_summary': coverage_summary,
            'harmonized_subject': response_data.get('harmonized_subject'),
            'client_id': response_data.get('client_id'),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _update_stage2_analysis(self, response_id: str, analysis_result: Dict) -> bool:
        """Update Stage 2 analysis in database"""
        try:
            # Prepare data for database update
            update_data = {
                'sentiment': analysis_result.get('sentiment', 'neutral'),
                'impact_score': analysis_result.get('impact_score', 3),
                'research_question_alignment': json.dumps(analysis_result.get('research_question_alignment', [])),
                'total_questions_addressed': analysis_result.get('total_questions_addressed', 0),
                'coverage_summary': analysis_result.get('coverage_summary', ''),
                'stage2_analysis_timestamp': datetime.now().isoformat()
            }
            
            # Update the response in database
            success = self.db.update_stage2_analysis(response_id, update_data)
            
            if success:
                logger.info(f"✅ Updated Stage 2 analysis for {response_id}")
            else:
                logger.error(f"❌ Failed to update Stage 2 analysis for {response_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Database update failed for {response_id}: {e}")
            return False
    
    def _update_processing_stats(self, analysis_result: Dict, success: bool):
        """Update processing statistics"""
        self.processing_stats['total_processed'] += 1
        
        if success:
            self.processing_stats['successful_analyses'] += 1
            
            # Update sentiment distribution
            sentiment = analysis_result.get('sentiment', 'neutral')
            if sentiment in self.processing_stats['sentiment_distribution']:
                self.processing_stats['sentiment_distribution'][sentiment] += 1
            
            # Update impact distribution
            impact_score = analysis_result.get('impact_score', 3)
            if impact_score in self.processing_stats['impact_distribution']:
                self.processing_stats['impact_distribution'][impact_score] += 1
            
            # Update harmonized subjects
            harmonized_subject = analysis_result.get('harmonized_subject', 'Unknown')
            self.processing_stats['harmonized_subjects_analyzed'].add(harmonized_subject)
        else:
            self.processing_stats['failed_analyses'] += 1
    
    def _create_summary_result(self) -> Dict:
        """Create summary of processing results"""
        return {
            'total_processed': self.processing_stats['total_processed'],
            'successful_analyses': self.processing_stats['successful_analyses'],
            'failed_analyses': self.processing_stats['failed_analyses'],
            'success_rate': (self.processing_stats['successful_analyses'] / max(1, self.processing_stats['total_processed'])) * 100,
            'sentiment_distribution': self.processing_stats['sentiment_distribution'],
            'impact_distribution': self.processing_stats['impact_distribution'],
            'research_question_coverage': self.processing_stats['research_question_coverage'],
            'harmonized_subjects_analyzed': list(self.processing_stats['harmonized_subjects_analyzed']),
            'timestamp': datetime.now().isoformat()
        }

def main():
    """Test the enhanced Stage 2 processor"""
    if len(sys.argv) < 2:
        print("Usage: python enhanced_stage2_with_research_questions.py <client_id>")
        sys.exit(1)
    
    client_id = sys.argv[1]
    
    try:
        processor = EnhancedStage2WithResearchQuestions()
        result = processor.process_incremental(client_id)
        
        print("✅ Enhanced Stage 2 analysis complete!")
        print(f"📊 Processed: {result['total_processed']}")
        print(f"✅ Successful: {result['successful_analyses']}")
        print(f"❌ Failed: {result['failed_analyses']}")
        print(f"📈 Success Rate: {result['success_rate']:.1f}%")
        
        # Print research question coverage
        print("\n📋 Research Question Coverage:")
        for question, coverage in result['research_question_coverage'].items():
            print(f"  • {question[:50]}...")
            print(f"    Responses: {coverage['responses_addressed']}")
            print(f"    Avg Alignment: {coverage['total_alignment_score'] / max(1, coverage['responses_addressed']):.1f}/5.0")
            print(f"    High Priority: {coverage['high_priority_count']}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 