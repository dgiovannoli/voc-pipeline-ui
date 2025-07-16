#!/usr/bin/env python3
"""
Stage 4 Theme Analyzer - Evidence-Driven Format
Generates themes based on evidence strength rather than artificial counts
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

class EvidenceDrivenStage4Analyzer:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.db = SupabaseDatabase()
        
    def analyze_themes_evidence_driven(self) -> bool:
        """Analyze themes using evidence-driven approach"""
        try:
            # Get Stage 3 findings
            findings = self.db.get_stage3_findings(self.client_id)
            if findings.empty:
                logger.error("No Stage 3 findings found")
                return False
                
            logger.info(f"Found {len(findings)} Stage 3 findings")
            
            # Prepare findings for analysis
            findings_json = self._prepare_findings_json(findings)
            
            # Generate themes using evidence-driven approach
            themes_data = self._generate_evidence_driven_themes(findings_json, findings)
            
            # Save themes to database
            success = self._save_evidence_driven_themes(themes_data)
            
            if success:
                logger.info(f"Successfully generated {len(themes_data)} evidence-driven themes")
                return True
            else:
                logger.error("Failed to save themes")
                return False
                
        except Exception as e:
            logger.error(f"Error in evidence-driven theme analysis: {e}")
            return False
    
    def _prepare_findings_json(self, findings: pd.DataFrame) -> str:
        """Prepare findings as JSON for analysis"""
        findings_list = []
        for _, row in findings.iterrows():
            finding = {
                'finding_id': row.get('finding_id', ''),
                'quote': row.get('primary_quote', ''),
                'insight': row.get('finding_statement', ''),
                'company_id': row.get('interview_company', ''),
                'classification': row.get('finding_category', ''),
                'priority_level': row.get('priority_level', ''),
                'evidence_strength': row.get('evidence_strength', 1)
            }
            findings_list.append(finding)
        
        return json.dumps(findings_list, indent=2)
    
    def _generate_evidence_driven_themes(self, findings_json: str, findings: pd.DataFrame) -> List[Dict]:
        """Generate themes based on evidence strength rather than artificial counts"""
        
        prompt = f"""
You are analyzing customer interview data from legal professionals to identify key themes that impact their buying decisions.

Based on the following customer quotes and insights, identify themes that have strong evidence and clear business implications.

GENERATE THEMES BASED ON EVIDENCE STRENGTH:

1. MARKET THEMES: Cross-company buyer behavior patterns
   - Generate themes when you find strong cross-company evidence (3+ companies)
   - Focus on competitive dynamics, pricing sensitivity, integration needs
   - Each theme must have clear supporting evidence from multiple companies

2. PRODUCT THEMES: Rev-specific feature feedback  
   - Generate themes when you find specific Rev feature mentions
   - Focus on Rev's accuracy, pricing, integrations, user experience
   - Can be single-company if the feedback is highly specific to Rev
   - Must include concrete feature references or improvement suggestions

QUALITY CRITERIA:
- Each theme must have clear supporting evidence
- Avoid generic themes without specific customer language
- Prioritize themes with actionable business implications
- Include specific quotes that demonstrate the pattern

For each theme, provide EXACTLY in this format:

Theme Title: [Emotional Driver] + [Specific Context] + [Business Impact]
Voice of Customer: [The most representative customer quote that illustrates this theme]
What Your Buyers Are Telling You: [Two-sentence structure: Sentence 1 = Decision behavior or specific problem with consequence. Sentence 2 = Customer evidence with direct quotes]
The Opportunity: [Strategic implications for product positioning and pricing]

Requirements:
- Theme titles must follow: [Emotional Driver] + [Specific Context] + [Business Impact]
- Emotional drivers: Fear, Anxiety, Pressure, Fatigue, Frustration
- Business impacts: Drives, Blocks, Creates, etc.
- Theme statements must be two sentences with clear flow
- Sentence 1: Market impact or decision behavior
- Sentence 2: Specific customer evidence with quotes
- Base everything on the provided customer data
- Focus on themes that reveal buying criteria, preferences, or pain points
- Generate themes based on evidence strength, not artificial counts

Customer Data:
{findings_json}

Generate themes in EXACTLY this format:

Theme Title: "Fear of Video Evidence Leaks Drives Security Decisions"
Voice of Customer: [Full customer quote]
What Your Buyers Are Telling You: [Two-sentence structure with customer evidence]
The Opportunity: [Strategic implications]

