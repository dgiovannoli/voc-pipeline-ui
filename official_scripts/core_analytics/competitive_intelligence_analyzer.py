#!/usr/bin/env python3

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from supabase_database import SupabaseDatabase
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

load_dotenv()

class CompetitiveIntelligenceAnalyzer:
    """
    Enhanced competitive intelligence analyzer that transforms response labeling
    into actionable win/loss insights using the 10-Criteria Executive Scorecard Framework.
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
                "weight": 1.0,
                "deal_breaker_threshold": 2.0,  # Score below this often leads to loss
                "deal_winner_threshold": 4.0    # Score above this often leads to win
            },
            "implementation_onboarding": {
                "name": "Implementation & Onboarding", 
                "category": "Core Solution",
                "description": "Deployment ease, time-to-value, setup complexity",
                "weight": 0.9,
                "deal_breaker_threshold": 2.5,
                "deal_winner_threshold": 4.0
            },
            "integration_technical_fit": {
                "name": "Integration & Technical Fit",
                "category": "Core Solution", 
                "description": "APIs, compatibility, architecture alignment, data integration",
                "weight": 0.8,
                "deal_breaker_threshold": 2.0,
                "deal_winner_threshold": 4.0
            },
            
            # Trust & Risk Factors
            "support_service_quality": {
                "name": "Support & Service Quality",
                "category": "Trust & Risk",
                "description": "Post-sale experience, responsiveness, expertise, SLAs",
                "weight": 0.9,
                "deal_breaker_threshold": 2.5,
                "deal_winner_threshold": 4.0
            },
            "security_compliance": {
                "name": "Security & Compliance",
                "category": "Trust & Risk",
                "description": "Data protection, governance, risk management, certifications",
                "weight": 1.1,  # Higher weight for security
                "deal_breaker_threshold": 2.0,
                "deal_winner_threshold": 4.0
            },
            "market_position_reputation": {
                "name": "Market Position & Reputation",
                "category": "Trust & Risk",
                "description": "Brand trust, references, analyst recognition, market presence",
                "weight": 0.8,
                "deal_breaker_threshold": 2.5,
                "deal_winner_threshold": 4.0
            },
            "vendor_stability": {
                "name": "Vendor Stability",
                "category": "Trust & Risk",
                "description": "Financial health, roadmap clarity, long-term viability",
                "weight": 1.0,
                "deal_breaker_threshold": 2.5,
                "deal_winner_threshold": 4.0
            },
            
            # Experience & Commercial Factors
            "sales_experience_partnership": {
                "name": "Sales Experience & Partnership",
                "category": "Experience & Commercial",
                "description": "Buying process quality, relationship building, trust",
                "weight": 0.9,
                "deal_breaker_threshold": 2.5,
                "deal_winner_threshold": 4.0
            },
            "commercial_terms": {
                "name": "Commercial Terms",
                "category": "Experience & Commercial",
                "description": "Price, contract flexibility, ROI, total cost of ownership",
                "weight": 1.2,  # Higher weight for pricing
                "deal_breaker_threshold": 2.0,
                "deal_winner_threshold": 4.0
            },
            "speed_responsiveness": {
                "name": "Speed & Responsiveness",
                "category": "Experience & Commercial",
                "description": "Implementation timeline, decision-making agility, response times",
                "weight": 0.8,
                "deal_breaker_threshold": 2.5,
                "deal_winner_threshold": 4.0
            }
        }
    
    def get_labeled_quotes_with_outcomes(self) -> pd.DataFrame:
        """Get labeled quotes with deal outcomes for win/loss analysis"""
        try:
            # Get Stage 2 response labeling data
            stage2_data = self.db.get_stage2_response_labeling(self.client_id)
            
            if stage2_data.empty:
                return pd.DataFrame()
            
            # Get interview metadata for deal outcomes
            metadata = self.db.get_interview_metadata(self.client_id)
            
            # Merge with metadata to get deal outcomes
            if not metadata.empty:
                # Extract interview_id from quote_id (assuming format: file_interviewid_qa_criterion)
                stage2_data['interview_id'] = stage2_data['quote_id'].str.extract(r'_(\d+)_')[0]
                stage2_data['interview_id'] = pd.to_numeric(stage2_data['interview_id'], errors='coerce')
                
                # Merge with metadata
                merged_data = stage2_data.merge(
                    metadata[['interview_id', 'deal_status', 'company']], 
                    on='interview_id', 
                    how='left'
                )
                
                # Clean deal status
                merged_data['deal_status'] = merged_data['deal_status'].fillna('Unknown')
                merged_data['deal_outcome'] = merged_data['deal_status'].map({
                    'Won': 'win',
                    'Lost': 'loss', 
                    'No Decision': 'no_decision',
                    'Unknown': 'unknown'
                }).fillna('unknown')
                
                return merged_data
            else:
                # If no metadata, add placeholder
                stage2_data['deal_outcome'] = 'unknown'
                stage2_data['company'] = 'Unknown'
                return stage2_data
                
        except Exception as e:
            st.error(f"Error getting labeled quotes: {e}")
            return pd.DataFrame()
    
    def calculate_competitive_health_scores(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate competitive health scores for each criterion"""
        if data.empty:
            return {}
        
        health_scores = {}
        
        for criterion_key, criterion_info in self.criteria_framework.items():
            criterion_data = data[data['criterion'] == criterion_key]
            
            if criterion_data.empty:
                continue
            
            # Calculate scores by deal outcome
            win_data = criterion_data[criterion_data['deal_outcome'] == 'win']
            loss_data = criterion_data[criterion_data['deal_outcome'] == 'loss']
            
            # Overall performance
            overall_avg = criterion_data['relevance_score'].mean()
            overall_std = criterion_data['relevance_score'].std()
            
            # Win vs Loss performance
            win_avg = win_data['relevance_score'].mean() if not win_data.empty else 0
            loss_avg = loss_data['relevance_score'].mean() if not loss_data.empty else 0
            
            # Deal impact analysis
            deal_breaker_rate = (criterion_data['relevance_score'] < criterion_info['deal_breaker_threshold']).mean()
            deal_winner_rate = (criterion_data['relevance_score'] >= criterion_info['deal_winner_threshold']).mean()
            
            # Win/loss correlation
            win_loss_gap = win_avg - loss_avg if win_avg > 0 and loss_avg > 0 else 0
            
            # Competitive health score (0-100)
            health_score = self._calculate_health_score(
                overall_avg, win_loss_gap, deal_breaker_rate, deal_winner_rate, criterion_info
            )
            
            health_scores[criterion_key] = {
                'criterion_name': criterion_info['name'],
                'category': criterion_info['category'],
                'overall_avg': round(overall_avg, 2),
                'win_avg': round(win_avg, 2),
                'loss_avg': round(loss_avg, 2),
                'win_loss_gap': round(win_loss_gap, 2),
                'deal_breaker_rate': round(deal_breaker_rate * 100, 1),
                'deal_winner_rate': round(deal_winner_rate * 100, 1),
                'health_score': round(health_score, 1),
                'sample_size': len(criterion_data),
                'win_sample': len(win_data),
                'loss_sample': len(loss_data),
                'weight': criterion_info['weight']
            }
        
        return health_scores
    
    def _calculate_health_score(self, overall_avg: float, win_loss_gap: float, 
                               deal_breaker_rate: float, deal_winner_rate: float, 
                               criterion_info: Dict) -> float:
        """Calculate competitive health score (0-100)"""
        
        # Base score from overall performance (0-40 points)
        base_score = min(40, overall_avg * 8)  # Scale 0-5 to 0-40
        
        # Win/loss gap bonus (0-30 points)
        gap_bonus = min(30, win_loss_gap * 15)  # Positive gap = good
        
        # Deal winner rate bonus (0-20 points)
        winner_bonus = deal_winner_rate * 20
        
        # Deal breaker penalty (0-20 points deducted)
        breaker_penalty = deal_breaker_rate * 20
        
        # Weight adjustment
        weight_multiplier = criterion_info['weight']
        
        total_score = (base_score + gap_bonus + winner_bonus - breaker_penalty) * weight_multiplier
        
        return max(0, min(100, total_score))
    
    def identify_win_loss_drivers(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Identify key drivers of wins and losses"""
        if data.empty:
            return {}
        
        drivers = {
            'win_drivers': [],
            'loss_drivers': [],
            'critical_gaps': [],
            'competitive_advantages': []
        }
        
        health_scores = self.calculate_competitive_health_scores(data)
        
        for criterion_key, score_data in health_scores.items():
            criterion_info = self.criteria_framework[criterion_key]
            
            # Win drivers (high scores in won deals)
            if score_data['win_avg'] >= 4.0 and score_data['win_sample'] >= 3:
                drivers['win_drivers'].append({
                    'criterion': criterion_info['name'],
                    'avg_score': score_data['win_avg'],
                    'sample_size': score_data['win_sample'],
                    'category': criterion_info['category']
                })
            
            # Loss drivers (low scores in lost deals)
            if score_data['loss_avg'] <= 2.5 and score_data['loss_sample'] >= 3:
                drivers['loss_drivers'].append({
                    'criterion': criterion_info['name'],
                    'avg_score': score_data['loss_avg'],
                    'sample_size': score_data['loss_sample'],
                    'category': criterion_info['category']
                })
            
            # Critical gaps (high deal breaker rate)
            if score_data['deal_breaker_rate'] >= 30:
                drivers['critical_gaps'].append({
                    'criterion': criterion_info['name'],
                    'deal_breaker_rate': score_data['deal_breaker_rate'],
                    'category': criterion_info['category']
                })
            
            # Competitive advantages (high win/loss gap)
            if score_data['win_loss_gap'] >= 1.0 and score_data['win_sample'] >= 2 and score_data['loss_sample'] >= 2:
                drivers['competitive_advantages'].append({
                    'criterion': criterion_info['name'],
                    'win_loss_gap': score_data['win_loss_gap'],
                    'category': criterion_info['category']
                })
        
        # Sort by impact
        drivers['win_drivers'].sort(key=lambda x: x['avg_score'], reverse=True)
        drivers['loss_drivers'].sort(key=lambda x: x['avg_score'])
        drivers['critical_gaps'].sort(key=lambda x: x['deal_breaker_rate'], reverse=True)
        drivers['competitive_advantages'].sort(key=lambda x: x['win_loss_gap'], reverse=True)
        
        return drivers
    
    def generate_executive_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive executive dashboard data"""
        data = self.get_labeled_quotes_with_outcomes()
        
        if data.empty:
            return {
                'error': 'No labeled quotes found. Please run Stage 2 analysis first.',
                'health_scores': {},
                'drivers': {},
                'summary_metrics': {}
            }
        
        health_scores = self.calculate_competitive_health_scores(data)
        drivers = self.identify_win_loss_drivers(data)
        
        # Calculate summary metrics
        total_quotes = len(data)
        total_deals = data['interview_id'].nunique()
        win_deals = data[data['deal_outcome'] == 'win']['interview_id'].nunique()
        loss_deals = data[data['deal_outcome'] == 'loss']['interview_id'].nunique()
        
        # Overall competitive health score
        if health_scores:
            overall_health = np.mean([score['health_score'] for score in health_scores.values()])
        else:
            overall_health = 0
        
        summary_metrics = {
            'total_quotes': total_quotes,
            'total_deals': total_deals,
            'win_deals': win_deals,
            'loss_deals': loss_deals,
            'win_rate': round(win_deals / total_deals * 100, 1) if total_deals > 0 else 0,
            'overall_health_score': round(overall_health, 1),
            'criteria_covered': len(health_scores),
            'critical_gaps_count': len(drivers.get('critical_gaps', [])),
            'competitive_advantages_count': len(drivers.get('competitive_advantages', []))
        }
        
        return {
            'health_scores': health_scores,
            'drivers': drivers,
            'summary_metrics': summary_metrics,
            'raw_data': data
        }
    
    def create_competitive_health_chart(self, health_scores: Dict[str, Any]) -> go.Figure:
        """Create competitive health radar chart"""
        if not health_scores:
            return go.Figure()
        
        # Prepare data for radar chart
        criteria_names = [score['criterion_name'] for score in health_scores.values()]
        health_values = [score['health_score'] for score in health_scores.values()]
        categories = [score['category'] for score in health_scores.values()]
        
        # Color coding by category
        colors = {
            'Core Solution': '#1f77b4',
            'Trust & Risk': '#ff7f0e', 
            'Experience & Commercial': '#2ca02c'
        }
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=health_values,
            theta=criteria_names,
            fill='toself',
            name='Competitive Health Score',
            line_color='#1f77b4',
            fillcolor='rgba(31, 119, 180, 0.3)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="Competitive Health Score by Criterion",
            height=500
        )
        
        return fig
    
    def create_win_loss_comparison_chart(self, health_scores: Dict[str, Any]) -> go.Figure:
        """Create win/loss comparison chart"""
        if not health_scores:
            return go.Figure()
        
        criteria_names = [score['criterion_name'] for score in health_scores.values()]
        win_scores = [score['win_avg'] for score in health_scores.values()]
        loss_scores = [score['loss_avg'] for score in health_scores.values()]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Won Deals',
            x=criteria_names,
            y=win_scores,
            marker_color='#2ca02c'
        ))
        
        fig.add_trace(go.Bar(
            name='Lost Deals', 
            x=criteria_names,
            y=loss_scores,
            marker_color='#d62728'
        ))
        
        fig.update_layout(
            title="Average Scores: Won vs Lost Deals",
            xaxis_title="Criteria",
            yaxis_title="Average Score",
            barmode='group',
            height=500
        )
        
        return fig
    
    def save_competitive_analysis(self, dashboard_data: Dict[str, Any]) -> bool:
        """Save competitive analysis results to database"""
        try:
            analysis_data = {
                'client_id': self.client_id,
                'generated_at': datetime.now().isoformat(),
                'summary_metrics': json.dumps(dashboard_data['summary_metrics']),
                'health_scores': json.dumps(dashboard_data['health_scores']),
                'drivers': json.dumps(dashboard_data['drivers']),
                'total_quotes_analyzed': dashboard_data['summary_metrics']['total_quotes'],
                'total_deals_analyzed': dashboard_data['summary_metrics']['total_deals'],
                'overall_health_score': dashboard_data['summary_metrics']['overall_health_score']
            }
            
            # Save to competitive_analysis table
            result = self.db.supabase.table('competitive_analysis').insert(analysis_data).execute()
            
            return True
            
        except Exception as e:
            st.error(f"Error saving competitive analysis: {e}")
            return False 