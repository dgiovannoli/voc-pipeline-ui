"""
Comprehensive VOC System
========================

A complete system that implements the reframed VOC analysis approach:

Key Insights:
1. When products work well: Customers talk about benefits/outcomes (product becomes invisible)
2. When products have problems: Customers complain directly about the product (product becomes visible)
3. Neutral discussions = no complaints = positive indicator
4. Product complaints = direct improvement roadmap

This system provides:
- Reframed scoring that treats "no complaints" as positive
- Prioritized improvement opportunities from product complaints
- Winning factors from benefit discussions
- Strategic recommendations for product development
- Executive-ready reporting
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
from official_scripts.reframed_voc_analyzer import ReframedVOCAnalyzer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ComprehensiveVOCReport:
    """Comprehensive VOC analysis report"""
    client_id: str
    analysis_date: str
    reframed_score: float
    performance_level: str
    problem_ratio: float
    benefit_ratio: float
    neutral_ratio: float
    total_feedback: int
    improvement_opportunities: List[Dict]
    winning_factors: List[Dict]
    strategic_recommendations: List[str]
    executive_summary: str
    detailed_analysis: str

class ComprehensiveVOCSystem:
    """
    Comprehensive VOC System that implements the reframed approach
    and provides strategic insights for product development
    """
    
    def __init__(self, database: SupabaseDatabase):
        self.db = database
        self.reframed_analyzer = ReframedVOCAnalyzer(database)
        
    def generate_comprehensive_report(self, client_id: str = "Rev") -> ComprehensiveVOCReport:
        """
        Generate a comprehensive VOC report using the reframed approach
        """
        logger.info(f"🎯 GENERATING COMPREHENSIVE VOC REPORT FOR CLIENT: {client_id}")
        logger.info("=" * 70)
        
        # Get reframed assessment
        assessment = self.reframed_analyzer.analyze_client_feedback(client_id)
        
        # Generate strategic recommendations
        strategic_recommendations = self._generate_strategic_recommendations(assessment)
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(assessment)
        
        # Generate detailed analysis
        detailed_analysis = self._generate_detailed_analysis(assessment)
        
        return ComprehensiveVOCReport(
            client_id=client_id,
            analysis_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            reframed_score=assessment.overall_score,
            performance_level=assessment.performance_level,
            problem_ratio=assessment.problem_ratio,
            benefit_ratio=assessment.benefit_ratio,
            neutral_ratio=1 - assessment.problem_ratio - assessment.benefit_ratio,
            total_feedback=int(assessment.problem_ratio + assessment.benefit_ratio + (1 - assessment.problem_ratio - assessment.benefit_ratio)) * assessment.total_feedback if hasattr(assessment, 'total_feedback') else 0,
            improvement_opportunities=assessment.improvement_opportunities,
            winning_factors=assessment.winning_factors,
            strategic_recommendations=strategic_recommendations,
            executive_summary=executive_summary,
            detailed_analysis=detailed_analysis
        )
    
    def _generate_strategic_recommendations(self, assessment) -> List[str]:
        """
        Generate strategic recommendations based on the reframed analysis
        """
        recommendations = []
        
        # Calculate key metrics
        problem_count = len(assessment.product_complaints)
        benefit_count = len(assessment.benefit_discussions)
        neutral_count = len(assessment.neutral_discussions)
        total_feedback = problem_count + benefit_count + neutral_count
        
        # 1. Product Development Priorities
        if problem_count > 0:
            recommendations.append(
                f"🚀 PRIORITY 1: Address {problem_count} Product Complaints "
                f"({(problem_count/total_feedback)*100:.1f}% of feedback) - "
                "These represent direct improvement opportunities with clear ROI"
            )
        else:
            recommendations.append(
                "✅ EXCELLENT: No product complaints identified - "
                "Focus on enhancing existing benefits and expanding market reach"
            )
        
        # 2. Customer Satisfaction Strategy
        if neutral_count > benefit_count:
            recommendations.append(
                f"💡 STRATEGY: Leverage {neutral_count} satisfied customers "
                f"({(neutral_count/total_feedback)*100:.1f}% of feedback) - "
                "These customers aren't complaining, indicating product meets expectations"
            )
        
        # 3. Competitive Advantage
        if benefit_count > 0:
            recommendations.append(
                f"🏆 COMPETITIVE EDGE: Amplify {benefit_count} identified benefits "
                f"({(benefit_count/total_feedback)*100:.1f}% of feedback) - "
                "Use these as key differentiators in marketing and sales"
            )
        
        # 4. Risk Management
        if assessment.overall_score < 6.0:
            recommendations.append(
                "⚠️ RISK MITIGATION: Score below 6.0 indicates significant improvement needed - "
                "Prioritize addressing product complaints to prevent customer churn"
            )
        elif assessment.overall_score >= 8.0:
            recommendations.append(
                "🎯 GROWTH OPPORTUNITY: Excellent score (8.0+) indicates strong product-market fit - "
                "Focus on scaling successful features and expanding market presence"
            )
        
        # 5. Specific Improvement Areas
        if assessment.improvement_opportunities:
            top_issues = self._extract_top_issues(assessment.improvement_opportunities)
            recommendations.append(
                f"🔧 TARGETED IMPROVEMENTS: Focus on {', '.join(top_issues[:3])} - "
                "These represent the most common customer pain points"
            )
        
        return recommendations
    
    def _extract_top_issues(self, improvement_opportunities: List[Dict]) -> List[str]:
        """
        Extract the most common issues from improvement opportunities
        """
        issue_counts = {}
        for opp in improvement_opportunities:
            for issue in opp.get('issues', []):
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Sort by frequency
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        return [issue for issue, count in sorted_issues]
    
    def _generate_executive_summary(self, assessment) -> str:
        """
        Generate an executive summary of the VOC analysis
        """
        problem_count = len(assessment.product_complaints)
        benefit_count = len(assessment.benefit_discussions)
        neutral_count = len(assessment.neutral_discussions)
        total_feedback = problem_count + benefit_count + neutral_count
        
        summary = f"""
