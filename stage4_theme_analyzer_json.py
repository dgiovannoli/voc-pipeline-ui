#!/usr/bin/env python3
"""
Stage 4 JSON Theme Analyzer
Generates themes from Stage 3 JSON findings using the B2B SaaS Win/Loss Theme Development Protocol
Outputs JSON data structure for better LLM integration and data flexibility
"""

import os
import json
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
import openai
from supabase_database import SupabaseDatabase
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Stage4ThemeAnalyzerJSON:
    def __init__(self, client_id: str = "default"):
        self.client_id = client_id
        self.supabase = SupabaseDatabase()
        
        # Load OpenAI API key
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Load theme prompt
        self.theme_prompt = self._load_theme_prompt()
        
    def _load_theme_prompt(self) -> str:
        """Load the theme prompt from the Context/Theme Prompt.txt file"""
        try:
            with open('Context/Theme Prompt.txt', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error("Theme Prompt.txt file not found in Context/ directory")
            raise
        except Exception as e:
            logger.error(f"Error loading theme prompt: {e}")
            raise
    
    def _get_findings_json(self) -> List[Dict]:
        """Get findings in JSON format from Supabase"""
        try:
            # Get JSON findings from database
            findings = self.supabase.get_json_findings(client_id=self.client_id)
            
            if not findings:
                logger.warning(f"No JSON findings found for client {self.client_id}")
                return []
            
            logger.info(f"📊 Retrieved {len(findings)} JSON findings for theme analysis")
            return findings
            
        except Exception as e:
            logger.error(f"❌ Error retrieving JSON findings: {str(e)}")
            return []
    
    def _prepare_findings_for_llm(self, findings: List[Dict]) -> str:
        """Prepare findings data for LLM processing"""
        try:
            # Extract key information for LLM
            llm_findings = []
            
            for finding in findings:
                llm_finding = {
                    'finding_id': finding.get('finding_id'),
                    'finding_statement': finding.get('finding_statement'),
                    'finding_category': finding.get('finding_category'),
                    'impact_score': finding.get('impact_score'),
                    'confidence_score': finding.get('confidence_score'),
                    'supporting_quotes': finding.get('supporting_quotes', []),
                    'companies_mentioned': finding.get('companies_mentioned', []),
                    'interview_company': finding.get('interview_company'),
                    'interview_date': finding.get('interview_date'),
                    'interview_type': finding.get('interview_type'),
                    'interviewee_name': finding.get('interviewee_name'),
                    'interviewee_role': finding.get('interviewee_role'),
                    'interviewee_company': finding.get('interviewee_company')
                }
                llm_findings.append(llm_finding)
            
            # Convert to JSON string
            findings_json = json.dumps(llm_findings, indent=2, default=str)
            
            logger.info(f"📝 Prepared {len(llm_findings)} findings for LLM processing")
            return findings_json
            
        except Exception as e:
            logger.error(f"❌ Error preparing findings for LLM: {str(e)}")
            return ""
    
    def _call_llm_for_json_themes(self, findings_json: str) -> str:
        """Call OpenAI API to generate JSON themes using the comprehensive protocol"""
        try:
            # Prepare the prompt with JSON findings data
            full_prompt = f"""
{self.theme_prompt}

FINDINGS DATA TO ANALYZE (JSON format):
{findings_json}

EXECUTION INSTRUCTIONS:
1. Execute the CRITICAL DATA VALIDATION first
2. Process through each step systematically
3. Complete all validation checkpoints before proceeding
4. Generate both cross-company themes and strategic alerts
5. Ensure all output meets executive communication standards

OUTPUT REQUIREMENTS:
- Generate themes based on actual patterns found in the findings data
- Each theme MUST be based on actual finding content, not generic statements
- Use the real finding IDs from the provided data
- Themes should be specific and actionable business insights
- Avoid generic, template-like language
- Base themes on the actual finding statements, not assumptions
- Generate as many themes as needed to capture the key patterns (typically 3-8 themes)
- Include strategic alerts for high-value single-company findings

JSON OUTPUT FORMAT:
Return a JSON object with the following structure:

{{
  "themes": [
    {{
      "theme_id": "T1",
      "theme_name": "Executive theme title",
      "theme_description": "50-75 word executive narrative",
      "strategic_importance": "HIGH|MEDIUM|LOW",
      "action_items": ["action1", "action2", "action3"],
      "related_findings": ["F001", "F002"]
    }}
  ],
  "alerts": [
    {{
      "alert_id": "A1",
      "alert_type": "REVENUE_THREAT|COMPETITIVE_DISPLACEMENT|STRATEGIC_DISRUPTION",
      "alert_message": "50-75 word urgent narrative",
      "priority": "HIGH|MEDIUM|LOW",
      "recommended_actions": ["action1", "action2"]
    }}
  ],
  "metadata": {{
    "total_themes": 5,
    "total_alerts": 2,
    "analysis_date": "2024-01-01",
    "client_id": "{self.client_id}"
  }}
}}

Return ONLY the JSON object (no explanations or extra text).
"""
            
            # Call OpenAI API
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert qualitative research analyst specializing in B2B SaaS competitive intelligence. Transform validated findings from multiple win/loss interviews into executive-ready strategic themes and high-value strategic alerts. Follow the B2B SaaS Win/Loss Theme Development Protocol exactly. Return only valid JSON."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.1,
                max_tokens=6000
            )
            
            llm_output = response.choices[0].message.content.strip()
            
            # Log the raw output for debugging
            logger.info("📝 Raw LLM output:")
            logger.info("=" * 50)
            logger.info(llm_output)
            logger.info("=" * 50)
            
            return llm_output
            
        except Exception as e:
            logger.error(f"Error calling LLM for JSON themes: {e}")
            return ""
    
    def _parse_json_themes_output(self, llm_output: str) -> Dict:
        """Parse JSON themes output from LLM"""
        try:
            # Clean the output to extract JSON
            cleaned_output = self._extract_json_from_llm_output(llm_output)
            
            if not cleaned_output:
                logger.error("No valid JSON found in LLM output")
                return {"themes": [], "alerts": [], "metadata": {}}
            
            # Parse JSON
            parsed_data = json.loads(cleaned_output)
            
            # Validate structure
            if not isinstance(parsed_data, dict):
                logger.error("LLM output is not a valid JSON object")
                return {"themes": [], "alerts": [], "metadata": {}}
            
            # Ensure required fields exist
            themes = parsed_data.get('themes', [])
            alerts = parsed_data.get('alerts', [])
            metadata = parsed_data.get('metadata', {})
            
            logger.info(f"✅ Parsed {len(themes)} themes and {len(alerts)} alerts from LLM output")
            
            return {
                "themes": themes,
                "alerts": alerts,
                "metadata": metadata
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return {"themes": [], "alerts": [], "metadata": {}}
        except Exception as e:
            logger.error(f"Error parsing JSON themes output: {e}")
            return {"themes": [], "alerts": [], "metadata": {}}
    
    def _extract_json_from_llm_output(self, llm_output: str) -> str:
        """Extract JSON from LLM output, handling markdown code blocks"""
        try:
            # Remove markdown code blocks if present
            if "```json" in llm_output:
                start = llm_output.find("```json") + 7
                end = llm_output.find("```", start)
                if end != -1:
                    return llm_output[start:end].strip()
            
            if "```" in llm_output:
                start = llm_output.find("```") + 3
                end = llm_output.find("```", start)
                if end != -1:
                    return llm_output[start:end].strip()
            
            # If no code blocks, return the whole output
            return llm_output.strip()
            
        except Exception as e:
            logger.error(f"Error extracting JSON from LLM output: {e}")
            return llm_output.strip()
    
    def _create_json_theme(self, theme_data: Dict, theme_id: str) -> Dict:
        """Create a JSON theme structure"""
        theme = {
            'theme_id': theme_id,
            'theme_name': theme_data.get('theme_name', ''),
            'theme_description': theme_data.get('theme_description', ''),
            'strategic_importance': theme_data.get('strategic_importance', 'MEDIUM'),
            'action_items': theme_data.get('action_items', []),
            'related_findings': theme_data.get('related_findings', []),
            'alert_id': None,
            'alert_type': None,
            'alert_message': None,
            'alert_priority': None,
            'recommended_actions': [],
            'theme_data': theme_data,
            'alert_data': {},
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'analysis_version': '4.0',
                'client_id': self.client_id
            },
            'analysis_date': datetime.now().date().isoformat(),
            'created_at': datetime.now().isoformat()
        }
        
        return theme
    
    def _create_json_alert(self, alert_data: Dict, alert_id: str) -> Dict:
        """Create a JSON alert structure"""
        alert = {
            'theme_id': None,
            'theme_name': None,
            'theme_description': None,
            'strategic_importance': None,
            'action_items': [],
            'related_findings': [],
            'alert_id': alert_id,
            'alert_type': alert_data.get('alert_type', ''),
            'alert_message': alert_data.get('alert_message', ''),
            'alert_priority': alert_data.get('priority', 'MEDIUM'),
            'recommended_actions': alert_data.get('recommended_actions', []),
            'theme_data': {},
            'alert_data': alert_data,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'analysis_version': '4.0',
                'client_id': self.client_id
            },
            'analysis_date': datetime.now().date().isoformat(),
            'created_at': datetime.now().isoformat()
        }
        
        return alert
    
    def _save_json_themes_to_supabase(self, themes: List[Dict], alerts: List[Dict]) -> int:
        """Save JSON themes and alerts to Supabase"""
        saved_count = 0
        
        # Save themes
        for theme in themes:
            if self.supabase.save_json_theme(theme, self.client_id):
                saved_count += 1
        
        # Save alerts
        for alert in alerts:
            if self.supabase.save_json_theme(alert, self.client_id):
                saved_count += 1
        
        logger.info(f"✅ Saved {saved_count}/{len(themes) + len(alerts)} JSON themes and alerts to Supabase")
        return saved_count
    
    def process_stage4_themes_json(self) -> Dict:
        """Process Stage 4 themes and output JSON structure"""
        logger.info("🚀 Starting Stage 4 JSON Theme Analysis")
        
        # Get JSON findings
        findings = self._get_findings_json()
        
        if not findings:
            logger.warning("⚠️ No JSON findings found for theme analysis")
            return {
                'themes': [],
                'alerts': [],
                'metadata': {
                    'total_themes': 0,
                    'total_alerts': 0,
                    'analysis_date': datetime.now().isoformat(),
                    'client_id': self.client_id
                }
            }
        
        # Prepare findings for LLM
        findings_json = self._prepare_findings_for_llm(findings)
        
        if not findings_json:
            logger.warning("⚠️ No findings data available for theme generation")
            return {
                'themes': [],
                'alerts': [],
                'metadata': {
                    'total_themes': 0,
                    'total_alerts': 0,
                    'analysis_date': datetime.now().isoformat(),
                    'client_id': self.client_id
                }
            }
        
        # Call LLM to generate themes
        llm_output = self._call_llm_for_json_themes(findings_json)
        
        if not llm_output:
            logger.warning("⚠️ No response from LLM")
            return {
                'themes': [],
                'alerts': [],
                'metadata': {
                    'total_themes': 0,
                    'total_alerts': 0,
                    'analysis_date': datetime.now().isoformat(),
                    'client_id': self.client_id
                }
            }
        
        # Parse LLM output
        parsed_data = self._parse_json_themes_output(llm_output)
        
        # Create JSON theme and alert structures
        themes = []
        alerts = []
        
        # Process themes
        for i, theme_data in enumerate(parsed_data.get('themes', [])):
            theme_id = theme_data.get('theme_id', f"T{i+1:03d}")
            theme = self._create_json_theme(theme_data, theme_id)
            themes.append(theme)
        
        # Process alerts
        for i, alert_data in enumerate(parsed_data.get('alerts', [])):
            alert_id = alert_data.get('alert_id', f"A{i+1:03d}")
            alert = self._create_json_alert(alert_data, alert_id)
            alerts.append(alert)
        
        # Save to Supabase
        saved_count = self._save_json_themes_to_supabase(themes, alerts)
        
        # Create output structure
        output = {
            'themes': themes,
            'alerts': alerts,
            'metadata': {
                'total_themes': len(themes),
                'total_alerts': len(alerts),
                'themes_saved': saved_count,
                'analysis_date': datetime.now().isoformat(),
                'client_id': self.client_id,
                'llm_metadata': parsed_data.get('metadata', {})
            }
        }
        
        logger.info(f"✅ Stage 4 JSON theme analysis complete: {len(themes)} themes, {len(alerts)} alerts generated")
        return output
    
    def export_themes_json(self, filters: Optional[Dict] = None) -> str:
        """Export themes as JSON file"""
        return self.supabase.export_json_themes(client_id=self.client_id, filters=filters)

def run_stage4_json_analysis(client_id: str = 'default'):
    """Run Stage 4 JSON theme analysis"""
    analyzer = Stage4ThemeAnalyzerJSON(client_id=client_id)
    results = analyzer.process_stage4_themes_json()
    
    # Print summary
    print(f"\n📊 Stage 4 JSON Theme Analysis Results:")
    print(f"   Total themes: {results['metadata']['total_themes']}")
    print(f"   Total alerts: {results['metadata']['total_alerts']}")
    print(f"   Themes saved: {results['metadata']['themes_saved']}")
    print(f"   Client ID: {results['metadata']['client_id']}")
    
    # Export to JSON file
    export_file = analyzer.export_themes_json()
    if export_file:
        print(f"   Exported to: {export_file}")
    
    return results

if __name__ == "__main__":
    run_stage4_json_analysis() 