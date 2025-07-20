"""
Reframed VOC Analyzer
=====================

Based on the insight that:
- When products work well: Customers talk about benefits/outcomes (product becomes invisible)
- When products have problems: Customers complain directly about the product (product becomes visible)

This reframes the analysis to:
1. Treat "no complaints" as positive
2. Prioritize product complaints as improvement opportunities
3. Score based on the ratio of problems to benefits
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from official_scripts.database.supabase_database import SupabaseDatabase
from official_scripts.holistic_evaluation import HolisticEvaluator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ReframedAssessment:
    """Assessment results using the reframed VOC analysis approach"""
    overall_score: float
    performance_level: str
    problem_ratio: float  # Ratio of problems to total feedback
    benefit_ratio: float  # Ratio of benefits to total feedback
    improvement_opportunities: List[Dict]
    winning_factors: List[Dict]
    product_complaints: List[Dict]
    benefit_discussions: List[Dict]
    neutral_discussions: List[Dict]
    assessment_summary: str

class ReframedVOCAnalyzer:
    """
    Reframed VOC Analyzer that treats "no complaints" as positive
    and prioritizes product complaints as improvement opportunities
    """
    
    def __init__(self, database: SupabaseDatabase):
        self.db = database
        self.holistic_evaluator = HolisticEvaluator()
        
    def analyze_client_feedback(self, client_id: str = "Rev") -> ReframedAssessment:
        """
        Analyze client feedback using the reframed approach
        """
        logger.info(f"🎯 REFRAMED VOC ANALYSIS FOR CLIENT: {client_id}")
        logger.info("=" * 60)
        
        # Get all data
        stage1_data = self.db.get_stage1_data_responses(client_id=client_id)
        stage2_data = self.db.get_stage2_response_labeling(client_id)
        
        logger.info(f"📊 Data Sources:")
        logger.info(f"   Stage 1 Quotes: {len(stage1_data)}")
        logger.info(f"   Stage 2 Enriched: {len(stage2_data)}")
        
        # Categorize feedback using reframed approach
        categorized_feedback = self._categorize_feedback_reframed(stage1_data, stage2_data)
        
        # Calculate reframed metrics
        metrics = self._calculate_reframed_metrics(categorized_feedback)
        
        # Generate improvement opportunities from product complaints
        improvement_opportunities = self._extract_improvement_opportunities(
            categorized_feedback['product_complaints']
        )
        
        # Extract winning factors from benefit discussions
        winning_factors = self._extract_winning_factors(
            categorized_feedback['benefit_discussions']
        )
        
        # Calculate reframed score
        reframed_score = self._calculate_reframed_score(metrics)
        
        # Generate assessment summary
        assessment_summary = self._generate_reframed_summary(
            metrics, reframed_score, improvement_opportunities, winning_factors
        )
        
        return ReframedAssessment(
            overall_score=reframed_score,
            performance_level=self._get_performance_level(reframed_score),
            problem_ratio=metrics['problem_ratio'],
            benefit_ratio=metrics['benefit_ratio'],
            improvement_opportunities=improvement_opportunities,
            winning_factors=winning_factors,
            product_complaints=categorized_feedback['product_complaints'],
            benefit_discussions=categorized_feedback['benefit_discussions'],
            neutral_discussions=categorized_feedback['neutral_discussions'],
            assessment_summary=assessment_summary
        )
    
    def _categorize_feedback_reframed(self, stage1_data: pd.DataFrame, stage2_data: pd.DataFrame) -> Dict:
        """
        Categorize feedback using the reframed approach:
        - Product Complaints: Direct complaints about product features/issues
        - Benefit Discussions: Positive outcomes and business value
        - Neutral Discussions: General discussion (treated as positive - no complaints)
        """
        
        # Convert DataFrames to lists of dicts for easier processing
        stage1_list = stage1_data.to_dict('records') if not stage1_data.empty else []
        stage2_list = stage2_data.to_dict('records') if not stage2_data.empty else []
        
        # Create lookup for Stage 2 enriched data
        stage2_lookup = {item['quote_id']: item for item in stage2_list if 'quote_id' in item}
        
        product_complaints = []
        benefit_discussions = []
        neutral_discussions = []
        
        for quote in stage1_list:
            quote_id = quote.get('response_id')  # Use response_id instead of id
            quote_text = quote.get('verbatim_response', '').lower()  # Use verbatim_response instead of response_text
            
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
            
            # Categorize based on content and sentiment
            if self._is_product_complaint(quote_text, sentiment):
                product_complaints.append({
                    'quote_id': quote_id,
                    'text': quote.get('verbatim_response', ''),
                    'sentiment': sentiment,
                    'priority': priority,
                    'enriched_data': enriched_data
                })
            elif self._is_benefit_discussion(quote_text, sentiment):
                benefit_discussions.append({
                    'quote_id': quote_id,
                    'text': quote.get('verbatim_response', ''),
                    'sentiment': sentiment,
                    'priority': priority,
                    'enriched_data': enriched_data
                })
            else:
                # Neutral discussions - treated as positive (no complaints)
                neutral_discussions.append({
                    'quote_id': quote_id,
                    'text': quote.get('verbatim_response', ''),
                    'sentiment': sentiment,
                    'priority': priority,
                    'enriched_data': enriched_data
                })
        
        return {
            'product_complaints': product_complaints,
            'benefit_discussions': benefit_discussions,
            'neutral_discussions': neutral_discussions
        }
    
    def _is_product_complaint(self, text: str, sentiment: str) -> bool:
        """
        Identify product complaints - direct issues with the product
        """
        complaint_indicators = [
            'slow', 'delayed', 'delay', 'inaccurate', 'error', 'bug', 'crash',
            'doesn\'t work', 'not working', 'problem', 'issue', 'difficult',
            'hard to use', 'confusing', 'frustrating', 'annoying', 'terrible',
            'bad', 'poor', 'awful', 'horrible', 'useless', 'broken', 'failed',
            'doesn\'t integrate', 'integration issues', 'technical problems',
            'quality issues', 'accuracy problems', 'speed issues'
        ]
        
        # Check for complaint indicators or negative sentiment
        has_complaint_indicators = any(indicator in text for indicator in complaint_indicators)
        is_negative_sentiment = sentiment in ['negative', 'very negative']
        
        return has_complaint_indicators or is_negative_sentiment
    
    def _is_benefit_discussion(self, text: str, sentiment: str) -> bool:
        """
        Identify benefit discussions - positive outcomes and business value
        """
        benefit_indicators = [
            'saves time', 'efficient', 'efficiency', 'worth it', 'valuable',
            'investment', 'return', 'benefit', 'advantage', 'improvement',
            'better', 'great', 'excellent', 'amazing', 'fantastic', 'love',
            'satisfied', 'happy', 'pleased', 'impressed', 'recommend',
            'streamlines', 'automates', 'reduces', 'increases', 'improves',
            'saves money', 'cost effective', 'productive', 'time saving'
        ]
        
        # Check for benefit indicators or positive sentiment
        has_benefit_indicators = any(indicator in text for indicator in benefit_indicators)
        is_positive_sentiment = sentiment in ['positive', 'very positive']
        
        return has_benefit_indicators or is_positive_sentiment
    
    def _calculate_reframed_metrics(self, categorized_feedback: Dict) -> Dict:
        """
        Calculate metrics using the reframed approach
        """
        total_feedback = (
            len(categorized_feedback['product_complaints']) +
            len(categorized_feedback['benefit_discussions']) +
            len(categorized_feedback['neutral_discussions'])
        )
        
        if total_feedback == 0:
            return {
                'problem_ratio': 0.0,
                'benefit_ratio': 0.0,
                'neutral_ratio': 0.0,
                'total_feedback': 0
            }
        
        problem_ratio = len(categorized_feedback['product_complaints']) / total_feedback
        benefit_ratio = len(categorized_feedback['benefit_discussions']) / total_feedback
        neutral_ratio = len(categorized_feedback['neutral_discussions']) / total_feedback
        
        return {
            'problem_ratio': problem_ratio,
            'benefit_ratio': benefit_ratio,
            'neutral_ratio': neutral_ratio,
            'total_feedback': total_feedback
        }
    
    def _calculate_reframed_score(self, metrics: Dict) -> float:
        """
        Calculate reframed score based on the insight that:
        - Product complaints = problems (negative impact)
        - Benefit discussions = positive outcomes
        - Neutral discussions = no complaints (positive)
        
        Score formula: (benefits + neutral) / total * 10
        This treats "no complaints" as positive
        """
        if metrics['total_feedback'] == 0:
            return 0.0
        
        # Treat neutral discussions as positive (no complaints)
        positive_ratio = metrics['benefit_ratio'] + metrics['neutral_ratio']
        
        # Scale to 0-10
        score = positive_ratio * 10
        
        return round(score, 1)
    
    def _extract_improvement_opportunities(self, product_complaints: List[Dict]) -> List[Dict]:
        """
        Extract improvement opportunities from product complaints
        """
        opportunities = []
        
        for complaint in product_complaints:
            text = complaint['text']
            priority = complaint.get('priority', 1)
            
            # Extract specific issues mentioned
            issues = self._extract_specific_issues(text)
            
            if issues:
                opportunities.append({
                    'quote_id': complaint['quote_id'],
                    'text': text,
                    'issues': issues,
                    'priority': priority,
                    'impact': 'High' if priority >= 3 else 'Medium' if priority >= 2 else 'Low'
                })
        
        # Sort by priority
        opportunities.sort(key=lambda x: x['priority'], reverse=True)
        
        return opportunities[:10]  # Top 10 opportunities
    
    def _extract_specific_issues(self, text: str) -> List[str]:
        """
        Extract specific product issues from complaint text
        """
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
        """
        Extract winning factors from benefit discussions
        """
        factors = []
        
        for benefit in benefit_discussions:
            text = benefit['text']
            priority = benefit.get('priority', 1)
            
            # Extract specific benefits mentioned
            benefits = self._extract_specific_benefits(text)
            
            if benefits:
                factors.append({
                    'quote_id': benefit['quote_id'],
                    'text': text,
                    'benefits': benefits,
                    'priority': priority,
                    'impact': 'High' if priority >= 3 else 'Medium' if priority >= 2 else 'Low'
                })
        
        # Sort by priority
        factors.sort(key=lambda x: x['priority'], reverse=True)
        
        return factors[:10]  # Top 10 factors
    
    def _extract_specific_benefits(self, text: str) -> List[str]:
        """
        Extract specific benefits from positive discussion text
        """
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
        """
        Get performance level based on reframed score
        """
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
    
    def _generate_reframed_summary(self, metrics: Dict, score: float, 
                                 improvement_opportunities: List[Dict], 
                                 winning_factors: List[Dict]) -> str:
        """
        Generate assessment summary using reframed approach
        """
        total_feedback = metrics['total_feedback']
        problem_count = int(metrics['problem_ratio'] * total_feedback)
        benefit_count = int(metrics['benefit_ratio'] * total_feedback)
        neutral_count = int(metrics['neutral_ratio'] * total_feedback)
        
        summary = f"""
