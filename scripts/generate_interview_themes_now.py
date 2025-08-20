#!/usr/bin/env python3
import sys
from pathlib import Path
import json
import os
import re
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from supabase_database import SupabaseDatabase  # type: ignore

PROMPT = (
	"WIN–LOSS INTERVIEW THEMES (OUTCOME‑AWARE, ICP TARGET COVERED)\n\n"
	"Inputs\n"
	"- outcome: \"<WON|LOST|ICP_TARGET|UNKNOWN>\"\n"
	"- transcript: <<<TRANSCRIPT_TEXT>>>\n\n"
	"Task\n"
	"1) Determine operative_outcome\n"
	"   - If outcome ≠ UNKNOWN: use it as ground truth.\n"
	"   - If UNKNOWN: infer WON or LOST or ICP_TARGET (one word) + 1‑sentence rationale.\n\n"
	"2) Produce 3–5 reasons_for_outcome (bullets), consistent with the operative_outcome\n"
	"   - If WON: why we won (no loss bullets).\n"
	"   - If LOST: why we lost (no win bullets).\n"
	"   - If ICP_TARGET: give decision insights to guide GTM (current_vendor_drivers, disqualifiers_for_us, evaluation_criteria, switching_barriers).\n"
	"   - Each bullet ≤ 22 words, client‑facing, specific, no filler.\n\n"
	"3) competitive_intel (1–3 bullets)\n"
	"   - Vendor strengths/weaknesses, pricing models, feature deltas, integration claims. In LOST/ICP_TARGET, praise of another vendor goes here.\n\n"
	"4) other_signals (0–2 bullets)\n"
	"   - Important patterns not already covered.\n\n"
	"Constraints\n"
	"- No quotes/IDs; no hedging; no duplication across sections.\n"
	"- Keep reasons_for_outcome strictly aligned to operative_outcome.\n\n"
	"Output (valid JSON only)\n"
	"{\n"
	"  \"operative_outcome\": \"WON|LOST|ICP_TARGET\",\n"
	"  \"rationale\": \"Present only if UNKNOWN input; else empty string\",\n"
	"  \"reasons_for_outcome\": [\n"
	"    {\"theme\": \"…\", \"category\": \"product_fit|commercial|service|speed|trust|gaps|price_model|procurement|competitor_edge|current_vendor_drivers|disqualifiers_for_us|evaluation_criteria|switching_barriers\"}\n"
	"  ],\n"
	"  \"competitive_intel\": [{\"theme\": \"…\"}],\n"
	"  \"other_signals\": [{\"theme\": \"…\"}]\n"
	"}\n"
)


def _fallback_extract_bullets(text: str) -> List[str]:
	lines = [l.strip(" \t•-*\u2022") for l in text.splitlines() if l.strip()]
	candidates = []
	for l in lines:
		if re.match(r"^[-*\u2022]", l) or len(l.split()) >= 4:
			candidates.append(l.rstrip('.'))
	seen = set()
	uniq = []
	for c in candidates:
		if c not in seen:
			seen.add(c)
			uniq.append(c)
	return uniq[:5]


def call_llm(outcome: str, text: str) -> Dict[str, Any]:
	try:
		from langchain_openai import ChatOpenAI
		llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2, max_tokens=900)
		filled = PROMPT.replace("<WON|LOST|ICP_TARGET|UNKNOWN>", outcome).replace("<<<TRANSCRIPT_TEXT>>>", text[:12000])
		resp = llm.invoke(filled)
		out = (resp.content or "").strip().replace('```json','').replace('```','').strip()
		start = out.find('{'); end = out.rfind('}') + 1
		if start != -1 and end > start:
			obj = json.loads(out[start:end])
			return obj
		# Fallback JSON
		return {
			"operative_outcome": outcome if outcome != "UNKNOWN" else "ICP_TARGET",
			"rationale": "",
			"reasons_for_outcome": [{"theme": t, "category": "signal"} for t in _fallback_extract_bullets(out)],
			"competitive_intel": [],
			"other_signals": []
		}
	except Exception:
		return {
			"operative_outcome": outcome if outcome != "UNKNOWN" else "ICP_TARGET",
			"rationale": "",
			"reasons_for_outcome": [],
			"competitive_intel": [],
			"other_signals": []
		}


def main():
	import argparse
	ap = argparse.ArgumentParser(description="Generate per-interview themes from saved transcripts now (outcome-aware).")
	ap.add_argument("--client", required=True, help="Client ID")
	args = ap.parse_args()

	db = SupabaseDatabase()
	# Load transcripts and metadata
	tx = db.fetch_interview_transcripts(args.client)
	meta = db.get_interview_metadata(args.client)
	if tx is None or tx.empty:
		print("No transcripts found.")
		return 1
	if meta is None:
		meta = Path()

	meta_df = meta if isinstance(meta, Path) else meta
	written = 0
	for _, row in tx.iterrows():
		iid = str(row.get('interview_id') or "").strip()
		text = str(row.get('full_transcript') or "").strip()
		if not iid or not text:
			continue
		deal_status = "UNKNOWN"
		try:
			ms = meta_df[meta_df['interview_id'] == iid]
			if not ms.empty:
				raw = str(ms.iloc[0].get('deal_status') or '').strip().lower()
				if raw in ('won','lost'):
					deal_status = raw.upper()
				elif 'icp' in raw:
					deal_status = 'ICP_TARGET'
		except Exception:
			pass

		obj = call_llm(deal_status if deal_status else "UNKNOWN", text)
		op_out = (obj.get('operative_outcome') or deal_status or 'UNKNOWN').upper()
		# Save reasons_for_outcome
		for item in (obj.get('reasons_for_outcome') or [])[:5]:
			theme = str(item.get('theme') if isinstance(item, dict) else item)
			cat = str(item.get('category') if isinstance(item, dict) else '').strip().lower() or ('won' if op_out=='WON' else 'lost' if op_out=='LOST' else 'signal')
			subject = 'won' if op_out=='WON' else 'lost' if op_out=='LOST' else cat
			if theme:
				ok = db.upsert_interview_level_theme(client_id=args.client, interview_id=iid, theme_statement=theme, subject=subject, sentiment=None, impact_score=None, notes="auto")
				if ok:
					written += 1
		# Save competitive_intel
		for ci in (obj.get('competitive_intel') or [])[:3]:
			theme = str(ci.get('theme') if isinstance(ci, dict) else ci)
			if theme:
				ok = db.upsert_interview_level_theme(client_id=args.client, interview_id=iid, theme_statement=theme, subject='ci', sentiment=None, impact_score=None, notes="auto")
				if ok:
					written += 1
		# Save other_signals
		for sig in (obj.get('other_signals') or [])[:2]:
			theme = str(sig.get('theme') if isinstance(sig, dict) else sig)
			if theme:
				ok = db.upsert_interview_level_theme(client_id=args.client, interview_id=iid, theme_statement=theme, subject='signal', sentiment=None, impact_score=None, notes="auto")
				if ok:
					written += 1

	print(f"Wrote {written} interview themes for {args.client}")
	return 0


if __name__ == "__main__":
	sys.exit(main()) 