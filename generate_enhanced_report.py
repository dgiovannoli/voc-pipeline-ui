#!/usr/bin/env python3
"""
Generate Enhanced Theme Story Scorecard Report
Direct text file generation without Streamlit UI
"""

import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from official_scripts.enhanced_theme_story_scorecard import EnhancedThemeStoryScorecard

def generate_and_save_report(client_id='Rev'):
    """Generate enhanced report and save as text file"""
    
    print(f"🎯 Generating Enhanced Theme Story Scorecard Report for {client_id}")
    print("=" * 80)
    
    try:
        # Create generator instance
        generator = EnhancedThemeStoryScorecard()
        generator.client_id = client_id
        
        # Generate the enhanced report
        scorecard = generator.generate_enhanced_report()
        
        # Generate report text
        report_text = generate_full_report_text(scorecard, client_id)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{client_id}_ENHANCED_THEME_STORY_REPORT_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"✅ Report saved successfully: {filename}")
        print(f"📄 File size: {len(report_text)} characters")
        
        return filename
        
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def generate_full_report_text(scorecard, client_id):
    """Generate the full enhanced report text"""
    
    report_lines = []
    report_lines.append(f"🎯 {client_id.upper()} ENHANCED THEME-STORY SCORECARD REPORT")
    report_lines.append("Executive-Ready: Themes, Evidence, Credibility, Actionable Insights")
    report_lines.append("="*100)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # Executive Summary
    overall_score = calculate_overall_score(scorecard)
    performance_level = get_performance_level(overall_score)
    
    report_lines.append("📋 EXECUTIVE SUMMARY")
    report_lines.append(f"   Overall Score: {overall_score:.1f}/10")
    report_lines.append(f"   Performance Level: {performance_level}")
    report_lines.append("")
    
    # Count strengths and weaknesses
    total_strengths = sum(data['scorecard_metrics']['strength_count'] for data in scorecard.values())
    total_weaknesses = sum(data['scorecard_metrics']['weakness_count'] for data in scorecard.values())
    total_opportunities = sum(data['scorecard_metrics']['opportunity_count'] for data in scorecard.values())
    
    report_lines.append("   🏆 TOP STRENGTHS:")
    strengths_by_criterion = []
    for criterion, data in scorecard.items():
        if data['scorecard_metrics']['strength_count'] > 0:
            strengths_by_criterion.append({
                'criterion': data['framework']['title'],
                'strength_count': data['scorecard_metrics']['strength_count'],
                'score': data['scorecard_metrics']['score']
            })
    
    strengths_by_criterion.sort(key=lambda x: x['strength_count'], reverse=True)
    for strength in strengths_by_criterion[:3]:
        report_lines.append(f"     • {strength['criterion']}: {strength['strength_count']} strengths (Score: {strength['score']:.1f}/10)")
    
    report_lines.append("")
    report_lines.append("   🔧 TOP AREAS FOR IMPROVEMENT:")
    weaknesses_by_criterion = []
    for criterion, data in scorecard.items():
        if data['scorecard_metrics']['weakness_count'] > 0:
            weaknesses_by_criterion.append({
                'criterion': data['framework']['title'],
                'weakness_count': data['scorecard_metrics']['weakness_count'],
                'score': data['scorecard_metrics']['score']
            })
    
    weaknesses_by_criterion.sort(key=lambda x: x['weakness_count'], reverse=True)
    for weakness in weaknesses_by_criterion[:3]:
        report_lines.append(f"     • {weakness['criterion']}: {weakness['weakness_count']} weaknesses (Score: {weakness['score']:.1f}/10)")
    
    report_lines.append("")
    
    # Scorecard Framework
    report_lines.append("📊 DETAILED SCORECARD FRAMEWORK")
    report_lines.append("   Understanding the Framework:")
    report_lines.append("   • Score (0-10): Overall performance in this area based on theme analysis")
    report_lines.append("   • Weight (%): Relative importance of this area to overall business success")
    report_lines.append("   • Evidence: Number of supporting quotes and findings from customer interviews")
    report_lines.append("   • Performance: Executive assessment of competitive position")
    report_lines.append("")
    
    for criterion, data in scorecard.items():
        metrics = data['scorecard_metrics']
        framework = data['framework']
        
        report_lines.append(f"   📋 {framework['title']}")
        report_lines.append(f"     Weight: {metrics['weight']*100:.0f}% - {framework['business_impact']}")
        report_lines.append(f"     Score: {metrics['score']:.1f}/10 - {metrics['performance_description']}")
        report_lines.append(f"     Evidence: {metrics['total_evidence']} items from {metrics['unique_clients']} clients")
        report_lines.append(f"     Coverage: {metrics['evidence_coverage']} evidence, {metrics['client_coverage']} client coverage")
        report_lines.append(f"     Themes: {metrics['strength_count']} strengths, {metrics['weakness_count']} weaknesses, {metrics['opportunity_count']} opportunities")
        report_lines.append("")
    
    # Theme-Driven Analysis
    report_lines.append("🎯 THEME-DRIVEN ANALYSIS BY CRITERION")
    report_lines.append("")
    
    for criterion, data in scorecard.items():
        report_lines.append(f"   📋 {data['framework']['title']}")
        report_lines.append(f"     {data['framework']['executive_description']}")
        report_lines.append("")
        
        # Strengths
        positive_themes = [t for t in data['all_themes'] if t['direction']['direction'] == 'positive']
        if positive_themes:
            report_lines.append("     🏆 STRENGTHS:")
            for theme in positive_themes[:3]:  # Top 3 strengths
                evidence = data['theme_evidence'].get(theme['theme_id'], {})
                evidence_summary = evidence.get('evidence_summary', {})
                
                report_lines.append(f"       • {theme['title']}")
                report_lines.append(f"         {theme['statement']}")
                report_lines.append(f"         Business Impact: {theme['business_impact']['description']}")
                report_lines.append(f"         Evidence: {evidence_summary.get('total_evidence', 0)} items from {evidence_summary.get('unique_clients', 0)} clients")
                
                # Show top supporting quote
                if evidence.get('quotes'):
                    top_quote = evidence['quotes'][0]
                    report_lines.append(f"         Key Quote: \"{top_quote['quote'][:200]}...\"")
                    report_lines.append(f"           - {top_quote['interviewee_name']}, {top_quote.get('interviewee_role', 'Unknown Role')} at {top_quote['company']}")
                report_lines.append("")
        
        # Weaknesses
        negative_themes = [t for t in data['all_themes'] if t['direction']['direction'] == 'negative']
        if negative_themes:
            report_lines.append("     🔧 AREAS FOR IMPROVEMENT:")
            for theme in negative_themes[:3]:  # Top 3 weaknesses
                evidence = data['theme_evidence'].get(theme['theme_id'], {})
                evidence_summary = evidence.get('evidence_summary', {})
                
                report_lines.append(f"       • {theme['title']}")
                report_lines.append(f"         {theme['statement']}")
                report_lines.append(f"         Business Impact: {theme['business_impact']['description']}")
                report_lines.append(f"         Evidence: {evidence_summary.get('total_evidence', 0)} items from {evidence_summary.get('unique_clients', 0)} clients")
                
                # Show top supporting quote
                if evidence.get('quotes'):
                    top_quote = evidence['quotes'][0]
                    report_lines.append(f"         Key Quote: \"{top_quote['quote'][:200]}...\"")
                    report_lines.append(f"           - {top_quote['interviewee_name']}, {top_quote.get('interviewee_role', 'Unknown Role')} at {top_quote['company']}")
                report_lines.append("")
    
    # Strategic Implications
    report_lines.append("📈 STRATEGIC IMPLICATIONS")
    report_lines.append("   🎯 Executive Recommendations:")
    report_lines.append("")
    
    for criterion, data in scorecard.items():
        metrics = data['scorecard_metrics']
        framework = data['framework']
        
        if metrics['performance'] in ['excellent', 'good']:
            report_lines.append(f"     • {framework['title']}: Leverage existing strengths for competitive advantage")
        elif metrics['performance'] in ['poor', 'critical']:
            report_lines.append(f"     • {framework['title']}: Prioritize improvements to address competitive vulnerabilities")
        else:
            report_lines.append(f"     • {framework['title']}: Focus on opportunities to enhance competitive positioning")
    
    report_lines.append("")
    report_lines.append("🎯 ENHANCED THEME-STORY SCORECARD REPORT COMPLETE")
    report_lines.append("="*100)
    
    return "\n".join(report_lines)

