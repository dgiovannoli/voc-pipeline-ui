"""
Production VOC System - Interview-Weighted Approach
==================================================

Primary VOC analysis system using interview-weighted methodology.
Each customer counts equally, providing more representative insights.

Key Features:
- Interview-weighted scoring (each customer = 1 vote)
- Strategic recommendations based on customer-level insights
- Executive-ready reporting
- Product development prioritization
- Customer success insights
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
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProductionVOCReport:
    """Production VOC analysis report using interview-weighted approach"""
    client_id: str
    analysis_date: str
    overall_score: float
    performance_level: str
    total_interviews: int
    total_quotes: int
    customer_satisfaction_rate: float
    problem_customers: int
    satisfied_customers: int
    benefit_customers: int
    improvement_opportunities: List[Dict]
    winning_factors: List[Dict]
    strategic_recommendations: List[str]
    executive_summary: str
    detailed_analysis: str

class ProductionVOCSystem:
    """
    Production VOC System using interview-weighted approach
    """
    
    def __init__(self, database: SupabaseDatabase):
        self.db = database
        
    def generate_voc_report(self, client_id: str = "Rev") -> ProductionVOCReport:
        """
        Generate comprehensive VOC report using interview-weighted approach
        """
        logger.info(f"🎯 PRODUCTION VOC ANALYSIS FOR CLIENT: {client_id}")
        logger.info("=" * 60)
        
        # Get data
        stage1_data = self.db.get_stage1_data_responses(client_id=client_id)
        stage2_data = self.db.get_stage2_response_labeling(client_id)
        
        logger.info(f"📊 Data Sources:")
        logger.info(f"   Stage 1 Quotes: {len(stage1_data)}")
        logger.info(f"   Stage 2 Enriched: {len(stage2_data)}")
        
        # Analyze by interview
        interview_analysis = self._analyze_by_interview(stage1_data, stage2_data)
        
        # Calculate metrics
        metrics = self._calculate_metrics(interview_analysis)
        
        # Generate insights
        improvement_opportunities = self._extract_improvement_opportunities(
            interview_analysis['all_product_complaints']
        )
        winning_factors = self._extract_winning_factors(
            interview_analysis['all_benefit_discussions']
        )
        strategic_recommendations = self._generate_strategic_recommendations(metrics, interview_analysis)
        
        # Generate reports
        executive_summary = self._generate_executive_summary(metrics, interview_analysis)
        detailed_analysis = self._generate_detailed_analysis(metrics, interview_analysis, improvement_opportunities, winning_factors)
        
        return ProductionVOCReport(
            client_id=client_id,
            analysis_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            overall_score=metrics['overall_score'],
            performance_level=metrics['performance_level'],
            total_interviews=metrics['total_interviews'],
            total_quotes=len(stage1_data),
            customer_satisfaction_rate=metrics['customer_satisfaction_rate'],
            problem_customers=metrics['problem_customers'],
            satisfied_customers=metrics['satisfied_customers'],
            benefit_customers=metrics['benefit_customers'],
            improvement_opportunities=improvement_opportunities,
            winning_factors=winning_factors,
            strategic_recommendations=strategic_recommendations,
            executive_summary=executive_summary,
            detailed_analysis=detailed_analysis
        )
    
    def _analyze_by_interview(self, stage1_data: pd.DataFrame, stage2_data: pd.DataFrame) -> Dict:
        """
        Analyze feedback by interview (customer) rather than individual quotes
        """
        stage1_list = stage1_data.to_dict('records') if not stage1_data.empty else []
        stage2_list = stage2_data.to_dict('records') if not stage2_data.empty else []
        
        # Create lookup for Stage 2 enriched data
        stage2_lookup = {item['quote_id']: item for item in stage2_list if 'quote_id' in item}
        
        # Group quotes by interview
        interviews = {}
        all_product_complaints = []
        all_benefit_discussions = []
        
        for quote in stage1_list:
            # Create composite interview identifier
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
                    'interview_key': interview_key
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
                    'interview_key': interview_key
                })
            else:
                interviews[interview_key]['neutral_discussions'].append({
                    'quote_id': quote_id,
                    'text': quote.get('verbatim_response', ''),
                    'sentiment': sentiment,
                    'priority': priority
                })
            
            interviews[interview_key]['total_quotes'] += 1
        
        # Categorize interviews
        interview_categories = {
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
                interview_categories['mixed_interviews'].append(interview_data)
            elif has_complaints:
                interview_categories['problem_interviews'].append(interview_data)
            elif has_benefits:
                interview_categories['benefit_interviews'].append(interview_data)
            else:
                interview_categories['neutral_interviews'].append(interview_data)
        
        return {
            'interviews': interviews,
            'interview_categories': interview_categories,
            'all_product_complaints': all_product_complaints,
            'all_benefit_discussions': all_benefit_discussions
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
    
    def _calculate_metrics(self, interview_analysis: Dict) -> Dict:
        """Calculate interview-weighted metrics"""
        categories = interview_analysis['interview_categories']
        
        total_interviews = sum(len(cat) for cat in categories.values())
        
        if total_interviews == 0:
            return {
                'overall_score': 0.0,
                'performance_level': 'No Data',
                'customer_satisfaction_rate': 0.0,
                'problem_customers': 0,
                'satisfied_customers': 0,
                'benefit_customers': 0,
                'total_interviews': 0
            }
        
        # Calculate customer counts
        problem_customers = len(categories['problem_interviews'])
        benefit_customers = len(categories['benefit_interviews'])
        neutral_customers = len(categories['neutral_interviews'])
        mixed_customers = len(categories['mixed_interviews'])
        
        # Calculate satisfaction rate (customers with no complaints)
        satisfied_customers = benefit_customers + neutral_customers + mixed_customers
        customer_satisfaction_rate = (satisfied_customers / total_interviews) * 100
        
        # Calculate overall score (0-10 scale)
        overall_score = (satisfied_customers / total_interviews) * 10
        
        # Determine performance level
        if overall_score >= 8.0:
            performance_level = "Excellent"
        elif overall_score >= 6.0:
            performance_level = "Good"
        elif overall_score >= 4.0:
            performance_level = "Fair"
        elif overall_score >= 2.0:
            performance_level = "Poor"
        else:
            performance_level = "Critical"
        
        return {
            'overall_score': round(overall_score, 1),
            'performance_level': performance_level,
            'customer_satisfaction_rate': round(customer_satisfaction_rate, 1),
            'problem_customers': problem_customers,
            'satisfied_customers': satisfied_customers,
            'benefit_customers': benefit_customers + mixed_customers,
            'total_interviews': total_interviews
        }
    
    def _extract_improvement_opportunities(self, product_complaints: List[Dict]) -> List[Dict]:
        """Extract improvement opportunities from product complaints"""
        opportunities = []
        
        for complaint in product_complaints:
            text = complaint['text']
            priority = complaint.get('priority', 1)
            
            issues = self._extract_specific_issues(text)
            
            if issues:
                opportunities.append({
                    'quote_id': complaint['quote_id'],
                    'interview_key': complaint.get('interview_key', 'unknown'),
                    'text': text,
                    'issues': issues,
                    'priority': priority,
                    'impact': 'High' if priority >= 3 else 'Medium' if priority >= 2 else 'Low'
                })
        
        opportunities.sort(key=lambda x: x['priority'], reverse=True)
        return opportunities[:10]
    
    def _extract_specific_issues(self, text: str) -> List[str]:
        """Extract specific product issues"""
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
            
            benefits = self._extract_specific_benefits(text)
            
            if benefits:
                factors.append({
                    'quote_id': benefit['quote_id'],
                    'interview_key': benefit.get('interview_key', 'unknown'),
                    'text': text,
                    'benefits': benefits,
                    'priority': priority,
                    'impact': 'High' if priority >= 3 else 'Medium' if priority >= 2 else 'Low'
                })
        
        factors.sort(key=lambda x: x['priority'], reverse=True)
        return factors[:10]
    
    def _extract_specific_benefits(self, text: str) -> List[str]:
        """Extract specific benefits"""
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
    
    def _generate_strategic_recommendations(self, metrics: Dict, interview_analysis: Dict) -> List[str]:
        """Generate strategic recommendations"""
        recommendations = []
        
        # Customer success recommendations
        if metrics['problem_customers'] > 0:
            recommendations.append(
                f"🎯 PRIORITY 1: Address {metrics['problem_customers']} customer(s) with product issues "
                f"({metrics['problem_customers']}/{metrics['total_interviews']} customers) - "
                "These represent immediate retention risks"
            )
        else:
            recommendations.append(
                "✅ EXCELLENT: No customers with product complaints identified - "
                "Focus on enhancing existing benefits and expanding market reach"
            )
        
        # Customer satisfaction strategy
        recommendations.append(
            f"💡 CUSTOMER SUCCESS: {metrics['satisfied_customers']}/{metrics['total_interviews']} customers "
            f"({metrics['customer_satisfaction_rate']:.1f}%) are satisfied - "
            "Leverage for testimonials, referrals, and case studies"
        )
        
        # Competitive advantage
        if metrics['benefit_customers'] > 0:
            recommendations.append(
                f"🏆 COMPETITIVE EDGE: {metrics['benefit_customers']}/{metrics['total_interviews']} customers "
                f"({(metrics['benefit_customers']/metrics['total_interviews'])*100:.1f}%) discuss benefits - "
                "Use as key differentiators in marketing and sales"
            )
        
        # Performance assessment
        if metrics['overall_score'] >= 8.0:
            recommendations.append(
                "🚀 GROWTH OPPORTUNITY: Excellent customer satisfaction indicates strong product-market fit - "
                "Focus on scaling successful features and expanding market presence"
            )
        elif metrics['overall_score'] < 6.0:
            recommendations.append(
                "⚠️ RISK MITIGATION: Customer satisfaction below 60% indicates significant improvement needed - "
                "Prioritize addressing customer issues to prevent churn"
            )
        
        return recommendations
    
    def _generate_executive_summary(self, metrics: Dict, interview_analysis: Dict) -> str:
        """Generate executive summary"""
        summary = f"""
