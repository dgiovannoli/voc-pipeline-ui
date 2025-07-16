#!/usr/bin/env python3
"""
Stage 4 Theme Analyzer (Two-Step Version)
Generates themes from Stage 3 findings using a two-step LLM protocol:
1. LLM generates only theme statements (no quotes)
2. LLM selects the most representative quote for each theme
"""

import os
import json
import logging
import pandas as pd
import re
from typing import List, Dict, Any, Optional
import openai
import numpy as np
from supabase_database import SupabaseDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Stage4ThemeAnalyzerTwoStep:
    def __init__(self, client_id: str = "Rev"):
        self.client_id = client_id
        self.supabase = SupabaseDatabase()
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.theme_prompt = self._load_theme_prompt()

    def _load_theme_prompt(self) -> str:
        return """
NEW THEME FRAMEWORK REQUIREMENTS (TWO-STEP VERSION)
==================================================

THEME TITLE STRUCTURE: [Emotional Driver] (encouraged) + [Specific Issue/Behavior] + [Impact/Outcome]

**THEME TYPE REQUIREMENTS:**
- For findings with classification = "Rev-specific": Generate a Rev-specific theme. The title MUST start with "Rev's ..." and be specific to Rev's features, workflows, or user experience.
- For findings with classification = "Market trend": Generate a general market theme. The title MUST NOT start with "Rev's ..." and should describe broader industry patterns.
- You MUST check the 'classification' field for each finding and generate the correct type of theme.

**TITLE STRUCTURE GUIDANCE:**
- Strongly encourage including an emotional driver (e.g., Frustration, Anxiety, Relief, Excitement) when the evidence or customer language expresses emotion, pain, or feel.
- If the evidence is neutral, use a specific, business-focused title without an emotional driver.
- Title structure: [Emotional Driver] (encouraged) + [Specific Issue/Behavior] + [Impact/Outcome]

**EXAMPLES OF CORRECT OUTPUT:**
{"theme_title": "Frustration with Rev's Speaker Identification Blocks Trial Preparation", "theme_statement": "Attorneys experience significant frustration when Rev's speaker identification fails during multi-party legal recordings, making trial preparation more difficult. Interviewees are reluctant to rely on Rev for complex cases when accuracy is not guaranteed."}
{"theme_title": "Anxiety Over Rising Costs Jeopardizes Small Firm Viability", "theme_statement": "Small firm attorneys express anxiety about rising costs for Rev's transcription services, which threatens their ability to remain competitive. Many are considering alternative solutions due to budget constraints."}
{"theme_title": "Rev's Integration Gap with Westlaw Hinders Legal Workflow", "theme_statement": "Legal professionals report workflow inefficiencies when Rev does not integrate with Westlaw, requiring manual data transfer. This gap reduces Rev's value for firms seeking seamless research and transcription."}
{"theme_title": "Cost Concerns Limit Software Adoption", "theme_statement": "Decision-makers avoid adopting new legal tech solutions due to concerns about ongoing subscription costs. Many firms delay purchases until pricing models become more flexible."}
{"theme_title": "Excitement About AI-Driven Transcription Boosts Productivity", "theme_statement": "Attorneys express excitement about AI-driven transcription tools that improve productivity and reduce turnaround times. Firms adopting these solutions report faster case preparation and higher client satisfaction."}

**EXAMPLES OF INCORRECT OUTPUT:**
{"theme_title": "Rev's Speaker Identification Issues", ...} (✗ Missing emotional driver, too generic)
{"theme_title": "Legal Tech Adoption", ...} (✗ Too vague, missing specific issue/impact)
{"theme_title": "Rev's Integration", ...} (✗ Too short, missing context and impact)
{"theme_title": "Cost Concerns", ...} (✗ Too short, missing context and impact)
{"theme_title": "Frustration with Legal Tech", ...} (✗ Missing specific issue/behavior and impact)

**VALIDATION RULES:**
1. Theme titles for Rev-specific themes MUST start with "Rev's ..." and be specific to Rev.
2. Theme titles for market themes MUST NOT start with "Rev's ..." and should describe broader industry patterns.
3. Titles should follow the structure: [Emotional Driver] (encouraged) + [Specific Issue/Behavior] + [Impact/Outcome].
4. Theme statements MUST be exactly two sentences, paraphrased, and contain no direct quotes.
5. No solutioning language ("needs improvement", "should be", "must", etc.).
6. No generic statements; must be specific and paraphrased.

**IMPORTANT:**
- Do NOT include direct quotes or quoted phrases in the theme statement. Only paraphrased synthesis is allowed.
- Do NOT invent or estimate specific numbers, percentages, or metrics unless directly stated in the evidence.

"""

    def _call_llm_for_theme_statements(self, findings_json: str) -> str:
        """Step 1: Call LLM to generate theme statements (no quotes)"""
        prompt = f"""
{self.theme_prompt}
FINDINGS DATA TO ANALYZE:
{findings_json}
Return ONLY valid, minified JSON (no markdown, no explanations, no extra text, no comments). Example:
{{"themes": [...]}}
"""
        client = openai.OpenAI(api_key=self.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert B2B SaaS competitive intelligence analyst specializing in win/loss analysis. Generate executive-ready strategic themes from customer interview findings."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        return response.choices[0].message.content.strip()

    def _parse_llm_themes_output(self, llm_output: str) -> List[Dict]:
        # Same as before, but expects only theme_title and theme_statement
        try:
            parsed_data = json.loads(llm_output)
            return parsed_data.get('themes', [])
        except Exception as e:
            logger.error(f"Error parsing LLM themes output: {e}")
            return []

    def _call_llm_for_quote(self, theme: Dict, findings: List[Dict]) -> str:
        """Step 2: Call LLM to select the most representative direct quote for a theme"""
        # Prepare a prompt with the theme and supporting findings
        theme_title = theme.get('theme_title', '')
        theme_statement = theme.get('theme_statement', '')
        # Gather all quotes from supporting findings
        quotes = []
        for f in findings:
            q = f.get('primary_quote', '')
            if q:
                quotes.append(q)
            q2 = f.get('secondary_quote', '')
            if q2:
                quotes.append(q2)
        quotes = [q for q in quotes if q.strip()]
        if not quotes:
            return ""
        # Prompt for LLM
        prompt = f"""
Given the following theme:
Title: {theme_title}
Statement: {theme_statement}

And these direct quotes from interviewees:
{json.dumps(quotes, indent=2)}

Select the single most representative direct quote for this theme. Return ONLY the quote, nothing else.
"""
        client = openai.OpenAI(api_key=self.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert B2B SaaS qualitative researcher. Select the most representative direct quote for a theme."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=256
        )
        return response.choices[0].message.content.strip().strip('"')

    def analyze_themes_two_step(self, client_id: str = 'Rev') -> bool:
        """Main method: Step 1 - generate theme statements; Step 2 - select quotes"""
        logger.info(f"🎯 Starting Stage 4 (Two-Step) theme analysis for client: {client_id}")
        # Step 1: Get findings and generate theme statements
        findings = self.supabase.get_stage3_findings_list(client_id)
        if not findings:
            logger.warning(f"No findings found for client {client_id}")
            return False
        findings_json = json.dumps(findings, indent=2)
        llm_output = self._call_llm_for_theme_statements(findings_json)
        themes = self._parse_llm_themes_output(llm_output)
        if not themes:
            logger.warning("No themes generated by LLM")
            return False
        # Step 2: For each theme, select the most representative quote
        for theme in themes:
            # Find supporting findings (simple match: all findings for now)
            quote = self._call_llm_for_quote(theme, findings)
            theme['primary_quote'] = quote
        # Save to database
        success = self._save_themes_to_database(themes)
        if success:
            logger.info(f"✅ Stage 4 (Two-Step) theme analysis completed successfully for client {client_id}")
        else:
            logger.error(f"❌ Failed to save themes for client {client_id}")
        return success

    def _save_themes_to_database(self, themes: List[Dict[str, Any]]) -> bool:
        # Use the same logic as before, but only save theme_title, theme_statement, primary_quote
        try:
            if not themes:
                logger.warning("No themes to save")
                return False
            success_count = 0
            for theme in themes:
                theme_data = {
                    'client_id': self.client_id,
                    'theme_title': theme.get('theme_title', ''),
                    'theme_statement': theme.get('theme_statement', ''),
                    'primary_quote': theme.get('primary_quote', ''),
                    'theme_type': 'theme',
                }
                if self.supabase.save_stage4_theme(theme_data):
                    success_count += 1
            logger.info(f"✅ Successfully saved {success_count}/{len(themes)} themes to database")
            return success_count > 0
        except Exception as e:
            logger.error(f"Error saving themes to database: {e}")
            return False

    def process_themes(self, client_id: str = None) -> bool:
        if client_id:
            self.client_id = client_id
        return self.analyze_themes_two_step(self.client_id)

def main():
    """Main function to run Stage 4 theme analysis (Two-Step Version)"""
    import sys
    import argparse
    parser = argparse.ArgumentParser(description='Stage 4 Theme Analysis (Two-Step Version)')
    parser.add_argument('--client_id', type=str, default='Rev', help='Client ID to analyze')
    args = parser.parse_args()
    client_id = args.client_id
    try:
        analyzer = Stage4ThemeAnalyzerTwoStep(client_id)
        success = analyzer.process_themes()
        if success:
            print(f"✅ Stage 4 theme analysis (Two-Step) completed successfully for client: {client_id}")
            sys.exit(0)
        else:
            print(f"❌ Stage 4 theme analysis (Two-Step) failed for client: {client_id}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error running Stage 4 theme analysis (Two-Step): {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 