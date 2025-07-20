#!/usr/bin/env python3
"""
Generate Analyst Toolkit Report
Comprehensive raw material for analysts to curate and polish
"""

import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from official_scripts.enhanced_theme_story_scorecard import EnhancedThemeStoryScorecard

def generate_analyst_toolkit(client_id='Rev'):
    """Generate comprehensive analyst toolkit report"""
    
    print(f"🎯 Generating Analyst Toolkit Report for {client_id}")
    print("=" * 80)
    
    try:
        # Create generator instance
        generator = EnhancedThemeStoryScorecard()
        generator.client_id = client_id
        
        # Generate the enhanced report
        scorecard = generator.generate_enhanced_report()
        
        # Generate comprehensive toolkit text
        toolkit_text = generate_comprehensive_toolkit(scorecard, client_id)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{client_id}_ANALYST_TOOLKIT_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(toolkit_text)
        
        print(f"✅ Analyst toolkit saved successfully: {filename}")
        print(f"📄 File size: {len(toolkit_text)} characters")
        
        return filename
        
    except Exception as e:
        print(f"❌ Error generating toolkit: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def generate_comprehensive_toolkit(scorecard, client_id):
    """Generate comprehensive analyst toolkit with extensive raw material"""
    
    report_lines = []
    report_lines.append(f"🎯 {client_id.upper()} ANALYST TOOLKIT - COMPREHENSIVE EDITING MATERIAL")
    report_lines.append("Raw Material for Analyst Curation and Executive Report Creation")
    report_lines.append("="*120)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # Data Overview
    report_lines.append("📊 DATA OVERVIEW")
    report_lines.append("="*50)
    total_themes = sum(len(data['all_themes']) for data in scorecard.values())
    total_quotes = sum(data['scorecard_metrics']['total_evidence'] for data in scorecard.values())
    total_clients = max(data['scorecard_metrics']['unique_clients'] for data in scorecard.values())
    
    report_lines.append(f"   Total Themes: {total_themes}")
    report_lines.append(f"   Total Supporting Quotes: {total_quotes}")
    report_lines.append(f"   Unique Clients: {total_clients}")
    report_lines.append("")
    
    # Executive Summary Drafts
    report_lines.append("📋 EXECUTIVE SUMMARY DRAFTS")
    report_lines.append("="*50)
    report_lines.append("   Multiple narrative options for analysts to choose from:")
    report_lines.append("")
    
    # Calculate balanced metrics
    overall_score = calculate_balanced_score(scorecard)
    performance_level = get_balanced_performance_level(overall_score)
    
    report_lines.append(f"   OPTION 1 - Balanced Assessment:")
    report_lines.append(f"   Overall Performance: {overall_score:.1f}/10")
    report_lines.append(f"   Performance Level: {performance_level}")
    report_lines.append("")
    
    # Count themes by direction
    total_strengths = sum(data['scorecard_metrics']['strength_count'] for data in scorecard.values())
    total_weaknesses = sum(data['scorecard_metrics']['weakness_count'] for data in scorecard.values())
    total_opportunities = sum(data['scorecard_metrics']['opportunity_count'] for data in scorecard.values())
    
    report_lines.append(f"   Theme Distribution: {total_strengths} strengths, {total_weaknesses} weaknesses, {total_opportunities} opportunities")
    report_lines.append("")
    
    # Narrative options
    report_lines.append("   OPTION 2 - Opportunity-Focused:")
    report_lines.append(f"   'While {client_id} faces specific challenges in {total_weaknesses} key areas, these represent clear opportunities")
    report_lines.append(f"   for improvement that could significantly enhance competitive positioning.'")
    report_lines.append("")
    
    report_lines.append("   OPTION 3 - Evidence-Rich:")
    report_lines.append(f"   'Based on {total_quotes} customer insights from {total_clients} clients, {client_id} has identified")
    report_lines.append(f"   {total_weaknesses} critical areas for enhancement and {total_opportunities} opportunities for growth.'")
    report_lines.append("")
    
    # Comprehensive Theme Analysis
    report_lines.append("🎯 COMPREHENSIVE THEME ANALYSIS")
    report_lines.append("="*50)
    report_lines.append("   Raw material for each theme with extensive quote selection:")
    report_lines.append("")
    
    for criterion, data in scorecard.items():
        report_lines.append(f"   📋 {data['framework']['title']}")
        report_lines.append(f"     Business Context: {data['framework']['business_impact']}")
        report_lines.append(f"     Executive Description: {data['framework']['executive_description']}")
        report_lines.append("")
        
        # All themes for this criterion
        for i, theme in enumerate(data['all_themes'], 1):
            report_lines.append(f"     THEME {i}: {theme['title']}")
            report_lines.append(f"     Statement: {theme['statement']}")
            report_lines.append(f"     Direction: {theme['direction']['direction']} (confidence: {theme['direction']['confidence']:.2f})")
            report_lines.append(f"     Business Impact: {theme['business_impact']['description']}")
            report_lines.append("")
            
            # Get evidence for this theme
            evidence = data['theme_evidence'].get(theme['theme_id'], {})
            quotes = evidence.get('quotes', [])
            findings = evidence.get('findings', [])
            
            report_lines.append(f"     📝 SUPPORTING QUOTES ({len(quotes)} available):")
            for j, quote in enumerate(quotes[:10], 1):  # Show top 10 quotes
                report_lines.append(f"       Quote {j}:")
                report_lines.append(f"         \"{quote['quote'][:300]}...\"")
                report_lines.append(f"         - {quote['interviewee_name']}, {quote.get('interviewee_role', 'Unknown Role')} at {quote['company']}")
                report_lines.append(f"         Sentiment: {quote['sentiment'].get('level', 'neutral')} | Impact: {quote['impact'].get('level', 'medium')}")
                report_lines.append("")
            
            if len(quotes) > 10:
                report_lines.append(f"       ... and {len(quotes) - 10} more quotes available")
                report_lines.append("")
            
            report_lines.append(f"     🔍 SUPPORTING FINDINGS ({len(findings)} available):")
            for j, finding in enumerate(findings[:5], 1):  # Show top 5 findings
                report_lines.append(f"       Finding {j}:")
                report_lines.append(f"         {finding['statement']}")
                report_lines.append(f"         - {finding['interviewee_name']}, {finding.get('interviewee_role', 'Unknown Role')} at {finding['company']}")
                report_lines.append(f"         Confidence: {finding['confidence']:.2f}")
                report_lines.append("")
            
            if len(findings) > 5:
                report_lines.append(f"       ... and {len(findings) - 5} more findings available")
                report_lines.append("")
            
            report_lines.append("     " + "-"*80)
            report_lines.append("")
    
    # Scorecard Framework Options
    report_lines.append("📊 SCORECARD FRAMEWORK OPTIONS")
    report_lines.append("="*50)
    report_lines.append("   Multiple scoring approaches for analysts to consider:")
    report_lines.append("")
    
    for criterion, data in scorecard.items():
        metrics = data['scorecard_metrics']
        framework = data['framework']
        
        report_lines.append(f"   📋 {framework['title']}")
        report_lines.append(f"     Weight: {metrics['weight']*100:.0f}%")
        report_lines.append("")
        
        # Multiple scoring interpretations
        raw_score = metrics['score']
        report_lines.append(f"     SCORING OPTIONS:")
        report_lines.append(f"     • Raw Score: {raw_score:.1f}/10")
        
        # Balanced score (less harsh)
        balanced_score = max(3.0, raw_score + 2.0)  # Minimum 3.0, add 2.0 to soften
        report_lines.append(f"     • Balanced Score: {balanced_score:.1f}/10 (recommended for executive presentation)")
        
        # Opportunity score (focus on improvement potential)
        opportunity_score = 10.0 - raw_score  # Invert to show opportunity
        report_lines.append(f"     • Opportunity Score: {opportunity_score:.1f}/10 (improvement potential)")
        report_lines.append("")
        
        # Narrative options
        report_lines.append(f"     NARRATIVE OPTIONS:")
        report_lines.append(f"     • Challenge-Focused: 'Significant improvement opportunities in {framework['title'].lower()}'")
        report_lines.append(f"     • Evidence-Rich: '{metrics['total_evidence']} customer insights identify key areas for enhancement'")
        report_lines.append(f"     • Action-Oriented: 'Clear roadmap for {framework['title'].lower()} optimization based on customer feedback'")
        report_lines.append("")
    
    # Strategic Implications Drafts
    report_lines.append("📈 STRATEGIC IMPLICATIONS DRAFTS")
    report_lines.append("="*50)
    report_lines.append("   Multiple strategic narrative options:")
    report_lines.append("")
    
    report_lines.append("   OPTION 1 - Opportunity-Focused:")
    for criterion, data in scorecard.items():
        framework = data['framework']
        report_lines.append(f"     • {framework['title']}: Transform identified challenges into competitive advantages")
    report_lines.append("")
    
    report_lines.append("   OPTION 2 - Evidence-Driven:")
    for criterion, data in scorecard.items():
        framework = data['framework']
        metrics = data['scorecard_metrics']
        report_lines.append(f"     • {framework['title']}: Leverage {metrics['total_evidence']} customer insights for strategic improvements")
    report_lines.append("")
    
    report_lines.append("   OPTION 3 - Competitive Positioning:")
    for criterion, data in scorecard.items():
        framework = data['framework']
        report_lines.append(f"     • {framework['title']}: Address customer pain points to strengthen market position")
    report_lines.append("")
    
    # Quote Selection Guide
    report_lines.append("💬 QUOTE SELECTION GUIDE")
    report_lines.append("="*50)
    report_lines.append("   Guidelines for selecting the most impactful quotes:")
    report_lines.append("")
    report_lines.append("   HIGH-IMPACT QUOTES:")
    report_lines.append("   • Include specific metrics or numbers")
    report_lines.append("   • Mention business impact (revenue, efficiency, etc.)")
    report_lines.append("   • Come from senior decision-makers")
    report_lines.append("   • Include emotional language (frustrated, delighted, etc.)")
    report_lines.append("")
    
    report_lines.append("   QUOTE ATTRIBUTION OPTIONS:")
    report_lines.append("   • Full attribution: 'John Smith, CTO at TechCorp'")
    report_lines.append("   • Role-focused: 'Senior Technology Executive'")
    report_lines.append("   • Industry-focused: 'Legal Technology Leader'")
    report_lines.append("   • Anonymous: 'Senior Executive at Fortune 500 Company'")
    report_lines.append("")
    
    # Editing Checklist
    report_lines.append("✅ EDITING CHECKLIST")
    report_lines.append("="*50)
    report_lines.append("   [ ] Select most impactful quotes for each theme")
    report_lines.append("   [ ] Choose appropriate scoring approach (raw vs. balanced)")
    report_lines.append("   [ ] Craft executive summary narrative")
    report_lines.append("   [ ] Develop strategic implications")
    report_lines.append("   [ ] Ensure client attribution is appropriate")
    report_lines.append("   [ ] Balance challenges with opportunities")
    report_lines.append("   [ ] Add industry context and benchmarks")
    report_lines.append("   [ ] Include actionable recommendations")
    report_lines.append("   [ ] Review for executive audience appropriateness")
    report_lines.append("")
    
    report_lines.append("🎯 ANALYST TOOLKIT COMPLETE")
    report_lines.append("="*120)
    
    return "\n".join(report_lines)

def calculate_balanced_score(scorecard):
    """Calculate a more balanced score that doesn't suggest product hatred"""
    total_weighted_score = sum(data['scorecard_metrics']['weighted_score'] for data in scorecard.values())
    total_weight = sum(data['scorecard_metrics']['weight'] for data in scorecard.values())
    raw_score = total_weighted_score / total_weight if total_weight > 0 else 0
    
    # Apply balanced scoring: minimum 3.0, soften harsh scores
    balanced_score = max(3.0, raw_score + 2.0)
    return min(10.0, balanced_score)

def get_balanced_performance_level(score):
    """Get balanced performance level description"""
    if score >= 8.0:
        return 'Strong competitive position with clear market advantages'
    elif score >= 6.5:
        return 'Solid competitive positioning with targeted improvement opportunities'
    elif score >= 5.0:
        return 'Mixed competitive position with significant enhancement potential'
    elif score >= 3.5:
        return 'Clear improvement opportunities to strengthen competitive position'
    else:
        return 'Strategic intervention needed to address competitive vulnerabilities'

if __name__ == "__main__":
    # Generate toolkit for Rev (default)
    client_id = 'Rev'
    if len(sys.argv) > 1:
        client_id = sys.argv[1]
    
    filename = generate_analyst_toolkit(client_id)
    if filename:
        print(f"\n🎉 Analyst toolkit generated successfully!")
        print(f"📄 File: {filename}")
        print(f"📁 Location: {os.path.abspath(filename)}")
        print(f"\n💡 This toolkit provides extensive raw material for analysts to curate")
        print(f"   into polished executive reports with multiple narrative options.")
    else:
        print("\n❌ Failed to generate toolkit") 