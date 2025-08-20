from __future__ import annotations

import re
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple, Set

import pandas as pd
import numpy as np
from datetime import datetime, timezone

DEFAULT_KEYWORDS: Dict[str, Sequence[str]] = {
	"direct_api": ["api","webhook","portal","shipstation api","easypost api","direct integration"],
	"via_3pl_wms": ["3pl","wms","warehouse management","third-party logistics","3rd party","fulfillment center","warehouse"],
	"price_efficiency": ["price","rate","fee","cost","total cost","throughput","sla","uptime","latency","automation","integration","reliability","efficiency","capacity"],
	"provider_brands": ["ShipStation","EasyPost","Pitney Bowes","Stamps","Shippo","XPS","Endicia"],
}

_WORD_BOUNDARY_TOKENS = {"api", "3pl", "wms", "sla"}


def _compile_patterns(keywords: Dict[str, Sequence[str]]) -> Dict[str, List[re.Pattern]]:
	patterns: Dict[str, List[re.Pattern]] = {}
	for k, toks in keywords.items():
		compiled: List[re.Pattern] = []
		for t in toks:
			t_norm = re.escape(t.strip())
			if t.lower() in _WORD_BOUNDARY_TOKENS or re.fullmatch(r"[a-z0-9]+", t.lower()):
				pat = re.compile(rf"(?i)\b{t_norm}\b")
			else:
				pat = re.compile(rf"(?i){t_norm}")
			compiled.append(pat)
		patterns[k] = compiled
	return patterns


def _count_patterns(text: str, pats: List[re.Pattern]) -> int:
	if not text:
		return 0
	total = 0
	for p in pats:
		total += len(p.findall(text))
	return total


def _any_match(text: str, pats: List[re.Pattern]) -> bool:
	if not text:
		return False
	return any(p.search(text) is not None for p in pats)


def _safe_mean(series: pd.Series) -> Optional[float]:
	try:
		vals = pd.to_numeric(series, errors="coerce")
		if vals.notna().any():
			return float(vals.mean())
		return None
	except Exception:
		return None


@dataclass
class QuoteRef:
	response_id: Any
	interview_id: Any
	company: Optional[str]
	interviewee_name: Optional[str]
	excerpt: str


def assign_channel_for_interview(
	responses_df: pd.DataFrame,
	metadata_row: pd.Series,
	keywords: Optional[Dict[str, Sequence[str]]] = None,
) -> Literal["direct_api", "via_3pl_wms", "uncertain"]:
	if metadata_row is not None:
		kc = str(metadata_row.get("known_channel") or "").strip().lower()
		if kc in {"direct_api", "via_3pl_wms"}:
			return kc  # type: ignore[return-value]

	kw = keywords or DEFAULT_KEYWORDS
	pats = _compile_patterns(kw)
	text = " ".join(
		(responses_df.get("question", pd.Series(dtype=str)).fillna("").astype(str) + " " +
		 responses_df.get("verbatim_response", pd.Series(dtype=str)).fillna("").astype(str))
		.tolist()
	)
	direct_hits = _count_patterns(text, pats["direct_api"])
	via_hits = _count_patterns(text, pats["via_3pl_wms"])
	if direct_hits > via_hits:
		return "direct_api"
	elif via_hits > direct_hits:
		return "via_3pl_wms"
	else:
		return "uncertain"


