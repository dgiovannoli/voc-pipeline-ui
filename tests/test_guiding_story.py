import pandas as pd

from guiding_story_analyzer import (
	assign_channel_for_interview,
	compute_interview_signals,
	compute_provider_indifference_index,
	aggregate_segment_metrics,
	select_representative_quotes,
	to_overview_table,
)


def _mk_responses():
	rows = [
		{"response_id": 1, "interview_id": "A", "company": "Alpha", "interviewee_name": "Ann",
		 "question": "How did you integrate?", "verbatim_response": "We used the API and webhook. Total cost mattered.",
		 "sentiment": "positive", "impact_score": 0.9, "harmonized_subject": "integration"},
		{"response_id": 2, "interview_id": "A", "company": "Alpha", "interviewee_name": "Ann",
		 "question": "Any brands?", "verbatim_response": "We compared ShipStation with options.", "sentiment": "neutral",
		 "impact_score": 0.7, "harmonized_subject": "vendor choice"},
		{"response_id": 3, "interview_id": "B", "company": "Beta", "interviewee_name": "Bob",
		 "question": "Ops flow?", "verbatim_response": "Our 3PL and WMS handle it; reliability and fees are key.",
		 "sentiment": "negative", "impact_score": 0.8, "harmonized_subject": "operations"},
		{"response_id": 4, "interview_id": "B", "company": "Beta", "interviewee_name": "Bob",
		 "question": "Brands?", "verbatim_response": "We rarely care about brands.", "sentiment": "neutral",
		 "impact_score": 0.6, "harmonized_subject": "priorities"},
	]
	return pd.DataFrame(rows)


def _mk_meta():
	rows = [
		{"interview_id": "A", "company": "Alpha", "company_size": "small", "known_channel": None},
		{"interview_id": "B", "company": "Beta", "company_size": "large", "known_channel": "via_3pl_wms"},
	]
	return pd.DataFrame(rows)


def test_assign_channel_keyword_inference():
	responses = _mk_responses()
	meta = _mk_meta()
	rowA = meta[meta["interview_id"] == "A"].iloc[0]
	gA = responses[responses["interview_id"] == "A"]
	segA = assign_channel_for_interview(gA, rowA, None)
	assert segA == "direct_api"

	rowB = meta[meta["interview_id"] == "B"].iloc[0]
	gB = responses[responses["interview_id"] == "B"]
	segB = assign_channel_for_interview(gB, rowB, None)
	assert segB == "via_3pl_wms"


def test_provider_indifference_monotonicity():
	df2 = pd.DataFrame({
		"channel_hits": [1, 2],
		"price_efficiency_hits": [1, 1],
		"provider_brand_hits": [2, 2],
	})
	idx2 = compute_provider_indifference_index(df2)
	assert idx2.iloc[1] > idx2.iloc[0]

	df3 = pd.DataFrame({
		"channel_hits": [2, 2],
		"price_efficiency_hits": [1, 1],
		"provider_brand_hits": [1, 5],
	})
	idx3 = compute_provider_indifference_index(df3)
	assert idx3.iloc[1] < idx3.iloc[0]


def test_aggregate_segment_metrics_interview_weighted():
	responses = _mk_responses()
	meta = _mk_meta()
	rows = []
	for iid, g in responses.groupby("interview_id"):
		md = meta[meta["interview_id"] == iid].iloc[0]
		signals = compute_interview_signals(g, None)
		seg = assign_channel_for_interview(g, md, None)
		rows.append({"interview_id": iid, "company": md["company"], "assigned_channel": seg, **signals})
	ildf = pd.DataFrame(rows)
	ildf["provider_indifference_index"] = compute_provider_indifference_index(ildf[["channel_hits","price_efficiency_hits","provider_brand_hits"]])

	segments = aggregate_segment_metrics(ildf)
	assert set(segments.keys()) == {"direct_api","via_3pl_wms"}
	total_share = sum(seg["share_of_interviews"] for seg in segments.values())
	assert abs(total_share - 1.0) < 1e-6
	for seg in segments.values():
		assert isinstance(seg["top_subjects"], list)


def test_quote_selection_constraints():
	responses = _mk_responses()
	meta = _mk_meta()
	rows = []
	for iid, g in responses.groupby("interview_id"):
		md = meta[meta["interview_id"] == iid].iloc[0]
		signals = compute_interview_signals(g, None)
		seg = assign_channel_for_interview(g, md, None)
		rows.append({"interview_id": iid, "company": md["company"], "assigned_channel": seg, **signals})
	ildf = pd.DataFrame(rows)
	quotes = select_representative_quotes(responses, ildf, per_segment=2, max_chars=50)
	for seg, qlist in quotes.items():
		for q in qlist:
			assert len(q["excerpt"]) <= 51
			assert q["interview_id"] in set(ildf["interview_id"]) 
			assert isinstance(q["response_id"], (int, str))


def test_to_overview_table_smoke():
	payload = {
		"segments": {
			"direct_api": {"interview_count": 3, "share_of_interviews": 0.6, "mean_impact_score": 0.8,
						   "price_efficiency_rate": 0.67, "provider_indifference_index_mean": 0.7,
						   "sentiment_mix": {"positive": 0.5, "negative": 0.2, "neutral": 0.3}},
			"via_3pl_wms": {"interview_count": 2, "share_of_interviews": 0.4, "mean_impact_score": 0.75,
						   "price_efficiency_rate": 0.5, "provider_indifference_index_mean": 0.6,
						   "sentiment_mix": {"positive": 0.4, "negative": 0.3, "neutral": 0.3}},
		}
	}
	df = to_overview_table(payload)
	assert set(df.columns) >= {"segment","interview_count","share_of_interviews"}
	assert len(df) == 2 