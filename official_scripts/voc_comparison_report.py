"""
VOC Comparison Report
====================

Shows both quote-counted and interview-weighted approaches side by side
to demonstrate the difference in methodology and results.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from official_scripts.database.supabase_database import SupabaseDatabase
from official_scripts.production_voc_system import ProductionVOCSystem
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VOCComparisonReport:
    """
    Generates a comparison between quote-counted and interview-weighted approaches
    """
    
    def __init__(self, database: SupabaseDatabase):
        self.db = database
        self.voc_system = ProductionVOCSystem(database)
    
    def generate_comparison(self, client_id: str = "Rev") -> str:
        """
        Generate a comprehensive comparison report
        """
        logger.info(f"🎯 GENERATING VOC COMPARISON REPORT FOR CLIENT: {client_id}")
        logger.info("=" * 60)
        
        # Get interview-weighted results
        interview_report = self.voc_system.generate_voc_report(client_id)
        
        # Get quote-counted results
        quote_results = self._calculate_quote_counted_results(client_id)
        
        # Generate comparison
        comparison = self._generate_comparison_text(interview_report, quote_results)
        
        return comparison
    
    def _calculate_quote_counted_results(self, client_id: str) -> Dict:
        """
        Calculate quote-counted results for comparison
        """
        stage1_data = self.db.get_stage1_data_responses(client_id=client_id)
        stage2_data = self.db.get_stage2_response_labeling(client_id)
        
        stage1_list = stage1_data.to_dict('records') if not stage1_data.empty else []
        stage2_list = stage2_data.to_dict('records') if not stage2_data.empty else []
        
        # Create lookup for Stage 2 enriched data
        stage2_lookup = {item['quote_id']: item for item in stage2_list if 'quote_id' in item}
        
        # Count quotes by category
        product_complaints = 0
        benefit_discussions = 0
        neutral_discussions = 0
        total_quotes = len(stage1_list)
        
        for quote in stage1_list:
            quote_id = quote.get('response_id')
            quote_text = quote.get('verbatim_response', '').lower()
            
            # Get enriched data if available
            enriched_data = stage2_lookup.get(quote_id, {})
            sentiment = enriched_data.get('sentiment', 'neutral')
            
            # Categorize quote
            if self._is_product_complaint(quote_text, sentiment):
                product_complaints += 1
            elif self._is_benefit_discussion(quote_text, sentiment):
                benefit_discussions += 1
            else:
                neutral_discussions += 1
        
        # Calculate quote-counted score
        satisfied_quotes = benefit_discussions + neutral_discussions
        quote_satisfaction_rate = (satisfied_quotes / total_quotes) * 100 if total_quotes > 0 else 0
        quote_score = (satisfied_quotes / total_quotes) * 10 if total_quotes > 0 else 0
        
        return {
            'total_quotes': total_quotes,
            'product_complaints': product_complaints,
            'benefit_discussions': benefit_discussions,
            'neutral_discussions': neutral_discussions,
            'satisfied_quotes': satisfied_quotes,
            'quote_satisfaction_rate': round(quote_satisfaction_rate, 1),
            'quote_score': round(quote_score, 1)
        }
    
    def _is_product_complaint(self, text: str, sentiment: str) -> bool:
        """Identify product complaints"""
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
        """Identify benefit discussions"""
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
    
    def _generate_comparison_text(self, interview_report, quote_results: Dict) -> str:
        """
        Generate the comparison text
        """
        comparison = f"""
🎯 VOC ANALYSIS COMPARISON REPORT
=================================

📊 METHODOLOGY COMPARISON:
   • Interview-Weighted: Each customer counts equally (1 vote per customer)
   • Quote-Counted: Each quote counts equally (1 vote per quote)

📈 RESULTS COMPARISON:
   • Total Customers: {interview_report.total_interviews}
   • Total Quotes: {interview_report.total_quotes}