def compute_interview_signals(
	responses_df: pd.DataFrame,
	keywords: Optional[Dict[str, Sequence[str]]] = None,
) -> Dict[str, Any]:
	kw = keywords or DEFAULT_KEYWORDS
	pats = _compile_patterns(kw)
	all_text = " ".join(
		(responses_df.get("question", pd.Series(dtype=str)).fillna("").astype(str) + " " +
		 responses_df.get("verbatim_response", pd.Series(dtype=str)).fillna("").astype(str))
		.tolist()
	)
	provider_brand_hits = _count_patterns(all_text, pats["provider_brands"]) 
	channel_hits = _count_patterns(all_text, pats["direct_api"]) + _count_patterns(all_text, pats["via_3pl_wms"])
	per_resp_text = (
		responses_df.get("question", pd.Series(dtype=str)).fillna("").astype(str) + " " +
		responses_df.get("verbatim_response", pd.Series(dtype=str)).fillna("").astype(str)
	)
	has_price_eff = per_resp_text.apply(lambda t: _any_match(t, pats["price_efficiency"]))
	price_efficiency_hits = int(has_price_eff.sum())
	price_efficiency_salience = float(has_price_eff.mean()) if len(has_price_eff) else 0.0

	s = responses_df.get("sentiment", pd.Series(dtype=str)).fillna("").astype(str).str.lower()
	pos = (s == "positive").sum()
	neg = (s == "negative").sum()
	neu = (s == "neutral").sum() + (s == "").sum()
	total = max(int(pos + neg + neu), 1)
	sentiment_mix = {
		"positive": round(pos / total, 4),
		"negative": round(neg / total, 4),
		"neutral": round(neu / total, 4),
	}

	mean_impact_score = _safe_mean(responses_df.get("impact_score", pd.Series(dtype=float)))
	subj_series = responses_df.get("harmonized_subject", pd.Series(dtype=str)).dropna().astype(str)
	subjects: Set[str] = set([s.strip() for s in subj_series if s.strip()])

	return {
		"provider_brand_hits": int(provider_brand_hits),
		"channel_hits": int(channel_hits),
		"price_efficiency_hits": int(price_efficiency_hits),
		"price_efficiency_salience": float(price_efficiency_salience),
		"sentiment_mix": sentiment_mix,
		"mean_impact_score": mean_impact_score,
		"subjects": subjects,
	}


def compute_provider_indifference_index(interview_signals_df: pd.DataFrame) -> pd.Series:
	num = interview_signals_df["channel_hits"].fillna(0).astype(float) + interview_signals_df["price_efficiency_hits"].fillna(0).astype(float)
	brand = interview_signals_df["provider_brand_hits"].fillna(0).astype(float)
	denom = num + brand
	with np.errstate(divide="ignore", invalid="ignore"):
		idx = np.where(denom > 0, num / denom, 0.5)
	return pd.Series(idx, index=interview_signals_df.index, name="provider_indifference_index").clip(0.0, 1.0)


def aggregate_segment_metrics(interview_level_df: pd.DataFrame) -> Dict[str, Any]:
	segments: Dict[str, Any] = {}
	total_interviews = int(len(interview_level_df))
	if total_interviews == 0:
		return segments

	for seg, g in interview_level_df.groupby("assigned_channel", dropna=False):
		seg_key = seg if isinstance(seg, str) and seg else "uncertain"
		interview_count = int(len(g))
		company_count = int(g["company"].nunique(dropna=True))
		share = interview_count / total_interviews if total_interviews else 0.0

		if "sentiment_mix" in g.columns:
			sent_df = pd.json_normalize(g["sentiment_mix"])
			sent_avg = {
				"positive": round(float(sent_df["positive"].mean()) if "positive" in sent_df else 0.0, 4),
				"negative": round(float(sent_df["negative"].mean()) if "negative" in sent_df else 0.0, 4),
				"neutral": round(float(sent_df["neutral"].mean()) if "neutral" in sent_df else 0.0, 4),
			}
		else:
			sent_avg = {"positive": 0.0, "negative": 0.0, "neutral": 1.0}

		mean_impact = _safe_mean(g["mean_impact_score"]) if "mean_impact_score" in g.columns else None
		price_eff_rate = float((g["price_efficiency_salience"] > 0).mean()) if "price_efficiency_salience" in g.columns else 0.0
		price_eff_salience_mean = float(g["price_efficiency_salience"].mean()) if "price_efficiency_salience" in g.columns else 0.0
		pii_mean = float(g["provider_indifference_index"].mean()) if "provider_indifference_index" in g.columns else 0.0

		subj_counts: Dict[str, int] = {}
		if "subjects" in g.columns:
			for sset in g["subjects"]:
				for s in (sset or []):
					subj_counts[s] = subj_counts.get(s, 0) + 1
		top_subjects = sorted(
			[{"subject": s, "interview_count": c} for s, c in subj_counts.items()],
			key=lambda x: (-x["interview_count"], x["subject"])
		)[:10]

		segments[seg_key] = {
			"interview_count": interview_count,
			"company_count": company_count,
			"share_of_interviews": round(share, 4),
			"sentiment_mix": sent_avg,
			"mean_impact_score": round(mean_impact, 4) if mean_impact is not None else None,
			"price_efficiency_rate": round(price_eff_rate, 4),
			"price_efficiency_salience_mean": round(price_eff_salience_mean, 4),
			"provider_indifference_index_mean": round(pii_mean, 4),
			"top_subjects": top_subjects,
		}

	return segments


