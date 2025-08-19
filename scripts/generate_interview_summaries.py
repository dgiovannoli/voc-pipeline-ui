#!/usr/bin/env python3
import argparse
import os
import csv
from pathlib import Path
from typing import List, Dict, Any

from openai import OpenAI

from win_loss_report_generator import WinLossReportGenerator


def summarize_text(client: OpenAI, text: str) -> str:
	messages = [
		{"role": "system", "content": "You are an analyst writing a brief win/loss interview summary."},
		{"role": "user", "content": (
			"In 2–3 sentences, summarize the interview like a win‑loss analyst. "
			"Focus on who the interviewee is, why they were evaluating, the qualitative tone (no numbers), "
			"top 1–2 reasons behind that tone, and one improvement that would have increased confidence.\n\n"
			f"Transcript:\n{text[:6000]}"
		)}
	]
	resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0.4, max_tokens=140)
	return (resp.choices[0].message.content or '').strip()


def load_interview_texts(gen: WinLossReportGenerator) -> List[Dict[str, Any]]:
	# Try to pull interview metadata table if available; otherwise use stage1 responses grouped by interview_id
	df = gen.db.get_stage1_data_responses(client_id=gen.client_id)
	records = df.to_dict('records') if df is not None else []
	by_interview: Dict[str, Dict[str, Any]] = {}
	for r in records:
		ikey = r.get('interview_id') or f"{r.get('company') or r.get('company_name') or 'Unknown'}|{r.get('interviewee_name','')}|{str(r.get('created_at') or '')[:10]}"
		acc = by_interview.setdefault(ikey, {"company": r.get('company') or r.get('company_name') or 'Unknown', "chunks": []})
		text = (r.get('verbatim_response') or '').strip()
		if text:
			acc["chunks"].append(text)
	items = []
	for ikey, v in by_interview.items():
		full_text = "\n".join(v["chunks"])[:12000]
		if not full_text:
			continue
		items.append({"interview_key": ikey, "company": v["company"], "text": full_text})
	return items


def upsert_summaries(gen: WinLossReportGenerator, summaries: List[Dict[str, str]]):
	# Try Supabase upsert; else write CSV
	try:
		db = gen.db
		rows = []
		for s in summaries:
			rows.append({
				"client_id": gen.client_id,
				"interview_key": s["interview_key"],
				"company": s["company"],
				"summary": s["summary"],
			})
		# Use a table name interview_summaries (create externally if needed)
		db.supabase.table('interview_summaries').upsert(rows).execute()
		print(f"✅ Upserted {len(rows)} interview summaries to Supabase")
		return
	except Exception as e:
		print(f"⚠️ Supabase upsert unavailable ({e}). Writing CSV.")
		out = Path(f"interview_summaries_{gen.client_id}.csv")
		with out.open('w', newline='') as f:
			w = csv.DictWriter(f, fieldnames=["client_id","interview_key","company","summary"]) 
			w.writeheader()
			for s in summaries:
				w.writerow({"client_id": gen.client_id, **s})
		print(f"✅ Wrote {len(summaries)} interview summaries to {out}")


def main():
	p = argparse.ArgumentParser(description="Generate brief win-loss summaries per interview and store them")
	p.add_argument('--client', required=True)
	args = p.parse_args()
	api_key = os.getenv('OPENAI_API_KEY')
	if not api_key:
		raise SystemExit("OPENAI_API_KEY not set")
	client = OpenAI(api_key=api_key)
	gen = WinLossReportGenerator(args.client)
	items = load_interview_texts(gen)
	summaries = []
	for it in items:
		try:
			sum_text = summarize_text(client, it["text"])
			summaries.append({"interview_key": it["interview_key"], "company": it["company"], "summary": sum_text})
		except Exception as e:
			print(f"Failed to summarize {it['interview_key']}: {e}")
	upsert_summaries(gen, summaries)

if __name__ == '__main__':
	main() 