🎯 EXECUTIVE VOC SUMMARY - INTERVIEW-WEIGHTED APPROACH
======================================================

📊 PERFORMANCE OVERVIEW:
   • Overall Score: {metrics['overall_score']}/10 ({metrics['performance_level']})
   • Customer Satisfaction: {metrics['customer_satisfaction_rate']:.1f}%
   • Total Customers: {metrics['total_interviews']}
   • Total Feedback: {sum(interview['total_quotes'] for interview in interview_analysis['interviews'].values())} quotes

💡 KEY INSIGHTS:
   • {metrics['satisfied_customers']} out of {metrics['total_interviews']} customers ({metrics['customer_satisfaction_rate']:.1f}%) are satisfied
   • {metrics['benefit_customers']} customers ({(metrics['benefit_customers']/metrics['total_interviews'])*100:.1f}%) explicitly discuss benefits
   • {metrics['problem_customers']} customer(s) ({(metrics['problem_customers']/metrics['total_interviews'])*100:.1f}%) report product issues

🎯 STRATEGIC IMPLICATIONS:
   • Product is meeting expectations for {metrics['satisfied_customers']} customers
   • {metrics['problem_customers']} customer(s) represent immediate retention opportunities
   • {metrics['benefit_customers']} customers provide competitive advantage ammunition

