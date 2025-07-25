#!/usr/bin/env python3

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import logging
from typing import Dict, List, Optional, Tuple
import yaml
from collections import defaultdict, Counter

# Import Supabase database manager
from supabase_database import SupabaseDatabase

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Stage5ExecutiveAnalyzer:
    """
    Stage 5: Executive Synthesis - Transform stage4_themes into C-suite ready narratives with criteria scorecard
    """
    
    def __init__(self, config_path="config/analysis_config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=4000,
            temperature=0.2
        )
        
        # Initialize Supabase database
        self.db = SupabaseDatabase()
        
        # Processing metrics
        self.processing_metrics = {
            "total_stage4_themes_processed": 0,
            "executive_stage4_themes_generated": 0,
            "high_impact_stage4_themes": 0,
            "competitive_stage4_themes": 0,
            "criteria_analyzed": 0,
            "processing_errors": 0
        }
    
    def load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Default configuration for Stage 5"""
        return {
            'stage5': {
                'min_theme_strength': 'Medium',
                'max_executive_stage4_themes': 10,
                'priority_score_weights': {
                    'competitive_flag': 3.0,
                    'theme_strength': 2.0,
                    'company_count': 1.5,
                    'avg_confidence': 1.0
                }
            }
        }
    
    def get_stage4_themes_for_synthesis(self, client_id: str = 'default') -> pd.DataFrame:
        """Get stage4_themes from database for executive synthesis"""
        return self.db.get_stage4_themes(client_id=client_id)
    
    def generate_criteria_scorecard(self, client_id: str = 'default') -> Dict:
        """Generate criteria scorecard from database"""
        return self.db.generate_criteria_scorecard(client_id=client_id)
    
    def generate_executive_synthesis(self, stage4_themes_df: pd.DataFrame, scorecard: Dict) -> List[Dict]:
        """Generate executive synthesis from stage4_themes with scorecard context"""
        logger.info("🎯 Generating executive synthesis...")
        
        executive_stage4_themes = []
        
        for _, theme in stage4_themes_df.iterrows():
            try:
                synthesis = self._generate_single_executive_theme(theme, scorecard)
                if synthesis:
                    executive_stage4_themes.append(synthesis)
                    
            except Exception as e:
                logger.error(f"Error generating synthesis for theme {theme.get('id')}: {e}")
                self.processing_metrics["processing_errors"] += 1
        
        # Sort by priority score
        executive_stage4_themes.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        
        # Assign priority ranks
        for i, theme in enumerate(executive_stage4_themes, 1):
            theme['priority_rank'] = i
        
        logger.info(f"✅ Generated {len(executive_stage4_themes)} executive stage4_themes")
        return executive_stage4_themes
    
    def _generate_single_executive_theme(self, theme: pd.Series, scorecard: Dict) -> Optional[Dict]:
        """Generate executive synthesis for a single theme"""
        
        prompt = ChatPromptTemplate.from_template("""
        You are a senior research consultant for Buried Wins, specializing in executive communication for C-suite B2B SaaS clients.
        
        THEME DATA:
        {theme_data}
        
        CRITERIA SCORECARD CONTEXT:
        {scorecard_context}
        
        TASK: Create an executive-ready synthesis that incorporates both theme insights AND criteria performance data.
        
        REQUIREMENTS:
        1. **Punch Then Explain**: Bold headline + concise business narrative
        2. **Data-Anchored**: Include specific metrics from both stage4_themes and criteria scorecard
        3. **Business Tension**: Highlight strategic implications and performance gaps
        4. **Executive Relevance**: Focus on decision-making impact and priority actions
        5. **Criteria Integration**: Reference specific criteria performance where relevant
        
        CRITICAL: You MUST respond with ONLY valid JSON. No additional text, explanations, or formatting outside the JSON structure.
        
        OUTPUT FORMAT (JSON only):
        {{
            "theme_headline": "Executive-ready headline following punch-then-explain principle",
            "narrative_explanation": "2-3 sentence business narrative incorporating criteria performance",
            "business_impact_level": "High|Medium|Emerging",
            "strategic_recommendations": "High-level strategic implications with criteria-specific actions",
            "executive_readiness": "Presentation|Report|Follow-up",
            "criteria_connections": ["List of criteria this theme connects to"],
            "performance_insights": "How this theme relates to criteria performance data"
        }}
        
        IMPORTANT: 
        - Use exact quotes with response_id prefixes
        - Reference specific criteria performance ratings (EXCEPTIONAL, STRONG, GOOD, NEEDS ATTENTION, CRITICAL ISSUE)
        - Connect stage4_themes to criteria scorecard insights
        - Focus on business impact, not technical details
        - Use Buried Wins editorial style: conversational authority, clarity over cleverness, punch then explain
        - RESPOND WITH ONLY THE JSON OBJECT - NO OTHER TEXT
        """)
        
        try:
            result = self.llm.invoke(prompt.format_messages(
                theme_data=self._format_theme_for_llm(theme),
                scorecard_context=self._format_scorecard_for_llm(scorecard)
            ))
            
            # Try to parse JSON with better error handling
            try:
                synthesis = json.loads(result.content)
            except json.JSONDecodeError as json_error:
                logger.warning(f"JSON parsing failed for theme {theme.get('id')}: {json_error}")
                logger.warning(f"LLM response: {result.content[:200]}...")
                
                # Create fallback synthesis structure
                synthesis = {
                    "theme_headline": f"Executive Action Required: {theme.get('theme_statement', 'N/A')[:50]}...",
                    "narrative_explanation": f"Analysis of {theme.get('theme_statement', 'N/A')} with business implications for Rev.",
                    "business_impact_level": "Medium",
                    "strategic_recommendations": "Review theme statement and criteria performance for strategic implications.",
                    "executive_readiness": "Report",
                    "criteria_connections": [],
                    "performance_insights": "Theme requires manual review for performance insights."
                }
            
            # Add metadata
            synthesis['original_theme_id'] = theme.get('id')
            synthesis['priority_score'] = self._calculate_priority_score(theme, scorecard)
            synthesis['theme_category'] = theme.get('theme_category', 'Strategic')
            synthesis['supporting_evidence_summary'] = self._generate_evidence_summary(theme)
            synthesis['competitive_context'] = self._extract_competitive_context(theme, scorecard)
            
            # Add quotes if available
            if theme.get('primary_theme_quote'):
                synthesis['primary_executive_quote'] = theme['primary_theme_quote']
            if theme.get('secondary_theme_quote'):
                synthesis['secondary_executive_quote'] = theme['secondary_theme_quote']
            
            # Generate quote attribution
            synthesis['quote_attribution'] = self._generate_quote_attribution(theme)
            
            return synthesis
            
        except Exception as e:
            logger.error(f"Error generating synthesis: {e}")
            return None
    
    def _format_theme_for_llm(self, theme: pd.Series) -> str:
        """Format theme data for LLM consumption"""
        return f"""
        Theme Statement: {theme.get('theme_statement', 'N/A')}
        Category: {theme.get('theme_category', 'N/A')}
        Strength: {theme.get('theme_strength', 'N/A')}
        Companies: {', '.join(theme.get('interview_companies', []))}
        Business Implications: {theme.get('business_implications', 'N/A')}
        Primary Quote: {theme.get('primary_theme_quote', 'N/A')}
        Secondary Quote: {theme.get('secondary_theme_quote', 'N/A')}
        Competitive Flag: {theme.get('competitive_flag', False)}
        """
    
    def _format_scorecard_for_llm(self, scorecard: Dict) -> str:
        """Format scorecard data for LLM consumption"""
        if not scorecard:
            return "No criteria scorecard data available"
        
        overall = scorecard.get('overall_performance', {})
        criteria_details = scorecard.get('criteria_details', [])
        
        scorecard_text = f"""
        Overall Performance: {overall.get('average_performance_rating', 'N/A')}
        Total Criteria Analyzed: {overall.get('total_criteria_analyzed', 0)}
        Performance Trend: {overall.get('performance_trend', 'N/A')}
        
        Top Performing Criteria: {', '.join(overall.get('top_performing_criteria', []))}
        Critical Attention Needed: {', '.join(overall.get('critical_attention_needed', []))}
        
        Criteria Performance Details:
        """
        
        for criterion in criteria_details[:5]:  # Top 5 criteria
            scorecard_text += f"""
        - {criterion['criterion']}: {criterion['performance_rating']} (Score: {criterion['avg_score']}, Mentions: {criterion['total_mentions']}, Companies: {criterion['companies_affected']})
          Priority: {criterion['executive_priority']}, Urgency: {criterion['action_urgency']}
          Key Insight: {criterion['key_insights']}
            """
        
        return scorecard_text
    
    def _calculate_priority_score(self, theme: pd.Series, scorecard: Dict) -> float:
        """Calculate priority score for executive theme"""
        weights = self.config.get('stage5', {}).get('priority_score_weights', {})
        
        score = 0.0
        
        # Competitive flag weight
        if theme.get('competitive_flag', False):
            score += weights.get('competitive_flag', 3.0)
        
        # Theme strength weight
        strength_scores = {'High': 2.0, 'Medium': 1.5, 'Emerging': 1.0}
        strength = theme.get('theme_strength', 'Medium')
        score += weights.get('theme_strength', 2.0) * strength_scores.get(strength, 1.0)
        
        # Company count weight
        company_count = len(theme.get('interview_companies', []))
        score += weights.get('company_count', 1.5) * min(company_count / 5.0, 1.0)
        
        # Average confidence weight
        avg_confidence = theme.get('avg_confidence_score', 0)
        score += weights.get('avg_confidence', 1.0) * (avg_confidence / 5.0)
        
        # Additional weight for high-impact criteria connections
        criteria_connections = self._identify_criteria_connections(theme, scorecard)
        for criterion in criteria_connections:
            if criterion in scorecard.get('criteria_details', []):
                criterion_data = next((c for c in scorecard['criteria_details'] if c['criterion'] == criterion), None)
                if criterion_data and criterion_data['performance_rating'] in ['CRITICAL ISSUE', 'NEEDS ATTENTION']:
                    score += 1.0
        
        return round(score, 2)
    
    def _identify_criteria_connections(self, theme: pd.Series, scorecard: Dict) -> List[str]:
        """Identify which criteria this theme connects to"""
        theme_statement = theme.get('theme_statement', '').lower()
        connections = []
        
        # Simple keyword matching - could be enhanced with more sophisticated NLP
        criteria_keywords = {
            'product_capability': ['product', 'feature', 'functionality', 'capability', 'performance'],
            'implementation_onboarding': ['implementation', 'onboarding', 'setup', 'deployment', 'ease'],
            'integration_technical_fit': ['integration', 'technical', 'api', 'compatibility', 'fit'],
            'support_service_quality': ['support', 'service', 'quality', 'help', 'assistance'],
            'security_compliance': ['security', 'compliance', 'privacy', 'data', 'protection'],
            'market_position_reputation': ['market', 'position', 'reputation', 'brand', 'trust'],
            'vendor_stability': ['vendor', 'stability', 'financial', 'viability', 'long-term'],
            'sales_experience_partnership': ['sales', 'experience', 'partnership', 'relationship', 'trust'],
            'commercial_terms': ['commercial', 'terms', 'pricing', 'cost', 'roi'],
            'speed_responsiveness': ['speed', 'responsiveness', 'timeline', 'agility', 'fast']
        }
        
        for criterion, keywords in criteria_keywords.items():
            if any(keyword in theme_statement for keyword in keywords):
                connections.append(criterion)
        
        return connections
    
    def _generate_evidence_summary(self, theme: pd.Series) -> str:
        """Generate supporting evidence summary"""
        company_count = len(theme.get('interview_companies', []))
        finding_count = theme.get('finding_count', 0)
        avg_confidence = theme.get('avg_confidence_score', 0)
        
        return f"{company_count} companies, {finding_count} findings, avg confidence {avg_confidence:.1f}"
    
    def _extract_competitive_context(self, theme: pd.Series, scorecard: Dict) -> str:
        """Extract competitive context from theme and scorecard"""
        if not theme.get('competitive_flag', False):
            return "No competitive context identified"
        
        # Look for competitive criteria in scorecard
        competitive_criteria = []
        for criterion in scorecard.get('criteria_details', []):
            if criterion['criterion'] in ['market_position_reputation', 'vendor_stability']:
                if criterion['performance_rating'] in ['NEEDS ATTENTION', 'CRITICAL ISSUE']:
                    competitive_criteria.append(criterion['criterion'])
        
        if competitive_criteria:
            return f"Competitive implications identified in: {', '.join(competitive_criteria)}"
        else:
            return "Competitive theme with no specific criteria issues identified"
    
    def _generate_quote_attribution(self, theme: pd.Series) -> str:
        """Generate quote attribution for executive presentation"""
        companies = theme.get('interview_companies', [])
        if companies:
            return f"Insights from {len(companies)} companies including {companies[0]}"
        else:
            return "Customer insights"
    
    def save_executive_stage4_themes(self, executive_stage4_themes: List[Dict], client_id: str = 'default'):
        """Save executive stage4_themes to Supabase"""
        logger.info("💾 Saving executive stage4_themes to Supabase...")
        
        saved_count = 0
        for theme in executive_stage4_themes:
            theme['client_id'] = client_id  # Add client_id to each theme
            if self.db.save_executive_theme(theme):
                saved_count += 1
                if theme.get('business_impact_level') == 'High':
                    self.processing_metrics["high_impact_stage4_themes"] += 1
                if theme.get('theme_category') == 'Competitive':
                    self.processing_metrics["competitive_stage4_themes"] += 1
        
        logger.info(f"✅ Saved {saved_count} executive stage4_themes to Supabase")
        self.processing_metrics["executive_stage4_themes_generated"] = saved_count
    
    def save_criteria_scorecard(self, scorecard: Dict, client_id: str = 'default'):
        """Save criteria scorecard to Supabase"""
        logger.info("💾 Saving criteria scorecard to Supabase...")
        
        scorecard['client_id'] = client_id  # Add client_id to scorecard
        if self.db.save_criteria_scorecard(scorecard):
            self.processing_metrics["criteria_analyzed"] = len(scorecard.get('criteria_details', []))
            logger.info(f"✅ Saved criteria scorecard with {self.processing_metrics['criteria_analyzed']} criteria")
        else:
            logger.error("❌ Failed to save criteria scorecard")
    
    def process_executive_synthesis(self, client_id: str = 'default') -> Dict:
        """Main processing function for Stage 5"""
        
        logger.info("🚀 STAGE 5: EXECUTIVE SYNTHESIS")
        logger.info("=" * 60)
        
        # Generate criteria scorecard
        logger.info("📊 Generating criteria scorecard...")
        scorecard = self.generate_criteria_scorecard(client_id)
        
        if not scorecard:
            logger.info("✅ No criteria data available for scorecard generation")
            return {"status": "no_criteria_data", "message": "No criteria data available"}
        
        # Save scorecard
        self.save_criteria_scorecard(scorecard, client_id)
        
        # Get stage4_themes for synthesis
        stage4_themes_df = self.get_stage4_themes_for_synthesis(client_id)
        
        if stage4_themes_df.empty:
            logger.info("✅ No stage4_themes available for executive synthesis")
            return {"status": "no_stage4_themes", "message": "No stage4_themes available"}
        
        self.processing_metrics["total_stage4_themes_processed"] = len(stage4_themes_df)
        
        # Generate executive synthesis
        executive_stage4_themes = self.generate_executive_synthesis(stage4_themes_df, scorecard)
        
        if not executive_stage4_themes:
            logger.info("✅ No executive stage4_themes generated")
            return {"status": "no_executive_stage4_themes", "message": "No executive stage4_themes generated"}
        
        # Save executive stage4_themes
        self.save_executive_stage4_themes(executive_stage4_themes, client_id)
        
        # Generate summary
        summary = self.generate_summary_statistics(executive_stage4_themes, scorecard)
        
        logger.info(f"\n✅ Stage 5 complete! Generated {len(executive_stage4_themes)} executive stage4_themes")
        self.print_summary_report(summary)
        
        return {
            "status": "success",
            "stage4_themes_processed": len(stage4_themes_df),
            "executive_stage4_themes_generated": len(executive_stage4_themes),
            "high_impact_stage4_themes": self.processing_metrics["high_impact_stage4_themes"],
            "competitive_stage4_themes": self.processing_metrics["competitive_stage4_themes"],
            "criteria_analyzed": self.processing_metrics["criteria_analyzed"],
            "summary": summary,
            "processing_metrics": self.processing_metrics
        }
    
    def generate_summary_statistics(self, executive_stage4_themes: List[Dict], scorecard: Dict) -> Dict:
        """Generate summary statistics"""
        
        # Executive theme statistics
        impact_distribution = Counter(theme.get('business_impact_level', 'Unknown') for theme in executive_stage4_themes)
        readiness_distribution = Counter(theme.get('executive_readiness', 'Unknown') for theme in executive_stage4_themes)
        category_distribution = Counter(theme.get('theme_category', 'Unknown') for theme in executive_stage4_themes)
        
        # Priority score statistics
        priority_scores = [theme.get('priority_score', 0) for theme in executive_stage4_themes]
        avg_priority_score = sum(priority_scores) / len(priority_scores) if priority_scores else 0
        
        # Scorecard statistics
        overall_performance = scorecard.get('overall_performance', {})
        criteria_details = scorecard.get('criteria_details', [])
        
        return {
            'total_executive_stage4_themes': len(executive_stage4_themes),
            'impact_distribution': dict(impact_distribution),
            'readiness_distribution': dict(readiness_distribution),
            'category_distribution': dict(category_distribution),
            'average_priority_score': round(avg_priority_score, 2),
            'overall_criteria_performance': overall_performance.get('average_performance_rating', 'N/A'),
            'total_criteria_analyzed': len(criteria_details),
            'high_impact_count': self.processing_metrics["high_impact_stage4_themes"],
            'competitive_count': self.processing_metrics["competitive_stage4_themes"]
        }
    
    def print_summary_report(self, summary: Dict):
        """Print a comprehensive summary report"""
        
        logger.info(f"\n📊 STAGE 5 SUMMARY REPORT")
        logger.info("=" * 60)
        logger.info(f"Total executive stage4_themes generated: {summary['total_executive_stage4_themes']}")
        logger.info(f"High impact stage4_themes: {summary['high_impact_count']}")
        logger.info(f"Competitive stage4_themes: {summary['competitive_count']}")
        logger.info(f"Average priority score: {summary['average_priority_score']}")
        logger.info(f"Overall criteria performance: {summary['overall_criteria_performance']}")
        logger.info(f"Total criteria analyzed: {summary['total_criteria_analyzed']}")
        
        logger.info(f"\n📈 BUSINESS IMPACT DISTRIBUTION:")
        for impact, count in summary['impact_distribution'].items():
            logger.info(f"  {impact}: {count}")
        
        logger.info(f"\n🎯 EXECUTIVE READINESS DISTRIBUTION:")
        for readiness, count in summary['readiness_distribution'].items():
            logger.info(f"  {readiness}: {count}")
        
        logger.info(f"\n🏷️ THEME CATEGORY DISTRIBUTION:")
        for category, count in summary['category_distribution'].items():
            logger.info(f"  {category}: {count}")

def run_stage5_analysis(client_id: str = 'default'):
    """Run Stage 5 executive synthesis analysis"""
    analyzer = Stage5ExecutiveAnalyzer()
    return analyzer.process_executive_synthesis(client_id=client_id)

# Run the analysis
if __name__ == "__main__":
    import sys
    
    print("🎯 Stage 5: Executive Synthesis")
    print("=" * 50)
    print("Generating executive synthesis with criteria scorecard...")
    print()
    
    try:
        result = run_stage5_analysis()
        
        if result["status"] == "success":
            print("✅ Stage 5 completed successfully!")
            print(f"📊 Executive stage4_themes generated: {result['executive_stage4_themes_generated']}")
            print(f"🏆 High impact stage4_themes: {result['high_impact_stage4_themes']}")
            print(f"🏅 Competitive stage4_themes: {result['competitive_stage4_themes']}")
            print(f"📋 Criteria analyzed: {result['criteria_analyzed']}")
        else:
            print(f"⚠️ Stage 5 completed with status: {result['status']}")
            print(f"📝 Message: {result.get('message', 'No message provided')}")
            
    except Exception as e:
        print(f"❌ Error running Stage 5: {e}")
        sys.exit(1) 