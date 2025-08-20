#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from supabase_database import SupabaseDatabase


def import_evidence(xlsx_path: str, client_id: str) -> int:
    db = SupabaseDatabase()
    try:
        df = pd.read_excel(xlsx_path, sheet_name='Interview Cluster Evidence')
    except Exception as e:
        print(f"Failed to read sheet: {e}")
        return 0
    required = ['Cluster ID','Response ID']
    for col in required:
        if col not in df.columns:
            print(f"Missing required column: {col}")
            return 0
    total = 0
    for _, row in df.iterrows():
        cluster_id = row.get('Cluster ID')
        response_id = row.get('Response ID')
        if pd.isna(cluster_id) or pd.isna(response_id):
            continue
        label = row.get('Decision') if 'Decision' in df.columns else None
        notes = row.get('Notes') if 'Notes' in df.columns else None
        rank = row.get('Suggested Rank') if 'Suggested Rank' in df.columns else None
        ok = db.upsert_interview_cluster_evidence(
            client_id=client_id,
            cluster_id=int(cluster_id),
            response_id=str(response_id),
            evidence_label=str(label) if pd.notna(label) else None,
            notes=str(notes) if pd.notna(notes) else None,
            rank=int(rank) if pd.notna(rank) else None,
        )
        if ok:
            total += 1
    return total


def main():
    p = argparse.ArgumentParser(description='Import Interview Cluster Evidence decisions from workbook')
    p.add_argument('--client', required=True)
    p.add_argument('--xlsx', required=True)
    args = p.parse_args()
    count = import_evidence(args.xlsx, args.client)
    print(f"Upserted {count} evidence rows for {args.client}")


if __name__ == '__main__':
    main() 