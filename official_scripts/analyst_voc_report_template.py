"""
Analyst VOC Report Template
==========================

Integrated report template for analysts that combines:
- Interview-weighted VOC analysis (primary)
- Quote-counted analysis (secondary)
- Strategic recommendations
- Executive summary
- Detailed findings

This template provides a structured format for consistent analyst reporting.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from official_scripts.database.supabase_database import SupabaseDatabase
from official_scripts.production_voc_system import ProductionVOCSystem
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AnalystVOCReport:
    """Complete analyst VOC report with all sections"""
    client_id: str
    analysis_date: str
    analyst_name: str
    report_version: str
    
    # Interview-weighted metrics (primary)
    interview_score: float
    interview_satisfaction: float
    total_customers: int
    problem_customers: int
    satisfied_customers: int
    benefit_customers: int
    
    # Quote-counted metrics (secondary)
    quote_score: float
    quote_satisfaction: float
    total_quotes: int
    problem_quotes: int
    benefit_quotes: int
    
    # Key insights
    executive_summary: str
    methodology_explanation: str
    customer_breakdown: str
    improvement_opportunities: List[Dict]
    winning_factors: List[Dict]
    strategic_recommendations: List[str]
    
    # Detailed analysis
    detailed_findings: str
    comparison_analysis: str
    action_items: List[str]
    
    # Technical details
    data_sources: Dict
    confidence_level: str
    limitations: List[str]

class AnalystVOCReportGenerator:
    """
    Generates comprehensive analyst VOC reports using interview-weighted approach
    """
    
    def __init__(self, database: SupabaseDatabase):
        self.db = database
        self.voc_system = ProductionVOCSystem(database)
    
    def generate_analyst_report(self, client_id: str, analyst_name: str = "Analyst") -> AnalystVOCReport:
        """
        Generate complete analyst VOC report
        """
        logger.info(f"📋 GENERATING ANALYST VOC REPORT FOR CLIENT: {client_id}")
        logger.info(f"👤 Analyst: {analyst_name}")
        logger.info("=" * 60)
        
        # Get interview-weighted results (primary)
        interview_report = self.voc_system.generate_voc_report(client_id)
        
        # Get quote-counted results (secondary)
        quote_results = self._calculate_quote_counted_results(client_id)
        
        # Generate all sections
        executive_summary = self._generate_executive_summary(interview_report, quote_results)
        methodology_explanation = self._generate_methodology_explanation()
        customer_breakdown = self._generate_customer_breakdown(interview_report)
        improvement_opportunities = interview_report.improvement_opportunities
        winning_factors = interview_report.winning_factors
        strategic_recommendations = interview_report.strategic_recommendations
        detailed_findings = self._generate_detailed_findings(interview_report, quote_results)
        comparison_analysis = self._generate_comparison_analysis(interview_report, quote_results)
        action_items = self._generate_action_items(interview_report)
        
        return AnalystVOCReport(
            client_id=client_id,
            analysis_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            analyst_name=analyst_name,
            report_version="1.0",
            
            # Interview-weighted metrics
            interview_score=interview_report.overall_score,
            interview_satisfaction=interview_report.customer_satisfaction_rate,
            total_customers=interview_report.total_interviews,
            problem_customers=interview_report.problem_customers,
            satisfied_customers=interview_report.satisfied_customers,
            benefit_customers=interview_report.benefit_customers,
            
            # Quote-counted metrics
            quote_score=quote_results['quote_score'],
            quote_satisfaction=quote_results['quote_satisfaction_rate'],
            total_quotes=quote_results['total_quotes'],
            problem_quotes=quote_results['product_complaints'],
            benefit_quotes=quote_results['benefit_discussions'],
            
            # Content sections
            executive_summary=executive_summary,
            methodology_explanation=methodology_explanation,
            customer_breakdown=customer_breakdown,
            improvement_opportunities=improvement_opportunities,
            winning_factors=winning_factors,
            strategic_recommendations=strategic_recommendations,
            detailed_findings=detailed_findings,
            comparison_analysis=comparison_analysis,
            action_items=action_items,
            
            # Technical details
            data_sources={
                'stage1_quotes': quote_results['total_quotes'],
                'stage2_enriched': len(self.db.get_stage2_response_labeling(client_id)),
                'stage3_findings': len(self.db.get_stage3_findings(client_id)),
                'stage4_themes': len(self.db.get_themes(client_id))
            },
            confidence_level="High",
            limitations=[
                "Analysis based on available interview data",
                "Sentiment analysis may not capture nuanced feedback",
                "Limited historical comparison data"
            ]
        )
    
    def _calculate_quote_counted_results(self, client_id: str) -> Dict:
        """Calculate quote-counted results for comparison"""
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
    
    def _generate_executive_summary(self, interview_report, quote_results: Dict) -> str:
        """Generate executive summary"""
        summary = f"""
🎯 EXECUTIVE VOC SUMMARY - {interview_report.client_id.upper()}
===============================================================

