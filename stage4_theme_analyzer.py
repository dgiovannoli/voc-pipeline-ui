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

class Stage4ThemeAnalyzer:
    """
    Stage 4: Theme Generation - Pattern recognition and executive insights from findings
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
            "total_findings_processed": 0,
            "themes_generated": 0,
            "high_strength_themes": 0,
            "competitive_themes": 0,
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
        """Default configuration for Stage 4"""
        return {
            'stage4': {
                'min_confidence_threshold': 3.0,
                'min_companies_per_theme': 2,
                'min_findings_per_theme': 3,
                'max_themes_per_category': 5,
                'competitive_keywords': [
                    'vs', 'versus', 'compared to', 'alternative', 'competitor',
                    'switching', 'migration', 'evaluation', 'selection process',
                    'vendor', 'solution', 'platform', 'tool'
                ]
            }
        }
    
    def get_findings_for_analysis(self, client_id: str = 'default') -> pd.DataFrame:
        """Get findings from database for theme analysis"""
        df = self.db.get_enhanced_findings(client_id=client_id)
        logger.info(f"📊 Loaded {len(df)} findings from Supabase for client {client_id}")
        return df
    
    def analyze_finding_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze patterns across findings to identify potential themes"""
        logger.info("🔍 Analyzing finding patterns...")
        
        patterns = {}
        
        # Get configuration values with defaults
        stage4_config = self.config.get('stage4', {})
        min_findings = stage4_config.get('min_findings_per_theme', 3)
        min_companies = stage4_config.get('min_companies_per_theme', 2)
        
        # Group by criterion to find patterns
        for criterion in df['criterion'].unique():
            criterion_findings = df[df['criterion'] == criterion]
            
            if len(criterion_findings) < min_findings:
                continue
            
            # Analyze finding types
            finding_types = criterion_findings['finding_type'].value_counts()
            
            # Analyze impact scores
            impact_scores = criterion_findings['impact_score'].tolist()
            avg_impact = sum(impact_scores) / len(impact_scores)
            
            # Extract companies and quotes
            companies = set()
            quotes = []
            finding_ids = []
            
            for _, finding in criterion_findings.iterrows():
                if 'companies_affected' in finding and finding['companies_affected']:
                    companies.add(finding['companies_affected'])
                if 'sample_quotes' in finding and finding['sample_quotes']:
                    quotes.extend(finding['sample_quotes'])
                finding_ids.append(finding['id'])
            
            # Check if pattern meets minimum requirements
            if len(companies) >= min_companies:
                patterns[criterion] = {
                    'finding_count': len(criterion_findings),
                    'company_count': len(companies),
                    'companies': list(companies),
                    'finding_types': finding_types.to_dict(),
                    'avg_impact_score': avg_impact,
                    'quotes': quotes[:5],  # Limit to top 5 quotes
                    'finding_ids': finding_ids,
                    'avg_confidence': criterion_findings['confidence_score'].mean()
                }
        
        logger.info(f"✅ Identified {len(patterns)} potential theme patterns")
        return patterns
    
    def detect_competitive_themes(self, patterns: Dict) -> Dict:
        """Detect competitive themes based on keyword analysis"""
        logger.info("🏆 Detecting competitive themes...")
        
        stage4_config = self.config.get('stage4', {})
        competitive_keywords = stage4_config.get('competitive_keywords', [
            'vs', 'versus', 'compared to', 'alternative', 'competitor',
            'switching', 'migration', 'evaluation', 'selection process',
            'vendor', 'solution', 'platform', 'tool'
        ])
        
        competitive_patterns = {}
        
        for criterion, pattern in patterns.items():
            competitive_score = 0
            
            # Check quotes for competitive keywords
            for quote in pattern['quotes']:
                quote_lower = quote.lower()
                for keyword in competitive_keywords:
                    if keyword in quote_lower:
                        competitive_score += 1
            
            # Check finding descriptions
            findings_df = self.db.get_high_confidence_findings()
            criterion_findings = findings_df[findings_df['criterion'] == criterion]
            
            for _, finding in criterion_findings.iterrows():
                desc_lower = finding['description'].lower()
                for keyword in competitive_keywords:
                    if keyword in desc_lower:
                        competitive_score += 1
            
            # Mark as competitive if score is high enough
            if competitive_score >= 2:
                pattern['competitive_flag'] = True
                pattern['competitive_score'] = competitive_score
                competitive_patterns[criterion] = pattern
            else:
                pattern['competitive_flag'] = False
                pattern['competitive_score'] = competitive_score
        
        logger.info(f"✅ Identified {len(competitive_patterns)} competitive themes")
        return patterns
    
    def generate_theme_statements(self, patterns: Dict) -> List[Dict]:
        """Generate theme statements using LLM"""
        logger.info("📝 Generating theme statements...")
        
        themes = []
        
        for criterion, pattern in patterns.items():
            # Prepare data for LLM
            finding_summary = []
            for finding_type, count in pattern['finding_types'].items():
                finding_summary.append(f"- {finding_type}: {count} findings")
            
            quote_examples = "\n".join([f"'{quote[:200]}...'" for quote in pattern['quotes'][:3]])
            
            prompt = ChatPromptTemplate.from_template("""
            Generate an executive-ready theme statement based on this pattern analysis:
            
            CRITERION: {criterion}
            COMPANIES: {companies}
            FINDING TYPES: {finding_types}
            AVERAGE IMPACT SCORE: {avg_impact}
            COMPETITIVE FLAG: {competitive_flag}
            
            SAMPLE QUOTES:
            {quotes}
            
            REQUIREMENTS:
            - Write 1-2 sentences maximum
            - Focus on business implications
            - Use executive language
            - Be specific and actionable
            - If competitive, mention competitive context
            
            OUTPUT: Just the theme statement, no additional formatting.
            """)
            
            try:
                result = self.llm.invoke(prompt.format_messages(
                    criterion=criterion,
                    companies=", ".join(pattern['companies']),
                    finding_types="\n".join(finding_summary),
                    avg_impact=f"{pattern['avg_impact_score']:.1f}",
                    competitive_flag="Yes" if pattern.get('competitive_flag', False) else "No",
                    quotes=quote_examples
                ))
                
                theme_statement = result.content.strip()
                
                # Determine theme strength
                if pattern['company_count'] >= 4 and pattern['avg_impact_score'] >= 3.5:
                    theme_strength = "High"
                elif pattern['company_count'] >= 2 and pattern['avg_impact_score'] >= 2.5:
                    theme_strength = "Medium"
                else:
                    theme_strength = "Emerging"
                
                # Determine theme category
                if pattern.get('competitive_flag', False):
                    theme_category = "Competitive"
                elif pattern['avg_impact_score'] >= 3.5:
                    theme_category = "Opportunity"
                elif pattern['avg_impact_score'] <= 2.0:
                    theme_category = "Barrier"
                else:
                    theme_category = "Strategic"
                
                theme = {
                    'theme_statement': theme_statement,
                    'theme_category': theme_category,
                    'theme_strength': theme_strength,
                    'interview_companies': pattern['companies'],
                    'supporting_finding_ids': pattern['finding_ids'],
                    'supporting_response_ids': [],  # Will be populated from findings
                    'deal_status_distribution': {"won": 0, "lost": 0},  # Placeholder
                    'competitive_flag': pattern.get('competitive_flag', False),
                    'business_implications': f"Impact score: {pattern['avg_impact_score']:.1f}, affecting {pattern['company_count']} companies",
                    'primary_theme_quote': pattern['quotes'][0] if pattern['quotes'] else "",
                    'secondary_theme_quote': pattern['quotes'][1] if len(pattern['quotes']) > 1 else "",
                    'quote_attributions': f"Primary: {pattern['companies'][0] if pattern['companies'] else 'Unknown'}",
                    'evidence_strength': theme_strength,
                    'avg_confidence_score': pattern['avg_confidence'],
                    'company_count': pattern['company_count'],
                    'finding_count': pattern['finding_count']
                }
                
                themes.append(theme)
                
            except Exception as e:
                logger.error(f"❌ Error generating theme for {criterion}: {e}")
                self.processing_metrics["processing_errors"] += 1
        
        logger.info(f"✅ Generated {len(themes)} theme statements")
        return themes
    
    def save_themes_to_supabase(self, themes: List[Dict], client_id: str = 'default'):
        """Save themes to Supabase"""
        logger.info("💾 Saving themes to Supabase...")
        
        saved_count = 0
        for theme in themes:
            theme['client_id'] = client_id  # Add client_id to each theme
            if self.db.save_theme(theme):
                saved_count += 1
                if theme['theme_strength'] == 'High':
                    self.processing_metrics["high_strength_themes"] += 1
                if theme['competitive_flag']:
                    self.processing_metrics["competitive_themes"] += 1
        
        logger.info(f"✅ Saved {saved_count} themes to Supabase for client {client_id}")
        self.processing_metrics["themes_generated"] = saved_count
    
    def process_themes(self, client_id: str = 'default') -> Dict:
        """Main processing function for Stage 4"""
        
        logger.info("🚀 STAGE 4: THEME GENERATION")
        logger.info("=" * 60)
        
        # Get findings for analysis
        df = self.get_findings_for_analysis(client_id=client_id)
        
        if df.empty:
            logger.info("✅ No findings available for theme generation")
            return {"status": "no_data", "message": "No findings available"}
        
        self.processing_metrics["total_findings_processed"] = len(df)
        
        # Analyze patterns
        patterns = self.analyze_finding_patterns(df)
        
        if not patterns:
            logger.info("✅ No patterns found meeting minimum requirements")
            return {"status": "no_patterns", "message": "No patterns found"}
        
        # Detect competitive themes
        patterns = self.detect_competitive_themes(patterns)
        
        # Generate theme statements
        themes = self.generate_theme_statements(patterns)
        
        if not themes:
            logger.info("✅ No themes generated")
            return {"status": "no_themes", "message": "No themes generated"}
        
        # Save to Supabase
        self.save_themes_to_supabase(themes, client_id=client_id)
        
        # Generate summary
        summary = self.generate_summary_statistics(themes)
        
        logger.info(f"\n✅ Stage 4 complete! Generated {len(themes)} themes")
        self.print_summary_report(summary)
        
        return {
            "status": "success",
            "findings_processed": len(df),
            "themes_generated": len(themes),
            "high_strength_themes": self.processing_metrics["high_strength_themes"],
            "competitive_themes": self.processing_metrics["competitive_themes"],
            "summary": summary,
            "processing_metrics": self.processing_metrics
        }
    
    def generate_summary_statistics(self, themes: List[Dict]) -> Dict:
        """Generate summary statistics"""
        
        # Theme strength distribution
        strength_distribution = Counter(theme['theme_strength'] for theme in themes)
        
        # Theme category distribution
        category_distribution = Counter(theme['theme_category'] for theme in themes)
        
        # Company coverage
        all_companies = set()
        for theme in themes:
            all_companies.update(theme['interview_companies'])
        
        # Average confidence and impact
        avg_confidence = sum(theme['avg_confidence_score'] for theme in themes) / len(themes) if themes else 0
        
        return {
            'total_themes': len(themes),
            'strength_distribution': dict(strength_distribution),
            'category_distribution': dict(category_distribution),
            'companies_covered': len(all_companies),
            'average_confidence': avg_confidence,
            'high_strength_count': self.processing_metrics["high_strength_themes"],
            'competitive_count': self.processing_metrics["competitive_themes"]
        }
    
    def print_summary_report(self, summary: Dict):
        """Print a comprehensive summary report"""
        
        logger.info(f"\n📊 STAGE 4 SUMMARY REPORT")
        logger.info("=" * 60)
        logger.info(f"Total themes generated: {summary['total_themes']}")
        logger.info(f"High strength themes: {summary['high_strength_count']}")
        logger.info(f"Competitive themes: {summary['competitive_count']}")
        logger.info(f"Companies covered: {summary['companies_covered']}")
        logger.info(f"Average confidence: {summary['average_confidence']:.2f}")
        
        logger.info(f"\n📈 THEME STRENGTH DISTRIBUTION:")
        for strength, count in summary['strength_distribution'].items():
            logger.info(f"  {strength}: {count}")
        
        logger.info(f"\n🎯 THEME CATEGORY DISTRIBUTION:")
        for category, count in summary['category_distribution'].items():
            logger.info(f"  {category}: {count}")

def run_stage4_analysis(client_id: str = 'default'):
    """Run Stage 4 theme analysis"""
    analyzer = Stage4ThemeAnalyzer()
    return analyzer.process_themes(client_id=client_id)

# Run the analysis
if __name__ == "__main__":
    print("🔍 Running Stage 4: Theme Generation...")
    result = run_stage4_analysis()
    print(f"✅ Stage 4 complete: {result}") 