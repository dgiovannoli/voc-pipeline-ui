#!/usr/bin/env python3
"""
Research-Driven Stage 4 Theme Analyzer
Uses data-driven requirements instead of arbitrary numbers for theme generation
BEST PRACTICE: Let the data determine the number of meaningful patterns
"""

import os
import json
import logging
import pandas as pd
import re
from typing import List, Dict, Any, Tuple
import openai
from supabase_database import SupabaseDatabase
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResearchDrivenStage4Analyzer:
    def __init__(self, client_id: str = "Rev"):
        self.client_id = client_id
        self.supabase = SupabaseDatabase()
        
        # Load OpenAI API key
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Research-driven thresholds (data-determined, not arbitrary)
        self.research_thresholds = {
            'min_companies_per_theme': 2,  # Cross-company validation required
            'min_findings_per_theme': 3,   # Sufficient evidence threshold
            'min_confidence_score': 3.0,   # Quality threshold from Stage 3
            'max_themes_per_pattern': 2,   # Avoid over-segmentation
            'similarity_threshold': 0.7,   # Clustering threshold
            'min_theme_impact_score': 3.0  # Business impact threshold
        }
        
        # Quality control parameters
        self.quality_controls = {
            'require_cross_company_validation': True,
            'prevent_solutioning_language': True,
            'require_business_impact': True,
            'validate_evidence_strength': True
        }
        
    def analyze_findings_data_structure(self, findings: List[Dict]) -> Dict:
        """Analyze the data structure to determine research-driven requirements"""
        if not findings:
            return {
                'total_findings': 0,
                'companies_represented': 0,
                'confidence_distribution': {},
                'pattern_density': 0,
                'recommended_theme_count': 0,
                'recommended_alert_count': 0
            }
        
        # Analyze data structure
        total_findings = len(findings)
        companies = set()
        confidence_scores = []
        impact_scores = []
        
        for finding in findings:
            # Extract company information
            company = finding.get('interview_company', finding.get('company', ''))
            if company:
                companies.add(company)
            
            # Collect confidence scores
            confidence = finding.get('enhanced_confidence', finding.get('confidence_score', 0))
            if confidence:
                confidence_scores.append(confidence)
            
            # Collect impact scores
            impact = finding.get('impact_score', 0)
            if impact:
                impact_scores.append(impact)
        
        # Calculate pattern density
        pattern_density = self._calculate_pattern_density(findings)
        
        # Determine research-driven requirements
        recommended_theme_count = self._calculate_recommended_theme_count(
            total_findings, len(companies), pattern_density, confidence_scores
        )
        
        recommended_alert_count = self._calculate_recommended_alert_count(
            total_findings, impact_scores
        )
        
        return {
            'total_findings': total_findings,
            'companies_represented': len(companies),
            'confidence_distribution': self._analyze_confidence_distribution(confidence_scores),
            'pattern_density': pattern_density,
            'recommended_theme_count': recommended_theme_count,
            'recommended_alert_count': recommended_alert_count,
            'data_quality_score': self._calculate_data_quality_score(findings)
        }
    
    def _calculate_pattern_density(self, findings: List[Dict]) -> float:
        """Calculate the density of meaningful patterns in the data"""
        if not findings:
            return 0.0
        
        # Use TF-IDF to identify semantic clusters
        texts = [finding.get('finding_statement', '') for finding in findings]
        if not any(texts):
            return 0.0
        
        try:
            vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Use DBSCAN to identify clusters
            clustering = DBSCAN(eps=0.3, min_samples=2).fit(tfidf_matrix)
            n_clusters = len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)
            
            # Pattern density = clusters / total findings
            return n_clusters / len(findings) if len(findings) > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"Error calculating pattern density: {e}")
            return 0.1  # Default low density
    
    def _calculate_recommended_theme_count(self, total_findings: int, companies: int, 
                                         pattern_density: float, confidence_scores: List[float]) -> int:
        """Calculate research-driven theme count based on data characteristics"""
        
        # REVISED LOGIC: Prioritize company coverage over finding count
        # A theme with 5 companies and 1 finding each is stronger than 2 companies with 3 findings each
        
        # Base calculation on company coverage and pattern density
        if companies >= 5:
            # High company coverage - can support more themes
            base_themes = max(3, int(companies * 0.4))  # ~2 themes per 5 companies
        elif companies >= 3:
            # Medium company coverage
            base_themes = max(2, int(companies * 0.5))  # ~1.5 themes per 3 companies
        else:
            # Low company coverage - limit themes
            base_themes = max(1, min(companies, 2))
        
        # Adjust for pattern density (but don't over-weight it)
        pattern_multiplier = min(1.5, max(0.5, pattern_density * 5))  # Cap the multiplier
        
        # Adjust for confidence quality
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 3.0
        if avg_confidence >= 4.0:
            confidence_multiplier = 1.3
        elif avg_confidence >= 3.0:
            confidence_multiplier = 1.0
        else:
            confidence_multiplier = 0.7
        
        recommended = int(base_themes * pattern_multiplier * confidence_multiplier)
        
        # Apply reasonable bounds based on company coverage
        min_themes = max(1, companies // 3)  # At least 1 theme per 3 companies
        max_themes = min(companies, total_findings // 2)  # No more themes than companies, and no more than 1 per 2 findings
        
        return max(min_themes, min(recommended, max_themes))
    
    def _calculate_recommended_alert_count(self, total_findings: int, impact_scores: List[float]) -> int:
        """Calculate research-driven alert count based on high-impact findings"""
        
        if not impact_scores:
            return 0
        
        # Count high-impact findings (impact score >= 4.0)
        high_impact_count = sum(1 for score in impact_scores if score >= 4.0)
        
        # Alerts should be rare - only for truly high-impact findings
        # Even 1 high-impact finding could warrant an alert if it's significant enough
        recommended = max(0, min(5, high_impact_count))
        
        return recommended
    
    def _analyze_confidence_distribution(self, confidence_scores: List[float]) -> Dict:
        """Analyze the distribution of confidence scores"""
        if not confidence_scores:
            return {'high': 0, 'medium': 0, 'low': 0}
        
        high = sum(1 for score in confidence_scores if score >= 4.0)
        medium = sum(1 for score in confidence_scores if 3.0 <= score < 4.0)
        low = sum(1 for score in confidence_scores if score < 3.0)
        
        return {'high': high, 'medium': medium, 'low': low}
    
    def _calculate_data_quality_score(self, findings: List[Dict]) -> float:
        """Calculate overall data quality score"""
        if not findings:
            return 0.0
        
        quality_indicators = []
        
        for finding in findings:
            # Check for required fields
            has_statement = bool(finding.get('finding_statement', ''))
            has_company = bool(finding.get('interview_company', finding.get('company', '')))
            has_confidence = finding.get('enhanced_confidence', 0) >= 3.0
            
            quality_indicators.append(has_statement and has_company and has_confidence)
        
        return sum(quality_indicators) / len(quality_indicators) if quality_indicators else 0.0
    
    def generate_research_driven_prompt(self, findings_json: str, data_analysis: Dict) -> str:
        """Generate a research-driven prompt based on data analysis"""
        
        theme_count = data_analysis.get('recommended_theme_count', 8)
        alert_count = data_analysis.get('recommended_alert_count', 3)
        companies = data_analysis.get('companies_represented', 0)
        pattern_density = data_analysis.get('pattern_density', 0.1)
        
        prompt = f"""
You are an expert qualitative research analyst specializing in B2B SaaS competitive intelligence.

RESEARCH-DRIVEN ANALYSIS REQUIREMENTS:
Based on the data analysis, generate exactly {theme_count} themes and {alert_count} strategic alerts.

DATA CHARACTERISTICS:
- Total findings: {data_analysis.get('total_findings', 0)}
- Companies represented: {companies}
- Pattern density: {pattern_density:.2f}
- Data quality score: {data_analysis.get('data_quality_score', 0):.2f}

QUALITY REQUIREMENTS:
1. ONLY generate themes for genuine cross-company patterns (2+ companies minimum)
2. Each theme must have 3+ supporting findings with confidence ≥ 3.0
3. Focus on business impact: revenue threats, competitive vulnerabilities, market opportunities
4. AVOID solutioning language - describe what is happening, not what should be done
5. Use specific examples and concrete details from findings
6. Ensure themes reflect actual data patterns, not forced segmentation

THEME GENERATION RULES:
- Generate exactly {theme_count} themes (no more, no less)
- Each theme must be 50-75 words with cross-company validation
- Include specific business insights and competitive dynamics
- Use concrete examples from the findings
- Every theme must inherit cross-company validation from its source pattern

STRATEGIC ALERT RULES:
- Generate exactly {alert_count} strategic alerts (no more, no less)
- Focus on high-impact findings requiring immediate attention
- Use findings from single companies with high business impact
- Include specific strategic implications

FINDINGS DATA:
{findings_json}

OUTPUT FORMAT:
Return a JSON object with this structure:
{{
  "themes": [
    {{
      "theme_id": "T1",
      "theme_title": "Specific, descriptive title",
      "theme_statement": "50-75 word executive narrative with cross-company validation",
      "classification": "REVENUE_THREAT|COMPETITIVE_VULNERABILITY|MARKET_OPPORTUNITY",
      "deal_context": "Won: X, Lost: Y",
      "metadata_insights": "",
      "primary_quote": "",
      "secondary_quote": "",
      "competitive_flag": false,
      "supporting_finding_ids": "F1,F2,F3",
      "company_ids": ""
    }}
  ],
  "strategic_alerts": [
    {{
      "alert_id": "A1",
      "alert_title": "High-impact finding title",
      "alert_statement": "50-75 word urgent narrative",
      "alert_classification": "REVENUE_THREAT|COMPETITIVE_VULNERABILITY|MARKET_OPPORTUNITY",
      "strategic_implications": "Specific business implications",
      "primary_alert_quote": "",
      "secondary_alert_quote": "",
      "supporting_alert_finding_ids": "F1",
      "alert_company_ids": ""
    }}
  ]
}}

CRITICAL: Generate exactly {theme_count} themes and {alert_count} alerts based on real patterns in the data.
"""
        
        return prompt
    
    def _call_llm_with_research_driven_prompt(self, findings_json: str, data_analysis: Dict) -> str:
        """Call OpenAI API with research-driven prompt"""
        try:
            prompt = self.generate_research_driven_prompt(findings_json, data_analysis)
            
            # Updated for OpenAI API v1.0+
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert B2B SaaS competitive intelligence analyst. Generate themes and alerts based on actual data patterns, not arbitrary targets."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.3
            )
            
            llm_output = response.choices[0].message.content.strip()
            logger.info(f"✅ Research-driven theme generation completed")
            
            return llm_output
            
        except Exception as e:
            logger.error(f"❌ Error in research-driven theme generation: {e}")
            return ""
    
    def _get_findings_json(self) -> str:
        """Get findings data in JSON format for LLM processing"""
        try:
            findings = self.supabase.get_stage3_findings_list(self.client_id)
            
            if not findings:
                return ""
            
            # Convert to JSON format
            findings_data = []
            for finding in findings:
                finding_data = {
                    'finding_id': finding.get('finding_id', ''),
                    'finding_statement': finding.get('finding_statement', ''),
                    'interview_company': finding.get('interview_company', ''),
                    'enhanced_confidence': finding.get('enhanced_confidence', 0),
                    'impact_score': finding.get('impact_score', 0),
                    'primary_quote': finding.get('primary_quote', ''),
                    'secondary_quote': finding.get('secondary_quote', ''),
                    'finding_category': finding.get('finding_category', ''),
                    'deal_status': finding.get('deal_status', '')
                }
                findings_data.append(finding_data)
            
            return json.dumps(findings_data, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting findings JSON: {e}")
            return ""
    
    def _parse_themes_output(self, output: str) -> List[Dict]:
        """Parse themes and alerts from LLM output"""
        try:
            # Extract JSON from output
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if not json_match:
                logger.error("No JSON found in LLM output")
                return []
            
            data = json.loads(json_match.group())
            
            themes = []
            
            # Process themes
            for theme in data.get('themes', []):
                theme_data = {
                    'theme_id': theme.get('theme_id', ''),
                    'theme_type': 'theme',
                    'competitive_flag': theme.get('competitive_flag', False),
                    'theme_title': theme.get('theme_title', ''),
                    'theme_statement': theme.get('theme_statement', ''),
                    'classification': theme.get('classification', ''),
                    'deal_context': theme.get('deal_context', ''),
                    'metadata_insights': theme.get('metadata_insights', ''),
                    'primary_quote': theme.get('primary_quote', ''),
                    'secondary_quote': theme.get('secondary_quote', ''),
                    'supporting_finding_ids': theme.get('supporting_finding_ids', ''),
                    'company_ids': theme.get('company_ids', ''),
                    'alert_title': '',
                    'alert_statement': '',
                    'alert_classification': '',
                    'strategic_implications': '',
                    'primary_alert_quote': '',
                    'secondary_alert_quote': '',
                    'supporting_alert_finding_ids': '',
                    'alert_company_ids': ''
                }
                themes.append(theme_data)
            
            # Process strategic alerts
            for alert in data.get('strategic_alerts', []):
                alert_data = {
                    'theme_id': alert.get('alert_id', ''),
                    'theme_type': 'strategic_alert',
                    'competitive_flag': False,
                    'theme_title': '',
                    'theme_statement': '',
                    'classification': '',
                    'deal_context': '',
                    'metadata_insights': '',
                    'primary_quote': '',
                    'secondary_quote': '',
                    'supporting_finding_ids': '',
                    'company_ids': '',
                    'alert_title': alert.get('alert_title', ''),
                    'alert_statement': alert.get('alert_statement', ''),
                    'alert_classification': alert.get('alert_classification', ''),
                    'strategic_implications': alert.get('strategic_implications', ''),
                    'primary_alert_quote': alert.get('primary_alert_quote', ''),
                    'secondary_alert_quote': alert.get('secondary_alert_quote', ''),
                    'supporting_alert_finding_ids': alert.get('supporting_alert_finding_ids', ''),
                    'alert_company_ids': alert.get('alert_company_ids', '')
                }
                themes.append(alert_data)
            
            return themes
            
        except Exception as e:
            logger.error(f"Error parsing themes output: {e}")
            return []
    
    def _match_themes_to_findings(self, themes: List[Dict], findings: List[Dict]) -> List[Dict]:
        """Match themes to findings and attach real quotes"""
        try:
            # Create finding lookup by ID
            findings_lookup = {}
            for finding in findings:
                finding_id = finding.get('finding_id', '')
                if finding_id:
                    findings_lookup[finding_id] = finding
            
            for theme in themes:
                # Match supporting finding IDs
                supporting_ids = theme.get('supporting_finding_ids', '')
                if supporting_ids:
                    finding_ids = [fid.strip() for fid in supporting_ids.split(',')]
                    
                    # Find the best quotes from supporting findings
                    primary_quotes = []
                    secondary_quotes = []
                    
                    for fid in finding_ids:
                        if fid in findings_lookup:
                            finding = findings_lookup[fid]
                            primary_quote = finding.get('primary_quote', '')
                            secondary_quote = finding.get('secondary_quote', '')
                            
                            if primary_quote:
                                primary_quotes.append(primary_quote)
                            if secondary_quote:
                                secondary_quotes.append(secondary_quote)
                    
                    # Set the best quotes
                    if primary_quotes:
                        theme['primary_quote'] = primary_quotes[0]
                    if secondary_quotes:
                        theme['secondary_quote'] = secondary_quotes[0]
            
            return themes
            
        except Exception as e:
            logger.error(f"Error matching themes to findings: {e}")
            return themes
    
    def _save_themes_to_database(self, themes: List[Dict[str, Any]]) -> bool:
        """Save themes to database"""
        try:
            saved_count = 0
            
            for theme in themes:
                # Prepare theme data for database
                theme_data = {
                    'client_id': self.client_id,
                    'theme_id': theme.get('theme_id', ''),
                    'theme_type': theme.get('theme_type', 'theme'),
                    'competitive_flag': self._convert_to_boolean(theme.get('competitive_flag', False)),
                    'theme_title': theme.get('theme_title', ''),
                    'theme_statement': theme.get('theme_statement', ''),
                    'classification': theme.get('classification', ''),
                    'deal_context': theme.get('deal_context', ''),
                    'metadata_insights': theme.get('metadata_insights', ''),
                    'primary_quote': theme.get('primary_quote', ''),
                    'secondary_quote': theme.get('secondary_quote', ''),
                    'supporting_finding_ids': theme.get('supporting_finding_ids', ''),
                    'company_ids': theme.get('company_ids', ''),
                    'alert_title': theme.get('alert_title', ''),
                    'alert_statement': theme.get('alert_statement', ''),
                    'alert_classification': theme.get('alert_classification', ''),
                    'strategic_implications': theme.get('strategic_implications', ''),
                    'primary_alert_quote': theme.get('primary_alert_quote', ''),
                    'secondary_alert_quote': theme.get('secondary_alert_quote', ''),
                    'supporting_alert_finding_ids': theme.get('supporting_alert_finding_ids', ''),
                    'alert_company_ids': theme.get('alert_company_ids', '')
                }
                
                # Save to database
                if self.supabase.save_stage4_theme(theme_data):
                    saved_count += 1
            
            logger.info(f"✅ Saved {saved_count}/{len(themes)} themes to database")
            return saved_count > 0
            
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
    
    def analyze_themes_research_driven(self) -> bool:
        """Main method to analyze findings using research-driven approach"""
        try:
            logger.info(f"🎯 Starting Research-Driven Stage 4 theme analysis for client: {self.client_id}")
            
            # Get findings from database
            findings = self.supabase.get_stage3_findings_list(self.client_id)
            
            if not findings:
                logger.warning(f"No Stage 3 findings found for client {self.client_id}")
                return False
            
            logger.info(f"📊 Found {len(findings)} findings to analyze")
            
            # Analyze data structure to determine requirements
            logger.info("🔍 Analyzing data structure for research-driven requirements...")
            data_analysis = self.analyze_findings_data_structure(findings)
            
            logger.info(f"📈 Data Analysis Results:")
            logger.info(f"   - Total findings: {data_analysis['total_findings']}")
            logger.info(f"   - Companies represented: {data_analysis['companies_represented']}")
            logger.info(f"   - Pattern density: {data_analysis['pattern_density']:.2f}")
            logger.info(f"   - Recommended themes: {data_analysis['recommended_theme_count']}")
            logger.info(f"   - Recommended alerts: {data_analysis['recommended_alert_count']}")
            logger.info(f"   - Data quality score: {data_analysis['data_quality_score']:.2f}")
            
            # Convert findings to JSON
            findings_json = self._get_findings_json()
            if not findings_json:
                logger.warning("No findings data available")
                return False
            
            # Generate themes using research-driven approach
            logger.info("🔄 Generating themes using research-driven requirements...")
            themes_output = self._call_llm_with_research_driven_prompt(findings_json, data_analysis)
            if not themes_output:
                logger.error("❌ Research-driven theme generation failed")
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
                logger.info(f"✅ Research-driven Stage 4 theme analysis completed successfully for client {self.client_id}")
                logger.info(f"📊 Generated {len([t for t in themes if t.get('theme_type') == 'theme'])} themes and {len([t for t in themes if t.get('theme_type') == 'strategic_alert'])} alerts")
            else:
                logger.error(f"❌ Failed to save themes to database for client {self.client_id}")
            
            return success
                
        except Exception as e:
            logger.error(f"Error in research-driven theme analysis: {e}")
            return False
    
    def process_themes(self, client_id: str = None) -> bool:
        """Process themes for a specific client using research-driven approach"""
        if client_id:
            self.client_id = client_id
        
        return self.analyze_themes_research_driven()

if __name__ == "__main__":
    # Example usage
    analyzer = ResearchDrivenStage4Analyzer()
    success = analyzer.analyze_themes_research_driven()
    
    if success:
        print("✅ Research-driven Stage 4 analysis completed successfully")
    else:
        print("❌ Research-driven Stage 4 analysis failed") 