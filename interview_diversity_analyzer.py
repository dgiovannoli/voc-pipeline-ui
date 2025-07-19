#!/usr/bin/env python3
"""
Interview Diversity Analyzer
Addresses the risk of over-valuing individual quotes vs. interview diversity
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from redesigned_stage2_analyzer import RedesignedStage2Analyzer
from supabase_database import SupabaseDatabase

class InterviewDiversityAnalyzer:
    """
    Analyzer that accounts for interview diversity and prevents over-valuation
    of individual quotes while ensuring comprehensive coverage across interviews.
    """
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.db = SupabaseDatabase()
        self.stage2_analyzer = RedesignedStage2Analyzer(client_id, batch_size=10, max_workers=2)
        
        # Interview diversity weights
        self.diversity_weights = {
            'interview_coverage': 0.4,  # Weight for covering different interviews
            'criteria_coverage': 0.3,   # Weight for covering different criteria
            'sentiment_balance': 0.2,   # Weight for balanced sentiment distribution
            'confidence_quality': 0.1   # Weight for high-confidence insights
        }
        
        # Minimum thresholds for meaningful analysis
        self.min_thresholds = {
            'min_interviews_per_criterion': 2,  # Need at least 2 interviews mentioning each criterion
            'min_quotes_per_interview': 3,      # Need at least 3 quotes per interview for diversity
            'max_quotes_per_criterion_per_interview': 3,  # Limit quotes per criterion per interview
            'min_sentiment_diversity': 0.3      # At least 30% sentiment diversity
        }
    
    def analyze_with_diversity_focus(self) -> Dict[str, Any]:
        """Analyze quotes with focus on interview diversity rather than individual quote value"""
        
        print("🎯 INTERVIEW DIVERSITY ANALYSIS")
        print("=" * 50)
        
        # Get all quotes with interview metadata
        quotes_df = self.db.get_stage1_quotes(self.client_id)
        if quotes_df.empty:
            return {"error": "No quotes found"}
        
        # Group by interview to understand diversity
        interview_groups = self._group_quotes_by_interview(quotes_df)
        
        print(f"📊 Interview Analysis:")
        print(f"   Total interviews: {len(interview_groups)}")
        print(f"   Total quotes: {len(quotes_df)}")
        
        # Analyze interview diversity
        diversity_analysis = self._analyze_interview_diversity(interview_groups)
        
        # Select quotes for analysis based on diversity principles
        selected_quotes = self._select_quotes_for_diversity(interview_groups, diversity_analysis)
        
        print(f"\n📋 Quote Selection for Diversity:")
        print(f"   Original quotes: {len(quotes_df)}")
        print(f"   Selected quotes: {len(selected_quotes)}")
        print(f"   Selection rate: {len(selected_quotes)/len(quotes_df)*100:.1f}%")
        
        # Process selected quotes with diversity-aware analysis
        results = self._process_diversity_aware_analysis(selected_quotes, interview_groups)
        
        return results
    
    def _group_quotes_by_interview(self, quotes_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Group quotes by interview ID"""
        interview_groups = {}
        
        for _, quote in quotes_df.iterrows():
            interview_id = quote.get('interview_id', 'unknown')
            if interview_id not in interview_groups:
                interview_groups[interview_id] = []
            interview_groups[interview_id].append(quote)
        
        # Convert to DataFrames
        return {interview_id: pd.DataFrame(quotes) for interview_id, quotes in interview_groups.items()}
    
    def _analyze_interview_diversity(self, interview_groups: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Analyze the diversity across interviews"""
        
        diversity_metrics = {
            'interview_coverage': {},
            'criteria_coverage': {},
            'sentiment_distribution': {},
            'quote_distribution': {}
        }
        
        # Analyze each interview
        for interview_id, quotes_df in interview_groups.items():
            interview_metrics = {
                'quote_count': len(quotes_df),
                'unique_companies': quotes_df['company'].nunique(),
                'unique_interviewees': quotes_df['interviewee_name'].nunique(),
                'quote_lengths': quotes_df['verbatim_response'].str.len().describe(),
                'has_positive_feedback': any('love' in q.lower() or 'excellent' in q.lower() 
                                           for q in quotes_df['verbatim_response']),
                'has_negative_feedback': any('hate' in q.lower() or 'terrible' in q.lower() 
                                           for q in quotes_df['verbatim_response']),
                'has_neutral_feedback': True  # Assume neutral if no strong sentiment
            }
            
            diversity_metrics['interview_coverage'][interview_id] = interview_metrics
        
        # Calculate overall diversity scores
        total_interviews = len(interview_groups)
        total_quotes = sum(len(quotes) for quotes in interview_groups.values())
        
        diversity_metrics['overall'] = {
            'total_interviews': total_interviews,
            'total_quotes': total_quotes,
            'avg_quotes_per_interview': total_quotes / total_interviews if total_interviews > 0 else 0,
            'interview_diversity_score': self._calculate_interview_diversity_score(interview_groups),
            'criteria_diversity_score': self._calculate_criteria_diversity_score(interview_groups),
            'sentiment_diversity_score': self._calculate_sentiment_diversity_score(interview_groups)
        }
        
        return diversity_metrics
    
    def _calculate_interview_diversity_score(self, interview_groups: Dict[str, pd.DataFrame]) -> float:
        """Calculate how diverse the interviews are"""
        
        if not interview_groups:
            return 0.0
        
        # Factors that increase diversity:
        # 1. More interviews (up to a point)
        # 2. Different companies
        # 3. Different interviewee roles
        # 4. Balanced quote distribution
        
        total_interviews = len(interview_groups)
        all_companies = set()
        all_interviewees = set()
        quote_counts = []
        
        for interview_id, quotes_df in interview_groups.items():
            all_companies.update(quotes_df['company'].dropna())
            all_interviewees.update(quotes_df['interviewee_name'].dropna())
            quote_counts.append(len(quotes_df))
        
        # Calculate diversity components
        company_diversity = min(1.0, len(all_companies) / total_interviews) if total_interviews > 0 else 0
        interviewee_diversity = min(1.0, len(all_interviewees) / total_interviews) if total_interviews > 0 else 0
        
        # Quote distribution balance (prefer more balanced distribution)
        if quote_counts:
            quote_std = np.std(quote_counts)
            quote_mean = np.mean(quote_counts)
            quote_balance = 1.0 / (1.0 + quote_std / quote_mean) if quote_mean > 0 else 0
        else:
            quote_balance = 0
        
        # Overall diversity score
        diversity_score = (company_diversity * 0.4 + 
                          interviewee_diversity * 0.4 + 
                          quote_balance * 0.2)
        
        return diversity_score
    
    def _calculate_criteria_diversity_score(self, interview_groups: Dict[str, pd.DataFrame]) -> float:
        """Calculate how diverse the criteria coverage is across interviews"""
        
        # This would be calculated after Stage 2 analysis
        # For now, return a placeholder
        return 0.5
    
    def _calculate_sentiment_diversity_score(self, interview_groups: Dict[str, pd.DataFrame]) -> float:
        """Calculate sentiment diversity across interviews"""
        
        all_sentiments = []
        
        for interview_id, quotes_df in interview_groups.items():
            for _, quote in quotes_df.iterrows():
                text = quote['verbatim_response'].lower()
                
                # Simple sentiment detection
                if any(word in text for word in ['love', 'excellent', 'amazing', 'outstanding', 'perfect']):
                    all_sentiments.append('positive')
                elif any(word in text for word in ['hate', 'terrible', 'awful', 'horrible', 'worst']):
                    all_sentiments.append('negative')
                else:
                    all_sentiments.append('neutral')
        
        if not all_sentiments:
            return 0.0
        
        # Calculate sentiment diversity
        sentiment_counts = pd.Series(all_sentiments).value_counts()
        total_sentiments = len(all_sentiments)
        
        # Diversity is higher when sentiments are more evenly distributed
        sentiment_proportions = sentiment_counts / total_sentiments
        diversity_score = 1.0 - sentiment_proportions.max()  # Lower max proportion = higher diversity
        
        return diversity_score
    
    def _select_quotes_for_diversity(self, interview_groups: Dict[str, pd.DataFrame], 
                                   diversity_analysis: Dict[str, Any]) -> List[Dict]:
        """Select quotes that maximize interview diversity"""
        
        selected_quotes = []
        
        for interview_id, quotes_df in interview_groups.items():
            interview_metrics = diversity_analysis['interview_coverage'].get(interview_id, {})
            quote_count = interview_metrics.get('quote_count', 0)
            
            # Apply diversity-based selection rules
            if quote_count >= self.min_thresholds['min_quotes_per_interview']:
                # Select quotes strategically to maximize diversity
                selected_for_interview = self._select_quotes_from_interview(quotes_df, interview_id)
                selected_quotes.extend(selected_for_interview)
            else:
                # Include all quotes from interviews with few quotes to ensure coverage
                selected_quotes.extend(quotes_df.to_dict('records'))
        
        return selected_quotes
    
    def _select_quotes_from_interview(self, quotes_df: pd.DataFrame, interview_id: str) -> List[Dict]:
        """Select quotes from a single interview to maximize diversity"""
        
        selected = []
        quotes_list = quotes_df.to_dict('records')
        
        # Sort quotes by potential diversity value
        scored_quotes = []
        for quote in quotes_list:
            diversity_score = self._calculate_quote_diversity_value(quote, quotes_list)
            scored_quotes.append((diversity_score, quote))
        
        # Sort by diversity score (highest first)
        scored_quotes.sort(key=lambda x: x[0], reverse=True)
        
        # Select top quotes, but limit per interview to ensure diversity across interviews
        max_quotes_per_interview = min(10, len(scored_quotes))  # Cap at 10 quotes per interview
        
        for score, quote in scored_quotes[:max_quotes_per_interview]:
            selected.append(quote)
        
        return selected
    
    def _calculate_quote_diversity_value(self, quote: Dict, all_quotes: List[Dict]) -> float:
        """Calculate the diversity value of a quote within its interview context"""
        
        text = quote.get('verbatim_response', '').lower()
        
        # Factors that increase diversity value:
        diversity_score = 0.0
        
        # 1. Unique sentiment (different from other quotes in interview)
        sentiment = self._detect_sentiment(text)
        other_sentiments = [self._detect_sentiment(q.get('verbatim_response', '').lower()) 
                           for q in all_quotes if q != quote]
        
        if sentiment not in other_sentiments:
            diversity_score += 0.3  # Unique sentiment adds value
        
        # 2. Specific criteria mentioned (vs generic feedback)
        criteria_keywords = {
            'product_capability': ['accuracy', 'feature', 'performance', 'capability'],
            'customer_support_experience': ['support', 'help', 'service', 'response'],
            'commercial_terms': ['price', 'cost', 'contract', 'roi', 'value'],
            'implementation_onboarding': ['setup', 'implementation', 'training', 'onboarding'],
            'speed_responsiveness': ['speed', 'fast', 'slow', 'timeline', 'response']
        }
        
        criteria_mentioned = []
        for criterion, keywords in criteria_keywords.items():
            if any(keyword in text for keyword in keywords):
                criteria_mentioned.append(criterion)
        
        # More specific criteria = higher diversity value
        diversity_score += len(criteria_mentioned) * 0.1
        
        # 3. Quote length and detail (more detailed = more valuable)
        word_count = len(text.split())
        if word_count > 20:
            diversity_score += 0.2
        elif word_count > 10:
            diversity_score += 0.1
        
        # 4. Competitive language (mentions competitors, comparisons)
        competitive_indicators = ['compared', 'versus', 'instead', 'competitor', 'alternative']
        if any(indicator in text for indicator in competitive_indicators):
            diversity_score += 0.3
        
        # 5. Business impact language
        impact_indicators = ['deal', 'win', 'loss', 'revenue', 'cost', 'budget', 'roi']
        if any(indicator in text for indicator in impact_indicators):
            diversity_score += 0.2
        
        return diversity_score
    
    def _detect_sentiment(self, text: str) -> str:
        """Simple sentiment detection for diversity calculation"""
        
        positive_words = ['love', 'excellent', 'amazing', 'outstanding', 'perfect', 'great', 'good']
        negative_words = ['hate', 'terrible', 'awful', 'horrible', 'worst', 'bad', 'poor']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _process_diversity_aware_analysis(self, selected_quotes: List[Dict], 
                                        interview_groups: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Process quotes with diversity-aware analysis"""
        
        print(f"\n🔄 Processing {len(selected_quotes)} diversity-selected quotes...")
        
        # Process quotes with the redesigned analyzer
        results = []
        for quote in selected_quotes:
            try:
                result = self.stage2_analyzer._analyze_quote_enhanced(
                    quote['quote_id'],
                    quote['verbatim_response'],
                    quote.get('company', ''),
                    quote.get('interviewee_name', '')
                )
                
                if result.get('analysis_success', False):
                    # Add interview diversity metadata
                    result['diversity_metadata'] = {
                        'interview_id': quote.get('interview_id'),
                        'company': quote.get('company'),
                        'interviewee_name': quote.get('interviewee_name'),
                        'diversity_score': self._calculate_quote_diversity_value(quote, selected_quotes),
                        'interview_quote_count': len(interview_groups.get(quote.get('interview_id', ''), []))
                    }
                
                results.append(result)
                
            except Exception as e:
                print(f"❌ Error processing quote {quote.get('quote_id')}: {str(e)}")
                results.append({
                    'quote_id': quote.get('quote_id'),
                    'analysis_success': False,
                    'error': str(e)
                })
        
        # Apply diversity-based weighting to results
        weighted_results = self._apply_diversity_weighting(results, interview_groups)
        
        # Save results with diversity awareness
        self._save_diversity_aware_results(weighted_results)
        
        return {
            'total_quotes_processed': len(results),
            'successful_analyses': len([r for r in results if r.get('analysis_success', False)]),
            'diversity_metrics': self._calculate_final_diversity_metrics(results, interview_groups),
            'weighted_results': weighted_results
        }
    
    def _apply_diversity_weighting(self, results: List[Dict], 
                                 interview_groups: Dict[str, pd.DataFrame]) -> List[Dict]:
        """Apply diversity-based weighting to analysis results"""
        
        weighted_results = []
        
        for result in results:
            if not result.get('analysis_success', False):
                weighted_results.append(result)
                continue
            
            diversity_metadata = result.get('diversity_metadata', {})
            interview_id = diversity_metadata.get('interview_id')
            
            # Calculate diversity weight
            diversity_weight = self._calculate_diversity_weight(result, interview_groups)
            
            # Apply weight to relevance scores
            analysis_data = result.get('analysis_data', {})
            criteria_eval = analysis_data.get('criteria_evaluation', {})
            
            for criterion, eval_data in criteria_eval.items():
                if isinstance(eval_data, dict):
                    # Adjust relevance score based on diversity
                    original_score = eval_data.get('relevance_score', 0)
                    adjusted_score = original_score * diversity_weight
                    
                    # Cap the adjustment to prevent extreme values
                    adjusted_score = min(5.0, adjusted_score)
                    
                    eval_data['relevance_score'] = round(adjusted_score, 2)
                    eval_data['diversity_weight'] = diversity_weight
                    eval_data['original_relevance_score'] = original_score
            
            weighted_results.append(result)
        
        return weighted_results
    
    def _calculate_diversity_weight(self, result: Dict, 
                                  interview_groups: Dict[str, pd.DataFrame]) -> float:
        """Calculate diversity weight for a result"""
        
        diversity_metadata = result.get('diversity_metadata', {})
        interview_id = diversity_metadata.get('interview_id')
        
        if not interview_id or interview_id not in interview_groups:
            return 1.0  # Default weight
        
        # Factors that increase diversity weight:
        weight = 1.0
        
        # 1. Interview coverage (fewer quotes from this interview = higher weight)
        interview_quote_count = len(interview_groups[interview_id])
        total_interviews = len(interview_groups)
        
        if total_interviews > 0:
            # Interviews with fewer quotes get higher weight
            coverage_weight = 1.0 + (1.0 / interview_quote_count) * 0.5
            weight *= coverage_weight
        
        # 2. Company diversity (unique companies get higher weight)
        all_companies = set()
        for quotes_df in interview_groups.values():
            all_companies.update(quotes_df['company'].dropna())
        
        company_count = len(all_companies)
        if company_count > 0:
            # More companies = higher weight for each quote
            company_weight = 1.0 + (company_count / total_interviews) * 0.3
            weight *= company_weight
        
        # 3. Quote diversity score
        diversity_score = diversity_metadata.get('diversity_score', 0)
        diversity_weight = 1.0 + diversity_score * 0.5
        weight *= diversity_weight
        
        return min(2.0, weight)  # Cap at 2.0x weight
    
    def _save_diversity_aware_results(self, weighted_results: List[Dict]):
        """Save results with diversity awareness"""
        
        print(f"💾 Saving diversity-aware results...")
        
        for result in weighted_results:
            if not result.get('analysis_success', False):
                continue
            
            analysis_data = result.get('analysis_data', {})
            criteria_eval = analysis_data.get('criteria_evaluation', {})
            diversity_metadata = result.get('diversity_metadata', {})
            
            for criterion, eval_data in criteria_eval.items():
                if isinstance(eval_data, dict) and eval_data.get('relevance_score', 0) > 0:
                    
                    # Create database record with diversity metadata
                    db_record = {
                        'quote_id': result['quote_id'],
                        'client_id': self.client_id,
                        'criterion': criterion,
                        'relevance_score': eval_data.get('relevance_score', 0),
                        'sentiment': eval_data.get('sentiment', 'neutral'),
                        'priority': eval_data.get('deal_impact', 'minor'),
                        'confidence': eval_data.get('confidence', 'medium'),
                        'relevance_explanation': eval_data.get('explanation', ''),
                        'analysis_timestamp': result.get('analysis_timestamp'),
                        'analysis_version': '2.0_diversity_aware',
                        'processing_metadata': {
                            'overall_sentiment': analysis_data.get('quote_analysis', {}).get('overall_sentiment'),
                            'competitive_insight': analysis_data.get('quote_analysis', {}).get('competitive_insight'),
                            'high_confidence': eval_data.get('confidence') == 'high',
                            'diversity_weight': eval_data.get('diversity_weight', 1.0),
                            'original_relevance_score': eval_data.get('original_relevance_score', 0),
                            'interview_id': diversity_metadata.get('interview_id'),
                            'company': diversity_metadata.get('company'),
                            'interviewee_name': diversity_metadata.get('interviewee_name')
                        }
                    }
                    
                    try:
                        self.db.supabase.table('stage2_response_labeling').insert(db_record).execute()
                    except Exception as e:
                        print(f"❌ Failed to save record: {str(e)}")
    
    def _calculate_final_diversity_metrics(self, results: List[Dict], 
                                         interview_groups: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate final diversity metrics"""
        
        successful_results = [r for r in results if r.get('analysis_success', False)]
        
        if not successful_results:
            return {"error": "No successful analyses"}
        
        # Calculate diversity metrics
        interview_ids = set()
        companies = set()
        criteria_covered = set()
        sentiments = []
        
        for result in successful_results:
            diversity_metadata = result.get('diversity_metadata', {})
            interview_ids.add(diversity_metadata.get('interview_id'))
            companies.add(diversity_metadata.get('company'))
            
            analysis_data = result.get('analysis_data', {})
            criteria_eval = analysis_data.get('criteria_evaluation', {})
            
            for criterion, eval_data in criteria_eval.items():
                if isinstance(eval_data, dict) and eval_data.get('relevance_score', 0) > 0:
                    criteria_covered.add(criterion)
                    sentiments.append(eval_data.get('sentiment', 'neutral'))
        
        return {
            'interview_coverage': len(interview_ids),
            'company_coverage': len(companies),
            'criteria_coverage': len(criteria_covered),
            'sentiment_diversity': len(set(sentiments)),
            'total_interviews_available': len(interview_groups),
            'coverage_percentage': len(interview_ids) / len(interview_groups) * 100 if interview_groups else 0
        }

def run_diversity_aware_analysis(client_id: str = "Rev"):
    """Run diversity-aware analysis"""
    analyzer = InterviewDiversityAnalyzer(client_id)
    return analyzer.analyze_with_diversity_focus()

if __name__ == "__main__":
    results = run_diversity_aware_analysis()
    print(json.dumps(results, indent=2)) 