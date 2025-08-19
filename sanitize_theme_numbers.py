#!/usr/bin/env python3

"""
Sanitize theme headlines to remove unsupported numeric claims.
- For each theme, extract numeric tokens from theme_statement
- If a token does not appear in any supporting quote (exact string match, normalized), replace with a safe qualitative phrase
- Update research_themes.theme_statement

Safe replacements:
- Percentages (e.g., 30%) → "significant"
- Currency/amounts (e.g., $5,000, 50k) → "material"
- Plain numbers (e.g., 12) → "meaningful"

This pass is deterministic and avoids LLM hallucinations.
"""

import os
import re
import sys
import json
import logging
from typing import List, Dict, Any, Set

import pandas as pd

# Ensure project imports work
sys.path.append(os.path.dirname(__file__))
from official_scripts.database.supabase_database import SupabaseDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NUM_PATTERNS = [
    re.compile(r"\$\s?\d[\d,]*\.?\d*"),   # $5,000 or $5000
    re.compile(r"\b\d{1,3}(?:\.\d+)?%\b"), # 30%
    re.compile(r"\b\d+(?:\.\d+)?k\b", re.IGNORECASE), # 50k
    re.compile(r"\b\d[\d,]*\.?\d*\b"),    # plain numbers
]


def extract_numeric_tokens(text: str) -> List[str]:
    tokens: List[str] = []
    if not text:
        return tokens
    for pat in NUM_PATTERNS:
        tokens.extend(m.group(0) for m in pat.finditer(text))
    # Deduplicate preserving order
    seen: Set[str] = set()
    uniq = []
    for t in tokens:
        if t not in seen:
            uniq.append(t)
            seen.add(t)
    return uniq


def normalize(s: str) -> str:
    return s.replace(",", "").strip().lower()


def build_allowed_token_set(quotes: List[str]) -> Set[str]:
    allowed: Set[str] = set()
    qnorm = [normalize(q) for q in quotes if q]
    # Collect all numeric substrings from quotes and normalized variants (e.g., 50000 for 50k)
    for q in qnorm:
        for pat in NUM_PATTERNS:
            for m in pat.finditer(q):
                tok = m.group(0)
                allowed.add(tok)
                # Expand k-suffix to zeros
                if tok.endswith('k'):
                    try:
                        num = float(tok[:-1])
                        allowed.add(str(int(num * 1000)))
                    except Exception:
                        pass
    return allowed


def replace_token(headline: str, token: str) -> str:
    repl = "meaningful"
    t = token.strip()
    if '%' in t:
        repl = "significant"
    elif t.lower().endswith('k') or t.startswith('$'):
        repl = "material"
    # Use regex escape for literal replacement
    return re.sub(re.escape(token), repl, headline)


def sanitize_headlines(client_id: str) -> Dict[str, Any]:
    db = SupabaseDatabase()

    themes = db.supabase.table('research_themes').select(
        'theme_id,theme_statement,supporting_quotes'
    ).eq('client_id', client_id).execute().data or []

    quotes_df = pd.DataFrame(
        db.supabase.table('stage1_data_responses').select(
            'response_id,verbatim_response'
        ).eq('client_id', client_id).execute().data or []
    )

    updated = 0
    audited: List[Dict[str, Any]] = []

    for t in themes:
        theme_id = t.get('theme_id')
        headline = t.get('theme_statement') or ''
        ids = t.get('supporting_quotes') or []
        if not headline or not ids:
            continue

        tokens = extract_numeric_tokens(headline)
        if not tokens:
            continue

        sel = quotes_df[quotes_df['response_id'].isin(ids)]
        allowed = build_allowed_token_set(sel['verbatim_response'].tolist())

        new_headline = headline
        unsupported = []
        for tok in tokens:
            if normalize(tok) not in {normalize(a) for a in allowed}:
                new_headline = replace_token(new_headline, tok)
                unsupported.append(tok)

        if new_headline != headline:
            db.supabase.table('research_themes').update({
                'theme_statement': new_headline
            }).eq('theme_id', theme_id).execute()
            updated += 1
        audited.append({
            'theme_id': theme_id,
            'original': headline,
            'sanitized': new_headline,
            'unsupported_tokens': unsupported
        })

    return {"updated": updated, "audited": audited[:10]}  # return a sample


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--client', required=True)
    args = parser.parse_args()

    result = sanitize_headlines(args.client)
    print(json.dumps(result, indent=2)) 