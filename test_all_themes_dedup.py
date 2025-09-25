#!/usr/bin/env python3
"""
Test LLM Prompt Against All Themes Tab
Analyzes only the themes in the All Themes tab for duplicates
"""

import json
import sys
from pathlib import Path
from typing import List, Dict
import pandas as pd
from openai import OpenAI
import os

# Import from current directory
from supabase_database import SupabaseDatabase

class AllThemesDeduplicator:
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

    def fetch_all_themes(self) -> pd.DataFrame:
        """Fetch themes that would appear in the All Themes tab"""
        # Get research themes (same as All Themes tab)
        research_themes = self.db.fetch_research_themes_all(self.client_id)
        
        # Get canonical interview themes from rollup clusters (same as All Themes tab)
        try:
            from interview_theme_rollup import rollup_interview_themes
            rollup_result = rollup_interview_themes(self.db, self.client_id)
            canonical_interview_themes = rollup_result.clusters.copy()
        except Exception as e:
            print(f"⚠️ Could not fetch rollup interview themes: {e}")
            canonical_interview_themes = pd.DataFrame(columns=['cluster_id', 'canonical_theme'])
        
        if research_themes.empty and canonical_interview_themes.empty:
            return pd.DataFrame()
        
        # Prepare research themes
        research_df = research_themes.copy()
        research_df['source'] = research_df['origin'].map(lambda x: 'discovered' if str(x).startswith('DISCOVERED:') else 'research')
        research_df['subject'] = research_df['harmonized_subject'].fillna('Uncategorized')
        research_df['theme_id'] = research_df['theme_id']  # Keep original UUID
        
        # Prepare canonical interview themes (same format as All Themes tab)
        if not canonical_interview_themes.empty:
            interview_df = canonical_interview_themes.copy()
            interview_df['source'] = 'interview_canonical'
            interview_df['subject'] = 'Interview'  # Will be mapped later
            interview_df['theme_id'] = interview_df['cluster_id'].apply(lambda x: f"interview_theme_{int(x):03d}")
            interview_df['theme_statement'] = interview_df['canonical_theme']
        else:
            interview_df = pd.DataFrame(columns=['theme_id', 'theme_statement', 'source', 'subject'])
        
        # Combine all themes (this represents the All Themes tab)
        all_themes = pd.concat([research_df, interview_df], ignore_index=True)
        return all_themes

    def get_all_themes_for_analysis(self, themes_df: pd.DataFrame) -> List[Dict]:
        """Get ALL themes for LLM analysis (research, discovered, and canonical interview themes)"""
        # Get all themes that can be analyzed for merging
        all_analyzable_themes = themes_df[themes_df['source'].isin(['research', 'discovered', 'interview_canonical'])]
        
        if len(all_analyzable_themes) < 2:
            return []
        
        print(f"📊 Found {len(all_analyzable_themes)} total themes to analyze:")
        source_counts = all_analyzable_themes['source'].value_counts()
        for source, count in source_counts.items():
            print(f"  - {source}: {count}")
        
        # Convert to simple list of themes
        themes_list = []
        for _, theme in all_analyzable_themes.iterrows():
            themes_list.append({
                'theme_id': theme['theme_id'],
                'theme_statement': theme['theme_statement'],
                'subject': theme['subject'],
                'source': theme['source']
            })
        
        return themes_list

    def analyze_themes_with_llm(self, themes_list: List[Dict]) -> List[Dict]:
        """Use LLM to analyze themes for duplicates"""
        if not themes_list:
            return []
        
        print(f"🧠 Analyzing {len(themes_list)} themes with LLM...")
        
        # Create the analysis prompt with all themes
        analysis_prompt = self.dedup_prompt + "\n\nAnalyze these themes for duplicates:\n\n"
        
        for j, theme in enumerate(themes_list):
            analysis_prompt += f"Theme {j+1} ({theme['source']}): {theme['theme_statement']}\n"
            analysis_prompt += f"ID: {theme['theme_id']}\n"
            analysis_prompt += f"Subject: {theme['subject']}\n\n"
        
        analysis_prompt += "Investigate all possible pairs and return JSON array of duplicate analysis results."
        
        try:
            print("📤 Sending to OpenAI...")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise theme deduplication analyst. Return only valid JSON."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1,
                max_tokens=3000
            )
            
            # Parse the response
            content = response.choices[0].message.content
            print(f"📥 Received response ({len(content)} characters)")
            
            try:
                # Extract JSON from the response
                json_start = content.find('[')
                json_end = content.rfind(']') + 1
                if json_start != -1 and json_end != -1:
                    json_str = content[json_start:json_end]
                    results = json.loads(json_str)
                    print(f"✅ Successfully parsed {len(results)} results")
                    return results
                else:
                    print(f"⚠️ Could not extract JSON from response")
                    print(f"Response preview: {content[:200]}...")
                    return []
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"Response content: {content[:300]}...")
                return []
                
        except Exception as e:
            print(f"❌ Error calling OpenAI API: {e}")
            return []

    def display_results(self, results: List[Dict]):
        """Display the analysis results in a readable format"""
        if not results:
            print("❌ No results to display")
            return
        
        print(f"\n📊 Analysis Results Summary:")
        print(f"  Total pairs analyzed: {len(results)}")
        
        # Count by recommendation
        merge_count = len([r for r in results if r.get('merge_recommendation') == 'MERGE'])
        do_not_merge_count = len([r for r in results if r.get('merge_recommendation') == 'DO_NOT_MERGE'])
        
        print(f"  Recommended for merge: {merge_count}")
        print(f"  Do not merge: {do_not_merge_count}")
        
        # Count by confidence
        high_count = len([r for r in results if r.get('decision_band') == 'High'])
        medium_count = len([r for r in results if r.get('decision_band') == 'Medium'])
        low_count = len([r for r in results if r.get('decision_band') == 'Low'])
        
        print(f"  High confidence: {high_count}")
        print(f"  Medium confidence: {medium_count}")
        print(f"  Low confidence: {low_count}")
        
        # Show merge recommendations
        if merge_count > 0:
            print(f"\n🔗 Merge Recommendations:")
            for i, result in enumerate(results, 1):
                if result.get('merge_recommendation') == 'MERGE':
                    print(f"  {i}. {result.get('theme_id_A', 'N/A')} + {result.get('theme_id_B', 'N/A')}")
                    print(f"     Subject: {result.get('subject_A', 'N/A')} + {result.get('subject_B', 'N/A')}")
                    print(f"     Confidence: {result.get('decision_band', 'N/A')}")
                    print(f"     Rationale: {result.get('rationale', 'N/A')}")
                    print(f"     Canonical: {result.get('canonical_label_suggestion', 'N/A')}")
                    print()

