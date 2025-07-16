#!/usr/bin/env python3
"""
Show Latest Themes
Display the themes that were just saved to the database
"""

from supabase_database import SupabaseDatabase

def show_latest_themes():
    """Show the latest themes in the database"""
    
    print("🎯 LATEST THEMES IN DATABASE\n")
    
    try:
        db = SupabaseDatabase()
        
        # Get themes ordered by creation time (newest first)
        response = db.supabase.table('stage4_themes').select(
            'theme_id, theme_title, theme_statement, classification, primary_quote, secondary_quote, supporting_finding_ids'
        ).eq('client_id', 'Rev').order('created_at', desc=True).limit(10).execute()
        
        if not response.data:
            print("❌ No themes found in database")
            return
        
        themes = response.data
        
        print(f"📊 Found {len(themes)} recent themes\n")
        
        for i, theme in enumerate(themes, 1):
            theme_id = theme.get('theme_id', 'Unknown')
            title = theme.get('theme_title', 'No title')
            statement = theme.get('theme_statement', 'No statement')
            classification = theme.get('classification', 'Unknown')
            primary_quote = theme.get('primary_quote', 'No quote')
            secondary_quote = theme.get('secondary_quote', 'No quote')
            supporting_findings = theme.get('supporting_finding_ids', 'No findings')
            
            print(f"🔍 THEME {i}: {theme_id}")
            print("=" * 80)
            print(f"Title: {title}")
            print(f"Classification: {classification}")
            print(f"Supporting Findings: {supporting_findings}")
            print()
            print("Statement:")
            print(f"  {statement}")
            print()
            print("Primary Quote:")
            print(f"  {primary_quote[:200]}{'...' if len(primary_quote) > 200 else ''}")
            print()
            if secondary_quote and secondary_quote != 'No quote':
                print("Secondary Quote:")
                print(f"  {secondary_quote[:200]}{'...' if len(secondary_quote) > 200 else ''}")
                print()
            print()
        
    except Exception as e:
        print(f"❌ Error showing themes: {e}")

if __name__ == "__main__":
    show_latest_themes() 