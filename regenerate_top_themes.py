#!/usr/bin/env python3
"""
Regenerate Top Themes
Regenerate interview themes with only the top 3-5 most important ones per interview
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from supabase_database import SupabaseDatabase

# The same sophisticated prompt that generated high-quality ShipStation API themes
PROMPT = (
    "WIN–LOSS INTERVIEW THEMES (OUTCOME‑AWARE, ICP TARGET COVERED)\n\n"
    "Inputs\n"
    "- outcome: \"<WON|LOST|ICP_TARGET|UNKNOWN>\"\n"
    "- transcript: <<<TRANSCRIPT_TEXT>>>\n\n"
    "Task\n"
    "1) Determine operative_outcome\n"
    "   - If outcome ≠ UNKNOWN: use it as ground truth.\n"
    "   - If UNKNOWN: infer WON or LOST or ICP_TARGET (one word) + 1‑sentence rationale.\n\n"
    "2) Produce EXACTLY 3 reasons_for_outcome (bullets), consistent with the operative_outcome\n"
    "   - If WON: why we won (no loss bullets).\n"
    "   - If LOST: why we lost (no win bullets).\n"
    "   - If ICP_TARGET: give decision insights to guide GTM.\n"
    "   - Each bullet ≤ 22 words, client‑facing, specific, no filler.\n"
    "   - Include one concrete detail per bullet: vendor, feature, price model, integration, throughput/volume, SLA, or switching barrier.\n\n"
    "3) competitive_intel (EXACTLY 1 bullet)\n"
    "   - Vendor strengths/weaknesses, pricing models, feature deltas, integration claims.\n\n"
    "4) other_signals (EXACTLY 1 bullet)\n"
    "   - Most important pattern not already covered.\n\n"
    "Constraints\n"
    "- EXACTLY 5 total themes (3 outcome + 1 competitive + 1 signal)\n"
    "- No quotes/IDs; no hedging; no duplication across sections.\n"
    "- Keep reasons_for_outcome strictly aligned to operative_outcome.\n\n"
    "Output (valid JSON only)\n"
    "{\n"
    "  \"operative_outcome\": \"WON|LOST|ICP_TARGET\",\n"
    "  \"rationale\": \"Present only if UNKNOWN input; else empty string\",\n"
    "  \"reasons_for_outcome\": [\n"
    "    {\"theme\": \"…\", \"category\": \"outcome_reason\"}\n"
    "  ],\n"
    "  \"competitive_intel\": [{\"theme\": \"…\"}],\n"
    "  \"other_signals\": [{\"theme\": \"…\"}]\n"
    "}\n"
)

def call_llm(outcome: str, text: str) -> Dict[str, Any]:
    """Call LLM to generate structured interview analysis"""
    try:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2, max_tokens=900)
        filled = PROMPT.replace("<WON|LOST|ICP_TARGET|UNKNOWN>", outcome).replace("<<<TRANSCRIPT_TEXT>>>", text[:12000])
        resp = llm.invoke(filled)
        out = (resp.content or "").strip().replace('```json','').replace('```','').strip()
        start = out.find('{'); end = out.rfind('}') + 1
        if start != -1 and end > start:
            obj = json.loads(out[start:end])
            return obj
        # Fallback JSON
        return {
            "operative_outcome": outcome if outcome != "UNKNOWN" else "ICP_TARGET",
            "rationale": "",
            "reasons_for_outcome": [],
            "competitive_intel": [],
            "other_signals": []
        }
    except Exception as e:
        print(f"   ⚠️ LLM call failed: {e}")
        # Fallback JSON
        return {
            "operative_outcome": outcome if outcome != "UNKNOWN" else "ICP_TARGET",
            "rationale": "",
            "reasons_for_outcome": [],
            "competitive_intel": [],
            "other_signals": []
        }

def regenerate_top_themes():
    """Regenerate interview themes with only top 3-5 per interview"""
    
    client_id = "ShipBob"
    
    try:
        print(f"🚀 Regenerating interview themes with top 5 per interview for client: {client_id}")
        
        # Initialize database connection
        db = SupabaseDatabase()
        
        # First, clear existing themes to start fresh
        print(f"🧹 Clearing existing interview themes...")
        try:
            db.supabase.table('interview_level_themes').delete().eq('client_id', client_id).execute()
            print(f"   ✅ Cleared existing themes")
        except Exception as e:
            print(f"   ⚠️ Could not clear themes: {e}")
        
        # Get all interviews
        print(f"📊 Fetching interviews...")
        interviews = db.supabase.table('interview_metadata').select('*').eq('client_id', client_id).execute()
        
        if not interviews.data:
            print(f"❌ No interviews found")
            return False
        
        print(f"✅ Found {len(interviews.data)} interviews")
        
        # Get all responses
        print(f"📝 Fetching responses...")
        responses = db.supabase.table('stage1_data_responses').select('*').eq('client_id', client_id).execute()
        
        if not responses.data:
            print(f"❌ No responses found")
            return False
        
        print(f"✅ Found {len(responses.data)} responses")
        
        # Group responses by interview_id
        interview_responses = {}
        for response in responses.data:
            interview_id = response.get('interview_id')
            if interview_id:
                if interview_id not in interview_responses:
                    interview_responses[interview_id] = []
                interview_responses[interview_id].append(response)
        
        print(f"📊 Grouped responses for {len(interview_responses)} interviews")
        
        # Generate themes for each interview (EXACTLY 5 per interview)
        total_themes = 0
        for interview in interviews.data:
            interview_id = interview.get('interview_id')
            company = interview.get('company', 'Unknown')
            interviewee = interview.get('interviewee_name', 'Unknown')
            deal_status = interview.get('deal_status', '')
            
            print(f"\n🔄 Processing {interview_id}: {company} - {interviewee}")
            
            if interview_id in interview_responses:
                # Combine all responses for this interview
                combined_text = ' '.join([str(r.get('verbatim_response', '')) for r in interview_responses[interview_id]])
                
                if len(combined_text.strip()) < 100:
                    print(f"   ⚠️ Insufficient transcript data ({len(combined_text)} chars)")
                    continue
                
                # Determine outcome for LLM
                outcome = "UNKNOWN"
                if deal_status:
                    deal_lower = deal_status.lower()
                    if 'won' in deal_lower:
                        outcome = "WON"
                    elif 'lost' in deal_lower:
                        outcome = "LOST"
                    elif 'icp' in deal_lower:
                        outcome = "ICP_TARGET"
                
                print(f"   🔍 Analyzing transcript with LLM (outcome: {outcome})...")
                
                # Call LLM for structured analysis (will generate EXACTLY 5 themes)
                obj = call_llm(outcome, combined_text)
                
                # Extract themes from different sections
                themes_created = 0
                
                # Save reasons_for_outcome themes (EXACTLY 3)
                for item in (obj.get('reasons_for_outcome') or [])[:3]:
                    theme = str(item.get('theme') if isinstance(item, dict) else item)
                    if theme:
                        try:
                            db.supabase.table('interview_level_themes').insert({
                                'client_id': client_id,
                                'interview_id': interview_id,
                                'theme_statement': theme,
                                'subject': 'outcome_reason',
                                'sentiment': None,
                                'impact_score': None,
                                'notes': 'auto-generated'
                            }).execute()
                            themes_created += 1
                        except Exception as e:
                            print(f"   ⚠️ Failed to save theme: {e}")
                
                # Save competitive_intel themes (EXACTLY 1)
                for ci in (obj.get('competitive_intel') or [])[:1]:
                    theme = str(ci.get('theme') if isinstance(ci, dict) else ci)
                    if theme:
                        try:
                            db.supabase.table('interview_level_themes').insert({
                                'client_id': client_id,
                                'interview_id': interview_id,
                                'theme_statement': theme,
                                'subject': 'competitive_intel',
                                'sentiment': None,
                                'impact_score': None,
                                'notes': 'auto-generated'
                            }).execute()
                            themes_created += 1
                        except Exception as e:
                            print(f"   ⚠️ Failed to save theme: {e}")
                
                # Save other_signals themes (EXACTLY 1)
                for sig in (obj.get('other_signals') or [])[:1]:
                    theme = str(sig.get('theme') if isinstance(sig, dict) else sig)
                    if theme:
                        try:
                            db.supabase.table('interview_level_themes').insert({
                                'client_id': client_id,
                                'interview_id': interview_id,
                                'theme_statement': theme,
                                'subject': 'signal',
                                'sentiment': None,
                                'impact_score': None,
                                'notes': 'auto-generated'
                            }).execute()
                            themes_created += 1
                        except Exception as e:
                            print(f"   ⚠️ Failed to save theme: {e}")
                
                total_themes += themes_created
                print(f"   ✅ Created {themes_created} themes (target: 5)")
                
            else:
                print(f"   ⚠️ No responses found for {interview_id}")
        
        print(f"\n📊 Theme Generation Results:")
        print(f"  - Total interviews processed: {len(interviews.data)}")
        print(f"  - Total themes created: {total_themes}")
        print(f"  - Expected themes: {len(interviews.data) * 5}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error regenerating top themes: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Regenerating interview themes with top 5 per interview...")
    success = regenerate_top_themes()
    
    if success:
        print("\n🎉 Top theme generation completed successfully!")
        print("💡 You can now generate a focused workbook with manageable themes")
    else:
        print("\n❌ Top theme generation failed!")
        print("💡 Check the error messages above for details") 