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
    
    def __init__(self, client_id: str = "default"):
        self.client_id = client_id
        self.db = SupabaseDatabase()
        
        # Base Quality Gates (will be adjusted dynamically)
        self.base_min_companies_per_theme = 2
        self.base_min_quotes_per_theme = 3     
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
            self.min_quotes_per_theme = max(2, int(avg_quotes_per_company))
            logger.info(f"📊 Adaptive Mode: Low quote density - requiring {self.min_quotes_per_theme}+ quotes per theme")
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
            
            # Apply data quality filtering
            cleaned_df = self._apply_data_quality_filtering(analyzed_df)
            
            logger.info(f"🧹 Data quality filtering: {len(analyzed_df)} → {len(cleaned_df)} quotes (removed {len(analyzed_df) - len(cleaned_df)} questions/non-verbatim content)")
            
            return cleaned_df
            
        except Exception as e:
            logger.error(f"❌ Error loading enhanced data: {e}")
            return pd.DataFrame()
    
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
            logger.info(f"   📝 Quote count: {len(quotes)} (need {self.min_quotes_per_theme})")
            if len(quotes) < self.min_quotes_per_theme:
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
            quality_score = self._calculate_quality_score(quotes, theme_type)
            company_distribution = self._analyze_company_distribution(quotes)
            
            cluster["validation_metrics"] = {
                "companies_count": unique_companies,
                "quotes_count": len(quotes),
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
        
        Weighting (aligned with Stage 4 _calculate_cluster_confidence):
        - Company Coverage: 40% (highest priority)
        - Evidence Quality: 30% 
        - Quote Volume: 20% (reduced priority)
        - Theme Coherence: 10%
        """
        score = 0.0
        
        # 1. Company Coverage (40% weight) - Stage 4 methodology
        company_col = 'company' if 'company' in quotes.columns else 'company_name'
        unique_companies = quotes[company_col].nunique()
        
        # Stage 4 formula: min(companies / 4.0, 0.4) * 10 = 0-4 points (40%)
        company_score = min(unique_companies / 4.0, 1.0) * 4.0
        score += company_score
        
        # 2. Evidence Quality (30% weight)
        avg_impact = quotes['impact_score'].mean()
        evidence_score = (avg_impact / 5.0) * 3.0  # 0-3 points (30%)
        score += evidence_score
        
        # 3. Quote Volume (20% weight) - reduced priority
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
            strength_quotes = strength_quotes[
                strength_quotes['deal_status'].str.contains('won', case=False, na=False)
            ]
        
        if len(strength_quotes) > 0:
            clusters.append({
                "theme_type": "strength",
                "harmonized_subject": subject,
                "quotes": strength_quotes,
                "pattern_summary": f"Positive customer feedback about {subject}" + 
                                 (f" from won deals" if has_deal_data else "")
            })
        
        # 2. WEAKNESS: Negative sentiment + Lost deals (or predominantly negative)
        weakness_quotes = quotes[quotes['sentiment'] == 'negative']
        if has_deal_data:
            weakness_quotes = weakness_quotes[
                weakness_quotes['deal_status'].str.contains('lost', case=False, na=False)
            ]
        
        if len(weakness_quotes) > 0:
            clusters.append({
                "theme_type": "weakness",
                "harmonized_subject": subject,
                "quotes": weakness_quotes,
                "pattern_summary": f"Negative customer feedback about {subject}" +
                                 (f" from lost deals" if has_deal_data else "")
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
                    "pattern_summary": f"Positive feedback about {subject} from lost deals - unmet market opportunity"
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
                    "pattern_summary": f"Negative feedback about {subject} from won deals - potential risk area"
                })
        
        # 5. INVESTIGATION NEEDED: Mixed/neutral sentiment or conflicting patterns
        mixed_quotes = quotes[quotes['sentiment'].isin(['mixed', 'neutral'])]
        
        # Add conflicting patterns only if we have significant volume
        if len(mixed_quotes) > 1 or (len(quotes) > 5 and len(sentiment_counts) >= 2):
            clusters.append({
                "theme_type": "investigation_needed",
                "harmonized_subject": subject,
                "quotes": mixed_quotes if len(mixed_quotes) > 0 else quotes,
                "pattern_summary": f"Mixed or unclear customer sentiment about {subject} requiring deeper analysis"
            })
        
        return clusters
    
    def _generate_theme_statements(self, validated_themes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate executive-ready theme statements for validated themes.
        
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
            
            # Generate theme statement (placeholder - will implement LLM later)
            theme_statement = self._generate_theme_statement_fallback(theme)
            
            # Select best supporting quotes
            supporting_quotes = self._select_supporting_quotes(quotes, theme_type)
            
            final_theme = {
                "theme_id": f"WL{i:03d}",
                "theme_statement": theme_statement,
                "theme_type": theme_type,
                "harmonized_subject": subject,
                "supporting_quotes": supporting_quotes,
                "all_quotes": quotes.to_dict('records'),
                "validation_metrics": theme["validation_metrics"],
                "competitive_flag": self._check_competitive_relevance(quotes),
                "generated_at": datetime.now().isoformat()
            }
            
            final_themes.append(final_theme)
        
        return final_themes
    
    def _generate_theme_statement_fallback(self, theme: Dict[str, Any]) -> str:
        """Generate a fallback theme statement without LLM"""
        quotes = theme["quotes"]
        theme_type = theme["theme_type"]
        subject = theme["harmonized_subject"]
        company_col = 'company' if 'company' in quotes.columns else 'company_name'
        companies_count = quotes[company_col].nunique()
        
        if theme_type == "strength":
            return f"Customers consistently praise {subject.lower()} as a key differentiator, with {companies_count} companies highlighting its positive impact on their decision."
        elif theme_type == "weakness":
            return f"Multiple customers cite concerns about {subject.lower()}, with {companies_count} companies identifying this as a barrier to adoption."
        else:
            return f"Mixed feedback about {subject.lower()} across {companies_count} companies suggests this area requires deeper analysis."
    
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
                "Total Quotes": metrics["quotes_count"],
                "Companies": metrics["companies_count"],
                "Avg Impact Score": f"{metrics['avg_impact_score']:.1f}",
                "Quality Score": metrics["quality_score"],
                "Competitive Flag": "Yes" if theme["competitive_flag"] else "No",
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