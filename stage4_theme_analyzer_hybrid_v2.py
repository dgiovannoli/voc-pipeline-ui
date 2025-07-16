#!/usr/bin/env python3
"""
Stage 4 Theme Analyzer - Hybrid V2 Approach
Combines depth of hybrid with cross-company validation strength of V2
"""

import os
import json
import logging
import pandas as pd
import re
from typing import List, Dict, Any
import openai
from supabase_database import SupabaseDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Stage4ThemeAnalyzerHybridV2:
    def __init__(self, client_id: str = "Rev"):
        self.client_id = client_id
        self.supabase = SupabaseDatabase()
        
        # Load OpenAI API key
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.openai_api_key)
    
    def _get_findings_json(self) -> str:
        """Convert findings to JSON format for LLM processing"""
        try:
            # Get findings from database
            findings = self.supabase.get_stage3_findings_list(self.client_id)
            
            if not findings:
                logger.warning(f"No Stage 3 findings found for client {self.client_id}")
                return ""
            
            # Convert to JSON format
            findings_json = json.dumps(findings, indent=2)
            logger.info(f"📊 Prepared {len(findings)} findings in JSON format")
            
            return findings_json
            
        except Exception as e:
            logger.error(f"❌ Error getting findings JSON: {e}")
            return ""
    
    def _identify_company_field(self, df: pd.DataFrame) -> str:
        """Identify the company identifier field in the findings data"""
        company_fields = ['interview_company', 'company', 'organization', 'firm']
        
        for field in company_fields:
            if field in df.columns:
                unique_companies = df[field].dropna().unique()
                if len(unique_companies) > 1:
                    logger.info(f"Identified {field} as the company identifier with {len(unique_companies)} unique companies")
                    return field
        
        logger.warning("No clear company identifier found")
        return "interview_company"  # Default fallback
    
    def _call_stage4a_pattern_identification(self, findings_json: str) -> str:
        """Stage 4A: Identify broad patterns with STRONG cross-company validation"""
        try:
            pattern_prompt = f"""
You are an expert qualitative research analyst specializing in B2B SaaS competitive intelligence.

TASK: Identify 12-18 broad patterns from the provided findings data with STRONG cross-company validation.

PATTERN IDENTIFICATION REQUIREMENTS:
- Focus on identifying high-level themes that span multiple companies
- Look for recurring business challenges, opportunities, and competitive dynamics
- **CRITICAL: Each pattern MUST be supported by findings from 3+ companies**
- Patterns should be business-focused, not technical features
- Avoid solutioning language - describe what is happening, not what should be done

FINDINGS DATA:
{findings_json}

OUTPUT FORMAT:
Return a JSON object with this structure:
{{
  "patterns": [
    {{
      "pattern_id": "P1",
      "pattern_title": "Subscription Model Resistance",
      "pattern_description": "Broad description of the pattern across companies",
      "supporting_finding_ids": ["F1", "F2", "F3"],
      "company_count": 3,
      "business_impact": "COMPETITIVE VULNERABILITY|REVENUE THREAT|MARKET OPPORTUNITY"
    }}
  ]
}}

CRITICAL REQUIREMENTS:
- Use ONLY finding IDs from the provided data (F1, F2, F3, etc.)
- **EACH PATTERN MUST HAVE FINDINGS FROM AT LEAST 3 DIFFERENT COMPANIES**
- Focus on business impact and competitive dynamics
- Avoid generic patterns - be specific about the business implications
- Generate 12-18 patterns for comprehensive coverage

Return ONLY the JSON object, no explanations.
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert business analyst specializing in pattern identification from customer research data with strong cross-company validation."},
                    {"role": "user", "content": pattern_prompt}
                ],
                temperature=0.2,
                max_tokens=4000
            )
            
            llm_output = response.choices[0].message.content.strip()
            logger.info(f"✅ Stage 4A: Pattern identification completed")
            
            return llm_output
            
        except Exception as e:
            logger.error(f"❌ Error in Stage 4A pattern identification: {e}")
            return ""
    
    def _call_stage4b_theme_development(self, patterns_json: str, findings_json: str) -> str:
        """Stage 4B: Develop comprehensive themes from validated patterns"""
        try:
            theme_prompt = f"""
