#!/usr/bin/env python3
import sys
from typing import List, Dict, Any, Set, Tuple

from discussion_guide_integration import DiscussionGuideIntegrator
from supabase_database import SupabaseDatabase
from research_theme_generator import generate_research_clusters_for_question
from win_loss_report_generator import WinLossReportGenerator
from excel_win_loss_exporter import ExcelWinLossExporter


def normalize(s: str) -> str:
    return (s or '').strip().lower()


def score_pair(db_q_text: str, gq_text: str) -> float:
    db_q_text = (db_q_text or '').strip()
    gq_text = (gq_text or '').strip()
    if not db_q_text or not gq_text:
        return 0.0
    def _norm(x: str) -> str:
        x = (x or '').strip().lower()
        return ''.join(ch for ch in x if ch.isalnum() or ch.isspace())
    norm_db = _norm(db_q_text)
    ngq = _norm(gq_text)
    stop = {"can","you","your","about","tell","me","walk","through","share","as","was","it","that","how","what","would","to","the","and","or","a","of","for","just","maybe","well","like"}
    db_tokens_all = set(norm_db.split())
    gq_tokens_all = set(ngq.split())
    db_tokens = {t for t in db_tokens_all if t and t not in stop}
    gq_tokens = {t for t in gq_tokens_all if t and t not in stop}
    if not db_tokens or not gq_tokens:
        return 0.0
    inter = len(db_tokens & gq_tokens)
    union = max(len(db_tokens | gq_tokens), 1)
    score = inter / union
    comp_keywords = {"competitor","competitors","compare","compared","versus","vs","strength","strengths","weakness","weaknesses"}
    if (db_tokens_all & comp_keywords) and (gq_tokens_all & comp_keywords):
        score += 0.2
    if ("introduce" in norm_db or "your role" in norm_db) and ("firm" in norm_db or "attorneys" in norm_db or "support" in norm_db or "size" in norm_db):
        if ("introduce" in ngq) or ("to start" in ngq) or ("describe your role" in ngq):
            score = max(score, 0.9)
    if ('rated' in ngq and 'pricing' in ngq) and ('rating' in norm_db or 'rated' in norm_db or 'pricing' in norm_db):
        score = max(score, 0.6)
    if (('prompted' in ngq or 'pain' in ngq) and (('pain point' in norm_db) or ('prompt' in norm_db))):
        score = max(score, 0.7)
    if (('implementation' in ngq or 'onboarding' in ngq or 'experience' in ngq) and ('experience' in norm_db or 'implementation' in norm_db or 'onboarding' in norm_db)):
        score = max(score, 0.6)
    return float(min(score, 1.0))


