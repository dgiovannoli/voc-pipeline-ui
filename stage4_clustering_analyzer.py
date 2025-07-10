#!/usr/bin/env python3

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import logging
from typing import Dict, List, Optional, Tuple
import yaml
from collections import defaultdict, Counter
import re
from sklearn.metrics.pairwise import cosine_similarity
from scipy.cluster.hierarchy import linkage, fcluster
from sentence_transformers import SentenceTransformer

# Import Supabase database manager
from supabase_database import SupabaseDatabase

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Stage4ClusteringAnalyzer:
    """
    Stage 4: Clustering-Based Theme Generation - Uses agglomerative clustering and LLM for high-quality stage4_themes
    """
    
    def __init__(self, config_path="config/analysis_config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=4000,
            temperature=0.2
        )
        
        # Initialize Supabase database
        self.db = SupabaseDatabase()
        
        # Initialize sentence transformer for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Processing metrics
        self.processing_metrics = {
            "total_findings_processed": 0,
            "stage4_themes_generated": 0,
            "high_strength_stage4_themes": 0,
            "competitive_stage4_themes": 0,
            "clusters_formed": 0,
            "processing_errors": 0
        }
    
    def load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Default configuration for clustering-based Stage 4"""
        return {
            'stage4': {
                'min_confidence_threshold': 2.0,
                'min_companies_per_theme': 2,
                'min_findings_per_theme': 1,
                'min_quotes_per_theme': 2,
                'max_stage4_themes_per_category': 8,
                'clustering': {
                    'target_clusters': 20,  # Target 10-30 clusters
                    'similarity_threshold': 0.5,  # Start with 0.5, adjust based on results
                    'min_cluster_size': 2,
                    'max_cluster_size': 50
                },
                'quality_scoring': {
                    'specificity_threshold': 2.0,
                    'actionability_threshold': 1.5,
                    'evidence_strength_threshold': 1.5,
                    'min_overall_score': 2.0
                },
                'competitive_keywords': [
                    'vs', 'versus', 'compared to', 'alternative', 'competitor',
                    'switching', 'migration', 'evaluation', 'selection process',
                    'vendor', 'solution', 'platform', 'tool', 'competition',
                    'market leader', 'industry standard', 'best in class'
                ]
            }
        }
    
    def get_findings_for_analysis(self, client_id: str = 'default') -> pd.DataFrame:
        """Get findings for clustering analysis"""
        try:
            findings_df = self.db.get_stage3_findings(client_id=client_id)
            
            if findings_df.empty:
                logger.warning(f"No findings found for client {client_id}")
                return pd.DataFrame()
            
            # Filter by confidence threshold
            stage4_config = self.config.get('stage4', {})
            min_confidence = stage4_config.get('min_confidence_threshold', 2.0)
            
            if 'confidence_score' in findings_df.columns:
                findings_df = findings_df[findings_df['confidence_score'] >= min_confidence]
            
            logger.info(f"📊 Retrieved {len(findings_df)} findings for clustering analysis")
            return findings_df
            
        except Exception as e:
            logger.error(f"❌ Error getting findings: {e}")
            return pd.DataFrame()
    
    def cluster_findings(self, findings_df: pd.DataFrame) -> Tuple[List[int], Dict]:
        """Cluster findings using agglomerative clustering"""
        logger.info("🔍 Clustering findings using agglomerative clustering...")
        
        if findings_df.empty:
            logger.warning("No findings to cluster")
            return [], {}
        
        # Get finding descriptions
        findings_text = findings_df['description'].tolist()
        
        # Generate embeddings
        logger.info("Generating embeddings...")
        embeddings = self.embedding_model.encode(findings_text)
        
        # Compute similarity matrix
        logger.info("Computing similarity matrix...")
        similarity_matrix = cosine_similarity(embeddings)
        
        # Convert to distance matrix
        distance_matrix = 1 - similarity_matrix
        
        # Get clustering config
        stage4_config = self.config.get('stage4', {})
        clustering_config = stage4_config.get('clustering', {})
        target_clusters = clustering_config.get('target_clusters', 20)
        similarity_threshold = clustering_config.get('similarity_threshold', 0.5)
        
        # Perform agglomerative clustering
        logger.info(f"Performing clustering with target {target_clusters} clusters...")
        Z = linkage(distance_matrix, method='average')
        
        # Try different thresholds to get target number of clusters
        thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        best_threshold = similarity_threshold
        best_cluster_count = 0
        
        for threshold in thresholds:
            labels = fcluster(Z, t=threshold, criterion='distance')
            cluster_count = len(set(labels))
            
            if 10 <= cluster_count <= 30:
                best_threshold = threshold
                best_cluster_count = cluster_count
                break
            elif cluster_count > best_cluster_count and cluster_count <= 30:
                best_threshold = threshold
                best_cluster_count = cluster_count
        
        # Use best threshold
        labels = fcluster(Z, t=best_threshold, criterion='distance')
        
        logger.info(f"✅ Clustering complete: {len(set(labels))} clusters formed with threshold {best_threshold}")
        
        # Create cluster info
        cluster_info = {
            'threshold_used': best_threshold,
            'cluster_count': len(set(labels)),
            'distance_matrix': distance_matrix,
            'linkage_matrix': Z
        }
        
        return labels, cluster_info
    
    def analyze_clusters(self, findings_df: pd.DataFrame, labels: List[int]) -> List[Dict]:
        """Analyze clusters and prepare for theme generation"""
        logger.info("📊 Analyzing clusters...")
        
        findings_df = findings_df.copy()
        findings_df['cluster_id'] = labels
        
        clusters = []
        stage4_config = self.config.get('stage4', {})
        min_findings = stage4_config.get('min_findings_per_theme', 1)
        
        for cluster_id in sorted(set(labels)):
            cluster_findings = findings_df[findings_df['cluster_id'] == cluster_id]
            
            if cluster_findings.shape[0] < min_findings:
                continue
            
            # Calculate cluster metrics
            avg_confidence = 0.0
            avg_impact = 0.0
            
            if 'enhanced_confidence' in cluster_findings.columns:
                avg_confidence = float(cluster_findings['enhanced_confidence'].mean())
            elif 'confidence_score' in cluster_findings.columns:
                avg_confidence = float(cluster_findings['confidence_score'].mean())
                
            if 'impact_score' in cluster_findings.columns:
                avg_impact = float(cluster_findings['impact_score'].mean())
            
            # Check for competitive stage4_themes
            competitive_flag = self._check_competitive_cluster(cluster_findings)
            
            # Get supporting quotes
            supporting_quotes = cluster_findings['description'].tolist()
            
            # Create cluster analysis
            cluster_analysis = {
                'cluster_id': cluster_id,
                'findings': cluster_findings.to_dict('records'),
                'companies': [],  # Skip company analysis for now
                'company_count': 0,
                'finding_count': int(cluster_findings.shape[0]),
                'avg_confidence': avg_confidence,
                'avg_impact_score': avg_impact,
                'competitive_flag': competitive_flag,
                'supporting_quotes': supporting_quotes,
                'finding_ids': cluster_findings['id'].tolist() if 'id' in cluster_findings.columns else [],
                'criteria_covered': cluster_findings['criterion'].unique().tolist() if 'criterion' in cluster_findings.columns else []
            }
            
            clusters.append(cluster_analysis)
        
        logger.info(f"✅ Analyzed {len(clusters)} valid clusters")
        return clusters
    
    def _check_competitive_cluster(self, cluster_findings: pd.DataFrame) -> bool:
        """Check if cluster contains competitive stage4_themes"""
        stage4_config = self.config.get('stage4', {})
        competitive_keywords = stage4_config.get('competitive_keywords', [])
        
        # Check all findings in cluster
        for _, finding in cluster_findings.iterrows():
            description = str(finding.get('description', '')).lower()
            for keyword in competitive_keywords:
                if keyword.lower() in description:
                    return True
        
        return False
    
    def generate_theme_statements(self, clusters: List[Dict], client_id: str = 'default') -> List[Dict]:
        """Generate theme statements using LLM for each cluster"""
        logger.info("📝 Generating theme statements using LLM...")
        
        stage4_themes = []
        logger.debug(f"generate_theme_statements: clusters type={type(clusters)}, len={len(clusters)}")
        
        for cluster in clusters:
            try:
                logger.debug(f"Processing cluster {cluster.get('cluster_id', 'unknown')} for theme generation")
                theme_statement = self._generate_cluster_theme(cluster)
                
                if theme_statement is None or (isinstance(theme_statement, str) and theme_statement.strip() == ""):
                    logger.debug(f"Skipping cluster {cluster.get('cluster_id', 'unknown')} - no theme statement generated")
                    continue
                
                # Determine theme strength and category
                theme_strength = self._determine_theme_strength(cluster)
                theme_category = self._determine_theme_category(cluster)
                
                # Get primary and secondary quotes
                supporting_quotes = cluster.get('supporting_quotes', [])
                primary_quote = supporting_quotes[0] if len(supporting_quotes) > 0 else ""
                secondary_quote = supporting_quotes[1] if len(supporting_quotes) > 1 else ""
                
                # Create theme object
                theme = {
                    'theme_statement': theme_statement,
                    'theme_category': theme_category,
                    'theme_strength': theme_strength,
                    'interview_companies': cluster.get('companies', []),
                    'supporting_finding_ids': cluster.get('finding_ids', []),
                    'supporting_response_ids': [],  # Will be populated from findings
                    'deal_status_distribution': {"won": 0, "lost": 0},  # Placeholder
                    'competitive_flag': cluster.get('competitive_flag', False),
                    'business_implications': f"Impact score: {cluster.get('avg_impact_score', 0.0):.1f}, affecting {cluster.get('company_count', 0)} companies",
                    'primary_theme_quote': primary_quote,
                    'secondary_theme_quote': secondary_quote,
                    'quote_attributions': f"Primary: {cluster.get('companies', ['Unknown'])[0] if cluster.get('companies') else 'Unknown'}",
                    'evidence_strength': theme_strength,
                    'avg_confidence_score': cluster.get('avg_confidence', 0.0),
                    'company_count': cluster.get('company_count', 0),
                    'finding_count': cluster.get('finding_count', 0),
                    'quotes': json.dumps(cluster.get('supporting_quotes', [])),
                    'pattern_type': 'clustering_based',
                    'cluster_id': cluster.get('cluster_id', 0),
                    'client_id': client_id
                }
                
                stage4_themes.append(theme)
                
                # Update metrics
                if theme_strength == 'High':
                    self.processing_metrics["high_strength_stage4_themes"] += 1
                if cluster.get('competitive_flag', False):
                    self.processing_metrics["competitive_stage4_themes"] += 1
                
                logger.debug(f"Generated theme for cluster {cluster.get('cluster_id', 'unknown')}: {theme_statement[:100]}...")
                
            except Exception as e:
                logger.error(f"❌ Error generating theme for cluster {cluster.get('cluster_id', 'unknown')}: {e}")
                self.processing_metrics["processing_errors"] += 1
                continue
        
        logger.info(f"✅ Generated {len(stage4_themes)} theme statements")
        return stage4_themes
    
    def _generate_cluster_theme(self, cluster: Dict) -> Optional[str]:
        """Generate theme statement for a cluster using LLM"""
        
        # Prepare cluster data for LLM
        companies = ', '.join(cluster['companies'])
        finding_count = cluster['finding_count']
        avg_impact = cluster['avg_impact_score']
        competitive_flag = cluster['competitive_flag']
        criteria_covered = ', '.join(cluster['criteria_covered']) if cluster['criteria_covered'] else 'Multiple criteria'
        
        # Get sample quotes (limit to 5 for token efficiency)
        sample_quotes = cluster['supporting_quotes'][:5]
        quotes_text = '\n'.join([f"- {quote}" for quote in sample_quotes])
        
        prompt = ChatPromptTemplate.from_template("""
        You are a senior business analyst creating executive-ready theme statements from clustered findings.

        TASK: Generate a concise, business-relevant theme statement that summarizes the key insight from this cluster of findings.

        CLUSTER DATA:
        - Companies: {companies}
        - Finding Count: {finding_count}
        - Average Impact Score: {avg_impact}
        - Competitive Flag: {competitive_flag}
        - Criteria Covered: {criteria_covered}
        
        SAMPLE FINDINGS:
        {quotes}
        
        REQUIREMENTS:
        1. **Specific Issue/Opportunity**: Identify concrete problems or opportunities
        2. **Measurable Impact**: Include quantifiable outcomes or business implications
        3. **Business Context**: Add relevant business context
        4. **No Prescriptive Language**: Avoid "should", "must", "need to"
        5. **Concise**: Keep to 1-2 sentences maximum
        6. **Evidence-Based**: Base on actual findings, not generic observations
        
        EXAMPLES OF GOOD THEME STATEMENTS:
        - "Speed and turnaround time directly impact competitive positioning and user satisfaction in time-sensitive legal workflows"
        - "Accuracy concerns create competitive vulnerability and reduce user confidence in Rev's core value proposition"
        - "Integration gaps force manual steps, slowing legal workflows and prompting integration requests"
        
        EXAMPLES OF BAD THEME STATEMENTS:
        - "Rev should improve operational efficiency" (prescriptive)
        - "The analysis reveals moderate concerns" (generic)
        - "Strategic alignment will foster stronger relationships" (vague business speak)
        
        Generate ONE concise theme statement that captures the key business insight:
        """)
        
        try:
            response = self.llm.invoke(prompt.format(
                companies=companies,
                finding_count=finding_count,
                avg_impact=f"{avg_impact:.1f}",
                competitive_flag=competitive_flag,
                criteria_covered=criteria_covered,
                quotes=quotes_text
            ))
            
            theme_statement = response.content.strip()
            
            # Clean up the response
            if theme_statement.startswith('"') and theme_statement.endswith('"'):
                theme_statement = theme_statement[1:-1]
            
            return theme_statement
            
        except Exception as e:
            logger.error(f"❌ Error generating theme with LLM: {e}")
            return None
    
    def _determine_theme_strength(self, cluster: Dict) -> str:
        """Determine theme strength based on cluster metrics"""
        company_count = cluster['company_count']
        avg_impact = cluster['avg_impact_score']
        
        if company_count >= 5 and avg_impact >= 4.0:
            return "High"
        elif company_count >= 3 and avg_impact >= 3.0:
            return "Medium"
        else:
            return "Emerging"
    
    def _determine_theme_category(self, cluster: Dict) -> str:
        """Determine theme category based on cluster characteristics"""
        avg_impact = cluster['avg_impact_score']
        competitive_flag = cluster['competitive_flag']
        
        if competitive_flag:
            return "Competitive"
        elif avg_impact >= 4.0:
            return "Opportunity"
        elif avg_impact <= 2.0:
            return "Barrier"
        else:
            return "Strategic"
    
    def save_stage4_themes_to_supabase(self, stage4_themes: List[Dict], client_id: str = 'default'):
        """Save stage4_themes to Supabase database"""
        logger.info(f"💾 Saving {len(stage4_themes)} stage4_themes to Supabase...")
        logger.debug(f"save_stage4_themes_to_supabase: stage4_themes type={type(stage4_themes)}, len={len(stage4_themes)}")
        
        saved_count = 0
        skipped_count = 0
        
        for theme in stage4_themes:
            try:
                logger.debug(f"Saving theme: {theme.get('theme_statement', '')[:80]}")
                result = self.db.save_theme(theme, client_id=client_id)
                if result is True:
                    saved_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                logger.error(f"❌ Error saving theme: {e}")
                skipped_count += 1
        
        logger.info(f"✅ Saved {saved_count} stage4_themes to Supabase for client {client_id}")
        if skipped_count > 0:
            logger.warning(f"⚠️ Skipped {skipped_count} stage4_themes due to save failures")
        
        self.processing_metrics["stage4_themes_generated"] = saved_count
    
    def purge_old_stage4_themes(self, client_id: str = 'default'):
        """Purge old stage4_themes for the client"""
        try:
            # Delete existing stage4_themes for this client
            result = self.db.supabase.table('stage4_themes').delete().eq('client_id', client_id).execute()
            logger.info(f"🗑️ Purged old stage4_themes for client {client_id}")
        except Exception as e:
            logger.error(f"❌ Error purging old stage4_themes: {e}")
    
    def process_stage4_themes(self, client_id: str = 'default') -> Dict:
        """Main processing function for clustering-based Stage 4"""
        
        logger.info("🚀 STAGE 4: CLUSTERING-BASED THEME GENERATION")
        logger.info("=" * 60)
        
        # Purge old stage4_themes first
        self.purge_old_stage4_themes(client_id)
        
        # Get findings for analysis
        findings_df = self.get_findings_for_analysis(client_id=client_id)
        
        if findings_df.empty:
            logger.info("✅ No findings available for theme generation")
            return {"status": "no_data", "message": "No findings available"}
        
        self.processing_metrics["total_findings_processed"] = len(findings_df)
        
        # Cluster findings
        labels, cluster_info = self.cluster_findings(findings_df)
        
        if not labels:
            logger.info("✅ No clusters formed")
            return {"status": "no_clusters", "message": "No clusters formed"}
        
        self.processing_metrics["clusters_formed"] = cluster_info['cluster_count']
        
        # Analyze clusters
        logger.info("📊 Starting cluster analysis...")
        clusters = self.analyze_clusters(findings_df, labels)
        logger.info(f"📊 Cluster analysis complete: {len(clusters)} valid clusters")
        
        if not clusters:
            logger.info("✅ No valid clusters found")
            return {"status": "no_valid_clusters", "message": "No valid clusters found"}
        
        # Generate theme statements
        logger.info("📝 Starting theme generation...")
        stage4_themes = self.generate_theme_statements(clusters, client_id=client_id)
        logger.info(f"📝 Theme generation complete: {len(stage4_themes)} stage4_themes")
        
        if not stage4_themes:
            logger.info("✅ No stage4_themes generated")
            return {"status": "no_stage4_themes", "message": "No stage4_themes generated"}
        
        # Save to Supabase
        logger.info("💾 Starting theme save...")
        self.save_stage4_themes_to_supabase(stage4_themes, client_id=client_id)
        logger.info("💾 Theme save complete")
        
        # Generate summary
        summary = self.generate_summary_statistics(stage4_themes)
        
        logger.info(f"\n✅ Stage 4 complete! Generated {len(stage4_themes)} stage4_themes from {len(clusters)} clusters")
        self.print_summary_report(summary)
        
        return {
            "status": "success",
            "stage4_themes_generated": len(stage4_themes),
            "clusters_formed": len(clusters),
            "high_strength_stage4_themes": self.processing_metrics["high_strength_stage4_themes"],
            "competitive_stage4_themes": self.processing_metrics["competitive_stage4_themes"],
            "summary": summary
        }
    
    def generate_summary_statistics(self, stage4_themes: List[Dict]) -> Dict:
        """Generate summary statistics for stage4_themes"""
        if not stage4_themes:
            return {}
        
        total_stage4_themes = len(stage4_themes)
        high_strength = sum(1 for theme in stage4_themes if theme.get('theme_strength') == 'High')
        competitive = sum(1 for theme in stage4_themes if theme.get('competitive_flag', False))
        
        # Get unique companies
        all_companies = set()
        for theme in stage4_themes:
            companies = theme.get('interview_companies', [])
            all_companies.update(companies)
        
        return {
            'total_stage4_themes': total_stage4_themes,
            'high_strength': high_strength,
            'competitive_stage4_themes': competitive,
            'companies_covered': len(all_companies),
            'clusters_formed': self.processing_metrics["clusters_formed"]
        }
    
    def print_summary_report(self, summary: Dict):
        """Print summary report"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 STAGE 4 SUMMARY REPORT")
        logger.info("=" * 60)
        logger.info(f"🎯 Total Themes Generated: {summary.get('total_stage4_themes', 0)}")
        logger.info(f"🏆 High Strength Themes: {summary.get('high_strength', 0)}")
        logger.info(f"🏅 Competitive Themes: {summary.get('competitive_stage4_themes', 0)}")
        logger.info(f"🏢 Companies Covered: {summary.get('companies_covered', 0)}")
        logger.info(f"🔗 Clusters Formed: {summary.get('clusters_formed', 0)}")
        logger.info("=" * 60)

def run_stage4_clustering_analysis(client_id: str = 'default'):
    """Run clustering-based Stage 4 analysis"""
    try:
        analyzer = Stage4ClusteringAnalyzer()
        result = analyzer.process_stage4_themes(client_id=client_id)
        return result
    except Exception as e:
        logger.error(f"❌ Error in Stage 4 clustering analysis: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    result = run_stage4_clustering_analysis('Rev')
    print(f"Stage 4 result: {result}") 