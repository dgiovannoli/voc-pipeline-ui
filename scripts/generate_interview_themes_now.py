#!/usr/bin/env python3
import sys
from pathlib import Path
import json
import os
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from supabase_database import SupabaseDatabase  # type: ignore

PROMPT = (
	"You are analyzing a transcript of a win-loss interview.\n\n"
	"Your task is to summarize the most important insights into 3–5 concise bullet points, focusing only on:\n"
	"- Why the deal was WON\n"
	"- Why the deal was LOST\n"
	"- Any COMPETITIVE INTEL mentioned\n"
	"- Any other THEMES or SIGNALS the speaker emphasized as important\n\n"
	"Do not summarize the whole interview.\n"
	"Do not include filler or nice-to-know details.\n"
	"Write each bullet as if it will go into a client-facing win-loss report.\n\n"
	"Return exactly this JSON object:\n"
	"{\"themes\":[{\"theme\":\"one bullet\"}, {\"theme\":\"another bullet\"}]}\n"
	"Rules: 3 to 5 items only; do not add any fields other than 'theme'."
)


def _fallback_extract_bullets(text: str) -> list[str]:
	"""If model doesn't return JSON, extract 3–5 bullet-like lines."""
	lines = [l.strip(" \t•-*\u2022") for l in text.splitlines() if l.strip()]
	# Keep lines that look like bullets or short statements
	candidates = []
	for l in lines:
		if re.match(r"^[-*\u2022]", l) or len(l.split()) >= 4:
			candidates.append(l.rstrip('.'))
	# Deduplicate while preserving order
	seen = set()
	uniq = []
	for c in candidates:
		if c not in seen:
			seen.add(c)
			uniq.append(c)
	return uniq[:5]


def call_llm(text: str) -> list[str]:
	try:
		from langchain_openai import ChatOpenAI
		llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2, max_tokens=500)
		resp = llm.invoke(f"{PROMPT}\n\nTRANSCRIPT:\n{text[:10000]}")
		out = (resp.content or "").strip()
		out = out.replace('```json','').replace('```','').strip()
		start = out.find('{')
		end = out.rfind('}') + 1
		if start != -1 and end > start:
			obj = json.loads(out[start:end])
			arr = obj.get('themes') or []
			vals = [str(x.get('theme') if isinstance(x, dict) else x) for x in arr if x]
			if 3 <= len(vals) <= 5:
				return vals
			# If too many, trim; if too few, fall back to extraction
			if len(vals) > 5:
				return vals[:5]
			if len(vals) < 3:
				return _fallback_extract_bullets(out)
			return vals
		# No JSON found → fallback
		return _fallback_extract_bullets(out)
	except Exception:
		return []


def main():
	import argparse
	ap = argparse.ArgumentParser(description="Generate per-interview themes from saved transcripts now.")
	ap.add_argument("--client", required=True, help="Client ID")
	args = ap.parse_args()

	db = SupabaseDatabase()
	# Load transcripts
	tx = db.fetch_interview_transcripts(args.client)
	if tx is None or tx.empty:
		print("No transcripts found.")
		return 1

	written = 0
	for _, row in tx.iterrows():
		iid = str(row.get('interview_id') or "").strip()
		text = str(row.get('full_transcript') or "").strip()
		if not iid or not text:
			continue
		themes = call_llm(text)
		for t in themes[:5]:
			if t:
				ok = db.upsert_interview_level_theme(client_id=args.client, interview_id=iid, theme_statement=t, subject="", sentiment=None, impact_score=None, notes="auto")
				if ok:
					written += 1
	print(f"Wrote {written} interview themes for {args.client}")
	return 0


if __name__ == "__main__":
	sys.exit(main()) 