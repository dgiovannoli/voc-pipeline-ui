#!/usr/bin/env python3
"""
Clean And Regenerate
Completely clear all themes and regenerate exactly 5 per interview
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from supabase_database import SupabaseDatabase

def clean_and_regenerate():
    """Completely clear all themes and regenerate exactly 5 per interview"""
    
    client_id = "ShipBob"
    
    try:
        print(f"🧹 Completely clearing all interview themes for client: {client_id}")
        
        # Initialize database connection
        db = SupabaseDatabase()
        
        # Delete ALL themes for this client
        print(f"🗑️ Deleting all existing themes...")
        result = db.supabase.table('interview_level_themes').delete().eq('client_id', client_id).execute()
        print(f"   ✅ Deleted themes")
        
        # Verify deletion
        remaining = db.supabase.table('interview_level_themes').select('*').eq('client_id', client_id).execute()
        print(f"   📊 Remaining themes: {len(remaining.data)}")
        
        if len(remaining.data) > 0:
            print(f"   ⚠️ Some themes still remain - manual cleanup may be needed")
        else:
            print(f"   ✅ All themes successfully cleared")
        
        return True
        
    except Exception as e:
        print(f"❌ Error clearing themes: {e}")
        return False

if __name__ == "__main__":
    print("🧹 Cleaning all interview themes...")
    success = clean_and_regenerate()
    
    if success:
        print("\n🎉 Theme cleanup completed!")
        print("💡 Run regenerate_top_themes.py to create new focused themes")
    else:
        print("\n❌ Theme cleanup failed!")
        print("💡 Check the error messages above for details") 