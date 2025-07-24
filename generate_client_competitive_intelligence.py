#!/usr/bin/env python3
"""
Client-Agnostic Competitive Intelligence Generator
Generates competitive intelligence reports for any client without hardcoded references
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from supabase_database import SupabaseDatabase
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

class ClientCompetitiveIntelligenceGenerator:
    """
    Client-agnostic competitive intelligence generator that works with any client
    without hardcoded references to specific companies.
    """
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.db = SupabaseDatabase()
        
    def generate_competitive_intelligence_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive competitive intelligence report for the specified client
        
        Returns:
            Complete competitive intelligence analysis
        """
        try:
            print(f"🎯 Generating Competitive Intelligence Report for {self.client_id}")
            print("=" * 80)
            
            # Get client-specific data
            client_data = self._get_client_data()
            
            if not client_data:
                return {"error": f"No data found for client {self.client_id}"}
            
            # Generate competitive analysis
            competitive_analysis = self._analyze_competitive_positioning(client_data)
            
            # Generate market insights
            market_insights = self._analyze_market_insights(client_data)
            
            # Generate strategic recommendations
            strategic_recommendations = self._generate_strategic_recommendations(client_data)
            
            # Create executive summary
            executive_summary = self._create_executive_summary(client_data, competitive_analysis)
            
            # Compile full report
            report = {
                "client_id": self.client_id,
                "generated_date": datetime.now().isoformat(),
                "executive_summary": executive_summary,
                "competitive_analysis": competitive_analysis,
                "market_insights": market_insights,
                "strategic_recommendations": strategic_recommendations,
                "data_summary": self._create_data_summary(client_data)
            }
            
            # Save report
            self._save_report(report)
            
            print(f"✅ Competitive intelligence report generated successfully for {self.client_id}")
            return report
            
        except Exception as e:
            print(f"❌ Error generating competitive intelligence report: {e}")
            return {"error": str(e)}
    
    def _get_client_data(self) -> Dict[str, Any]:
        """Get all relevant data for the client"""
        try:
            # Get Stage 1 responses
            responses = self.db.get_stage1_data_responses(self.client_id)
            
            # Get Stage 2 labeled responses
            labeled_responses = self.db.get_stage2_response_labeling(self.client_id)
            
            # Get Stage 3 findings
            findings = self.db.get_stage3_findings(self.client_id)
            
            # Get Stage 4 themes
            themes = self.db.get_themes(self.client_id)
            
            return {
                "responses": responses,
                "labeled_responses": labeled_responses,
                "findings": findings,
                "themes": themes,
                "total_responses": len(responses) if not responses.empty else 0,
                "total_labeled": len(labeled_responses) if not labeled_responses.empty else 0,
                "total_findings": len(findings) if not findings.empty else 0,
                "total_themes": len(themes) if not themes.empty else 0
            }
            
        except Exception as e:
            print(f"Error getting client data: {e}")
            return {}
    
    def _analyze_competitive_positioning(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze competitive positioning based on client data"""
        
        labeled_responses = client_data.get('labeled_responses', pd.DataFrame())
        
        if labeled_responses.empty:
            return {"error": "No labeled response data available"}
        
        # Analyze satisfaction scores
        satisfaction_analysis = self._analyze_satisfaction_scores(labeled_responses)
        
        # Analyze competitive mentions
        competitive_mentions = self._extract_competitive_mentions(labeled_responses)
        
        # Analyze decision factors
        decision_factors = self._analyze_decision_factors(labeled_responses)
        
        return {
            "satisfaction_analysis": satisfaction_analysis,
            "competitive_mentions": competitive_mentions,
            "decision_factors": decision_factors,
            "positioning_summary": self._create_positioning_summary(satisfaction_analysis, competitive_mentions)
        }
    
    def _analyze_satisfaction_scores(self, labeled_responses: pd.DataFrame) -> Dict[str, Any]:
        """Analyze satisfaction scores from labeled responses"""
        
        if labeled_responses.empty:
            return {}
        
        # Calculate overall satisfaction
        if 'satisfaction_score' in labeled_responses.columns:
            overall_satisfaction = labeled_responses['satisfaction_score'].mean()
            satisfaction_distribution = labeled_responses['satisfaction_score'].value_counts().to_dict()
        else:
            overall_satisfaction = 0
            satisfaction_distribution = {}
        
        # Analyze by criteria
        criteria_analysis = {}
        if 'criterion' in labeled_responses.columns:
            for criterion in labeled_responses['criterion'].unique():
                criterion_data = labeled_responses[labeled_responses['criterion'] == criterion]
                if 'relevance_score' in criterion_data.columns:
                    criteria_analysis[criterion] = {
                        "avg_score": criterion_data['relevance_score'].mean(),
                        "count": len(criterion_data),
                        "satisfaction": criterion_data['satisfaction_score'].mean() if 'satisfaction_score' in criterion_data.columns else 0
                    }
        
        return {
            "overall_satisfaction": overall_satisfaction,
            "satisfaction_distribution": satisfaction_distribution,
            "criteria_analysis": criteria_analysis
        }
    
    def _extract_competitive_mentions(self, labeled_responses: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract competitive mentions from labeled responses"""
        
        competitive_mentions = []
        
        if labeled_responses.empty or 'verbatim_response' not in labeled_responses.columns:
            return competitive_mentions
        
        # Look for competitive keywords in responses
        competitive_keywords = [
            'competitor', 'alternative', 'other solution', 'compared to', 'instead of',
            'versus', 'vs', 'better than', 'worse than', 'different from',
            'similar to', 'like', 'unlike', 'prefer', 'choose', 'selected'
        ]
        
        for _, response in labeled_responses.iterrows():
            verbatim = str(response.get('verbatim_response', '')).lower()
            
            for keyword in competitive_keywords:
                if keyword in verbatim:
                    competitive_mentions.append({
                        "response_id": response.get('response_id', ''),
                        "company": response.get('company', 'Unknown'),
                        "interviewee": response.get('interviewee_name', 'Unknown'),
                        "keyword": keyword,
                        "context": verbatim[:200] + "..." if len(verbatim) > 200 else verbatim,
                        "satisfaction_score": response.get('satisfaction_score', 0),
                        "criterion": response.get('criterion', 'Unknown')
                    })
                    break
        
        return competitive_mentions
    
    def _analyze_decision_factors(self, labeled_responses: pd.DataFrame) -> Dict[str, Any]:
        """Analyze decision factors from labeled responses"""
        
        if labeled_responses.empty:
            return {}
        
        # Analyze by criterion and satisfaction
        decision_analysis = {}
        
        if 'criterion' in labeled_responses.columns and 'satisfaction_score' in labeled_responses.columns:
            for criterion in labeled_responses['criterion'].unique():
                criterion_data = labeled_responses[labeled_responses['criterion'] == criterion]
                
                high_satisfaction = criterion_data[criterion_data['satisfaction_score'] >= 8]
                low_satisfaction = criterion_data[criterion_data['satisfaction_score'] <= 4]
                
                decision_analysis[criterion] = {
                    "total_responses": len(criterion_data),
                    "high_satisfaction_count": len(high_satisfaction),
                    "low_satisfaction_count": len(low_satisfaction),
                    "avg_satisfaction": criterion_data['satisfaction_score'].mean(),
                    "importance_score": criterion_data['relevance_score'].mean() if 'relevance_score' in criterion_data.columns else 0
                }
        
        return decision_analysis
    
    def _create_positioning_summary(self, satisfaction_analysis: Dict[str, Any], competitive_mentions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create competitive positioning summary"""
        
        overall_satisfaction = satisfaction_analysis.get('overall_satisfaction', 0)
        
        # Determine positioning based on satisfaction
        if overall_satisfaction >= 8.0:
            positioning = "Market leader with strong customer satisfaction"
        elif overall_satisfaction >= 6.5:
            positioning = "Market challenger with solid customer satisfaction"
        elif overall_satisfaction >= 5.0:
            positioning = "Market follower with mixed customer satisfaction"
        else:
            positioning = "Market challenger with improvement opportunities"
        
        # Analyze competitive landscape
        competitor_count = len(set([mention['keyword'] for mention in competitive_mentions]))
        
        return {
            "positioning": positioning,
            "overall_satisfaction": overall_satisfaction,
            "competitive_mentions_count": len(competitive_mentions),
            "unique_competitors_mentioned": competitor_count,
            "strength_areas": self._identify_strength_areas(satisfaction_analysis),
            "improvement_areas": self._identify_improvement_areas(satisfaction_analysis)
        }
    
    def _identify_strength_areas(self, satisfaction_analysis: Dict[str, Any]) -> List[str]:
        """Identify areas of strength based on satisfaction analysis"""
        
        strength_areas = []
        criteria_analysis = satisfaction_analysis.get('criteria_analysis', {})
        
        for criterion, data in criteria_analysis.items():
            if data.get('satisfaction', 0) >= 8.0:
                strength_areas.append(criterion)
        
        return strength_areas
    
    def _identify_improvement_areas(self, satisfaction_analysis: Dict[str, Any]) -> List[str]:
        """Identify areas for improvement based on satisfaction analysis"""
        
        improvement_areas = []
        criteria_analysis = satisfaction_analysis.get('criteria_analysis', {})
        
        for criterion, data in criteria_analysis.items():
            if data.get('satisfaction', 0) <= 5.0:
                improvement_areas.append(criterion)
        
        return improvement_areas
    
    def _analyze_market_insights(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market insights from client data"""
        
        themes = client_data.get('themes', pd.DataFrame())
        findings = client_data.get('findings', pd.DataFrame())
        
        market_insights = {
            "theme_analysis": self._analyze_themes(themes),
            "finding_analysis": self._analyze_findings(findings),
            "market_trends": self._identify_market_trends(themes, findings)
        }
        
        return market_insights
    
    def _analyze_themes(self, themes: pd.DataFrame) -> Dict[str, Any]:
        """Analyze themes for market insights"""
        
        if themes.empty:
            return {}
        
        theme_analysis = {
            "total_themes": len(themes),
            "theme_categories": {},
            "top_themes": []
        }
        
        # Analyze theme categories
        if 'theme_category' in themes.columns:
            theme_analysis['theme_categories'] = themes['theme_category'].value_counts().to_dict()
        
        # Get top themes by confidence
        if 'enhanced_confidence' in themes.columns:
            top_themes = themes.nlargest(5, 'enhanced_confidence')
            theme_analysis['top_themes'] = top_themes[['theme_title', 'enhanced_confidence']].to_dict('records')
        
        return theme_analysis
    
    def _analyze_findings(self, findings: pd.DataFrame) -> Dict[str, Any]:
        """Analyze findings for market insights"""
        
        if findings.empty:
            return {}
        
        finding_analysis = {
            "total_findings": len(findings),
            "finding_categories": {},
            "top_findings": []
        }
        
        # Analyze finding categories
        if 'finding_category' in findings.columns:
            finding_analysis['finding_categories'] = findings['finding_category'].value_counts().to_dict()
        
        # Get top findings by confidence
        if 'enhanced_confidence' in findings.columns:
            top_findings = findings.nlargest(5, 'enhanced_confidence')
            finding_analysis['top_findings'] = top_findings[['finding_statement', 'enhanced_confidence']].to_dict('records')
        
        return finding_analysis
    
    def _identify_market_trends(self, themes: pd.DataFrame, findings: pd.DataFrame) -> List[str]:
        """Identify market trends from themes and findings"""
        
        trends = []
        
        # Analyze themes for trends
        if not themes.empty and 'theme_title' in themes.columns:
            theme_titles = themes['theme_title'].str.lower().str.cat(sep=' ')
            
            # Look for trend indicators
            trend_keywords = ['growing', 'increasing', 'trend', 'emerging', 'new', 'evolving', 'changing']
            for keyword in trend_keywords:
                if keyword in theme_titles:
                    trends.append(f"Emerging trend: {keyword} customer needs")
        
        # Analyze findings for trends
        if not findings.empty and 'finding_statement' in findings.columns:
            finding_statements = findings['finding_statement'].str.lower().str.cat(sep=' ')
            
            for keyword in trend_keywords:
                if keyword in finding_statements:
                    trends.append(f"Market trend: {keyword} market dynamics")
        
        return trends
    
    def _generate_strategic_recommendations(self, client_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate strategic recommendations based on client data"""
        
        recommendations = []
        
        # Get competitive analysis
        competitive_analysis = self._analyze_competitive_positioning(client_data)
        positioning_summary = competitive_analysis.get('positioning_summary', {})
        
        # Generate recommendations based on positioning
        satisfaction = positioning_summary.get('overall_satisfaction', 0)
        strength_areas = positioning_summary.get('strength_areas', [])
        improvement_areas = positioning_summary.get('improvement_areas', [])
        
        # Recommendation 1: Leverage strengths
        if strength_areas:
            recommendations.append({
                "priority": "High",
                "category": "Leverage Strengths",
                "recommendation": f"Capitalize on strong performance in {', '.join(strength_areas[:3])}",
                "rationale": "Strong customer satisfaction in these areas provides competitive advantage",
                "timeline": "3-6 months",
                "impact": "High"
            })
        
        # Recommendation 2: Address weaknesses
        if improvement_areas:
            recommendations.append({
                "priority": "High",
                "category": "Address Weaknesses",
                "recommendation": f"Improve performance in {', '.join(improvement_areas[:3])}",
                "rationale": "Low satisfaction in these areas creates competitive vulnerability",
                "timeline": "6-12 months",
                "impact": "High"
            })
        
        # Recommendation 3: Market expansion
        if satisfaction >= 7.0:
            recommendations.append({
                "priority": "Medium",
                "category": "Market Expansion",
                "recommendation": "Expand into adjacent market segments",
                "rationale": "Strong customer satisfaction indicates product-market fit",
                "timeline": "12-18 months",
                "impact": "Medium"
            })
        
        return recommendations
    
    def _create_executive_summary(self, client_data: Dict[str, Any], competitive_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create executive summary for the competitive intelligence report"""
        
        positioning_summary = competitive_analysis.get('positioning_summary', {})
        
        summary = {
            "client_id": self.client_id,
            "positioning": positioning_summary.get('positioning', 'Market position analysis pending'),
            "overall_satisfaction": positioning_summary.get('overall_satisfaction', 0),
            "data_summary": {
                "total_responses": client_data.get('total_responses', 0),
                "total_findings": client_data.get('total_findings', 0),
                "total_themes": client_data.get('total_themes', 0)
            },
            "key_insights": [
                f"Customer satisfaction: {positioning_summary.get('overall_satisfaction', 0):.1f}/10",
                f"Strength areas: {len(positioning_summary.get('strength_areas', []))} identified",
                f"Improvement areas: {len(positioning_summary.get('improvement_areas', []))} identified",
                f"Competitive mentions: {positioning_summary.get('competitive_mentions_count', 0)} found"
            ]
        }
        
        return summary
    
    def _create_data_summary(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create data summary for the report"""
        
        return {
            "data_sources": {
                "stage1_responses": client_data.get('total_responses', 0),
                "stage2_labeled": client_data.get('total_labeled', 0),
                "stage3_findings": client_data.get('total_findings', 0),
                "stage4_themes": client_data.get('total_themes', 0)
            },
            "data_quality": {
                "completeness": "High" if client_data.get('total_responses', 0) > 0 else "Low",
                "diversity": "High" if client_data.get('total_responses', 0) > 10 else "Low"
            }
        }
    
    def _save_report(self, report: Dict[str, Any]) -> str:
        """Save the competitive intelligence report to file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.client_id}_COMPETITIVE_INTELLIGENCE_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📄 Report saved: {filename}")
        return filename

def generate_competitive_intelligence_for_client(client_id: str) -> Dict[str, Any]:
    """
    Generate competitive intelligence report for a specific client
    
    Args:
        client_id: The client ID to generate the report for
        
    Returns:
        Complete competitive intelligence analysis
    """
    generator = ClientCompetitiveIntelligenceGenerator(client_id)
    return generator.generate_competitive_intelligence_report()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        client_id = sys.argv[1]
    else:
        client_id = input("Enter client ID: ")
    
    report = generate_competitive_intelligence_for_client(client_id)
    print(f"✅ Competitive intelligence report generated for {client_id}") 