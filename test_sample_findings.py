import os
from dotenv import load_dotenv
load_dotenv()
os.environ['SUPABASE_SERVICE_KEY'] = os.environ.get('SUPABASE_ANON_KEY')
from supabase import create_client, Client

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(url, key)

response = supabase.table('enhanced_findings').select('*').eq('client_id', 'Rev').order('created_at', desc=True).limit(10).execute()
findings = response.data

print('Sample of 10 most recent findings:')
for i, finding in enumerate(findings):
    print(f'\nFinding {i+1}:')
    print('  Confidence:', finding.get('enhanced_confidence', 'N/A'))
    print('  Criteria met:', finding.get('criteria_met', 'N/A'))
    statement = finding.get('description', finding.get('finding_statement', 'N/A'))
    print('  Statement:', (statement[:300] + '...') if statement and len(statement) > 300 else statement) 