def main():
    # Initialize OpenAI client
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OpenAI API key required. Set OPENAI_API_KEY environment variable")
        return
    
    openai_client = OpenAI(api_key=api_key)
    
    print(f"🔍 Testing LLM Prompt Against All Themes Tab")
    print(f"Client: ShipStation API")
    
    # Initialize deduplicator
    deduplicator = AllThemesDeduplicator("ShipStation API", openai_client)
    
    # Fetch themes
    print("\n📥 Fetching themes...")
    themes_df = deduplicator.fetch_all_themes()
    
    if themes_df.empty:
        print("❌ No themes found")
        return
    
    print(f"✅ Found {len(themes_df)} total themes")
    
    # Get all themes for analysis
    print("\n🔍 Getting all themes for analysis...")
    themes_list = deduplicator.get_all_themes_for_analysis(themes_df)
    
    if not themes_list:
        print("❌ No themes to analyze")
        return
    
    print(f"✅ Found {len(themes_list)} total themes for analysis")
    
    # Analyze with LLM
    results = deduplicator.analyze_themes_with_llm(themes_list)
    
    if not results:
        print("❌ No analysis results")
        return
    
    print(f"✅ LLM analysis complete: {len(results)} results")
    
    # Display results
    deduplicator.display_results(results)
    
    print(f"\n🎯 Test complete!")
    print(f"   This shows how the LLM would analyze your All Themes tab")
    print(f"   If results look good, we can integrate this into your workflow")

if __name__ == '__main__':
    main() 