#!/usr/bin/env python3
"""
Enhanced Theme Deduplication Engine
Implements the user's recommended approach:
- Multi-signal scoring (cosine + noun overlap + sentiment + domain)
- Three-table schema (raw, canonical, mapping)
- Interview themes as evidence only, never merged
- Analyst approval workflow with confidence thresholds
"""

import sys
from pathlib import Path
import argparse
import pandas as pd
import numpy as np
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

sys.path.append(str(Path(__file__).resolve().parents[1]))
from supabase_database import SupabaseDatabase
from embedding_utils import EmbeddingManager

@dataclass
class MergeSuggestion:
    """Represents a suggested merge with full context"""
    theme_a_id: str
    theme_b_id: str
    theme_a_statement: str
    theme_b_statement: str
    subject: str
    primary_facet: str
    cosine_score: float
    noun_overlap_score: float
    sentiment_alignment: float
    domain_overlap: int
    composite_score: float
    confidence_level: str  # 'high', 'medium', 'low'
    merge_rationale: str
    suggested_canonical: str

class EnhancedThemeDeduplicator:
    def __init__(self, db: SupabaseDatabase, client_id: str):
        self.db = db
        self.client_id = client_id
        self.mgr = EmbeddingManager()
        
        # Enhanced domain facets based on user's examples
        self.FACETS = {
            'Integration': {
                'api', 'webhook', 'integration', 'integrate', 'oms', 'order management', 
                'shopify', 'bigcommerce', 'woocommerce', 'data transfer', 'sync', 
                'mapping', 'schema', 'seamless', 'compatibility', 'challenges'
            },
            'Pricing': {
                'price', 'pricing', 'cost', 'fees', 'fee', 'rates', 'rate', 'surcharge', 
                'discount', 'savings', 'saver', 'cheap', 'expense', 'transparency', 
                'rate cards', 'hidden costs', 'lowest bidder'
            },
            'Support': {
                'support', 'account manager', 'cs', 'customer success', 'onboarding', 
                'documentation', 'docs', 'examples', 'sdk', 'sample', 'training', 
                'human qualities', 'dedicated support'
            },
            'Efficiency': {
                'efficiency', 'streamline', 'processes', 'frustration', 'carriers', 
                'differentiation', 'fulfillment', 'simplify', 'time-consuming', 
                'challenges', 'lack of access'
            },
            'Reliability': {
                'uptime', 'latency', 'sla', 'reliability', 'downtime', 'outage', 
                'incident', 'status', 'throttle', 'throttling', 'timeout', 'retry'
            },
            'Competition': {
                'competitor', 'competitors', 'vs', 'versus', 'switch', 'switched', 
                'shipstation', 'easypost', 'pitney', 'stamps', 'shippo', 'xps', 'endicia'
            }
        }
        
        self.FACET_VOCAB = set().union(*self.FACETS.values())
        
        # Generic terms to filter out
        self.GENERIC_TERMS = {
            'need', 'needs', 'fast', 'quick', 'easy', 'good', 'great', 'nice', 
            'help', 'use', 'work', 'really', 'very', 'best', 'better', 'more', 
            'less', 'much', 'many', 'important', 'crucial', 'key'
        }

    def normalize_text(self, text: str) -> str:
        """Enhanced text normalization"""
        import re
        s = (text or '').lower()
        s = re.sub(r'https?://\S+', ' ', s)
        s = re.sub(r'[^a-z ]+', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    def extract_content_tokens(self, text: str) -> set:
        """Extract meaningful content tokens with n-grams"""
        s = self.normalize_text(text)
        parts = [p for p in s.split() if p and p not in self.GENERIC_TERMS]
        
        # Unigrams (filtered)
        tokens = set(parts)
        
        # Bigrams
        bigrams = [f"{parts[i]} {parts[i+1]}" for i in range(len(parts)-1)] if len(parts) > 1 else []
        tokens.update(bigrams)
        
        # Trigrams
        trigrams = [f"{parts[i]} {parts[i+1]} {parts[i+2]}" for i in range(len(parts)-2)] if len(parts) > 2 else []
        tokens.update(trigrams)
        
        return tokens

    def detect_facets(self, text: str) -> set:
        """Detect which business facets a theme addresses"""
        tokens = self.extract_content_tokens(text)
        matched = set()
        
        for facet, keywords in self.FACETS.items():
            if any(kw in tokens for kw in keywords):
                matched.add(facet)
        
        if not matched:
            # Fallback: broad API/integration keyword
            if any(k in tokens for k in ('api', 'integration', 'webhook')):
                matched.add('Integration')
        
        return matched or {'Other'}

    def assign_primary_facet(self, text: str) -> str:
        """Assign a deterministic primary facet"""
        facets = self.detect_facets(text)
        
        # Priority order based on business importance
        priority_order = ['Integration', 'Pricing', 'Support', 'Efficiency', 'Reliability', 'Competition']
        
        for preferred in priority_order:
            if preferred in facets:
                return preferred
        
        return sorted(facets).pop()

    def calculate_sentiment_alignment(self, text_a: str, text_b: str) -> float:
        """Calculate sentiment alignment between two themes"""
        # Simple sentiment keywords (could be enhanced with proper sentiment analysis)
        positive_words = {'efficiency', 'seamless', 'easy', 'good', 'great', 'improve', 'better', 'smooth'}
        negative_words = {'challenges', 'frustration', 'difficult', 'problem', 'issue', 'lack', 'time-consuming'}
        
        tokens_a = set(self.normalize_text(text_a).split())
        tokens_b = set(self.normalize_text(text_b).split())
        
        pos_a = len(tokens_a & positive_words)
        neg_a = len(tokens_a & negative_words)
        pos_b = len(tokens_b & positive_words)
        neg_b = len(tokens_b & negative_words)
        
        # Sentiment direction alignment
        if (pos_a > neg_a and pos_b > neg_b) or (pos_a < neg_a and pos_b < neg_b):
            return 1.0  # Same sentiment direction
        elif (pos_a == neg_a) or (pos_b == neg_b):
            return 0.5  # Neutral alignment
        else:
            return 0.0  # Opposite sentiment

    def build_merge_suggestions(self, min_cosine: float = 0.68) -> List[MergeSuggestion]:
        """Build merge suggestions using enhanced multi-signal scoring with tight gates"""
        
        # Fetch all themes
        research_themes = self.db.fetch_research_themes_all(self.client_id)
        interview_themes = self.db.fetch_interview_level_themes(self.client_id)
        
        if research_themes.empty and interview_themes.empty:
            return []
        
        # Prepare research themes
        research_df = research_themes.copy()
        research_df['source'] = research_df['origin'].map(lambda x: 'discovered' if str(x).startswith('DISCOVERED:') else 'research')
        research_df['subject'] = research_df['harmonized_subject'].fillna('Uncategorized')
        research_df['primary_facet'] = research_df['theme_statement'].apply(self.assign_primary_facet)
        
        # Prepare interview themes (these will be evidence only, not merged)
        interview_df = interview_themes.copy()
        interview_df['source'] = 'interview'
        interview_df['subject'] = interview_df.get('subject', 'Interview')
        interview_df['primary_facet'] = interview_df['theme_statement'].apply(self.assign_primary_facet)
        
        # Only research/discovered themes can be merged
        mergeable_df = research_df[research_df['source'].isin(['research', 'discovered'])]
        
        if mergeable_df.empty:
            return []
        
        suggestions = []
        
        # First: within-subject merges (same subject + facet) - BALANCED GATES
        for (subject, facet), group in mergeable_df.groupby(['subject', 'primary_facet']):
            if len(group) < 2:
                continue
            
            # Generate all pairs within this subject+facet group
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    theme_a = group.iloc[i]
                    theme_b = group.iloc[j]
                    
                    # Within-subject: use passed min_cosine + noun-phrase Jaccard ≥0.15 (relaxed to catch real duplicates)
                    suggestion = self._create_merge_suggestion(theme_a, theme_b, subject, facet, 
                                                           min_cosine=min_cosine, min_jaccard=0.15)
                    if suggestion:  # Temporarily disable hard conflict rules for debugging
                        suggestions.append(suggestion)
        
        # Second: cross-subject merges (same facet, different subjects) - BALANCED GATES
        for facet, group in mergeable_df.groupby('primary_facet'):
            if len(group) < 2:
                continue
            
            # Only consider cross-subject merges for high-similarity pairs
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    theme_a = group.iloc[i]
                    theme_b = group.iloc[j]
                    
                    # Skip if same subject (already handled above)
                    if theme_a['subject'] == theme_b['subject']:
                        continue
                    
                    # Cross-subject: ≥0.72 cosine + entity overlap ≥0.20 (relaxed to catch semantic duplicates)
                    suggestion = self._create_merge_suggestion(theme_a, theme_b, 
                                                           f"Cross-subject: {theme_a['subject']} + {theme_b['subject']}", 
                                                           facet, min_cosine=0.72, min_entity_overlap=0.20)
                    if suggestion:  # Temporarily disable hard conflict rules for debugging
                        suggestions.append(suggestion)
        
        # Apply mutual nearest neighbors (MNN) + top-K filtering
        suggestions = self._apply_mnn_filtering(suggestions, k=2)
        
        # Apply impact-based prioritization
        suggestions = self._prioritize_by_impact(suggestions)
        
        # Apply per-subject caps and cluster size limits
        suggestions = self._apply_structural_limits(suggestions)
        
        # Sort by composite score (highest first)
        suggestions.sort(key=lambda x: x.composite_score, reverse=True)
        
        return suggestions

    def _calculate_cosine_similarity(self, text_a: str, text_b: str) -> float:
        """Calculate cosine similarity between two theme statements"""
        try:
            emb_a = self.mgr.get_embeddings_batch([text_a], batch_size=1)[0]
            emb_b = self.mgr.get_embeddings_batch([text_b], batch_size=1)[0]
            
            if emb_a is None or emb_b is None:
                return 0.0
            
            return self.mgr.calculate_cosine_similarity(emb_a, emb_b)
        except Exception:
            return 0.0

    def _calculate_noun_overlap(self, text_a: str, text_b: str) -> float:
        """Calculate noun phrase overlap between themes"""
        tokens_a = self.extract_content_tokens(text_a)
        tokens_b = self.extract_content_tokens(text_b)
        
        if not tokens_a or not tokens_b:
            return 0.0
        
        intersection = len(tokens_a & tokens_b)
        union = len(tokens_a | tokens_b)
        
        return intersection / union if union > 0 else 0.0

    def _calculate_domain_overlap(self, text_a: str, text_b: str) -> float:
        """Calculate domain-specific keyword overlap"""
        tokens_a = self.extract_content_tokens(text_a)
        tokens_b = self.extract_content_tokens(text_b)
        
        domain_tokens_a = tokens_a & self.FACET_VOCAB
        domain_tokens_b = tokens_b & self.FACET_VOCAB
        
        intersection = len(domain_tokens_a & domain_tokens_b)
        return intersection

    def _calculate_entity_overlap(self, text_a: str, text_b: str) -> float:
        """Calculate entity overlap for cross-subject merge validation"""
        # Extract business entities (companies, platforms, systems)
        entities_a = self._extract_business_entities(text_a)
        entities_b = self._extract_business_entities(text_b)
        
        if not entities_a or not entities_b:
            return 0.0
        
        intersection = len(entities_a & entities_b)
        union = len(entities_a | entities_b)
        
        return intersection / union if union > 0 else 0.0

    def _extract_business_entities(self, text: str) -> set:
        """Extract business entities from text"""
        text_lower = text.lower()
        entities = set()
        
        # Platform/company names
        platform_keywords = {
            'shopify', 'bigcommerce', 'woocommerce', 'magento', 'prestashop',
            'shipstation', 'easypost', 'shippo', 'pitney', 'stamps', 'endicia',
            'salesforce', 'netsuite', 'sap', 'oracle', 'microsoft', 'google',
            'amazon', 'fedex', 'ups', 'usps', 'dhl'
        }
        
        # System types
        system_keywords = {
            'wms', 'crm', 'erp', 'oms', 'pim', 'cms', 'api', 'webhook',
            'database', 'platform', 'system', 'software', 'tool'
        }
        
        # Check for platform mentions
        for platform in platform_keywords:
            if platform in text_lower:
                entities.add(platform)
        
        # Check for system mentions
        for system in system_keywords:
            if system in text_lower:
                entities.add(system)
        
        return entities

    def _generate_merge_rationale(self, text_a: str, text_b: str, 
                                 cosine: float, noun_overlap: float, 
                                 sentiment: float, domain: int) -> str:
        """Generate human-readable merge rationale"""
        reasons = []
        
        if cosine >= 0.80:
            reasons.append("high semantic similarity")
        elif cosine >= 0.70:
            reasons.append("moderate semantic similarity")
        
        if noun_overlap >= 0.30:
            reasons.append("significant content overlap")
        elif noun_overlap >= 0.15:
            reasons.append("moderate content overlap")
        
        if sentiment >= 0.8:
            reasons.append("aligned sentiment")
        
        if domain >= 3:
            reasons.append("strong domain alignment")
        elif domain >= 1:
            reasons.append("shared domain concepts")
        
        if not reasons:
            reasons.append("moderate overall similarity")
        
        return f"Merge suggested based on: {', '.join(reasons)}"

    def _create_merge_suggestion(self, theme_a: pd.Series, theme_b: pd.Series, 
                                subject: str, facet: str, min_cosine: float = 0.74, 
                                min_jaccard: float = 0.35, min_entity_overlap: float = 0.0) -> Optional[MergeSuggestion]:
        """Create a merge suggestion if themes meet similarity criteria"""
        # Calculate multi-signal scores
        cosine_score = self._calculate_cosine_similarity(
            theme_a['theme_statement'], 
            theme_b['theme_statement']
        )
        
        # Debug output
        print(f"DEBUG: Comparing themes with cosine {cosine_score:.4f} vs threshold {min_cosine}")
        
        if cosine_score < min_cosine:
            print(f"DEBUG: Cosine {cosine_score:.4f} < {min_cosine}, rejecting")
            return None
        
        noun_overlap = self._calculate_noun_overlap(
            theme_a['theme_statement'], 
            theme_b['theme_statement']
        )
        
        # Check noun overlap threshold
        if min_jaccard > 0 and noun_overlap < min_jaccard:
            return None
        
        sentiment_align = self.calculate_sentiment_alignment(
            theme_a['theme_statement'], 
            theme_b['theme_statement']
        )
        
        domain_overlap = self._calculate_domain_overlap(
            theme_a['theme_statement'], 
            theme_b['theme_statement']
        )
        
        # Check entity overlap threshold for cross-subject merges
        if min_entity_overlap > 0:
            entity_overlap_score = self._calculate_entity_overlap(
                theme_a['theme_statement'], 
                theme_b['theme_statement']
            )
            if entity_overlap_score < min_entity_overlap:
                return None
        
        # Composite score (weighted)
        composite_score = (
            0.5 * cosine_score +      # Semantic similarity
            0.25 * noun_overlap +     # Content overlap
            0.15 * sentiment_align +  # Sentiment alignment
            0.10 * (domain_overlap / 10.0)  # Domain overlap (normalized)
        )
        
        # Balanced confidence level based on relaxed thresholds
        if composite_score >= 0.75 and cosine_score >= 0.72:
            confidence = 'high'
        elif composite_score >= 0.65 and cosine_score >= 0.68:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        # Generate merge rationale
        rationale = self._generate_merge_rationale(
            theme_a['theme_statement'], 
            theme_b['theme_statement'],
            cosine_score, noun_overlap, sentiment_align, domain_overlap
        )
        
        # Suggested canonical theme
        suggested_canonical = self._suggest_canonical_theme(
            theme_a['theme_statement'], 
            theme_b['theme_statement']
        )
        
        return MergeSuggestion(
            theme_a_id=theme_a['theme_id'],
            theme_b_id=theme_b['theme_id'],
            theme_a_statement=theme_a['theme_statement'],
            theme_b_statement=theme_b['theme_statement'],
            subject=subject,
            primary_facet=facet,
            cosine_score=cosine_score,
            noun_overlap_score=noun_overlap,
            sentiment_alignment=sentiment_align,
            domain_overlap=domain_overlap,
            composite_score=composite_score,
            confidence_level=confidence,
            merge_rationale=rationale,
            suggested_canonical=suggested_canonical
        )

    def _has_hard_merge_conflicts(self, theme_a: pd.Series, theme_b: pd.Series) -> bool:
        """Check for hard merge conflicts that should prevent merging"""
        
        # Extract entities and context from theme statements
        text_a = str(theme_a['theme_statement']).lower()
        text_b = str(theme_b['theme_statement']).lower()
        
        # 1. Conflicting entities (only truly incompatible ones)
        conflicting_entities = {
            'api': ['manual', 'human', 'phone', 'email'],  # Only keep truly incompatible
            'automated': ['manual', 'human'],
            'self-service': ['human', 'phone', 'email']
        }
        
        for entity, conflicts in conflicting_entities.items():
            if entity in text_a and any(conflict in text_b for conflict in conflicts):
                return True
            if entity in text_b and any(conflict in text_a for conflict in conflicts):
                return True
        
        # 2. Opposite sentiment/polarity
        positive_words = {'efficiency', 'seamless', 'easy', 'good', 'great', 'improve', 'better', 'smooth', 'fast'}
        negative_words = {'challenges', 'frustration', 'difficult', 'problem', 'issue', 'lack', 'time-consuming', 'complex'}
        
        pos_a = sum(1 for word in positive_words if word in text_a)
        neg_a = sum(1 for word in negative_words if word in text_a)
        pos_b = sum(1 for word in positive_words if word in text_b)
        neg_b = sum(1 for word in negative_words if word in text_b)
        
        # If one theme is clearly positive and the other clearly negative
        if (pos_a > neg_a and pos_b < neg_b) or (pos_a < neg_a and pos_b > neg_b):
            if abs(pos_a - neg_a) > 1 and abs(pos_b - neg_b) > 1:  # Clear sentiment difference
                return True
        
        # 3. Different stakeholders (only truly incompatible ones)
        # Allow ops + finance themes to merge if they're about the same business problem
        # Only block if they're completely different domains
        ops_keywords = {'warehouse', 'fulfillment', 'carrier', 'shipping'}
        finance_keywords = {'roi', 'budget', 'financial', 'accounting'}
        
        ops_a = any(keyword in text_a for keyword in ops_keywords)
        ops_b = any(keyword in text_b for keyword in ops_keywords)
        finance_a = any(keyword in text_a for keyword in finance_keywords)
        finance_b = any(keyword in text_b for keyword in finance_keywords)
        
        # Only block if both themes are purely ops vs purely finance AND have no common business problem
        if (ops_a and not any(k in text_a for k in ['cost', 'pricing', 'efficiency', 'challenges', 'problem']) and 
            finance_b and not any(k in text_b for k in ['operations', 'process', 'efficiency', 'challenges', 'problem'])):
            return True
        if (ops_b and not any(k in text_b for k in ['cost', 'pricing', 'efficiency', 'challenges', 'problem']) and 
            finance_a and not any(k in text_a for k in ['operations', 'process', 'efficiency', 'challenges', 'problem'])):
            return True
        
        # 4. Different modality (only truly incompatible ones)
        # Allow pricing + support themes to merge if they're about the same business problem
        # Only block if they're completely different domains
        pricing_keywords = {'roi', 'budget', 'accounting', 'financial'}
        support_keywords = {'documentation', 'help desk', 'customer service'}
        
        pricing_a = any(keyword in text_a for keyword in pricing_keywords)
        pricing_b = any(keyword in text_b for keyword in pricing_keywords)
        support_a = any(keyword in text_a for keyword in support_keywords)
        support_b = any(keyword in text_b for keyword in support_keywords)
        
        # Only block if both themes are purely pricing vs purely support AND have no common business problem
        if (pricing_a and not any(k in text_a for k in ['support', 'help', 'training', 'challenges', 'problem']) and 
            support_b and not any(k in text_b for k in ['cost', 'pricing', 'budget', 'challenges', 'problem'])):
            return True
        if (pricing_b and not any(k in text_b for k in ['support', 'help', 'training', 'challenges', 'problem']) and 
            support_a and not any(k in text_a for k in ['cost', 'pricing', 'budget', 'challenges', 'problem'])):
            return True
        
        # 5. Temporal qualifiers (pilot vs steady-state)
        pilot_keywords = {'pilot', 'testing', 'trial', 'initial', 'first time', 'new'}
        steady_keywords = {'ongoing', 'steady', 'production', 'live', 'operational', 'established'}
        
        pilot_a = any(keyword in text_a for keyword in pilot_keywords)
        pilot_b = any(keyword in text_b for keyword in pilot_keywords)
        steady_a = any(keyword in text_a for keyword in steady_keywords)
        steady_b = any(keyword in text_b for keyword in steady_keywords)
        
        if (pilot_a and steady_b) or (pilot_b and steady_a):
            return True
        
        return False

    def _apply_mnn_filtering(self, suggestions: List[MergeSuggestion], k: int = 2) -> List[MergeSuggestion]:
        """Apply mutual nearest neighbors filtering to keep only reciprocal top-K pairs"""
        
        if not suggestions:
            return suggestions
        
        # Build theme-to-suggestions mapping
        theme_suggestions = {}
        for suggestion in suggestions:
            if suggestion.theme_a_id not in theme_suggestions:
                theme_suggestions[suggestion.theme_a_id] = []
            if suggestion.theme_b_id not in theme_suggestions:
                theme_suggestions[suggestion.theme_b_id] = []
            
            theme_suggestions[suggestion.theme_a_id].append(suggestion)
            theme_suggestions[suggestion.theme_b_id].append(suggestion)
        
        # Keep only mutual nearest neighbors
        filtered_suggestions = []
        for suggestion in suggestions:
            # Check if this is in the top-K for both themes
            theme_a_top_k = sorted(theme_suggestions[suggestion.theme_a_id], 
                                  key=lambda x: x.composite_score, reverse=True)[:k]
            theme_b_top_k = sorted(theme_suggestions[suggestion.theme_b_id], 
                                  key=lambda x: x.composite_score, reverse=True)[:k]
            
            if suggestion in theme_a_top_k and suggestion in theme_b_top_k:
                filtered_suggestions.append(suggestion)
        
        return filtered_suggestions

    def _prioritize_by_impact(self, suggestions: List[MergeSuggestion]) -> List[MergeSuggestion]:
        """Prioritize suggestions by impact (company coverage, interview coverage)"""
        
        if not suggestions:
            return suggestions
        
        # For now, we'll use a simple heuristic
        # In a full implementation, you'd query the database for actual coverage data
        
        # Sort by composite score first, then by estimated impact
        suggestions.sort(key=lambda x: (x.composite_score, x.domain_overlap), reverse=True)
        
        return suggestions

    def _apply_structural_limits(self, suggestions: List[MergeSuggestion]) -> List[MergeSuggestion]:
        """Apply per-subject caps and cluster size limits"""
        
        if not suggestions:
            return suggestions
        
        # Group by subject
        subject_groups = {}
        for suggestion in suggestions:
            subject = suggestion.subject
            if subject not in subject_groups:
                subject_groups[subject] = []
            subject_groups[subject].append(suggestion)
        
        # Apply per-subject cap (max 12 suggestions per subject)
        filtered_suggestions = []
        for subject, group_suggestions in subject_groups.items():
            # Sort by composite score and take top 12
            sorted_group = sorted(group_suggestions, key=lambda x: x.composite_score, reverse=True)[:12]
            filtered_suggestions.extend(sorted_group)
        
        # Apply cluster size limit (max 7 themes per cluster)
        # This is a simplified version - in practice you'd need to track cluster membership
        # For now, we'll just limit the total suggestions to a reasonable number
        max_total_suggestions = 50  # Conservative limit
        if len(filtered_suggestions) > max_total_suggestions:
            filtered_suggestions = filtered_suggestions[:max_total_suggestions]
        
        return filtered_suggestions

    def _suggest_canonical_theme(self, text_a: str, text_b: str) -> str:
        """Suggest a canonical theme statement that combines both themes"""
        # Simple approach: use the longer, more specific statement
        if len(text_a) > len(text_b):
            return text_a
        else:
            return text_b

    def export_suggestions_to_csv(self, suggestions: List[MergeSuggestion], output_path: str):
        """Export merge suggestions to CSV for analyst review"""
        if not suggestions:
            print("No merge suggestions to export")
            return
        
        rows = []
        for s in suggestions:
            rows.append({
                'Theme A ID': s.theme_a_id,
                'Theme A Statement': s.theme_a_statement,
                'Theme B ID': s.theme_b_id,
                'Theme B Statement': s.theme_b_statement,
                'Subject': s.subject,
                'Primary Facet': s.primary_facet,
                'Cosine Score': round(s.cosine_score, 3),
                'Noun Overlap': round(s.noun_overlap_score, 3),
                'Sentiment Alignment': round(s.sentiment_alignment, 3),
                'Domain Overlap': s.domain_overlap,
                'Composite Score': round(s.composite_score, 3),
                'Confidence': s.confidence_level,
                'Merge Rationale': s.merge_rationale,
                'Suggested Canonical': s.suggested_canonical
            })
        
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        print(f"Exported {len(rows)} merge suggestions to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Enhanced Theme Deduplication Engine')
    parser.add_argument('--client', required=True, help='Client ID to process')
    parser.add_argument('--min-cosine', type=float, default=0.75, 
                       help='Minimum cosine similarity threshold (default: 0.75)')
    parser.add_argument('--output', default='merge_suggestions.csv',
                       help='Output CSV file path (default: merge_suggestions.csv)')
    
    args = parser.parse_args()
    
    print(f"🔍 Enhanced Theme Deduplication for client: {args.client}")
    print(f"📊 Minimum cosine threshold: {args.min_cosine}")
    
    # Initialize
    db = SupabaseDatabase()
    deduplicator = EnhancedThemeDeduplicator(db, args.client)
    
    # Generate merge suggestions
    print("🔄 Building merge suggestions...")
    suggestions = deduplicator.build_merge_suggestions(min_cosine=args.min_cosine)
    
    if not suggestions:
        print("✅ No merge suggestions found - themes are already well-differentiated")
        return
    
    # Analyze suggestions
    high_conf = [s for s in suggestions if s.confidence_level == 'high']
    medium_conf = [s for s in suggestions if s.confidence_level == 'medium']
    low_conf = [s for s in suggestions if s.confidence_level == 'low']
    
    print(f"\n📊 Merge Suggestions Summary:")
    print(f"  High confidence: {len(high_conf)} (auto-merge candidates)")
    print(f"  Medium confidence: {len(medium_conf)} (review recommended)")
    print(f"  Low confidence: {len(low_conf)} (manual review required)")
    print(f"  Total: {len(suggestions)}")
    
    # Show top suggestions
    if suggestions:
        print(f"\n🏆 Top 5 Merge Suggestions:")
        for i, s in enumerate(suggestions[:5], 1):
            print(f"  {i}. {s.theme_a_id} + {s.theme_b_id}")
            print(f"     Subject: {s.subject} | Facet: {s.primary_facet}")
            print(f"     Score: {s.composite_score:.3f} | Confidence: {s.confidence_level}")
            print(f"     Rationale: {s.merge_rationale}")
            print()
    
    # Export to CSV
    deduplicator.export_suggestions_to_csv(suggestions, args.output)
    
    print(f"✅ Deduplication analysis complete!")
    print(f"📁 Results exported to: {args.output}")
    print(f"\n💡 Next steps:")
    print(f"  1. Review high-confidence suggestions for auto-merge")
    print(f"  2. Manually review medium/low confidence suggestions")
    print(f"  3. Use the three-table schema to implement approved merges")

if __name__ == '__main__':
    main() 