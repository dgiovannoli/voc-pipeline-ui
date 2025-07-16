#!/usr/bin/env python3
"""
Enhanced Stage 4 Theme Analyzer
Uses new structure: [Emotional Driver] + [Specific Context] + [Business Impact]
Separates client-specific themes from market themes
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedStage4ThemeAnalyzer:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.db = SupabaseDatabase()
        
        # Initialize OpenAI client
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = openai.OpenAI(api_key=self.openai_api_key)
        
    def analyze_themes_enhanced_structure(self) -> bool:
        """Analyze themes using enhanced structure with client-specific detection"""
        try:
            # Get Stage 3 findings
            findings = self.db.get_stage3_findings(self.client_id)
            if findings.empty:
                logger.error("No Stage 3 findings found")
                return False
                
            logger.info(f"Found {len(findings)} Stage 3 findings")
            
            # Prepare findings for analysis
            findings_json = self._prepare_findings_json(findings)
            
            # Generate themes using enhanced structure
            themes_data = self._generate_enhanced_structure_themes(findings_json, findings)
            
            # Save themes to database
            success = self._save_enhanced_structure_themes(themes_data)
            
            if success:
                logger.info(f"Successfully generated {len(themes_data)} themes with enhanced structure")
                return True
            else:
                logger.error("Failed to save themes")
                return False
                
        except Exception as e:
            logger.error(f"Error in enhanced structure theme analysis: {e}")
            return False

    def _prepare_findings_json(self, findings: pd.DataFrame) -> str:
        """Prepare findings in JSON format for LLM processing"""
        try:
            # Convert to list of dictionaries
            findings_list = findings.to_dict('records')
            
            # Add client-specific detection info
            for finding in findings_list:
                if finding.get('client_specific', False):
                    finding['finding_statement'] = f"{self.client_id}-specific: {finding.get('finding_statement', '')}"
            
            findings_json = json.dumps(findings_list, indent=2)
            logger.info(f"Prepared {len(findings_list)} findings in JSON format")
            return findings_json
            
        except Exception as e:
            logger.error(f"Error preparing findings JSON: {e}")
            return ""

    def _generate_enhanced_structure_themes(self, findings_json: str, findings: pd.DataFrame) -> List[Dict]:
        """Generate themes using enhanced structure with client-specific detection"""
        try:
            prompt = self._get_enhanced_structure_prompt()
            
            # Add findings data to prompt
            full_prompt = prompt.format(findings_data=findings_json)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=4000,
                temperature=0.1
            )
            
            themes_text = response.choices[0].message.content
            logger.info("Generated themes with enhanced structure")
            
            # Parse themes with enhanced structure
            themes = self._parse_enhanced_structure_themes(themes_text, findings)
            
            # Validate themes
            validated_themes = self._validate_enhanced_structure_themes(themes, findings)
            
            return validated_themes
            
        except Exception as e:
            logger.error(f"Error generating enhanced structure themes: {e}")
            return []

    def _get_enhanced_structure_prompt(self) -> str:
        """Get enhanced structure prompt with client-specific detection"""
        return f"""
You are an expert B2B SaaS win/loss researcher. Your task is to generate executive-ready themes from customer interview findings, using only the actual customer voice and evidence.

**For each theme, output in this exact format:**

---
Theme Title: [Emotional Driver] + [Specific Context] + [Business Impact]
- Emotional Driver: frustration, anxiety, pressure, fatigue, fear, etc.
- Specific Context: what specific situation, feature, or experience
- Business Impact: drives, blocks, creates, impacts, affects, influences, etc.

Examples:
- "Frustration with Speaker Identification Blocks Usability"
- "Anxiety Over Rising Costs Jeopardizes Small Firm Viability" 
- "Pressure for Real-Time Transcription Creates Competitive Pressure"
- "Fatigue from Manual Edits Blocks Efficiency Gains"

Theme Statement: [Two sentences, strictly.]
- Sentence 1: Describe the business impact or decision behavior, using specific, non-generic language. State what is happening, to whom, and why it matters, in a way that is relevant to business or buying decisions.
- Sentence 2: Provide specific customer evidence, including a direct quote (in quotation marks) and, if possible, quantify the number of companies or customers expressing this view.

Strategic Implications: [One sentence on what this means for the business, in plain, actionable language.]

**EXAMPLES:**

---
Theme Title: "Frustration with Speaker Identification Blocks Usability"
Theme Statement: Legal professionals struggle to use transcripts effectively when speaker identification fails during multi-party recordings. As one customer said, "But if it could identify each speaker that would be huge. And do it again accurately." (3 companies)
Strategic Implications: Invest in advanced speaker identification technology to enhance transcript accuracy and user satisfaction.

