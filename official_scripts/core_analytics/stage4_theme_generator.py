#!/usr/bin/env python3
"""
Enhanced Theme Generator - Scalable Version
Combines V1's comprehensive approach with V2's two-sentence format
Designed to generate comprehensive theme sets for any client
"""

import os
import json
import logging
import pandas as pd
import re
from typing import List, Dict, Any, Tuple
import openai
from supabase_database import SupabaseDatabase
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedThemeGeneratorScalable:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.supabase = SupabaseDatabase()
        
        # Load OpenAI API key
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Load enhanced theme prompt with comprehensive approach
        self.theme_prompt = self._load_comprehensive_theme_prompt()
        
        # Quality thresholds
        self.min_evidence_strength = 3  # Minimum score for theme inclusion
        self.min_companies_per_theme = 2  # Minimum companies for cross-company validation
        self.min_findings_per_theme = 2   # Minimum findings per theme
        
        # Clustering parameters
        self.similarity_threshold = 0.3  # Minimum similarity for clustering
        self.min_cluster_size = 2  # Minimum findings per cluster
        
        # Quality control parameters
        self.allow_single_company_themes = False  # Whether to allow single-company themes
        self.require_company_data = False  # Whether to require company data (temporarily disabled for testing)
        
    def _load_comprehensive_theme_prompt(self) -> str:
        """Load the comprehensive theme generation prompt"""
        return f"""
⚠️ CRITICAL INSTRUCTION: You MUST follow these title requirements EXACTLY. If you do not follow them, your response will be rejected.

THEME TITLE REQUIREMENTS (CRITICAL - MUST FOLLOW EXACTLY):
- Titles MUST clearly identify the SPECIFIC problem from findings using exact terminology
- Use concrete, evidence-based language from actual findings - NO generic terms
- NO generic titles like "efficiency declines", "quality issues", "user satisfaction"
- MUST use specific terminology from findings (e.g., "speaker identification fails", "voice recognition errors")
- Include specific context when available (e.g., "multi-party recordings")
- Titles MUST be specific enough that the client immediately understands the exact issue
- Highlight business impact or consequence using evidence from findings

EXAMPLES OF GOOD TITLES (use this format):
- "Speaker identification failures in multi-party recordings force manual corrections"
- "Voice recognition errors affect speaker distinction in legal transcripts"
- "Transcription inaccuracies require extensive manual revisions during case preparation"

EXAMPLES OF BAD TITLES (DO NOT USE):
- "Audio quality issues disrupt user satisfaction" (too generic)
- "Workflow efficiency declines due to unclear audio quality" (too vague)
- "Transcription quality issues hinder case preparation efficiency" (not specific enough)

CRITICAL: Generate 7-10 comprehensive, business-focused themes with executive-style titles that capture SPECIFIC customer feedback and detailed insights from the interview data.

THEME COVERAGE REQUIREMENTS:
- MUST include themes that capture SPECIFIC customer pain points and feedback from the interview data
- MUST include themes for core product functionality and user experience issues with concrete details
- MUST include themes for workflow efficiency and integration challenges with specific examples
- MUST include themes for pricing and subscription models with actual customer reactions
- MUST include themes for feature adoption and user engagement with specific user behaviors
- MUST include themes for service quality and accuracy issues with detailed customer complaints
- MUST include themes for core product functionality issues that appear multiple times across interviews
- MUST include themes for technical accuracy problems that affect user workflow and satisfaction
- Each theme must use specific product terminology and customer feedback from the findings
- NO industry-specific language (e.g., no "legal", "law", "attorney", "court", "case", "evidence", "discovery", "defender", "firm", "processes" references)
- Use universal business terms: "client", "customer", "user", "organization", "business", "workflow", "process", "operations", "activities"
- CRITICAL: Replace any industry-specific terms with universal business language
- CRITICAL: Use SPECIFIC details, quotes, and customer feedback from the interview data - avoid generic statements
- CRITICAL: Pay special attention to findings marked as "Priority Finding" or containing technical accuracy issues

PRIORITY REQUIREMENTS:
- MUST prioritize client-specific findings first (client-specific findings should be the primary focus)
- MUST create dedicated themes for client-specific product issues with SPECIFIC customer feedback
- MUST ensure each client-specific finding is included in at least one theme
- MUST use specific product terminology and customer quotes from the findings
- MUST create themes that specifically address: core product functionality, user experience, workflow efficiency, integration challenges
- Quality over quantity - fewer, better themes that capture real client-specific issues with concrete details
- CRITICAL: Review all client-specific findings and ensure each major product issue gets its own dedicated theme
- CRITICAL: Use universal business language - NO industry-specific terms
- CRITICAL: Extract and use SPECIFIC customer pain points, complaints, and feedback from the interview data

CRITICAL REQUIREMENTS:
1. THEME STATEMENT REQUIREMENTS (Two-Sentence Executive Framework):
   - EXACTLY two sentences - NO MORE, NO LESS
   - Sentence 1: Decision behavior or specific problem with consequence (25-35 words max)
   - Sentence 2: Most common interviewee pain point or reaction in your own words (25-35 words max)
   - NO direct quotes in the statement - only in the quote fields
   - NO solutioning language ("indicating a need for", "suggesting", "recommending")
   - NO generic statements; must be specific and paraphrased using customer feedback details
   - NO invented numbers or company names
   - If evidence is qualitative, state it as such
   - Focus on specific product problems causing customer pain, or opportunities for improvement
   - CRITICAL: Each statement MUST be exactly two sentences, not paragraphs
   - CRITICAL: Use universal business language - NO industry-specific terms (legal, medical, financial, etc.)
   - CRITICAL: Include SPECIFIC customer pain points, complaints, and feedback details from the interview data

2. EVIDENCE-BASED REQUIREMENTS:
   - Extract SPECIFIC customer pain points, complaints, and feedback from the interview data
   - Use concrete details like timeframes, specific errors, user behaviors, and customer reactions
   - Avoid generic statements - every theme should reflect actual customer feedback
   - Use exact terminology from findings in titles and statements

3. CUSTOMER FEEDBACK REQUIREMENT:
   - Extract SPECIFIC customer pain points, complaints, and feedback from the interview data
   - Use concrete details like timeframes, specific errors, user behaviors, and customer reactions
   - Avoid generic statements - every theme should reflect actual customer feedback

4. TITLE SPECIFICITY REQUIREMENTS:
   - Every title MUST identify the exact problem using terminology from findings
   - NO generic terms like "issues", "problems", "concerns" without specific context
   - Use specific product features, errors, or user behaviors mentioned in findings
   - Include specific context (e.g., "multi-party recordings", "case preparation", "transcript review")

5. SPEAKER ACCURACY THEME REQUIREMENT:
   - CRITICAL: If findings mention speaker identification, voice recognition, or audio quality issues, create a specific theme
   - Use exact terminology from findings like "speaker identification fails", "voice recognition errors"
   - Include specific context like "multi-party recordings" or "transcript clarity"
   - Make the business impact clear (e.g., "force manual corrections", "affect speaker distinction")

EXAMPLE THEME (Follow this exact format):
Title: "Speaker identification failures in multi-party recordings force manual corrections"
Statement: "Users report that speaker identification fails in multi-party recordings, which significantly decreases transcription accuracy. Multiple customers mention that this absence affects case preparation timelines and forces them to use time-consuming manual search operations."

CRITICAL: Generate themes that follow this exact format and specificity level. NO generic titles or statements.
"""
    
    def cluster_findings_for_themes(self, findings: List[Dict]) -> List[Dict]:
        """
        Two-stage clustering approach:
        1. Category-based grouping
        2. Semantic clustering within categories
        """
        logger.info(f"🔍 Starting hybrid clustering analysis on {len(findings)} findings")
        
        # Stage 1: Group by category
        category_groups = {}
        for finding in findings:
            category = finding.get('finding_category', '')
            if category and category.strip():
                if category not in category_groups:
                    category_groups[category] = []
                category_groups[category].append(finding)
        
        logger.info(f"📊 Found {len(category_groups)} categories: {list(category_groups.keys())}")
        
        # Stage 2: Semantic clustering within each category
        theme_clusters = []
        
        for category, category_findings in category_groups.items():
            if len(category_findings) < 2:
                logger.info(f"⚠️ Skipping category '{category}': only {len(category_findings)} findings")
                continue
            
            logger.info(f"🔍 Clustering category '{category}' with {len(category_findings)} findings")
            
            # Debug: Check company data in this category
            companies_in_category = set()
            for finding in category_findings:
                # Try multiple company fields
                company = finding.get('interview_company', '')
                if not company or not company.strip():
                    company = finding.get('companies_affected', '')
                if not company or not company.strip():
                    company = finding.get('company', '')
                
                if company and company.strip():
                    companies_in_category.add(company.strip())
            logger.info(f"📊 Companies in '{category}': {list(companies_in_category)}")
            
            # Use semantic similarity to cluster within category
            clusters = self._semantic_cluster_findings(category_findings)
            
            # Validate each cluster has 2+ companies
            for i, cluster in enumerate(clusters):
                companies = set()
                for finding in cluster:
                    # Try multiple company fields
                    company = finding.get('interview_company', '')
                    if not company or not company.strip():
                        company = finding.get('companies_affected', '')
                    if not company or not company.strip():
                        company = finding.get('company', '')
                    
                    if company and company.strip():
                        companies.add(company.strip())
                
                logger.info(f"🔍 Cluster {i+1} companies: {list(companies)}")
                
                # Check if we have valid company data
                has_valid_companies = len(companies) >= self.min_companies_per_theme
                has_any_companies = len(companies) > 0
                
                if has_valid_companies or (not self.require_company_data and has_any_companies):
                    confidence = self._calculate_cluster_confidence(cluster)
                    theme_clusters.append({
                        'category': category,
                        'findings': cluster,
                        'companies': list(companies),
                        'confidence': confidence,
                        'cluster_id': f"{category}_cluster_{i+1}",
                        'finding_ids': [f.get('finding_id', '') for f in cluster],
                        'cross_company': has_valid_companies
                    })
                    logger.info(f"✅ Created cluster '{category}_cluster_{i+1}': {len(companies)} companies, {len(cluster)} findings, confidence: {confidence:.2f}, cross-company: {has_valid_companies}")
                else:
                    logger.info(f"⚠️ Rejected cluster in '{category}': only {len(companies)} companies")
        
        # Stage 3: Cross-category semantic clustering for important patterns
        logger.info(f"🔍 Performing cross-category semantic clustering on all {len(findings)} findings")
        cross_category_clusters = self._semantic_cluster_findings(findings)
        
        for i, cluster in enumerate(cross_category_clusters):
            if len(cluster) < 2:
                continue
                
            # Check if this cluster spans multiple categories
            categories_in_cluster = set()
            for finding in cluster:
                category = finding.get('finding_category', '')
                if category:
                    categories_in_cluster.add(category)
            
            # Only create cross-category clusters if they span multiple categories
            if len(categories_in_cluster) > 1:
                logger.info(f"🔍 Found cross-category cluster {i+1} spanning {len(categories_in_cluster)} categories: {list(categories_in_cluster)}")
                
                # Check companies in this cross-category cluster
                companies = set()
                for finding in cluster:
                    company = finding.get('interview_company', '')
                    if company and company.strip():
                        companies.add(company.strip())
                
                # For cross-category clusters, we can be more lenient with company requirements
                # since these represent important cross-cutting issues
                min_companies_for_cross_category = max(2, self.min_companies_per_theme - 1)
                
                if len(companies) >= min_companies_for_cross_category:
                    confidence = self._calculate_cluster_confidence(cluster)
                    theme_clusters.append({
                        'category': f'Cross_Category_{i+1}',
                        'findings': cluster,
                        'companies': list(companies),
                        'confidence': confidence,
                        'cluster_id': f"cross_category_cluster_{i+1}",
                        'finding_ids': [f.get('finding_id', '') for f in cluster],
                        'cross_company': len(companies) >= self.min_companies_per_theme
                    })
                    logger.info(f"✅ Created cross-category cluster {i+1}: {len(companies)} companies, {len(cluster)} findings, confidence: {confidence:.2f}")
                else:
                    logger.info(f"⚠️ Rejected cross-category cluster {i+1}: only {len(companies)} companies (minimum {min_companies_for_cross_category})")
        
        # Stage 4: Priority-based clustering for high-impact findings that don't cluster naturally
        logger.info(f"🔍 Checking for high-impact findings that need special treatment")
        
        # Find findings that appear in Priority Finding category (indicating high importance)
        priority_findings = []
        for finding in findings:
            if finding.get('finding_category') == 'Priority Finding':
                priority_findings.append(finding)
        
        # For each priority finding, check if it has related findings across categories
        for priority_finding in priority_findings:
            priority_text = priority_finding.get('finding_statement', '').lower()
            
            # Find related findings by looking for similar key concepts
            related_findings = [priority_finding]
            
            for finding in findings:
                if finding.get('finding_id') == priority_finding.get('finding_id'):
                    continue  # Skip self
                    
                finding_text = finding.get('finding_statement', '').lower()
                
                # Check for semantic similarity using key terms (industry-agnostic)
                priority_words = set(priority_text.split())
                finding_words = set(finding_text.split())
                
                # Find common significant words (longer than 4 chars)
                common_words = [w for w in priority_words.intersection(finding_words) if len(w) > 4]
                
                # If they share significant terms and are from different categories, consider them related
                if len(common_words) >= 2 and finding.get('finding_category') != priority_finding.get('finding_category'):
                    related_findings.append(finding)
            
            # If we found related findings across categories, create a special cluster
            if len(related_findings) >= 2:
                companies = set()
                for finding in related_findings:
                    company = finding.get('interview_company', '')
                    if company and company.strip():
                        companies.add(company.strip())
                
                if len(companies) >= 2:  # Lower threshold for priority-based clusters
                    confidence = self._calculate_cluster_confidence(related_findings)
                    theme_clusters.append({
                        'category': f'Priority_Cross_Category_{priority_finding.get("finding_id")}',
                        'findings': related_findings,
                        'companies': list(companies),
                        'confidence': confidence,
                        'cluster_id': f"priority_cross_category_{priority_finding.get('finding_id')}",
                        'finding_ids': [f.get('finding_id', '') for f in related_findings],
                        'cross_company': len(companies) >= self.min_companies_per_theme
                    })
                    logger.info(f"✅ Created priority-based cross-category cluster for F{priority_finding.get('finding_id')}: {len(companies)} companies, {len(related_findings)} findings, confidence: {confidence:.2f}")
        
        logger.info(f"🎯 Generated {len(theme_clusters)} valid theme clusters (including priority-based)")
        return theme_clusters
    
    def _semantic_cluster_findings(self, findings: List[Dict]) -> List[List[Dict]]:
        """
        Use TF-IDF and cosine similarity to cluster findings semantically
        """
        if len(findings) < 2:
            return []
        
        # Extract text for clustering
        texts = []
        for finding in findings:
            # Combine finding statement and quotes for clustering
            finding_text = finding.get('finding_statement', '')
            primary_quote = finding.get('primary_quote', '')
            secondary_quote = finding.get('secondary_quote', '')
            
            combined_text = f"{finding_text} {primary_quote} {secondary_quote}".strip()
            if combined_text:  # Only add non-empty texts
                texts.append(combined_text)
            else:
                texts.append("placeholder text")  # Fallback for empty texts
        
        # Create TF-IDF vectors
        try:
            vectorizer = TfidfVectorizer(
                max_features=500,  # Reduced features
                stop_words='english',
                ngram_range=(1, 1),  # Simplified n-grams
                min_df=1,
                max_df=0.95
            )
            
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Ensure similarity matrix is valid (no negative values)
            similarity_matrix = np.clip(similarity_matrix, 0, 1)
            
            # Use DBSCAN for clustering with adjusted parameters
            clustering = DBSCAN(
                eps=0.7,  # Higher threshold for more inclusive clustering
                min_samples=2,  # Minimum cluster size
                metric='precomputed'
            )
            
            # Convert similarity to distance (1 - similarity)
            distance_matrix = 1 - similarity_matrix
            
            # Ensure distance matrix is valid
            distance_matrix = np.clip(distance_matrix, 0, 1)
            
            # Perform clustering
            cluster_labels = clustering.fit_predict(distance_matrix)
            
            # Group findings by cluster
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label == -1:  # Noise points
                    continue
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(findings[i])
            
            # Return clusters as list of lists
            cluster_list = list(clusters.values())
            
            logger.info(f"🔍 Semantic clustering created {len(cluster_list)} clusters from {len(findings)} findings")
            return cluster_list
            
        except Exception as e:
            logger.error(f"❌ Error in semantic clustering: {e}")
            # Fallback: return findings as single cluster if clustering fails
            return [findings]
    
    def _calculate_cluster_confidence(self, cluster: List[Dict]) -> float:
        """
        Calculate confidence score for a cluster (0-1 scale)
        """
        if not cluster:
            return 0.0
        
        # Company diversity (0-0.4 points)
        companies = set()
        for finding in cluster:
            # Try multiple company fields
            company = finding.get('interview_company', '')
            if not company or not company.strip():
                company = finding.get('companies_affected', '')
            if not company or not company.strip():
                company = finding.get('company', '')
            
            if company and company.strip():
                companies.add(company.strip())
        
        company_diversity = min(len(companies) / 4.0, 0.4)  # Max 0.4 for 4+ companies
        
        # Evidence strength (0-0.3 points)
        evidence_scores = []
        for finding in cluster:
            evidence_strength = finding.get('evidence_strength', 0)
            if isinstance(evidence_strength, (int, float)):
                evidence_scores.append(evidence_strength)
            else:
                evidence_scores.append(3)  # Default score
        
        avg_evidence = sum(evidence_scores) / len(evidence_scores) if evidence_scores else 3
        evidence_score = min(avg_evidence / 8.0, 0.3)  # Max 0.3 for perfect evidence
        
        # Cluster size (0-0.2 points)
        cluster_size_score = min(len(cluster) / 6.0, 0.2)  # Max 0.2 for 6+ findings
        
        # Quote quality (0-0.1 points)
        quote_score = 0.0
        for finding in cluster:
            primary_quote = finding.get('primary_quote', '')
            if primary_quote and len(primary_quote.strip()) > 50:
                quote_score += 0.05
            secondary_quote = finding.get('secondary_quote', '')
            if secondary_quote and len(secondary_quote.strip()) > 50:
                quote_score += 0.05
        
        quote_score = min(quote_score, 0.1)
        
        total_confidence = company_diversity + evidence_score + cluster_size_score + quote_score
        
        return min(total_confidence, 1.0)
    
    def validate_cross_company_theme(self, theme: Dict, findings: List[Dict]) -> Tuple[bool, str]:
        """
        Validate that themes actually represent cross-company patterns
        """
        try:
            supporting_finding_ids = theme.get('supporting_finding_ids', '').split(',')
            companies_involved = set()
            
            for finding_id in supporting_finding_ids:
                finding_id = finding_id.strip()
                if not finding_id:
                    continue
                    
                # Find the finding in our data
                finding = self._get_finding_by_id(finding_id, findings)
                if finding:
                    # Try multiple company fields
                    company = finding.get('interview_company', '')
                    if not company or not company.strip():
                        company = finding.get('companies_affected', '')
                    if not company or not company.strip():
                        company = finding.get('company', '')
                    
                    if company and company.strip():
                        companies_involved.add(company.strip())
            
            # Require minimum 2 different companies
            if len(companies_involved) < self.min_companies_per_theme:
                return False, f"Only {len(companies_involved)} companies involved (minimum {self.min_companies_per_theme})"
            
            return True, f"Validated across {len(companies_involved)} companies: {', '.join(companies_involved)}"
            
        except Exception as e:
            logger.error(f"Error validating cross-company theme: {e}")
            return False, f"Validation error: {str(e)}"
    
    def _get_finding_by_id(self, finding_id: str, findings: List[Dict]) -> Dict:
        """Get finding by ID from the findings list"""
        for finding in findings:
            if finding.get('finding_id') == finding_id:
                return finding
        return {}
    
    def calculate_theme_evidence_strength(self, theme: Dict, findings: List[Dict]) -> int:
        """
        Score theme quality based on evidence strength (0-8 scale)
        """
        score = 0
        
        # Company diversity (0-3 points)
        companies = set()
        supporting_finding_ids = theme.get('supporting_finding_ids', '').split(',')
        
        for finding_id in supporting_finding_ids:
            finding_id = finding_id.strip()
            if not finding_id:
                continue
                
            finding = self._get_finding_by_id(finding_id, findings)
            if finding:
                # Try multiple company fields
                company = finding.get('interview_company', '')
                if not company or not company.strip():
                    company = finding.get('companies_affected', '')
                if not company or not company.strip():
                    company = finding.get('company', '')
                
                if company and company.strip():
                    companies.add(company.strip())
        
        if len(companies) >= 4:
            score += 3
        elif len(companies) >= 3:
            score += 2
        elif len(companies) >= 2:
            score += 1
        
        # Quote quality (0-3 points)
        primary_quote = theme.get('primary_quote', '')
        secondary_quote = theme.get('secondary_quote', '')
        
        if primary_quote and len(primary_quote.strip()) > 50:
            score += 2
        if secondary_quote and len(secondary_quote.strip()) > 50:
            score += 1
        
        # Specificity (0-2 points)
        theme_statement = theme.get('theme_statement', '')
        if 'specific' in theme_statement.lower() or any(company in theme_statement for company in companies):
            score += 1
        if len(theme_statement) > 100:  # Longer, more detailed statements
            score += 1
        
        return score
    
    def apply_quality_thresholds(self, themes: List[Dict], findings: List[Dict]) -> List[Dict]:
        """
        Only keep themes that meet quality standards
        """
        quality_themes = []
        
        for theme in themes:
            # Validate cross-company requirement (only if company data is required)
            if self.require_company_data:
                is_valid, validation_msg = self.validate_cross_company_theme(theme, findings)
                
                if not is_valid:
                    logger.warning(f"Rejecting theme {theme.get('theme_id', 'unknown')}: {validation_msg}")
                    continue
            
            # Calculate evidence strength
            evidence_strength = self.calculate_theme_evidence_strength(theme, findings)
            
            if evidence_strength >= 5:  # High quality threshold
                theme['evidence_strength'] = 'Strong'
                theme['evidence_score'] = evidence_strength
                quality_themes.append(theme)
                logger.info(f"✅ Accepted theme {theme.get('theme_id', 'unknown')} with Strong evidence (score: {evidence_strength})")
            elif evidence_strength >= self.min_evidence_strength:  # Medium quality threshold
                theme['evidence_strength'] = 'Moderate'
                theme['evidence_score'] = evidence_strength
                quality_themes.append(theme)
                logger.info(f"✅ Accepted theme {theme.get('theme_id', 'unknown')} with Moderate evidence (score: {evidence_strength})")
            else:
                logger.warning(f"Rejecting theme {theme.get('theme_id', 'unknown')}: Insufficient evidence (score: {evidence_strength})")
        
        return quality_themes
    
    def identify_real_cross_company_patterns(self, findings: List[Dict]) -> Dict:
        """
        Identify actual patterns across companies using hybrid clustering
        """
        logger.info(f"🔍 Starting hybrid clustering pattern identification")
        
        # Use clustering to identify patterns
        theme_clusters = self.cluster_findings_for_themes(findings)
        
        # Convert clusters to pattern format
        patterns = {}
        for cluster in theme_clusters:
            category = cluster['category']
            if category not in patterns:
                patterns[category] = {'companies': set(), 'findings': []}
            
            patterns[category]['companies'].update(cluster['companies'])
            patterns[category]['findings'].extend(cluster['findings'])
        
        # Return patterns with 2+ companies OR clusters with valid findings (when company data is not required)
        real_patterns = {}
        for category, data in patterns.items():
            if len(data['companies']) >= self.min_companies_per_theme:
                real_patterns[category] = data
            elif not self.require_company_data and len(data['findings']) >= 2:
                # Create pattern from clusters even without company data
                real_patterns[category] = data
        
        logger.info(f"📊 Identified {len(real_patterns)} real cross-company patterns using clustering")
        for category, data in real_patterns.items():
            logger.info(f"   {category}: {len(data['companies'])} companies, {len(data['findings'])} findings")
        
        return real_patterns
    
    def _get_findings_json(self) -> str:
        """Convert findings to JSON format for LLM processing with proper validation and client-specific prioritization"""
        try:
            # Get findings from database
            findings = self.supabase.get_stage3_findings_list(self.client_id)
            
            if not findings:
                logger.warning(f"No findings found for client {self.client_id}")
                return ""
            
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(findings)
            
            # Validate company identification
            company_field = self._identify_company_field(df)
            if not company_field:
                logger.error("PROCESSING HALTED: Cannot verify company identification")
                return ""
            
            # Filter and prioritize findings based on classification
            prioritized_findings = []
            
            # First, prioritize client-specific findings
            client_specific_findings = []
            market_trend_findings = []
            unclassified_findings = []
            
            for _, finding in df.iterrows():
                classification = finding['classification'].strip() if pd.notna(finding['classification']) else ''
                
                if f"{self.client_id}-specific".lower() in classification.lower():
                    client_specific_findings.append(finding)
                elif "market trend" in classification.lower():
                    market_trend_findings.append(finding)
                else:
                    unclassified_findings.append(finding)
            
            logger.info(f"📊 Classification breakdown:")
            logger.info(f"   {self.client_id}-specific findings: {len(client_specific_findings)}")
            logger.info(f"   Market trend findings: {len(market_trend_findings)}")
            logger.info(f"   Unclassified findings: {len(unclassified_findings)}")
            
            # Prioritize client-specific findings first, then market trends, then unclassified
            prioritized_findings.extend(client_specific_findings)
            prioritized_findings.extend(market_trend_findings)
            prioritized_findings.extend(unclassified_findings)
            
            # Ensure all required columns exist
            required_columns = [
                'finding_id', 'finding_statement', company_field, 'date', 
                'deal_status', 'interviewee_name', 'supporting_response_ids', 
                'evidence_strength', 'finding_category', 'criteria_met', 
                'priority_level', 'primary_quote', 'secondary_quote', 'quote_attributions',
                'classification', 'classification_reasoning'
            ]
            
            for col in required_columns:
                if col not in df.columns:
                    df[col] = ""
            
            # Add metadata columns if available
            metadata_columns = ['segment', 'role', 'deal_value', 'industry']
            for col in metadata_columns:
                if col not in df.columns:
                    df[col] = ""
            
            # Convert prioritized findings to list of dictionaries (JSON format)
            findings_list = []
            for finding in prioritized_findings:
                finding_dict = {}
                for col in required_columns + metadata_columns:
                    finding_dict[col] = finding.get(col, "")
                findings_list.append(finding_dict)
            
            # Convert to JSON string
            findings_json = json.dumps(findings_list, indent=2)
            
            logger.info(f"📊 Prepared {len(findings_list)} prioritized findings in JSON format")
            logger.info(f"   Priority order: {self.client_id}-specific → Market trends → Unclassified")
            return findings_json
            
        except Exception as e:
            logger.error(f"❌ Error getting findings JSON: {e}")
            return ""
    
    def _identify_company_field(self, df: pd.DataFrame) -> str:
        """Identify the correct company field in the DataFrame"""
        company_fields = ['interview_company', 'companies_affected', 'company', 'organization', 'firm']
        
        for field in company_fields:
            if field in df.columns:
                # Check if the field has meaningful data
                non_empty_values = df[field].dropna().astype(str).str.strip()
                if len(non_empty_values[non_empty_values != '']) > 0:
                    logger.info(f"✅ Identified company field: {field}")
                    return field
        
        # If no company field with data is found, use interview_company as default
        if 'interview_company' in df.columns:
            logger.warning("⚠️ No company field with data found, using interview_company as default")
            return 'interview_company'
        
        logger.warning("⚠️ No company field found in findings data")
        return ""
    
    def _call_llm_for_themes(self, findings_json: str) -> str:
        """Call OpenAI API to generate comprehensive themes using the enhanced protocol"""
        try:
            # Prepare the prompt with findings data
            full_prompt = f"""
{self.theme_prompt}

FINDINGS DATA TO ANALYZE:
{findings_json}

MANDATORY EXECUTION INSTRUCTIONS:
1. Execute the CRITICAL DATA VALIDATION first
2. Process through each step systematically
3. Complete all validation checkpoints before proceeding
4. Generate COMPREHENSIVE themes with specific details and actionable insights
5. Ensure all output meets executive communication standards

CRITICAL: You MUST reference actual finding IDs from the provided data. Every theme and alert must have at least one valid finding ID in the supporting_finding_ids field. Do NOT generate new finding IDs.

COMPREHENSIVE THEME REQUIREMENTS:
- Generate 7-10 comprehensive themes that cover the full spectrum of customer insights
- Each theme should capture specific, detailed patterns from 2-4 related findings
- Focus on concrete examples and specific customer experiences with attribution
- Include nuanced insights rather than broad categories
- Maintain cross-company validation for each theme
- Use detailed narrative with company examples and business impact

THEME STATEMENT REQUIREMENTS (Two-Sentence Executive Framework):
- EXACTLY two sentences
- Sentence 1: Decision behavior or specific problem with consequence
- Sentence 2: Summarize the most common interviewee pain point or reaction in your own words (no direct quotes)
- No solutioning language
- No generic statements; must be specific and paraphrased
- No invented numbers or company names
- If evidence is qualitative, state it as such
- Focus on specific product problems causing customer pain, or opportunities for improvement

COMPREHENSIVE THEME CATEGORIES TO COVER:
1. Product Quality Issues (audio quality, accuracy, content isolation)
2. Cost and Efficiency Concerns (transcription costs, turnaround times, operational efficiency)
3. Market Adoption Barriers (subscription fatigue, adoption challenges)
4. Revenue Impact Issues (billable hours, pricing models)
5. Competitive Advantages (AI capabilities, efficiency gains)
6. Integration and Workflow Needs (platform integration, workflow optimization)
7. User Experience Problems (audio recording, interface issues)

OUTPUT REQUIREMENTS:
- Output a single JSON object with two arrays: 'themes' and 'strategic_alerts'.
- Each theme and alert MUST be based on actual finding content, not generic statements.
- CRITICAL: Use ONLY the exact finding IDs from the provided data (e.g., F1, F2, F3, etc.). Do NOT generate new finding IDs.
- Themes should be specific and actionable business insights with concrete details.
- Avoid generic, template-like language.
- Base themes on the actual finding statements, not assumptions.
- Generate 7-10 comprehensive themes to capture detailed patterns.
- Include 3-8 strategic alerts for high-value single-company findings.
- Do NOT generate or invent quotes. Leave quote fields empty - they will be populated by the system.
- Do NOT generate or invent finding IDs. Use ONLY the exact finding IDs from the provided data.

CRITICAL THEME STATEMENT REQUIREMENTS:
- Theme statements MUST use the two-sentence executive framework
- Sentence 1: Decision behavior or specific problem with consequence
- Sentence 2: Most common interviewee pain point or reaction in your own words
- DO NOT use solutioning language like "indicating a need for", "suggesting", "recommending", "requiring"
- Focus on describing what patterns reveal about competitive dynamics
- Use executive-appropriate language without implementation recommendations
- Include specific details and concrete examples from findings

JSON OUTPUT FORMAT:
{{
  "themes": [
    {{
      "theme_id": "T1",
      "theme_title": "Business-focused title with clear impact",
      "theme_statement": "Sentence 1: Decision behavior or specific problem with consequence. Sentence 2: Most common interviewee pain point or reaction in your own words.",
      "classification": "REVENUE_THREAT|COMPETITIVE_VULNERABILITY|MARKET_OPPORTUNITY|COST_EFFICIENCY|COMPETITIVE_ADVANTAGE",
      "deal_context": "...",
      "metadata_insights": "...",
      "primary_quote": "",
      "secondary_quote": "",
      "competitive_flag": true,
      "supporting_finding_ids": "F1,F2,F3",
      "company_ids": ""
    }}
    // ... 7-10 comprehensive themes
  ],
  "strategic_alerts": [
    {{
      "alert_id": "A1",
      "alert_title": "Single-company high-impact finding",
      "alert_statement": "Sentence 1: Decision behavior or specific problem with consequence. Sentence 2: Most common interviewee pain point or reaction in your own words.",
      "alert_classification": "REVENUE_THREAT|COMPETITIVE_VULNERABILITY|MARKET_OPPORTUNITY",
      "strategic_implications": "...",
      "primary_alert_quote": "",
      "secondary_alert_quote": "",
      "supporting_alert_finding_ids": "F1,F2",
      "alert_company_ids": ""
    }}
    // ... 3-8 strategic alerts
  ]
}}

IMPORTANT: 
- supporting_finding_ids and supporting_alert_finding_ids must use ONLY the exact finding IDs from the provided data (e.g., F1, F2, F3, etc.). Do NOT create new finding IDs.
- Leave all quote fields empty ("") - they will be populated by the system using real quotes from the findings.

CRITICAL REQUIREMENTS:
1. FINDING ID REQUIREMENT: Every theme and alert MUST reference at least one actual finding ID from the provided data in the supporting_finding_ids field. Use ONLY the exact finding IDs from the input data (e.g., F1, F2, F3, etc.).

2. QUOTE REQUIREMENTS:
   - Leave all quote fields empty ("") - do NOT generate or invent quotes
   - The system will automatically populate quotes from the referenced findings
   - Do NOT paraphrase or create any quote text

3. VALIDATION: Before outputting any theme or alert, verify that:
   - The supporting_finding_ids field contains at least one valid finding ID from the input data
   - The finding ID actually exists in the provided findings list
   - All quote fields are left empty for system population

Return ONLY the JSON object (no explanations or extra text).
"""
            
            # Call OpenAI API
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert B2B SaaS competitive intelligence analyst specializing in win/loss analysis and executive communication. You MUST follow the user's instructions EXACTLY. Do not deviate from the specified format or requirements."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            llm_output = response.choices[0].message.content.strip()
            logger.info(f"✅ LLM generated comprehensive theme response ({len(llm_output)} characters)")
            
            return llm_output
            
        except Exception as e:
            logger.error(f"❌ Error calling LLM for comprehensive themes: {str(e)}")
            return ""
    
    def _parse_llm_themes_output(self, llm_output: str) -> List[Dict]:
        """Parse themes and alerts from LLM JSON output"""
        try:
            # Extract JSON from LLM output
            json_start = llm_output.find('{')
            json_end = llm_output.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("No JSON found in LLM output")
                return []
            
            json_str = llm_output[json_start:json_end]
            
            # Parse JSON
            data = json.loads(json_str)
            
            themes = []
            
            # Process themes
            if 'themes' in data:
                for theme in data['themes']:
                    theme['theme_type'] = 'theme'
                    themes.append(theme)
            
            # Process strategic alerts
            if 'strategic_alerts' in data:
                for alert in data['strategic_alerts']:
                    alert['theme_type'] = 'strategic_alert'
                    themes.append(alert)
            
            logger.info(f"✅ Parsed {len(themes)} themes/alerts from LLM output")
            return themes
            
        except Exception as e:
            logger.error(f"❌ Error parsing LLM themes output: {str(e)}")
            return []
    
    def _match_themes_to_findings(self, themes: List[Dict], findings: List[Dict]) -> List[Dict]:
        """Match themes to findings using hybrid approach: always try keyword-based matching first, then fallback to embedding-based association"""
        try:
            # Step 1: Create embeddings for all findings
            logger.info("🔍 Creating embeddings for all findings...")
            finding_embeddings = self._create_finding_embeddings(findings)
            
            # Step 2: Enhance theme associations using hybrid matching
            logger.info("🔍 Enhancing theme associations using hybrid matching (keyword first for all themes)...")
            enhanced_themes = []
            
            # Create embeddings for all themes in batch
            theme_texts = []
            theme_indices = []
            
            for i, theme in enumerate(themes):
                theme_text = f"{theme.get('theme_title', '')} {theme.get('theme_statement', '')}"
                if theme_text.strip():
                    theme_texts.append(theme_text)
                    theme_indices.append(i)
            
            # Batch API call for theme embeddings
            theme_embeddings = []
            if theme_texts:
                theme_embeddings = self._get_batch_embeddings(theme_texts)
            
            # Process each theme with hybrid matching
            for i, theme in enumerate(themes):
                theme_embedding = []
                if i in theme_indices:
                    embedding_index = theme_indices.index(i)
                    if embedding_index < len(theme_embeddings):
                        theme_embedding = theme_embeddings[embedding_index]
                
                # Always try keyword-based matching first for all themes
                keyword_matches = self._find_keyword_matches(theme, findings)
                
                if keyword_matches:
                    # Use keyword matches if found
                    similar_findings = keyword_matches
                    logger.info(f"✅ Theme {theme.get('theme_id', 'unknown')}: Found {len(similar_findings)} keyword matches")
                else:
                    # Fall back to embedding-based matching
                    similar_findings = self._find_similar_findings(
                        theme_embedding, finding_embeddings, findings, 
                        top_k=8, similarity_threshold=0.5
                    )
                    logger.info(f"🔍 Theme {theme.get('theme_id', 'unknown')}: Using embedding matches ({len(similar_findings)} found)")
                
                # Update theme with enhanced associations
                if similar_findings:
                    theme['supporting_finding_ids'] = ','.join([f['finding_id'] for f in similar_findings])
                    
                    # Extract companies from all associated findings
                    companies = set()
                    for finding in similar_findings:
                        # Try interview_company first
                        company = finding.get('interview_company', '')
                        if company and company.strip():
                            companies.add(company.strip())
                            logger.info(f"✅ Added company from interview_company: {company.strip()}")
                        else:
                            # Try companies_affected (JSON array)
                            companies_affected = finding.get('companies_affected', '')
                            if companies_affected:
                                try:
                                    # Parse JSON array
                                    import json
                                    company_list = json.loads(companies_affected)
                                    if isinstance(company_list, list):
                                        for comp in company_list:
                                            if comp and comp.strip():
                                                companies.add(comp.strip())
                                                logger.info(f"✅ Added company from companies_affected: {comp.strip()}")
                                except (json.JSONDecodeError, TypeError):
                                    # If not JSON, treat as string
                                    if companies_affected and companies_affected.strip():
                                        companies.add(companies_affected.strip())
                                        logger.info(f"✅ Added company from companies_affected (string): {companies_affected.strip()}")
                    
                    theme['company_ids'] = ','.join(list(companies))
                    logger.info(f"🔍 Theme {theme.get('theme_id', 'unknown')} companies: {list(companies)}")
                    
                    # Validate cross-company pattern
                    if len(companies) >= 2:
                        theme['cross_company_validated'] = True
                        logger.info(f"✅ Theme {theme.get('theme_id', 'unknown')}: {len(similar_findings)} findings, {len(companies)} companies")
                    else:
                        theme['cross_company_validated'] = False
                        logger.warning(f"⚠️ Theme {theme.get('theme_id', 'unknown')}: Only {len(companies)} companies")
                
                # Attach quotes from enhanced findings
                self._attach_quotes_to_theme(theme, findings)
                enhanced_themes.append(theme)
            
            logger.info(f"✅ Enhanced associations for {len(enhanced_themes)} themes/alerts")
            return enhanced_themes
            
        except Exception as e:
            logger.error(f"❌ Error matching themes to findings: {str(e)}")
            return themes
    
    def _find_keyword_matches(self, theme: Dict, findings: List[Dict]) -> List[Dict]:
        """Find keyword-based matches for specific themes"""
        theme_title = theme.get('theme_title', '').lower()
        theme_statement = theme.get('theme_statement', '').lower()
        theme_text = f"{theme_title} {theme_statement}"
        
        # Define keyword patterns for specific themes
        keyword_patterns = {
            'speaker': {
                'keywords': ['speaker', 'voice recognition', 'multi-speaker', 'speaker identification', 'speaker accuracy'],
                'finding_keywords': ['speaker', 'voice recognition', 'multi-speaker', 'speaker identification', 'overlapping dialogue', 'speaker attribution']
            },
            'accuracy': {
                'keywords': ['accuracy', 'inaccurate', 'transcription accuracy', 'accuracy issues'],
                'finding_keywords': ['accuracy', 'inaccurate', 'transcription accuracy', 'errors', 'corrections']
            },
            'cost': {
                'keywords': ['cost', 'pricing', 'subscription', 'expensive', 'affordable'],
                'finding_keywords': ['cost', 'pricing', 'subscription', 'expensive', 'affordable', 'monthly fee']
            },
            'integration': {
                'keywords': ['integration', 'connect', 'platform', 'workflow'],
                'finding_keywords': ['integration', 'connect', 'platform', 'workflow', 'tools']
            },
            'turnaround': {
                'keywords': ['turnaround', 'speed', 'time', 'delivery', 'quick'],
                'finding_keywords': ['turnaround', 'speed', 'time', 'delivery', 'quick', 'minutes', 'hours']
            }
        }
        
        # Check if theme matches any keyword pattern
        matched_pattern = None
        for pattern_name, pattern_data in keyword_patterns.items():
            if any(keyword in theme_text for keyword in pattern_data['keywords']):
                matched_pattern = pattern_name
                break
        
        if not matched_pattern:
            return []
        
        # Find findings that match the pattern
        matching_findings = []
        for finding in findings:
            finding_text = f"{finding.get('finding_statement', '')} {finding.get('primary_quote', '')}".lower()
            
            # Check if finding contains relevant keywords
            pattern_keywords = keyword_patterns[matched_pattern]['finding_keywords']
            if any(keyword in finding_text for keyword in pattern_keywords):
                matching_findings.append(finding)
        
        # Sort by confidence and return top matches
        matching_findings.sort(key=lambda x: x.get('enhanced_confidence', 0), reverse=True)
        
        # Return top 5 matches for the pattern
        return matching_findings[:5]
    
    def _create_finding_embeddings(self, findings: List[Dict]) -> Dict[str, List[float]]:
        """Create embeddings for all findings using batch API call"""
        embeddings = {}
        
        # Prepare all texts for batch embedding
        texts = []
        finding_ids = []
        
        for finding in findings:
            # Combine finding text for embedding
            finding_text = f"{finding.get('finding_statement', '')} {finding.get('primary_quote', '')} {finding.get('secondary_quote', '')}"
            if finding_text.strip():
                texts.append(finding_text)
                finding_ids.append(finding['finding_id'])
        
        if not texts:
            logger.warning("No valid texts found for embedding")
            return embeddings
        
        # Single batch API call for all findings
        try:
            batch_embeddings = self._get_batch_embeddings(texts)
            
            # Map embeddings back to finding IDs
            for i, embedding in enumerate(batch_embeddings):
                if i < len(finding_ids):
                    embeddings[finding_ids[i]] = embedding
            
            logger.info(f"✅ Created embeddings for {len(embeddings)} findings using batch API call")
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Error in batch embedding creation: {str(e)}")
            return embeddings
    
    def _get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get OpenAI embeddings for multiple texts in a single batch call"""
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"❌ Error getting batch embeddings: {str(e)}")
            return []
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get OpenAI embedding for single text (fallback method)"""
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"❌ Error getting embedding: {str(e)}")
            return []
    
    def _find_similar_findings(self, theme_embedding: List[float], finding_embeddings: Dict, 
                              findings: List[Dict], top_k: int = 5, similarity_threshold: float = 0.7) -> List[Dict]:
        """Find most similar findings using cosine similarity"""
        similarities = []
        
        for finding_id, finding_embedding in finding_embeddings.items():
            if theme_embedding and finding_embedding:
                similarity = cosine_similarity([theme_embedding], [finding_embedding])[0][0]
                if similarity >= similarity_threshold:
                    similarities.append((finding_id, similarity))
        
        # Sort by similarity and return top_k findings
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_finding_ids = [fid for fid, _ in similarities[:top_k]]
        
        # Return actual finding objects
        similar_findings = []
        for finding in findings:
            if finding['finding_id'] in top_finding_ids:
                similar_findings.append(finding)
        
        # Debug logging
        if similar_findings:
            logger.info(f"🔍 Found {len(similar_findings)} similar findings (threshold: {similarity_threshold})")
            for finding in similar_findings[:3]:  # Log first 3
                company = finding.get('interview_company', 'NO_COMPANY')
                logger.info(f"   - {finding['finding_id']}: {company}")
        else:
            logger.warning(f"⚠️ No similar findings found with threshold {similarity_threshold}")
        
        return similar_findings
    
    def _attach_quotes_to_theme(self, theme: Dict, findings: List[Dict]):
        """Attach quotes from associated findings to theme"""
        supporting_finding_ids = theme.get('supporting_finding_ids', '')
        if supporting_finding_ids:
            finding_ids = [fid.strip() for fid in supporting_finding_ids.split(',') if fid.strip()]
            
            # Get primary quote from first finding
            if finding_ids:
                first_finding = self._get_finding_by_id(finding_ids[0], findings)
                if first_finding:
                    primary_quote = first_finding.get('primary_quote', '')
                    if primary_quote:
                        theme['primary_quote'] = primary_quote
                    
                    # Get secondary quote from second finding if available
                    if len(finding_ids) > 1:
                        second_finding = self._get_finding_by_id(finding_ids[1], findings)
                        if second_finding:
                            secondary_quote = second_finding.get('primary_quote', '')
                            if secondary_quote:
                                theme['secondary_quote'] = secondary_quote
        
        # For strategic alerts, get alert quotes
        if theme.get('theme_type') == 'strategic_alert':
            alert_finding_ids = theme.get('supporting_alert_finding_ids', '')
            if alert_finding_ids:
                finding_ids = [fid.strip() for fid in alert_finding_ids.split(',') if fid.strip()]
                if finding_ids:
                    first_finding = self._get_finding_by_id(finding_ids[0], findings)
                    if first_finding:
                        primary_quote = first_finding.get('primary_quote', '')
                        if primary_quote:
                            theme['primary_alert_quote'] = primary_quote
                    
                    # Get secondary alert quote from second finding if available
                    if len(finding_ids) > 1:
                        second_finding = self._get_finding_by_id(finding_ids[1], findings)
                        if second_finding:
                            secondary_quote = second_finding.get('primary_quote', '')
                            if secondary_quote:
                                theme['secondary_alert_quote'] = secondary_quote
    
    def _save_themes_to_database(self, themes: List[Dict[str, Any]]) -> bool:
        """Save themes to database with enhanced validation"""
        try:
            saved_count = 0
            
            for theme in themes:
                try:
                    # Determine if this is a theme or strategic alert
                    theme_type = theme.get('theme_type', 'theme')
                    if theme_type == 'strategic_alert':
                        # Map alert fields to dedicated alert columns
                        theme_data = {
                            'client_id': self.client_id,
                            'theme_id': theme.get('alert_id', ''),
                            'theme_type': 'strategic_alert',
                            'competitive_flag': False,
                            
                            # Theme fields (empty for alerts)
                            'theme_title': '',
                            'theme_statement': '',
                            'classification': '',
                            'deal_context': '',
                            'metadata_insights': '',
                            'primary_quote': '',
                            'secondary_quote': '',
                            'supporting_finding_ids': '',
                            'company_ids': '',
                            'evidence_strength': theme.get('evidence_strength', 'Weak'),
                            'evidence_score': theme.get('evidence_score', 0),
                            
                            # Strategic Alert fields
                            'alert_title': theme.get('alert_title', ''),
                            'alert_statement': theme.get('alert_statement', ''),
                            'alert_classification': theme.get('alert_classification', ''),
                            'strategic_implications': theme.get('strategic_implications', ''),
                            'primary_alert_quote': theme.get('primary_alert_quote', ''),
                            'secondary_alert_quote': theme.get('secondary_alert_quote', ''),
                            'supporting_alert_finding_ids': theme.get('supporting_alert_finding_ids', ''),
                            'alert_company_ids': theme.get('alert_company_ids', ''),
                        }
                    else:
                        # Regular theme
                        theme_data = {
                            'client_id': self.client_id,
                            'theme_id': theme.get('theme_id', ''),
                            'theme_type': 'theme',
                            'competitive_flag': self._convert_to_boolean(theme.get('competitive_flag', False)),
                            'theme_title': theme.get('theme_title', ''),
                            'theme_statement': theme.get('theme_statement', ''),
                            'classification': theme.get('classification', ''),
                            'deal_context': theme.get('deal_context', ''),
                            'metadata_insights': theme.get('metadata_insights', ''),
                            'primary_quote': theme.get('primary_quote', ''),
                            'secondary_quote': theme.get('secondary_quote', ''),
                            'supporting_finding_ids': theme.get('supporting_finding_ids', ''),
                            'company_ids': theme.get('company_ids', ''),
                            'evidence_strength': theme.get('evidence_strength', 'Weak'),
                            'evidence_score': theme.get('evidence_score', 0),
                            
                            # Strategic Alert fields (empty for themes)
                            'alert_title': '',
                            'alert_statement': '',
                            'alert_classification': '',
                            'strategic_implications': '',
                            'primary_alert_quote': '',
                            'secondary_alert_quote': '',
                            'supporting_alert_finding_ids': '',
                            'alert_company_ids': '',
                        }
                    
                    # Save to database
                    success = self.supabase.save_theme(theme_data, self.client_id)
                    if success:
                        saved_count += 1
                        logger.info(f"✅ Saved theme/alert: {theme_data.get('theme_id', 'unknown')}")
                    else:
                        logger.warning(f"⚠️ Failed to save theme/alert: {theme_data.get('theme_id', 'unknown')}")
                
                except Exception as e:
                    logger.error(f"❌ Error saving theme {theme.get('theme_id', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"✅ Successfully saved {saved_count}/{len(themes)} themes/alerts to database")
            return saved_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error saving themes to database: {str(e)}")
            return False
    
    def analyze_themes(self) -> bool:
        """Main method to analyze findings and generate comprehensive themes"""
        try:
            logger.info(f"🎯 Starting Comprehensive Stage 4 theme analysis for client: {self.client_id}")
            
            # Get findings from database
            findings = self.supabase.get_stage3_findings_list(self.client_id)
            
            if not findings:
                logger.warning(f"No Stage 3 findings found for client {self.client_id}")
                return False
            
            logger.info(f"📊 Found {len(findings)} findings to analyze")
            
            # Debug: Check available fields in findings
            if findings:
                sample_finding = findings[0]
                logger.info(f"🔍 Sample finding fields: {list(sample_finding.keys())}")
                logger.info(f"🔍 Sample finding company field: {sample_finding.get('interview_company', 'NOT_FOUND')}")
                logger.info(f"🔍 Sample finding company field (alt): {sample_finding.get('company', 'NOT_FOUND')}")
                logger.info(f"🔍 Sample finding company field (alt2): {sample_finding.get('organization', 'NOT_FOUND')}")
            
            # Identify real cross-company patterns using clustering
            real_patterns = self.identify_real_cross_company_patterns(findings)
            
            if not real_patterns:
                logger.warning("No real cross-company patterns found in findings")
                return False
            
            # Generate themes from findings
            themes = self._generate_themes_from_findings(findings)
            
            if not themes:
                logger.warning("No themes generated from findings")
                return False
            
            # Filter out themes with invalid IDs (unknown, empty, or missing)
            valid_themes = []
            for theme in themes:
                theme_id = theme.get('theme_id', '')
                theme_title = theme.get('theme_title', '')
                
                if theme_id and theme_id.strip() and theme_id != 'unknown' and theme_title and theme_title.strip():
                    valid_themes.append(theme)
                else:
                    logger.warning(f"⚠️ Filtering out invalid theme: id='{theme_id}', title='{theme_title[:50]}...'")
            
            if not valid_themes:
                logger.warning("No valid themes after filtering")
                return False
            
            logger.info(f"📊 Generated {len(themes)} themes, {len(valid_themes)} valid after filtering")
            themes = valid_themes
            
            # Apply quality thresholds
            quality_themes = self.apply_quality_thresholds(themes, findings)
            
            if not quality_themes:
                logger.warning("No themes passed quality thresholds")
                return False
            
            logger.info(f"✅ {len(quality_themes)} themes passed quality validation")
            
            # Save themes to database
            success = self._save_themes_to_database(quality_themes)
            
            if success:
                logger.info(f"✅ Comprehensive Stage 4 theme analysis completed successfully for client {self.client_id}")
            else:
                logger.error(f"❌ Failed to save themes to database for client {self.client_id}")
            
            return success
                
        except Exception as e:
            logger.error(f"Error in comprehensive theme analysis: {e}")
            return False
    
    def _generate_themes_from_findings(self, findings: List[Dict]) -> List[Dict]:
        """Generate comprehensive themes from findings using LLM with enhanced protocol"""
        try:
            if not findings:
                logger.warning("No findings provided for theme generation")
                return []
            
            # Convert findings to JSON format for LLM
            findings_json = self._get_findings_json()
            if not findings_json:
                logger.warning("No findings data available for theme generation")
                return []
            
            # Call LLM to generate comprehensive themes (expects JSON output)
            llm_output = self._call_llm_for_themes(findings_json)
            if not llm_output:
                logger.warning("No response from LLM")
                return []
            
            # Parse themes and alerts from LLM JSON output
            themes = self._parse_llm_themes_output(llm_output)
            if not themes:
                logger.warning("No themes parsed from LLM output")
                return []
            
            # Match themes to findings and attach real quotes
            themes = self._match_themes_to_findings(themes, findings)
            
            logger.info(f"🎯 Generated {len(themes)} comprehensive themes/alerts from findings")
            return themes
            
        except Exception as e:
            logger.error(f"Error generating comprehensive themes from findings: {e}")
            return []
    
    def _convert_to_boolean(self, value: str) -> bool:
        """Convert string value to boolean"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', 'yes', '1', 'y']
        return False
    
    def process_themes(self, client_id: str = None) -> bool:
        """Process comprehensive themes for a specific client"""
        if client_id:
            self.client_id = client_id
        
        return self.analyze_themes()

def main():
    """Main function to run comprehensive Stage 4 theme analysis"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python stage4_theme_generator.py <client_id>")
        sys.exit(1)
    client_id = sys.argv[1]
    
    analyzer = EnhancedThemeGeneratorScalable(client_id=client_id)
    success = analyzer.process_themes()
    
    if success:
        print(f"✅ Comprehensive Stage 4 theme analysis completed successfully for client: {client_id}")
    else:
        print(f"❌ Comprehensive Stage 4 theme analysis failed for client: {client_id}")
    
    return success

if __name__ == "__main__":
    main() 