📊 PERFORMANCE OVERVIEW:
   • Primary Score (Interview-Weighted): {interview_report.overall_score}/10 ({interview_report.performance_level})
   • Secondary Score (Quote-Counted): {quote_results['quote_score']}/10
   • Customer Satisfaction: {interview_report.customer_satisfaction_rate}% ({interview_report.satisfied_customers}/{interview_report.total_interviews} customers)
   • Total Feedback: {interview_report.total_quotes} quotes from {interview_report.total_interviews} customers

💡 KEY INSIGHTS:
   • {interview_report.satisfied_customers} out of {interview_report.total_interviews} customers ({interview_report.customer_satisfaction_rate}%) are satisfied
   • {interview_report.benefit_customers} customers ({(interview_report.benefit_customers/interview_report.total_interviews)*100:.1f}%) explicitly discuss benefits
   • {interview_report.problem_customers} customer(s) ({(interview_report.problem_customers/interview_report.total_interviews)*100:.1f}%) report product issues

🎯 STRATEGIC IMPLICATIONS:
   • Product is meeting expectations for {interview_report.satisfied_customers} customers
   • {interview_report.problem_customers} customer(s) represent immediate retention opportunities
   • {interview_report.benefit_customers} customers provide competitive advantage ammunition

🚀 RECOMMENDED ACTIONS:
   • Priority 1: Address {interview_report.problem_customers} customer(s) with product issues
   • Priority 2: Amplify benefits from {interview_report.satisfied_customers} satisfied customers
   • Priority 3: Leverage {interview_report.satisfied_customers} satisfied customers for testimonials
"""
        
        return summary.strip()
    
    def _generate_methodology_explanation(self) -> str:
        """Generate methodology explanation"""
        methodology = """
📋 METHODOLOGY EXPLANATION
==========================

🎯 PRIMARY APPROACH: Interview-Weighted Analysis
   • Each customer counts equally (1 vote per customer)
   • Prevents overweighing of verbose customers
   • More representative of customer sentiment
   • Better for executive decision-making
   • Used for strategic recommendations and business metrics

📊 SECONDARY APPROACH: Quote-Counted Analysis
   • Each quote counts equally (1 vote per quote)
   • Provides detailed issue breakdown
   • Useful for product development prioritization
   • Shows granular feedback patterns
   • Used for technical roadmap and feature planning

📈 SCORING METHODOLOGY:
   • Interview-Weighted Score: (Satisfied Customers / Total Customers) × 10
   • Quote-Counted Score: (Satisfied Quotes / Total Quotes) × 10
   • Customer Satisfaction: (Satisfied Customers / Total Customers) × 100
   • Quote Satisfaction: (Satisfied Quotes / Total Quotes) × 100

🔍 CATEGORIZATION CRITERIA:
   • Product Complaints: Negative sentiment or complaint indicators
   • Benefit Discussions: Positive sentiment or benefit indicators
   • Neutral Discussions: Neither complaints nor benefits
   • Mixed Customers: Both complaints and benefits
   • Problem Customers: Only complaints
   • Benefit Customers: Only benefits
"""
        
        return methodology.strip()
    
    def _generate_customer_breakdown(self, interview_report) -> str:
        """Generate customer breakdown"""
        breakdown = f"""
📊 CUSTOMER BREAKDOWN - INTERVIEW-WEIGHTED
==========================================

🔍 CUSTOMER CATEGORIES:
   • Problem Customers: {interview_report.problem_customers} ({(interview_report.problem_customers/interview_report.total_interviews)*100:.1f}%)
   • Benefit Customers: {interview_report.benefit_customers} ({(interview_report.benefit_customers/interview_report.total_interviews)*100:.1f}%)
   • Mixed Customers: {interview_report.total_interviews - interview_report.problem_customers - interview_report.benefit_customers} ({(interview_report.total_interviews - interview_report.problem_customers - interview_report.benefit_customers)/interview_report.total_interviews*100:.1f}%)

📋 CUSTOMER DETAILS:
"""
        
        # Add customer details from the report
        if hasattr(interview_report, 'detailed_analysis'):
            breakdown += interview_report.detailed_analysis
        
        return breakdown.strip()
    
    def _generate_detailed_findings(self, interview_report, quote_results: Dict) -> str:
        """Generate detailed findings"""
        findings = f"""
📋 DETAILED VOC FINDINGS
========================

🎯 INTERVIEW-WEIGHTED FINDINGS (PRIMARY):
   • Overall Score: {interview_report.overall_score}/10 ({interview_report.performance_level})
   • Customer Satisfaction: {interview_report.customer_satisfaction_rate}%
   • Problem Customers: {interview_report.problem_customers}
   • Satisfied Customers: {interview_report.satisfied_customers}
   • Benefit Customers: {interview_report.benefit_customers}

📊 QUOTE-COUNTED FINDINGS (SECONDARY):
   • Overall Score: {quote_results['quote_score']}/10
   • Quote Satisfaction: {quote_results['quote_satisfaction_rate']}%
   • Problem Quotes: {quote_results['product_complaints']}
   • Benefit Quotes: {quote_results['benefit_discussions']}
   • Neutral Quotes: {quote_results['neutral_discussions']}

