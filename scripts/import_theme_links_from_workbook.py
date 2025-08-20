#!/usr/bin/env python3
import sys
from pathlib import Path
import argparse
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from supabase_database import SupabaseDatabase

"""
Expected workbook columns for decisions in All Themes tab:
- Theme ID (or unique key present; fallback to statement hash if needed)
- Subject
- Source (research/discovered/interview)
- Analyst Decision: Canonical | Duplicate-of:[ID] | Ignore
- Reason (optional)
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--client', required=True)
    ap.add_argument('--xlsx', required=True)
    ap.add_argument('--sheet', default='All Themes')
    args = ap.parse_args()

    db = SupabaseDatabase()
    try:
        df = pd.read_excel(args.xlsx, sheet_name=args.sheet)
    except Exception as e:
        print(f"Failed to read sheet: {e}")
        return 1

    required = ['Theme ID','Source','Analyst Decision']
    for c in required:
        if c not in df.columns:
            print(f"Missing column: {c}")
            return 1

    updates = 0
    for _, row in df.iterrows():
        decision = str(row.get('Analyst Decision') or '').strip()
        if not decision:
            continue
        if decision.lower() == 'ignore' or decision.lower() == 'canonical':
            continue
        # Expect Duplicate-of:[ID]
        if decision.lower().startswith('duplicate-of:'):
            theme_id = str(row.get('Theme ID'))
            canonical_id = decision.split(':', 1)[1].strip()
            source = str(row.get('Source') or '').lower()
            reason = str(row.get('Reason') or '')
            if theme_id and canonical_id:
                if db.upsert_theme_link(args.client, theme_id, canonical_id, source, reason):
                    updates += 1
    print(f"Upserted {updates} theme links for {args.client}")
    return 0

if __name__ == '__main__':
    sys.exit(main()) 