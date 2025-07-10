import os
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
os.environ['SUPABASE_SERVICE_KEY'] = os.environ.get('SUPABASE_ANON_KEY')
from supabase import create_client, Client

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(url, key)

# Get all findings for client Rev
response = supabase.table('enhanced_findings').select('*').eq('client_id', 'Rev').order('created_at', desc=True).execute()
findings = response.data

# Convert to DataFrame
df = pd.DataFrame(findings)

# Select relevant columns for analysis (only include columns that exist)
columns_to_export = [
    'id',
    'created_at',
    'enhanced_confidence',
    'criteria_met',
    'criteria_scores',
    'description',
    'title',
    'finding_type',
    'priority_level',
    'credibility_tier',
    'impact_score',
    'companies_affected'
]

# Filter to only include columns that exist in the DataFrame
existing_columns = [col for col in columns_to_export if col in df.columns]
export_df = df[existing_columns].copy()

# Add summary statistics
print(f"Total findings exported: {len(export_df)}")
print(f"Confidence score distribution:")
print(export_df['enhanced_confidence'].value_counts().sort_index())
print(f"\nCriteria met distribution:")
print(export_df['criteria_met'].value_counts().sort_index())
print(f"\nPriority level distribution:")
print(export_df['priority_level'].value_counts())

# Export to CSV
filename = f"enhanced_findings_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
export_df.to_csv(filename, index=False)
print(f"\nExported findings to: {filename}")

# Also create a summary file
summary_filename = f"findings_summary_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt"
with open(summary_filename, 'w') as f:
    f.write("ENHANCED FINDINGS SUMMARY\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"Total findings: {len(export_df)}\n")
    f.write(f"Average confidence score: {export_df['enhanced_confidence'].mean():.2f}\n")
    f.write(f"Average criteria met: {export_df['criteria_met'].mean():.2f}\n")
    f.write(f"Priority findings (≥4.0): {len(export_df[export_df['enhanced_confidence'] >= 4.0])}\n")
    f.write(f"Standard findings (≥3.0): {len(export_df[export_df['enhanced_confidence'] >= 3.0])}\n\n")
    
    f.write("CONFIDENCE SCORE DISTRIBUTION:\n")
    f.write(export_df['enhanced_confidence'].value_counts().sort_index().to_string())
    f.write("\n\nCRITERIA MET DISTRIBUTION:\n")
    f.write(export_df['criteria_met'].value_counts().sort_index().to_string())
    f.write("\n\nPRIORITY LEVEL DISTRIBUTION:\n")
    f.write(export_df['priority_level'].value_counts().to_string())
    f.write("\n\nSAMPLE FINDINGS (first 10):\n")
    f.write("-" * 50 + "\n")
    for i, row in export_df.head(10).iterrows():
        f.write(f"\nFinding {i+1}:\n")
        f.write(f"  Confidence: {row['enhanced_confidence']}\n")
        f.write(f"  Criteria met: {row['criteria_met']}\n")
        f.write(f"  Statement: {row['description']}\n")

print(f"Created summary file: {summary_filename}") 