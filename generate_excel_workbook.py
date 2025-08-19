#!/usr/bin/env python3
"""
Excel Workbook Generator - Production Script

This script generates comprehensive Excel workbooks for VOC analysis
with cross-section theme handling and analyst curation tools.

Usage:
    python generate_excel_workbook.py --client Supio
    python generate_excel_workbook.py --client Supio --output custom_filename.xlsx
"""

import argparse
import sys
import os
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from win_loss_report_generator import WinLossReportGenerator
from excel_win_loss_exporter import ExcelWinLossExporter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_workbook(client_id: str, output_path: str = None, unified: bool = True) -> str:
    """
    Generate Excel workbook for specified client
    
    Args:
        client_id: The client identifier (e.g., 'Supio')
        output_path: Optional custom output path
        
    Returns:
        Path to generated Excel file
    """
    try:
        logger.info(f"🚀 Starting Excel workbook generation for client: {client_id}")
        
        # Step 1: Generate themes
        logger.info("📊 Step 1/2: Generating themes and analysis...")
        generator = WinLossReportGenerator(client_id)
        themes_data = generator.generate_analyst_report()
        
        if not themes_data["success"]:
            logger.error(f"❌ Theme generation failed: {themes_data.get('error')}")
            return None
        
        logger.info(f"✅ Generated {len(themes_data['themes'])} themes")
        
        # Step 2: Create Excel workbook
        logger.info("📋 Step 2/2: Creating Excel workbook...")
        exporter = ExcelWinLossExporter()
        
        if output_path:
            # Use custom output path
            final_output_path = exporter.export_analyst_workbook(themes_data, output_path, unified=unified)
        else:
            # Use default naming
            final_output_path = exporter.export_analyst_workbook(themes_data, unified=unified)
        
        # Verify file was created
        if os.path.exists(final_output_path):
            file_size = os.path.getsize(final_output_path)
            logger.info(f"✅ Excel workbook created successfully!")
            logger.info(f"📁 File: {final_output_path}")
            logger.info(f"📊 Size: {file_size:,} bytes")
            return final_output_path
        else:
            logger.error("❌ Excel file was not created")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error generating workbook: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(
        description="Generate Excel workbook for VOC analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_excel_workbook.py --client Supio
  python generate_excel_workbook.py --client Supio --output custom_report.xlsx
        """
    )
    
    parser.add_argument(
        '--client', 
        required=True,
        help='Client ID (e.g., Supio)'
    )
    
    parser.add_argument(
        '--output',
        help='Custom output filename (optional)'
    )
    # Default to unified Themes sheet; use --legacy to switch to multi-tab
    parser.set_defaults(unified=True)
    parser.add_argument(
        '--legacy',
        dest='unified',
        action='store_false',
        help='Generate legacy multi-tab workbook (Win Drivers, Loss Factors, etc.) instead of unified Themes tab'
    )
    
    args = parser.parse_args()
    
    # Generate workbook
    output_path = generate_workbook(args.client, args.output, unified=args.unified)
    
    if output_path:
        print(f"\n🎉 SUCCESS: Excel workbook generated!")
        print(f"📁 File: {output_path}")
        print(f"💡 Open the file to start analyst curation")
    else:
        print(f"\n❌ FAILED: Could not generate Excel workbook")
        sys.exit(1)

if __name__ == "__main__":
    main() 