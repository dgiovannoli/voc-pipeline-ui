#!/usr/bin/env python3
"""
Trim Themes To Top
Trim interview themes down to only the top 3-5 most important ones per interview
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from supabase_database import SupabaseDatabase

def trim_themes_to_top():
    """Trim interview themes down to top 3-5 per interview"""
    
    client_id = "ShipBob"
    max_themes_per_interview = 5  # Keep only top 5 themes per interview
    
    try:
        print(f"✂️ Trimming interview themes to top {max_themes_per_interview} per interview for client: {client_id}")
        
        # Initialize database connection
        db = SupabaseDatabase()
        
        # Get all interview themes
        print(f"📊 Fetching current interview themes...")
        themes = db.supabase.table('interview_level_themes').select('*').eq('client_id', client_id).execute()
        
        if not themes.data:
            print(f"❌ No interview themes found")
            return False
        
        print(f"✅ Found {len(themes.data)} total themes")
        
        # Group themes by interview_id
        themes_by_interview = {}
        for theme in themes.data:
            interview_id = theme.get('interview_id')
            if interview_id:
                if interview_id not in themes_by_interview:
                    themes_by_interview[interview_id] = []
                themes_by_interview[interview_id].append(theme)
        
        print(f"📊 Current theme distribution:")
        for interview_id, interview_themes in themes_by_interview.items():
            print(f"   {interview_id}: {len(interview_themes)} themes")
        
        # For each interview, keep only the top themes
        themes_to_keep = []
        themes_to_delete = []
        
        for interview_id, interview_themes in themes_by_interview.items():
            if len(interview_themes) <= max_themes_per_interview:
                # Already under limit, keep all
                themes_to_keep.extend(interview_themes)
                print(f"   ✅ {interview_id}: Keeping all {len(interview_themes)} themes (under limit)")
            else:
                # Over limit, keep top themes
                # Prioritize by subject type: outcome_reason > competitive_intel > signal
                priority_order = ['outcome_reason', 'competitive_intel', 'signal']
                
                # Sort themes by priority
                sorted_themes = sorted(interview_themes, key=lambda x: (
                    priority_order.index(x.get('subject', 'signal')) if x.get('subject') in priority_order else len(priority_order),
                    len(x.get('theme_statement', ''))  # Secondary sort by length (longer = more detailed)
                ))
                
                # Keep top themes
                top_themes = sorted_themes[:max_themes_per_interview]
                themes_to_keep.extend(top_themes)
                
                # Mark excess themes for deletion
                excess_themes = sorted_themes[max_themes_per_interview:]
                themes_to_delete.extend(excess_themes)
                
                print(f"   ✂️ {interview_id}: Keeping top {len(top_themes)} themes, removing {len(excess_themes)} excess themes")
        
        print(f"\n📊 Trimming Results:")
        print(f"   Total themes before: {len(themes.data)}")
        print(f"   Themes to keep: {len(themes_to_keep)}")
        print(f"   Themes to remove: {len(themes_to_delete)}")
        
        # Delete excess themes
        if themes_to_delete:
            print(f"\n🗑️ Removing excess themes...")
            deleted_count = 0
            
            for theme in themes_to_delete:
                try:
                    db.supabase.table('interview_level_themes').delete().eq('id', theme.get('id')).execute()
                    deleted_count += 1
                except Exception as e:
                    print(f"   ⚠️ Failed to delete theme {theme.get('id')}: {e}")
            
            print(f"   ✅ Deleted {deleted_count} excess themes")
        
        # Verify final count
        final_themes = db.supabase.table('interview_level_themes').select('*').eq('client_id', client_id).execute()
        print(f"\n📊 Final Results:")
        print(f"   Total themes after trimming: {len(final_themes.data)}")
        
        # Show final distribution
        final_themes_by_interview = {}
        for theme in final_themes.data:
            interview_id = theme.get('interview_id')
            if interview_id:
                if interview_id not in final_themes_by_interview:
                    final_themes_by_interview[interview_id] = []
                final_themes_by_interview[interview_id].append(theme)
        
        print(f"\n📊 Final Theme Distribution:")
        for interview_id in sorted(final_themes_by_interview.keys()):
            theme_count = len(final_themes_by_interview[interview_id])
            print(f"   {interview_id}: {theme_count} themes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error trimming themes: {e}")
        return False

if __name__ == "__main__":
    print("✂️ Trimming interview themes to manageable levels...")
    success = trim_themes_to_top()
    
    if success:
        print("\n🎉 Theme trimming completed successfully!")
        print("💡 You can now generate a focused workbook with top themes")
    else:
        print("\n❌ Theme trimming failed!")
        print("💡 Check the error messages above for details") 