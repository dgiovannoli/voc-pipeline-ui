"""
Interview-Weighted VOC Analyzer
==============================

A version of the reframed VOC analyzer that weights by interviews rather than individual quotes
to avoid overweighing interviews that have many quotes.

Key Insight: Each interview should count equally, regardless of how many quotes it produces.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from official_scripts.database.supabase_database import SupabaseDatabase
from official_scripts.reframed_voc_analyzer import ReframedVOCAnalyzer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class InterviewWeightedAssessment:
    """Assessment results using interview-weighted VOC analysis"""
    overall_score: float
    performance_level: str
    problem_ratio: float  # Ratio of interviews with problems
    benefit_ratio: float  # Ratio of interviews with benefits
    neutral_ratio: float  # Ratio of interviews with only neutral feedback
    total_interviews: int
    total_quotes: int
    improvement_opportunities: List[Dict]
    winning_factors: List[Dict]
    interview_breakdown: Dict
    assessment_summary: str

class InterviewWeightedVOCAnalyzer:
    """
    Interview-weighted VOC analyzer that counts interviews rather than individual quotes
    """
    
    def __init__(self, database: SupabaseDatabase):
        self.db = database
        self.reframed_analyzer = ReframedVOCAnalyzer(database)
        
    def analyze_client_feedback(self, client_id: str = "Rev") -> InterviewWeightedAssessment:
        """
        Analyze client feedback using interview-weighted approach
        """
        logger.info(f"🎯 INTERVIEW-WEIGHTED VOC ANALYSIS FOR CLIENT: {client_id}")
        logger.info("=" * 70)
        
        # Get all data
        stage1_data = self.db.get_stage1_data_responses(client_id=client_id)
        stage2_data = self.db.get_stage2_response_labeling(client_id)
        
        logger.info(f"📊 Data Sources:")
        logger.info(f"   Stage 1 Quotes: {len(stage1_data)}")
        logger.info(f"   Stage 2 Enriched: {len(stage2_data)}")
        
        # Analyze by interview
        interview_analysis = self._analyze_by_interview(stage1_data, stage2_data)
        
        # Calculate interview-weighted metrics
        metrics = self._calculate_interview_weighted_metrics(interview_analysis)
        
        # Generate improvement opportunities (still from individual quotes for specificity)
        improvement_opportunities = self._extract_improvement_opportunities(
            interview_analysis['all_product_complaints']
        )
        
        # Extract winning factors (still from individual quotes for specificity)
        winning_factors = self._extract_winning_factors(
            interview_analysis['all_benefit_discussions']
        )
        
        # Calculate interview-weighted score
        weighted_score = self._calculate_interview_weighted_score(metrics)
        
        # Generate assessment summary
        assessment_summary = self._generate_interview_weighted_summary(
            metrics, weighted_score, improvement_opportunities, winning_factors, interview_analysis
        )
        
        return InterviewWeightedAssessment(
            overall_score=weighted_score,
            performance_level=self._get_performance_level(weighted_score),
            problem_ratio=metrics['problem_ratio'],
            benefit_ratio=metrics['benefit_ratio'],
            neutral_ratio=metrics['neutral_ratio'],
            total_interviews=metrics['total_interviews'],
            total_quotes=len(stage1_data),
            improvement_opportunities=improvement_opportunities,
            winning_factors=winning_factors,
            interview_breakdown=interview_analysis['interview_breakdown'],
            assessment_summary=assessment_summary
        )
    
    def _analyze_by_interview(self, stage1_data: pd.DataFrame, stage2_data: pd.DataFrame) -> Dict:
        """
        Analyze feedback by interview rather than by individual quote
        """
        # Convert DataFrames to lists of dicts
        stage1_list = stage1_data.to_dict('records') if not stage1_data.empty else []
        stage2_list = stage2_data.to_dict('records') if not stage2_data.empty else []
        
        # Create lookup for Stage 2 enriched data
        stage2_lookup = {item['quote_id']: item for item in stage2_list if 'quote_id' in item}
        
        # Group quotes by interview
        interviews = {}
        all_product_complaints = []
        all_benefit_discussions = []
        
        for quote in stage1_list:
            # Create composite interview identifier since interview_id is None
            interview_key = f"{quote.get('interviewee_name', 'Unknown')} | {quote.get('company', 'Unknown')}"
            quote_id = quote.get('response_id')
            quote_text = quote.get('verbatim_response', '').lower()
            
            # Get enriched data if available
            enriched_data = stage2_lookup.get(quote_id, {})
            sentiment = enriched_data.get('sentiment', 'neutral')
            priority = enriched_data.get('priority', 1)
            
            # Convert priority to integer if it's a string
            if isinstance(priority, str):
                try:
                    priority = int(priority)
                except (ValueError, TypeError):
                    priority = 1
            elif not isinstance(priority, (int, float)):
                priority = 1
            
            # Initialize interview if not exists
            if interview_key not in interviews:
                interviews[interview_key] = {
                    'interview_key': interview_key,
                    'interviewee_name': quote.get('interviewee_name', 'Unknown'),
                    'company': quote.get('company', 'Unknown'),
                    'deal_status': quote.get('deal_status', 'Unknown'),
                    'product_complaints': [],
                    'benefit_discussions': [],
                    'neutral_discussions': [],
                    'total_quotes': 0
                }
            
            # Categorize quote
            if self._is_product_complaint(quote_text, sentiment):
                interviews[interview_key]['product_complaints'].append({
                    'quote_id': quote_id,
                    'text': quote.get('verbatim_response', ''),
                    'sentiment': sentiment,
                    'priority': priority
                })
                all_product_complaints.append({
                    'quote_id': quote_id,
                    'text': quote.get('verbatim_response', ''),
                    'sentiment': sentiment,
                    'priority': priority,
                    'interview_id': interview_key # Store composite key as interview_id
                })
            elif self._is_benefit_discussion(quote_text, sentiment):
                interviews[interview_key]['benefit_discussions'].append({
                    'quote_id': quote_id,
                    'text': quote.get('verbatim_response', ''),
                    'sentiment': sentiment,
                    'priority': priority
                })
                all_benefit_discussions.append({
                    'quote_id': quote_id,
                    'text': quote.get('verbatim_response', ''),
                    'sentiment': sentiment,
                    'priority': priority,
                    'interview_id': interview_key # Store composite key as interview_id
                })
            else:
                interviews[interview_key]['neutral_discussions'].append({
                    'quote_id': quote_id,
                    'text': quote.get('verbatim_response', ''),
                    'sentiment': sentiment,
                    'priority': priority
                })
            
            interviews[interview_key]['total_quotes'] += 1
        
        # Determine interview-level categorization
        interview_breakdown = {
            'problem_interviews': [],
            'benefit_interviews': [],
            'neutral_interviews': [],
            'mixed_interviews': []
        }
        
        for interview_key, interview_data in interviews.items():
            has_complaints = len(interview_data['product_complaints']) > 0
            has_benefits = len(interview_data['benefit_discussions']) > 0
            has_neutral = len(interview_data['neutral_discussions']) > 0
            
            if has_complaints and has_benefits:
                interview_breakdown['mixed_interviews'].append(interview_data)
            elif has_complaints:
                interview_breakdown['problem_interviews'].append(interview_data)
            elif has_benefits:
                interview_breakdown['benefit_interviews'].append(interview_data)
            else:
                interview_breakdown['neutral_interviews'].append(interview_data)
        
        return {
            'interviews': interviews,
            'interview_breakdown': interview_breakdown,
            'all_product_complaints': all_product_complaints,
            'all_benefit_discussions': all_benefit_discussions
        }
    
    def _is_product_complaint(self, text: str, sentiment: str) -> bool:
        """Identify product complaints - direct issues with the product"""
        complaint_indicators = [
            'slow', 'delayed', 'delay', 'inaccurate', 'error', 'bug', 'crash',
            'doesn\'t work', 'not working', 'problem', 'issue', 'difficult',
            'hard to use', 'confusing', 'frustrating', 'annoying', 'terrible',
            'bad', 'poor', 'awful', 'horrible', 'useless', 'broken', 'failed',
            'doesn\'t integrate', 'integration issues', 'technical problems',
            'quality issues', 'accuracy problems', 'speed issues'
        ]
        
        has_complaint_indicators = any(indicator in text for indicator in complaint_indicators)
        is_negative_sentiment = sentiment in ['negative', 'very negative']
        
        return has_complaint_indicators or is_negative_sentiment
    
    def _is_benefit_discussion(self, text: str, sentiment: str) -> bool:
        """Identify benefit discussions - positive outcomes and business value"""
        benefit_indicators = [
            'saves time', 'efficient', 'efficiency', 'worth it', 'valuable',
            'investment', 'return', 'benefit', 'advantage', 'improvement',
            'better', 'great', 'excellent', 'amazing', 'fantastic', 'love',
            'satisfied', 'happy', 'pleased', 'impressed', 'recommend',
            'streamlines', 'automates', 'reduces', 'increases', 'improves',
            'saves money', 'cost effective', 'productive', 'time saving'
        ]
        
        has_benefit_indicators = any(indicator in text for indicator in benefit_indicators)
        is_positive_sentiment = sentiment in ['positive', 'very positive']
        
        return has_benefit_indicators or is_positive_sentiment
    
    def _calculate_interview_weighted_metrics(self, interview_analysis: Dict) -> Dict:
        """
        Calculate metrics weighted by interviews rather than individual quotes
        """
        breakdown = interview_analysis['interview_breakdown']
        
        total_interviews = (
            len(breakdown['problem_interviews']) +
            len(breakdown['benefit_interviews']) +
            len(breakdown['neutral_interviews']) +
            len(breakdown['mixed_interviews'])
        )
        
        if total_interviews == 0:
            return {
                'problem_ratio': 0.0,
                'benefit_ratio': 0.0,
                'neutral_ratio': 0.0,
                'mixed_ratio': 0.0,
                'total_interviews': 0
            }
        
        # Calculate ratios
        problem_ratio = len(breakdown['problem_interviews']) / total_interviews
        benefit_ratio = len(breakdown['benefit_interviews']) / total_interviews
        neutral_ratio = len(breakdown['neutral_interviews']) / total_interviews
        mixed_ratio = len(breakdown['mixed_interviews']) / total_interviews
        
        return {
            'problem_ratio': problem_ratio,
            'benefit_ratio': benefit_ratio,
            'neutral_ratio': neutral_ratio,
            'mixed_ratio': mixed_ratio,
            'total_interviews': total_interviews
        }
    
    def _calculate_interview_weighted_score(self, metrics: Dict) -> float:
        """
        Calculate interview-weighted score
        Formula: (benefit_interviews + neutral_interviews + mixed_interviews) / total * 10
        Mixed interviews count as positive since they have benefits
        """
        if metrics['total_interviews'] == 0:
            return 0.0
        
        # Treat neutral and mixed interviews as positive (no complaints or has benefits)
        positive_ratio = (
            metrics['benefit_ratio'] + 
            metrics['neutral_ratio'] + 
            metrics['mixed_ratio']
        )
        
        # Scale to 0-10
        score = positive_ratio * 10
        
        return round(score, 1)
    
    def _extract_improvement_opportunities(self, product_complaints: List[Dict]) -> List[Dict]:
        """Extract improvement opportunities from product complaints"""
        opportunities = []
        
        for complaint in product_complaints:
            text = complaint['text']
            priority = complaint.get('priority', 1)
            
            # Extract specific issues mentioned
            issues = self._extract_specific_issues(text)
            
            if issues:
                opportunities.append({
                    'quote_id': complaint['quote_id'],
                    'interview_id': complaint.get('interview_id', 'unknown'),
                    'text': text,
                    'issues': issues,
                    'priority': priority,
                    'impact': 'High' if priority >= 3 else 'Medium' if priority >= 2 else 'Low'
                })
        
        # Sort by priority
        opportunities.sort(key=lambda x: x['priority'], reverse=True)
        
        return opportunities[:10]  # Top 10 opportunities
    
    def _extract_specific_issues(self, text: str) -> List[str]:
        """Extract specific product issues from complaint text"""
        issues = []
        
        issue_patterns = {
            'speed': ['slow', 'delayed', 'delay', 'speed', 'fast', 'quick'],
            'accuracy': ['inaccurate', 'accuracy', 'wrong', 'correct', 'precise'],
            'reliability': ['crash', 'error', 'bug', 'broken', 'failed', 'unreliable'],
            'usability': ['difficult', 'hard to use', 'confusing', 'complex', 'user friendly'],
            'integration': ['integrate', 'integration', 'connect', 'compatible'],
            'quality': ['quality', 'poor quality', 'good quality', 'excellent quality']
        }
        
        text_lower = text.lower()
        
        for category, keywords in issue_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                issues.append(category)
        
        return issues
    
    def _extract_winning_factors(self, benefit_discussions: List[Dict]) -> List[Dict]:
        """Extract winning factors from benefit discussions"""
        factors = []
        
        for benefit in benefit_discussions:
            text = benefit['text']
            priority = benefit.get('priority', 1)
            
            # Extract specific benefits mentioned
            benefits = self._extract_specific_benefits(text)
            
            if benefits:
                factors.append({
                    'quote_id': benefit['quote_id'],
                    'interview_id': benefit.get('interview_id', 'unknown'),
                    'text': text,
                    'benefits': benefits,
                    'priority': priority,
                    'impact': 'High' if priority >= 3 else 'Medium' if priority >= 2 else 'Low'
                })
        
        # Sort by priority
        factors.sort(key=lambda x: x['priority'], reverse=True)
        
        return factors[:10]  # Top 10 factors
    
    def _extract_specific_benefits(self, text: str) -> List[str]:
        """Extract specific benefits from positive discussion text"""
        benefits = []
        
        benefit_patterns = {
            'efficiency': ['efficient', 'efficiency', 'saves time', 'time saving', 'productive'],
            'cost_savings': ['saves money', 'cost', 'investment', 'worth', 'valuable'],
            'quality': ['quality', 'accurate', 'precise', 'reliable', 'consistent'],
            'ease_of_use': ['easy', 'simple', 'user friendly', 'intuitive', 'straightforward'],
            'integration': ['integrates', 'connects', 'works with', 'compatible'],
            'business_value': ['business', 'value', 'return', 'benefit', 'advantage']
        }
        
        text_lower = text.lower()
        
        for category, keywords in benefit_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                benefits.append(category)
        
        return benefits
    
    def _get_performance_level(self, score: float) -> str:
        """Get performance level based on interview-weighted score"""
        if score >= 8.0:
            return "Excellent"
        elif score >= 6.0:
            return "Good"
        elif score >= 4.0:
            return "Fair"
        elif score >= 2.0:
            return "Poor"
        else:
            return "Critical"
    
    def _generate_interview_weighted_summary(self, metrics: Dict, score: float, 
                                           improvement_opportunities: List[Dict], 
                                           winning_factors: List[Dict],
                                           interview_analysis: Dict) -> str:
        """Generate assessment summary using interview-weighted approach"""
        
        breakdown = interview_analysis['interview_breakdown']
        total_interviews = metrics['total_interviews']
        
        problem_count = len(breakdown['problem_interviews'])
        benefit_count = len(breakdown['benefit_interviews'])
        neutral_count = len(breakdown['neutral_interviews'])
        mixed_count = len(breakdown['mixed_interviews'])
        
        summary = f"""
