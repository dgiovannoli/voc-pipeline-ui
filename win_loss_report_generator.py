#!/usr/bin/env python3
"""
Win-Loss Report Generator
A purpose-built system that transforms enhanced Stage 1 & 2 data into analyst-ready spreadsheets.
Focuses on win-loss themes, competitive intelligence, and comprehensive quote curation.
"""

import os
import sys
import logging
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import threading
from collections import defaultdict, Counter

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import our modules
from supabase_database import SupabaseDatabase

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Progress tracking for UI
winloss_progress_data = {"completed_steps": 0, "total_steps": 0, "current_step": "", "themes_generated": 0}
winloss_progress_lock = threading.Lock()

class WinLossReportGenerator:
    """
    Generate analyst-ready win-loss curation spreadsheets from enhanced Stage 1 & 2 data.
    
    Key Features:
    - Uses harmonized subjects as natural theme categories
    - Applies Stage 4 quality gates for high-quality themes
    - Creates analyst curation workflow with Include/Exclude capabilities
    - Generates multi-tab Excel reports for comprehensive analysis
    """
    
    def __init__(self, client_id: str = "default", include_research_themes: bool = True, research_alignment_min: float = 0.15):
        self.client_id = client_id
        self.db = SupabaseDatabase()
        
        # Base Quality Gates (will be adjusted dynamically)
        self.base_min_companies_per_theme = 2
        self.base_min_quotes_per_theme = 2     
        self.base_min_impact_threshold = 3
        self.coherence_threshold = 0.7    # Minimum percentage for narrative coherence (e.g., 70% positive sentiment for strength)
        
        # Adaptive thresholds (set after data loading)
        self.min_companies_per_theme = 2
        self.min_quotes_per_theme = 3
        self.min_impact_threshold = 3
        
        # Theme categorization
        self.strength_criteria = {"sentiment": "positive", "deal_status": "closed won"}
        self.weakness_criteria = {"sentiment": "negative", "deal_status": "closed lost"}
        
        # LLM setup for theme statement generation
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY not found - theme statement generation will use fallback method")
        
        # Hybrid theme generation flags
        self.include_research_themes = include_research_themes
        # Minimum fraction (0-1) of quotes in a group that should align to the primary research question
        self.research_alignment_min = research_alignment_min
        
        logger.info(f"✅ WinLossReportGenerator initialized for client: {client_id}")
    
    def _set_adaptive_quality_gates(self, quotes_data: pd.DataFrame):
        """
        Set adaptive quality gates based on dataset characteristics.
        Ensures we generate useful themes even with smaller datasets.
        """
        company_col = 'company' if 'company' in quotes_data.columns else 'company_name'
        total_quotes = len(quotes_data)
        total_companies = quotes_data[company_col].nunique()
        avg_quotes_per_company = total_quotes / max(total_companies, 1)
        
        # Adaptive company threshold
        if total_companies == 1:
            self.min_companies_per_theme = 1  # Single company case
            logger.info("📊 Adaptive Mode: Single company detected - allowing single-company themes")
        elif total_companies <= 3:
            self.min_companies_per_theme = 2  # Small multi-company
            logger.info("📊 Adaptive Mode: Small multi-company dataset - requiring 2+ companies per theme")
        else:
            self.min_companies_per_theme = self.base_min_companies_per_theme
        
        # Adaptive quotes threshold
        if avg_quotes_per_company < 3:
            self.min_quotes_per_theme = 2
            logger.info(f"📊 Adaptive Mode: Low quote density - requiring {self.min_quotes_per_theme}+ quotes per theme (fixed minimum)")
        else:
            self.min_quotes_per_theme = self.base_min_quotes_per_theme
        
        # Adaptive impact threshold
        avg_impact = quotes_data['impact_score'].mean()
        if avg_impact < 3.5:
            self.min_impact_threshold = max(2.5, avg_impact - 0.5)
            logger.info(f"📊 Adaptive Mode: Lower average impact - requiring {self.min_impact_threshold:.1f}+ impact score")
        else:
            self.min_impact_threshold = self.base_min_impact_threshold
        
        logger.info(f"🎯 Quality Gates Set: {self.min_companies_per_theme} companies, {self.min_quotes_per_theme} quotes, {self.min_impact_threshold:.1f} impact")
    
    def generate_analyst_report(self) -> Dict[str, Any]:
        """
        Main method to generate the complete analyst curation report.
        
        Returns:
            Dict containing report data and metadata
        """
        with winloss_progress_lock:
            winloss_progress_data.update({
                "completed_steps": 0,
                "total_steps": 6,
                "current_step": "Initializing analysis...",
                "themes_generated": 0
            })
        
        try:
            logger.info(f"🚀 Starting win-loss report generation for client: {self.client_id}")
            
            # Step 1: Load enhanced data from single table
            self._update_progress(1, "Loading enhanced Stage 1 & 2 data...")
            quotes_data = self._load_enhanced_data()
            
            if quotes_data.empty:
                logger.warning(f"⚠️ No data found for client {self.client_id}")
                return {"success": False, "error": "No data found for client"}
            
            logger.info(f"📊 Loaded {len(quotes_data)} quotes from enhanced single table")
            
            # Step 1.5: Set adaptive quality gates based on dataset characteristics
            self._set_adaptive_quality_gates(quotes_data)
            
            # Step 2: Group quotes by harmonized subjects
            self._update_progress(2, "Grouping quotes by harmonized subjects...")
            subject_groups = self._group_by_harmonized_subjects(quotes_data)
            
            # Step 3: Identify potential theme clusters
            self._update_progress(3, "Identifying potential theme clusters...")
            theme_clusters = self._identify_theme_clusters(subject_groups)
            
            # Optionally add research-seeded clusters and deduplicate
            if self.include_research_themes:
                self._update_progress(3, "Generating research-seeded theme candidates...")
                research_clusters = self._generate_research_seeded_clusters(quotes_data)
                theme_clusters.extend(research_clusters)
                theme_clusters = self._merge_and_dedupe_theme_clusters(theme_clusters)
            
            # Step 4: Apply Stage 4 quality gates
            self._update_progress(4, "Applying quality gates for high-quality themes...")
            validated_themes = self._apply_quality_gates(theme_clusters)
            
            # Step 5: Generate theme statements
            self._update_progress(5, "Generating executive-ready theme statements...")
            final_themes = self._generate_theme_statements(validated_themes)
            
            # Step 6: Prepare analyst curation data
            self._update_progress(6, "Preparing analyst curation spreadsheet data...")
            curation_data = self._prepare_curation_data(final_themes, quotes_data)
            
            with winloss_progress_lock:
                winloss_progress_data["themes_generated"] = len(final_themes)
            
            logger.info(f"✅ Generated {len(final_themes)} high-quality themes for analyst curation")
            
            return {
                "success": True,
                "themes": final_themes,
                "curation_data": curation_data,
                "metadata": {
                    "client_id": self.client_id,
                    "generated_at": datetime.now().isoformat(),
                    "total_quotes": len(quotes_data),
                    "total_themes": len(final_themes),
                    "companies_analyzed": quotes_data['company'].nunique() if 'company' in quotes_data.columns else (quotes_data['company_name'].nunique() if 'company_name' in quotes_data.columns else 0),
                    "harmonized_subjects": list(quotes_data['harmonized_subject'].dropna().unique()) if 'harmonized_subject' in quotes_data.columns else []
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating win-loss report: {e}")
            return {"success": False, "error": str(e)}
    
    def _update_progress(self, step: int, message: str):
        """Update progress tracking for UI"""
        with winloss_progress_lock:
            winloss_progress_data.update({
                "completed_steps": step,
                "current_step": message
            })
        logger.info(f"Step {step}/6: {message}")
    
    def _load_enhanced_data(self) -> pd.DataFrame:
        """
        Load enhanced Stage 1 & 2 data from the single table.
        
        Returns:
            DataFrame with all quotes and their enhanced metadata
        """
        try:
            # Get enhanced data with all Stage 2 analysis
            df = self.db.get_stage1_data_responses(client_id=self.client_id)
            
            if df.empty:
                return df
            
            # Filter for analyzed quotes (those with Stage 2 analysis)
            analyzed_df = df[df['sentiment'].notna() & df['impact_score'].notna()].copy()
            
            logger.info(f"📈 Found {len(analyzed_df)} analyzed quotes out of {len(df)} total quotes")
            
            # Parse research question alignment data
            if 'research_question_alignment' in analyzed_df.columns:
                analyzed_df = self._parse_research_question_alignment(analyzed_df)
                logger.info(f"🔍 Parsed research question alignment for {len(analyzed_df)} quotes")
            
            # Apply data quality filtering
            cleaned_df = self._apply_data_quality_filtering(analyzed_df)
            
            logger.info(f"🧹 Data quality filtering: {len(analyzed_df)} → {len(cleaned_df)} quotes (removed {len(analyzed_df) - len(cleaned_df)} questions/non-verbatim content)")
            
            return cleaned_df
            
        except Exception as e:
            logger.error(f"❌ Error loading enhanced data: {e}")
            return pd.DataFrame()
    
    def _parse_research_question_alignment(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse the research_question_alignment JSON data into usable format.
        
        Args:
            df: DataFrame with research_question_alignment column
            
        Returns:
            DataFrame with parsed research question data
        """
        import json
        
        def parse_alignment(alignment_str):
            if pd.isna(alignment_str) or alignment_str == '':
                return []
            try:
                if isinstance(alignment_str, str):
                    return json.loads(alignment_str)
                return alignment_str
            except (json.JSONDecodeError, TypeError):
                return []
        
        # Parse research question alignment
        df['parsed_research_alignment'] = df['research_question_alignment'].apply(parse_alignment)

        # Use DB question as source of truth when available
        db_question_col = 'question' if 'question' in df.columns else None
        def choose_primary(alignment_list, db_q):
            if isinstance(db_q, str) and db_q.strip():
                return db_q
            return alignment_list[0]['question_text'] if alignment_list and len(alignment_list) > 0 else "No research question aligned"
        df['primary_research_question'] = df.apply(
            lambda row: choose_primary(row['parsed_research_alignment'], row[db_question_col]) if db_question_col else (
                row['parsed_research_alignment'][0]['question_text'] if row['parsed_research_alignment'] else "No research question aligned"
            ), axis=1
        )

        # Extract research question indices
        df['research_question_indices'] = df['parsed_research_alignment'].apply(
            lambda x: [item['question_index'] for item in x] if x else []
        )

        return df
    
    def _analyze_theme_research_alignment(self, quotes: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze research question alignment patterns within a theme.
        
        Args:
            quotes: DataFrame of quotes for a theme
            
        Returns:
            Dictionary with research alignment analysis
        """
        if 'primary_research_question' not in quotes.columns:
            return {
                'primary_question': "No research question data available",
                'question_coverage': [],
                'alignment_confidence': 0.0
            }
        
        # Get unique research questions for this theme
        research_questions = quotes['primary_research_question'].value_counts()
        
        if research_questions.empty:
            return {
                'primary_question': "No research question data available",
                'question_coverage': [],
                'alignment_confidence': 0.0
            }
        
        # Primary research question (most common)
        primary_question = research_questions.index[0]
        
        # Calculate alignment confidence (percentage of quotes with the primary question)
        alignment_confidence = (research_questions.iloc[0] / len(quotes)) * 100
        
        # Get all research questions covered
        question_coverage = research_questions.to_dict()
        
        return {
            'primary_question': primary_question,
            'question_coverage': question_coverage,
            'alignment_confidence': alignment_confidence
        }
    
    def _group_by_harmonized_subjects(self, quotes_data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Group quotes by their harmonized subjects for theme analysis.
        
        Args:
            quotes_data: DataFrame with enhanced quote data
            
        Returns:
            Dictionary mapping harmonized subjects to their quotes
        """
        subject_groups = {}
        
        # Group by harmonized_subject, handling missing values
        harmonized_col = 'harmonized_subject'
        if harmonized_col not in quotes_data.columns:
            logger.warning("⚠️ harmonized_subject column not found, using 'subject' instead")
            harmonized_col = 'subject'
        
        for subject, group in quotes_data.groupby(harmonized_col, dropna=True):
            if pd.isna(subject) or subject == '':
                continue
            subject_groups[subject] = group.copy()
        
        logger.info(f"📊 Grouped quotes into {len(subject_groups)} harmonized subjects")
        return subject_groups
    
    def _identify_theme_clusters(self, subject_groups: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """
        Identify potential theme clusters within each harmonized subject.
        
        Args:
            subject_groups: Dictionary of harmonized subjects to quotes
            
        Returns:
            List of potential theme clusters
        """
        clusters = []
        
        for subject, quotes in subject_groups.items():
            logger.info(f"🔍 Analyzing {len(quotes)} quotes in '{subject}' category")
            
            # Enhanced theme categorization logic
            # Addresses feedback: "mixed signal theme type but positive sentiment. This is confusing."
            
            theme_clusters = self._categorize_theme_clusters(subject, quotes)
            clusters.extend(theme_clusters)
        
        logger.info(f"🎯 Identified {len(clusters)} potential theme clusters")
        return clusters
    
    def _apply_quality_gates(self, theme_clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply Stage 4 quality gates to validate themes.
        
        Args:
            theme_clusters: List of potential theme clusters
            
        Returns:
            List of validated themes that passed all quality gates
        """
        validated_themes = []
        
        logger.info(f"🚪 Evaluating {len(theme_clusters)} theme clusters against quality gates...")
        
        for cluster in theme_clusters:
            quotes = cluster["quotes"]
            theme_type = cluster["theme_type"]
            subject = cluster["harmonized_subject"]
            
            logger.info(f"\n📋 Evaluating theme: '{subject}' ({theme_type})")
            logger.info(f"   📊 Quote count: {len(quotes)}")
            
            # Quality Gate 1: Cross-Company Validation
            company_col = 'company' if 'company' in quotes.columns else 'company_name'
            unique_companies = quotes[company_col].nunique()
            logger.info(f"   🏢 Company count: {unique_companies} (need {self.min_companies_per_theme})")
            
            if unique_companies < self.min_companies_per_theme:
                logger.info(f"   ❌ Gate 1 FAILED: Cross-company validation")
                continue
            else:
                logger.info(f"   ✅ Gate 1 PASSED: Cross-company validation")
            
            # Quality Gate 2: Evidence Significance
            # Count at most one quote per company (diminishing returns)
            quotes_dedup = quotes.drop_duplicates(subset=[company_col], keep='first')
            effective_quote_count = len(quotes_dedup)
            logger.info(f"   📝 Effective quotes (1/company): {effective_quote_count} (need {self.min_quotes_per_theme})")
            if effective_quote_count < self.min_quotes_per_theme:
                logger.info(f"   ❌ Gate 2 FAILED: Evidence significance")
                continue
            else:
                logger.info(f"   ✅ Gate 2 PASSED: Evidence significance")
            
            # Quality Gate 3: Impact Threshold
            avg_impact = quotes['impact_score'].mean()
            logger.info(f"   📈 Average impact: {avg_impact:.1f} (need {self.min_impact_threshold:.1f})")
            if avg_impact < self.min_impact_threshold:
                logger.info(f"   ❌ Gate 3 FAILED: Impact threshold")
                continue
            else:
                logger.info(f"   ✅ Gate 3 PASSED: Impact threshold")
            
            # Quality Gate 4: Narrative Coherence (for strength/weakness themes)
            sentiment_coherence = None
            if theme_type in ["strength", "weakness"]:
                expected_sentiment = "positive" if theme_type == "strength" else "negative"
                sentiment_coherence = (quotes['sentiment'] == expected_sentiment).mean()
                logger.info(f"   🎭 Sentiment coherence: {sentiment_coherence:.1%} (need {self.coherence_threshold:.1%})")
                
                if sentiment_coherence < self.coherence_threshold:
                    logger.info(f"   ❌ Gate 4 FAILED: Narrative coherence")
                    continue
                else:
                    logger.info(f"   ✅ Gate 4 PASSED: Narrative coherence")
            else:
                logger.info(f"   ⏭️  Gate 4 SKIPPED: Mixed signal theme")
            
            # Passed all gates - add validation metrics
            quality_score = self._calculate_quality_score(quotes_dedup, theme_type)
            company_distribution = self._analyze_company_distribution(quotes)
            
            cluster["validation_metrics"] = {
                "companies_count": unique_companies,
                "quotes_count": effective_quote_count,
                "avg_impact_score": avg_impact,
                "sentiment_coherence": sentiment_coherence,
                "quality_score": quality_score,
                "company_distribution": company_distribution
            }
            
            validated_themes.append(cluster)
            logger.info(f"   🎉 THEME VALIDATED with quality score: {quality_score}")
        
        logger.info(f"\n🎯 Final Result: {len(validated_themes)} themes passed quality validation out of {len(theme_clusters)} candidates")
        return validated_themes
    
    def _calculate_quality_score(self, quotes: pd.DataFrame, theme_type: str) -> float:
        """
        Calculate enhanced quality score using Stage 4 methodology.
        
        Updated weighting:
        - Company Coverage: 45%
        - Evidence Quality (avg impact): 25% 
        - Quote Volume (1/company): 20% (reduced priority)
        - Theme Coherence: 10%
        """
        score = 0.0
        
        # 1. Company Coverage (40% weight) - Stage 4 methodology
        company_col = 'company' if 'company' in quotes.columns else 'company_name'
        unique_companies = quotes[company_col].nunique()
        
        # Company score upweighted to 4.5/10
        company_score = min(unique_companies / 4.0, 1.0) * 4.5
        score += company_score
        
        # 2. Evidence Quality (30% weight)
        avg_impact = quotes['impact_score'].mean()
        evidence_score = (avg_impact / 5.0) * 2.5  # 0-2.5 points (25%)
        score += evidence_score
        
        # 3. Quote Volume (20% weight) - reduced priority
        # Count quotes effectively as 1 per company (input already deduped upstream)
        quote_count = len(quotes)
        volume_score = min(quote_count / 10.0, 1.0) * 2.0  # 0-2 points (20%)
        score += volume_score
        
        # 4. Theme Coherence (10% weight)
        coherence_score = 0.0
        if theme_type in ["strength", "weakness"]:
            expected_sentiment = "positive" if theme_type == "strength" else "negative"
            consistency = (quotes['sentiment'] == expected_sentiment).mean()
            coherence_score = consistency * 1.0  # 0-1 points (10%)
        else:
            # For mixed signals, score based on how mixed they actually are
            sentiment_variety = quotes['sentiment'].nunique()
            coherence_score = min(sentiment_variety / 3.0, 1.0) * 1.0
        
        score += coherence_score
        return round(score, 2)
    
    def _analyze_company_distribution(self, quotes: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze how quotes are distributed across companies.
        Implements Stage 4 company diversity analysis.
        """
        company_col = 'company' if 'company' in quotes.columns else 'company_name'
        company_counts = quotes[company_col].value_counts()
        
        if len(company_counts) == 0:
            return {
                "total_companies": 0,
                "quote_distribution": {},
                "max_company_percentage": 0,
                "bias_warning": False,
                "company_balance_score": 0.0,
                "distribution_summary": "No companies found"
            }
        
        max_company_percentage = (company_counts.iloc[0] / len(quotes)) * 100
        bias_warning = max_company_percentage > 60  # Single company >60% is bias
        
        return {
            "total_companies": len(company_counts),
            "quote_distribution": company_counts.to_dict(),
            "max_company_percentage": round(max_company_percentage, 1),
            "bias_warning": bias_warning,
            "company_balance_score": self._calculate_balance_score(company_counts),
            "distribution_summary": self._create_distribution_summary(company_counts)
        }
    
    def _calculate_balance_score(self, company_counts: pd.Series) -> float:
        """Calculate how balanced the company representation is (0-1 scale)"""
        if len(company_counts) <= 1:
            return 0.0
        
        # Perfect balance = all companies have equal quotes
        total_quotes = company_counts.sum()
        ideal_per_company = total_quotes / len(company_counts)
        
        # Calculate variance from ideal distribution
        variance = sum((count - ideal_per_company) ** 2 for count in company_counts) / len(company_counts)
        max_variance = ideal_per_company ** 2  # Maximum possible variance
        
        # Convert to balance score (1.0 = perfect balance, 0.0 = maximum imbalance)
        balance_score = max(0.0, 1.0 - (variance / max_variance))
        return round(balance_score, 2)
    
    def _create_distribution_summary(self, company_counts: pd.Series) -> str:
        """Create human-readable distribution summary"""
        if len(company_counts) == 0:
            return "No companies"
        elif len(company_counts) == 1:
            return f"Single company: {company_counts.index[0]} ({company_counts.iloc[0]} quotes)"
        else:
            # Show top companies
            top_3 = company_counts.head(3)
            summary_parts = []
            for company, count in top_3.items():
                summary_parts.append(f"{company}({count})")
            
            if len(company_counts) > 3:
                summary_parts.append(f"+{len(company_counts) - 3} more")
            
            return f"{len(company_counts)} companies: " + ", ".join(summary_parts)
    
    def _apply_data_quality_filtering(self, quotes_data: pd.DataFrame) -> pd.DataFrame:
        """
        Filter out questions and non-verbatim content from quotes.
        Addresses feedback: "this is a question not a verbatim quote"
        """
        if quotes_data.empty:
            return quotes_data
        
        original_count = len(quotes_data)
        filtered_data = quotes_data.copy()
        
        # Define patterns that indicate questions or non-verbatim content
        question_patterns = [
            r'^If\s+',                    # "If Supio created their own..."
            r'^Would\s+',                 # "Would you consider..."
            r'^How\s+',                   # "How would you..."
            r'^What\s+if\s+',            # "What if we..."
            r'^Do\s+you\s+think\s+',     # "Do you think..."
            r'^Could\s+you\s+',          # "Could you imagine..."
            r'\?\s*$',                   # Ends with question mark
            r'^Let\'s\s+say\s+',         # "Let's say hypothetically..."
            r'^Imagine\s+if\s+',         # "Imagine if we..."
            r'^Suppose\s+',              # "Suppose you had..."
        ]
        
        # Combine patterns
        combined_pattern = '|'.join(question_patterns)
        
        # Filter out matches
        mask = ~filtered_data['verbatim_response'].str.contains(
            combined_pattern, 
            case=False, 
            na=False, 
            regex=True
        )
        
        filtered_data = filtered_data[mask]
        
        # Additional filtering for very short responses (likely not verbatim)
        filtered_data = filtered_data[filtered_data['verbatim_response'].str.len() >= 20]
        
        # Log what was filtered out for transparency
        removed_count = original_count - len(filtered_data)
        if removed_count > 0:
            logger.info(f"   📋 Removed {removed_count} items: questions, hypotheticals, or very short responses")
            
            # Log examples of what was removed (first 2)
            removed_items = quotes_data[~quotes_data.index.isin(filtered_data.index)]
            for i, (_, item) in enumerate(removed_items.head(2).iterrows()):
                preview = item['verbatim_response'][:100] + "..." if len(item['verbatim_response']) > 100 else item['verbatim_response']
                logger.info(f"     ❌ Removed: \"{preview}\"")
        
        return filtered_data
    
    def _categorize_theme_clusters(self, subject: str, quotes: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Enhanced theme categorization with clear sentiment-deal status alignment.
        Fixes confusion between theme type and sentiment.
        """
        clusters = []
        
        # Analyze sentiment and deal status distribution
        sentiment_counts = quotes['sentiment'].value_counts()
        
        # Determine if we have deal status data
        has_deal_data = 'deal_status' in quotes.columns and quotes['deal_status'].notna().sum() > 0
        
        if has_deal_data:
            won_ratio = quotes['deal_status'].str.contains('won', case=False, na=False).mean()
        else:
            won_ratio = 0.5  # Neutral assumption if no deal data
        
        # 1. STRENGTH: Positive sentiment + Won deals (or predominantly positive with no deal data)
        strength_quotes = quotes[quotes['sentiment'] == 'positive']
        if has_deal_data:
            # Prioritize won deals for strength themes
            won_quotes = strength_quotes[
                strength_quotes['deal_status'].str.contains('won', case=False, na=False)
            ]
            other_quotes = strength_quotes[
                ~strength_quotes['deal_status'].str.contains('won', case=False, na=False)
            ]
            
            # Use won deals if available, otherwise fall back to other positive quotes
            if len(won_quotes) >= self.min_quotes_per_theme:
                strength_quotes = won_quotes
                deal_context = " from won deals"
            elif len(strength_quotes) >= self.min_quotes_per_theme:
                deal_context = " (mixed deal outcomes)"
            else:
                strength_quotes = pd.DataFrame()  # Not enough quotes
                deal_context = ""
        else:
            deal_context = ""
        
        if len(strength_quotes) >= self.min_quotes_per_theme:
            clusters.append({
                "theme_type": "strength",
                "harmonized_subject": subject,
                "quotes": strength_quotes,
                "pattern_summary": f"Positive customer feedback about {subject}{deal_context}",
                "deal_outcome_focus": "won" if has_deal_data and "won" in deal_context else "mixed",
                "theme_origin": "discovered"
            })
        
        # 2. WEAKNESS: Negative sentiment + Lost deals (or predominantly negative)
        weakness_quotes = quotes[quotes['sentiment'] == 'negative']
        if has_deal_data:
            # Prioritize lost deals for weakness themes
            lost_quotes = weakness_quotes[
                weakness_quotes['deal_status'].str.contains('lost', case=False, na=False)
            ]
            other_quotes = weakness_quotes[
                ~weakness_quotes['deal_status'].str.contains('lost', case=False, na=False)
            ]
            
            # Use lost deals if available, otherwise fall back to other negative quotes
            if len(lost_quotes) >= self.min_quotes_per_theme:
                weakness_quotes = lost_quotes
                deal_context = " from lost deals"
            elif len(weakness_quotes) >= self.min_quotes_per_theme:
                deal_context = " (mixed deal outcomes)"
            else:
                weakness_quotes = pd.DataFrame()  # Not enough quotes
                deal_context = ""
        else:
            deal_context = ""
        
        if len(weakness_quotes) >= self.min_quotes_per_theme:
            clusters.append({
                "theme_type": "weakness",
                "harmonized_subject": subject,
                "quotes": weakness_quotes,
                "pattern_summary": f"Negative customer feedback about {subject}{deal_context}",
                "deal_outcome_focus": "lost" if has_deal_data and "lost" in deal_context else "mixed",
                "theme_origin": "discovered"
            })
        
        # 3. OPPORTUNITY: Positive sentiment + Lost deals (unmet potential)
        if has_deal_data:
            opportunity_quotes = quotes[
                (quotes['sentiment'] == 'positive') & 
                (quotes['deal_status'].str.contains('lost', case=False, na=False))
            ]
            
            if len(opportunity_quotes) > 0:
                clusters.append({
                    "theme_type": "opportunity",
                    "harmonized_subject": subject,
                    "quotes": opportunity_quotes,
                    "pattern_summary": f"Positive feedback about {subject} from lost deals - unmet market opportunity",
                    "theme_origin": "discovered"
                })
        
        # 4. CONCERN: Negative sentiment + Won deals (risk area)
        if has_deal_data:
            concern_quotes = quotes[
                (quotes['sentiment'] == 'negative') & 
                (quotes['deal_status'].str.contains('won', case=False, na=False))
            ]
            
            if len(concern_quotes) > 0:
                clusters.append({
                    "theme_type": "concern",
                    "harmonized_subject": subject,
                    "quotes": concern_quotes,
                    "pattern_summary": f"Negative feedback about {subject} from won deals - potential risk area",
                    "theme_origin": "discovered"
                })
        
        # 5. INVESTIGATION NEEDED: Mixed/neutral sentiment or conflicting patterns
        mixed_quotes = quotes[quotes['sentiment'].isin(['mixed', 'neutral'])]
        
        # Add conflicting patterns only if we have significant volume
        if len(mixed_quotes) > 1 or (len(quotes) > 5 and len(sentiment_counts) >= 2):
            clusters.append({
                "theme_type": "investigation_needed",
                "harmonized_subject": subject,
                "quotes": mixed_quotes if len(mixed_quotes) > 0 else quotes,
                "pattern_summary": f"Mixed or unclear customer sentiment about {subject} requiring deeper analysis",
                "theme_origin": "discovered"
            })
        
        return clusters
    
    def _generate_theme_statements(self, validated_themes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate executive-ready theme statements for validated themes.
        Now research-question-driven to ensure alignment with original research intent.
        
        Args:
            validated_themes: List of themes that passed quality gates
            
        Returns:
            List of themes with generated statements
        """
        final_themes = []
        
        for i, theme in enumerate(validated_themes, 1):
            quotes = theme["quotes"]
            theme_type = theme["theme_type"]
            subject = theme["harmonized_subject"]
            
            # Generate theme ID
            theme_id = f"theme_{i:03d}_{theme_type}"
            
            # Analyze research question alignment for this theme
            research_alignment = self._analyze_theme_research_alignment(quotes)
            
            # Analyze deal status distribution for context
            deal_status_distribution = self._analyze_deal_status_distribution(quotes)
            
            # Generate theme statement based on research question alignment with deal status
            theme_statement = self._generate_research_driven_theme_statement(
                quotes, theme_type, subject, research_alignment, deal_status_distribution
            )
            
            # Generate theme title based on research question
            theme_title = self._generate_research_driven_theme_title(
                research_alignment, theme_type, subject
            )
            
            # Calculate quality metrics
            quality_score = theme["validation_metrics"].get("quality_score", theme["validation_metrics"].get("confidence_score", 0.0))
            company_distribution = self._calculate_company_distribution(quotes)
            
            # Determine report section and win-loss category
            win_loss_category = self._determine_win_loss_category(theme)
            report_section = self._determine_report_section(win_loss_category)
            
            # Prepare supporting quotes (top 3 by impact score)
            supporting_quotes = quotes.nlargest(3, 'impact_score')[['verbatim_response', 'company', 'interviewee_name', 'sentiment', 'impact_score']].to_dict('records')
            
            # Create final theme object
            final_theme = {
                "theme_id": theme_id,
                "theme_title": theme_title,
                "theme_statement": theme_statement,
                "theme_type": theme_type,
                "harmonized_subject": subject,
                "report_section": report_section,
                "win_loss_category": win_loss_category,
                "quality_score": quality_score,
                "company_distribution": company_distribution,
                "research_alignment": research_alignment,
                "all_quotes": quotes.to_dict('records'),
                "supporting_quotes": supporting_quotes,
                "pattern_summary": theme.get("pattern_summary", ""),
                "competitive_flag": theme.get("competitive_flag", False),
                "validation_metrics": theme["validation_metrics"],
                "deal_outcome_focus": theme.get("deal_outcome_focus", "mixed"),
                "theme_origin": theme.get("theme_origin", "discovered"),
                "research_primary_question": research_alignment.get('primary_question', ''),
                "research_alignment_score": research_alignment.get('alignment_confidence', 0.0)
            }
            
            final_themes.append(final_theme)
        
        return final_themes
    
    def _generate_enhanced_theme_statement(self, quotes: List[Dict], theme_type: str, harmonized_subject: str) -> str:
        """Generate enhanced theme statement with company context and competitive references"""
        
        # Extract company context and competitive references
        companies = list(set([q.get('company', q.get('company_name', 'Unknown')) for q in quotes]))
        competitors_mentioned = []
        competitive_context = ""
        
        for quote in quotes:
            quote_text = quote.get('verbatim_response', '').lower()
            # Look for competitor mentions
            competitors = ['eve', 'evenup', 'parrot', 'filevine', 'competitor', 'competition']
            for comp in competitors:
                if comp in quote_text:
                    if comp not in ['competitor', 'competition']:
                        competitors_mentioned.append(comp.title())
                    competitive_context = "competitive positioning"
        
        # Create context-rich prompt
        context_info = f"Subject: {harmonized_subject}, Companies: {', '.join(companies[:3])}"
        if competitors_mentioned:
            context_info += f", Competitors: {', '.join(competitors_mentioned)}"
        if competitive_context:
            context_info += f", Context: {competitive_context}"
        
        prompt = f"""
        Generate an executive-ready theme statement for a {theme_type} theme in the {harmonized_subject} category.
        
        Context: {context_info}
        
        Requirements:
        1. Include specific company context when relevant
        2. Reference competitive positioning if mentioned
        3. Highlight quantifiable impact or outcomes
        4. Use B2B SaaS expert copywriter voice
        5. Make it actionable and specific
        6. Focus on customer pain points or wins
        7. Include competitive differentiators if applicable
        
        Example style: "Companies like [Company] struggle with [specific pain] when [situation], leading to [impact]. Supio addresses this by [solution], resulting in [outcome] compared to competitors like [competitor]."
        
        Generate a clear, specific theme statement that captures the key insight from these customer quotes.
        """
        
        try:
            response = self._call_openai_api(prompt, max_tokens=150)
            return response.strip()
        except Exception as e:
            self.logger.error(f"Error generating enhanced theme statement: {e}")
            return f"Enhanced {theme_type} theme in {harmonized_subject} category"
    
    def _generate_enhanced_theme_title(self, theme: Dict[str, Any], supporting_quotes: List[Dict]) -> str:
        """Generate enhanced theme title using Stage 4 specificity methodology"""
        quotes = theme["quotes"]
        theme_type = theme["theme_type"]
        subject = theme["harmonized_subject"]
        
        # Use LLM if available for title generation
        if self.openai_api_key:
            return self._generate_llm_theme_title(theme, supporting_quotes)
        else:
            return self._generate_enhanced_template_title(theme, supporting_quotes)
    
    def _generate_llm_theme_title(self, theme: Dict[str, Any], supporting_quotes: List[Dict]) -> str:
        """Generate specific theme title using LLM with Stage 4 methodology"""
        quotes = theme["quotes"]
        theme_type = theme["theme_type"]
        subject = theme["harmonized_subject"]
        
        # Extract customer terminology and specific issues
        quote_analysis = self._analyze_customer_quotes(quotes)
        
        # Create Stage 4-style title generation prompt
        prompt = self._create_theme_title_prompt(theme, quote_analysis, supporting_quotes)
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert B2B SaaS competitive intelligence analyst specializing in creating specific, actionable theme titles that executives can immediately understand. Use exact customer terminology and specific business impacts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=100
            )
            
            title = response.choices[0].message.content.strip()
            
            # Remove quotes if LLM added them
            title = title.replace('"', '').replace("'", "")
            
            # Ensure title is not too long (max 100 characters)
            if len(title) > 100:
                title = title[:97] + "..."
            
            return title
                
        except Exception as e:
            logger.warning(f"LLM theme title generation failed: {e}, using enhanced template")
            return self._generate_enhanced_template_title(theme, supporting_quotes)
    
    def _create_theme_title_prompt(self, theme: Dict[str, Any], quote_analysis: Dict[str, Any], supporting_quotes: List[Dict]) -> str:
        """Create Stage 4-style prompt for theme title generation"""
        quotes = theme["quotes"]
        theme_type = theme["theme_type"]
        subject = theme["harmonized_subject"]
        
        # Get most representative quote
        top_quote = supporting_quotes[0]['quote_text'] if supporting_quotes else ""
        
        prompt = f"""
⚠️ CRITICAL: Generate a SPECIFIC theme title following Stage 4 methodology EXACTLY.

THEME CONTEXT:
- Subject Area: {subject}
- Theme Type: {theme_type}
- Customer Pain Points: {', '.join(quote_analysis['pain_points'][:2])}
- Business Impacts: {', '.join(quote_analysis['business_impacts'][:2])}
- Top Customer Quote: "{top_quote}"

TITLE REQUIREMENTS (CRITICAL - MUST FOLLOW EXACTLY):
- Titles MUST clearly identify the SPECIFIC problem using exact customer terminology
- Use concrete, evidence-based language from actual quotes - NO generic terms
- NO generic titles like "efficiency declines", "quality issues", "user satisfaction"
- MUST use specific terminology from quotes
- Include specific context when available
- Titles MUST be specific enough that the client immediately understands the exact issue
- Highlight business impact or consequence using evidence from quotes
- Maximum 15 words

EXAMPLES OF GOOD TITLES:
- "Credit-based pricing model confusion leads prospects to request flat-rate alternatives"
- "Document organization limitations force manual filing workarounds for case materials"
- "Multi-user access restrictions prevent team collaboration during evaluation process"

EXAMPLES OF BAD TITLES (DO NOT USE):
- "Pricing issues disrupt user satisfaction" (too generic)
- "Workflow efficiency declines due to unclear processes" (too vague)
- "Quality issues hinder preparation efficiency" (not specific enough)

Generate ONE specific title that identifies the exact problem using customer terminology:
"""
        return prompt
    
    def _generate_enhanced_template_title(self, theme: Dict[str, Any], supporting_quotes: List[Dict]) -> str:
        """Generate enhanced template-based title when LLM is not available"""
        quotes = theme["quotes"]
        theme_type = theme["theme_type"]
        subject = theme["harmonized_subject"]
        
        # Analyze quotes for specific terminology
        quote_analysis = self._analyze_customer_quotes(quotes)
        
        # Try to extract specific issues from quotes
        specific_issue = self._extract_specific_issue(quotes, quote_analysis)
        business_impact = self._extract_business_impact(quotes, quote_analysis)
        
        # Create more specific titles based on extracted information
        if specific_issue and business_impact:
            return f"{specific_issue} {business_impact}"
        elif specific_issue:
            return f"{specific_issue} affects {subject.lower()} adoption"
        elif business_impact:
            return f"{subject} limitations {business_impact}"
        else:
            # Fallback to enhanced but generic titles
            if theme_type == "strength":
                return f"{subject} capabilities drive positive evaluation outcomes"
            elif theme_type == "weakness":
                return f"{subject} limitations create adoption barriers for prospects"
            else:
                return f"{subject} performance varies across different customer use cases"
    
    def _extract_specific_issue(self, quotes: pd.DataFrame, quote_analysis: Dict[str, Any]) -> str:
        """Extract specific issue terminology from customer quotes"""
        # Look for specific problems mentioned by customers
        issue_patterns = [
            'pricing model', 'credit system', 'user interface', 'document management', 
            'file organization', 'search functionality', 'integration capabilities',
            'reporting features', 'user access', 'training requirements', 'setup process'
        ]
        
        text_combined = ' '.join(quotes['verbatim_response'].astype(str).str.lower())
        
        for pattern in issue_patterns:
            if pattern in text_combined:
                return pattern.title()
        
        # If no specific pattern, use the most common pain point
        if quote_analysis['pain_points']:
            pain = quote_analysis['pain_points'][0]
            # Clean up the pain point to make it title-worthy
            words = pain.split()[:4]  # Take first 4 words
            return ' '.join(words).title()
        
        return ""
    
    def _extract_business_impact(self, quotes: pd.DataFrame, quote_analysis: Dict[str, Any]) -> str:
        """Extract business impact terminology from customer quotes"""
        # Look for specific business consequences
        impact_patterns = [
            'delays evaluation', 'requires workarounds', 'prevents adoption', 
            'forces manual processes', 'creates confusion', 'extends timelines',
            'increases costs', 'reduces efficiency', 'complicates workflow'
        ]
        
        text_combined = ' '.join(quotes['verbatim_response'].astype(str).str.lower())
        
        for pattern in impact_patterns:
            if pattern in text_combined:
                return pattern
        
        # If no specific pattern, use the most common business impact
        if quote_analysis['business_impacts']:
            impact = quote_analysis['business_impacts'][0]
            # Clean up the impact to make it title-worthy
            words = impact.split()[:4]  # Take first 4 words
            return ' '.join(words).lower()
        
        return ""
    
    def _generate_enhanced_theme_statement(self, theme: Dict[str, Any]) -> str:
        """Generate enhanced theme statement using Stage 4 methodology with LLM"""
        quotes = theme["quotes"]
        theme_type = theme["theme_type"]
        subject = theme["harmonized_subject"]
        
        # Use LLM if available, otherwise fallback to enhanced template
        if self.openai_api_key:
            return self._generate_llm_theme_statement(theme)
        else:
            return self._generate_enhanced_template_statement(theme)
    
    def _generate_llm_theme_statement(self, theme: Dict[str, Any]) -> str:
        """Generate theme statement using LLM with Stage 4 executive framework"""
        quotes = theme["quotes"]
        theme_type = theme["theme_type"]
        subject = theme["harmonized_subject"]
        
        # Extract customer terminology and pain points
        quote_analysis = self._analyze_customer_quotes(quotes)
        
        # Create Stage 4-style prompt
        prompt = self._create_theme_statement_prompt(theme, quote_analysis)
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert B2B SaaS competitive intelligence analyst specializing in executive communication. Generate theme statements that are board-deck ready with specific customer terminology."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            statement = response.choices[0].message.content.strip()
            
            # Validate two-sentence format
            sentences = statement.split('.')
            if len(sentences) >= 2:
                # Take first two sentences and ensure proper format
                sentence1 = sentences[0].strip() + '.'
                sentence2 = sentences[1].strip() + '.'
                return f"{sentence1} {sentence2}"
            else:
                return statement
                
        except Exception as e:
            logger.warning(f"LLM theme statement generation failed: {e}, using enhanced template")
            return self._generate_enhanced_template_statement(theme)
    
    def _analyze_customer_quotes(self, quotes: pd.DataFrame) -> Dict[str, Any]:
        """Analyze quotes to extract customer terminology and pain points"""
        analysis = {
            "specific_terms": [],
            "pain_points": [],
            "business_impacts": [],
            "customer_behaviors": [],
            "timeframes": [],
            "quantifiable_impacts": []
        }
        
        # Keywords to identify different types of customer feedback
        pain_keywords = ['problem', 'issue', 'difficult', 'frustrating', 'annoying', 'slow', 'error', 'fail', 'broken', 'confusing']
        impact_keywords = ['takes', 'requires', 'forces', 'prevents', 'delays', 'costs', 'waste', 'manual', 'workaround']
        behavior_keywords = ['switch', 'choose', 'evaluate', 'compare', 'consider', 'decide', 'prefer', 'avoid']
        time_keywords = ['minutes', 'hours', 'days', 'weeks', 'time', 'fast', 'slow', 'quick', 'immediately']
        
        for _, quote in quotes.iterrows():
            text = str(quote['verbatim_response']).lower()
            
            # Extract specific product/feature terms (capitalize words that appear frequently)
            words = text.split()
            for word in words:
                if len(word) > 4 and word.isalpha():
                    analysis["specific_terms"].append(word)
            
            # Extract pain points
            for keyword in pain_keywords:
                if keyword in text:
                    # Extract surrounding context
                    context = self._extract_context_around_keyword(text, keyword)
                    analysis["pain_points"].append(context)
            
            # Extract business impacts
            for keyword in impact_keywords:
                if keyword in text:
                    context = self._extract_context_around_keyword(text, keyword)
                    analysis["business_impacts"].append(context)
            
            # Extract customer behaviors
            for keyword in behavior_keywords:
                if keyword in text:
                    context = self._extract_context_around_keyword(text, keyword)
                    analysis["customer_behaviors"].append(context)
            
            # Extract timeframes
            for keyword in time_keywords:
                if keyword in text:
                    context = self._extract_context_around_keyword(text, keyword)
                    analysis["timeframes"].append(context)
        
        # Clean and deduplicate
        for key in analysis:
            analysis[key] = list(set(analysis[key]))[:5]  # Top 5 unique items
        
        return analysis
    
    def _extract_context_around_keyword(self, text: str, keyword: str, window: int = 10) -> str:
        """Extract context around a keyword"""
        words = text.split()
        try:
            keyword_index = words.index(keyword)
            start = max(0, keyword_index - window)
            end = min(len(words), keyword_index + window + 1)
            return ' '.join(words[start:end])
        except ValueError:
            return ""
    
    def _create_theme_statement_prompt(self, theme: Dict[str, Any], quote_analysis: Dict[str, Any]) -> str:
        """Create Stage 4-style prompt for theme statement generation"""
        quotes = theme["quotes"]
        theme_type = theme["theme_type"]
        subject = theme["harmonized_subject"]
        company_col = 'company' if 'company' in quotes.columns else 'company_name'
        companies_count = quotes[company_col].nunique()
        
        # Get sample quotes for context
        sample_quotes = quotes['verbatim_response'].head(3).tolist()
        
        prompt = f"""
⚠️ CRITICAL: Generate an executive-ready theme statement following Stage 4 methodology EXACTLY.

THEME CONTEXT:
- Subject Area: {subject}
- Theme Type: {theme_type}
- Companies: {companies_count}
- Customer Pain Points: {', '.join(quote_analysis['pain_points'][:3])}
- Business Impacts: {', '.join(quote_analysis['business_impacts'][:3])}
- Customer Behaviors: {', '.join(quote_analysis['customer_behaviors'][:3])}

SAMPLE CUSTOMER QUOTES:
{chr(10).join([f"- {quote}" for quote in sample_quotes])}

CRITICAL REQUIREMENTS:
1. EXACTLY two sentences - NO MORE, NO LESS
2. Sentence 1: Decision behavior or specific problem with consequence (25-35 words max)
3. Sentence 2: Most common customer pain point or reaction (25-35 words max)
4. NO direct quotes in the statement
5. NO solutioning language ("indicating a need for", "suggesting", "recommending")
6. Use SPECIFIC customer terminology from quotes
7. Focus on specific product problems causing customer pain
8. Use universal business language - NO industry-specific terms

EXAMPLES OF GOOD STATEMENTS:
- "Credit-based pricing model confusion leads prospects to request flat-rate alternatives during evaluation. Multiple customers report difficulty understanding usage forecasting which creates budget approval delays."
- "Document organization limitations force users to implement manual filing workarounds for case materials. Legal teams consistently mention time-consuming searches that impact workflow efficiency and case preparation timelines."

Generate a theme statement that follows this exact format and specificity level:
"""
        return prompt
    
    def _generate_enhanced_template_statement(self, theme: Dict[str, Any]) -> str:
        """Generate enhanced template-based statement when LLM is not available"""
        quotes = theme["quotes"]
        theme_type = theme["theme_type"]
        subject = theme["harmonized_subject"]
        company_col = 'company' if 'company' in quotes.columns else 'company_name'
        companies_count = quotes[company_col].nunique()
        
        # Analyze quotes for better terminology
        quote_analysis = self._analyze_customer_quotes(quotes)
        
        # Create more specific statements based on theme type
        if theme_type == "strength":
            if quote_analysis["customer_behaviors"]:
                behavior = quote_analysis["customer_behaviors"][0]
                return f"Customers consistently {behavior} due to {subject.lower()} capabilities that differentiate from competitors. {companies_count} organizations report positive decision impact and recommend the solution based on this strength."
            else:
                return f"Customers consistently praise {subject.lower()} as a key differentiator during vendor evaluation. {companies_count} companies highlight its positive impact on their purchasing decision and implementation success."
                
        elif theme_type == "weakness":
            if quote_analysis["pain_points"]:
                pain = quote_analysis["pain_points"][0]
                return f"Multiple customers cite {pain} related to {subject.lower()} as a barrier to adoption. {companies_count} companies identify this issue as requiring workarounds or additional vendor evaluation."
            else:
                return f"Multiple customers express concerns about {subject.lower()} limitations during evaluation process. {companies_count} companies identify this as a barrier requiring additional consideration or alternative solutions."
                
        else:  # mixed/investigation_needed
            return f"Mixed customer feedback about {subject.lower()} reveals varying experiences across different use cases. {companies_count} companies provide divergent perspectives that suggest context-dependent performance requiring deeper analysis."
    
    def _select_supporting_quotes(self, quotes: pd.DataFrame, theme_type: str, max_quotes: int = 5) -> List[Dict]:
        """Select the best supporting quotes for the theme"""
        # Sort by impact score and select top quotes
        sorted_quotes = quotes.sort_values(['impact_score', 'created_at'], ascending=[False, False])
        
        selected = []
        company_col = 'company' if 'company' in quotes.columns else 'company_name'
        for _, quote in sorted_quotes.head(max_quotes).iterrows():
            selected.append({
                "quote_text": quote['verbatim_response'],
                "company": quote[company_col],
                "interviewee": quote['interviewee_name'],
                "sentiment": quote['sentiment'],
                "impact_score": quote['impact_score'],
                "response_id": quote['response_id']
            })
        
        return selected
    
    def _check_competitive_relevance(self, quotes: pd.DataFrame) -> bool:
        """Check if theme has competitive intelligence relevance"""
        # Look for competitive keywords in the quotes
        competitive_keywords = ['competitor', 'alternative', 'versus', 'compared to', 'other vendor', 'switch']
        
        for _, quote in quotes.iterrows():
            text = str(quote['verbatim_response']).lower()
            if any(keyword in text for keyword in competitive_keywords):
                return True
        
        # Check if harmonized subject is Market Discovery
        if quotes.get('harmonized_subject', '').iloc[0] == 'Market Discovery':
            return True
        
        return False
    
    def _prepare_curation_data(self, themes: List[Dict[str, Any]], all_quotes: pd.DataFrame) -> Dict[str, Any]:
        """
        Prepare data for analyst curation spreadsheet.
        
        Args:
            themes: Final validated themes
            all_quotes: All quotes data for reference
            
        Returns:
            Dictionary containing all spreadsheet tab data
        """
        curation_data = {
            "themes_overview": self._prepare_themes_overview(themes),
            "quote_curation_workspace": self._prepare_quote_workspace(themes),
            "competitive_intelligence": self._prepare_competitive_view(themes),
            "discussion_guide_view": self._prepare_discussion_guide_view(all_quotes),
            "report_builder_template": self._prepare_report_builder(themes)
        }
        
        return curation_data
    
    def _prepare_themes_overview(self, themes: List[Dict[str, Any]]) -> List[Dict]:
        """Prepare the themes overview tab for analysts"""
        overview = []
        
        for theme in themes:
            metrics = theme["validation_metrics"]
            overview.append({
                "Theme ID": theme["theme_id"],
                "Theme Statement": theme["theme_statement"],
                "Theme Type": theme["theme_type"].title(),
                "Harmonized Subject": theme["harmonized_subject"],
                "Total Quotes": metrics.get("quotes_count", 0),
                "Companies": metrics.get("companies_count", 0),
                "Avg Impact Score": f"{metrics['avg_impact_score']:.1f}",
                "Quality Score": f"{metrics['quality_score']:.1f}",
                "Competitive Flag": "Yes" if theme.get("competitive_flag", False) else "No",
                "Deal Status Breakdown": self._get_deal_breakdown(theme["all_quotes"]),
                "Sentiment Breakdown": self._get_sentiment_breakdown(theme["all_quotes"])
            })
        
        return overview
    
    def _prepare_quote_workspace(self, themes: List[Dict[str, Any]]) -> List[Dict]:
        """Prepare the main quote curation workspace"""
        workspace = []
        
        for theme in themes:
            # Get the right company column name
            sample_quote = theme["all_quotes"][0] if theme["all_quotes"] else {}
            company_col = 'company' if 'company' in sample_quote else 'company_name'
            
            for quote_data in theme["all_quotes"]:
                workspace.append({
                    "Theme ID": theme["theme_id"],
                    "Theme Statement": theme["theme_statement"],
                    "Theme Type": theme["theme_type"].title(),
                    "Harmonized Subject": theme["harmonized_subject"],
                    "Verbatim Quote": quote_data["verbatim_response"],
                    "Sentiment": quote_data["sentiment"].title(),
                    "Impact Score": quote_data["impact_score"],
                    "Deal Status": quote_data["deal_status"],
                    "Company Name": quote_data.get(company_col, quote_data.get("company", quote_data.get("company_name", ""))),
                    "Interviewee Name": quote_data["interviewee_name"],
                    "Interview Date": quote_data.get("interview_date", ""),
                    "Original Question": quote_data.get("question", ""),
                    "Response ID": quote_data["response_id"],
                    "Analyst Decision (Include/Exclude)": "",  # Empty for analyst to fill
                    "Analyst Notes": ""  # Empty for analyst to fill
                })
        
        return workspace
    
    def _prepare_competitive_view(self, themes: List[Dict[str, Any]]) -> List[Dict]:
        """Prepare competitive intelligence deep dive"""
        competitive = []
        
        for theme in themes:
            if theme["competitive_flag"]:
                # Get the right company column name
                sample_quote = theme["all_quotes"][0] if theme["all_quotes"] else {}
                company_col = 'company' if 'company' in sample_quote else 'company_name'
                
                for quote_data in theme["all_quotes"]:
                    competitive.append({
                        "Competitive Theme": theme["theme_statement"],
                        "Verbatim Quote": quote_data["verbatim_response"],
                        "Mentioned Competitor(s)": self._extract_competitors(quote_data["verbatim_response"]),
                        "Sentiment": quote_data["sentiment"].title(),
                        "Deal Status": quote_data["deal_status"],
                        "Company Name": quote_data.get(company_col, quote_data.get("company", quote_data.get("company_name", ""))),
                        "Impact Score": quote_data["impact_score"]
                    })
        
        return competitive
    
    def _prepare_discussion_guide_view(self, all_quotes: pd.DataFrame) -> List[Dict]:
        """Prepare discussion guide organized view (placeholder for now)"""
        # This would map to actual discussion guide sections when integrated
        guide_view = []
        
        company_col = 'company' if 'company' in all_quotes.columns else 'company_name'
        
        for _, quote in all_quotes.iterrows():
            guide_view.append({
                "Guide Section": "TBD - Map to Discussion Guide",  # Will be mapped later
                "Guide Question/Topic": quote.get("question", ""),
                "Verbatim Quote": quote["verbatim_response"],
                "Sentiment": quote["sentiment"].title() if pd.notna(quote["sentiment"]) else "",
                "Impact Score": quote["impact_score"] if pd.notna(quote["impact_score"]) else "",
                "Company Name": quote[company_col],
                "Harmonized Subject": quote.get("harmonized_subject", "")
            })
        
        return guide_view
    
    def _prepare_report_builder(self, themes: List[Dict[str, Any]]) -> Dict[str, List]:
        """Prepare the report builder template structure"""
        builder = {
            "key_strengths": [theme for theme in themes if theme["theme_type"] == "strength"],
            "key_weaknesses": [theme for theme in themes if theme["theme_type"] == "weakness"],
            "competitive_insights": [theme for theme in themes if theme["competitive_flag"]],
            "mixed_signals": [theme for theme in themes if theme["theme_type"] == "mixed_signal"]
        }
        
        return builder
    
    def _get_deal_breakdown(self, quotes: List[Dict]) -> str:
        """Get deal status breakdown for quotes"""
        deal_counts = Counter([q.get("deal_status", "unknown") for q in quotes])
        return ", ".join([f"{status}: {count}" for status, count in deal_counts.items()])
    
    def _get_sentiment_breakdown(self, quotes: List[Dict]) -> str:
        """Get sentiment breakdown for quotes"""
        sentiment_counts = Counter([q.get("sentiment", "unknown") for q in quotes])
        return ", ".join([f"{sentiment}: {count}" for sentiment, count in sentiment_counts.items()])
    
    def _extract_competitors(self, quote_text: str) -> str:
        """Extract mentioned competitors from quote text (basic implementation)"""
        # This would be enhanced with actual competitor detection logic
        competitive_terms = []
        text_lower = quote_text.lower()
        
        if 'competitor' in text_lower:
            competitive_terms.append('Unspecified competitor')
        if 'alternative' in text_lower:
            competitive_terms.append('Alternative solution')
        
        return ", ".join(competitive_terms) if competitive_terms else "No specific competitors mentioned"

    def _determine_win_loss_category(self, theme: Dict[str, Any]) -> str:
        """
        Determine the win-loss category for a theme based on its type and characteristics.
        
        Args:
            theme: Theme dictionary with type and characteristics
            
        Returns:
            String indicating win-loss category
        """
        theme_type = theme.get('theme_type', '')
        subject = theme.get('harmonized_subject', '').lower()
        
        # Map theme types to win-loss categories
        if theme_type == 'strength':
            return 'win_driver'
        elif theme_type == 'weakness':
            return 'loss_factor'
        elif theme_type == 'opportunity':
            return 'opportunity'
        elif theme_type == 'concern':
            return 'risk'
        elif theme_type == 'investigation_needed':
            # For investigation themes, determine based on subject
            if 'competitive' in subject or 'competitor' in subject:
                return 'competitive_intelligence'
            elif 'implementation' in subject or 'deployment' in subject:
                return 'implementation_insight'
            else:
                return 'investigation_needed'
        else:
            return 'other'
    
    def _determine_report_section(self, win_loss_category: str) -> str:
        """
        Determine the report section for a win-loss category.
        
        Args:
            win_loss_category: The win-loss category
            
        Returns:
            String indicating report section
        """
        section_mapping = {
            'win_driver': 'Win Drivers',
            'loss_factor': 'Loss Factors', 
            'competitive_intelligence': 'Competitive Intelligence',
            'implementation_insight': 'Implementation Insights',
            'opportunity': 'Opportunities',
            'risk': 'Risk Areas',
            'investigation_needed': 'Areas for Investigation',
            'other': 'Other Insights'
        }
        
        return section_mapping.get(win_loss_category, 'Other Insights')
    
    def _calculate_sentiment_coherence(self, quotes: pd.DataFrame) -> float:
        """
        Calculate sentiment coherence percentage for a set of quotes.
        
        Args:
            quotes: DataFrame of quotes
            
        Returns:
            Float representing coherence percentage
        """
        if len(quotes) == 0:
            return 0.0
        
        sentiment_counts = quotes['sentiment'].value_counts()
        dominant_sentiment_count = sentiment_counts.iloc[0] if not sentiment_counts.empty else 0
        
        return (dominant_sentiment_count / len(quotes)) * 100

    def _call_openai_api(self, prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> str:
        """
        Call OpenAI API for text generation.
        
        Args:
            prompt: The prompt to send to the API
            max_tokens: Maximum tokens to generate
            temperature: Creativity level (0.0-1.0)
            
        Returns:
            Generated text response
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert business analyst specializing in customer feedback analysis and win-loss reporting."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}")
            return ""
    
    def _generate_research_driven_theme_statement(self, quotes: pd.DataFrame, theme_type: str, subject: str, research_alignment: Dict, deal_status_distribution: Dict[str, Any] = None) -> str:
        """
        Generate theme statement based on research question alignment with deal status context.
        """
        # Get primary research question
        primary_question = research_alignment.get('primary_question', '')
        
        if primary_question:
            # Generate LLM-driven statement with research context and deal status
            return self._generate_llm_research_driven_statement(primary_question, quotes, theme_type, subject, deal_status_distribution)
        else:
            # Fallback to template-based statement with deal status
            return self._generate_template_research_driven_statement("", quotes, theme_type, subject, deal_status_distribution)
    
    def _generate_research_driven_theme_title(self, research_alignment: Dict, theme_type: str, subject: str) -> str:
        """
        Generate theme title based on research question alignment.
        
        Args:
            research_alignment: Research alignment analysis
            theme_type: Type of theme
            subject: Harmonized subject
            
        Returns:
            Research-driven theme title
        """
        primary_question = research_alignment.get('primary_question', '')
        
        if not primary_question:
            # Fallback to subject-based title
            return f"{subject.title()} {theme_type.title()}"
        
        # Extract key concept from research question
        question_keywords = research_alignment.get('question_keywords', [])
        if question_keywords:
            key_concept = question_keywords[0].title()
        else:
            # Extract from question text
            key_concept = primary_question.split()[0].title()
        
        return f"{key_concept} {theme_type.title()}"
    
    def _analyze_deal_status_distribution(self, quotes: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze deal status distribution for theme context.
        """
        if 'deal_status' not in quotes.columns:
            return {"has_deal_data": False, "won_count": 0, "lost_count": 0, "other_count": 0}
        
        deal_counts = quotes['deal_status'].value_counts()
        won_count = deal_counts.get('closed won', 0) + deal_counts.get('won', 0)
        lost_count = deal_counts.get('closed lost', 0) + deal_counts.get('lost', 0)
        other_count = len(quotes) - won_count - lost_count
        
        return {
            "has_deal_data": True,
            "won_count": won_count,
            "lost_count": lost_count,
            "other_count": other_count,
            "total_count": len(quotes),
            "won_percentage": (won_count / len(quotes) * 100) if len(quotes) > 0 else 0,
            "lost_percentage": (lost_count / len(quotes) * 100) if len(quotes) > 0 else 0
        }
    
    def _generate_llm_research_driven_statement(self, primary_question: str, aligned_quotes: pd.DataFrame, theme_type: str, subject: str, deal_status_distribution: Dict[str, Any] = None) -> str:
        """
        Generate enhanced LLM-based theme statement with company context, competitive references, and deal status.
        """
        try:
            # Extract company context and competitive references
            companies = list(set(aligned_quotes['company'].tolist()))
            if 'company_name' in aligned_quotes.columns:
                companies.extend(aligned_quotes['company_name'].tolist())
            companies = [c for c in companies if c and c != 'Unknown']
            competitors_mentioned = []
            competitive_context = ""
            
            for quote in aligned_quotes.to_dict('records'):
                quote_text = quote.get('verbatim_response', '').lower()
                # Look for competitor mentions
                competitors = ['eve', 'evenup', 'parrot', 'filevine', 'competitor', 'competition']
                for comp in competitors:
                    if comp in quote_text:
                        if comp not in ['competitor', 'competition']:
                            competitors_mentioned.append(comp.title())
                        competitive_context = "competitive positioning"
            
            # Prepare context for LLM
            quote_texts = aligned_quotes['verbatim_response'].tolist()[:5]  # Top 5 aligned quotes
            quote_context = "\n".join([f"- {quote}" for quote in quote_texts])
            
            # Create context-rich prompt with deal status
            context_info = f"Companies: {', '.join(companies[:3])}"
            if competitors_mentioned:
                context_info += f", Competitors: {', '.join(competitors_mentioned)}"
            if competitive_context:
                context_info += f", Context: {competitive_context}"
            
            # Add deal status context
            deal_context = ""
            if deal_status_distribution and deal_status_distribution.get("has_deal_data"):
                won_pct = deal_status_distribution.get("won_percentage", 0)
                lost_pct = deal_status_distribution.get("lost_percentage", 0)
                if won_pct > 50:
                    deal_context = f" (primarily from won deals - {won_pct:.0f}%)"
                elif lost_pct > 50:
                    deal_context = f" (primarily from lost deals - {lost_pct:.0f}%)"
                else:
                    deal_context = f" (mixed deal outcomes - {won_pct:.0f}% won, {lost_pct:.0f}% lost)"
            
            prompt = f"""
            Based on the research question and aligned customer quotes, generate a SINGLE-LINE HEADLINE (not prose) that is specific to Supio and the buyer context.

            RESEARCH QUESTION: {primary_question}
            THEME TYPE: {theme_type}
            SUBJECT AREA: {subject}
            CONTEXT: {context_info}
            DEAL OUTCOME: {deal_context}

            ALIGNED QUOTES:
            {quote_context}

            HEADLINE REQUIREMENTS (CRITICAL – FOLLOW EXACTLY):
            - Output ONE concise headline only (no bullets, no paragraphs, no trailing period)
            - ≤95 characters; active voice; 1 idea; no generic buzzwords
            - Be specific to Supio and the buyer's situation/stage (e.g., evaluation, onboarding)
            - Prefer customer terminology from quotes; paraphrase is fine; avoid vendor adjectives
            - Ground in evidence: reflect what ≥2 companies/quotes say; if thinner, hedge with "Some buyers"
            - Avoid competitor name-drops unless clearly supported in quotes

            GOOD EXAMPLES:
            - Clear onboarding/training from Supio reduces perceived risk during pre‑litigation
            - Credit-based pricing confusion pushes buyers to request flat-rate options
            - Slow document ingestion delays evaluations compared to buyer expectations

            Produce the HEADLINE now (no prefix, no quotes):"""
            
            response = self._call_openai_api(prompt, max_tokens=60, temperature=0.2)
            return response.strip()
            
        except Exception as e:
            logger.warning(f"LLM theme generation failed: {e}")
            return self._generate_template_research_driven_statement(primary_question, aligned_quotes, theme_type, subject)
    
    def _generate_template_research_driven_statement(self, primary_question: str, aligned_quotes: pd.DataFrame, theme_type: str, subject: str, deal_status_distribution: Dict[str, Any] = None) -> str:
        """
        Generate template-based theme statement that addresses the research question with deal status context.
        """
        # Extract key patterns from aligned quotes
        sentiment_dist = aligned_quotes['sentiment'].value_counts()
        avg_impact = aligned_quotes['impact_score'].mean()
        
        # Add deal status context
        deal_context = ""
        if deal_status_distribution and deal_status_distribution.get("has_deal_data"):
            won_pct = deal_status_distribution.get("won_percentage", 0)
            lost_pct = deal_status_distribution.get("lost_percentage", 0)
            if won_pct > 50:
                deal_context = f" from customers who chose us ({won_pct:.0f}% of quotes)"
            elif lost_pct > 50:
                deal_context = f" from customers who chose competitors ({lost_pct:.0f}% of quotes)"
            else:
                deal_context = f" from mixed deal outcomes ({won_pct:.0f}% won, {lost_pct:.0f}% lost)"
        
        # Determine the main insight based on research question
        if "evaluate" in primary_question.lower():
            insight = "evaluation criteria and decision factors"
        elif "pricing" in primary_question.lower():
            insight = "pricing considerations and value perception"
        elif "competitive" in primary_question.lower():
            insight = "competitive positioning and differentiation"
        else:
            insight = "customer experience and satisfaction"
        
        # Generate context-appropriate statement
        if theme_type == "strength":
            return f"Customers{deal_context} consistently highlight {subject} as a key strength, with {sentiment_dist.get('positive', 0)} positive mentions and average impact score of {avg_impact:.1f}. This addresses {insight} identified in the research."
        elif theme_type == "weakness":
            return f"Customers{deal_context} frequently mention {subject} as an area of concern, with {sentiment_dist.get('negative', 0)} negative mentions and average impact score of {avg_impact:.1f}. This impacts {insight} and requires attention."
        else:
            return f"Analysis of {subject}{deal_context} reveals {insight} with {len(aligned_quotes)} relevant quotes and average impact score of {avg_impact:.1f}. This provides insights into customer decision-making factors."
    
    def _analyze_theme_research_alignment(self, quotes: pd.DataFrame) -> Dict:
        """
        Analyze research question alignment for a theme's quotes.
        
        Args:
            quotes: DataFrame of quotes for this theme
            
        Returns:
            Dictionary with research alignment analysis
        """
        # Get all research question alignments from quotes
        question_counts = {}
        total_quotes = len(quotes)
        aligned_quotes = 0
        
        for _, quote in quotes.iterrows():
            if pd.notna(quote.get('research_question_alignment')):
                aligned_quotes += 1
                try:
                    alignment_data = json.loads(quote['research_question_alignment'])
                    if isinstance(alignment_data, list):
                        for alignment in alignment_data:
                            if isinstance(alignment, dict):
                                question_text = alignment.get('question_text', '')
                                if question_text:
                                    question_counts[question_text] = question_counts.get(question_text, 0) + 1
                    elif isinstance(alignment_data, dict):
                        question_text = alignment_data.get('question_text', '')
                        if question_text:
                            question_counts[question_text] = question_counts.get(question_text, 0) + 1
                except (json.JSONDecodeError, TypeError, AttributeError):
                    continue
        
        if not question_counts:
            return {
                'primary_question': '',
                'question_coverage': {},
                'alignment_confidence': 0.0
            }
        
        # Get primary question (most frequent)
        primary_question = max(question_counts.items(), key=lambda x: x[1])[0]
        
        # Calculate coverage and confidence
        alignment_confidence = (aligned_quotes / total_quotes) * 100 if total_quotes > 0 else 0
        
        return {
            'primary_question': primary_question,
            'question_coverage': question_counts,
            'alignment_confidence': alignment_confidence
        }

    def _calculate_company_distribution(self, quotes: pd.DataFrame) -> Dict:
        """
        Calculate company distribution for quotes.
        
        Args:
            quotes: DataFrame of quotes
            
        Returns:
            Dictionary with company distribution analysis
        """
        company_counts = quotes['company'].value_counts()
        total_companies = len(company_counts)
        total_quotes = len(quotes)
        
        return {
            'companies': company_counts.to_dict(),
            'company_count': total_companies,
            'quote_count': total_quotes,
            'avg_quotes_per_company': total_quotes / total_companies if total_companies > 0 else 0
        }

    def _generate_research_seeded_clusters(self, quotes_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate potential theme clusters seeded by discussion-guide research questions."""
        clusters: List[Dict[str, Any]] = []
        if 'primary_research_question' not in quotes_data.columns:
            return clusters
        
        # Import generator utility
        try:
            from research_theme_generator import generate_research_clusters_for_question
        except Exception as e:
            logger.warning(f"Research theme generator unavailable: {e}")
            return clusters
        
        # Iterate by mapped DB question (Final)
        for question, group in quotes_data.groupby('primary_research_question', dropna=True):
            if not isinstance(question, str) or not question.strip() or question.strip() == 'No research question aligned':
                continue
            q_clusters = generate_research_clusters_for_question(
                question_text=question.strip(),
                quotes_for_question=group.copy(),
                min_companies=self.min_companies_per_theme,
                min_quotes=self.min_quotes_per_theme,
                min_avg_impact=self.min_impact_threshold,
            )
            clusters.extend(q_clusters)
        
        logger.info(f"🧪 Research-seeded clusters generated: {len(clusters)}")
        return clusters

    def _merge_and_dedupe_theme_clusters(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge near-duplicate clusters based on quote overlap and tag hybrids."""
        merged: List[Dict[str, Any]] = []
        used = [False] * len(clusters)
        
        def quote_id_set(df: pd.DataFrame) -> set:
            return set(df.get('response_id', pd.Series(dtype=object)).tolist()) if not df.empty else set()
        
        for i, c1 in enumerate(clusters):
            if used[i]:
                continue
            ids1 = quote_id_set(c1['quotes'])
            base = c1
            for j in range(i + 1, len(clusters)):
                if used[j]:
                    continue
                c2 = clusters[j]
                # Only consider merge across different origins or same subject/theme type
                ids2 = quote_id_set(c2['quotes'])
                if not ids1 or not ids2:
                    continue
                intersection = len(ids1 & ids2)
                union = len(ids1 | ids2)
                jaccard = (intersection / union) if union > 0 else 0.0
                if jaccard >= 0.6:
                    # Merge: union quotes, prefer more populous quotes set's type
                    union_quotes = pd.concat([base['quotes'], c2['quotes']], ignore_index=True).drop_duplicates(subset=['response_id'])
                    preferred = base if len(base['quotes']) >= len(c2['quotes']) else c2
                    base = {
                        "theme_type": preferred['theme_type'],
                        "harmonized_subject": preferred.get('harmonized_subject', base.get('harmonized_subject', '')),
                        "quotes": union_quotes,
                        "pattern_summary": preferred.get('pattern_summary', base.get('pattern_summary', '')),
                        "deal_outcome_focus": preferred.get('deal_outcome_focus', base.get('deal_outcome_focus', 'mixed')),
                        "theme_origin": "hybrid" if c1.get('theme_origin') != c2.get('theme_origin') else c1.get('theme_origin', 'discovered'),
                        "research_primary_question_seed": c1.get('research_primary_question_seed') or c2.get('research_primary_question_seed')
                    }
                    ids1 = quote_id_set(base['quotes'])
                    used[j] = True
            merged.append(base)
            used[i] = True
        
        logger.info(f"🧹 Deduplicated clusters: {len(clusters)} → {len(merged)}")
        return merged

# Test function for development
def test_win_loss_generator():
    """Test the WinLossReportGenerator with sample data"""
    generator = WinLossReportGenerator(client_id="Supio")
    result = generator.generate_analyst_report()
    
    if result["success"]:
        print(f"✅ Successfully generated {result['metadata']['total_themes']} themes")
        print(f"📊 Analyzed {result['metadata']['total_quotes']} quotes from {result['metadata']['companies_analyzed']} companies")
    else:
        print(f"❌ Error: {result['error']}")
    
    return result

if __name__ == "__main__":
    test_win_loss_generator() 