🎯 EXECUTIVE VOC SUMMARY
========================

📊 PERFORMANCE OVERVIEW:
   • Overall Score: {assessment.overall_score}/10 ({assessment.performance_level})
   • Customer Satisfaction: {(neutral_count/total_feedback)*100:.1f}% (no complaints)
   • Product Issues: {(problem_count/total_feedback)*100:.1f}% (improvement opportunities)
   • Explicit Benefits: {(benefit_count/total_feedback)*100:.1f}% (competitive advantages)

💡 KEY INSIGHTS:
   • {neutral_count} customers ({neutral_count/total_feedback*100:.1f}%) have no complaints
   • {benefit_count} customers ({benefit_count/total_feedback*100:.1f}%) explicitly discuss benefits
   • {problem_count} customers ({problem_count/total_feedback*100:.1f}%) report specific issues

🎯 STRATEGIC IMPLICATIONS:
   • Product is meeting expectations for {neutral_count + benefit_count} customers ({((neutral_count + benefit_count)/total_feedback)*100:.1f}%)
   • {problem_count} improvement opportunities represent direct ROI potential
   • Neutral discussions indicate satisfied customers who aren't experiencing problems

🚀 RECOMMENDED ACTIONS:
   • Priority 1: Address {problem_count} product complaints for immediate impact
   • Priority 2: Amplify {benefit_count} identified benefits in marketing
   • Priority 3: Leverage {neutral_count} satisfied customers for testimonials/referrals
"""
        
        return summary.strip()
    
    def _generate_detailed_analysis(self, assessment) -> str:
        """
        Generate detailed analysis with specific examples
        """
        problem_count = len(assessment.product_complaints)
        benefit_count = len(assessment.benefit_discussions)
        neutral_count = len(assessment.neutral_discussions)
        
        analysis = f"""
📋 DETAILED VOC ANALYSIS
========================

