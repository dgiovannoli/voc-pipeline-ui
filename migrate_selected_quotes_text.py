from supabase import create_client
import json
import os

# Set your Supabase credentials (use environment variables for safety)
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch all findings
findings = supabase.table("stage3_findings").select("id, selected_quotes").execute().data

for finding in findings:
    finding_id = finding["id"]
    selected_quotes = finding.get("selected_quotes")
    if not selected_quotes:
        continue
    # Parse JSON if needed
    if isinstance(selected_quotes, str):
        try:
            selected_quotes = json.loads(selected_quotes)
        except Exception:
            continue
    updated_quotes = []
    for quote in selected_quotes:
        quote_id = quote.get("quote_id")
        if not quote_id:
            updated_quotes.append(quote)
            continue
        # Fetch the quote text from stage1_data_responses
        resp = supabase.table("stage1_data_responses").select("verbatim_response").eq("response_id", quote_id).execute()
        if resp.data and resp.data[0].get("verbatim_response"):
            quote["text"] = resp.data[0]["verbatim_response"]
        updated_quotes.append(quote)
    # Update the finding with the new selected_quotes array
    supabase.table("stage3_findings").update({"selected_quotes": json.dumps(updated_quotes)}).eq("id", finding_id).execute()

print("Migration complete: selected_quotes now includes quote text.") 