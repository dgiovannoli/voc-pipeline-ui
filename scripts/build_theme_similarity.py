#!/usr/bin/env python3
import sys
from pathlib import Path
import argparse
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from supabase_database import SupabaseDatabase
from embedding_utils import EmbeddingManager

GENERIC = { 'need','needs','fast','quick','easy','good','great','nice','help','use','work' }

def normalize(text: str) -> str:
    import re
    s = (text or '').lower()
    s = re.sub(r'https?://\S+', ' ', s)
    s = re.sub(r'[^a-z ]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def content_tokens(text: str) -> set:
    s = normalize(text)
    parts = [p for p in s.split() if p and p not in GENERIC]
    bigrams = [f"{parts[i]} {parts[i+1]}" for i in range(len(parts)-1)] if len(parts) > 1 else []
    return set(parts + bigrams)


def build_pairs(df: pd.DataFrame) -> pd.DataFrame:
    # Produce cross product by subject; avoid self-pairs
    groups = []
    for subj, g in df.groupby('subject'):
        if len(g) < 2:
            continue
        g = g.reset_index(drop=True)
        left = g.assign(_key=1)
        right = g.assign(_key=1)
        pairs = left.merge(right, on=['_key','subject'], suffixes=('_a','_b'))
        pairs = pairs[pairs['theme_id_a'] != pairs['theme_id_b']]
        groups.append(pairs.drop(columns=['_key']))
    if not groups:
        return pd.DataFrame()
    out = pd.concat(groups, ignore_index=True)
    return out


def score_pairs(pairs: pd.DataFrame, mgr: EmbeddingManager) -> pd.DataFrame:
    if pairs.empty:
        return pairs
    texts_a = pairs['theme_statement_a'].astype(str).tolist()
    texts_b = pairs['theme_statement_b'].astype(str).tolist()
    embs_a = mgr.get_embeddings_batch(texts_a, batch_size=100)
    embs_b = mgr.get_embeddings_batch(texts_b, batch_size=100)
    cos = []
    for ea, eb in zip(embs_a, embs_b):
        if ea is None or eb is None:
            cos.append(0.0)
        else:
            cos.append(mgr.calculate_cosine_similarity(ea, eb))
    pairs['cosine'] = cos
    # token jaccard
    tok_a = [content_tokens(t) for t in texts_a]
    tok_b = [content_tokens(t) for t in texts_b]
    jacc = []
    for ta, tb in zip(tok_a, tok_b):
        if not ta or not tb:
            jacc.append(0.0)
            continue
        inter = len(ta & tb)
        union = len(ta | tb)
        jacc.append((inter/union) if union else 0.0)
    pairs['jaccard'] = jacc
    # Composite
    pairs['score'] = 0.7 * pairs['cosine'] + 0.3 * pairs['jaccard']
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--client', required=True)
    ap.add_argument('--min-score', type=float, default=0.7)
    args = ap.parse_args()

    db = SupabaseDatabase()
    mgr = EmbeddingManager()

    # Gather themes across sources
    r = db.fetch_research_themes_all(args.client)
    i = db.fetch_interview_level_themes(args.client)
    # Normalize fields
    r = r.rename(columns={'theme_id':'theme_id','theme_statement':'theme_statement','harmonized_subject':'subject'})
    r = r[['theme_id','theme_statement','subject']].dropna()
    r['source'] = 'research'
    i = i.rename(columns={'theme_statement':'theme_statement'})
    i['subject'] = i.get('subject', pd.Series(['Interview'] * len(i)))
    i = i[['interview_id','theme_statement','subject']].dropna()
    i['theme_id'] = i['interview_id'].astype(str) + '::IT'
    i['source'] = 'interview'
    all_df = pd.concat([r[['theme_id','theme_statement','subject','source']], i[['theme_id','theme_statement','subject','source']]], ignore_index=True)
    all_df = all_df.dropna(subset=['theme_id','theme_statement','subject'])

    if all_df.empty:
        print('No themes found')
        return 0

    pairs = build_pairs(all_df)
    if pairs.empty:
        print('No pairs to score')
        return 0

    pairs = score_pairs(pairs, mgr)
    pairs = pairs[pairs['score'] >= args.min_score]

    rows = []
    for _, row in pairs.iterrows():
        rows.append({
            'client_id': args.client,
            'theme_id': row['theme_id_a'],
            'other_theme_id': row['theme_id_b'],
            'subject': row['subject'],
            'score': float(row['score']),
            'features_json': {
                'cosine': float(row['cosine']),
                'jaccard': float(row['jaccard'])
            }
        })
    count = db.upsert_theme_similarity(rows)
    print(f"Upserted {count} similarity rows for {args.client}")
    return 0

if __name__ == '__main__':
    sys.exit(main()) 