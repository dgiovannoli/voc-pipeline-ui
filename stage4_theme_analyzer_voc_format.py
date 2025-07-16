#!/usr/bin/env python3
"""
Stage 4 Theme Analyzer - Voice of Customer Format
Outputs themes in a research-driven format with clear customer voice
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

class VoiceOfCustomerStage4Analyzer:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.db = SupabaseDatabase()
        
    def analyze_themes_voc_format(self) -> bool:
        """Analyze themes using Voice of Customer format"""
        try:
            # Get Stage 3 findings
            findings = self.db.get_stage3_findings(self.client_id)
            if findings.empty:
                logger.error("No Stage 3 findings found")
                return False
                
            logger.info(f"Found {len(findings)} Stage 3 findings")
            
            # Prepare findings for analysis
            findings_json = self._prepare_findings_json(findings)
            
            # Generate themes in VOC format
            themes_data = self._generate_voc_themes(findings_json, findings)
            
            # Save themes to database
            success = self._save_voc_themes(themes_data)
            
            if success:
                logger.info(f"Successfully generated {len(themes_data)} themes in VOC format")
                return True
            else:
                logger.error("Failed to save themes")
                return False
                
        except Exception as e:
            logger.error(f"Error in VOC theme analysis: {e}")
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
                'classification': row.get('finding_category', '')
            }
            findings_list.append(finding)
        
        return json.dumps(findings_list, indent=2)
    
    def _generate_voc_themes(self, findings_json: str, findings: pd.DataFrame) -> List[Dict]:
        """Generate themes in Voice of Customer format"""
        
        prompt = f"""
You are analyzing customer interview data from legal professionals to identify key themes that impact their buying decisions.

Based on the following customer quotes and insights, identify the most important themes that reveal customer preferences, pain points, and buying criteria.

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
- Generate 5-8 themes total

Customer Data:
{findings_json}

Generate themes in EXACTLY this format:

Theme Title: "Fear of Video Evidence Leaks Drives Security Decisions"
Voice of Customer: [Full customer quote]
What Your Buyers Are Telling You: [Two-sentence structure with customer evidence]
The Opportunity: [Strategic implications]

Ensure all analysis is based directly on the customer data provided.
"""

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a research analyst specializing in B2B customer insights. Provide neutral, data-driven analysis based on customer quotes. Generate themes in the exact format specified."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=6000,
                temperature=0.2
            )
            
            themes_text = response.choices[0].message.content
            
            # Parse themes from response
            themes = self._parse_voc_themes(themes_text, findings)
            
            # Validate themes
            if not themes:
                logger.warning("No themes generated, retrying with different approach")
                return []
            
            logger.info(f"Successfully generated {len(themes)} themes")
            return themes
            
        except Exception as e:
            logger.error(f"Error generating VOC themes: {e}")
            return []
    
    def _parse_voc_themes(self, themes_text: str, findings: pd.DataFrame) -> List[Dict]:
        """Parse themes from AI response"""
        themes = []
        
        # Split by theme markers
        theme_sections = re.split(r'Theme Title:', themes_text)
        
        for section in theme_sections[1:]:  # Skip first empty section
            try:
                lines = section.strip().split('\n')
                
                # Extract theme title - already in correct format
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
                    'deal_context': 'Won: 1, Lost: 0'  # Default, could be enhanced
                }
                
                themes.append(theme)
                
            except Exception as e:
                logger.warning(f"Error parsing theme section: {e}")
                continue
        
        return themes
    
    def _find_supporting_findings(self, quote: str, findings: pd.DataFrame) -> str:
        """Find finding IDs that support this theme based on quote similarity"""
        # Simple keyword matching - could be enhanced with semantic similarity
        keywords = quote.lower().split()[:10]  # First 10 words as keywords
        
        supporting_ids = []
        for _, row in findings.iterrows():
            finding_text = f"{row.get('primary_quote', '')} {row.get('finding_statement', '')}".lower()
            if any(keyword in finding_text for keyword in keywords):
                supporting_ids.append(row.get('finding_id', ''))
        
        return ','.join(supporting_ids[:3])  # Limit to 3 findings
    
    def _extract_insight(self, title: str) -> str:
        """Extract insight from theme title to create formatted title"""
        # The new structure doesn't need insight extraction since titles are already formatted
        # This method is kept for backward compatibility but should not be used
        return title
    
    def _validate_theme_title_format(self, title: str) -> bool:
        """Validate that theme title follows the expected format"""
        # Check for emotional drivers
        emotional_drivers = ['fear', 'anxiety', 'pressure', 'fatigue', 'frustration']
        has_emotional_driver = any(driver in title.lower() for driver in emotional_drivers)
        
        # Check for business impact words
        impact_words = ['drives', 'blocks', 'creates', 'enables', 'threatens']
        has_impact_word = any(word in title.lower() for word in impact_words)
        
        # Check length (5-10 words)
        word_count = len(title.split())
        proper_length = 5 <= word_count <= 10
        
        return has_emotional_driver and has_impact_word and proper_length
    
    def _classify_theme(self, analysis: str) -> str:
        """Classify theme based on content analysis"""
        analysis_lower = analysis.lower()
        
        if any(word in analysis_lower for word in ['cost', 'price', 'expensive', 'budget']):
            return 'REVENUE THREAT'
        elif any(word in analysis_lower for word in ['accuracy', 'quality', 'precision']):
            return 'COMPETITIVE VULNERABILITY'
        elif any(word in analysis_lower for word in ['opportunity', 'advantage', 'benefit']):
            return 'MARKET OPPORTUNITY'
        else:
            return 'COMPETITIVE VULNERABILITY'
    
    def _save_voc_themes(self, themes: List[Dict]) -> bool:
        """Save themes to database in VOC format"""
        try:
            for theme in themes:
                # Map to database schema
                theme_data = {
                    'client_id': self.client_id,
                    'theme_id': theme['theme_id'],
                    'theme_type': theme['theme_type'],
                    'competitive_flag': theme['competitive_flag'],
                    'theme_title': theme['theme_title'],
                    'theme_statement': theme['theme_statement'],
                    'classification': theme['classification'],
                    'deal_context': theme['deal_context'],
                    'primary_quote': theme['primary_quote'],
                    'supporting_finding_ids': theme['supporting_finding_ids'],
                    'strategic_implications': theme['strategic_implications']
                }
                
                # Save to database
                success = self.db.save_theme(theme_data)
                if not success:
                    logger.error(f"Failed to save theme {theme['theme_id']}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving VOC themes: {e}")
            return False

def main():
    """Run Voice of Customer Stage 4 analysis"""
    analyzer = VoiceOfCustomerStage4Analyzer("Rev")
    success = analyzer.analyze_themes_voc_format()
    
    if success:
        print("✅ Voice of Customer Stage 4 analysis completed successfully")
    else:
        print("❌ Voice of Customer Stage 4 analysis failed")

if __name__ == "__main__":
    main() 