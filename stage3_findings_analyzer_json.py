#!/usr/bin/env python3

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import logging
from typing import Dict, List, Optional, Tuple, Set, Any
import yaml
from collections import defaultdict, Counter
import re
import pprint
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')

# Import Supabase database manager
from supabase_database import SupabaseDatabase

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Stage3FindingsAnalyzerJSON:
    """
    Stage 3: JSON-based Enhanced Findings Identification with Buried Wins Criteria v4.0
    Outputs JSON data structure for better LLM integration and data flexibility
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
        
        # Load criteria from config
        self.criteria = self.config.get('criteria', {})
        
        # Enhanced evaluation criteria from Buried Wins v4.0
        self.evaluation_criteria = {
            'novelty': {
                'description': 'The observation is new/unexpected for the client, challenging assumptions or established beliefs',
                'trigger_question': 'Is this something the client has not previously recognized?'
            },
            'actionability': {
                'description': 'The observation suggests a clear step, fix, or action the client could take to improve outcomes',
                'trigger_question': 'Could this directly inform a roadmap item or go-to-market plan?'
            },
            'specificity': {
                'description': 'The finding is precise, detailed, and not generic. References a particular feature, workflow, market condition, or user group',
                'trigger_question': 'Is this about a concrete product aspect, metric, or process?'
            },
            'materiality': {
                'description': 'The finding has meaningful business impact—affecting revenue, customer satisfaction, retention, or competitive positioning',
                'trigger_question': 'Does this affect a key business KPI or customer segment?'
            },
            'recurrence': {
                'description': 'The same observation appears across multiple interviews or sources, suggesting a theme',
                'trigger_question': 'Is this echoed by two or more stakeholders/roles?'
            },
            'stakeholder_weight': {
                'description': 'The observation comes from a high-influence decision maker or critical user persona',
                'trigger_question': 'Does the source matter to the client\'s business priorities?'
            },
            'tension_contrast': {
                'description': 'The finding exposes a tension, tradeoff, or significant contrast, revealing friction or opportunity',
                'trigger_question': 'Does this highlight a dilemma, blocker, or gap vs. competitors?'
            },
            'metric_quantification': {
                'description': 'The finding is supported by a tangible metric, timeframe, or quantifiable outcome',
                'trigger_question': 'Is there a number or business measure that makes this impactful?'
            }
        }
        
        # Processing metrics
        self.processing_metrics = {
            "total_quotes_processed": 0,
            "patterns_identified": 0,
            "findings_generated": 0,
            "priority_findings": 0,
            "standard_findings": 0,
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
        """Default configuration for Stage 3 with enhanced scoring"""
        return {
            'stage3': {
                'confidence_thresholds': {
                    'priority_finding': 7.0,
                    'standard_finding': 5.0,
                    'minimum_confidence': 1.0
                },
                'pattern_thresholds': {
                    'minimum_quotes': 1,
                    'minimum_companies': 1,
                    'minimum_criteria_met': 1
                },
                'stakeholder_multipliers': {
                    'executive_perspective': 1.5,
                    'budget_holder_perspective': 1.5,
                    'champion_perspective': 1.3,
                    'end_user_perspective': 1.0,
                    'it_technical_perspective': 1.0
                },
                'decision_impact_multipliers': {
                    'deal_tipping_point': 2.0,
                    'differentiator_factor': 1.5,
                    'blocker_factor': 1.5,
                    'high_salience': 1.4,
                    'medium_salience': 1.2,
                    'low_salience': 1.0
                },
                'evidence_strength_multipliers': {
                    'strong_positive': 1.3,
                    'strong_negative': 1.3,
                    'perspective_shifting': 1.3,
                    'organizational_conflict': 1.2,
                    'standard_evidence': 1.0
                },
                'batch_size': 100,
                'max_patterns_per_criterion': 5,
                'max_quotes_per_finding': 3
            },
            'criteria': {
                'product_capability': {'description': 'Functionality, features, performance, and core solution fit'},
                'implementation_onboarding': {'description': 'Deployment ease, time-to-value, setup complexity'},
                'integration_technical_fit': {'description': 'APIs, data compatibility, technical architecture alignment'},
                'support_service_quality': {'description': 'Post-sale support, responsiveness, expertise, SLAs'},
                'security_compliance': {'description': 'Data protection, certifications, governance, risk management'},
                'market_position_reputation': {'description': 'Brand trust, references, analyst recognition, market presence'},
                'vendor_stability': {'description': 'Financial health, roadmap clarity, long-term viability'},
                'sales_experience_partnership': {'description': 'Buying process quality, relationship building, trust'},
                'commercial_terms': {'description': 'Price, contract flexibility, ROI, total cost of ownership'},
                'speed_responsiveness': {'description': 'Implementation timeline, decision-making speed, agility'}
            }
        }
    
    def get_scored_quotes(self, client_id: str = 'default') -> pd.DataFrame:
        """Get all quotes with scores from Supabase"""
        df = self.db.get_scored_quotes(client_id=client_id)
        logger.info(f"📊 Loaded {len(df)} scored quotes from Supabase for client {client_id}")
        return df
    
    def evaluate_finding_criteria(self, quotes_data: List[Dict]) -> Dict:
        """Evaluate quotes against the 8 Buried Wins evaluation criteria"""
        criteria_scores = {criterion: 0 for criterion in self.evaluation_criteria.keys()}
        
        # Analyze quotes for each criterion
        for quote in quotes_data:
            text = f"{quote.get('original_quote', '')} {quote.get('relevance_explanation', '')}"
            text_lower = text.lower()
            
            # Novelty check
            if any(word in text_lower for word in ['new', 'unexpected', 'surprising', 'didn\'t realize', 'first time']):
                criteria_scores['novelty'] = 1
            
            # Actionability check
            if any(word in text_lower for word in ['should', 'could', 'need to', 'must', 'recommend', 'suggest']):
                criteria_scores['actionability'] = 1
            
            # Specificity check
            if any(word in text_lower for word in ['specific', 'particular', 'exactly', 'specifically', 'concrete']):
                criteria_scores['specificity'] = 1
            
            # Materiality check
            if any(word in text_lower for word in ['revenue', 'cost', 'money', 'business', 'impact', 'critical', 'important']):
                criteria_scores['materiality'] = 1
            
            # Recurrence check (handled separately in pattern analysis)
            if len(quotes_data) >= 2:
                criteria_scores['recurrence'] = 1
            
            # Stakeholder weight check
            if any(word in text_lower for word in ['executive', 'ceo', 'cto', 'vp', 'director', 'manager']):
                criteria_scores['stakeholder_weight'] = 1
            
            # Tension contrast check
            if any(word in text_lower for word in ['but', 'however', 'although', 'despite', 'while', 'tension', 'conflict']):
                criteria_scores['tension_contrast'] = 1
            
            # Metric quantification check
            if any(word in text_lower for word in ['percent', '%', 'dollars', '$', 'million', 'thousand', 'users', 'customers']):
                criteria_scores['metric_quantification'] = 1
        
        return criteria_scores
    
    def calculate_enhanced_confidence_score(self, quotes_data: List[Dict], criteria_scores: Dict) -> float:
        """Calculate enhanced confidence score based on Buried Wins criteria"""
        base_score = sum(criteria_scores.values()) / len(self.evaluation_criteria)
        
        # Apply multipliers
        stakeholder_multiplier = self._calculate_stakeholder_multiplier(quotes_data)
        impact_multiplier = self._calculate_impact_multiplier(quotes_data)
        evidence_multiplier = self._calculate_evidence_multiplier(quotes_data)
        
        enhanced_score = base_score * stakeholder_multiplier * impact_multiplier * evidence_multiplier
        
        # Normalize to 0-10 scale
        return min(enhanced_score * 10, 10.0)
    
    def _calculate_stakeholder_multiplier(self, quotes_data: List[Dict]) -> float:
        """Calculate stakeholder multiplier based on quote sources"""
        multipliers = self.config['stage3']['stakeholder_multipliers']
        total_multiplier = 1.0
        
        for quote in quotes_data:
            text = quote.get('original_quote', '').lower()
            if any(word in text for word in ['executive', 'ceo', 'cto', 'vp']):
                total_multiplier *= multipliers['executive_perspective']
            elif any(word in text for word in ['budget', 'finance', 'cost']):
                total_multiplier *= multipliers['budget_holder_perspective']
            elif any(word in text for word in ['champion', 'advocate', 'sponsor']):
                total_multiplier *= multipliers['champion_perspective']
        
        return total_multiplier
    
    def _calculate_impact_multiplier(self, quotes_data: List[Dict]) -> float:
        """Calculate impact multiplier based on deal impact"""
        multipliers = self.config['stage3']['decision_impact_multipliers']
        total_multiplier = 1.0
        
        for quote in quotes_data:
            text = quote.get('original_quote', '').lower()
            if any(word in text for word in ['deal breaker', 'critical', 'essential']):
                total_multiplier *= multipliers['deal_tipping_point']
            elif any(word in text for word in ['differentiator', 'unique', 'advantage']):
                total_multiplier *= multipliers['differentiator_factor']
            elif any(word in text for word in ['blocker', 'obstacle', 'barrier']):
                total_multiplier *= multipliers['blocker_factor']
        
        return total_multiplier
    
    def _calculate_evidence_multiplier(self, quotes_data: List[Dict]) -> float:
        """Calculate evidence strength multiplier"""
        multipliers = self.config['stage3']['evidence_strength_multipliers']
        total_multiplier = 1.0
        
        for quote in quotes_data:
            text = quote.get('original_quote', '').lower()
            if any(word in text for word in ['strong', 'very', 'extremely']):
                total_multiplier *= multipliers['strong_positive']
            elif any(word in text for word in ['conflict', 'disagreement', 'tension']):
                total_multiplier *= multipliers['organizational_conflict']
        
        return total_multiplier
    
    def select_optimal_quotes(self, quotes_data: List[Dict], max_quotes: int = 3) -> List[Dict]:
        """Select the best quotes for a finding based on relevance and impact"""
        if len(quotes_data) <= max_quotes:
            return quotes_data
        
        # Sort by relevance score and deal weighted score
        sorted_quotes = sorted(quotes_data, 
                             key=lambda x: (x.get('relevance_score', 0), x.get('deal_weighted_score', 0)), 
                             reverse=True)
        
        return sorted_quotes[:max_quotes]
    
    def identify_enhanced_patterns(self, df: pd.DataFrame) -> Dict:
        """Identify patterns across criteria and companies"""
        patterns = {}
        
        for criterion in self.criteria.keys():
            criterion_data = df[df['criterion'] == criterion]
            if len(criterion_data) == 0:
                continue
            
            # Analyze company-specific patterns
            company_patterns = self._analyze_enhanced_company_patterns(criterion_data, criterion)
            
            # Analyze cross-company patterns
            cross_company_patterns = self._analyze_cross_company_patterns(company_patterns, criterion)
            
            patterns[criterion] = {
                'company_patterns': company_patterns,
                'cross_company_patterns': cross_company_patterns,
                'total_quotes': len(criterion_data),
                'unique_companies': criterion_data['company'].nunique()
            }
        
        return patterns
    
    def _analyze_enhanced_company_patterns(self, criterion_data: pd.DataFrame, criterion: str) -> List[Dict]:
        """Analyze patterns within individual companies"""
        patterns = []
        
        for company in criterion_data['company'].unique():
            company_quotes = criterion_data[criterion_data['company'] == company]
            
            if len(company_quotes) < self.config['stage3']['pattern_thresholds']['minimum_quotes']:
                continue
            
            # Calculate aggregate scores
            avg_relevance = company_quotes['relevance_score'].mean()
            avg_deal_score = company_quotes['deal_weighted_score'].mean()
            total_quotes = len(company_quotes)
            
            # Select representative quotes
            top_quotes = company_quotes.nlargest(3, 'relevance_score')
            selected_quotes = []
            
            for _, quote in top_quotes.iterrows():
                selected_quotes.append({
                    'quote_id': quote['quote_id'],
                    'original_quote': quote['original_quote'],
                    'relevance_score': quote['relevance_score'],
                    'deal_weighted_score': quote['deal_weighted_score'],
                    'sentiment': quote.get('sentiment', 'neutral'),
                    'interviewee_name': quote.get('interviewee_name', ''),
                    'response_id': quote.get('response_id', '')
                })
            
            pattern = {
                'company': company,
                'criterion': criterion,
                'avg_relevance_score': avg_relevance,
                'avg_deal_weighted_score': avg_deal_score,
                'total_quotes': total_quotes,
                'selected_quotes': selected_quotes,
                'pattern_type': 'company_specific'
            }
            
            patterns.append(pattern)
        
        return patterns
    
    def _analyze_cross_company_patterns(self, company_patterns: List[Dict], criterion: str) -> List[Dict]:
        """Analyze patterns across multiple companies"""
        if len(company_patterns) < self.config['stage3']['pattern_thresholds']['minimum_companies']:
            return []
        
        # Aggregate across companies
        all_quotes = []
        for pattern in company_patterns:
            all_quotes.extend(pattern['selected_quotes'])
        
        # Calculate cross-company metrics
        avg_relevance = sum(q['relevance_score'] for q in all_quotes) / len(all_quotes)
        avg_deal_score = sum(q['deal_weighted_score'] for q in all_quotes) / len(all_quotes)
        
        # Select top quotes across companies
        sorted_quotes = sorted(all_quotes, key=lambda x: x['relevance_score'], reverse=True)
        top_quotes = sorted_quotes[:self.config['stage3']['max_quotes_per_finding']]
        
        # Evaluate against Buried Wins criteria
        criteria_scores = self.evaluate_finding_criteria(top_quotes)
        confidence_score = self.calculate_enhanced_confidence_score(top_quotes, criteria_scores)
        
        # Generate finding statement
        finding_statement = self._generate_finding_statement(criterion, top_quotes, criteria_scores)
        
        pattern = {
            'criterion': criterion,
            'avg_relevance_score': avg_relevance,
            'avg_deal_weighted_score': avg_deal_score,
            'total_quotes': len(all_quotes),
            'companies_involved': [p['company'] for p in company_patterns],
            'selected_quotes': top_quotes,
            'criteria_scores': criteria_scores,
            'confidence_score': confidence_score,
            'finding_statement': finding_statement,
            'pattern_type': 'cross_company'
        }
        
        return [pattern]
    
    def _generate_finding_statement(self, criterion: str, quotes: List[Dict], criteria_scores: Dict) -> str:
        """Generate a finding statement based on quotes and criteria scores"""
        criterion_desc = self.criteria[criterion]['description']
        
        # Extract key themes from quotes
        themes = []
        for quote in quotes:
            text = quote['original_quote'].lower()
            if any(word in text for word in ['problem', 'issue', 'challenge']):
                themes.append('problem')
            elif any(word in text for word in ['benefit', 'advantage', 'positive']):
                themes.append('benefit')
            elif any(word in text for word in ['need', 'requirement', 'must']):
                themes.append('requirement')
        
        # Generate statement based on dominant theme
        if themes:
            dominant_theme = max(set(themes), key=themes.count)
            if dominant_theme == 'problem':
                return f"Companies face challenges with {criterion_desc.lower()}, particularly around implementation and integration."
            elif dominant_theme == 'benefit':
                return f"Companies value {criterion_desc.lower()} as a key differentiator in their decision-making process."
            else:
                return f"Companies have specific requirements for {criterion_desc.lower()} that influence their purchasing decisions."
        else:
            return f"Companies consider {criterion_desc.lower()} as an important factor in their evaluation process."
    
    def create_json_finding(self, pattern: Dict, finding_id: str) -> Dict:
        """Create a JSON finding structure"""
        finding = {
            'finding_id': finding_id,
            'finding_statement': pattern['finding_statement'],
            'finding_category': pattern['criterion'],
            'impact_score': pattern['avg_deal_weighted_score'],
            'confidence_score': pattern['confidence_score'],
            'supporting_quotes': [q['original_quote'] for q in pattern['selected_quotes']],
            'companies_mentioned': pattern['companies_involved'],
            'interview_company': pattern['companies_involved'][0] if pattern['companies_involved'] else None,
            'interview_date': datetime.now().date().isoformat(),
            'interview_type': 'win_loss',
            'interviewer_name': None,
            'interviewee_role': None,
            'interviewee_company': None,
            'finding_data': {
                'pattern_type': pattern['pattern_type'],
                'total_quotes': pattern['total_quotes'],
                'criteria_scores': pattern['criteria_scores'],
                'selected_quotes_details': pattern['selected_quotes']
            },
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'analysis_version': '4.0',
                'confidence_thresholds': self.config['stage3']['confidence_thresholds']
            }
        }
        
        return finding
    
    def save_json_findings_to_supabase(self, findings: List[Dict], client_id: str = 'default'):
        """Save JSON findings to Supabase"""
        saved_count = 0
        for finding in findings:
            if self.db.save_json_finding(finding, client_id=client_id):
                saved_count += 1
        
        logger.info(f"✅ Saved {saved_count}/{len(findings)} JSON findings to Supabase")
        return saved_count
    
    def process_stage3_findings_json(self, client_id: str = 'default') -> Dict:
        """Process Stage 3 findings and output JSON structure"""
        logger.info("🚀 Starting Stage 3 JSON Findings Analysis")
        
        # Get scored quotes
        df = self.get_scored_quotes(client_id=client_id)
        if df.empty:
            logger.warning("⚠️ No scored quotes found for analysis")
            return {
                'findings': [],
                'metadata': {
                    'total_findings': 0,
                    'analysis_date': datetime.now().isoformat(),
                    'source_data': 'stage2_response_labeling',
                    'client_id': client_id
                }
            }
        
        # Identify patterns
        patterns = self.identify_enhanced_patterns(df)
        
        # Generate findings
        findings = []
        finding_counter = 1
        
        for criterion, criterion_patterns in patterns.items():
            for pattern in criterion_patterns['cross_company_patterns']:
                if pattern['confidence_score'] >= self.config['stage3']['confidence_thresholds']['minimum_confidence']:
                    finding_id = f"F{finding_counter:03d}"
                    finding = self.create_json_finding(pattern, finding_id)
                    findings.append(finding)
                    finding_counter += 1
        
        # Save to Supabase
        saved_count = self.save_json_findings_to_supabase(findings, client_id)
        
        # Create output structure
        output = {
            'findings': findings,
            'metadata': {
                'total_findings': len(findings),
                'findings_saved': saved_count,
                'analysis_date': datetime.now().isoformat(),
                'source_data': 'stage2_response_labeling',
                'client_id': client_id,
                'processing_metrics': self.processing_metrics
            }
        }
        
        logger.info(f"✅ Stage 3 JSON analysis complete: {len(findings)} findings generated")
        return output
    
    def export_findings_json(self, client_id: str = 'default', filters: Optional[Dict] = None) -> str:
        """Export findings as JSON file"""
        return self.db.export_json_findings(client_id=client_id, filters=filters)

def run_stage3_json_analysis(client_id: str = 'default'):
    """Run Stage 3 JSON analysis"""
    analyzer = Stage3FindingsAnalyzerJSON()
    results = analyzer.process_stage3_findings_json(client_id=client_id)
    
    # Print summary
    print(f"\n📊 Stage 3 JSON Analysis Results:")
    print(f"   Total findings: {results['metadata']['total_findings']}")
    print(f"   Findings saved: {results['metadata']['findings_saved']}")
    print(f"   Client ID: {results['metadata']['client_id']}")
    
    # Export to JSON file
    export_file = analyzer.export_findings_json(client_id=client_id)
    if export_file:
        print(f"   Exported to: {export_file}")
    
    return results

if __name__ == "__main__":
    run_stage3_json_analysis() 