🔧 IMPROVEMENT OPPORTUNITIES ({len(interview_report.improvement_opportunities)}):
"""
        
        for i, opp in enumerate(interview_report.improvement_opportunities[:5], 1):
            findings += f"""
   {i}. Priority {opp['priority']} - {opp['impact']} Impact
       Customer: {opp['interview_key']}
       Issues: {', '.join(opp['issues'])}
       Quote: "{opp['text'][:100]}..."
"""
        
        findings += f"""
✅ WINNING FACTORS ({len(interview_report.winning_factors)}):
"""
        
        for i, factor in enumerate(interview_report.winning_factors[:5], 1):
            findings += f"""
   {i}. Priority {factor['priority']} - {factor['impact']} Impact
       Customer: {factor['interview_key']}
       Benefits: {', '.join(factor['benefits'])}
       Quote: "{factor['text'][:100]}..."
"""
        
        return findings.strip()
    
    def _generate_comparison_analysis(self, interview_report, quote_results: Dict) -> str:
        """Generate comparison analysis"""
        comparison = f"""
📊 COMPARISON ANALYSIS
======================

🎯 SCORE COMPARISON:
   • Interview-Weighted: {interview_report.overall_score}/10
   • Quote-Counted: {quote_results['quote_score']}/10
   • Difference: {interview_report.overall_score - quote_results['quote_score']:.1f} points

💡 SATISFACTION COMPARISON:
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

🎯 RECOMMENDED USAGE:
   • Interview-Weighted: Executive reporting, strategic decisions, customer success
   • Quote-Counted: Product development, feature prioritization, technical roadmap
"""
        
        return comparison.strip()
    
    def _generate_action_items(self, interview_report) -> List[str]:
        """Generate action items"""
        action_items = [
            f"🎯 PRIORITY 1: Address {interview_report.problem_customers} customer(s) with product issues",
            f"📊 PRIORITY 2: Amplify benefits from {interview_report.satisfied_customers} satisfied customers",
            f"💬 PRIORITY 3: Leverage {interview_report.satisfied_customers} satisfied customers for testimonials",
            f"🔧 PRIORITY 4: Address {len(interview_report.improvement_opportunities)} identified improvement opportunities",
            f"🏆 PRIORITY 5: Use {len(interview_report.winning_factors)} winning factors in marketing materials"
        ]
        
        return action_items
    
    def export_report(self, report: AnalystVOCReport, format: str = "text") -> str:
        """Export the complete analyst report"""
        if format.lower() == "text":
            report_text = f"""
{report.executive_summary}

{report.methodology_explanation}

{report.customer_breakdown}

{report.detailed_findings}

{report.comparison_analysis}

🎯 STRATEGIC RECOMMENDATIONS:
"""
            
            for i, rec in enumerate(report.strategic_recommendations, 1):
                report_text += f"   {i}. {rec}\n"
            
            report_text += f"""
📋 ACTION ITEMS:
"""
            
            for i, action in enumerate(report.action_items, 1):
                report_text += f"   {i}. {action}\n"
            
            report_text += f"""
📊 TECHNICAL DETAILS:
   • Data Sources: {report.data_sources}
   • Confidence Level: {report.confidence_level}
   • Limitations: {', '.join(report.limitations)}

📅 Report Generated: {report.analysis_date}
👤 Analyst: {report.analyst_name}
👤 Client: {report.client_id}
📄 Version: {report.report_version}
"""
            
            return report_text.strip()
        
        elif format.lower() == "json":
            import json
            return json.dumps({
                "client_id": report.client_id,
                "analysis_date": report.analysis_date,
                "analyst_name": report.analyst_name,
                "report_version": report.report_version,
                "interview_weighted": {
                    "score": report.interview_score,
                    "satisfaction": report.interview_satisfaction,
                    "total_customers": report.total_customers,
                    "problem_customers": report.problem_customers,
                    "satisfied_customers": report.satisfied_customers,
                    "benefit_customers": report.benefit_customers
                },
                "quote_counted": {
                    "score": report.quote_score,
                    "satisfaction": report.quote_satisfaction,
                    "total_quotes": report.total_quotes,
                    "problem_quotes": report.problem_quotes,
                    "benefit_quotes": report.benefit_quotes
                },
                "improvement_opportunities_count": len(report.improvement_opportunities),
                "winning_factors_count": len(report.winning_factors),
                "strategic_recommendations": report.strategic_recommendations,
                "action_items": report.action_items,
                "data_sources": report.data_sources,
                "confidence_level": report.confidence_level,
                "limitations": report.limitations
            }, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

def main():
    """Test the analyst VOC report template"""
    print("📋 TESTING ANALYST VOC REPORT TEMPLATE")
    print("=" * 60)
    
    try:
        # Initialize system
        db = SupabaseDatabase()
        report_generator = AnalystVOCReportGenerator(db)
        
        # Generate report
        report = report_generator.generate_analyst_report("Rev", "John Doe")
        
        # Display results
        print(report_generator.export_report(report, "text"))
        
        # Export as JSON
        json_report = report_generator.export_report(report, "json")
        print(f"\n📄 JSON Export Preview:")
        print(json_report[:500] + "...")
        
    except Exception as e:
        print(f"❌ Error running analyst report template: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 