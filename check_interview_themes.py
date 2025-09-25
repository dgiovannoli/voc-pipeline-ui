#!/usr/bin/env python3
"""
Check Interview Themes
Check the current distribution of interview themes across interviews
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from supabase_database import SupabaseDatabase

def check_interview_themes():
    """Check the current distribution of interview themes across interviews"""
    
    client_id = "ShipBob"
    
    try:
        print(f"🔍 Checking interview themes distribution for client: {client_id}")
        
        # Initialize database connection
        db = SupabaseDatabase()
        
        # Get all interview themes
        print(f"📊 Fetching interview themes...")
        themes = db.supabase.table('interview_level_themes').select('*').eq('client_id', client_id).execute()
        
        if not themes.data:
            print(f"❌ No interview themes found")
            return False
        
        print(f"✅ Found {len(themes.data)} interview themes")
        
        # Group themes by interview_id
        themes_by_interview = {}
        for theme in themes.data:
            interview_id = theme.get('interview_id')
            if interview_id:
                if interview_id not in themes_by_interview:
                    themes_by_interview[interview_id] = []
                themes_by_interview[interview_id].append(theme)
        
        print(f"\n📊 Interview Themes Distribution:")
        print(f"{'='*80}")
        
        # Get all interviews for context
        interviews = db.supabase.table('interview_metadata').select('*').eq('client_id', client_id).execute()
        interview_map = {interview.get('interview_id'): interview for interview in interviews.data}
        
        total_themes = 0
        for interview_id in sorted(interview_map.keys()):
            interview = interview_map[interview_id]
            company = interview.get('company', 'Unknown')
            interviewee = interview.get('interviewee_name', 'Unknown')
            
            themes_count = len(themes_by_interview.get(interview_id, []))
            total_themes += themes_count
            
            print(f"📋 {interview_id}: {company} - {interviewee}")
            print(f"   Themes: {themes_count}")
            
            if themes_count > 0:
                for i, theme in enumerate(themes_by_interview[interview_id][:3], 1):  # Show first 3
                    theme_text = theme.get('theme_statement', '')[:100] + "..." if len(theme.get('theme_statement', '')) > 100 else theme.get('theme_statement', '')
                    print(f"     {i}. {theme_text}")
                if themes_count > 3:
                    print(f"     ... and {themes_count - 3} more")
            else:
                print(f"     ❌ No themes found")
            print()
        
        print(f"{'='*80}")
        print(f"📊 Summary:")
        print(f"   Total interviews: {len(interview_map)}")
        print(f"   Total themes: {total_themes}")
        print(f"   Average themes per interview: {total_themes/len(interview_map):.1f}")
        
        # Check for interviews with no themes
        interviews_without_themes = [interview_id for interview_id in interview_map.keys() if interview_id not in themes_by_interview or len(themes_by_interview[interview_id]) == 0]
        
        if interviews_without_themes:
            print(f"\n⚠️ Interviews with NO themes:")
            for interview_id in interviews_without_themes:
                interview = interview_map[interview_id]
                print(f"   - {interview_id}: {interview.get('company')} - {interview.get('interviewee_name')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking interview themes: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking interview themes distribution...")
    success = check_interview_themes()
    
    if success:
        print("\n✅ Interview themes check completed")
    else:
        print("\n❌ Interview themes check failed") 