---
Theme Title: "Anxiety Over Rising Costs Jeopardizes Small Firm Viability"
Theme Statement: Small firms face financial strain as essential service costs increase beyond their revenue capacity. One attorney shared, "Right now, Westlaw is about to price us out. They just raised all of our stuff almost 950 a month, and that's per login." (2 companies)
Strategic Implications: Develop pricing strategies that accommodate smaller firms' financial constraints.

---

**SEPARATE {self.client_id.upper()}-SPECIFIC THEMES FROM MARKET THEMES:**

When you encounter findings labeled "{self.client_id}-specific:" or containing {self.client_id}-specific feedback, create {self.client_id}-specific themes even if mentioned by only 1-2 companies.

{self.client_id}-specific themes should focus on:
- {self.client_id}'s specific features and capabilities
- {self.client_id}'s pricing model and concerns
- {self.client_id}'s integration capabilities
- {self.client_id}'s user experience and workflow issues

Market themes should focus on:
- General buyer preferences and behaviors
- Industry-wide trends and patterns
- Competitive landscape insights
- Broader market opportunities

Label each theme as "{self.client_id}-specific theme" or "Market theme" accordingly.

**Instructions:**
- Do not invent quotes or evidence. Use only what is present in the findings.
- Do not use generic headlines or consulting language.
- Each theme must be supported by at least one direct customer quote.
- If a theme is specific to {self.client_id} (mentions {self.client_id} by name, or refers to {self.client_id}-specific features, experiences, or feedback), include it as a "{self.client_id}-specific theme."
- If a theme is a general market/buyer theme, label it as such.
- Do not output more than 8 themes; only include those with strong, specific evidence.

**Output format:**
[Repeat the above structure for each theme.]

ANALYZE THE FOLLOWING FINDINGS:

{{findings_data}}
"""

    def _parse_enhanced_structure_themes(self, themes_text: str, findings: pd.DataFrame) -> List[Dict]:
        """Parse themes with enhanced structure"""
        themes = []
        
        # Split by theme sections
        theme_sections = re.split(r'---', themes_text)
        
        for section in theme_sections[1:]:  # Skip first empty section
            try:
                lines = section.strip().split('\n')
                
                # Extract theme title
                theme_title = ""
                theme_statement = ""
                strategic_implications = ""
                theme_type = "Market theme"  # Default
                
                for line in lines:
                    if line.startswith('Theme Title:'):
                        theme_title = line.replace('Theme Title:', '').strip()
                    elif line.startswith('Theme Statement:'):
                        theme_statement = line.replace('Theme Statement:', '').strip()
                    elif line.startswith('Strategic Implications:'):
                        strategic_implications = line.replace('Strategic Implications:', '').strip()
                    elif f"{self.client_id}-specific theme" in line:
                        theme_type = f"{self.client_id}-specific theme"
                
                # Extract primary quote from theme statement
                primary_quote = self._extract_quote_from_statement(theme_statement)
                
                # Find supporting finding IDs based on quote similarity
                supporting_findings = self._find_supporting_findings(primary_quote, findings)
                
                # Validate theme title format
                if not self._validate_enhanced_theme_title_format(theme_title):
                    logger.warning(f"Theme title '{theme_title}' doesn't follow expected format")
                
                theme = {
                    'theme_id': f'T{len(themes) + 1}',
                    'theme_title': theme_title,
                    'primary_quote': primary_quote,
                    'theme_statement': theme_statement,
                    'strategic_implications': strategic_implications,
                    'supporting_finding_ids': supporting_findings,
                    'theme_type': 'theme',
                    'competitive_flag': True,
                    'classification': self._classify_theme(theme_statement),
                    'deal_context': 'Won: 1, Lost: 0',  # Default, could be enhanced
                    'evidence_strength': len(supporting_findings.split(',')) if supporting_findings else 1,
                    'client_specific': theme_type == f"{self.client_id}-specific theme"
                }
                
                themes.append(theme)
                
            except Exception as e:
                logger.error(f"Error parsing theme {len(themes) + 1}: {e}")
                continue
        
        return themes

    def _validate_enhanced_theme_title_format(self, title: str) -> bool:
        """Validate theme title follows the enhanced format"""
        # Check for emotional driver + specific context + business impact
        emotional_drivers = ['frustration', 'anxiety', 'pressure', 'fatigue', 'fear', 'concern', 'worry']
        business_impacts = ['drives', 'blocks', 'creates', 'impacts', 'affects', 'influences', 'jeopardizes', 'hinders']
        
        title_lower = title.lower()
        has_emotional_driver = any(driver in title_lower for driver in emotional_drivers)
        has_business_impact = any(impact in title_lower for impact in business_impacts)
        
        return has_emotional_driver and has_business_impact

    def _extract_quote_from_statement(self, statement: str) -> str:
        """Extract primary quote from theme statement"""
        # Look for quoted text
        quote_match = re.search(r'"([^"]+)"', statement)
        if quote_match:
            return quote_match.group(1)
        
        # If no quoted text, return empty
        return ""

    def _find_supporting_findings(self, quote: str, findings: pd.DataFrame) -> str:
        """Find supporting finding IDs based on quote similarity"""
        supporting_ids = []
        
        # Simple keyword matching for now
        quote_lower = quote.lower()
        
        for _, row in findings.iterrows():
            finding_quote = row.get('primary_quote', '').lower()
            if finding_quote and any(word in finding_quote for word in quote_lower.split()[:5]):
                finding_id = row.get('finding_id', '')
                if finding_id:
                    supporting_ids.append(finding_id)
        
        return ','.join(supporting_ids) if supporting_ids else ''

    def _classify_theme(self, analysis: str) -> str:
        """Classify theme based on content analysis"""
        analysis_lower = analysis.lower()
        
        if any(word in analysis_lower for word in ['cost', 'price', 'pricing', 'budget']):
            return 'REVENUE THREAT'
        elif any(word in analysis_lower for word in ['competitor', 'alternative', 'switching']):
            return 'COMPETITIVE VULNERABILITY'
        elif any(word in analysis_lower for word in ['opportunity', 'potential', 'growth']):
            return 'MARKET OPPORTUNITY'
        else:
            return 'COMPETITIVE VULNERABILITY'

    def _validate_enhanced_structure_themes(self, themes: List[Dict], findings: pd.DataFrame) -> List[Dict]:
        """Validate themes based on enhanced structure criteria"""
        validated_themes = []
        
        for theme in themes:
            # Check evidence strength
            supporting_ids = theme.get('supporting_finding_ids', '')
            evidence_count = len(supporting_ids.split(',')) if supporting_ids else 0
            
            # Check for specific customer language
            quote = theme.get('primary_quote', '')
            has_specific_language = len(quote) > 10
            
            # Check for proper structure
            statement = theme.get('theme_statement', '')
            has_proper_structure = len(statement.split('.')) >= 2
            
            # Check for client-specific detection
            is_client_specific = theme.get('client_specific', False)
            
            # Enhanced validation criteria
            if (evidence_count >= 1 and  # At least one supporting finding
                has_specific_language and  # Contains specific customer language
                has_proper_structure):  # Has proper two-sentence structure
                
                validated_themes.append(theme)
                theme_type = "Rev-specific theme" if is_client_specific else "Market theme"
                logger.info(f"Theme '{theme.get('theme_title', '')}' passed validation ({theme_type})")
            else:
                logger.warning(f"Theme '{theme.get('theme_title', '')}' failed validation")
        
        return validated_themes

    def _save_enhanced_structure_themes(self, themes: List[Dict]) -> bool:
        """Save enhanced structure themes to database"""
        try:
            for theme in themes:
                # Prepare theme data for database (skip problematic columns for now)
                theme_data = {
                    'theme_id': theme['theme_id'],
                    'theme_title': theme['theme_title'],
                    'theme_statement': theme['theme_statement'],
                    'primary_quote': theme['primary_quote'],
                    'strategic_implications': theme['strategic_implications'],
                    'supporting_finding_ids': theme['supporting_finding_ids'],
                    'theme_type': theme['theme_type'],
                    'competitive_flag': theme['competitive_flag'],
                    'classification': theme['classification'],
                    'deal_context': theme['deal_context'],
                    'theme_evidence_strength': theme.get('evidence_strength', 1),
                    'client_id': self.client_id
                }
                
                # Save to database
                success = self.db.save_theme(theme_data)
                if not success:
                    logger.error(f"Failed to save theme {theme['theme_id']}")
                    return False
            
            logger.info(f"Successfully saved {len(themes)} enhanced structure themes")
            return True
            
        except Exception as e:
            logger.error(f"Error saving enhanced structure themes: {e}")
            return False

def main():
    """Main function to run enhanced structure theme analysis"""
    import sys
    
    if len(sys.argv) > 1:
        client_id = sys.argv[1]
    else:
        client_id = 'Rev'  # Default client
    
    analyzer = EnhancedStage4ThemeAnalyzer(client_id)
    success = analyzer.analyze_themes_enhanced_structure()
    
    if success:
        print(f"✅ Enhanced structure theme analysis completed successfully for {client_id}")
    else:
        print(f"❌ Enhanced structure theme analysis failed for {client_id}")

if __name__ == "__main__":
    main() 