🔍 FEEDBACK CATEGORIZATION:
   • Product Complaints: {problem_count} quotes
   • Benefit Discussions: {benefit_count} quotes  
   • Neutral Discussions: {neutral_count} quotes (treated as positive)
   • Total Feedback: {problem_count + benefit_count + neutral_count} quotes

🔧 IMPROVEMENT OPPORTUNITIES ({len(assessment.improvement_opportunities)}):
"""
        
        # Add top improvement opportunities
        for i, opp in enumerate(assessment.improvement_opportunities[:5], 1):
            analysis += f"""
   {i}. Priority {opp['priority']} - {opp['impact']} Impact
       Issues: {', '.join(opp['issues'])}
       Quote: "{opp['text'][:100]}..."
"""
        
        analysis += f"""
✅ WINNING FACTORS ({len(assessment.winning_factors)}):
"""
        
        # Add top winning factors
        for i, factor in enumerate(assessment.winning_factors[:5], 1):
            analysis += f"""
   {i}. Priority {factor['priority']} - {factor['impact']} Impact
       Benefits: {', '.join(factor['benefits'])}
       Quote: "{factor['text'][:100]}..."
"""
        
        analysis += f"""
📈 SCORING METHODOLOGY:
   • Reframed Score: {(assessment.benefit_ratio + (1 - assessment.problem_ratio - assessment.benefit_ratio))*10:.1f}/10
   • Formula: (Benefits + Neutral) / Total * 10
   • Rationale: Neutral discussions = no complaints = positive indicator
   • Traditional Score: ~4.0/10 (based on sentiment analysis)
   • Improvement: +{assessment.overall_score - 4.0:.1f} points

🎯 STRATEGIC RECOMMENDATIONS:
"""
        
        # Add strategic recommendations
        for i, rec in enumerate(self._generate_strategic_recommendations(assessment), 1):
            analysis += f"   {i}. {rec}\n"
        
        return analysis.strip()
    
    def export_report(self, report: ComprehensiveVOCReport, format: str = "text") -> str:
        """
        Export the comprehensive report in various formats
        """
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
                "reframed_score": report.reframed_score,
                "performance_level": report.performance_level,
                "problem_ratio": report.problem_ratio,
                "benefit_ratio": report.benefit_ratio,
                "neutral_ratio": report.neutral_ratio,
                "total_feedback": report.total_feedback,
                "improvement_opportunities_count": len(report.improvement_opportunities),
                "winning_factors_count": len(report.winning_factors),
                "strategic_recommendations": report.strategic_recommendations
            }, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def compare_clients(self, client_ids: List[str]) -> Dict:
        """
        Compare VOC performance across multiple clients
        """
        comparisons = {}
        
        for client_id in client_ids:
            try:
                report = self.generate_comprehensive_report(client_id)
                comparisons[client_id] = {
                    "reframed_score": report.reframed_score,
                    "performance_level": report.performance_level,
                    "problem_ratio": report.problem_ratio,
                    "benefit_ratio": report.benefit_ratio,
                    "neutral_ratio": report.neutral_ratio,
                    "total_feedback": report.total_feedback
                }
            except Exception as e:
                logger.error(f"Failed to analyze client {client_id}: {e}")
                comparisons[client_id] = {"error": str(e)}
        
        return comparisons

def main():
    """Test the comprehensive VOC system"""
    print("🎯 TESTING COMPREHENSIVE VOC SYSTEM")
    print("=" * 50)
    
    try:
        # Initialize system
        db = SupabaseDatabase()
        voc_system = ComprehensiveVOCSystem(db)
        
        # Generate comprehensive report
        report = voc_system.generate_comprehensive_report("Rev")
        
        # Display results
        print(voc_system.export_report(report, "text"))
        
        # Export as JSON
        json_report = voc_system.export_report(report, "json")
        print(f"\n📄 JSON Export Preview:")
        print(json_report[:500] + "...")
        
    except Exception as e:
        print(f"❌ Error running comprehensive VOC system: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 