def calculate_overall_score(scorecard):
    """Calculate overall score from scorecard"""
    total_weighted_score = sum(data['scorecard_metrics']['weighted_score'] for data in scorecard.values())
    total_weight = sum(data['scorecard_metrics']['weight'] for data in scorecard.values())
    return total_weighted_score / total_weight if total_weight > 0 else 0

def get_performance_level(score):
    """Get performance level description"""
    if score >= 7.5:
        return 'Excellent - Strong competitive advantages with clear market differentiation'
    elif score >= 6.0:
        return 'Good - Competitive positioning with some areas for improvement'
    elif score >= 4.5:
        return 'Fair - Mixed competitive position with significant improvement opportunities'
    elif score >= 3.0:
        return 'Poor - Competitive vulnerabilities requiring immediate attention'
    else:
        return 'Critical - Major competitive disadvantages requiring urgent strategic intervention'

if __name__ == "__main__":
    # Generate report for Rev (default)
    client_id = 'Rev'
    if len(sys.argv) > 1:
        client_id = sys.argv[1]
    
    filename = generate_and_save_report(client_id)
    if filename:
        print(f"\n🎉 Enhanced report generated successfully!")
        print(f"📄 File: {filename}")
        print(f"📁 Location: {os.path.abspath(filename)}")
    else:
        print("\n❌ Failed to generate report") 