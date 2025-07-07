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
import re
from difflib import SequenceMatcher

# Import Supabase database manager
from supabase_database import SupabaseDatabase

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Stage4ThemeAnalyzer:
    """
    Stage 4: Enhanced Theme Generation - Fuzzy matching and semantic grouping for executive insights
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
            "fuzzy_grouped_themes": 0,
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
        """Default configuration for Stage 4 with fuzzy matching"""
        return {
            'stage4': {
                'min_confidence_threshold': 3.0,
                'min_companies_per_theme': 1,
                'min_findings_per_theme': 1,
                'max_themes_per_category': 5,
                'fuzzy_matching': {
                    'similarity_threshold': 0.7,
                    'semantic_grouping': True,
                    'cross_criteria_grouping': True
                },
                'competitive_keywords': [
                    'vs', 'versus', 'compared to', 'alternative', 'competitor',
                    'switching', 'migration', 'evaluation', 'selection process',
                    'vendor', 'solution', 'platform', 'tool'
                ]
            }
        }
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts using fuzzy matching"""
        if not text1 or not text2:
            return 0.0
        
        # Normalize texts
        text1_clean = re.sub(r'[^\w\s]', '', text1.lower())
        text2_clean = re.sub(r'[^\w\s]', '', text2.lower())
        
        # Use SequenceMatcher for fuzzy string matching
        similarity = SequenceMatcher(None, text1_clean, text2_clean).ratio()
        
        # Additional semantic checks for common business terms
        semantic_mappings = {
            'product': ['capability', 'feature', 'functionality', 'solution'],
            'integration': ['technical', 'fit', 'compatibility', 'api'],
            'security': ['privacy', 'compliance', 'data', 'protection'],
            'support': ['service', 'help', 'assistance', 'quality'],
            'implementation': ['onboarding', 'setup', 'deployment', 'rollout'],
            'commercial': ['pricing', 'cost', 'terms', 'roi'],
            'speed': ['responsiveness', 'timeline', 'agility', 'efficiency']
        }
        
        # Check semantic mappings
        for primary, related in semantic_mappings.items():
            if primary in text1_clean and any(term in text2_clean for term in related):
                similarity += 0.2
            elif primary in text2_clean and any(term in text1_clean for term in related):
                similarity += 0.2
        
        return min(similarity, 1.0)
    
    def group_findings_by_semantic_similarity(self, findings_df: pd.DataFrame) -> List[List[Dict]]:
        """Group findings by semantic similarity across criteria"""
        logger.info("🔍 Grouping findings by semantic similarity...")
        
        stage4_config = self.config.get('stage4', {})
        fuzzy_config = stage4_config.get('fuzzy_matching', {})
        similarity_threshold = fuzzy_config.get('similarity_threshold', 0.7)
        
        findings_list = findings_df.to_dict('records')
        grouped_findings = []
        processed = set()
        
        for i, finding1 in enumerate(findings_list):
            if i in processed:
                continue
            
            current_group = [finding1]
            processed.add(i)
            
            # Compare with other findings
            for j, finding2 in enumerate(findings_list[i+1:], i+1):
                if j in processed:
                    continue
                
                # Calculate similarity between findings
                desc1 = finding1.get('description', '')
                desc2 = finding2.get('description', '')
                
                similarity = self.calculate_semantic_similarity(desc1, desc2)
                
                if similarity >= similarity_threshold:
                    current_group.append(finding2)
                    processed.add(j)
            
            if len(current_group) > 1:
                grouped_findings.append(current_group)
                logger.info(f"✅ Grouped {len(current_group)} findings with similarity {similarity:.2f}")
        
        logger.info(f"✅ Created {len(grouped_findings)} semantic groups")
        return grouped_findings
    
    def get_findings_for_analysis(self, client_id: str = 'default') -> pd.DataFrame:
        """Get findings from database for theme analysis"""
        df = self.db.get_enhanced_findings(client_id=client_id)
        logger.info(f"📊 Loaded {len(df)} findings from Supabase for client {client_id}")
        return df
    
    def analyze_finding_patterns(self, df: pd.DataFrame, client_id: str = 'default') -> Dict:
        """Analyze patterns across findings to identify potential themes using fuzzy matching and semantic grouping"""
        logger.info("🔍 Analyzing finding patterns with fuzzy matching...")
        
        # Load core_responses for interviewee_name lookup
        core_df = self.db.get_core_responses(client_id=client_id)
        
        patterns = {}
        
        # Get configuration values with defaults
        stage4_config = self.config.get('stage4', {})
        min_findings = stage4_config.get('min_findings_per_theme', 1)
        min_companies = stage4_config.get('min_companies_per_theme', 1)
        fuzzy_config = stage4_config.get('fuzzy_matching', {})
        semantic_grouping = fuzzy_config.get('semantic_grouping', True)
        cross_criteria_grouping = fuzzy_config.get('cross_criteria_grouping', True)
        
        # NEW: Group findings by semantic similarity first
        semantic_groups = []
        if semantic_grouping and cross_criteria_grouping:
            semantic_groups = self.group_findings_by_semantic_similarity(df)
        
        # Process semantic groups for cross-criteria themes
        for group_idx, finding_group in enumerate(semantic_groups):
            if len(finding_group) < min_findings:
                continue
            
            # Analyze the group as a potential cross-criteria theme
            group_pattern = self._analyze_finding_group(finding_group, core_df, f"semantic_group_{group_idx}")
            
            if group_pattern and group_pattern['company_count'] >= min_companies:
                patterns[f"semantic_group_{group_idx}"] = group_pattern
        
        # Process individual criteria patterns (existing logic)
        for criterion in df['criterion'].unique():
            criterion_findings = df[df['criterion'] == criterion]
            
            if len(criterion_findings) < min_findings:
                continue
            
            # Analyze finding types
            finding_types = criterion_findings['finding_type'].value_counts()
            
            # Analyze impact scores
            impact_scores = criterion_findings['impact_score'].tolist()
            # Cap all impact scores at 5 and warn if any > 5
            capped_scores = []
            for s in impact_scores:
                if s > 5:
                    logger.warning(f"Impact score > 5 found in findings: {s}. Capping to 5.")
                    capped_scores.append(5.0)
                else:
                    capped_scores.append(max(s, 0))
            avg_impact = sum(capped_scores) / len(capped_scores) if capped_scores else 0
            avg_impact = min(avg_impact, 5.0)
            
            # Extract interviewee_names and quotes (collect full quote objects)
            interviewees = set()
            quotes = []
            finding_ids = []
            for _, finding in criterion_findings.iterrows():
                if 'selected_quotes' in finding and finding['selected_quotes']:
                    for quote_obj in finding['selected_quotes']:
                        # If it's a dict, keep the full object for UI
                        if isinstance(quote_obj, dict):
                            quotes.append(quote_obj)
                            # Try to match interviewee_name by text if possible
                            quote_text = quote_obj.get('text', '')
                            match = core_df[core_df['verbatim_response'].str.startswith(quote_text[:30])]
                            if not match.empty:
                                interviewees.add(match.iloc[0]['interviewee_name'])
                        elif isinstance(quote_obj, str):
                            quotes.append({'text': quote_obj})
                            match = core_df[core_df['verbatim_response'].str.startswith(quote_obj[:30])]
                            if not match.empty:
                                interviewees.add(match.iloc[0]['interviewee_name'])
                finding_ids.append(finding['id'])
            
            # Check if pattern meets minimum requirements
            if len(interviewees) >= min_companies:
                # CRITICAL FIX: Ensure pattern has at least one quote
                if not quotes:
                    logger.warning(f"⚠️ Skipping theme pattern for {criterion} - no quotes found")
                    continue
                
                patterns[criterion] = {
                    'finding_count': len(criterion_findings),
                    'company_count': len(interviewees),
                    'companies': list(interviewees),
                    'finding_types': finding_types.to_dict(),
                    'avg_impact_score': avg_impact,
                    'quotes': quotes[:5],  # Limit to top 5 quote objects
                    'finding_ids': finding_ids,
                    'avg_confidence': criterion_findings['enhanced_confidence'].mean(),
                    'pattern_type': 'criterion_based'
                }
        
        logger.info(f"✅ Identified {len(patterns)} potential theme patterns (including {len([p for p in patterns.values() if p.get('pattern_type') == 'semantic_group'])} semantic groups)")
        return patterns
    
    def _analyze_finding_group(self, finding_group: List[Dict], core_df: pd.DataFrame, group_name: str) -> Optional[Dict]:
        """Analyze a group of findings for cross-criteria patterns"""
        
        # Extract interviewee_names and quotes
        interviewees = set()
        quotes = []
        finding_ids = []
        criteria_covered = set()
        impact_scores = []
        confidence_scores = []
        
        for finding in finding_group:
            finding_ids.append(finding['id'])
            criteria_covered.add(finding['criterion'])
            impact_scores.append(min(finding.get('impact_score', 0), 5.0))
            confidence_scores.append(finding.get('enhanced_confidence', 0))
            
            # Extract quotes
            if 'selected_quotes' in finding and finding['selected_quotes']:
                for quote_obj in finding['selected_quotes']:
                    if isinstance(quote_obj, dict):
                        quotes.append(quote_obj)
                        quote_text = quote_obj.get('text', '')
                        match = core_df[core_df['verbatim_response'].str.startswith(quote_text[:30])]
                        if not match.empty:
                            interviewees.add(match.iloc[0]['interviewee_name'])
                    elif isinstance(quote_obj, str):
                        quotes.append({'text': quote_obj})
                        match = core_df[core_df['verbatim_response'].str.startswith(quote_obj[:30])]
                        if not match.empty:
                            interviewees.add(match.iloc[0]['interviewee_name'])
        
        if not quotes:
            return None
        
        avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        return {
            'finding_count': len(finding_group),
            'company_count': len(interviewees),
            'companies': list(interviewees),
            'criteria_covered': list(criteria_covered),
            'avg_impact_score': avg_impact,
            'quotes': quotes[:5],
            'finding_ids': finding_ids,
            'avg_confidence': avg_confidence,
            'pattern_type': 'semantic_group',
            'group_name': group_name
        }
    
    def detect_competitive_themes(self, patterns: Dict, client_id: str = 'default') -> Dict:
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
                # Handle both string and dict quote objects
                if isinstance(quote, dict):
                    quote_text = quote.get('text', '')
                else:
                    quote_text = str(quote)
                
                quote_lower = quote_text.lower()
                for keyword in competitive_keywords:
                    if keyword in quote_lower:
                        competitive_score += 1
            
            # Check finding descriptions
            findings_df = self.db.get_enhanced_findings(client_id=client_id)  # Use client_id
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
        """Generate theme statements using LLM with enhanced fuzzy matching support"""
        logger.info("📝 Generating theme statements with fuzzy matching...")
        
        themes = []
        
        for pattern_key, pattern in patterns.items():
            # CRITICAL FIX: Ensure pattern has at least one quote before generating theme
            if not pattern.get('quotes'):
                logger.warning(f"⚠️ Skipping theme generation for {pattern_key} - no quotes found in pattern")
                continue
            
            # Generate theme statement based on pattern type
            if pattern.get('pattern_type') == 'semantic_group':
                theme_statement = self._generate_cross_criteria_theme(pattern, pattern_key)
            else:
                theme_statement = self._generate_criterion_theme(pattern, pattern_key)
            
            if not theme_statement:
                continue
            
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
            
            # Extract quote text for database storage
            primary_quote_text = ""
            secondary_quote_text = ""
            
            if pattern['quotes']:
                primary_quote = pattern['quotes'][0]
                if isinstance(primary_quote, dict):
                    primary_quote_text = primary_quote.get('text', '')
                else:
                    primary_quote_text = str(primary_quote)
            
            if len(pattern['quotes']) > 1:
                secondary_quote = pattern['quotes'][1]
                if isinstance(secondary_quote, dict):
                    secondary_quote_text = secondary_quote.get('text', '')
                else:
                    secondary_quote_text = str(secondary_quote)
            
            # Create theme object
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
                'primary_theme_quote': primary_quote_text,
                'secondary_theme_quote': secondary_quote_text,
                'quote_attributions': f"Primary: {pattern['companies'][0] if pattern['companies'] else 'Unknown'}",
                'evidence_strength': theme_strength,
                'avg_confidence_score': pattern['avg_confidence'],
                'company_count': pattern['company_count'],
                'finding_count': pattern['finding_count'],
                'quotes': json.dumps(pattern['quotes']),
                'pattern_type': pattern.get('pattern_type', 'criterion_based')
            }
            
            # Add cross-criteria information for semantic groups
            if pattern.get('pattern_type') == 'semantic_group':
                theme['criteria_covered'] = pattern.get('criteria_covered', [])
                theme['fuzzy_grouped'] = True
                self.processing_metrics["fuzzy_grouped_themes"] += 1
            
            themes.append(theme)
        
        logger.info(f"✅ Generated {len(themes)} theme statements (including {self.processing_metrics['fuzzy_grouped_themes']} fuzzy grouped)")
        return themes
    
    def _generate_cross_criteria_theme(self, pattern: Dict, pattern_key: str) -> Optional[str]:
        """Generate theme statement for cross-criteria semantic groups"""
        
        # Prepare finding summary
        criteria_covered = pattern.get('criteria_covered', [])
        criteria_summary = ", ".join(criteria_covered)
        
        # Handle quote objects properly
        quote_examples = []
        for quote in pattern['quotes'][:3]:
            if isinstance(quote, dict):
                quote_text = quote.get('text', '')
            else:
                quote_text = str(quote)
            quote_examples.append(f"'{quote_text[:200]}...'")
        quote_examples = "\n".join(quote_examples)
        
        prompt = ChatPromptTemplate.from_template("""
        Generate an executive-ready theme statement for a cross-criteria pattern that spans multiple business areas:
        
        CRITERIA COVERED: {criteria_covered}
        COMPANIES: {companies}
        FINDING COUNT: {finding_count}
        AVERAGE IMPACT SCORE: {avg_impact}
        COMPETITIVE FLAG: {competitive_flag}
        
        SAMPLE QUOTES:
        {quotes}
        
        REQUIREMENTS:
        - Write 1-2 sentences maximum
        - Focus on the broader business implications that span multiple criteria
        - Use executive language that connects the dots across different areas
        - Be specific about the cross-functional impact
        - If competitive, mention competitive context
        - Emphasize the strategic significance of this cross-criteria pattern
        
        OUTPUT: Just the theme statement, no additional formatting.
        """)
        
        try:
            result = self.llm.invoke(prompt.format_messages(
                criteria_covered=criteria_summary,
                companies=", ".join(pattern['companies']),
                finding_count=pattern['finding_count'],
                avg_impact=f"{pattern['avg_impact_score']:.1f}",
                competitive_flag="Yes" if pattern.get('competitive_flag', False) else "No",
                quotes=quote_examples
            ))
            
            return result.content.strip()
            
        except Exception as e:
            logger.error(f"❌ Error generating cross-criteria theme for {pattern_key}: {e}")
            self.processing_metrics["processing_errors"] += 1
            return None
    
    def _generate_criterion_theme(self, pattern: Dict, pattern_key: str) -> Optional[str]:
        """Generate theme statement for single-criterion patterns"""
        
        # Prepare finding summary
        finding_summary = []
        for finding_type, count in pattern['finding_types'].items():
            finding_summary.append(f"- {finding_type}: {count} findings")
        
        # Handle quote objects properly
        quote_examples = []
        for quote in pattern['quotes'][:3]:
            if isinstance(quote, dict):
                quote_text = quote.get('text', '')
            else:
                quote_text = str(quote)
            quote_examples.append(f"'{quote_text[:200]}...'")
        quote_examples = "\n".join(quote_examples)
        
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
                criterion=pattern_key,
                companies=", ".join(pattern['companies']),
                finding_types="\n".join(finding_summary),
                avg_impact=f"{pattern['avg_impact_score']:.1f}",
                competitive_flag="Yes" if pattern.get('competitive_flag', False) else "No",
                quotes=quote_examples
            ))
            
            return result.content.strip()
            
        except Exception as e:
            logger.error(f"❌ Error generating criterion theme for {pattern_key}: {e}")
            self.processing_metrics["processing_errors"] += 1
            return None
    
    def save_themes_to_supabase(self, themes: List[Dict], client_id: str = 'default'):
        """Save themes to Supabase"""
        logger.info("💾 Saving themes to Supabase...")
        
        saved_count = 0
        for theme in themes:
            # CRITICAL FIX: Ensure theme has at least one quote before saving
            if not theme.get('primary_theme_quote'):
                logger.warning(f"⚠️ Skipping theme save - no primary_theme_quote found")
                continue
            
            theme['client_id'] = client_id  # Add client_id to each theme
            if self.db.save_theme(theme, client_id=client_id):
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
        patterns = self.analyze_finding_patterns(df, client_id=client_id)
        
        if not patterns:
            logger.info("✅ No patterns found meeting minimum requirements")
            return {"status": "no_patterns", "message": "No patterns found"}
        
        # Detect competitive themes
        patterns = self.detect_competitive_themes(patterns, client_id=client_id)
        
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
        """Print a comprehensive summary report with fuzzy matching metrics"""
        
        logger.info(f"\n📊 STAGE 4 SUMMARY REPORT (Enhanced with Fuzzy Matching)")
        logger.info("=" * 70)
        logger.info(f"Total themes generated: {summary['total_themes']}")
        logger.info(f"High strength themes: {summary['high_strength_count']}")
        logger.info(f"Competitive themes: {summary['competitive_count']}")
        logger.info(f"Fuzzy grouped themes: {self.processing_metrics['fuzzy_grouped_themes']}")
        logger.info(f"Companies covered: {summary['companies_covered']}")
        logger.info(f"Average confidence: {summary['average_confidence']:.2f}")
        
        logger.info(f"\n📈 THEME STRENGTH DISTRIBUTION:")
        for strength, count in summary['strength_distribution'].items():
            logger.info(f"  {strength}: {count}")
        
        logger.info(f"\n🎯 THEME CATEGORY DISTRIBUTION:")
        for category, count in summary['category_distribution'].items():
            logger.info(f"  {category}: {count}")
        
        logger.info(f"\n🔍 FUZZY MATCHING PERFORMANCE:")
        logger.info(f"  Semantic groups created: {self.processing_metrics['fuzzy_grouped_themes']}")
        logger.info(f"  Cross-criteria themes: {self.processing_metrics['fuzzy_grouped_themes']}")
        logger.info(f"  Processing errors: {self.processing_metrics['processing_errors']}")
        
        logger.info(f"\n💡 ENHANCED FEATURES:")
        logger.info("  ✅ Fuzzy matching for semantic similarity")
        logger.info("  ✅ Cross-criteria theme generation")
        logger.info("  ✅ Enhanced business narratives")
        logger.info("  ✅ Improved quote attribution")

def run_stage4_analysis(client_id: str = 'default'):
    """Run Stage 4 theme analysis"""
    analyzer = Stage4ThemeAnalyzer()
    return analyzer.process_themes(client_id=client_id)

# Run the analysis
if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    client_id = 'default'
    if '--client_id' in sys.argv:
        try:
            client_id_index = sys.argv.index('--client_id')
            if client_id_index + 1 < len(sys.argv):
                client_id = sys.argv[client_id_index + 1]
        except (ValueError, IndexError):
            pass
    
    print(f"🔍 Running Stage 4: Theme Generation for client '{client_id}'...")
    result = run_stage4_analysis(client_id=client_id)
    print(f"✅ Stage 4 complete: {result}") 