def main(client_id: str = 'Supio') -> bool:
    db = SupabaseDatabase()
    # Load guide
    integrator = DiscussionGuideIntegrator()
    guide = integrator.parse_supio_discussion_guide('uploads/Supio_PRJ-00027 Discussion Guide v1.txt')
    guide_questions: List[str] = guide.get('questions', []) if guide else []
    if not guide_questions:
        print('❌ No discussion guide questions found')
        return False
    # Load quotes
    quotes_df = db.get_stage1_data_responses(client_id=client_id)
    if quotes_df is None or quotes_df.empty:
        print('❌ No quotes found')
        return False

    # Build mapping using exporter logic
    exporter = ExcelWinLossExporter()
    exporter.client_id = client_id
    exporter.discussion_guide = guide_questions
    exporter._build_question_map()

    # Build quick index maps
    db_q_by_id: Dict[str, str] = {}
    quotes_df = quotes_df.copy()
    for _, r in quotes_df.iterrows():
        rid = r.get('response_id')
        if rid is None:
            continue
        rid_s = str(rid)
        db_q_by_id[rid_s] = (r.get('question', '') or '')

    # Mapping per response
    mapped_gq_by_id: Dict[str, str] = {}
    for rid_s, dbq in db_q_by_id.items():
        try:
            mgq, _, _ = exporter._map_db_question_to_guide(dbq)
        except Exception:
            mgq = ''
        mapped_gq_by_id[rid_s] = mgq

    # Prepare generator thresholds from WinLossReportGenerator
    gen = WinLossReportGenerator(client_id)
    min_companies = gen.min_companies_per_theme
    min_quotes = gen.min_quotes_per_theme
    min_impact = gen.min_impact_threshold

    # Delete existing research themes for this client
    try:
        res = db.supabase.table('research_themes').select('theme_id').eq('client_id', client_id).eq('origin', 'research').execute()
        theme_ids = [t['theme_id'] for t in (res.data or []) if t.get('theme_id')]
        if theme_ids:
            db.supabase.table('research_theme_evidence').delete().in_('theme_id', theme_ids).execute()
            db.supabase.table('research_themes').delete().in_('theme_id', theme_ids).execute()
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

    # Rebuild themes per guide question
    theme_rows: List[Dict[str, Any]] = []
    theme_evidence_rows: List[Dict[str, Any]] = []

    # Convenience maps for evidence metadata
    quotes_by_id = {str(r.get('response_id')): r for _, r in quotes_df.iterrows() if r.get('response_id') is not None}

    MIN_ROWS_PER_Q = 8
    for gq in guide_questions:
        mapped_ids: Set[str] = {rid for rid, mgq in mapped_gq_by_id.items() if (mgq or '').strip() == gq.strip()}
        # Retrieval augmentation if sparse
        current_count = len(mapped_ids)
        if current_count < MIN_ROWS_PER_Q:
            scored: List[Tuple[float, str]] = []
            for rid_s, dbq in db_q_by_id.items():
                if not dbq:
                    continue
                s = score_pair(dbq, gq)
                if s > 0:
                    scored.append((s, rid_s))
            # Rank by score (desc); keep those not in mapped
            scored.sort(key=lambda x: (-x[0],))
            for s, rid_s in scored:
                if rid_s in mapped_ids:
                    continue
                if s < 0.6:
                    break
                mapped_ids.add(rid_s)
                if len(mapped_ids) >= MIN_ROWS_PER_Q:
                    break
        if not mapped_ids:
            continue
        # Build subset df for this question
        sub_records = [quotes_by_id[rid] for rid in mapped_ids if rid in quotes_by_id]
        if not sub_records:
            continue
        import pandas as pd
        sub_df = pd.DataFrame(sub_records)
        # Generate clusters
        clusters = generate_research_clusters_for_question(
            question_text=gq,
            quotes_for_question=sub_df,
            min_companies=min_companies,
            min_quotes=min_quotes,
            min_avg_impact=min_impact,
        )
        # For each cluster, generate headline
        for cl in clusters:
            aligned_df = cl.get('quotes')
            theme_type = cl.get('theme_type', 'investigation_needed')
            subject = cl.get('harmonized_subject', 'Research-Aligned')
            stmt = gen._generate_llm_research_driven_statement(
                primary_question=gq,
                aligned_quotes=aligned_df,
                theme_type=theme_type,
                subject=subject,
            )
            theme_rows.append({
                'client_id': client_id,
                'origin': 'research',
                'question_text': gq,
                'theme_statement': stmt,
            })

    # Upsert themes and collect returned IDs
    if theme_rows:
        inserted = db.upsert_research_themes_return(theme_rows)
        # Build a simple index by (question_text, theme_statement)
        key_to_id: Dict[Tuple[str, str], Any] = {}
        for row in (inserted or []):
            key = (row.get('question_text', ''), row.get('theme_statement', ''))
            key_to_id[key] = row.get('theme_id')
        # Reconstruct evidence rows by scoring again per question to reattach the same evidence selection
        for t in theme_rows:
            key = (t['question_text'], t['theme_statement'])
            tid = key_to_id.get(key)
            if not tid:
                continue
            gq = t['question_text']
            # same mapped_ids construction as above
            mapped_ids = {rid for rid, mgq in mapped_gq_by_id.items() if (mgq or '').strip() == gq.strip()}
            if len(mapped_ids) < MIN_ROWS_PER_Q:
                scored = []
                for rid_s, dbq in db_q_by_id.items():
                    if not dbq:
                        continue
                    s = score_pair(dbq, gq)
                    if s > 0:
                        scored.append((s, rid_s))
                scored.sort(key=lambda x: (-x[0],))
                for s, rid_s in scored:
                    if rid_s in mapped_ids:
                        continue
                    if s < 0.6:
                        break
                    mapped_ids.add(rid_s)
                    if len(mapped_ids) >= MIN_ROWS_PER_Q:
                        break
            for rid in mapped_ids:
                theme_evidence_rows.append({
                    'theme_id': tid,
                    'response_id': rid,
                })
    # Upsert evidence
    if theme_evidence_rows:
        db.upsert_research_theme_evidence(theme_evidence_rows)

    print(f"✅ Regenerated {len(theme_rows)} research themes and {len(theme_evidence_rows)} evidence links for {client_id}")
    return True


if __name__ == '__main__':
    cid = sys.argv[1] if len(sys.argv) > 1 else 'Supio'
    ok = main(cid)
    sys.exit(0 if ok else 1) 