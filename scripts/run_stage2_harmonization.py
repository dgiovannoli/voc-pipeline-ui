#!/usr/bin/env python3
"""
Step 2 Harmonization Runner
- Loads saved Stage 1 responses for a client from Supabase
- Applies LLM-based harmonization to subjects
- Updates records with harmonized fields (null-safe)

Usage:
  python scripts/run_stage2_harmonization.py --client "ShipStation API" --limit 200
"""
import argparse
import math
from typing import Optional
from supabase_database import SupabaseDatabase
from fixed_llm_harmonizer import FixedLLMHarmonizer


def sanitize_number(x):
	if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
		return None
	return x


def main():
	parser = argparse.ArgumentParser(description='Run Step 2 harmonization for a client')
	parser.add_argument('--client', required=True, help='Client ID to harmonize')
	parser.add_argument('--limit', type=int, default=0, help='Optional limit of records to process (0 = all)')
	args = parser.parse_args()

	db = SupabaseDatabase()
	harmonizer = FixedLLMHarmonizer()

	core_df = db.get_stage1_data_responses(client_id=args.client)
	if core_df.empty:
		print(f"No stage1_data_responses found for client {args.client}")
		return 0

	if args.limit and len(core_df) > args.limit:
		core_df = core_df.head(args.limit)

	updated = 0
	for _, row in core_df.iterrows():
		subject = row.get('subject')
		text = row.get('verbatim_response') or ''
		if not subject:
			continue
		try:
			res = harmonizer.harmonize_subject(subject, text)
			update_data = {
				'harmonized_subject': res.get('harmonized_subject'),
				'harmonization_confidence': sanitize_number(res.get('confidence')),
				'harmonization_method': res.get('mapping_method'),
				'harmonization_reasoning': res.get('reasoning'),
				'suggested_new_category': res.get('new_category_suggestion'),
				'harmonized_at': res.get('mapped_at'),
			}
			# Null-out NaN/inf
			update_data = {k: sanitize_number(v) for k, v in update_data.items()}
			db.supabase.table('stage1_data_responses').update(update_data).eq('response_id', row.get('response_id')).execute()
			updated += 1
		except Exception as e:
			print(f"⚠️ Harmonization failed for {row.get('response_id')}: {e}")

	print(f"✅ Harmonization updated {updated} rows for client {args.client}")
	return 0


if __name__ == '__main__':
	main() 