Ensure all analysis is based directly on the customer data provided.
Only generate themes that have strong supporting evidence.
"""

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a research analyst specializing in B2B customer insights. Provide neutral, data-driven analysis based on customer quotes. Generate themes based on evidence strength, not artificial counts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=6000,
                temperature=0.2
            )
            
            themes_text = response.choices[0].message.content
            
            # Parse themes from response
            themes = self._parse_evidence_driven_themes(themes_text, findings)
            
            # Validate themes based on evidence strength
            validated_themes = self._validate_theme_evidence(themes, findings)
            
            if not validated_themes:
                logger.warning("No themes passed evidence validation")
                return []
            
            logger.info(f"Successfully generated {len(validated_themes)} evidence-driven themes")
            return validated_themes
            
        except Exception as e:
            logger.error(f"Error generating evidence-driven themes: {e}")
            return []
    
    def _parse_evidence_driven_themes(self, themes_text: str, findings: pd.DataFrame) -> List[Dict]:
        """Parse themes from AI response"""
        themes = []
        
        # Split by theme markers
        theme_sections = re.split(r'Theme Title:', themes_text)
        
        for section in theme_sections[1:]:  # Skip first empty section
            try:
                lines = section.strip().split('\n')
                
                # Extract theme title
                theme_title = lines[0].strip()
                
                # Extract Voice of Customer quote
                voc_start = section.find('Voice of Customer:')
                voc_end = section.find('What Your Buyers Are Telling You:')
                if voc_start == -1 or voc_end == -1:
                    logger.warning(f"Could not parse Voice of Customer for theme {len(themes) + 1}")
                    continue
                voice_of_customer = section[voc_start + 18:voc_end].strip()
                
                # Extract What Your Buyers Are Telling You
                buyers_start = section.find('What Your Buyers Are Telling You:')
                buyers_end = section.find('The Opportunity:')
                if buyers_start == -1 or buyers_end == -1:
                    logger.warning(f"Could not parse What Your Buyers Are Telling You for theme {len(themes) + 1}")
                    continue
                buyers_analysis = section[buyers_start + 35:buyers_end].strip()
                
                # Extract The Opportunity
                opportunity_start = section.find('The Opportunity:')
                if opportunity_start == -1:
                    logger.warning(f"Could not parse The Opportunity for theme {len(themes) + 1}")
                    continue
                opportunity = section[opportunity_start + 17:].strip()
                
                # Find supporting finding IDs based on quote similarity
                supporting_findings = self._find_supporting_findings(voice_of_customer, findings)
                
                # Validate theme title format
                if not self._validate_theme_title_format(theme_title):
                    logger.warning(f"Theme title '{theme_title}' doesn't follow expected format")
                
                theme = {
                    'theme_id': f'T{len(themes) + 1}',
                    'theme_title': theme_title,
                    'primary_quote': voice_of_customer,
                    'theme_statement': buyers_analysis,
                    'strategic_implications': opportunity,
                    'supporting_finding_ids': supporting_findings,
                    'theme_type': 'theme',
                    'competitive_flag': True,
                    'classification': self._classify_theme(buyers_analysis),
                    'deal_context': 'Won: 1, Lost: 0',  # Default, could be enhanced
                    'evidence_strength': len(supporting_findings.split(',')) if supporting_findings else 1
                }
                
                themes.append(theme)
                
            except Exception as e:
                logger.error(f"Error parsing theme {len(themes) + 1}: {e}")
                continue
        
        return themes
    
    def _validate_theme_evidence(self, themes: List[Dict], findings: pd.DataFrame) -> List[Dict]:
        """Validate themes based on evidence strength"""
        validated_themes = []
        
        for theme in themes:
            # Check evidence strength
            supporting_ids = theme.get('supporting_finding_ids', '')
            evidence_count = len(supporting_ids.split(',')) if supporting_ids else 0
            
            # Check for specific customer language
            quote = theme.get('primary_quote', '')
            has_specific_language = self._has_specific_customer_language(quote)
            
            # Check for actionable implications
            opportunity = theme.get('strategic_implications', '')
            has_actionable_implications = len(opportunity.split()) > 10
            
            # Evidence validation criteria
            if (evidence_count >= 1 and  # At least one supporting finding
                has_specific_language and  # Contains specific customer language
                has_actionable_implications):  # Has actionable implications
                
                validated_themes.append(theme)
                logger.info(f"Theme '{theme.get('theme_title', '')}' passed evidence validation")
            else:
                logger.warning(f"Theme '{theme.get('theme_title', '')}' failed evidence validation")
        
        return validated_themes
    
    def _has_specific_customer_language(self, quote: str) -> bool:
        """Check if quote contains specific customer language"""
        if not quote:
            return False
        
        # Look for specific indicators
        specific_indicators = [
            'because', 'when', 'if', 'since', 'while', 'although', 'however', 'but',
            'accuracy', 'speed', 'cost', 'integration', 'security', 'compliance',
            'transcript', 'transcription', 'turnaround', 'timeline', 'workflow',
            'Rev', 'Turbo Scribe', 'Otter', 'Westlaw', 'LexisNexis', 'Clio'
        ]
        
        quote_lower = quote.lower()
        return any(indicator in quote_lower for indicator in specific_indicators)
    
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
    
    def _validate_theme_title_format(self, title: str) -> bool:
        """Validate theme title follows the required format"""
        # Check for emotional driver + specific context + business impact
        emotional_drivers = ['fear', 'anxiety', 'pressure', 'fatigue', 'frustration']
        business_impacts = ['drives', 'blocks', 'creates', 'impacts', 'affects', 'influences']
        
        title_lower = title.lower()
        has_emotional_driver = any(driver in title_lower for driver in emotional_drivers)
        has_business_impact = any(impact in title_lower for impact in business_impacts)
        
        return has_emotional_driver and has_business_impact
    
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
    
    def _save_evidence_driven_themes(self, themes: List[Dict]) -> bool:
        """Save evidence-driven themes to database"""
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
                    # Skip: theme_category, theme_companies_affected for now
                }
                
                # Save to database
                success = self.db.save_theme(theme_data)
                if not success:
                    logger.error(f"Failed to save theme {theme['theme_id']}")
                    return False
            
            logger.info(f"Successfully saved {len(themes)} evidence-driven themes")
            return True
            
        except Exception as e:
            logger.error(f"Error saving evidence-driven themes: {e}")
            return False

def main():
    """Main function to run evidence-driven theme analysis"""
    import sys
    
    if len(sys.argv) > 1:
        client_id = sys.argv[1]
    else:
        client_id = 'Rev'  # Default client
    
    analyzer = EvidenceDrivenStage4Analyzer(client_id)
    success = analyzer.analyze_themes_evidence_driven()
    
    if success:
        print(f"✅ Evidence-driven theme analysis completed successfully for {client_id}")
    else:
        print(f"❌ Evidence-driven theme analysis failed for {client_id}")

if __name__ == "__main__":
    main() 