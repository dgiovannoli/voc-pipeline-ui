"""
Holistic Evaluation System for VOC Pipeline
Provides balanced sentiment analysis and win/loss factor identification
"""

import pandas as pd
from typing import Dict, List, Any
from official_scripts.enhanced_quote_scoring import EnhancedQuoteScoring

class HolisticEvaluator:
    def __init__(self):
        self.quote_scoring = EnhancedQuoteScoring()
        
    def evaluate_criterion_holistically(self, criterion_data: Dict[str, Any], all_quotes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate a criterion using holistic sentiment analysis
        Prioritizes improvement opportunities while maintaining balanced assessment
        """
        # Convert DataFrame to list of dicts if needed
        if hasattr(all_quotes, 'to_dict'):
            all_quotes = all_quotes.to_dict('records')
        
        # Get all quotes that mention this criterion (not just categorized ones)
        criterion_quotes = self._extract_criterion_quotes(all_quotes, criterion_data['framework']['title'])
        
        # Analyze sentiment distribution
        sentiment_analysis = self._analyze_sentiment_distribution(criterion_quotes)
        
        # Identify improvement opportunities (Priority 1)
        improvement_opportunities = self._identify_improvement_opportunities(criterion_quotes)
        
        # Identify winning factors (Priority 2)
        winning_factors = self._identify_winning_factors(criterion_quotes)
        
        # Calculate holistic score
        holistic_score = self._calculate_holistic_score(sentiment_analysis, improvement_opportunities, winning_factors)
        
        # Generate contextual performance assessment
        performance_assessment = self._get_contextual_performance_assessment(
            holistic_score, 
            improvement_opportunities,
            winning_factors,
            customer_context={'are_paying_customers': True}
        )
        
        return {
            'holistic_score': holistic_score,
            'sentiment_breakdown': sentiment_analysis,
            'improvement_opportunities': improvement_opportunities,  # Priority 1
            'winning_factors': winning_factors,                     # Priority 2
            'performance_assessment': performance_assessment,
            'evidence_summary': self._create_evidence_summary(criterion_quotes)
        }
    
    def _extract_criterion_quotes(self, all_quotes: List[Dict[str, Any]], criterion_title: str) -> List[Dict[str, Any]]:
        """
        Extract all quotes that mention this criterion, regardless of categorization
        """
        criterion_keywords = self._get_criterion_keywords(criterion_title)
        relevant_quotes = []
        
        for quote in all_quotes:
            quote_text = quote.get('verbatim_response', '').lower()
            
            # Check if quote mentions this criterion
            keyword_matches = sum(1 for keyword in criterion_keywords if keyword in quote_text)
            if keyword_matches > 0:
                # Add priority scoring
                priority_score = self.quote_scoring.calculate_quote_priority_score(quote)
                quote['priority_score'] = priority_score
                quote['relevance_score'] = keyword_matches / len(criterion_keywords)
                relevant_quotes.append(quote)
        
        # Sort by priority score
        relevant_quotes.sort(key=lambda x: x['priority_score']['total_score'], reverse=True)
        return relevant_quotes
    
    def _analyze_sentiment_distribution(self, quotes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sentiment distribution across all quotes
        """
        positive_quotes = []
        negative_quotes = []
        neutral_quotes = []
        
        for quote in quotes:
            sentiment = self._analyze_quote_sentiment(quote['verbatim_response'])
            quote['sentiment'] = sentiment
            
            if sentiment['score'] > 0.6:
                positive_quotes.append(quote)
            elif sentiment['score'] < 0.4:
                negative_quotes.append(quote)
            else:
                neutral_quotes.append(quote)
        
        # Calculate weighted scores
        positive_score = self._calculate_weighted_sentiment_score(positive_quotes)
        negative_score = self._calculate_weighted_sentiment_score(negative_quotes)
        neutral_score = self._calculate_weighted_sentiment_score(neutral_quotes)
        
        return {
            'positive': {
                'count': len(positive_quotes),
                'weighted_score': positive_score,
                'quotes': positive_quotes[:5],  # Top 5 positive quotes
                'themes': self._extract_sentiment_themes(positive_quotes, 'positive')
            },
            'negative': {
                'count': len(negative_quotes),
                'weighted_score': negative_score,
                'quotes': negative_quotes[:5],  # Top 5 negative quotes
                'themes': self._extract_sentiment_themes(negative_quotes, 'negative')
            },
            'neutral': {
                'count': len(neutral_quotes),
                'weighted_score': neutral_score,
                'quotes': neutral_quotes[:3],  # Top 3 neutral quotes
                'themes': self._extract_sentiment_themes(neutral_quotes, 'neutral')
            }
        }
    
    def _identify_improvement_opportunities(self, quotes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify specific improvement opportunities from quotes
        """
        improvement_opportunities = []
        
        for quote in quotes:
            sentiment = quote.get('sentiment', {})
            priority_score = quote.get('priority_score', {}).get('total_score', 0)
            
            if sentiment.get('score', 0.5) < 0.5 and priority_score >= 5:
                improvement_opportunity = self._extract_improvement_opportunity(quote)
                if improvement_opportunity:
                    improvement_opportunities.append(improvement_opportunity)
        
        return {
            'improvement_opportunities': improvement_opportunities[:3],  # Top 3 improvement opportunities
            'net_sentiment': self._calculate_net_sentiment(quotes)
        }
    
    def _identify_winning_factors(self, quotes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify specific winning factors from quotes
        """
        winning_factors = []
        
        for quote in quotes:
            sentiment = quote.get('sentiment', {})
            priority_score = quote.get('priority_score', {}).get('total_score', 0)
            
            if sentiment.get('score', 0.5) > 0.7 and priority_score >= 5:
                winning_factor = self._extract_winning_factor(quote)
                if winning_factor:
                    winning_factors.append(winning_factor)
        
        return {
            'winning_factors': winning_factors[:3],  # Top 3 winning factors
            'net_sentiment': self._calculate_net_sentiment(quotes)
        }
    
    def _calculate_holistic_score(self, sentiment_analysis: Dict[str, Any], improvement_opportunities: Dict[str, Any], winning_factors: Dict[str, Any]) -> float:
        """
        Calculate holistic score based on sentiment distribution and win/loss factors
        """
        # Base score from sentiment distribution
        positive_weight = sentiment_analysis['positive']['weighted_score'] * 0.4
        negative_weight = (1 - sentiment_analysis['negative']['weighted_score']) * 0.4
        neutral_weight = sentiment_analysis['neutral']['weighted_score'] * 0.2
        
        base_score = positive_weight + negative_weight + neutral_weight
        
        # Adjust based on win/loss factor balance
        win_count = len(winning_factors['winning_factors'])
        loss_count = len(improvement_opportunities['improvement_opportunities']) # Assuming improvement opportunities are loss factors
        
        if win_count > loss_count:
            factor_adjustment = 0.2
        elif loss_count > win_count:
            factor_adjustment = -0.2
        else:
            factor_adjustment = 0
        
        final_score = min(10.0, max(0.0, base_score * 10 + factor_adjustment))
        return round(final_score, 1)
    
    def _get_contextual_performance_assessment(self, score: float, improvement_opportunities: Dict[str, Any], winning_factors: Dict[str, Any], customer_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate contextual performance assessment
        """
        if customer_context.get('are_paying_customers', False):
            # Context for paying customers
            if score >= 7.0:
                level = "Strong competitive advantage"
                description = "Customers consistently report positive experiences and value"
            elif score >= 5.0:
                level = "Solid performance with improvement opportunities"
                description = "Generally positive feedback with specific areas for enhancement"
            elif score >= 3.0:
                level = "Areas for enhancement identified"
                description = "Mixed feedback with clear improvement opportunities"
            else:
                level = "Significant improvement opportunities"
                description = "Customer feedback indicates need for substantial enhancements"
        else:
            # Standard win/loss assessment
            if score >= 7.0:
                level = "Winning factor"
                description = "Strong competitive advantage in this area"
            elif score >= 5.0:
                level = "Neutral factor"
                description = "Neither significant advantage nor disadvantage"
            else:
                level = "Losing factor"
                description = "Competitive disadvantage requiring attention"
        
        return {
            'level': level,
            'description': description,
            'score': score,
            'improvement_opportunities_count': len(improvement_opportunities['improvement_opportunities']),
            'winning_factors_count': len(winning_factors['winning_factors'])
        }
    
    def _analyze_quote_sentiment(self, quote_text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of a quote
        """
        quote_lower = quote_text.lower()
        
        # Enhanced positive indicators
        positive_words = [
            'love', 'great', 'good', 'excellent', 'amazing', 'wonderful', 'perfect', 'best',
            'easy', 'fast', 'efficient', 'helpful', 'useful', 'worth', 'saves', 'saved',
            'quick', 'quicker', 'faster', 'smooth', 'seamless', 'reliable', 'accurate'
        ]
        
        # Enhanced negative indicators
        negative_words = [
            'hate', 'terrible', 'bad', 'awful', 'worst', 'difficult', 'slow', 'inefficient',
            'problem', 'issue', 'frustrated', 'annoying', 'disappointing', 'expensive',
            'delay', 'delays', 'inaccurate', 'error', 'errors', 'broken', 'fail'
        ]
        
        positive_count = sum(1 for word in positive_words if word in quote_lower)
        negative_count = sum(1 for word in negative_words if word in quote_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
            confidence = min(1.0, positive_count / max(negative_count, 1))
            score = 0.5 + (confidence * 0.5)
        elif negative_count > positive_count:
            sentiment = 'negative'
            confidence = min(1.0, negative_count / max(positive_count, 1))
            score = 0.5 - (confidence * 0.5)
        else:
            sentiment = 'neutral'
            confidence = 0.5
            score = 0.5
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'score': score,
            'positive_words': positive_count,
            'negative_words': negative_count
        }
    
    def _calculate_weighted_sentiment_score(self, quotes: List[Dict[str, Any]]) -> float:
        """
        Calculate weighted sentiment score based on priority and sentiment
        """
        if not quotes:
            return 0.0
        
        total_weight = 0
        weighted_sum = 0
        
        for quote in quotes:
            priority_score = quote.get('priority_score', {}).get('total_score', 1)
            sentiment_score = quote.get('sentiment', {}).get('score', 0.5)
            
            weight = priority_score
            total_weight += weight
            weighted_sum += sentiment_score * weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _extract_improvement_opportunity(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract improvement opportunity from negative quote
        """
        text = quote.get('verbatim_response', '')
        
        # Look for specific negative indicators
        improvement_indicators = [
            'slow', 'delay', 'inefficient', 'problem', 'issue', 'frustrated', 'disappointing',
            'difficult', 'expensive', 'inaccurate', 'error', 'errors', 'broken', 'fail'
        ]
        
        for indicator in improvement_indicators:
            if indicator in text.lower():
                return {
                    'opportunity': f"Improvement: {indicator.replace('_', ' ').title()}",
                    'evidence': text[:200] + "..." if len(text) > 200 else text,
                    'interviewee': quote.get('interviewee_name', 'Unknown'),
                    'company': quote.get('company', 'Unknown'),
                    'priority_score': quote.get('priority_score', {}).get('total_score', 0)
                }
        
        return None
    
    def _extract_winning_factor(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract winning factor from positive quote
        """
        text = quote.get('verbatim_response', '')
        
        # Look for specific positive indicators
        winning_indicators = [
            'saves time', 'efficient', 'fast', 'quick', 'love', 'great', 'helpful',
            'worth', 'valuable', 'reliable', 'accurate', 'easy', 'smooth'
        ]
        
        for indicator in winning_indicators:
            if indicator in text.lower():
                return {
                    'factor': f"Winning: {indicator.replace('_', ' ').title()}",
                    'evidence': text[:200] + "..." if len(text) > 200 else text,
                    'interviewee': quote.get('interviewee_name', 'Unknown'),
                    'company': quote.get('company', 'Unknown'),
                    'priority_score': quote.get('priority_score', {}).get('total_score', 0)
                }
        
        return None
    
    def _extract_sentiment_themes(self, quotes: List[Dict[str, Any]], sentiment_type: str) -> List[str]:
        """
        Extract common themes from quotes of a particular sentiment
        """
        if not quotes:
            return []
        
        # Simple theme extraction based on common words
        all_text = ' '.join([q.get('verbatim_response', '') for q in quotes]).lower()
        
        # Extract common phrases (simplified)
        themes = []
        if sentiment_type == 'positive':
            if 'saves time' in all_text:
                themes.append("Time savings and efficiency")
            if 'love' in all_text or 'great' in all_text:
                themes.append("Positive user experience")
            if 'helpful' in all_text or 'useful' in all_text:
                themes.append("Practical utility and value")
        elif sentiment_type == 'negative':
            if 'slow' in all_text or 'delay' in all_text:
                themes.append("Speed and timing issues")
            if 'expensive' in all_text or 'cost' in all_text:
                themes.append("Pricing and cost concerns")
            if 'inaccurate' in all_text or 'error' in all_text:
                themes.append("Accuracy and quality issues")
        
        return themes[:3]  # Top 3 themes
    
    def _calculate_net_sentiment(self, quotes: List[Dict[str, Any]]) -> float:
        """
        Calculate net sentiment across all quotes
        """
        if not quotes:
            return 0.0
        
        total_sentiment = sum(q.get('sentiment', {}).get('score', 0.5) for q in quotes)
        return total_sentiment / len(quotes)
    
    def _create_evidence_summary(self, quotes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create summary of evidence
        """
        return {
            'total_quotes': len(quotes),
            'unique_companies': len(set(q.get('company', '') for q in quotes)),
            'priority_quotes': len([q for q in quotes if q.get('priority_score', {}).get('total_score', 0) >= 5]),
            'sample_quotes': quotes[:3]  # Top 3 quotes
        }
    
    def _get_criterion_keywords(self, criterion_title: str) -> List[str]:
        """
        Get keywords for criterion
        """
        keyword_mapping = {
            'Product Capability & Features': [
                'transcription', 'accuracy', 'speed', 'feature', 'delay', 'inaccuracy', 
                'correction', 'quality', 'performance', 'efficiency', 'time', 'faster', 
                'quicker', 'helpful', 'worth', 'love', 'great', 'amazing', 'saves', 'saved'
            ],
            'Commercial Terms & Pricing': [
                'pricing', 'cost', 'revenue', 'transparency', 'allocation', 'strategy', 
                'value', 'investment', 'roi', 'budget', 'expensive', 'cheaper', 'afford'
            ],
            'Integration & Technical Fit': [
                'integration', 'workflow', 'clio', 'software', 'system', 'manual', 
                'automation', 'api', 'technical', 'platform', 'sync', 'connect'
            ],
            'Security & Compliance': [
                'security', 'compliance', 'confidential', 'data', 'risk', 'trust', 
                'privacy', 'protection', 'audit'
            ],
            'Implementation & Onboarding': [
                'implementation', 'onboarding', 'training', 'adoption', 'setup', 
                'record', 'deployment', 'migration'
            ]
        }
        return keyword_mapping.get(criterion_title, []) 