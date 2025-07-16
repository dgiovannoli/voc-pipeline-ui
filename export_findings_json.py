#!/usr/bin/env python3

import json
import pandas as pd
import logging
from supabase_database import SupabaseDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def export_findings_json(client_id: str = 'Rev', output_file: str = "findings_for_stage4.json") -> bool:
    """Export Stage 3 findings as JSON for Stage 4 consumption"""
    try:
        # Initialize database connection
        db = SupabaseDatabase()
        
        # Get findings from database
        findings = db.get_stage3_findings_list(client_id=client_id)
        
        if not findings:
            logger.warning(f"No findings found for client {client_id}")
            return False
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(findings)
        
        # Ensure all required columns exist
        required_columns = [
            'Finding_ID', 'Finding_Statement', 'Interview_Company', 'Date', 
            'Deal_Status', 'Interviewee_Name', 'Supporting_Response_IDs', 
            'Evidence_Strength', 'Finding_Category', 'Criteria_Met', 
            'Priority_Level', 'Primary_Quote', 'Secondary_Quote', 'Quote_Attributions'
        ]
        
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""
        
        # Convert to list of dictionaries (JSON format)
        findings_list = df[required_columns].to_dict('records')
        
        # Save to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(findings_list, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Exported {len(findings_list)} findings to {output_file}")
        logger.info(f"📊 Sample finding: {findings_list[0] if findings_list else 'No findings'}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error exporting findings JSON: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    client_id = 'Rev'
    output_file = "findings_for_stage4.json"
    
    if len(sys.argv) > 1:
        client_id = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    print(f"🔍 Exporting Stage 3 findings as JSON for client '{client_id}'...")
    success = export_findings_json(client_id=client_id, output_file=output_file)
    
    if success:
        print(f"✅ Successfully exported findings to {output_file}")
    else:
        print("❌ Failed to export findings") 