#!/usr/bin/env python3
"""
LLM-Based Theme Deduplication Engine
Uses OpenAI to intelligently identify semantic duplicates while preserving specificity
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
import argparse

# Import from current directory
from supabase_database import SupabaseDatabase
from openai import OpenAI
import os

class LLMThemeDeduplicator:
    def __init__(self, client_id: str, openai_client: OpenAI):
        self.client_id = client_id
        self.openai_client = openai_client
        self.db = SupabaseDatabase()
        
        # The expert prompt for theme deduplication
        self.dedup_prompt = """You are a strict qualitative-dedupe analyst for B2B SaaS win/loss themes. Your job: find redundant themes without losing specificity from interviews. Prefer precision over recall.

Key concepts:
- Subject ≈ parent topic (e.g., Integration, Pricing, Support, Efficiency).
- Discovered/Research themes can be merged. Interview themes are never merged; they become Evidence.

Scoring rules:
- Cosine similarity threshold (LLM-estimated semantic similarity on 0–1 scale).
- Noun-phrase Jaccard overlap on extracted key phrases.
- Entity overlap on systems/brands/processes (e.g., Shopify, WMS, CRM, rate cards, carriers).
- Sentiment/polarity alignment (both problem or both praise).
- Domain facet match (Integration, Pricing, Support, Efficiency).

Within-Subject gate: cosine ≥ 0.74 AND noun Jaccard ≥ 0.35.
Cross-Subject gate: cosine ≥ 0.78 AND entity overlap ≥ 0.50.

Do-NOT-Merge rules (any one triggers DENY):
- Conflicting entities (e.g., Shopify vs WMS/CRM) without shared parent qualifier.
- Opposite sentiment/polarity.
- Different stakeholder focus (Ops vs Finance/Legal).
- Modality mismatch (Pricing vs Support; Discovery vs Implementation).
- Temporal mismatch (Pilot vs steady-state) unless explicitly the same.

Banding:
- High ≥ 0.80
- Medium 0.70–0.79
- Low < 0.70 (do not recommend)

Max cluster size: 7 (split by dominant entity if exceeded).
Per-subject cap: 12 suggestions max.

Interview themes are never merged; map them as Evidence to a canonical theme.

Output JSON schema (array of objects):
{
  "pair_type": "within_subject" | "cross_subject",
  "subject_A": "...",
  "subject_B": "...",
  "theme_id_A": "...",
  "theme_id_B": "...",
  "statement_A": "...",
  "statement_B": "...",
  "scores": {
    "cosine": 0.00,
    "noun_jaccard": 0.00,
    "entity_overlap": 0.00,
    "sentiment_align": true,
    "facet_match": true
  },
  "decision_band": "High" | "Medium" | "Low",
  "merge_recommendation": "MERGE" | "DO_NOT_MERGE",
  "canonical_label_suggestion": "...",
  "rationale": "Short, specific reason citing shared phrases/entities and alignment.",
  "evidence_policy": "If either is an interview_theme_* => treat as Evidence, not merged."
}