┌─────────────────────────────────────────────────────────────┐
│                    INTERVIEW-WEIGHTED                       │
├─────────────────────────────────────────────────────────────┤
│ Overall Score: {interview_report.overall_score}/10 ({interview_report.performance_level}) │
│ Customer Satisfaction: {interview_report.customer_satisfaction_rate}%                    │
│ Satisfied Customers: {interview_report.satisfied_customers}/{interview_report.total_interviews}        │
│ Problem Customers: {interview_report.problem_customers}                                    │
│ Benefit Customers: {interview_report.benefit_customers}                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     QUOTE-COUNTED                          │
├─────────────────────────────────────────────────────────────┤
│ Overall Score: {quote_results['quote_score']}/10                                    │
│ Quote Satisfaction: {quote_results['quote_satisfaction_rate']}%                        │
│ Satisfied Quotes: {quote_results['satisfied_quotes']}/{quote_results['total_quotes']}              │
│ Problem Quotes: {quote_results['product_complaints']}                                    │
│ Benefit Quotes: {quote_results['benefit_discussions']}                                    │
└─────────────────────────────────────────────────────────────┘

📊 KEY DIFFERENCES:

🎯 SCORE DIFFERENCE:
   • Interview-Weighted: {interview_report.overall_score}/10
   • Quote-Counted: {quote_results['quote_score']}/10
   • Difference: {interview_report.overall_score - quote_results['quote_score']:.1f} points

💡 SATISFACTION DIFFERENCE:
   • Interview-Weighted: {interview_report.customer_satisfaction_rate}% customer satisfaction
   • Quote-Counted: {quote_results['quote_satisfaction_rate']}% quote satisfaction
   • Difference: {interview_report.customer_satisfaction_rate - quote_results['quote_satisfaction_rate']:.1f} percentage points

🎯 PROBLEM ASSESSMENT:
   • Interview-Weighted: {interview_report.problem_customers} customer(s) with issues
   • Quote-Counted: {quote_results['product_complaints']} individual complaints
   • Difference: {quote_results['product_complaints'] - interview_report.problem_customers} more complaints than customers

📈 STRATEGIC IMPLICATIONS:

✅ INTERVIEW-WEIGHTED ADVANTAGES:
   • More representative of customer sentiment
   • Better for executive decision-making
   • Prevents overweighing verbose customers
   • Clearer customer success metrics
   • More actionable for retention strategies

⚠️ QUOTE-COUNTED LIMITATIONS:
   • Can overweigh verbose customers
   • Less representative of customer satisfaction
   • Harder to translate to business metrics
   • May inflate problem perception

🎯 RECOMMENDED APPROACH:

🏆 PRIMARY: Interview-Weighted Approach
   • Use for executive reporting
   • Use for strategic decision-making
   • Use for customer success metrics
   • Use for business performance assessment

📋 SECONDARY: Quote-Counted Approach
   • Use for product development prioritization
   • Use for detailed issue analysis
   • Use for feature improvement planning
   • Use for technical roadmap

💡 BUSINESS IMPACT:

🎯 CUSTOMER SUCCESS:
   • Interview-Weighted: Focus on {interview_report.problem_customers} customer(s)
   • Quote-Counted: Focus on {quote_results['product_complaints']} individual issues
   • Recommendation: Prioritize customer-level intervention

📊 MARKETING & SALES:
   • Interview-Weighted: {interview_report.satisfied_customers} satisfied customers for testimonials
   • Quote-Counted: {quote_results['satisfied_quotes']} positive quotes for marketing
   • Recommendation: Leverage customer stories over individual quotes

🚀 PRODUCT DEVELOPMENT:
   • Interview-Weighted: Address issues affecting {interview_report.problem_customers} customer(s)
   • Quote-Counted: Address {quote_results['product_complaints']} specific complaints
   • Recommendation: Use quote analysis for feature prioritization

📅 Report Generated: {interview_report.analysis_date}
👤 Client: {interview_report.client_id}
"""
        
        return comparison.strip()

def main():
    """Test the VOC comparison report"""
    print("🎯 TESTING VOC COMPARISON REPORT")
    print("=" * 60)
    
    try:
        # Initialize system
        db = SupabaseDatabase()
        comparison_system = VOCComparisonReport(db)
        
        # Generate comparison
        comparison = comparison_system.generate_comparison("Rev")
        
        # Display results
        print(comparison)
        
    except Exception as e:
        print(f"❌ Error running VOC comparison: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 