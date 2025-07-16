#!/usr/bin/env python3
"""
Stage 4 Theme Analyzer (Multi-Step Version)
Generates themes from Stage 3 findings using a multi-step LLM protocol:
1. LLM analyzes findings and identifies theme clusters
2. LLM generates theme titles for each cluster
3. LLM generates theme statements for each cluster
4. LLM selects the most representative quote for each theme
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

class Stage4ThemeAnalyzerMultiStep:
    def __init__(self, client_id: str = "Rev"):
        self.client_id = client_id
        self.supabase = SupabaseDatabase()
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

    def _call_llm_step1_cluster_analysis(self, findings_json: str) -> str:
        """Step 1: Analyze findings and identify theme clusters (best practice, industry-agnostic, no artificial limit)"""
        prompt = f"""
You are an expert qualitative researcher. Analyze the following customer interview findings and identify all distinct, recurring patterns, pain points, or opportunities mentioned by customers.

- Do not merge distinct issues, even if they are related. Each unique pain point, feature, or customer concern should be represented as its own theme.
- Do not limit the number of themes or clusters. Surface as many themes as are present in the data.
- Capture both major and minor themes. If a pattern or issue is mentioned by more than one customer, it should be included as a theme.
- Use industry-agnostic language (e.g., “product,” “feature,” “workflow,” “customer,” “user”).
- Themes should be as specific as possible, reflecting the actual language and context of the findings.
- For each theme, list the IDs of the supporting findings.

Return valid JSON in this format:
{{
  "themes": [
    {{
      "theme_id": "T1",
      "theme_title": "...",
      "supporting_finding_ids": ["F1", "F2", ...]
    }},
    ...
  ]
}}

FINDINGS DATA:
{findings_json}
"""
        client = openai.OpenAI(api_key=self.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert B2B SaaS competitive intelligence analyst specializing in win/loss analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=3000
        )
        return response.choices[0].message.content.strip()

    def _call_llm_step2_generate_titles(self, clusters_json: str) -> str:
        """Step 2: Generate theme titles for each cluster"""
        prompt = f"""
You are an expert B2B SaaS competitive intelligence analyst. Generate theme titles for these clusters.

CLUSTERS:
{clusters_json}

TITLE REQUIREMENTS:
- Each title MUST be a complete, standalone, declarative sentence that could be used as a presentation slide header.
- The subject should be the product, feature, or issue; the predicate should state the customer’s perception, concern, or sentiment, and the context.
- Titles should summarize customer perception, feedback, or sentiment as directly as possible, using evidence from the findings.
- Do NOT speculate about outcomes or causality unless customers explicitly stated them.
- Use neutral, evidence-based language that reflects what customers said or felt.
- If customers express emotion (frustration, anxiety, satisfaction), use that word and tie it to the context.
- If the feedback is neutral, keep the title neutral and descriptive.
- Titles MUST reference the specific workflow, scenario, or user action described in the findings or quotes (e.g., “trial preparation,” “billing,” “case initiation,” “deposition review,” etc.).
- Avoid generic business terms like “efficiency,” “productivity,” or “legal process” unless paired with a concrete, observable context.
- Use language and details from the findings themselves whenever possible.
- Be specific and actionable—someone at Rev should be able to immediately understand what customers are saying.

EXAMPLES OF CORRECT OUTPUT:
{{"theme_title": "Rev’s Transcription Accuracy is Causing Frustration During Deposition Review"}}
{{"theme_title": "Data Security is a Concern When Managing Sensitive Legal Documents"}}
{{"theme_title": "Subscription Packaging is a Concern for Small Firms"}}
{{"theme_title": "Rev’s Integration with Case Management Tools is Viewed Positively by Attorneys"}}

Return ONLY valid JSON:
{{"themes": [
  {{"cluster_id": "C1", "theme_title": "Rev’s Transcription Accuracy is Causing Frustration During Deposition Review"}},
  ...
]}}
"""
        client = openai.OpenAI(api_key=self.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert B2B SaaS competitive intelligence analyst specializing in win/loss analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        return response.choices[0].message.content.strip()

    def _call_llm_step3_generate_statements(self, clusters_with_titles: str) -> str:
        """Step 3: Generate theme statements for each cluster"""
        prompt = f"""
You are an expert B2B SaaS competitive intelligence analyst. Generate theme statements for these clusters.

CLUSTERS WITH TITLES:
{clusters_with_titles}

STATEMENT REQUIREMENTS:
- Exactly two sentences
- First sentence: Describe the business pattern or problem
- Second sentence: Provide evidence-driven synthesis (paraphrased, no quotes)
- No solutioning language ("needs improvement", "should be", etc.)
- Be specific and actionable