Return only valid JSON."""

    def fetch_themes(self) -> pd.DataFrame:
        """Fetch all themes for the client"""
        research_themes = self.db.fetch_research_themes_all(self.client_id)
        interview_themes = self.db.fetch_interview_level_themes(self.client_id)
        
        if research_themes.empty and interview_themes.empty:
            return pd.DataFrame()
        
        # Prepare research themes
        research_df = research_themes.copy()
        research_df['source'] = research_df['origin'].map(lambda x: 'discovered' if str(x).startswith('DISCOVERED:') else 'research')
        research_df['subject'] = research_df['harmonized_subject'].fillna('Uncategorized')
        
        # Prepare interview themes
        interview_df = interview_themes.copy()
        interview_df['source'] = 'interview'
        interview_df['subject'] = interview_df.get('subject', 'Interview')
        
        # Combine all themes
        all_themes = pd.concat([research_df, interview_df], ignore_index=True)
        return all_themes

    def create_theme_pairs(self, themes_df: pd.DataFrame) -> List[Dict]:
        """Create pairs of themes for LLM analysis"""
        pairs = []
        
        # Only create pairs between research/discovered themes (no interview theme merging)
        research_themes = themes_df[themes_df['source'].isin(['research', 'discovered'])]
        
        if len(research_themes) < 2:
            return pairs
        
        # Create all possible pairs
        for i in range(len(research_themes)):
            for j in range(i + 1, len(research_themes)):
                theme_a = research_themes.iloc[i]
                theme_b = research_themes.iloc[j]
                
                pair = {
                    'theme_id_A': theme_a['theme_id'],
                    'theme_id_B': theme_b['theme_id'],
                    'statement_A': theme_a['theme_statement'],
                    'statement_B': theme_b['theme_statement'],
                    'subject_A': theme_a['subject'],
                    'subject_B': theme_b['subject'],
                    'source_A': theme_a['source'],
                    'source_B': theme_b['source']
                }
                pairs.append(pair)
        
        return pairs

    def analyze_pairs_with_llm(self, theme_pairs: List[Dict]) -> List[Dict]:
        """Use LLM to analyze theme pairs for duplicates"""
        if not theme_pairs:
            return []
        
        # Process pairs in batches to avoid token limits
        batch_size = 5
        all_results = []
        
        for i in range(0, len(theme_pairs), batch_size):
            batch = theme_pairs[i:i + batch_size]
            
            # Create the analysis prompt for this batch
            batch_prompt = self.dedup_prompt + "\n\nAnalyze these theme pairs:\n\n"
            
            for j, pair in enumerate(batch):
                batch_prompt += f"Pair {j+1}:\n"
                batch_prompt += f"Theme A ({pair['source_A']}): {pair['statement_A']}\n"
                batch_prompt += f"Theme B ({pair['source_B']}): {pair['statement_B']}\n"
                batch_prompt += f"Subject A: {pair['subject_A']}\n"
                batch_prompt += f"Subject B: {pair['subject_B']}\n\n"
            
            batch_prompt += "Return JSON array of analysis results for each pair."
            
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a precise theme deduplication analyst. Return only valid JSON."},
                        {"role": "user", "content": batch_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2000
                )
                
                # Parse the response
                content = response.choices[0].message.content
                try:
                    # Extract JSON from the response
                    json_start = content.find('[')
                    json_end = content.rfind(']') + 1
                    if json_start != -1 and json_end != -1:
                        json_str = content[json_start:json_end]
                        results = json.loads(json_str)
                        all_results.extend(results)
                    else:
                        print(f"Warning: Could not extract JSON from response: {content[:100]}...")
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse JSON response: {e}")
                    print(f"Response content: {content[:200]}...")
                    
            except Exception as e:
                print(f"Error calling OpenAI API: {e}")
                continue
        
        return all_results

    def export_results(self, results: List[Dict], output_path: str):
        """Export results to CSV"""
        if not results:
            print("No results to export")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Flatten the scores column
        if 'scores' in df.columns:
            scores_df = pd.json_normalize(df['scores'])
            df = pd.concat([df.drop('scores', axis=1), scores_df], axis=1)
        
        # Export to CSV
        df.to_csv(output_path, index=False)
        print(f"Exported {len(results)} analysis results to {output_path}")
        
        # Print summary
        merge_count = len([r for r in results if r.get('merge_recommendation') == 'MERGE'])
        high_count = len([r for r in results if r.get('decision_band') == 'High'])
        medium_count = len([r for r in results if r.get('decision_band') == 'Medium'])
        
        print(f"\n📊 Analysis Summary:")
        print(f"  Total pairs analyzed: {len(results)}")
        print(f"  Recommended for merge: {merge_count}")
        print(f"  High confidence: {high_count}")
        print(f"  Medium confidence: {medium_count}")

def main():
    parser = argparse.ArgumentParser(description='LLM-Based Theme Deduplication Engine')
    parser.add_argument('--client', required=True, help='Client ID to process')
    parser.add_argument('--output', default='llm_dedup_results.csv',
                       help='Output CSV file path (default: llm_dedup_results.csv)')
    parser.add_argument('--openai-key', help='OpenAI API key (or set OPENAI_API_KEY env var)')
    
    args = parser.parse_args()
    
    # Initialize OpenAI client
    api_key = args.openai_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OpenAI API key required. Set OPENAI_API_KEY environment variable or use --openai-key")
        return
    
    openai_client = OpenAI(api_key=api_key)
    
    print(f"🔍 LLM-Based Theme Deduplication for client: {args.client}")
    
    # Initialize deduplicator
    deduplicator = LLMThemeDeduplicator(args.client, openai_client)
    
    # Fetch themes
    print("📥 Fetching themes...")
    themes_df = deduplicator.fetch_themes()
    
    if themes_df.empty:
        print("❌ No themes found")
        return
    
    print(f"✅ Found {len(themes_df)} themes")
    
    # Create theme pairs
    print("🔗 Creating theme pairs...")
    theme_pairs = deduplicator.create_theme_pairs(themes_df)
    
    if not theme_pairs:
        print("❌ No theme pairs to analyze")
        return
    
    print(f"✅ Created {len(theme_pairs)} theme pairs")
    
    # Analyze with LLM
    print("🧠 Analyzing pairs with LLM...")
    results = deduplicator.analyze_pairs_with_llm(theme_pairs)
    
    if not results:
        print("❌ No analysis results")
        return
    
    print(f"✅ LLM analysis complete: {len(results)} results")
    
    # Export results
    deduplicator.export_results(results, args.output)
    
    print(f"\n🎯 Next steps:")
    print(f"  1. Review high-confidence merge recommendations")
    print(f"  2. Use canonical labels to create consolidated themes")
    print(f"  3. Map interview themes as evidence to canonical themes")

if __name__ == '__main__':
    main() 