#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
import pandas as pd

from embedding_utils import EmbeddingManager
from supabase_database import SupabaseDatabase


@dataclass
class RollupResult:
	interview_themes: pd.DataFrame
	clusters: pd.DataFrame
	members: pd.DataFrame
	unclustered: pd.DataFrame  # themes that did not meet cluster threshold or size


def _cluster_by_threshold(embeddings: List[List[float]], threshold: float) -> List[int]:
	"""Greedy clustering: assign each item to first sufficiently similar prior item; otherwise new cluster."""
	assignments: List[int] = [-1] * len(embeddings)
	centroids: List[List[float]] = []
	mgr = EmbeddingManager()
	for i, emb in enumerate(embeddings):
		if emb is None:
			assignments[i] = -1
			continue
		# Try to assign to an existing centroid
		best_idx = -1
		best_sim = -1.0
		for c_idx, c in enumerate(centroids):
			s = mgr.calculate_cosine_similarity(emb, c)
			if s > best_sim:
				best_sim = s
				best_idx = c_idx
		if best_sim >= threshold and best_idx >= 0:
			assignments[i] = best_idx
			# Update centroid (simple average)
			c = centroids[best_idx]
			centroids[best_idx] = [(a + b) / 2.0 for a, b in zip(c, emb)]
		else:
			# New cluster
			centroids.append(emb)
			assignments[i] = len(centroids) - 1
	return assignments


def rollup_interview_themes(db: SupabaseDatabase, client_id: str, threshold: float = 0.88, min_cluster_size: int = 2) -> RollupResult:
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

	# Compute embeddings
	mgr = EmbeddingManager()
	texts = it_df['theme_statement'].astype(str).tolist()
	embs = mgr.get_embeddings_batch(texts, batch_size=50)
	assignments = _cluster_by_threshold(embs, threshold)
	it_df = it_df.assign(cluster_id=assignments)

	# Build clusters table with centroid-based canonical label
	grp = it_df.groupby('cluster_id')
	clusters_rows = []
	members_rows = []
	eligible_cluster_ids = set()
	for cid, g in grp:
		if cid < 0:
			continue
		idxs = g.index.tolist()
		g_texts = g['theme_statement'].astype(str).tolist()
		g_embs = [embs[i] for i in idxs]
		# Skip clusters smaller than min size
		if len(g_texts) < max(1, min_cluster_size):
			continue
		# Compute centroid
		valid_embs = [e for e in g_embs if e is not None]
		if valid_embs:
			centroid = [sum(vals) / len(valid_embs) for vals in zip(*valid_embs)]
			# Pick text with highest similarity to centroid
			best_i = 0
			best_sim = -1.0
			for i_local, e in enumerate(g_embs):
				if e is None:
					continue
				s = mgr.calculate_cosine_similarity(e, centroid)
				if s > best_sim:
					best_sim = s
					best_i = i_local
			canonical = g_texts[best_i]
		else:
			canonical = sorted(g_texts, key=lambda x: (-len(x), x))[0]

		clusters_rows.append({
			'cluster_id': cid,
			'members_count': len(g_texts),
			'canonical_theme': canonical,
			'interviews_covered': g['interview_id'].nunique(),
		})
		eligible_cluster_ids.add(cid)
		for iv, t in zip(g['interview_id'].tolist(), g_texts):
			members_rows.append({'cluster_id': cid, 'interview_id': iv, 'member_theme': t})

	clusters = pd.DataFrame(clusters_rows)
	if not clusters.empty:
		clusters['share_of_interviews'] = clusters['interviews_covered'] / max(1, it_df['interview_id'].nunique())
		clusters = clusters.sort_values(by=['interviews_covered','members_count'], ascending=[False, False]).reset_index(drop=True)
	members = pd.DataFrame(members_rows)

	# Unclustered = items with cluster_id == -1 or in clusters smaller than min size
	mask_un = ~it_df['cluster_id'].isin(list(eligible_cluster_ids))
	unclustered = it_df.loc[mask_un, ['interview_id','theme_statement']].reset_index(drop=True)

	return RollupResult(interview_themes=it_df[['interview_id','theme_statement']], clusters=clusters, members=members, unclustered=unclustered) 