You are an expert qualitative research analyst specializing in B2B SaaS competitive intelligence.

TASK: Develop comprehensive themes and strategic alerts from the identified patterns.

PATTERNS DATA:
{patterns_json}

FINDINGS DATA:
{findings_json}

COMPREHENSIVE THEME REQUIREMENTS:
- Generate 2-3 detailed themes for each pattern (aim for 15-25 total themes)
- Each theme should be 50-75 words with cross-company validation
- Include specific business insights and competitive dynamics
- Use concrete examples from the findings
- AVOID solutioning language - describe what is happening, not what should be done
- Focus on business impact: revenue threats, competitive vulnerabilities, market opportunities

STRATEGIC ALERT REQUIREMENTS:
- Identify high-impact findings requiring immediate attention
- Focus on revenue threats, competitive vulnerabilities, market opportunities
- Include specific strategic implications
- Use findings from single companies with high business impact

OUTPUT FORMAT:
Return a JSON object with this structure:
{{
  "themes": [
    {{
      "theme_id": "T1",
      "theme_title": "Subscription Fatigue Barrier",
      "theme_statement": "Subscription fatigue creates significant adoption barriers across 3 companies, with 80% of potential customers citing monthly fee accumulation as a primary concern during evaluation processes. This pattern reveals a fundamental market vulnerability where pricing models directly impact competitive positioning and customer acquisition success rates in the legal software sector.",
      "classification": "COMPETITIVE VULNERABILITY",
      "deal_context": "Won: 1, Lost: 0",
      "metadata_insights": "",
      "primary_quote": "",
      "secondary_quote": "",
      "competitive_flag": false,
      "supporting_finding_ids": "F25",
      "company_ids": ""
    }}
  ],
  "strategic_alerts": [
    {{
      "alert_id": "A1",
      "alert_title": "Urgent Need for Improved Legal Process Navigation",
      "alert_statement": "Client satisfaction deteriorates systematically across 4 organizations when legal process navigation delays exceed two weeks, with 90% of affected customers reporting unclear procedural guidance as the root cause. This operational pattern demonstrates how process complexity directly impacts competitive positioning and customer retention in high-stakes legal environments.",
      "alert_classification": "REVENUE THREAT",
      "strategic_implications": "This alert highlights the potential for revenue loss if client satisfaction continues to deteriorate due to navigational inefficiencies.",
      "primary_alert_quote": "",
      "secondary_alert_quote": "",
      "supporting_alert_finding_ids": "F6",
      "alert_company_ids": ""
    }}
  ]
}}

CRITICAL REQUIREMENTS:
- Use ONLY finding IDs from the provided data
- Leave all quote fields empty ("") - they will be populated by the system
- Every theme must include cross-company validation (e.g., "across 3 companies")
- Theme statements must be 50-75 words
- NO solutioning language (no "indicating", "suggesting", "should", "must", etc.)
- Generate comprehensive coverage (15-25 themes, 5-8 alerts)
- Each theme/alert should have unique business insights

