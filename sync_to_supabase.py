#!/usr/bin/env python3
"""
Simple script to sync data from SQLite to Supabase
Run this after setting up your Supabase project and adding environment variables
"""

import os
from dotenv import load_dotenv
from supabase_integration import HybridDatabaseManager
import json

load_dotenv()

def main():
    print("🔄 VOC Pipeline - SQLite to Supabase Sync")
    print("=" * 50)
    
    # Check environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url:
        print("❌ SUPABASE_URL not found in environment variables")
        print("💡 Add to your .env file:")
        print("   SUPABASE_URL=https://your-project.supabase.co")
        return
    
    if not supabase_key:
        print("❌ SUPABASE_ANON_KEY not found in environment variables")
        print("💡 Add to your .env file:")
        print("   SUPABASE_ANON_KEY=your_anon_key_here")
        return
    
    print(f"✅ Found Supabase URL: {supabase_url[:30]}...")
    print(f"✅ Found Supabase Key: {supabase_key[:20]}...")
    
    # Initialize hybrid database manager
    try:
        db_manager = HybridDatabaseManager()
        print("✅ Hybrid database manager initialized")
    except Exception as e:
        print(f"❌ Failed to initialize database manager: {e}")
        return
    
    # Check sync status
    print("\n📊 Checking sync status...")
    try:
        status = db_manager.get_sync_status()
        
        if "error" in status:
            print(f"❌ Error getting sync status: {status['error']}")
            return
        
        print(f"📈 Local responses: {status.get('total_local_responses', 0)}")
        print(f"📈 Local analyses: {status.get('total_local_analyses', 0)}")
        print(f"☁️ Supabase available: {status.get('supabase_available', False)}")
        
        # Show detailed status
        response_status = status.get('core_responses', {})
        analysis_status = status.get('quote_analysis', {})
        
        print("\n📋 Detailed Status:")
        print("Core Responses:")
        for sync_type, count in response_status.items():
            print(f"  - {sync_type}: {count}")
        
        print("Quote Analysis:")
        for sync_type, count in analysis_status.items():
            print(f"  - {sync_type}: {count}")
        
    except Exception as e:
        print(f"❌ Error checking sync status: {e}")
        return
    
    # Ask user if they want to sync
    print("\n" + "=" * 50)
    response = input("🔄 Do you want to sync all data to Supabase? (y/n): ").lower().strip()
    
    if response not in ['y', 'yes']:
        print("👋 Sync cancelled")
        return
    
    # Perform sync
    print("\n🔄 Syncing data to Supabase...")
    try:
        sync_stats = db_manager.sync_all_to_supabase()
        
        if "error" in sync_stats:
            print(f"❌ Sync failed: {sync_stats['error']}")
            return
        
        print("✅ Sync completed successfully!")
        print(f"📊 Synced {sync_stats.get('core_responses', 0)} core responses")
        print(f"📊 Synced {sync_stats.get('quote_analysis', 0)} quote analyses")
        print(f"❌ Errors: {sync_stats.get('errors', 0)}")
        
        # Show updated status
        print("\n📊 Updated sync status:")
        updated_status = db_manager.get_sync_status()
        if "error" not in updated_status:
            response_status = updated_status.get('core_responses', {})
            analysis_status = updated_status.get('quote_analysis', {})
            
            print("Core Responses:")
            for sync_type, count in response_status.items():
                print(f"  - {sync_type}: {count}")
            
            print("Quote Analysis:")
            for sync_type, count in analysis_status.items():
                print(f"  - {sync_type}: {count}")
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        return
    
    print("\n🎉 Sync process completed!")
    print("💡 You can now view your data in the Supabase dashboard")

if __name__ == "__main__":
    main() 