def select_representative_quotes(
	responses_df: pd.DataFrame,
	interview_level_df: pd.DataFrame,
	per_segment: int = 3,
	max_chars: int = 200,
	keywords: Optional[Dict[str, Sequence[str]]] = None,
) -> Dict[str, List[Dict[str, Any]]]:
	kw = keywords or DEFAULT_KEYWORDS
	pats = _compile_patterns(kw)
	seg_map = interview_level_df.set_index("interview_id")["assigned_channel"].to_dict()
	# Use the same grouping key column for mapping
	key_col = "__group_key__" if "__group_key__" in responses_df.columns else "interview_id"
	r = responses_df[responses_df[key_col].isin(seg_map.keys())].copy()
	text_series = (r.get("question", pd.Series(dtype=str)).fillna("").astype(str) + " " +
				   r.get("verbatim_response", pd.Series(dtype=str)).fillna("").astype(str))
	has_anchor = text_series.apply(lambda t: _any_match(t, pats["direct_api"]) or _any_match(t, pats["via_3pl_wms"]) or _any_match(t, pats["price_efficiency"]))
	r["__has_anchor__"] = has_anchor
	r["__impact__"] = pd.to_numeric(r.get("impact_score", pd.Series(dtype=float)), errors="coerce").fillna(-1.0)

	quotes_by_seg: Dict[str, List[Dict[str, Any]]] = {"direct_api": [], "via_3pl_wms": [], "uncertain": []}
	for seg in ["direct_api", "via_3pl_wms", "uncertain"]:
		sub = r[[seg_map.get(k) == seg for k in r[key_col]]].copy()
		if sub.empty:
			continue
		sub = sub.sort_values(by=["__has_anchor__", "__impact__"], ascending=[False, False])
		picked_interviews: Set[Any] = set()
		rows: List[Dict[str, Any]] = []
		for _, row in sub.iterrows():
			iid = row.get(key_col)
			if iid in picked_interviews:
				continue
			excerpt = str(row.get("verbatim_response", "") or "")
			if len(excerpt) > max_chars:
				excerpt = excerpt[: max(0, max_chars - 1)].rstrip() + "…"
			rows.append({
				"response_id": row.get("response_id"),
				"interview_id": iid,
				"company": row.get("company"),
				"interviewee_name": row.get("interviewee_name"),
				"excerpt": excerpt,
			})
			picked_interviews.add(iid)
			if len(rows) >= per_segment:
				break
		quotes_by_seg[seg] = rows

	return quotes_by_seg


