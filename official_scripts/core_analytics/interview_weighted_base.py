"""
Interview-Weighted Analysis Base Class
=====================================

Base class for interview-weighted VOC analysis that can be used across
all components in the analyst toolkit.

This provides consistent methodology for:
- Customer-level grouping
- Interview-weighted scoring
- Customer satisfaction calculation
- Problem/benefit customer identification
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class CustomerMetrics:
    """Customer-level metrics for interview-weighted analysis"""
    total_customers: int
    satisfied_customers: int
    problem_customers: int
    benefit_customers: int
    mixed_customers: int
    neutral_customers: int
    customer_satisfaction_rate: float
    overall_score: float
    performance_level: str

@dataclass
class CustomerGroup:
    """Customer group with their quotes and categorization"""
    customer_key: str
    interviewee_name: str
    company: str
    quotes: List[Dict]
    total_quotes: int
    product_complaints: List[Dict]
    benefit_discussions: List[Dict]
    neutral_discussions: List[Dict]
    customer_type: str  # 'problem', 'benefit', 'mixed', 'neutral'
    satisfaction_score: float

class InterviewWeightedBase:
    """
    Base class for interview-weighted VOC analysis
    """
    
    def __init__(self, database):
        self.db = database
    
    def group_quotes_by_customer(self, quotes_df: pd.DataFrame) -> Dict[str, CustomerGroup]:
        """
        Group quotes by customer (interview) using composite key
        """
        if quotes_df.empty:
            return {}
        
        customer_groups = {}
        
        for _, quote in quotes_df.iterrows():
            # Create composite customer key
            customer_key = f"{quote.get('interviewee_name', 'Unknown')} | {quote.get('company', 'Unknown')}"
            
            # Initialize customer group if not exists
            if customer_key not in customer_groups:
                customer_groups[customer_key] = CustomerGroup(
                    customer_key=customer_key,
                    interviewee_name=quote.get('interviewee_name', 'Unknown'),
                    company=quote.get('company', 'Unknown'),
                    quotes=[],
                    total_quotes=0,
                    product_complaints=[],
                    benefit_discussions=[],
                    neutral_discussions=[],
                    customer_type='neutral',
                    satisfaction_score=0.0
                )
            
            # Add quote to customer group
            quote_dict = quote.to_dict()
            customer_groups[customer_key].quotes.append(quote_dict)
            customer_groups[customer_key].total_quotes += 1
            
            # Categorize quote
            quote_text = quote.get('verbatim_response', '').lower()
            sentiment = quote.get('sentiment', 'neutral')
            
            if self._is_product_complaint(quote_text, sentiment):
                customer_groups[customer_key].product_complaints.append(quote_dict)
            elif self._is_benefit_discussion(quote_text, sentiment):
                customer_groups[customer_key].benefit_discussions.append(quote_dict)
            else:
                customer_groups[customer_key].neutral_discussions.append(quote_dict)
        
        # Categorize customers
        for customer_key, group in customer_groups.items():
            group.customer_type = self._categorize_customer(group)
            group.satisfaction_score = self._calculate_customer_satisfaction(group)
        
        return customer_groups
    
    def _is_product_complaint(self, text: str, sentiment: str) -> bool:
        """Identify product complaints"""
        complaint_indicators = [
            'slow', 'delayed', 'delay', 'inaccurate', 'error', 'bug', 'crash',
            'doesn\'t work', 'not working', 'problem', 'issue', 'difficult',
            'hard to use', 'confusing', 'frustrating', 'annoying', 'terrible',
            'bad', 'poor', 'awful', 'horrible', 'useless', 'broken', 'failed',
            'doesn\'t integrate', 'integration issues', 'technical problems',
            'quality issues', 'accuracy problems', 'speed issues'
        ]
        
        has_complaint_indicators = any(indicator in text for indicator in complaint_indicators)
        is_negative_sentiment = sentiment in ['negative', 'very negative']
        
        return has_complaint_indicators or is_negative_sentiment
    
    def _is_benefit_discussion(self, text: str, sentiment: str) -> bool:
        """Identify benefit discussions"""
        benefit_indicators = [
            'saves time', 'efficient', 'efficiency', 'worth it', 'valuable',
            'investment', 'return', 'benefit', 'advantage', 'improvement',
            'better', 'great', 'excellent', 'amazing', 'fantastic', 'love',
            'satisfied', 'happy', 'pleased', 'impressed', 'recommend',
            'streamlines', 'automates', 'reduces', 'increases', 'improves',
            'saves money', 'cost effective', 'productive', 'time saving'
        ]
        
        has_benefit_indicators = any(indicator in text for indicator in benefit_indicators)
        is_positive_sentiment = sentiment in ['positive', 'very positive']
        
        return has_benefit_indicators or is_positive_sentiment
    
    def _categorize_customer(self, customer_group: CustomerGroup) -> str:
        """Categorize customer based on their quotes"""
        has_complaints = len(customer_group.product_complaints) > 0
        has_benefits = len(customer_group.benefit_discussions) > 0
        has_neutral = len(customer_group.neutral_discussions) > 0
        
        if has_complaints and has_benefits:
            return 'mixed'
        elif has_complaints:
            return 'problem'
        elif has_benefits:
            return 'benefit'
        else:
            return 'neutral'
    
    def _calculate_customer_satisfaction(self, customer_group: CustomerGroup) -> float:
        """Calculate customer satisfaction score (0-10)"""
        if customer_group.customer_type == 'problem':
            return 0.0
        elif customer_group.customer_type == 'benefit':
            return 10.0
        elif customer_group.customer_type == 'mixed':
            # Mixed customers are considered satisfied but with room for improvement
            return 7.0
        else:  # neutral
            return 5.0
    
    def calculate_customer_metrics(self, customer_groups: Dict[str, CustomerGroup]) -> CustomerMetrics:
        """Calculate overall customer metrics"""
        if not customer_groups:
            return CustomerMetrics(
                total_customers=0,
                satisfied_customers=0,
                problem_customers=0,
                benefit_customers=0,
                mixed_customers=0,
                neutral_customers=0,
                customer_satisfaction_rate=0.0,
                overall_score=0.0,
                performance_level='No Data'
            )
        
        total_customers = len(customer_groups)
        problem_customers = sum(1 for group in customer_groups.values() if group.customer_type == 'problem')
        benefit_customers = sum(1 for group in customer_groups.values() if group.customer_type == 'benefit')
        mixed_customers = sum(1 for group in customer_groups.values() if group.customer_type == 'mixed')
        neutral_customers = sum(1 for group in customer_groups.values() if group.customer_type == 'neutral')
        
        # Satisfied customers = benefit + mixed + neutral (no complaints)
        satisfied_customers = benefit_customers + mixed_customers + neutral_customers
        
        # Calculate rates
        customer_satisfaction_rate = (satisfied_customers / total_customers) * 100 if total_customers > 0 else 0
        overall_score = (satisfied_customers / total_customers) * 10 if total_customers > 0 else 0
        
        # Determine performance level
        if overall_score >= 8.0:
            performance_level = "Excellent"
        elif overall_score >= 6.0:
            performance_level = "Good"
        elif overall_score >= 4.0:
            performance_level = "Fair"
        elif overall_score >= 2.0:
            performance_level = "Poor"
        else:
            performance_level = "Critical"
        
        return CustomerMetrics(
            total_customers=total_customers,
            satisfied_customers=satisfied_customers,
            problem_customers=problem_customers,
            benefit_customers=benefit_customers,
            mixed_customers=mixed_customers,
            neutral_customers=neutral_customers,
            customer_satisfaction_rate=round(customer_satisfaction_rate, 1),
            overall_score=round(overall_score, 1),
            performance_level=performance_level
        )
    
    def get_customer_metrics(self, client_id: str) -> Dict[str, Any]:
        """Get customer metrics for a specific client"""
        try:
            # Get quotes data
            quotes_df = self.db.get_stage1_data_responses(client_id=client_id)
            
            if quotes_df.empty:
                return self._empty_metrics()
            
            # Group by customer
            customer_groups = self.group_quotes_by_customer(quotes_df)
            
            # Calculate metrics
            metrics = self.calculate_customer_metrics(customer_groups)
            
            # Prepare return data
            return {
                'total_customers': metrics.total_customers,
                'satisfied_customers': metrics.satisfied_customers,
                'problem_customers': metrics.problem_customers,
                'benefit_customers': metrics.benefit_customers,
                'mixed_customers': metrics.mixed_customers,
                'neutral_customers': metrics.neutral_customers,
                'customer_satisfaction_rate': metrics.customer_satisfaction_rate,
                'overall_score': metrics.overall_score,
                'performance_level': metrics.performance_level,
                'customer_groups': customer_groups,
                'total_quotes': len(quotes_df)
            }
            
        except Exception as e:
            logger.error(f"Error getting customer metrics: {e}")
            return self._empty_metrics()
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            'total_customers': 0,
            'satisfied_customers': 0,
            'problem_customers': 0,
            'benefit_customers': 0,
            'mixed_customers': 0,
            'neutral_customers': 0,
            'customer_satisfaction_rate': 0.0,
            'overall_score': 0.0,
            'performance_level': 'No Data',
            'customer_groups': {},
            'total_quotes': 0
        }
    
    def get_customer_breakdown(self, customer_groups: Dict[str, CustomerGroup]) -> Dict[str, List[str]]:
        """Get breakdown of customers by category"""
        breakdown = {
            'problem_customers': [],
            'benefit_customers': [],
            'mixed_customers': [],
            'neutral_customers': []
        }
        
        for customer_key, group in customer_groups.items():
            customer_info = f"{group.interviewee_name} ({group.company}) - {group.total_quotes} quotes"
            
            if group.customer_type == 'problem':
                breakdown['problem_customers'].append(customer_info)
            elif group.customer_type == 'benefit':
                breakdown['benefit_customers'].append(customer_info)
            elif group.customer_type == 'mixed':
                breakdown['mixed_customers'].append(customer_info)
            else:  # neutral
                breakdown['neutral_customers'].append(customer_info)
        
        return breakdown
    
    def get_improvement_opportunities(self, customer_groups: Dict[str, CustomerGroup], max_opportunities: int = 10) -> List[Dict]:
        """Get improvement opportunities from customer groups"""
        opportunities = []
        
        for customer_key, group in customer_groups.items():
            if group.product_complaints:
                for complaint in group.product_complaints:
                    opportunities.append({
                        'customer_key': customer_key,
                        'interviewee_name': group.interviewee_name,
                        'company': group.company,
                        'quote_text': complaint.get('verbatim_response', ''),
                        'quote_id': complaint.get('response_id', ''),
                        'sentiment': complaint.get('sentiment', 'neutral'),
                        'priority': complaint.get('priority', 1)
                    })
        
        # Sort by priority and limit
        opportunities.sort(key=lambda x: x.get('priority', 1), reverse=True)
        return opportunities[:max_opportunities]
    
    def get_winning_factors(self, customer_groups: Dict[str, CustomerGroup], max_factors: int = 10) -> List[Dict]:
        """Get winning factors from customer groups"""
        factors = []
        
        for customer_key, group in customer_groups.items():
            if group.benefit_discussions:
                for benefit in group.benefit_discussions:
                    factors.append({
                        'customer_key': customer_key,
                        'interviewee_name': group.interviewee_name,
                        'company': group.company,
                        'quote_text': benefit.get('verbatim_response', ''),
                        'quote_id': benefit.get('response_id', ''),
                        'sentiment': benefit.get('sentiment', 'neutral'),
                        'priority': benefit.get('priority', 1)
                    })
        
        # Sort by priority and limit
        factors.sort(key=lambda x: x.get('priority', 1), reverse=True)
        return factors[:max_factors]
    
    def compare_with_quote_counted(self, client_id: str) -> Dict[str, Any]:
        """Compare interview-weighted with quote-counted approach"""
        try:
            # Get interview-weighted metrics
            interview_metrics = self.get_customer_metrics(client_id)
            
            # Get quote-counted metrics
            quotes_df = self.db.get_stage1_data_responses(client_id=client_id)
            stage2_df = self.db.get_stage2_response_labeling(client_id)
            
            if quotes_df.empty:
                return {
                    'interview_weighted': interview_metrics,
                    'quote_counted': self._empty_metrics(),
                    'comparison': {}
                }
            
            # Create lookup for Stage 2 data
            stage2_lookup = {}
            if not stage2_df.empty:
                stage2_lookup = {row['quote_id']: row for _, row in stage2_df.iterrows()}
            
            # Count quotes by category
            product_complaints = 0
            benefit_discussions = 0
            neutral_discussions = 0
            total_quotes = len(quotes_df)
            
            for _, quote in quotes_df.iterrows():
                quote_id = quote.get('response_id')
                quote_text = quote.get('verbatim_response', '').lower()
                
                # Get enriched data if available
                enriched_data = stage2_lookup.get(quote_id, {})
                sentiment = enriched_data.get('sentiment', 'neutral')
                
                # Categorize quote
                if self._is_product_complaint(quote_text, sentiment):
                    product_complaints += 1
                elif self._is_benefit_discussion(quote_text, sentiment):
                    benefit_discussions += 1
                else:
                    neutral_discussions += 1
            
            # Calculate quote-counted metrics
            satisfied_quotes = benefit_discussions + neutral_discussions
            quote_satisfaction_rate = (satisfied_quotes / total_quotes) * 100 if total_quotes > 0 else 0
            quote_score = (satisfied_quotes / total_quotes) * 10 if total_quotes > 0 else 0
            
            quote_metrics = {
                'total_quotes': total_quotes,
                'satisfied_quotes': satisfied_quotes,
                'problem_quotes': product_complaints,
                'benefit_quotes': benefit_discussions,
                'neutral_quotes': neutral_discussions,
                'quote_satisfaction_rate': round(quote_satisfaction_rate, 1),
                'quote_score': round(quote_score, 1)
            }
            
            # Comparison
            comparison = {
                'score_difference': interview_metrics['overall_score'] - quote_metrics['quote_score'],
                'satisfaction_difference': interview_metrics['customer_satisfaction_rate'] - quote_metrics['quote_satisfaction_rate'],
                'problem_difference': quote_metrics['problem_quotes'] - interview_metrics['problem_customers']
            }
            
            return {
                'interview_weighted': interview_metrics,
                'quote_counted': quote_metrics,
                'comparison': comparison
            }
            
        except Exception as e:
            logger.error(f"Error comparing approaches: {e}")
            return {
                'interview_weighted': self._empty_metrics(),
                'quote_counted': self._empty_metrics(),
                'comparison': {}
            } 