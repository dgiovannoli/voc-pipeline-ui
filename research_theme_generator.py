#!/usr/bin/env python3
"""
Research-First Theme Generator
- Produces per-question theme clusters to be consumed by Stage 4-style statement generation
- Enforces guardrails: >=2 unique companies AND >=2 quotes, with at most 1 quote per company
- Optionally splits into strength/weakness/mixed cohorts per question for up to 3 themes
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
import pandas as pd


def _select_one_quote_per_company(quotes: pd.DataFrame, company_col: str) -> pd.DataFrame:
    """Keep at most one (highest impact) quote per company to avoid overweighting a single firm."""
    if company_col not in quotes.columns or quotes.empty:
        return quotes
    # Sort by impact desc then take first per company
    sorted_df = quotes.sort_values(by=['impact_score'], ascending=False)
    deduped = sorted_df.drop_duplicates(subset=[company_col], keep='first')
    return deduped


def generate_research_clusters_for_question(
    question_text: str,
    quotes_for_question: pd.DataFrame,
    min_companies: int,
    min_quotes: int,
    min_avg_impact: float,
) -> List[Dict[str, Any]]:
    """
    Build research-origin theme clusters for a single guide question.
    Returns a list of cluster dicts compatible with downstream quality gates and statement generation.
    """
    clusters: List[Dict[str, Any]] = []
    if quotes_for_question is None or quotes_for_question.empty:
        return clusters

    # Determine company column present
    company_col = 'company' if 'company' in quotes_for_question.columns else (
        'company_name' if 'company_name' in quotes_for_question.columns else None
    )

    # Deduplicate to at most 1 quote per company
    quotes_1pc = _select_one_quote_per_company(quotes_for_question, company_col) if company_col else quotes_for_question

    # Guardrails
    unique_companies = quotes_1pc[company_col].nunique() if company_col else len(quotes_1pc)
    effective_quotes = len(quotes_1pc)
    avg_impact = float(quotes_1pc['impact_score'].mean()) if 'impact_score' in quotes_1pc.columns and not quotes_1pc.empty else 0.0

    if unique_companies < min_companies or effective_quotes < min_quotes or avg_impact < min_avg_impact:
        # Too thin to form a research theme
        return clusters

    # Split by sentiment for up to 3 coherent cohorts (strength/weakness/mixed)
    def make_cluster(subset: pd.DataFrame, theme_type: str) -> Optional[Dict[str, Any]]:
        if subset is None or subset.empty:
            return None
        # Enforce 1/company inside subset as well
        sub_1pc = _select_one_quote_per_company(subset, company_col) if company_col else subset
        uniq_companies = sub_1pc[company_col].nunique() if company_col else len(sub_1pc)
        if uniq_companies < min_companies or len(sub_1pc) < min_quotes:
            return None
        return {
            "theme_type": theme_type,
            "harmonized_subject": (subset['harmonized_subject'].mode().iloc[0]
                                    if 'harmonized_subject' in subset.columns and not subset['harmonized_subject'].isna().all()
                                    else "Research-Aligned"),
            "quotes": sub_1pc,
            "pattern_summary": f"{theme_type.title()} theme seeded by research question",
            "theme_origin": "research",
            "research_primary_question_seed": question_text,
        }

    pos = quotes_1pc[quotes_1pc['sentiment'] == 'positive'] if 'sentiment' in quotes_1pc.columns else pd.DataFrame()
    neg = quotes_1pc[quotes_1pc['sentiment'] == 'negative'] if 'sentiment' in quotes_1pc.columns else pd.DataFrame()
    mix = quotes_1pc[quotes_1pc['sentiment'].isin(['mixed', 'neutral'])] if 'sentiment' in quotes_1pc.columns else pd.DataFrame()

    for (subset, ttype) in [(pos, 'strength'), (neg, 'weakness'), (mix, 'investigation_needed')]:
        cluster = make_cluster(subset, ttype)
        if cluster:
            clusters.append(cluster)

    # If none created but guardrails met overall, emit a single mixed research cluster
    if not clusters:
        clusters.append({
            "theme_type": "investigation_needed",
            "harmonized_subject": (quotes_1pc['harmonized_subject'].mode().iloc[0]
                                    if 'harmonized_subject' in quotes_1pc.columns and not quotes_1pc['harmonized_subject'].isna().all()
                                    else "Research-Aligned"),
            "quotes": quotes_1pc,
            "pattern_summary": "Mixed evidence seeded by research question",
            "theme_origin": "research",
            "research_primary_question_seed": question_text,
        })

    return clusters 