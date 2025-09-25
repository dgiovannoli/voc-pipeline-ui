#!/usr/bin/env python3
"""
Quick Stage 1 Readiness Check
- Verifies which rows in a metadata CSV will be processed for a given client
  (Client Name match, Interview Status == Completed, and non-empty Raw Transcript)
- Does NOT call the LLM or write to the database.

Usage:
  python scripts/quick_stage1_readiness_check.py --csv "Interviews-ShipStation API_00034 (1).csv" --client "ShipStation API" --min-len 20
"""
import argparse
import csv
import os
import sys
import re
from typing import List, Dict


def normalize_client(s: str) -> str:
	return re.sub(r'[^a-z0-9]', '', (s or '').lower())


def load_rows(csv_path: str) -> List[Dict[str, str]]:
	if not os.path.exists(csv_path):
		raise FileNotFoundError(f"CSV file not found: {csv_path}")
	with open(csv_path, 'r', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		return list(reader)


def check_readiness(rows: List[Dict[str, str]], client_id: str, min_len: int) -> Dict[str, List[str]]:
	norm_client = normalize_client(client_id)
	eligible_ids: List[str] = []
	mismatched_client: List[str] = []
	not_completed: List[str] = []
	empty_transcript: List[str] = []
	short_transcript: List[str] = []
	all_client_ids: List[str] = []

	for r in rows:
		row_client = r.get('Client Name', '')
		if normalize_client(row_client) != norm_client:
			continue
		all_client_ids.append(r.get('Interview ID', ''))

		status = (r.get('Interview Status', '') or '').strip()
		if status != 'Completed':
			not_completed.append(r.get('Interview ID', ''))
			continue

		raw = (r.get('Raw Transcript', '') or '')
		raw_stripped = raw.strip()
		if len(raw_stripped) == 0:
			empty_transcript.append(r.get('Interview ID', ''))
			continue
		if len(raw_stripped) < min_len:
			short_transcript.append(r.get('Interview ID', ''))
			continue

		eligible_ids.append(r.get('Interview ID', ''))

	return {
		'found_for_client': all_client_ids,
		'eligible': eligible_ids,
		'not_completed': not_completed,
		'empty_transcript': empty_transcript,
		'short_transcript': short_transcript,
	}


def main():
	parser = argparse.ArgumentParser(description='Quick Stage 1 Readiness Check (no LLM/no DB)')
	parser.add_argument('--csv', required=True, help='Path to metadata CSV file')
	parser.add_argument('--client', required=True, help='Client ID to evaluate (e.g., "ShipStation API")')
	parser.add_argument('--min-len', type=int, default=20, help='Minimum Raw Transcript length to consider non-trivial')
	args = parser.parse_args()

	rows = load_rows(args.csv)
	result = check_readiness(rows, args.client, args.min_len)

	print(f"\nClient: {args.client}")
	print(f"Rows found for client: {len(result['found_for_client'])}")
	print(f"Eligible rows (Completed + Raw Transcript length >= {args.min_len}): {len(result['eligible'])}")

	if result['not_completed']:
		print(f"\nNot Completed ({len(result['not_completed'])}): {', '.join([x for x in result['not_completed'] if x])}")
	if result['empty_transcript']:
		print(f"\nEmpty Raw Transcript ({len(result['empty_transcript'])}): {', '.join([x for x in result['empty_transcript'] if x])}")
	if result['short_transcript']:
		print(f"\nShort Raw Transcript (<{args.min_len}) ({len(result['short_transcript'])}): {', '.join([x for x in result['short_transcript'] if x])}")
	if result['eligible']:
		print(f"\nEligible Interview IDs: {', '.join([x for x in result['eligible'] if x])}")

	# Exit code 0 even if none eligible; this is a diagnostic.
	return 0


if __name__ == '__main__':
	sys.exit(main()) 