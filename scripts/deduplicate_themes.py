#!/usr/bin/env python3
"""
Deduplicate and merge research/discovered themes (post-generation) for a client.
- Groups by normalized harmonized_subject (strips DISCOVERED: and punctuation/case)
- Within each group, finds near-duplicates by evidence overlap and token Jaccard of statements
- Chooses a canonical theme (max customer coverage), merges evidence/coverage
- Marks merged children via section='MERGED_INTO:<canonical_id>'
- Updates canonical 'supporting_quotes' and 'company_coverage'

Usage:
  python scripts/deduplicate_themes.py --client "ShipStation API" --dry-run
  python scripts/deduplicate_themes.py --client "ShipStation API" --write
"""
import argparse
import re
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict
from supabase_database import SupabaseDatabase


def normalize_subject(s: str) -> str:
	if not s:
		return ""
	val = s
	val = re.sub(r"^DISCOVERED:\s*", "", val, flags=re.IGNORECASE)
	val = re.sub(r"[^a-z0-9]+", " ", val.lower())
	return val.strip()


def token_set(s: str) -> Set[str]:
	if not s:
		return set()
	toks = re.findall(r"[a-zA-Z0-9]+", s.lower())
	return set(toks)


def jaccard(a: Set[str], b: Set[str]) -> float:
	if not a and not b:
		return 1.0
	if not a or not b:
		return 0.0
	return len(a & b) / len(a | b)


def as_list(x) -> List:
	if x is None:
		return []
	if isinstance(x, list):
		return x
	# Safeguard for JSON-as-string
	try:
		import json
		return json.loads(x)
	except Exception:
		return []


def dedup_client(db: SupabaseDatabase, client_id: str, dry_run: bool) -> Dict[str, Any]:
	res = db.supabase.table('research_themes').select('*').eq('client_id', client_id).execute()
	themes: List[Dict[str, Any]] = res.data or []
	if not themes:
		return {"merged_pairs": 0, "canonicals": 0, "message": "No themes found"}

	# Group by normalized subject
	groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
	for t in themes:
		key = normalize_subject(t.get('harmonized_subject', ''))
		groups[key].append(t)

	merged_pairs = 0
	canonicals = 0
	updates = []  # (table_update_kwargs)

	for key, group in groups.items():
		if len(group) < 2:
			continue
		# Compute coverage & evidence sizes
		def coverage_count(t):
			return len(as_list(t.get('company_coverage')))
		def quotes_set(t):
			return set(as_list(t.get('supporting_quotes')))
		def stmt_tokens(t):
			return token_set(t.get('theme_statement', ''))

		# Choose canonical = max coverage, then max evidence
		canonical = max(group, key=lambda t: (coverage_count(t), len(quotes_set(t))))
		canonicals += 1
		canonical_id = canonical.get('theme_id')

		# Prepare unions for canonical
		union_quotes = quotes_set(canonical)
		union_companies = set(as_list(canonical.get('company_coverage')))

		for t in group:
			if t is canonical:
				continue
			# Similarity checks
			q_overlap = jaccard(quotes_set(t), quotes_set(canonical))
			title_sim = jaccard(stmt_tokens(t), stmt_tokens(canonical))
			# Merge if either signal is high enough
			if q_overlap >= 0.30 or title_sim >= 0.85:
				merged_pairs += 1
				union_quotes |= quotes_set(t)
				union_companies |= set(as_list(t.get('company_coverage')))
				# Mark child as merged
				if not dry_run:
					db.supabase.table('research_themes').update({
						'section': f'MERGED_INTO:{canonical_id}'
					}).eq('theme_id', t.get('theme_id')).execute()

		# Update canonical
		if not dry_run:
			db.supabase.table('research_themes').update({
				'supporting_quotes': list(union_quotes),
				'company_coverage': list(union_companies)
			}).eq('theme_id', canonical_id).execute()

	return {"merged_pairs": merged_pairs, "canonicals": canonicals, "message": "OK", "groups": len(groups)}


def main():
	parser = argparse.ArgumentParser(description='Deduplicate and merge research/discovered themes for a client')
	parser.add_argument('--client', required=True, help='Client ID')
	parser.add_argument('--dry-run', action='store_true', help='Do not write changes')
	parser.add_argument('--write', action='store_true', help='Apply changes')
	args = parser.parse_args()

	db = SupabaseDatabase()
	result = dedup_client(db, args.client, dry_run=not args.write)
	print(f"Groups: {result.get('groups')} | Canonicals: {result.get('canonicals')} | Merged pairs: {result.get('merged_pairs')} | {result.get('message')}")

	return 0

if __name__ == '__main__':
	main() 