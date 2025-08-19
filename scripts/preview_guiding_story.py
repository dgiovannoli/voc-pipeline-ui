#!/usr/bin/env python3
import argparse
import json
import sys

from guiding_story_analyzer import build_guiding_story_payload

try:
	from supabase_database import SupabaseDatabase  # root DB
except Exception:
	SupabaseDatabase = None


def _resolve_db():
	if SupabaseDatabase:
		return SupabaseDatabase()
	raise RuntimeError("SupabaseDatabase not available")


def main():
	ap = argparse.ArgumentParser(description="Preview Guiding Story payload for a client (no LLM).")
	ap.add_argument("--client", required=True, help="Client ID")
	args = ap.parse_args()

	db = _resolve_db()
	payload = build_guiding_story_payload(client_id=args.client, db=db)
	segs = payload.get("segments", {})
	summary = {
		"client_id": payload.get("client_id"),
		"generated_at": payload.get("generated_at"),
		"segments": {
			k: {
				"interview_count": v.get("interview_count"),
				"share_of_interviews": v.get("share_of_interviews"),
				"mean_impact_score": v.get("mean_impact_score"),
				"price_efficiency_rate": v.get("price_efficiency_rate"),
				"provider_indifference_index_mean": v.get("provider_indifference_index_mean"),
			}
			for k, v in segs.items()
		},
		"notes": payload.get("notes"),
	}
	print(json.dumps(summary, indent=2))

	total_interviews = sum(v.get("interview_count", 0) for v in segs.values())
	if total_interviews == 0:
		sys.exit(1)


if __name__ == "__main__":
	main() 