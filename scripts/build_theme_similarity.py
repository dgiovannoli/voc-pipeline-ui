#!/usr/bin/env python3
import sys
from pathlib import Path
import argparse
import pandas as pd
import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1]))
from supabase_database import SupabaseDatabase
from embedding_utils import EmbeddingManager

GENERIC = {
    'need','needs','fast','quick','easy','good','great','nice','help','use','work','really','very','best','better','more','less','much','many'
}

# Lightweight domain facets
FACETS = {
    'Integration': {
        'api','webhook','integration','integrate','oms','order management','shopify','bigcommerce','woocommerce','data transfer','sync','mapping','schema'
    },
    'Price': {
        'price','pricing','cost','fees','fee','rates','rate','surcharge','discount','savings','saver','cheap','expense'
    },
    'Reliability': {
        'uptime','latency','sla','reliability','downtime','outage','incident','status','throttle','throttling','timeout','retry'
    },
    'Support': {
        'support','account manager','cs','customer success','onboarding','documentation','docs','examples','sdk','sample'
    },
    'Coverage': {
        'carrier','carriers','coverage','zone','domestic','international','region','service level','options','label'
    },
    'Feature': {
        'feature','returns','return label','refund','batch','manifest','pickup','address validation','customs'
    },
    'Competition': {
        'competitor','competitors','vs','versus','switch','switched','shipstation','easypost','pitney','stamps','shippo','xps','endicia'
    }
}

FACET_VOCAB = set().union(*FACETS.values())


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
    trigrams = [f"{parts[i]} {parts[i+1]} {parts[i+2]}" for i in range(len(parts)-2)] if len(parts) > 2 else []
    return set(parts + bigrams + trigrams)


def detect_facets(text: str) -> set:
    toks = content_tokens(text)
    matched = set()
    for facet, kws in FACETS.items():
        if any(k in toks for k in kws):
            matched.add(facet)
    if not matched:
        # fallback: broad API/integration keyword
        if any(k in toks for k in ('api','integration','webhook')):
            matched.add('Integration')
    return matched or {'Other'}


def assign_primary_facet(text: str) -> str:
    facets = detect_facets(text)
    # Pick a deterministic primary facet
    for preferred in ['Integration','Price','Reliability','Support','Coverage','Feature','Competition']:
        if preferred in facets:
            return preferred
    return sorted(facets).pop()


def build_pairs(df: pd.DataFrame) -> pd.DataFrame:
    # Produce cross product by subject and facet; avoid self-pairs
    groups = []
    for (subj, facet), g in df.groupby(['subject','facet']):
        if len(g) < 2:
            continue
        g = g.reset_index(drop=True)
        left = g.assign(_key=1)
        right = g.assign(_key=1)
        pairs = left.merge(right, on=['_key','subject','facet'], suffixes=('_a','_b'))
        pairs = pairs[pairs['theme_id_a'] != pairs['theme_id_b']]
        groups.append(pairs.drop(columns=['_key']))
    if not groups:
        return pd.DataFrame()
    out = pd.concat(groups, ignore_index=True)
    # Dedupe unordered pairs early
    out['pair_key'] = out.apply(lambda r: tuple(sorted([r['theme_id_a'], r['theme_id_b']])), axis=1)
    out = out.drop_duplicates(subset=['pair_key'])
    return out.drop(columns=['pair_key'])


def score_pairs(pairs: pd.DataFrame, mgr: EmbeddingManager, min_cos: float = 0.82, min_jacc: float = 0.30) -> pd.DataFrame:
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
    domain_overlap = []
    for ta, tb in zip(tok_a, tok_b):
        if not ta or not tb:
            jacc.append(0.0)
            domain_overlap.append(0)
            continue
        inter = len(ta & tb)
        union = len(ta | tb)
        jacc.append((inter/union) if union else 0.0)
        domain_overlap.append(len((ta & tb) & FACET_VOCAB))
    pairs['jaccard'] = jacc
    pairs['domain_overlap'] = domain_overlap
    # Hard precision gates
    gated = pairs[(pairs['cosine'] >= min_cos) & (pairs['jaccard'] >= min_jacc) & (pairs['domain_overlap'] >= 1)]
    if gated.empty:
        return gated
    # Composite
    gated['score'] = 0.6 * gated['cosine'] + 0.25 * gated['jaccard'] + 0.15 * (gated['domain_overlap'] > 0).astype(float)
    # Keep top-k per anchor to avoid over-linking
    gated = gated.sort_values(['theme_id_a','score'], ascending=[True, False])
    gated['rank'] = gated.groupby('theme_id_a').cumcount() + 1
    gated = gated[gated['rank'] <= 5].drop(columns=['rank'])
    return gated


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--client', required=True)
    ap.add_argument('--min-score', type=float, default=0.78)
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

    # Assign facets
    all_df['facet'] = all_df['theme_statement'].astype(str).apply(assign_primary_facet)

    pairs = build_pairs(all_df)
    if pairs.empty:
        print('No pairs to score')
        return 0

    pairs = score_pairs(pairs, mgr, min_cos=0.82, min_jacc=0.30)
    # Final score threshold
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
                'jaccard': float(row['jaccard']),
                'facet': row.get('facet'),
                'domain_overlap': int(row.get('domain_overlap', 0))
            }
        })
    count = db.upsert_theme_similarity(rows)
    print(f"Upserted {count} similarity rows for {args.client}")
    return 0

if __name__ == '__main__':
    sys.exit(main()) 