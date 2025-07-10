#!/usr/bin/env python3

"""
Stage 4: Theme Generation Runner
Generates executive themes from Stage 3 findings
"""

import sys
import os
from stage4_theme_analyzer import run_stage4_analysis

def main():
    print("🔍 Stage 4: Theme Generation")
    print("=" * 50)
    print("Generating executive themes from findings...")
    print()
    
    try:
        client_id = 'Rev'  # Use Rev client for theme generation
        result = run_stage4_analysis(client_id=client_id)
        
        if result["status"] == "success":
            print("✅ Stage 4 completed successfully!")
            print(f"📊 Themes generated: {result['themes_generated']}")
            print(f"🏆 High strength themes: {result['high_strength_themes']}")
            print(f"🏅 Competitive themes: {result['competitive_themes']}")
        else:
            print(f"⚠️ Stage 4 completed with status: {result['status']}")
            print(f"📝 Message: {result.get('message', 'No message provided')}")
            
    except Exception as e:
        print(f"❌ Error running Stage 4: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 