#!/usr/bin/env python3
import argparse
import sys
import pandas as pd
from pathlib import Path

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from supabase_database import SupabaseDatabase  # type: ignore

def main():
	ap = argparse.ArgumentParser(description="Upsert full transcripts from a metadata CSV without full processing.")
	ap.add_argument("--csv", required=True, help="Path to metadata CSV file")
	ap.add_argument("--client", required=True, help="Client ID to filter/save transcripts under")
	ap.add_argument("--column", default="Raw Transcript", help="Transcript column name (default: Raw Transcript)")
	args = ap.parse_args()

	csv_path = Path(args.csv)
	if not csv_path.exists():
		print(f"CSV not found: {csv_path}")
		return 1

	db = SupabaseDatabase()
	df = pd.read_csv(csv_path)
	required = ["Interview ID", "Client Name", "Interview Contact Company Name", "Interview Contact Full Name", args.column]
	missing = [c for c in required if c not in df.columns]
	if missing:
		print(f"Missing required columns: {missing}")
		return 1

	# Normalize client match
	client_norm = args.client.strip().lower().replace(" ", "")
	def _norm(s: str) -> str:
		return str(s or "").strip().lower().replace(" ", "")

	rows = df[df["Client Name"].apply(_norm) == client_norm]
	if rows.empty:
		print(f"No rows for client '{args.client}' in CSV")
		return 2

	upserts = 0
	for _, r in rows.iterrows():
		text = str(r.get(args.column, "") or "").strip()
		if not text:
			continue
		interview_id = str(r.get("Interview ID", "")).strip()
		company = str(r.get("Interview Contact Company Name", "")).strip()
		name = str(r.get("Interview Contact Full Name", "")).strip()
		ok = db.upsert_interview_transcript(client_id=args.client, interview_id=interview_id, company=company, interviewee_name=name, full_transcript=text)
		if ok:
			upserts += 1

	print(f"Upserted {upserts} transcripts for client '{args.client}' from {csv_path.name}")
	return 0


if __name__ == "__main__":
	sys.exit(main()) 