🎯 REFRAMED VOC ASSESSMENT SUMMARY
==================================

📊 OVERALL PERFORMANCE: {score}/10 ({self._get_performance_level(score)})

📈 FEEDBACK BREAKDOWN:
   • Product Complaints: {problem_count} ({metrics['problem_ratio']:.1%})
   • Benefit Discussions: {benefit_count} ({metrics['benefit_ratio']:.1%})
   • Neutral Discussions: {neutral_count} ({metrics['neutral_ratio']:.1%})
   • Total Feedback: {total_feedback}

🔍 KEY INSIGHTS:
   • {metrics['neutral_ratio']:.1%} of customers have no complaints (positive indicator)
   • {metrics['benefit_ratio']:.1%} explicitly discuss benefits and value
   • {metrics['problem_ratio']:.1%} report specific product issues

🚀 IMPROVEMENT OPPORTUNITIES: {len(improvement_opportunities)} identified
   • High Priority: {len([o for o in improvement_opportunities if o['impact'] == 'High'])}
   • Medium Priority: {len([o for o in improvement_opportunities if o['impact'] == 'Medium'])}
   • Low Priority: {len([o for o in improvement_opportunities if o['impact'] == 'Low'])}

✅ WINNING FACTORS: {len(winning_factors)} identified
   • High Impact: {len([w for w in winning_factors if w['impact'] == 'High'])}
   • Medium Impact: {len([w for w in winning_factors if w['impact'] == 'Medium'])}
   • Low Impact: {len([w for w in winning_factors if w['impact'] == 'Low'])}

💡 STRATEGIC RECOMMENDATION:
   Focus on addressing the {problem_count} product complaints as they represent
   direct improvement opportunities. The {neutral_count} neutral discussions
   indicate satisfied customers who aren't experiencing problems.
"""
        
        return summary.strip()

def main():
    """Test the reframed VOC analyzer"""
    db = SupabaseDatabase()
    analyzer = ReframedVOCAnalyzer(db)
    
    # Analyze Rev client
    assessment = analyzer.analyze_client_feedback("Rev")
    
    # Print results
    print(assessment.assessment_summary)
    
    print("\n🔧 TOP IMPROVEMENT OPPORTUNITIES:")
    for i, opp in enumerate(assessment.improvement_opportunities[:5], 1):
        print(f"{i}. {opp['text'][:100]}...")
        print(f"   Issues: {', '.join(opp['issues'])} | Impact: {opp['impact']}")
        print()
    
    print("\n✅ TOP WINNING FACTORS:")
    for i, factor in enumerate(assessment.winning_factors[:5], 1):
        print(f"{i}. {factor['text'][:100]}...")
        print(f"   Benefits: {', '.join(factor['benefits'])} | Impact: {factor['impact']}")
        print()

if __name__ == "__main__":
    main() 