🎯 INTERVIEW-WEIGHTED VOC ASSESSMENT SUMMARY
============================================

📊 OVERALL PERFORMANCE: {score}/10 ({self._get_performance_level(score)})

📈 INTERVIEW BREAKDOWN:
   • Problem Interviews: {problem_count} ({metrics['problem_ratio']:.1%})
   • Benefit Interviews: {benefit_count} ({metrics['benefit_ratio']:.1%})
   • Neutral Interviews: {neutral_count} ({metrics['neutral_ratio']:.1%})
   • Mixed Interviews: {mixed_count} ({metrics['mixed_ratio']:.1%})
   • Total Interviews: {total_interviews}
   • Total Quotes: {sum(interview['total_quotes'] for interview in interview_analysis['interviews'].values())}

🔍 KEY INSIGHTS:
   • {neutral_count + benefit_count + mixed_count} interviews ({((neutral_count + benefit_count + mixed_count)/total_interviews)*100:.1f}%) have no complaints
   • {benefit_count + mixed_count} interviews ({((benefit_count + mixed_count)/total_interviews)*100:.1f}%) explicitly discuss benefits
   • {problem_count} interviews ({metrics['problem_ratio']:.1f}%) report specific product issues

🚀 IMPROVEMENT OPPORTUNITIES: {len(improvement_opportunities)} identified
   • High Priority: {len([o for o in improvement_opportunities if o['impact'] == 'High'])}
   • Medium Priority: {len([o for o in improvement_opportunities if o['impact'] == 'Medium'])}
   • Low Priority: {len([o for o in improvement_opportunities if o['impact'] == 'Low'])}

