#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
import pandas as pd
import re

from embedding_utils import EmbeddingManager
from supabase_database import SupabaseDatabase


@dataclass
class RollupResult:
	interview_themes: pd.DataFrame
	clusters: pd.DataFrame
	members: pd.DataFrame
	unclustered: pd.DataFrame  # themes that did not meet cluster threshold or size


_STOPWORDS = {
	'and','or','but','the','a','an','to','of','for','in','on','at','by','with','from','as','is','are','was','were','be','been','being','that','this','it','they','we','you','i','their','our','your','his','her','its','not','no','do','does','did','have','has','had'
}


def _normalize_text(text: str) -> str:
	"""Normalize theme text to reduce over-specificity while preserving semantics.
	Lowercase, mask urls/emails/numbers/dates, map brand/provider tokens to placeholders,
	simplify common synonyms (api/webhook -> api, 3pl/wms/warehouse -> 3pl),
	and strip excessive punctuation.
	"""
	if not text:
		return ""
	s = str(text).lower()
	# URLs/emails
	s = re.sub(r'https?://\S+', ' [url] ', s)
	s = re.sub(r'\b[\w\.-]+@[\w\.-]+\.[a-z]{2,}\b', ' [email] ', s)
	# Numbers/dates
	s = re.sub(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', ' [date] ', s)
	s = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', ' [date] ', s)
	s = re.sub(r'\b\d+[\d,\.]*\b', ' [num] ', s)
	# Brands/providers to [brand]
	brands = [
		'shipstation','easypost','pitney bowes','stamps','shippo','xps','endicia','usps','ups','fedex','dhl'
	]
	for b in brands:
		s = re.sub(rf'\b{re.escape(b)}\b', ' [brand] ', s)
	# Channel keywords
	s = re.sub(r'\bwebhook(s)?\b', ' api ', s)
	s = re.sub(r'\bportal\b', ' api ', s)
	s = re.sub(r'\bapi(s)?\b', ' api ', s)
	s = re.sub(r'\b3pl(s)?\b', ' 3pl ', s)
	s = re.sub(r'\bwms\b', ' 3pl ', s)
	s = re.sub(r'\bwarehouse management\b', ' 3pl ', s)
	# Strip extra punctuation/whitespace
	s = re.sub(r'[^a-z\[\] ]+', ' ', s)
	s = re.sub(r'\s+', ' ', s).strip()
	return s


def _tokens(s: str) -> set:
	parts = [p for p in re.split(r'\s+', s) if p and p not in _STOPWORDS]
	return set(parts)


def _jaccard(a: set, b: set) -> float:
	if not a or not b:
		return 0.0
	inter = len(a & b)
	union = len(a | b)
	return inter / union if union else 0.0


def _cluster_by_threshold(embeddings: List[List[float]], tokens: List[set], threshold: float, min_token_overlap: float) -> List[int]:
	"""Greedy clustering with token-overlap gate to avoid over-merging."""
	assignments: List[int] = [-1] * len(embeddings)
	centroids: List[List[float]] = []
	centroid_tokens: List[set] = []
	mgr = EmbeddingManager()
	for i, emb in enumerate(embeddings):
		if emb is None:
			assignments[i] = -1
			continue
		best_idx = -1
		best_sim = -1.0
		for c_idx, c in enumerate(centroids):
			cos = mgr.calculate_cosine_similarity(emb, c)
			jac = _jaccard(tokens[i], centroid_tokens[c_idx])
			if cos >= threshold and jac >= min_token_overlap and cos > best_sim:
				best_sim = cos
				best_idx = c_idx
		if best_idx >= 0:
			assignments[i] = best_idx
			# Update centroid (simple average) and centroid tokens (union)
			c = centroids[best_idx]
			centroids[best_idx] = [(a + b) / 2.0 for a, b in zip(c, emb)]
			centroid_tokens[best_idx] = centroid_tokens[best_idx] | tokens[i]
		else:
			# New cluster
			centroids.append(emb)
			centroid_tokens.append(set(tokens[i]))
			assignments[i] = len(centroids) - 1
	return assignments


def rollup_interview_themes(db: SupabaseDatabase, client_id: str, threshold: float = 0.85, min_cluster_size: int = 2, normalize: bool = True, min_token_overlap: float = 0.08, min_interviews_covered: int = 2, max_clusters: int = 15) -> RollupResult:
	# Pull interview-level themes
	try:
		res = db.supabase.table('interview_level_themes').select(
			'interview_id,theme_statement'
		).eq('client_id', client_id).execute()
		rows = res.data or []
	except Exception:
		rows = []
	it_df = pd.DataFrame(rows)
	if it_df.empty:
		return RollupResult(interview_themes=it_df, clusters=pd.DataFrame(), members=pd.DataFrame(), unclustered=pd.DataFrame())

	# Compute embeddings on normalized text, preserve originals
	texts_original = it_df['theme_statement'].astype(str).tolist()
	texts_norm = [_normalize_text(t) for t in texts_original] if normalize else texts_original
	mgr = EmbeddingManager()
	embs = mgr.get_embeddings_batch(texts_norm, batch_size=50)
	toks = [_tokens(t) for t in texts_norm]
	assignments = _cluster_by_threshold(embs, toks, threshold, min_token_overlap)
	it_df = it_df.assign(cluster_id=assignments)

	# Build clusters table with centroid-based canonical label (original text)
	grp = it_df.groupby('cluster_id')
	clusters_rows = []
	members_rows = []
	eligible_cluster_ids = set()
	for cid, g in grp:
		if cid < 0:
			continue
		idxs = g.index.tolist()
		g_texts_orig = [texts_original[i] for i in idxs]
		g_embs = [embs[i] for i in idxs]
		# Skip clusters smaller than min size
		if len(g_texts_orig) < max(1, min_cluster_size):
			continue
		# Compute centroid
		valid_embs = [e for e in g_embs if e is not None]
		if valid_embs:
			centroid = [sum(vals) / len(valid_embs) for vals in zip(*valid_embs)]
			# Pick ORIGINAL text whose normalized embedding is closest to centroid
			best_i = 0
			best_sim = -1.0
			for i_local, e in enumerate(g_embs):
				if e is None:
					continue
				s = mgr.calculate_cosine_similarity(e, centroid)
				if s > best_sim:
					best_sim = s
					best_i = i_local
			canonical = g_texts_orig[best_i]
		else:
			canonical = sorted(g_texts_orig, key=lambda x: (-len(x), x))[0]

		clusters_rows.append({
			'cluster_id': cid,
			'members_count': len(g_texts_orig),
			'canonical_theme': canonical,
			'interviews_covered': g['interview_id'].nunique(),
		})
		eligible_cluster_ids.add(cid)
		for iv, t in zip(g['interview_id'].tolist(), g_texts_orig):
			members_rows.append({'cluster_id': cid, 'interview_id': iv, 'member_theme': t})

	clusters = pd.DataFrame(clusters_rows)
	members = pd.DataFrame(members_rows)

	# Filter by interviews covered; demote to unclustered
	unclustered = pd.DataFrame()
	if not clusters.empty:
		clusters['share_of_interviews'] = clusters['interviews_covered'] / max(1, it_df['interview_id'].nunique())
		# Separate weak clusters
		weak_ids = set(clusters.loc[clusters['interviews_covered'] < max(1, min_interviews_covered), 'cluster_id'].tolist())
		if not members.empty and weak_ids:
			weak_members = members[members['cluster_id'].isin(weak_ids)][['interview_id','member_theme']].rename(columns={'member_theme':'theme_statement'})
			unclustered = pd.concat([unclustered, weak_members], ignore_index=True)
		clusters = clusters[~clusters['cluster_id'].isin(weak_ids)].reset_index(drop=True)
		members = members[~members['cluster_id'].isin(weak_ids)].reset_index(drop=True)

	# Cap max clusters; demote the rest to unclustered by coverage then size
	if not clusters.empty and len(clusters) > max_clusters:
		clusters = clusters.sort_values(by=['interviews_covered','members_count'], ascending=[False, False]).reset_index(drop=True)
		keep_ids = set(clusters.head(max_clusters)['cluster_id'].tolist())
		drop_ids = set(clusters['cluster_id'].tolist()) - keep_ids
		if not members.empty and drop_ids:
			drop_members = members[members['cluster_id'].isin(drop_ids)][['interview_id','member_theme']].rename(columns={'member_theme':'theme_statement'})
			unclustered = pd.concat([unclustered, drop_members], ignore_index=True)
		clusters = clusters[clusters['cluster_id'].isin(keep_ids)].reset_index(drop=True)
		members = members[members['cluster_id'].isin(keep_ids)].reset_index(drop=True)

	return RollupResult(interview_themes=it_df[['interview_id','theme_statement']], clusters=clusters, members=members, unclustered=unclustered.reset_index(drop=True)) 