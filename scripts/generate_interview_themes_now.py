#!/usr/bin/env python3
import sys
from pathlib import Path
import json
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from supabase_database import SupabaseDatabase  # type: ignore

PROMPT = (
	"Summarize this interview into 5-7 concise, non-overlapping themes. "
	"Each theme should be a single sentence capturing what matters most in the conversation. "
	"Return JSON array under key 'themes' with items of the form {\"theme\":\"...\"}. "
	"Do not include quotes or IDs; only themes."
)


def call_llm(text: str) -> list[str]:
	try:
		from langchain_openai import ChatOpenAI
		llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2, max_tokens=400)
		resp = llm.invoke(f"{PROMPT}\n\nTEXT:\n{text[:8000]}")
		out = (resp.content or "").strip()
		out = out.replace('```json','').replace('```','').strip()
		start = out.find('{')
		end = out.rfind('}') + 1
		if start != -1 and end > start:
			obj = json.loads(out[start:end])
			arr = obj.get('themes') or []
			return [str(x.get('theme') if isinstance(x, dict) else x) for x in arr if x]
		return []
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
		for t in themes[:7]:
			if t:
				ok = db.upsert_interview_level_theme(client_id=args.client, interview_id=iid, theme_statement=t, subject="", sentiment=None, impact_score=None, notes="auto")
				if ok:
					written += 1
	print(f"Wrote {written} interview themes for {args.client}")
	return 0


if __name__ == "__main__":
	sys.exit(main()) 