def build_guiding_story_payload(
	client_id: Any,
	db: Any,
	keywords: Optional[Dict[str, Sequence[str]]] = None,
) -> Dict[str, Any]:
	# Fetch
	responses_df = None
	meta_df = None
	transcripts_df = None  # NEW
	try:
		if hasattr(db, "fetch_stage1_responses"):
			responses_df = db.fetch_stage1_responses(client_id)
		elif hasattr(db, "get_stage1_data_responses"):
			responses_df = db.get_stage1_data_responses(client_id=client_id)
	except Exception:
		responses_df = None
	try:
		if hasattr(db, "fetch_interview_metadata"):
			meta_df = db.fetch_interview_metadata(client_id)
		elif hasattr(db, "get_interview_metadata"):
			meta_df = db.get_interview_metadata(client_id)
	except Exception:
		meta_df = None
	# Fetch transcripts if available  # NEW
	try:
		if hasattr(db, "fetch_interview_transcripts"):
			transcripts_df = db.fetch_interview_transcripts(client_id)
	except Exception:
		transcripts_df = None

	if responses_df is None or len(responses_df) == 0:
		return {"client_id": client_id, "generated_at": datetime.now(timezone.utc).isoformat(), "segments": {}, "interviews": [], "quotes": {}, "notes": "No responses found."}
	if meta_df is None:
		meta_df = pd.DataFrame(columns=["interview_id","interviewee_name","company","company_size","known_channel","deal_status","client_id"])

	responses_df = pd.DataFrame(responses_df).copy()
	meta_df = pd.DataFrame(meta_df).copy()
	if transcripts_df is not None:
		transcripts_df = pd.DataFrame(transcripts_df).copy()

	for col in ["response_id","interview_id","company","interviewee_name","question","verbatim_response","sentiment","impact_score","harmonized_subject","deal_status","client_id"]:
		if col not in responses_df.columns:
			responses_df[col] = None
	for col in ["interview_id","interviewee_name","company","company_size","known_channel","deal_status","client_id"]:
		if col not in meta_df.columns:
			meta_df[col] = None

	responses_df = responses_df.merge(
		meta_df[["interview_id","company","interviewee_name","company_size","known_channel"]].drop_duplicates("interview_id"),
		on="interview_id", how="left", suffixes=("","_meta")
	)

	# Determine grouping key: prefer interview_id if present; else company|interviewee_name
	use_interview_id = "interview_id" in responses_df.columns and responses_df["interview_id"].notna().any()
	if use_interview_id:
		responses_df["__group_key__"] = responses_df["interview_id"].astype(str)
	else:
		responses_df["__group_key__"] = (
			responses_df.get("company", pd.Series(dtype=str)).fillna("").astype(str) + "|" +
			responses_df.get("interviewee_name", pd.Series(dtype=str)).fillna("").astype(str)
		)
	meta_df["__group_key__"] = (
		meta_df.get("company", pd.Series(dtype=str)).fillna("").astype(str) + "|" +
		meta_df.get("interviewee_name", pd.Series(dtype=str)).fillna("").astype(str)
	)
	if transcripts_df is not None and not transcripts_df.empty:
		# Normalize transcript key
		if "interview_id" in transcripts_df.columns and transcripts_df["interview_id"].notna().any():
			transcripts_df["__group_key__"] = transcripts_df["interview_id"].astype(str)
		else:
			transcripts_df["__group_key__"] = (
				transcripts_df.get("company", pd.Series(dtype=str)).fillna("").astype(str) + "|" +
				transcripts_df.get("interviewee_name", pd.Series(dtype=str)).fillna("").astype(str)
			)

	interview_rows: List[Dict[str, Any]] = []
	kw = keywords or DEFAULT_KEYWORDS
	for key, g in responses_df.groupby("__group_key__"):
		if use_interview_id:
			md_row = meta_df[meta_df["interview_id"] == g["interview_id"].dropna().astype(str).iloc[0]].iloc[0] if g["interview_id"].notna().any() and (meta_df["interview_id"] == g["interview_id"].dropna().astype(str).iloc[0]).any() else pd.Series(dtype=object)
		else:
			md_row = meta_df[meta_df["__group_key__"] == key].iloc[0] if (meta_df["__group_key__"] == key).any() else pd.Series(dtype=object)
		# Prefer full transcript text for signals if available
		if transcripts_df is not None and not transcripts_df.empty and (transcripts_df["__group_key__"] == key).any():
			full_text = transcripts_df[transcripts_df["__group_key__"] == key].iloc[0].get("full_transcript", "") or ""
			temp_df = pd.DataFrame({
				"question": [""],
				"verbatim_response": [full_text],
				"sentiment": [None],
				"impact_score": [None],
				"harmonized_subject": [None],
			})
			signals = compute_interview_signals(temp_df, kw)
		else:
			signals = compute_interview_signals(g, kw)
		seg = assign_channel_for_interview(g, md_row, kw)
		interview_rows.append({
			"interview_id": key,
			"company": (md_row.get("company") if md_row is not None else None) or g["company"].dropna().iloc[0] if "company" in g and not g["company"].dropna().empty else None,
			"company_size": (md_row.get("company_size") if md_row is not None else None),
			"known_channel": (md_row.get("known_channel") if md_row is not None else None),
			"assigned_channel": seg,
			**signals,
		})

	interview_level_df = pd.DataFrame(interview_rows)
	if interview_level_df.empty:  # NEW
		return {"client_id": client_id, "generated_at": datetime.now(timezone.utc).isoformat(), "segments": {}, "interviews": [], "quotes": {}, "notes": "No interviews aggregated for guiding story."}
	interview_level_df = interview_level_df.set_index("interview_id", drop=False)
	interview_level_df["provider_indifference_index"] = compute_provider_indifference_index(interview_level_df[["channel_hits","price_efficiency_hits","provider_brand_hits"]])

	segments = aggregate_segment_metrics(interview_level_df)
	quotes = select_representative_quotes(responses_df, interview_level_df, keywords=kw)

	notes: List[str] = []
	if interview_level_df["mean_impact_score"].isna().all():
		notes.append("Impact score missing for all interviews; mean_impact_score is null.")
	if len(interview_level_df) < 5:
		notes.append("Few interviews; interpret segment shares with caution.")
	if not any(len(v) for v in quotes.values()):
		notes.append("No representative quotes found under constraints.")

	payload = {
		"client_id": client_id,
		"generated_at": datetime.now(timezone.utc).isoformat(),
		"segments": segments,
		"interviews": interview_level_df[[
			"interview_id","company","company_size","known_channel","assigned_channel",
			"provider_indifference_index","price_efficiency_salience","mean_impact_score"
		]].to_dict(orient="records"),
		"quotes": quotes,
		"notes": "; ".join(notes) if notes else "",
	}
	return payload


