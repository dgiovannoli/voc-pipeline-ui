#!/usr/bin/env python3

"""
Export improved Stage 3 findings in a format that matches the example CSV
"""

import pandas as pd
import json
from supabase_database import SupabaseDatabase

def export_improved_findings():
    """Export findings in the format of the example CSV"""
    
    print("📊 Exporting improved Stage 3 findings...")
    
    # Get findings from database
    db = SupabaseDatabase()
    findings_df = db.get_enhanced_findings(client_id='Rev')
    
    if findings_df.empty:
        print("❌ No findings found")
        return
    
    print(f"✅ Found {len(findings_df)} findings")
    
    # Create export data in the format of the example CSV
    export_data = []
    
    for idx, finding in findings_df.iterrows():
        # Parse JSON fields
        criteria_scores = {}
        if 'criteria_scores' in finding and finding['criteria_scores']:
            if isinstance(finding['criteria_scores'], str):
                criteria_scores = json.loads(finding['criteria_scores'])
            else:
                criteria_scores = finding['criteria_scores']
        
        selected_quotes = []
        if 'selected_quotes' in finding and finding['selected_quotes']:
            if isinstance(finding['selected_quotes'], str):
                selected_quotes = json.loads(finding['selected_quotes'])
            else:
                selected_quotes = finding['selected_quotes']
        
        # Extract primary and secondary quotes with better parsing
        primary_quote = ""
        secondary_quote = ""
        if selected_quotes:
            # Handle different quote formats
            if isinstance(selected_quotes[0], dict):
                primary_quote = selected_quotes[0].get('text', selected_quotes[0].get('original_quote', ''))
            else:
                primary_quote = str(selected_quotes[0])
            
            if len(selected_quotes) > 1:
                if isinstance(selected_quotes[1], dict):
                    secondary_quote = selected_quotes[1].get('text', selected_quotes[1].get('original_quote', ''))
                else:
                    secondary_quote = str(selected_quotes[1])
        
        # Handle company and interviewee attribution
        interview_companies = finding.get('interview_companies', [])
        interviewee_names = finding.get('interviewee_names', [])
        interview_company = interview_companies[0] if interview_companies and interview_companies[0] not in [None, '', 'Unknown'] else 'Rev'
        interviewee_name = interviewee_names[0] if interviewee_names and interviewee_names[0] not in [None, '', 'Unknown', 'Multiple'] else 'Multiple'
        # Create export row
        export_row = {
            'Finding_ID': f"F{idx+1}",
            'Finding_Statement': finding.get('finding_statement', finding.get('description', '')),
            'Interview_Company': interview_company,
            'Date': finding.get('generated_at', '').split('T')[0] if finding.get('generated_at') else '',
            'Deal_Status': 'closed won',  # Default
            'Interviewee_Name': interviewee_name,
            'Supporting_Response_IDs': f"Rev_{idx+1}",  # Simplified
            'Evidence_Strength': finding.get('evidence_strength', 0),
            'Finding_Category': finding.get('finding_category', finding.get('finding_type', '')),
            'Criteria_Met': finding.get('criteria_covered', ''),
            'Priority_Level': finding.get('priority_level', '').title() + ' Finding',
            'Primary_Quote': primary_quote[:200] + "..." if len(primary_quote) > 200 else primary_quote,
            'Secondary_Quote': secondary_quote[:200] + "..." if len(secondary_quote) > 200 else secondary_quote,
            'Quote_Attributions': f"Primary: Rev_{idx+1} - Multiple; Secondary: Rev_{idx+2} - Multiple" if len(selected_quotes) > 1 else f"Primary: Rev_{idx+1} - Multiple"
        }
        
        export_data.append(export_row)
    
    # Create DataFrame and export
    export_df = pd.DataFrame(export_data)
    
    # Save to CSV
    output_file = 'improved_findings_export.csv'
    export_df.to_csv(output_file, index=False)
    
    print(f"✅ Exported {len(export_df)} findings to {output_file}")
    print("\n📋 Sample findings:")
    for i, row in export_df.head(3).iterrows():
        print(f"\n{i+1}. {row['Finding_Statement']}")
        print(f"   Category: {row['Finding_Category']}")
        print(f"   Evidence Strength: {row['Evidence_Strength']}")
        print(f"   Criteria Met: {row['Criteria_Met']}")

if __name__ == "__main__":
    export_improved_findings() 