🚀 RECOMMENDED ACTIONS:
   • Priority 1: Address {metrics['problem_customers']} customer(s) with product issues
   • Priority 2: Amplify benefits from {metrics['benefit_customers']} satisfied customers
   • Priority 3: Leverage {metrics['satisfied_customers']} satisfied customers for testimonials
"""
        
        return summary.strip()
    
    def _generate_detailed_analysis(self, metrics: Dict, interview_analysis: Dict, 
                                  improvement_opportunities: List[Dict], 
                                  winning_factors: List[Dict]) -> str:
        """Generate detailed analysis"""
        
        categories = interview_analysis['interview_categories']
        
        analysis = f"""
📋 DETAILED VOC ANALYSIS - INTERVIEW-WEIGHTED
=============================================

🔍 CUSTOMER BREAKDOWN:
   • Problem Customers: {len(categories['problem_interviews'])} ({(len(categories['problem_interviews'])/metrics['total_interviews'])*100:.1f}%)
   • Benefit Customers: {len(categories['benefit_interviews'])} ({(len(categories['benefit_interviews'])/metrics['total_interviews'])*100:.1f}%)
   • Neutral Customers: {len(categories['neutral_interviews'])} ({(len(categories['neutral_interviews'])/metrics['total_interviews'])*100:.1f}%)
   • Mixed Customers: {len(categories['mixed_interviews'])} ({(len(categories['mixed_interviews'])/metrics['total_interviews'])*100:.1f}%)