Return ONLY valid JSON:
{{"themes": [
  {{"cluster_id": "C1", "theme_title": "...", "theme_statement": "First sentence. Second sentence."}},
  ...
]}}
"""
        client = openai.OpenAI(api_key=self.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert B2B SaaS competitive intelligence analyst specializing in win/loss analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content.strip()

    def _call_llm_step4_select_quotes(self, theme: Dict, findings: List[Dict]) -> str:
        """Step 4: Select the most representative quote for each theme"""
        theme_title = theme.get('theme_title', '')
        theme_statement = theme.get('theme_statement', '')
        
        # Gather quotes from supporting findings
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
        
        prompt = f"""
Given this theme:
Title: {theme_title}
Statement: {theme_statement}

Select the single most representative quote from these options:
{json.dumps(quotes[:10], indent=2)}

Return ONLY the quote, nothing else.
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

    def _parse_json_output(self, llm_output: str, key: str = "themes") -> List[Dict]:
        """Parse LLM JSON output safely"""
        try:
            # Clean up markdown formatting if present
            cleaned_output = llm_output.strip()
            if cleaned_output.startswith('```json'):
                cleaned_output = cleaned_output[7:]
            if cleaned_output.endswith('```'):
                cleaned_output = cleaned_output[:-3]
            cleaned_output = cleaned_output.strip()
            
            parsed_data = json.loads(cleaned_output)
            return parsed_data.get(key, [])
        except Exception as e:
            logger.error(f"Error parsing LLM output: {e}")
            logger.error(f"Raw output: {llm_output}")
            return []

    def analyze_themes_multi_step(self, client_id: str = 'Rev') -> bool:
        """Main method: Multi-step theme analysis"""
        logger.info(f"🎯 Starting Stage 4 (Multi-Step) theme analysis for client: {client_id}")
        
        # Get findings
        findings = self.supabase.get_stage3_findings_list(client_id)
        if not findings:
            logger.warning(f"No findings found for client {client_id}")
            return False
        
        findings_json = json.dumps(findings, indent=2)
        
        # Step 1: Cluster analysis
        logger.info("Step 1: Analyzing findings and creating clusters...")
        clusters_output = self._call_llm_step1_cluster_analysis(findings_json)
        clusters = self._parse_json_output(clusters_output, "themes")
        if not clusters:
            logger.warning("No clusters generated in Step 1")
            return False
        
        # Step 2: Generate titles
        logger.info("Step 2: Generating theme titles...")
        titles_output = self._call_llm_step2_generate_titles(clusters_output)
        titles_data = self._parse_json_output(titles_output, "themes")
        
        # Merge clusters with titles
        clusters_with_titles = []
        for cluster in clusters:
            title_data = next((t for t in titles_data if t.get('cluster_id') == cluster.get('cluster_id')), {})
            cluster['theme_title'] = title_data.get('theme_title', '')
            clusters_with_titles.append(cluster)
        
        # Step 3: Generate statements
        logger.info("Step 3: Generating theme statements...")
        statements_output = self._call_llm_step3_generate_statements(json.dumps(clusters_with_titles, indent=2))
        statements_data = self._parse_json_output(statements_output, "themes")
        
        # Merge with statements
        final_themes = []
        for cluster in clusters_with_titles:
            statement_data = next((s for s in statements_data if s.get('cluster_id') == cluster.get('cluster_id')), {})
            theme = {
                'theme_title': cluster.get('theme_title', ''),
                'theme_statement': statement_data.get('theme_statement', ''),
                'cluster_id': cluster.get('cluster_id', ''),
                'finding_ids': cluster.get('supporting_finding_ids', []) # Changed from 'finding_ids' to 'supporting_finding_ids'
            }
            final_themes.append(theme)
        
        # Step 4: Select quotes
        logger.info("Step 4: Selecting representative quotes...")
        for theme in final_themes:
            quote = self._call_llm_step4_select_quotes(theme, findings)
            theme['primary_quote'] = quote
        
        # Save to database
        success = self._save_themes_to_database(final_themes)
        if success:
            logger.info(f"✅ Stage 4 (Multi-Step) theme analysis completed successfully for client {client_id}")
        else:
            logger.error(f"❌ Failed to save themes for client {client_id}")
        return success

    def _save_themes_to_database(self, themes: List[Dict[str, Any]]) -> bool:
        """Save themes to database"""
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
        return self.analyze_themes_multi_step(self.client_id)

def main():
    """Main function to run Stage 4 theme analysis (Multi-Step Version)"""
    import sys
    import argparse
    parser = argparse.ArgumentParser(description='Stage 4 Theme Analysis (Multi-Step Version)')
    parser.add_argument('--client_id', type=str, default='Rev', help='Client ID to analyze')
    args = parser.parse_args()
    client_id = args.client_id
    try:
        analyzer = Stage4ThemeAnalyzerMultiStep(client_id)
        success = analyzer.process_themes()
        if success:
            print(f"✅ Stage 4 theme analysis (Multi-Step) completed successfully for client: {client_id}")
            sys.exit(0)
        else:
            print(f"❌ Stage 4 theme analysis (Multi-Step) failed for client: {client_id}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error running Stage 4 theme analysis (Multi-Step): {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 