Return ONLY the JSON object, no explanations.
"""

            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4o for higher quality theme development
                messages=[
                    {"role": "system", "content": "You are an expert business analyst specializing in comprehensive theme development and strategic analysis with high-quality language."},
                    {"role": "user", "content": theme_prompt}
                ],
                temperature=0.1,
                max_tokens=6000  # Increased for comprehensive output
            )
            
            llm_output = response.choices[0].message.content.strip()
            logger.info(f"✅ Stage 4B: Theme development completed")
            
            return llm_output
            
        except Exception as e:
            logger.error(f"❌ Error in Stage 4B theme development: {e}")
            return ""
    
    def _parse_themes_output(self, llm_output: str) -> List[Dict]:
        """Parse themes and alerts from LLM JSON output"""
        try:
            # Extract JSON from LLM output
            json_start = llm_output.find('{')
            json_end = llm_output.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("No JSON found in LLM output")
                return []
            
            json_str = llm_output[json_start:json_end]
            
            # Parse JSON
            data = json.loads(json_str)
            
            themes = []
            
            # Process themes
            if 'themes' in data:
                for theme in data['themes']:
                    theme['theme_type'] = 'theme'
                    themes.append(theme)
            
            # Process strategic alerts
            if 'strategic_alerts' in data:
                for alert in data['strategic_alerts']:
                    alert['theme_type'] = 'strategic_alert'
                    themes.append(alert)
            
            logger.info(f"✅ Parsed {len(themes)} themes/alerts from LLM output")
            return themes
            
        except Exception as e:
            logger.error(f"❌ Error parsing themes output: {str(e)}")
            return []
    
    def _match_themes_to_findings(self, themes: List[Dict], findings: List[Dict]) -> List[Dict]:
        """Match themes to findings and attach real quotes from the database"""
        try:
            # Create a mapping of finding IDs to findings data
            findings_map = {}
            for finding in findings:
                finding_id = finding.get('finding_id', '')
                if finding_id:
                    findings_map[finding_id] = finding
            
            # Identify company field
            df = pd.DataFrame(findings)
            company_field = self._identify_company_field(df)
            
            # Process each theme/alert
            for theme in themes:
                # Get supporting finding IDs
                supporting_ids = theme.get('supporting_finding_ids', '')
                if isinstance(supporting_ids, str):
                    finding_ids = [fid.strip() for fid in supporting_ids.split(',') if fid.strip()]
                else:
                    finding_ids = supporting_ids
                
                # Find the best matching finding for primary quote
                primary_quote = ""
                secondary_quote = ""
                companies = set()
                
                for finding_id in finding_ids:
                    if finding_id in findings_map:
                        finding = findings_map[finding_id]
                        
                        # Get primary quote
                        if not primary_quote:
                            primary_quote = finding.get('primary_quote', '')
                        
                        # Get secondary quote
                        elif not secondary_quote:
                            secondary_quote = finding.get('primary_quote', '')
                        
                        # Collect companies
                        company = finding.get(company_field, '')
                        if company:
                            companies.add(company)
                
                # Update theme with quotes and company info
                if theme.get('theme_type') == 'strategic_alert':
                    theme['primary_alert_quote'] = primary_quote
                    theme['secondary_alert_quote'] = secondary_quote
                    theme['alert_company_ids'] = ','.join(companies)
                else:
                    theme['primary_quote'] = primary_quote
                    theme['secondary_quote'] = secondary_quote
                    theme['company_ids'] = ','.join(companies)
            
            logger.info(f"✅ Matched themes to findings with real quotes")
            return themes
            
        except Exception as e:
            logger.error(f"❌ Error matching themes to findings: {e}")
            return themes
    
    def _save_themes_to_database(self, themes: List[Dict[str, Any]]) -> bool:
        """Save themes to the database"""
        try:
            if not themes:
                logger.warning("No themes to save")
                return False
            
            # Save themes to database
            success_count = 0
            for theme in themes:
                try:
                    # Determine if this is a theme or strategic alert
                    theme_type = theme.get('theme_type', 'theme')
                    if theme_type == 'strategic_alert':
                        # Map alert fields to dedicated alert columns
                        theme_data = {
                            'client_id': self.client_id,
                            'theme_id': theme.get('alert_id', ''),
                            'theme_type': 'strategic_alert',
                            'competitive_flag': False,
                            
                            # Theme fields (empty for alerts)
                            'theme_title': '',
                            'theme_statement': '',
                            'classification': '',
                            'deal_context': '',
                            'metadata_insights': '',
                            'primary_quote': '',
                            'secondary_quote': '',
                            'supporting_finding_ids': '',
                            'company_ids': '',
                            
                            # Strategic Alert fields
                            'alert_title': theme.get('alert_title', ''),
                            'alert_statement': theme.get('alert_statement', ''),
                            'alert_classification': theme.get('alert_classification', ''),
                            'strategic_implications': theme.get('strategic_implications', ''),
                            'primary_alert_quote': theme.get('primary_alert_quote', ''),
                            'secondary_alert_quote': theme.get('secondary_alert_quote', ''),
                            'supporting_alert_finding_ids': theme.get('supporting_alert_finding_ids', ''),
                            'alert_company_ids': theme.get('alert_company_ids', ''),
                        }
                    else:
                        # Map theme fields as before
                        theme_data = {
                            'client_id': self.client_id,
                            'theme_id': theme.get('theme_id', ''),
                            'theme_title': theme.get('theme_title', ''),
                            'theme_statement': theme.get('theme_statement', ''),
                            'classification': theme.get('classification', ''),
                            'deal_context': theme.get('deal_context', ''),
                            'metadata_insights': theme.get('metadata_insights', ''),
                            'primary_quote': theme.get('primary_quote', ''),
                            'secondary_quote': theme.get('secondary_quote', ''),
                            'competitive_flag': self._convert_to_boolean(theme.get('competitive_flag', '')),
                            'supporting_finding_ids': theme.get('supporting_finding_ids', ''),
                            'company_ids': theme.get('company_ids', ''),
                            'theme_type': 'theme',
                        }
                    
                    # Save to database
                    if self.supabase.save_stage4_theme(theme_data):
                        success_count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving theme {theme.get('theme_id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"✅ Successfully saved {success_count}/{len(themes)} themes to database")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error saving themes to database: {e}")
            return False
    
    def _convert_to_boolean(self, value: str) -> bool:
        """Convert string value to boolean"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', 'yes', '1', 'y']
        return False
    
    def analyze_themes_hybrid_v2(self) -> bool:
        """Main method to analyze findings using hybrid V2 approach"""
        try:
            logger.info(f"🎯 Starting Stage 4 Hybrid V2 theme analysis for client: {self.client_id}")
            
            # Get findings from database
            findings = self.supabase.get_stage3_findings_list(self.client_id)
            
            if not findings:
                logger.warning(f"No Stage 3 findings found for client {self.client_id}")
                return False
            
            logger.info(f"📊 Found {len(findings)} findings to analyze")
            
            # Convert findings to JSON
            findings_json = self._get_findings_json()
            if not findings_json:
                logger.warning("No findings data available")
                return False
            
            # Stage 4A: Pattern Identification with STRONG cross-company validation
            logger.info("🔄 Stage 4A: Identifying patterns with cross-company validation...")
            patterns_output = self._call_stage4a_pattern_identification(findings_json)
            if not patterns_output:
                logger.error("❌ Stage 4A failed - no patterns identified")
                return False
            
            # Stage 4B: Comprehensive Theme Development
            logger.info("🔄 Stage 4B: Developing comprehensive themes...")
            themes_output = self._call_stage4b_theme_development(patterns_output, findings_json)
            if not themes_output:
                logger.error("❌ Stage 4B failed - no themes generated")
                return False
            
            # Parse themes and alerts
            themes = self._parse_themes_output(themes_output)
            if not themes:
                logger.warning("No themes parsed from output")
                return False
            
            # Match themes to findings and attach real quotes
            themes = self._match_themes_to_findings(themes, findings)
            
            # Save themes to database
            success = self._save_themes_to_database(themes)
            
            if success:
                logger.info(f"✅ Stage 4 Hybrid V2 theme analysis completed successfully for client {self.client_id}")
                logger.info(f"📊 Generated {len(themes)} themes/alerts using hybrid V2 approach")
            else:
                logger.error(f"❌ Failed to save themes to database for client {self.client_id}")
            
            return success
                
        except Exception as e:
            logger.error(f"Error in hybrid V2 theme analysis: {e}")
            return False
    
    def process_themes_hybrid_v2(self, client_id: str = None) -> bool:
        """Process themes using hybrid V2 approach for a specific client"""
        if client_id:
            self.client_id = client_id
        
        return self.analyze_themes_hybrid_v2()

def main():
    """Main function to run Stage 4 Hybrid V2 theme analysis"""
    import sys
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Stage 4 Hybrid V2 Theme Analysis')
    parser.add_argument('--client_id', type=str, default='Rev', help='Client ID to analyze')
    
    args = parser.parse_args()
    client_id = args.client_id
    
    try:
        analyzer = Stage4ThemeAnalyzerHybridV2(client_id)
        success = analyzer.process_themes_hybrid_v2()
        
        if success:
            print(f"✅ Stage 4 Hybrid V2 theme analysis completed successfully for client: {client_id}")
            sys.exit(0)
        else:
            print(f"❌ Stage 4 Hybrid V2 theme analysis failed for client: {client_id}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error running Stage 4 Hybrid V2 theme analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 