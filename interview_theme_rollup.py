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


def rollup_interview_themes(db: SupabaseDatabase, client_id: str, threshold: float = 0.78) -> RollupResult:
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
		return RollupResult(interview_themes=it_df, clusters=pd.DataFrame(), members=pd.DataFrame())

	# Compute embeddings
	mgr = EmbeddingManager()
	embs = mgr.get_embeddings_batch(it_df['theme_statement'].astype(str).tolist(), batch_size=50)
	assignments = _cluster_by_threshold(embs, threshold)
	it_df = it_df.assign(cluster_id=assignments)

	# Build clusters table
	grp = it_df.groupby('cluster_id')
	clusters = grp.agg(
		members_count=('theme_statement', 'count'),
		canonical_theme=('theme_statement', lambda s: sorted(s, key=lambda x: (-len(x), x))[0]),
		interviews_covered=('interview_id', lambda s: s.nunique())
	).reset_index()
	clusters['share_of_interviews'] = clusters['interviews_covered'] / max(1, it_df['interview_id'].nunique())
	clusters = clusters.sort_values(by=['interviews_covered','members_count'], ascending=[False, False]).reset_index(drop=True)

	members = it_df.rename(columns={'theme_statement': 'member_theme'})[['cluster_id','interview_id','member_theme']]
	return RollupResult(interview_themes=it_df[['interview_id','theme_statement']], clusters=clusters, members=members) 