📊 CUSTOMER DETAILS:
"""
        
        # Show problem customers
        if categories['problem_interviews']:
            analysis += "\n🔧 CUSTOMERS WITH ISSUES:\n"
            for interview in categories['problem_interviews']:
                analysis += f"   • {interview['interviewee_name']} ({interview['company']}) - {interview['total_quotes']} quotes\n"
        
        # Show benefit customers
        if categories['benefit_interviews']:
            analysis += "\n✅ CUSTOMERS WITH BENEFITS:\n"
            for interview in categories['benefit_interviews'][:5]:  # Top 5
                analysis += f"   • {interview['interviewee_name']} ({interview['company']}) - {interview['total_quotes']} quotes\n"
        
        # Show mixed customers
        if categories['mixed_interviews']:
            analysis += f"\n🔄 CUSTOMERS WITH MIXED FEEDBACK ({len(categories['mixed_interviews'])}):\n"
            for interview in categories['mixed_interviews'][:5]:  # Top 5
                analysis += f"   • {interview['interviewee_name']} ({interview['company']}) - {interview['total_quotes']} quotes\n"
        
        analysis += f"""
🔧 IMPROVEMENT OPPORTUNITIES ({len(improvement_opportunities)}):
"""
        
        for i, opp in enumerate(improvement_opportunities[:5], 1):
            analysis += f"""
   {i}. Priority {opp['priority']} - {opp['impact']} Impact
       Customer: {opp['interview_key']}
       Issues: {', '.join(opp['issues'])}
       Quote: "{opp['text'][:100]}..."
"""
        
        analysis += f"""
✅ WINNING FACTORS ({len(winning_factors)}):
"""
        
        for i, factor in enumerate(winning_factors[:5], 1):
            analysis += f"""
   {i}. Priority {factor['priority']} - {factor['impact']} Impact
       Customer: {factor['interview_key']}
       Benefits: {', '.join(factor['benefits'])}
       Quote: "{factor['text'][:100]}..."
"""
        
        analysis += f"""
📈 METHODOLOGY:
   • Interview-weighted scoring: Each customer counts equally
   • Customer satisfaction: {metrics['satisfied_customers']}/{metrics['total_interviews']} customers
   • Overall score: {metrics['overall_score']}/10 based on satisfied customers
   • Rationale: Prevents overweighing of verbose customers
"""
        
        return analysis.strip()
    
    def export_report(self, report: ProductionVOCReport, format: str = "text") -> str:
        """Export the report in various formats"""
        if format.lower() == "text":
            return f"""
{report.executive_summary}

{report.detailed_analysis}

📅 Report Generated: {report.analysis_date}
👤 Client: {report.client_id}
"""
        elif format.lower() == "json":
            import json
            return json.dumps({
                "client_id": report.client_id,
                "analysis_date": report.analysis_date,
                "overall_score": report.overall_score,
                "performance_level": report.performance_level,
                "customer_satisfaction_rate": report.customer_satisfaction_rate,
                "total_interviews": report.total_interviews,
                "total_quotes": report.total_quotes,
                "problem_customers": report.problem_customers,
                "satisfied_customers": report.satisfied_customers,
                "benefit_customers": report.benefit_customers,
                "improvement_opportunities_count": len(report.improvement_opportunities),
                "winning_factors_count": len(report.winning_factors),
                "strategic_recommendations": report.strategic_recommendations
            }, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

def main():
    """Test the production VOC system"""
    print("🎯 TESTING PRODUCTION VOC SYSTEM - INTERVIEW-WEIGHTED")
    print("=" * 60)
    
    try:
        # Initialize system
        db = SupabaseDatabase()
        voc_system = ProductionVOCSystem(db)
        
        # Generate report
        report = voc_system.generate_voc_report("Rev")
        
        # Display results
        print(voc_system.export_report(report, "text"))
        
        # Export as JSON
        json_report = voc_system.export_report(report, "json")
        print(f"\n📄 JSON Export Preview:")
        print(json_report[:500] + "...")
        
    except Exception as e:
        print(f"❌ Error running production VOC system: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 