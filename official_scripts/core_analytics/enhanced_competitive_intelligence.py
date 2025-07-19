#!/usr/bin/env python3

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from supabase_database import SupabaseDatabase
from dotenv import load_dotenv
import plotly.graph_objects as go
import streamlit as st

load_dotenv()

class EnhancedCompetitiveIntelligence:
    """
    Hybrid competitive intelligence system that adapts to different client data types:
    - Win/Loss Analysis: For clients with true competitive deals (ShipBob)
    - Satisfaction Analysis: For self-serve clients (Rev) with usage/engagement data
    """
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.db = SupabaseDatabase()
        
        # 10-Criteria Executive Scorecard Framework
        self.criteria_framework = {
            # Core Solution Factors
            "product_capability": {
                "name": "Product Capability",
                "category": "Core Solution",
                "description": "Functionality, performance, solution fit, feature completeness",
                "weight": 1.0
            },
            "implementation_onboarding": {
                "name": "Implementation & Onboarding", 
                "category": "Core Solution",
                "description": "Deployment ease, time-to-value, setup complexity",
                "weight": 0.9
            },
            "integration_technical_fit": {
                "name": "Integration & Technical Fit",
                "category": "Core Solution", 
                "description": "APIs, compatibility, architecture alignment, data integration",
                "weight": 0.8
            },
            
            # Trust & Risk Factors
            "support_service_quality": {
                "name": "Support & Service Quality",
                "category": "Trust & Risk",
                "description": "Post-sale experience, responsiveness, expertise, SLAs",
                "weight": 0.9
            },
            "security_compliance": {
                "name": "Security & Compliance",
                "category": "Trust & Risk",
                "description": "Data protection, governance, risk management, certifications",
                "weight": 1.1
            },
            "market_position_reputation": {
                "name": "Market Position & Reputation",
                "category": "Trust & Risk",
                "description": "Brand trust, references, analyst recognition, market presence",
                "weight": 0.8
            },
            "vendor_stability": {
                "name": "Vendor Stability",
                "category": "Trust & Risk",
                "description": "Financial health, roadmap clarity, long-term viability",
                "weight": 1.0
            },
            
            # Experience & Commercial Factors
            "sales_experience_partnership": {
                "name": "Sales Experience & Partnership",
                "category": "Experience & Commercial",
                "description": "Buying process quality, relationship building, trust",
                "weight": 0.9
            },
            "commercial_terms": {
                "name": "Commercial Terms",
                "category": "Experience & Commercial",
                "description": "Price, contract flexibility, ROI, total cost of ownership",
                "weight": 1.2
            },
            "speed_responsiveness": {
                "name": "Speed & Responsiveness",
                "category": "Experience & Commercial",
                "description": "Implementation timeline, decision-making agility, response times",
                "weight": 0.8
            }
        }
    
    def detect_data_type(self) -> str:
        """Detect if this is win/loss data or satisfaction data"""
        try:
            stage1_data = self.db.get_stage1_data_responses(client_id=self.client_id)
            if stage1_data.empty:
                return "unknown"
            
            # Check deal status patterns
            deal_statuses = stage1_data['deal_status'].unique()
            
            # If all deals are "Closed Won" or similar, it's satisfaction data
            if len(deal_statuses) == 1 and any(status in ['Closed Won', 'Won', 'Customer'] for status in deal_statuses):
                return "satisfaction"
            
            # If we have mixed outcomes (Won/Lost), it's win/loss data
            if any(status in ['Lost', 'Closed Lost', 'No Decision'] for status in deal_statuses):
                return "win_loss"
            
            # Default to satisfaction for self-serve clients
            return "satisfaction"
            
        except Exception as e:
            st.error(f"Error detecting data type: {e}")
            return "unknown"
    
    def get_flattened_stage2_data(self) -> pd.DataFrame:
        """Get Stage 2 data (already flattened to one row per criterion per quote)"""
        try:
            # Get Stage 2 data
            stage2_data = self.db.get_stage2_response_labeling(self.client_id)
            
            if stage2_data.empty:
                return pd.DataFrame()
            
            # The data is already flattened, just need to rename columns to match expected format
            flattened_data = stage2_data.copy()
            
            # Map existing columns to expected format
            column_mapping = {
                'criterion': 'criterion',
                'relevance_score': 'relevance_score',
                'sentiment': 'sentiment',
                'priority': 'priority',
                'confidence': 'confidence',
                'relevance_explanation': 'explanation'
            }
            
            # Rename columns that exist
            for old_col, new_col in column_mapping.items():
                if old_col in flattened_data.columns:
                    flattened_data = flattened_data.rename(columns={old_col: new_col})
            
            # Add missing columns with defaults
            if 'overall_sentiment' not in flattened_data.columns:
                flattened_data['overall_sentiment'] = flattened_data['sentiment']
            
            if 'explanation' not in flattened_data.columns:
                flattened_data['explanation'] = ''
            
            # Select only the columns we need
            required_columns = ['quote_id', 'criterion', 'relevance_score', 'sentiment', 'overall_sentiment', 'priority', 'confidence', 'explanation']
            available_columns = [col for col in required_columns if col in flattened_data.columns]
            
            return flattened_data[available_columns]
            
        except Exception as e:
            st.error(f"Error getting flattened Stage 2 data: {e}")
            return pd.DataFrame()
    
    def merge_with_stage1_metadata(self, stage2_data: pd.DataFrame) -> pd.DataFrame:
        """Merge Stage 2 data with Stage 1 metadata"""
        try:
            if stage2_data.empty:
                return pd.DataFrame()
            
            # Get Stage 1 data for metadata
            stage1_data = self.db.get_stage1_data_responses(client_id=self.client_id)
            
            if stage1_data.empty:
                return stage2_data
            
            # Extract interview_id from quote_id (assuming format: file_interviewid_qa_criterion)
            stage2_data['interview_id'] = stage2_data['quote_id'].str.extract(r'_(\d+)_')[0]
            stage2_data['interview_id'] = pd.to_numeric(stage2_data['interview_id'], errors='coerce')
            
            # Merge with Stage 1 metadata
            merged_data = stage2_data.merge(
                stage1_data[['interview_id', 'deal_status', 'company', 'interviewee_name', 'industry', 'segment']], 
                on='interview_id', 
                how='left'
            )
            
            # Clean deal status
            merged_data['deal_status'] = merged_data['deal_status'].fillna('Unknown')
            
            # Map deal status to outcome
            merged_data['deal_outcome'] = merged_data['deal_status'].map({
                'Closed Won': 'win',
                'Won': 'win',
                'Customer': 'win',
                'Closed Lost': 'loss',
                'Lost': 'loss',
                'No Decision': 'no_decision',
                'Unknown': 'unknown'
            }).fillna('unknown')
            
            return merged_data
            
        except Exception as e:
            st.error(f"Error merging with metadata: {e}")
            return stage2_data
    
    def calculate_win_loss_metrics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate win/loss analysis metrics"""
        if data.empty:
            return {}
        
        metrics = {}
        
        for criterion_key, criterion_info in self.criteria_framework.items():
            criterion_data = data[data['criterion'] == criterion_key]
            
            if criterion_data.empty:
                continue
            
            # Calculate scores by deal outcome
            win_data = criterion_data[criterion_data['deal_outcome'] == 'win']
            loss_data = criterion_data[criterion_data['deal_outcome'] == 'loss']
            
            # Overall performance
            overall_avg = criterion_data['relevance_score'].mean()
            
            # Win vs Loss performance
            win_avg = win_data['relevance_score'].mean() if not win_data.empty else 0
            loss_avg = loss_data['relevance_score'].mean() if not loss_data.empty else 0
            
            # Win/loss correlation
            win_loss_gap = win_avg - loss_avg if win_avg > 0 and loss_avg > 0 else 0
            
            # Deal impact analysis
            deal_breaker_rate = (criterion_data['relevance_score'] < 2.0).mean() * 100
            deal_winner_rate = (criterion_data['relevance_score'] >= 4.0).mean() * 100
            
            # Competitive health score (0-100)
            health_score = self._calculate_win_loss_health_score(
                overall_avg, win_loss_gap, deal_breaker_rate, deal_winner_rate, criterion_info
            )
            
            metrics[criterion_key] = {
                'criterion_name': criterion_info['name'],
                'category': criterion_info['category'],
                'overall_avg': round(overall_avg, 2),
                'win_avg': round(win_avg, 2),
                'loss_avg': round(loss_avg, 2),
                'win_loss_gap': round(win_loss_gap, 2),
                'deal_breaker_rate': round(deal_breaker_rate, 1),
                'deal_winner_rate': round(deal_winner_rate, 1),
                'health_score': round(health_score, 1),
                'sample_size': len(criterion_data),
                'win_sample': len(win_data),
                'loss_sample': len(loss_data),
                'weight': criterion_info['weight']
            }
        
        return metrics
    
    def calculate_satisfaction_metrics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate satisfaction analysis metrics"""
        if data.empty:
            return {}
        
        metrics = {}
        
        for criterion_key, criterion_info in self.criteria_framework.items():
            criterion_data = data[data['criterion'] == criterion_key]
            
            if criterion_data.empty:
                continue
            
            # Overall performance
            overall_avg = criterion_data['relevance_score'].mean()
            
            # Sentiment analysis
            positive_data = criterion_data[criterion_data['sentiment'] == 'positive']
            negative_data = criterion_data[criterion_data['sentiment'] == 'negative']
            neutral_data = criterion_data[criterion_data['sentiment'] == 'neutral']
            
            positive_rate = len(positive_data) / len(criterion_data) * 100
            negative_rate = len(negative_data) / len(criterion_data) * 100
            neutral_rate = len(neutral_data) / len(criterion_data) * 100
            
            # Satisfaction score (weighted by relevance and sentiment)
            satisfaction_score = self._calculate_satisfaction_score(
                overall_avg, positive_rate, negative_rate, criterion_info
            )
            
            # Critical issues (high relevance + negative sentiment)
            critical_issues = criterion_data[
                (criterion_data['relevance_score'] >= 3.0) & 
                (criterion_data['sentiment'] == 'negative')
            ]
            critical_issue_rate = len(critical_issues) / len(criterion_data) * 100
            
            # Strengths (high relevance + positive sentiment)
            strengths = criterion_data[
                (criterion_data['relevance_score'] >= 3.0) & 
                (criterion_data['sentiment'] == 'positive')
            ]
            strength_rate = len(strengths) / len(criterion_data) * 100
            
            metrics[criterion_key] = {
                'criterion_name': criterion_info['name'],
                'category': criterion_info['category'],
                'overall_avg': round(overall_avg, 2),
                'positive_rate': round(positive_rate, 1),
                'negative_rate': round(negative_rate, 1),
                'neutral_rate': round(neutral_rate, 1),
                'critical_issue_rate': round(critical_issue_rate, 1),
                'strength_rate': round(strength_rate, 1),
                'satisfaction_score': round(satisfaction_score, 1),
                'sample_size': len(criterion_data),
                'weight': criterion_info['weight']
            }
        
        return metrics
    
    def _calculate_win_loss_health_score(self, overall_avg: float, win_loss_gap: float, 
                                        deal_breaker_rate: float, deal_winner_rate: float, 
                                        criterion_info: Dict) -> float:
        """Calculate competitive health score for win/loss analysis"""
        
        # Base score from overall performance (0-40 points)
        base_score = min(40, overall_avg * 8)
        
        # Win/loss gap bonus (0-30 points)
        gap_bonus = min(30, win_loss_gap * 15)
        
        # Deal winner rate bonus (0-20 points)
        winner_bonus = deal_winner_rate * 0.2
        
        # Deal breaker penalty (0-20 points deducted)
        breaker_penalty = deal_breaker_rate * 0.2
        
        # Weight adjustment
        weight_multiplier = criterion_info['weight']
        
        total_score = (base_score + gap_bonus + winner_bonus - breaker_penalty) * weight_multiplier
        
        return max(0, min(100, total_score))
    
    def _calculate_satisfaction_score(self, overall_avg: float, positive_rate: float, 
                                     negative_rate: float, criterion_info: Dict) -> float:
        """Calculate satisfaction score for satisfaction analysis"""
        
        # Base score from overall performance (0-40 points)
        base_score = min(40, overall_avg * 8)
        
        # Positive sentiment bonus (0-40 points)
        positive_bonus = positive_rate * 0.4
        
        # Negative sentiment penalty (0-30 points deducted)
        negative_penalty = negative_rate * 0.3
        
        # Weight adjustment
        weight_multiplier = criterion_info['weight']
        
        total_score = (base_score + positive_bonus - negative_penalty) * weight_multiplier
        
        return max(0, min(100, total_score))
    
    def identify_insights(self, data: pd.DataFrame, data_type: str) -> Dict[str, Any]:
        """Identify key insights based on data type"""
        if data.empty:
            return {}
        
        insights = {
            'strengths': [],
            'weaknesses': [],
            'critical_issues': [],
            'opportunities': []
        }
        
        if data_type == "win_loss":
            metrics = self.calculate_win_loss_metrics(data)
            
            for criterion_key, metric_data in metrics.items():
                criterion_info = self.criteria_framework[criterion_key]
                
                # Win drivers (high scores in won deals)
                if metric_data['win_avg'] >= 4.0 and metric_data['win_sample'] >= 3:
                    insights['strengths'].append({
                        'criterion': criterion_info['name'],
                        'avg_score': metric_data['win_avg'],
                        'sample_size': metric_data['win_sample'],
                        'category': criterion_info['category']
                    })
                
                # Loss drivers (low scores in lost deals)
                if metric_data['loss_avg'] <= 2.5 and metric_data['loss_sample'] >= 3:
                    insights['weaknesses'].append({
                        'criterion': criterion_info['name'],
                        'avg_score': metric_data['loss_avg'],
                        'sample_size': metric_data['loss_sample'],
                        'category': criterion_info['category']
                    })
                
                # Critical gaps (high deal breaker rate)
                if metric_data['deal_breaker_rate'] >= 30:
                    insights['critical_issues'].append({
                        'criterion': criterion_info['name'],
                        'deal_breaker_rate': metric_data['deal_breaker_rate'],
                        'category': criterion_info['category']
                    })
                
                # Competitive advantages (high win/loss gap)
                if metric_data['win_loss_gap'] >= 1.0 and metric_data['win_sample'] >= 2 and metric_data['loss_sample'] >= 2:
                    insights['opportunities'].append({
                        'criterion': criterion_info['name'],
                        'win_loss_gap': metric_data['win_loss_gap'],
                        'category': criterion_info['category']
                    })
        
        elif data_type == "satisfaction":
            metrics = self.calculate_satisfaction_metrics(data)
            
            for criterion_key, metric_data in metrics.items():
                criterion_info = self.criteria_framework[criterion_key]
                
                # Strengths (high satisfaction scores)
                if metric_data['satisfaction_score'] >= 70:
                    insights['strengths'].append({
                        'criterion': criterion_info['name'],
                        'satisfaction_score': metric_data['satisfaction_score'],
                        'positive_rate': metric_data['positive_rate'],
                        'category': criterion_info['category']
                    })
                
                # Weaknesses (low satisfaction scores)
                if metric_data['satisfaction_score'] <= 40:
                    insights['weaknesses'].append({
                        'criterion': criterion_info['name'],
                        'satisfaction_score': metric_data['satisfaction_score'],
                        'negative_rate': metric_data['negative_rate'],
                        'category': criterion_info['category']
                    })
                
                # Critical issues (high negative rate)
                if metric_data['critical_issue_rate'] >= 20:
                    insights['critical_issues'].append({
                        'criterion': criterion_info['name'],
                        'critical_issue_rate': metric_data['critical_issue_rate'],
                        'category': criterion_info['category']
                    })
                
                # Opportunities (high positive rate but room for improvement)
                if metric_data['positive_rate'] >= 60 and metric_data['satisfaction_score'] < 80:
                    insights['opportunities'].append({
                        'criterion': criterion_info['name'],
                        'positive_rate': metric_data['positive_rate'],
                        'satisfaction_score': metric_data['satisfaction_score'],
                        'category': criterion_info['category']
                    })
        
        # Sort by impact
        for key in insights:
            if key == 'strengths':
                insights[key].sort(key=lambda x: x.get('avg_score', x.get('satisfaction_score', 0)), reverse=True)
            elif key == 'weaknesses':
                insights[key].sort(key=lambda x: x.get('avg_score', x.get('satisfaction_score', 0)))
            elif key == 'critical_issues':
                insights[key].sort(key=lambda x: x.get('deal_breaker_rate', x.get('critical_issue_rate', 0)), reverse=True)
            elif key == 'opportunities':
                insights[key].sort(key=lambda x: x.get('win_loss_gap', x.get('positive_rate', 0)), reverse=True)
        
        return insights
    
    def generate_executive_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive executive dashboard data"""
        # Detect data type
        data_type = self.detect_data_type()
        
        # Get and process data
        stage2_data = self.get_flattened_stage2_data()
        if stage2_data.empty:
            return {
                'error': 'No Stage 2 data found. Please run Stage 2 analysis first.',
                'data_type': data_type,
                'metrics': {},
                'insights': {},
                'summary_metrics': {}
            }
        
        # Merge with metadata
        merged_data = self.merge_with_stage1_metadata(stage2_data)
        
        # Calculate metrics based on data type
        if data_type == "win_loss":
            metrics = self.calculate_win_loss_metrics(merged_data)
        elif data_type == "satisfaction":
            metrics = self.calculate_satisfaction_metrics(merged_data)
        else:
            metrics = {}
        
        # Identify insights
        insights = self.identify_insights(merged_data, data_type)
        
        # Calculate summary metrics
        total_quotes = len(merged_data)
        total_deals = merged_data['interview_id'].nunique()
        
        if data_type == "win_loss":
            win_deals = merged_data[merged_data['deal_outcome'] == 'win']['interview_id'].nunique()
            loss_deals = merged_data[merged_data['deal_outcome'] == 'loss']['interview_id'].nunique()
            win_rate = round(win_deals / total_deals * 100, 1) if total_deals > 0 else 0
            overall_score = np.mean([m['health_score'] for m in metrics.values()]) if metrics else 0
        else:
            win_rate = 100  # All customers for satisfaction analysis
            overall_score = np.mean([m['satisfaction_score'] for m in metrics.values()]) if metrics else 0
        
        summary_metrics = {
            'data_type': data_type,
            'total_quotes': total_quotes,
            'total_deals': total_deals,
            'win_rate': win_rate,
            'overall_score': round(overall_score, 1),
            'criteria_covered': len(metrics),
            'critical_issues_count': len(insights.get('critical_issues', [])),
            'strengths_count': len(insights.get('strengths', []))
        }
        
        return {
            'data_type': data_type,
            'metrics': metrics,
            'insights': insights,
            'summary_metrics': summary_metrics,
            'raw_data': merged_data
        } 