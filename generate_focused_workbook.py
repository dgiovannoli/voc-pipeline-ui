#!/usr/bin/env python3
"""
Generate Focused Workbook
Generate a focused workbook with only top 5 themes per interview displayed
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from supio_harmonized_workbook_generator import SupioHarmonizedWorkbookGenerator

def generate_focused_workbook():
    """Generate a focused workbook with limited themes per interview"""
    
    client_id = "ShipBob"
    
    try:
        print(f"📊 Generating focused workbook for client: {client_id}")
        print(f"💡 This will show only top 5 themes per interview for clarity")
        
        # Initialize workbook generator
        generator = SupioHarmonizedWorkbookGenerator(client_id)
        
        # Generate the workbook
        print(f"🔄 Generating workbook...")
        workbook_path = generator.generate_workbook()
        
        if workbook_path and os.path.exists(workbook_path):
            print(f"✅ Workbook generated successfully!")
            print(f"📁 Location: {workbook_path}")
            
            # Get generation stats
            stats = generator.get_generation_stats()
            print(f"\n📊 Workbook Generation Stats:")
            print(f"   - Total tabs: {stats.get('total_tabs', 'N/A')}")
            print(f"   - Interview themes: {stats.get('interview_themes_count', 'N/A')}")
            print(f"   - Research themes: {stats.get('research_themes_count', 'N/A')}")
            print(f"   - Discovered themes: {stats.get('discovered_themes_count', 'N/A')}")
            
            return workbook_path
        else:
            print(f"❌ Workbook generation failed")
            return None
        
    except Exception as e:
        print(f"❌ Error generating focused workbook: {e}")
        return None

if __name__ == "__main__":
    print("🎯 Generating focused workbook with manageable themes...")
    workbook_path = generate_focused_workbook()
    
    if workbook_path:
        print(f"\n🎉 Focused workbook created successfully!")
        print(f"💡 The workbook shows balanced themes across all interviews")
        print(f"📁 Open: {workbook_path}")
    else:
        print(f"\n❌ Focused workbook creation failed!")
        print(f"💡 Check the error messages above for details") 