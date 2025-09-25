#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
import pandas as pd
import math

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from supabase_database import SupabaseDatabase  # type: ignore


def _norm_client(s: str) -> str:
	return ''.join(ch for ch in str(s).lower() if ch.isalnum())


def _to_iso_date(val: object) -> object:
	try:
		if val is None or (isinstance(val, float) and math.isnan(val)):
			return None
		dt = pd.to_datetime(val, errors='coerce')
		if pd.isna(dt):
			return None
		return dt.date().isoformat()
	except Exception:
		return None


def _none_if_nan(v: object) -> object:
	if v is None:
		return None
	if isinstance(v, float) and math.isnan(v):
		return None
	return v


def main():
	ap = argparse.ArgumentParser(description="Upsert interview_metadata from CSV (no transcript processing).")
	ap.add_argument("--csv", required=True, help="Path to metadata CSV file")
	ap.add_argument("--client", required=True, help="Client ID to filter rows")
	args = ap.parse_args()

	csv_path = Path(args.csv)
	if not csv_path.exists():
		print(f"CSV not found: {csv_path}")
		return 1

	db = SupabaseDatabase()
	df = pd.read_csv(csv_path)
	need_cols = [
		"Interview ID",
		"Client Name",
		"Interview Contact Full Name",
		"Interview Contact Company Name",
		"Deal Status",
		"Completion Date",
		"Industry",
	]
	missing = [c for c in need_cols if c not in df.columns]
	if missing:
		print(f"Missing required columns: {missing}")
		return 2

	df['__client_norm__'] = df['Client Name'].apply(_norm_client)
	target_norm = _norm_client(args.client)
	rows = df[df['__client_norm__'] == target_norm]
	if rows.empty:
		print(f"No rows for client '{args.client}' in CSV")
		return 0

	upserts = 0
	for _, r in rows.iterrows():
		interview_id = str(_none_if_nan(r.get('Interview ID')) or '')
		payload = {
			'client_id': args.client,
			'interview_id': interview_id,
			'interviewee_name': str(_none_if_nan(r.get('Interview Contact Full Name')) or ''),
			'company': str(_none_if_nan(r.get('Interview Contact Company Name')) or ''),
			'deal_status': str(_none_if_nan(r.get('Deal Status')) or ''),
			'date_of_interview': _to_iso_date(r.get('Completion Date')),
			'industry': str(_none_if_nan(r.get('Industry')) or ''),
			'interviewee_role': str(_none_if_nan(r.get('Interviewee Role')) or ''),
			'firm_size': str(_none_if_nan(r.get('Firm Size')) or ''),
			'audio_video_link': str(_none_if_nan(r.get('Audio/Video Link')) or ''),
			'contact_website': str(_none_if_nan(r.get('Interview Contact Website')) or ''),
			'interview_contact_website': str(_none_if_nan(r.get('Interview Contact Website')) or ''),
			'job_title': str(_none_if_nan(r.get('Job Title (from Contact ID)')) or ''),
			'contact_email': str(_none_if_nan(r.get('Interview Contact Email')) or ''),
			'client_name': str(_none_if_nan(r.get('Client Name')) or ''),
			'contact_id': str(_none_if_nan(r.get('Contact ID')) or ''),
			'interview_list_id_deals': str(_none_if_nan(r.get('Interview List ID (Deals Lookup)')) or ''),
			'interview_list_id_direct': str(_none_if_nan(r.get('Interview List ID (Direct Link)')) or ''),
		}
		# Remove empty strings to avoid overwriting with blanks
		payload = {k: v for k, v in payload.items() if v not in (None, '') or k in ('client_id','interview_id')}
		try:
			# Try update first
			res = db.supabase.table('interview_metadata').update(payload).eq('client_id', args.client).eq('interview_id', interview_id).execute()
			updated = bool(getattr(res, 'data', None)) and len(res.data) > 0
			if not updated:
				# Insert if not exists
				ins = db.supabase.table('interview_metadata').insert(payload).execute()
				if getattr(ins, 'data', None):
					upserts += 1
			else:
				upserts += 1
		except Exception as e:
			print(f"❌ Metadata sync failed for {interview_id}: {e}")

	print(f"Upserted/updated metadata for {upserts} rows for client '{args.client}'")
	return 0


if __name__ == "__main__":
	sys.exit(main()) 