def generate_narrative_llm(metrics_json: Dict[str, Any], llm: Any = None, max_words: int = 250) -> Optional[str]:
	if llm is None:
		return None
	system = (
		"You are generating a concise executive narrative (≤{max_words} words). "
		"Only use information given in the JSON. DO NOT invent any numbers, quotes, IDs, or companies."
	).format(max_words=max_words)
	user = (
		"Rewrite the following metrics JSON into a cohesive, neutral-toned narrative. "
		"Focus on segments, drivers, sentiment, and the role of provider brands vs integration/efficiency. "
		"Do not list raw JSON; write 2–4 short paragraphs. Do not add any data not present.\n\n"
		f"{json.dumps(metrics_json, ensure_ascii=False)}"
	)
	try:
		if hasattr(llm, "complete"):
			text = llm.complete(system=system, user=user)
		elif hasattr(llm, "invoke"):
			text = llm.invoke({"system": system, "user": user})
		else:
			return None
		words = str(text).split()
		if len(words) > max_words:
			text = " ".join(words[:max_words])
		return str(text)
	except Exception:
		return None


def to_overview_table(metrics_json: Dict[str, Any]) -> pd.DataFrame:
	rows = []
	segs = metrics_json.get("segments", {})
	for seg_id, seg in segs.items():
		rows.append({
			"segment": seg_id,
			"interview_count": seg.get("interview_count"),
			"share_of_interviews": seg.get("share_of_interviews"),
			"mean_impact_score": seg.get("mean_impact_score"),
			"price_efficiency_rate": seg.get("price_efficiency_rate"),
			"provider_indifference_index_mean": seg.get("provider_indifference_index_mean"),
			"sent_positive": seg.get("sentiment_mix", {}).get("positive"),
			"sent_negative": seg.get("sentiment_mix", {}).get("negative"),
			"sent_neutral": seg.get("sentiment_mix", {}).get("neutral"),
		})
	return pd.DataFrame(rows) 