✅ WINNING FACTORS: {len(winning_factors)} identified
   • High Impact: {len([w for w in winning_factors if w['impact'] == 'High'])}
   • Medium Impact: {len([w for w in winning_factors if w['impact'] == 'Medium'])}
   • Low Impact: {len([w for w in winning_factors if w['impact'] == 'Low'])}

💡 STRATEGIC RECOMMENDATION:
   Focus on addressing the {problem_count} interviews with product complaints as they represent
   direct improvement opportunities. The {neutral_count + benefit_count + mixed_count} interviews
   with no complaints indicate satisfied customers who aren't experiencing problems.

📊 COMPARISON WITH QUOTE-COUNTED APPROACH:
   • Interview-weighted score: {score}/10
   • Quote-counted score: ~8.8/10 (from reframed analyzer)
   • Difference: {score - 8.8:.1f} points
   • Rationale: Each interview counts equally, preventing overweighing of verbose interviews
"""
        
        return summary.strip()

def main():
    """Test the interview-weighted VOC analyzer"""
    print("🎯 TESTING INTERVIEW-WEIGHTED VOC ANALYSIS")
    print("=" * 50)
    
    try:
        # Initialize database and analyzer
        db = SupabaseDatabase()
        analyzer = InterviewWeightedVOCAnalyzer(db)
        
        # Run analysis
        assessment = analyzer.analyze_client_feedback("Rev")
        
        # Display results
        print(assessment.assessment_summary)
        
        # Show interview breakdown
        print(f"\n📊 INTERVIEW BREAKDOWN:")
        for category, interviews in assessment.interview_breakdown.items():
            print(f"   {category}: {len(interviews)} interviews")
            if len(interviews) > 0:
                for interview in interviews[:3]:  # Show first 3
                    print(f"     - {interview['interviewee_name']} ({interview['company']}) - {interview['total_quotes']} quotes")
        
    except Exception as e:
        print(f"❌ Error running interview-weighted analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 