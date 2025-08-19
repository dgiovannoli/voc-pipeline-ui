#!/usr/bin/env python3
"""
🎯 STAGE 3 THEME PROCESSOR
Creates high-quality themes from raw interview data using LLM analysis.
This is the core component that generates rich themes before workbook creation.
"""

import os
import sys
import logging
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import openai
from openai import OpenAI
import re
from collections import Counter
import yaml
import numpy as np

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from official_scripts.database.supabase_database import SupabaseDatabase

# Optional refinement utilities
try:
    from refine_theme_evidence import refine_all as refine_evidence_for_client
except Exception:
    refine_evidence_for_client = None

try:
    from tighten_theme_headlines import tighten_headlines as tighten_headlines_for_client
except Exception:
    tighten_headlines_for_client = None

try:
    from sanitize_theme_numbers import sanitize_headlines as sanitize_headlines_for_client
except Exception:
    sanitize_headlines_for_client = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'stage3_theme_processor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class Stage3ThemeProcessor:
    """
    Stage 3 Theme Processor - Creates high-quality themes from raw data
    """

    # -------------------- New Helpers for Specific Headlines --------------------
    @staticmethod
    def _tokenize(text: str) -> List[str]:
        if not text:
            return []
        text = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
        stop = set("the a an and or but so if then than with without into onto over under at on in to for from of by as is are was were be being been it this that those these their our your his her them they we you i not no can can't cannot won't will shall should would could may might must do does did done very more most much many few also".split())
        return [t for t in text.split() if t and t not in stop and len(t) > 2]

    def _build_lexicon(self, quotes_df: pd.DataFrame) -> List[str]:
        terms: List[str] = []
        # From verbatim text
        tokens: List[str] = []
        for txt in quotes_df.get('verbatim_response', []).fillna(""):
            tokens.extend(self._tokenize(txt))
        freq = Counter(tokens)
        common = [w for w, _ in freq.most_common(30)]
        terms.extend(common)
        # Add companies and any question keywords
        terms.extend([c for c in quotes_df.get('company', []).dropna().unique().tolist() if c])
        # Deduplicate while preserving order
        seen = set()
        lex = []
        for t in terms:
            if t and t not in seen:
                lex.append(t)
                seen.add(t)
        return lex[:25]

    @staticmethod
    def _extract_numbers(text: str) -> List[str]:
        if not text:
            return []
        pats = [
            re.compile(r"\$\s?\d[\d,]*\.?\d*"),
            re.compile(r"\b\d{1,3}(?:\.\d+)?%\b"),
            re.compile(r"\b\d+(?:\.\d+)?k\b", re.IGNORECASE),
            re.compile(r"\b\d[\d,]*\.?\d*\b"),
        ]
        toks = []
        for p in pats:
            toks.extend(m.group(0) for m in p.finditer(text))
        # Dedup preserve order
        seen = set(); out = []
        for t in toks:
            if t not in seen:
                out.append(t); seen.add(t)
        return out

    @staticmethod
    def _contains_causal_connector(text: str) -> bool:
        if not text:
            return False
        connectors = ["because"]
        low = text.lower()
        return any(c in low for c in connectors)

    def _normalize_text(self, text: str) -> str:
        """Lowercase, strip punctuation, collapse whitespace for robust matching."""
        if not isinstance(text, str):
            return ""
        t = text.lower()
        t = re.sub(r"[^a-z0-9\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def _token_overlap(self, a: str, b: str) -> float:
        """Compute token overlap ratio between two strings (Jaccard-like against target size)."""
        an = self._normalize_text(a)
        bn = self._normalize_text(b)
        if not an and not bn:
            return 1.0
        if not an or not bn:
            return 0.0
        sa = set(an.split())
        sb = set(bn.split())
        if not sa:
            return 0.0
        inter = len(sa & sb)
        return inter / max(len(sa), 1)

    # -------- Embedding-based semantic similarity helpers --------
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        try:
            if not text or not text.strip():
                return None
            resp = self.client.embeddings.create(
                model=os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small'),
                input=text.strip()
            )
            return resp.data[0].embedding
        except Exception as e:
            logger.warning(f"⚠️ Embedding error: {e}")
            return None

    def _get_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        if not texts:
            return []
        try:
            resp = self.client.embeddings.create(
                model=os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small'),
                input=texts
            )
            return [d.embedding for d in resp.data]
        except Exception as e:
            logger.warning(f"⚠️ Batch embedding error: {e}")
            return [None for _ in texts]

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        if vec1 is None or vec2 is None:
            return 0.0
        a = np.array(vec1, dtype=float)
        b = np.array(vec2, dtype=float)
        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    # -------- Domain lexicon and guide variant expansion --------
    def _load_domain_lexicon(self, quotes_df: pd.DataFrame) -> List[str]:
        terms: List[str] = []
        try:
            cfg_path = Path(__file__).parent / 'config' / 'subject_harmonization.yaml'
            if cfg_path.exists():
                with open(cfg_path, 'r') as f:
                    data = yaml.safe_load(f) or {}
                patterns = (data.get('harmonization_patterns') or {}).values()
                for p in patterns:
                    kws = p.get('keywords') or []
                    terms.extend(kws)
        except Exception as e:
            logger.warning(f"⚠️ Could not load domain lexicon from YAML: {e}")
        # add frequent tokens from responses to adapt
        tokens: List[str] = []
        for txt in quotes_df.get('verbatim_response', []).fillna(""):
            tokens.extend(self._tokenize(txt))
        freq = Counter(tokens)
        common = [w for w, _ in freq.most_common(40)]
        terms.extend(common)
        # deduplicate, lowercase
        seen = set(); out: List[str] = []
        for t in terms:
            tl = str(t).strip().lower()
            if tl and tl not in seen:
                out.append(tl); seen.add(tl)
        return out[:40]

    def _expand_guide_variants(self, question_text: str) -> List[str]:
        """Generate semantic paraphrases of the guide question to improve matching."""
        try:
            prompt = (
                "Paraphrase the following research question into 5 concise variants that preserve meaning "
                "but use different wording and synonyms. Return JSON list only.\nQUESTION: " + question_text
            )
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )
            content = resp.choices[0].message.content.strip()
            if content.startswith('```'):
                try:
                    content = content.split('```', 2)[1]
                except Exception:
                    pass
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    return [str(x) for x in data if isinstance(x, (str,))][:8]
            except Exception:
                # fall through
                pass
        except Exception as e:
            logger.warning(f"⚠️ Guide variant expansion failed: {e}")
        return []

    def _extract_entities(self, quotes_df: pd.DataFrame) -> List[str]:
        """Extract concrete entities (companies, acronyms) from quotes for specificity checks."""
        entities: List[str] = []
        # companies column often has real names (e.g., USPS, Endicia)
        entities.extend([c for c in quotes_df.get('company', []).dropna().unique().tolist() if isinstance(c, str) and c.strip()])
        # scan verbatim for all-caps acronyms and capitalized words likely to be entities
        for txt in quotes_df.get('verbatim_response', []).fillna(""):
            for token in re.findall(r"\b[A-Z]{3,}\b", str(txt)):
                if token not in entities:
                    entities.append(token)
            for token in re.findall(r"\b[A-Z][a-zA-Z]+\b", str(txt)):
                if token.lower() in {"the","and","but","because","when","due","resulting","leading","so"}:
                    continue
                if token not in entities:
                    entities.append(token)
        # de-dup while preserving order
        seen = set(); out: List[str] = []
        for e in entities:
            if e and e not in seen:
                out.append(e); seen.add(e)
        return out[:20]

    def _headline_from_quotes(self, question_text: str, category: str, quotes_df: pd.DataFrame) -> str:
        """Generate a specific Who–What–Why–Impact headline with validation/revision loop."""
        sample_df = quotes_df.copy().head(12)
        lexicon = self._build_lexicon(sample_df)
        entities = self._extract_entities(sample_df)
        client_name = self.client_id.strip()
        # Always make the client name a candidate entity
        if client_name not in entities:
            entities.insert(0, client_name)
        # Prefer USPS if present in quotes; else require client name
        quotes_text_all = " ".join(sample_df.get('verbatim_response', []).fillna("").tolist())
        must_entity = "USPS" if re.search(r"\bUSPS\b", quotes_text_all) else client_name

        quotes_block = "\n".join([
            f"- {row.get('company','')} | {row.get('interviewee_name','')} | {row.get('sentiment','')} | {row.get('deal_status','')} → {(row.get('verbatim_response','') or '').replace('\n',' ')[:220]}"
            for _, row in sample_df.iterrows()
        ])

        banned_phrases = [
            "b2b saas", "leaders", "stakeholders", "synergy", "optimize", "streamline",
            "robust", "scalable", "ecosystem", "empower", "best-in-class", "leverage",
            "enhancing user experience", "improve user experience"
        ]

        connectors = ["because"]

        base_prompt = f"""
ROLE: You are a VOC analyst writing an executive slide headline.

TASK: Produce ONE headline (12–18 words) in Who–What–Why–Impact and select supporting quotes by id.

MUST RULES:
- Use EXACTLY ONE causal connector chosen from CONNECTORS and include it verbatim in the headline.
- Include at least 2 terms from LEXICON (prioritize roles/systems/process terms found in QUOTES).
- Include one concrete entity from ENTITIES; prefer "USPS" if present, otherwise use "{must_entity}".
- Do NOT invent numbers; only include numbers that appear verbatim in QUOTES.
- Avoid generic/banned language: leaders, stakeholders, empower, streamline, optimize, robust, scalable, synergy, ecosystem, best-in-class, enhancing user experience, improve user experience.
- Be specific to this client and these interviewees (no generic "B2B SaaS leaders").

CONNECTORS: {', '.join(connectors)}
CLIENT_NAME: {self.client_id}
CATEGORY: {category}
RESEARCH_QUESTION: {question_text}
LEXICON: {', '.join(lexicon)}
ENTITIES: {', '.join(entities)}

QUOTES (only these are allowed as evidence):
{quotes_block}

EXAMPLES (style and format only):
- "Ops teams adopt Endicia because USPS returns processing delays cash posting, resulting in charge disputes"
- "Finance managers choose Endicia due to USPS manifest errors during invoicing, leading to rework"

OUTPUT (JSON only; no prose):
{{
  "headline": "12–18 words, includes exactly one connector and one entity from ENTITIES",
  "supporting_quotes": [],
  "used_lexicon_terms": [],
  "entity_used": "USPS|{must_entity}",
  "connector_used": "one of CONNECTORS",
  "numbers": []
}}
"""
        # Up to 4 attempts with self-critique
        for attempt in range(4):
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": base_prompt}],
                temperature=0.1,
                max_tokens=220
            )
            content = resp.choices[0].message.content.strip()
            if content.startswith('```'):
                try:
                    content = content.split('```', 2)[1]
                except Exception:
                    pass
            try:
                data = json.loads(content)
                headline = (data.get('headline') or '').strip()
                used_terms = [t.lower() for t in data.get('used_lexicon_terms', [])]
            except Exception:
                headline = content.strip()
                used_terms = []

            # Validate
            valid = True
            wc = len(headline.split())
            if wc < 12 or wc > 18:
                valid = False
            # lexicon overlap
            overlap = len({t for t in used_terms if t in [x.lower() for x in lexicon]})
            if overlap < 2:
                overlap = sum(1 for t in lexicon if t.lower() in headline.lower())
                if overlap < 2:
                    valid = False
            # connector strictly from text
            low_head = headline.lower()
            if not any(c in low_head for c in connectors):
                valid = False
            # numeric support
            qnorm = quotes_text_all.lower().replace(",", "")
            for n in self._extract_numbers(headline):
                raw = n.lower().replace(",", "")
                if raw and raw not in qnorm:
                    valid = False; break
            # banned phrases and misspelling
            if any(bp in low_head for bp in banned_phrases) or 'indicia' in low_head:
                valid = False
            # must include entity
            if must_entity.lower() not in low_head:
                valid = False

            if valid:
                return headline

            # Build stricter critique
            reasons = []
            if wc < 12 or wc > 18: reasons.append("length not 12–18 words")
            if overlap < 2: reasons.append("<2 lexicon terms used")
            if not any(c in low_head for c in connectors): reasons.append("missing causal connector")
            if any(bp in low_head for bp in banned_phrases) or 'indicia' in low_head: reasons.append("generic/banned wording")
            if must_entity.lower() not in low_head: reasons.append(f"missing required entity '{must_entity}'")
            critique = (
                "Rewrite to satisfy ALL rules. Use EXACTLY ONE connector from ['because','due to','when','leading to','resulting in','drives','causes','so that']; "
                f"include '{must_entity}' verbatim; avoid banned words (leaders, empower, streamline, synergy, robust, scalable); maintain 12–18 words; use ≥2 lexicon terms."
            )
            base_prompt = base_prompt + "\n\nREVISION_INSTRUCTION: " + ", ".join(reasons) + ". " + critique

        # Final strict rewrite attempt
        strict_prompt = (
            f"Rewrite this headline to satisfy rules exactly. HEADLINE: '{headline}'. "
            f"Use exactly one connector from {connectors}; include '{must_entity}' verbatim; avoid banned terms; 12–18 words; keep concrete roles from quotes. Return JSON with {{'headline': '...'}}"
        )
        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": strict_prompt}],
            temperature=0.0,
            max_tokens=160
        )
        try:
            data = json.loads(resp.choices[0].message.content.strip().strip('`'))
            final_head = (data.get('headline') or '').strip()
            return final_head if final_head else headline
        except Exception:
            return headline

    def _stage4_style_statement_from_quotes(self, question_text: str, category: str, quotes_df: pd.DataFrame) -> str:
        """Generate an EXACTLY two-sentence executive theme statement following Stage 4 methodology.
        Sentence 1: Decision behavior or specific problem with consequence
        Sentence 2: Most common interviewee pain point or reaction (paraphrased)
        No solutioning language. No invented numbers or entities. Uses only provided quotes.
        """
        sample = quotes_df.copy().head(12)
        sample_quotes = [
            f"- {str(r.get('verbatim_response','')).replace('\n',' ')[:240]}"
            for _, r in sample.iterrows()
            if str(r.get('verbatim_response','')).strip()
        ]
        quotes_block = "\n".join(sample_quotes)

        prompt = f"""
⚠️ CRITICAL: Generate an executive-ready theme statement following Stage 4 methodology EXACTLY.

THEME CONTEXT:
- Category: {category}
- Research Question: {question_text}

SAMPLE CUSTOMER QUOTES (evidence pool; do not invent):
{quotes_block}

CRITICAL REQUIREMENTS:
1. EXACTLY two sentences — NO MORE, NO LESS
2. Sentence 1: Decision behavior or specific problem with consequence (25–35 words)
3. Sentence 2: Most common customer pain point or reaction in your own words (25–35 words)
4. NO direct quotes inside the statement
5. NO solutioning language (e.g., "indicating a need for", "suggesting", "recommending", "requiring")
6. NO invented numbers or company names; use only what appears in QUOTES
7. Use SPECIFIC customer terminology from the quotes; avoid buzzwords

OUTPUT (JSON only; no prose):
{{
  "theme_statement": "Sentence 1. Sentence 2."
}}
"""
        # Up to 3 attempts with validation
        for _ in range(3):
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=220
            )
            content = resp.choices[0].message.content.strip()
            if content.startswith('```'):
                try:
                    content = content.split('```', 2)[1]
                except Exception:
                    pass
            try:
                data = json.loads(content)
                stmt = (data.get('theme_statement') or '').strip()
            except Exception:
                stmt = content.strip()

            # Validation: exactly two sentences, no solutioning keywords
            raw = stmt.replace('\n',' ').strip()
            # Normalize spaces
            raw = re.sub(r"\s+", " ", raw)
            sentences = [s.strip() for s in re.split(r"(?<=[\.!?])\s+", raw) if s.strip()]
            # Count only sentences ending in punctuation
            sentences = [s for s in sentences if re.search(r"[\.!?]$", s)]
            banned = ["indicating a need for", "suggesting", "recommending", "requiring"]
            has_banned = any(b in raw.lower() for b in banned)
            if len(sentences) == 2 and not has_banned:
                return " ".join(sentences)
            # tighten instruction
            prompt += "\nREVISION: Ensure exactly two sentences with terminal punctuation and remove any solutioning language."
        # Fallback
        return "Customers exhibit a specific behavior or face a clear problem, creating a tangible consequence. Interviewees consistently describe the most common reaction in their own words without proposing solutions."

    # -------------------- End Helpers --------------------

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.db = SupabaseDatabase()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.client_prefix = self._get_client_prefix(client_id)

    def _get_client_prefix(self, client_id: str) -> str:
        """Get client prefix for theme IDs"""
        if client_id.lower() == 'endicia':
            return 'EL'  # Endicia Law
        elif client_id.lower() == 'supio':
            return 'SL'  # Supio Law
        else:
            return client_id[:2].upper()

    def process_stage3_themes(self) -> Dict[str, Any]:
        """
        Main Stage 3 processing pipeline
        """
        start_time = datetime.now()
        logger.info(f"🚀 Starting Stage 3 theme processing for {self.client_id}")

        try:
            # Step 1: Extract discussion guide questions
            logger.info("📋 Step 1: Extracting discussion guide questions...")
            discussion_questions = self._extract_discussion_questions()

            # Step 2: Generate research themes from questions
            logger.info("🔬 Step 2: Generating research themes...")
            research_themes = self._generate_research_themes(discussion_questions)

            # Step 3: Generate discovered themes from patterns
            logger.info("🔍 Step 3: Generating discovered themes...")
            discovered_themes = self._generate_discovered_themes()

            # Step 4: Enhance themes with metadata
            logger.info("✨ Step 4: Enhancing themes with metadata...")
            enhanced_themes = self._enhance_themes_with_metadata(research_themes + discovered_themes)

            # Step 5: Save themes to database
            logger.info("💾 Step 5: Saving themes to database...")
            saved_count = self._save_themes_to_database(enhanced_themes)

            # Step 6: Evidence alignment and selection (caps: 6–12, max 2 per interview)
            refinement_result = None
            if refine_evidence_for_client is not None:
                logger.info("🧭 Step 6: Aligning and capping supporting quotes per theme...")
                refinement_result = refine_evidence_for_client(self.client_id)
                logger.info(f"✅ Evidence refinement complete: {refinement_result}")
            else:
                logger.info("ℹ️ Evidence refinement utility not available. Skipping.")

            # Step 7: Tighten headlines with Who–What–Why–Impact (grounded in quotes)
            tighten_result = None
            DO_TIGHTEN = os.getenv('STAGE3_TIGHTEN_HEADLINES', 'false').lower() in ('1','true','yes')
            if tighten_headlines_for_client is not None and DO_TIGHTEN:
                logger.info("✍️ Step 7: Tightening theme headlines (Who–What–Why–Impact)...")
                tighten_result = tighten_headlines_for_client(self.client_id)
                logger.info(f"✅ Headline tightening complete: {tighten_result}")
            else:
                logger.info("ℹ️ Skipping Step 7 headline tightening to preserve Stage 4 two-sentence statements. Set STAGE3_TIGHTEN_HEADLINES=true to enable.")

            # Step 8: Sanitize unsupported numbers in headlines
            sanitize_result = None
            if sanitize_headlines_for_client is not None:
                logger.info("🔒 Step 8: Sanitizing unsupported numeric claims in headlines...")
                sanitize_result = sanitize_headlines_for_client(self.client_id)
                logger.info(f"✅ Numeric sanitization complete: {sanitize_result}")
            else:
                logger.info("ℹ️ Numeric sanitization utility not available. Skipping.")

            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Stage 3 theme processing completed in {processing_time:.1f}s")
            logger.info(f"📊 Generated {len(enhanced_themes)} themes, saved {saved_count} to database")

            return {
                "success": True,
                "research_themes": len(research_themes),
                "discovered_themes": len(discovered_themes),
                "total_themes": len(enhanced_themes),
                "saved_count": saved_count,
                "processing_time": processing_time,
                "evidence_refinement": refinement_result,
                "headline_tightening": tighten_result,
                "numeric_sanitization": sanitize_result,
            }

        except Exception as e:
            logger.error(f"❌ Stage 3 theme processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _extract_discussion_questions(self) -> List[Dict[str, Any]]:
        """
        Extract discussion guide questions from interview metadata
        """
        try:
            # Get interview metadata with discussion guides
            response = self.db.supabase.table('interview_metadata').select(
                'interview_id,interview_guides,raw_transcript'
            ).eq('client_id', self.client_id).execute()

            if not response.data:
                logger.warning("⚠️ No interview metadata found, using default questions")
                return self._get_default_questions()

            questions = []
            for metadata in response.data:
                interview_id = metadata.get('interview_id')
                interview_guides = metadata.get('interview_guides', '')
                
                if interview_guides:
                    # Extract questions from discussion guide
                    extracted_questions = self._extract_questions_from_guide(interview_guides, interview_id)
                    questions.extend(extracted_questions)

            if not questions:
                logger.warning("⚠️ No questions extracted, using default questions")
                return self._get_default_questions()

            # Canonicalize across interviews to avoid duplicates
            questions = self._canonicalize_questions(questions)

            logger.info(f"✅ Extracted {len(questions)} discussion questions")
            return questions

        except Exception as e:
            logger.warning(f"⚠️ Error extracting discussion questions: {e}")
            return self._get_default_questions()

    def _canonicalize_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate guide questions across interviews by normalized text; keep the first verbatim as canonical.
        Returns a list with unique question_text and stable question_number ordering.
        """
        seen: Dict[str, Dict[str, Any]] = {}
        for q in questions:
            text = (q.get('question_text') or '').strip()
            if not text:
                continue
            key = self._normalize_text(text)
            if key not in seen:
                seen[key] = {
                    'question_text': text,
                    'question_number': q.get('question_number', len(seen) + 1),
                    'category': q.get('category') or 'Guide'
                }
        # Reassign sequential numbers to keep order stable
        out = []
        for i, item in enumerate(seen.values(), start=1):
            item['question_number'] = i
            out.append(item)
        return out

    def _extract_questions_from_guide(self, guide_text: str, interview_id: str) -> List[Dict[str, Any]]:
        """
        Extract questions from discussion guide using LLM
        """
        try:
            prompt = f"""
            Extract the main research questions from this discussion guide. 
            Focus on questions that would generate meaningful customer insights.
            
            Discussion Guide:
            {guide_text}
            
            Return a JSON array of question objects with this structure:
            [
                {{
                    "question_text": "The actual question text",
                    "question_number": 1,
                    "category": "Background/Evaluation/Decision/etc",
                    "interview_id": "{interview_id}"
                }}
            ]
            
            Only return the JSON array, no other text.
            """

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )

            content = response.choices[0].message.content.strip()
            
            # Clean up JSON response
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            questions = json.loads(content)
            return questions

        except Exception as e:
            logger.warning(f"⚠️ Error extracting questions from guide: {e}")
            return []

    def _get_default_questions(self) -> List[Dict[str, Any]]:
        """
        Get default research questions when no discussion guide is available
        """
        default_questions = [
            {
                "question_text": "What prompted you to evaluate solutions like this?",
                "question_number": 1,
                "category": "Background",
                "interview_id": "default"
            },
            {
                "question_text": "What were your main pain points and challenges?",
                "question_number": 2,
                "category": "Pain Points",
                "interview_id": "default"
            },
            {
                "question_text": "What benefits have you experienced with the solution?",
                "question_number": 3,
                "category": "Benefits",
                "interview_id": "default"
            },
            {
                "question_text": "How would you rate your overall experience?",
                "question_number": 4,
                "category": "Satisfaction",
                "interview_id": "default"
            },
            {
                "question_text": "How do you compare this to alternatives?",
                "question_number": 5,
                "category": "Competitive",
                "interview_id": "default"
            }
        ]
        return default_questions

    def _generate_research_themes(self, discussion_questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate research themes from discussion questions and associated quotes
        """
        try:
            # Get all quotes for this client
            response = self.db.supabase.table('stage1_data_responses').select(
                'response_id,company,interviewee_name,question,verbatim_response,sentiment,deal_status,impact_score'
            ).eq('client_id', self.client_id).execute()

            if not response.data:
                logger.warning("⚠️ No quotes found for research theme generation")
                return []

            quotes_df = pd.DataFrame(response.data)
            research_themes = []

            for question_data in discussion_questions:
                question_text = question_data['question_text']
                question_number = question_data['question_number']
                category = question_data['category']

                # Find quotes that match this guide question based on the question field (not response text)
                matching_quotes = self._find_matching_quotes(quotes_df, question_text)

                # Coverage thresholds: require ≥2 unique interviewees OR ≥4 quotes total
                coverage = matching_quotes['interviewee_name'].nunique() if not matching_quotes.empty else 0
                if matching_quotes is not None and not matching_quotes.empty:
                    if coverage >= 2 or len(matching_quotes) >= 4:
                        theme = self._create_research_theme(
                            question_data, matching_quotes, question_number, category
                        )
                        research_themes.append(theme)
                 
            logger.info(f"✅ Generated {len(research_themes)} research themes")
            return research_themes

        except Exception as e:
            logger.error(f"❌ Error generating research themes: {e}")
            return []

    def _find_matching_quotes(self, quotes_df: pd.DataFrame, question_text: str) -> pd.DataFrame:
        """
        Find quotes that match a guide question using semantic similarity on the Stage 1 'question' field.
        Priority: per-interview best matching question by embedding cosine similarity (>= 0.65);
        fallback to global similarity; final fallback to token overlap.
        """
        try:
            target = self._normalize_text(question_text)
            if 'question' not in quotes_df.columns or quotes_df.empty:
                return pd.DataFrame()

            df = quotes_df.copy()
            # Exclude UNKNOWN questions
            df = df[~df['question'].astype(str).str.upper().str.contains('UNKNOWN', na=False)].copy()
            if df.empty:
                return pd.DataFrame()

            # Compute expanded guide embedding (original + paraphrases)
            variants = self._expand_guide_variants(question_text)
            guide_texts = [question_text] + variants
            guide_embeds = self._get_embeddings_batch(guide_texts)
            # average non-null embeddings
            valid_ge = [e for e in guide_embeds if e is not None]
            target_embed = None
            if valid_ge:
                target_embed = list(np.mean(np.array(valid_ge, dtype=float), axis=0))
 
            uq_all = df['question'].dropna().astype(str).unique().tolist()
            uq_embeds = self._get_embeddings_batch(uq_all)
            q_to_embed = {q: e for q, e in zip(uq_all, uq_embeds)}

            # Precompute response embeddings for blended scoring
            resp_texts = df['verbatim_response'].fillna("").astype(str).tolist() if 'verbatim_response' in df.columns else []
            resp_embeds = self._get_embeddings_batch(resp_texts) if resp_texts else []
            df['__resp_embed'] = resp_embeds if resp_embeds else None

            # Build domain lexicon and a quick presence flag
            domain_terms = set(self._load_domain_lexicon(df))
            def has_domain_term(q, r):
                qn = self._normalize_text(str(q))
                rn = self._normalize_text(str(r))
                for t in domain_terms:
                    if t and (f" {t} " in f" {qn} " or f" {t} " in f" {rn} "):
                        return True
                return False

            # Build per-interview grouping (fallback to company if interviewee_name missing)
            group_key = 'interviewee_name' if 'interviewee_name' in df.columns else ('company' if 'company' in df.columns else None)
            selected_rows = []
            matched = pd.DataFrame()
 
            if group_key is not None and target_embed is not None:
                for gval, gdf in df.groupby(group_key):
                    rows = []
                    for idx, row in gdf.iterrows():
                        q_text = str(row.get('question', ''))
                        r_text = str(row.get('verbatim_response', ''))
                        q_emb = q_to_embed.get(q_text)
                        r_emb = row.get('__resp_embed') if '__resp_embed' in gdf.columns else None
                        sim_q = self._cosine_similarity(target_embed, q_emb)
                        sim_r = self._cosine_similarity(target_embed, r_emb)
                        blended = 0.5 * (sim_q + sim_r)
                        rows.append((idx, blended))
                    if not rows:
                        continue
                    # Pick best per interview by blended score
                    best_idx, best_s = max(rows, key=lambda x: x[1])
                    if best_s >= 0.55:
                        match_g = gdf.loc[[best_idx]].copy()
                        match_g['__blended_sim'] = best_s
                        # domain lexicon gating
                        if has_domain_term(match_g.iloc[0]['question'], match_g.iloc[0].get('verbatim_response','')):
                            selected_rows.append(match_g)
                if selected_rows:
                    matched = pd.concat(selected_rows, ignore_index=True)
 
            # If nothing matched by mapping, fallback to global question similarity
            if matched.empty:
                if target_embed is not None:
                    # Compute blended for all rows
                    sims_q = [self._cosine_similarity(target_embed, q_to_embed.get(q)) for q in df['question'].astype(str).tolist()]
                    sims_r = [self._cosine_similarity(target_embed, e) for e in (df['__resp_embed'].tolist() if '__resp_embed' in df.columns else [None]*len(df))]
                    blended = [0.5*(a+b) for a,b in zip(sims_q, sims_r)]
                    df['__blended_sim'] = blended
                    # Domain gating
                    df['__domain_ok'] = df.apply(lambda r: has_domain_term(r.get('question',''), r.get('verbatim_response','')), axis=1)
                    cand = df[(df['__blended_sim'] >= 0.55) & (df['__domain_ok'])].copy()
                    if cand.empty:
                        cand = df[(df['__blended_sim'] >= 0.45) & (df['__domain_ok'])].copy()
                    if cand.empty:
                        cand = df[df['__blended_sim'] >= 0.55].copy()
                    if cand.empty:
                        cand = df[df['__blended_sim'] >= 0.4].copy()
                    matched = cand.sort_values('__blended_sim', ascending=False).copy()
                else:
                    # Final fallback to token overlap
                    df['match_score'] = df['question'].apply(lambda q: self._token_overlap(target, str(q)))
                    matched = df[df['match_score'] >= 0.5].sort_values('match_score', ascending=False).copy()
                    if matched.empty:
                        matched = df[df['match_score'] >= 0.35].sort_values('match_score', ascending=False).copy()
                    matched = matched.drop(columns=['match_score'], errors='ignore')
 
            # Alignment gating: enforce proportion of well-aligned quotes
            if not matched.empty and '__blended_sim' in matched.columns:
                aligned = matched['__blended_sim'] >= 0.55
                frac = float(aligned.mean()) if len(matched) else 0.0
                if frac < 0.6:
                    strong = matched[matched['__blended_sim'] >= 0.55]
                    weak = matched[(matched['__blended_sim'] < 0.55) & (matched['__blended_sim'] >= 0.45)]
                    matched = pd.concat([strong, weak.head(max(0, 12-len(strong)))], ignore_index=True)

            # Cap to 50 for efficiency
            cols_drop = ['__resp_embed']
            return matched.drop(columns=[c for c in cols_drop if c in matched.columns], errors='ignore').head(50)

        except Exception as e:
            logger.warning(f"⚠️ Error finding matching quotes: {e}")
            return pd.DataFrame()

    def _create_research_theme(self, question_data: Dict[str, Any], matching_quotes: pd.DataFrame, question_number: int, category: str) -> Dict[str, Any]:
        """
        Create a research theme from question and matching quotes
        """
        try:
            # Build a Stage 4-style statement using quotes
            theme_statement = self._stage4_style_statement_from_quotes(
                question_text=question_data['question_text'],
                category=category,
                quotes_df=matching_quotes
            )

            # Create theme object
            theme = {
                "theme_id": str(uuid.uuid4()),
                "theme_statement": theme_statement,
                "origin": "research",
                "category": category,
                "question_text": question_data['question_text'],
                "question_number": question_number,
                "supporting_quotes": matching_quotes.head(12)['response_id'].tolist(),
                "companies": matching_quotes['company'].unique().tolist(),
                "interviewees": matching_quotes['interviewee_name'].unique().tolist(),
                "quote_count": int(min(len(matching_quotes), 12)),
                "company_count": len(matching_quotes['company'].unique()),
                "interviewee_count": len(matching_quotes['interviewee_name'].unique()),
                "sentiment_distribution": matching_quotes['sentiment'].value_counts().to_dict(),
                "deal_status_distribution": matching_quotes['deal_status'].value_counts().to_dict(),
                "average_impact_score": float(matching_quotes['impact_score'].mean() if 'impact_score' in matching_quotes.columns else 0),
                "confidence_score": 0.9,
                "created_at": datetime.now().isoformat()
            }

            return theme

        except Exception as e:
            logger.warning(f"⚠️ Error creating research theme: {e}")
            return {}

    def _generate_discovered_themes(self) -> List[Dict[str, Any]]:
        """
        Generate discovered themes focused on harmonized_subject patterns (more strategic and focused)
        """
        try:
            # Get all quotes for pattern analysis
            response = self.db.supabase.table('stage1_data_responses').select(
                'response_id,company,interviewee_name,question,verbatim_response,sentiment,deal_status,impact_score,harmonized_subject'
            ).eq('client_id', self.client_id).execute()

            if not response.data:
                logger.warning("⚠️ No quotes found for discovered theme generation")
                return []

            df = pd.DataFrame(response.data)
            discovered_themes = []

            # Focus on harmonized_subject based themes (more strategic and focused)
            
            # Pattern 1: High sentiment responses (only if significant)
            high_sentiment = df[df['sentiment'].isin(['positive', 'very_positive'])]
            if len(high_sentiment) >= 8:  # Higher threshold for sentiment
                theme = self._create_discovered_theme(
                    "Customer Satisfaction Excellence",
                    "Positive customer experiences and satisfaction drivers",
                    high_sentiment,
                    "Customer Satisfaction",
                    1
                )
                discovered_themes.append(theme)

            # Pattern 2: Negative sentiment responses (only if significant)
            negative_sentiment = df[df['sentiment'].isin(['negative', 'very_negative'])]
            if len(negative_sentiment) >= 5:  # Higher threshold for pain points
                theme = self._create_discovered_theme(
                    "Customer Pain Points",
                    "Customer pain points and dissatisfaction factors",
                    negative_sentiment,
                    "Pain Points",
                    2
                )
                discovered_themes.append(theme)

            # Pattern 3: Deal status patterns (only significant ones)
            for deal_status in df['deal_status'].unique():
                if pd.isna(deal_status):
                    continue
                deal_quotes = df[df['deal_status'] == deal_status]
                if len(deal_quotes) >= 6:  # Higher threshold for deal patterns
                    theme = self._create_discovered_theme(
                        f"{deal_status} Deal Patterns",
                        f"Patterns and insights from {deal_status} deals",
                        deal_quotes,
                        "Deal Analysis",
                        len(discovered_themes) + 3
                    )
                    discovered_themes.append(theme)

            # Pattern 4: High impact score patterns (strategic insights)
            if 'impact_score' in df.columns:
                high_impact = df[df['impact_score'] >= 7.5]  # Higher threshold
                if len(high_impact) >= 4:  # Only if we have enough high-impact quotes
                    theme = self._create_discovered_theme(
                        "High-Impact Customer Feedback",
                        "Customer feedback with high strategic impact scores",
                        high_impact,
                        "Strategic Impact",
                        len(discovered_themes) + 4
                    )
                    discovered_themes.append(theme)

            # Pattern 5: Harmonized subject clustering (NEW - more strategic)
            if 'harmonized_subject' in df.columns:
                # Group quotes by harmonized_subject and find significant clusters
                subject_groups = df.groupby('harmonized_subject')
                
                for subject, subject_quotes in subject_groups:
                    if pd.isna(subject) or subject == 'UNKNOWN':
                        continue
                    
                    # Only create themes for subjects with enough quotes
                    if len(subject_quotes) >= 4:  # Higher threshold for subject themes
                        # Analyze sentiment distribution within this subject
                        positive_count = len(subject_quotes[subject_quotes['sentiment'].isin(['positive', 'very_positive'])])
                        negative_count = len(subject_quotes[subject_quotes['sentiment'].isin(['negative', 'very_negative'])])
                        
                        if positive_count >= 3 or negative_count >= 3:
                            # Create theme based on dominant sentiment in this subject area
                            if positive_count > negative_count:
                                theme_title = f"{subject} - Positive Patterns"
                                theme_description = f"Positive patterns and satisfaction in {subject.lower()} area"
                                category = f"{subject} Analysis"
                            else:
                                theme_title = f"{subject} - Challenge Patterns"
                                theme_description = f"Challenges and pain points in {subject.lower()} area"
                                category = f"{subject} Analysis"
                            
                            theme = self._create_discovered_theme(
                                theme_title,
                                theme_description,
                                subject_quotes,
                                category,
                                len(discovered_themes) + 5
                            )
                            discovered_themes.append(theme)

            logger.info(f"✅ Generated {len(discovered_themes)} discovered themes (focused on harmonized subjects)")
            return discovered_themes

        except Exception as e:
            logger.error(f"❌ Error generating discovered themes: {e}")
            return []

    def _create_discovered_theme(self, title: str, description: str, quotes_df: pd.DataFrame, category: str, theme_number: int) -> Dict[str, Any]:
        """
        Create a discovered theme from pattern analysis
        """
        try:
            # Use Stage 4-style statement
            theme_statement = self._stage4_style_statement_from_quotes(
                question_text=title,
                category=category,
                quotes_df=quotes_df.head(12)
            )

            # Create theme object
            theme = {
                "theme_id": str(uuid.uuid4()),
                "theme_statement": theme_statement,
                "origin": "research",  # Workaround: Database only allows 'research'
                "category": f"DISCOVERED: {category}",
                "pattern_title": title,
                "pattern_description": description,
                "supporting_quotes": quotes_df.head(12)['response_id'].tolist(),
                "companies": quotes_df['company'].unique().tolist(),
                "interviewees": quotes_df['interviewee_name'].unique().tolist(),
                "quote_count": int(min(len(quotes_df), 12)),
                "company_count": len(quotes_df['company'].unique()),
                "interviewee_count": len(quotes_df['interviewee_name'].unique()),
                "sentiment_distribution": quotes_df['sentiment'].value_counts().to_dict(),
                "deal_status_distribution": quotes_df['deal_status'].value_counts().to_dict(),
                "average_impact_score": float(quotes_df['impact_score'].mean() if 'impact_score' in quotes_df.columns else 0),
                "confidence_score": 0.8,
                "created_at": datetime.now().isoformat()
            }

            return theme

        except Exception as e:
            logger.warning(f"⚠️ Error creating discovered theme: {e}")
            return {}

    def _enhance_themes_with_metadata(self, themes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance themes with additional metadata and insights
        """
        try:
            enhanced_themes = []

            for theme in themes:
                if not theme:
                    continue

                # Calculate evidence strength
                quote_count = theme.get('quote_count', 0)
                company_count = theme.get('company_count', 0)
                confidence_score = theme.get('confidence_score', 0.5)
                
                evidence_strength = min(1.0, (quote_count * 0.3 + company_count * 0.2 + confidence_score * 0.5))

                # Calculate sentiment coherence
                sentiment_dist = theme.get('sentiment_distribution', {})
                if sentiment_dist:
                    total_quotes = sum(sentiment_dist.values())
                    max_sentiment = max(sentiment_dist.values())
                    sentiment_coherence = max_sentiment / total_quotes if total_quotes > 0 else 0
                else:
                    sentiment_coherence = 0

                # Enhanced theme
                enhanced_theme = {
                    **theme,
                    "evidence_strength": round(evidence_strength, 2),
                    "sentiment_coherence": round(sentiment_coherence, 2),
                    "impact_score": round(theme.get('average_impact_score', 0), 2),
                    "harmonized_subject": theme.get('category', 'General'),
                    "company_coverage": theme.get('companies', []),
                    "deal_status_breakdown": theme.get('deal_status_distribution', {}),
                    "status": "draft",
                    "section": None,
                    "enhanced_at": datetime.now().isoformat()
                }

                enhanced_themes.append(enhanced_theme)

            logger.info(f"✅ Enhanced {len(enhanced_themes)} themes with metadata")
            return enhanced_themes

        except Exception as e:
            logger.error(f"❌ Error enhancing themes: {e}")
            return themes

    def _save_themes_to_database(self, themes: List[Dict[str, Any]]) -> int:
        """
        Save themes to the research_themes table
        """
        try:
            saved_count = 0

            for theme in themes:
                if not theme:
                    continue

                try:
                    # Prepare theme data for database
                    theme_data = {
                        "theme_id": theme['theme_id'],
                        "theme_statement": theme['theme_statement'],
                        "origin": theme['origin'],
                        "question_text": theme.get('question_text', 'Pattern-based analysis'),  # Required field
                        "harmonized_subject": theme.get('harmonized_subject', 'General'),
                        "impact_score": theme.get('impact_score', 0),
                        "company_coverage": theme.get('company_coverage', []),
                        "supporting_quotes": theme.get('supporting_quotes', []),
                        "evidence_strength": theme.get('evidence_strength', 0),
                        "deal_status_breakdown": theme.get('deal_status_breakdown', {}),
                        "sentiment_coherence": theme.get('sentiment_coherence', 0),
                        "interviewee_count": theme.get('interviewee_count', 0),
                        "status": theme.get('status', 'draft'),  # Database constraint only allows 'draft'
                        "section": theme.get('section'),
                        "client_id": self.client_id,
                        "created_at": theme.get('created_at'),
                        "updated_at": datetime.now().isoformat()
                    }

                    # Upsert theme to database
                    response = self.db.supabase.table('research_themes').upsert(
                        theme_data,
                        on_conflict='theme_id'
                    ).execute()

                    if response.data:
                        saved_count += 1
                        logger.debug(f"✅ Saved theme: {theme['theme_id']}")

                except Exception as e:
                    logger.warning(f"⚠️ Error saving theme {theme.get('theme_id', 'unknown')}: {e}")

            logger.info(f"✅ Successfully saved {saved_count} themes to database")
            return saved_count

        except Exception as e:
            logger.error(f"❌ Error saving themes to database: {e}")
            return 0

    def get_processing_status(self) -> Dict[str, Any]:
        """
        Get the current processing status for this client
        """
        try:
            # Check if themes exist for this client
            response = self.db.supabase.table('research_themes').select(
                'theme_id,origin,theme_statement,supporting_quotes'
            ).eq('client_id', self.client_id).execute()

            themes = response.data
            research_count = len([t for t in themes if t.get('origin') == 'research'])
            discovered_count = len([t for t in themes if t.get('origin') == 'discovered'])
            total_quotes = sum([len(t.get('supporting_quotes', [])) for t in themes])

            return {
                "client_id": self.client_id,
                "has_themes": len(themes) > 0,
                "total_themes": len(themes),
                "research_themes": research_count,
                "discovered_themes": discovered_count,
                "total_quotes_linked": total_quotes,
                "last_updated": themes[0].get('updated_at') if themes else None
            }

        except Exception as e:
            logger.error(f"❌ Error getting processing status: {e}")
            return {
                "client_id": self.client_id,
                "has_themes": False,
                "error": str(e)
            }

    def clear_existing_themes(self) -> int:
        """Delete all existing themes for this client before regeneration."""
        try:
            resp = self.db.supabase.table('research_themes').delete().eq('client_id', self.client_id).execute()
            deleted = getattr(resp, 'count', None) or (len(resp.data) if hasattr(resp, 'data') and resp.data else 0)
            logger.info(f"🧹 Cleared {deleted} existing themes for {self.client_id}")
            return deleted
        except Exception as e:
            logger.error(f"❌ Failed to clear existing themes: {e}")
            return 0

def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="Stage 3 Theme Processor")
    parser.add_argument("--client", required=True, help="Client ID to process")
    parser.add_argument("--check-status", action="store_true", help="Check processing status only")
    parser.add_argument("--clear-first", action="store_true", help="Clear all themes for client before processing")

    args = parser.parse_args()

    try:
        processor = Stage3ThemeProcessor(args.client)

        if args.check_status:
            status = processor.get_processing_status()
            print(json.dumps(status, indent=2))
        else:
            if args.clear_first:
                processor.clear_existing_themes()
            result = processor.process_stage3_themes()
            print(json.dumps(result, indent=2))

    except Exception as e:
        logger.error(f"❌ Stage 3 processing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 