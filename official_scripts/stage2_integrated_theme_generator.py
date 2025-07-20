"""
Stage 2 Integrated Theme Generator
Integrates Stage 2 enriched data into theme generation for improvement-focused analysis
"""

import pandas as pd
from typing import Dict, List, Any
from official_scripts.database.supabase_database import SupabaseDatabase
from official_scripts.holistic_evaluation import HolisticEvaluator

class Stage2IntegratedThemeGenerator:
    def __init__(self):
        self.db = SupabaseDatabase()
        self.holistic_evaluator = HolisticEvaluator()
        
    def generate_improvement_focused_themes(self, client_id: str) -> Dict[str, Any]:
        """
        Generate themes using Stage 2 enriched data with improvement focus
        """
        print(f"🎯 GENERATING STAGE 2 INTEGRATED THEMES FOR {client_id}")
        print("=" * 60)
        
        # Get Stage 1 quotes
        stage1_quotes = self.db.get_stage1_data_responses(client_id=client_id)
        print(f"📊 Retrieved {len(stage1_quotes)} Stage 1 quotes")
        
        # Get Stage 2 enriched data
        stage2_data = self.db.get_stage2_response_labeling(client_id=client_id)
        print(f"📊 Retrieved {len(stage2_data)} Stage 2 enriched analyses")
        
        # Merge Stage 1 and Stage 2 data
        enriched_quotes = self._merge_stage1_stage2_data(stage1_quotes, stage2_data)
        print(f"📊 Created {len(enriched_quotes)} enriched quote records")
        
        # Generate improvement-focused themes by criterion
        themes_by_criterion = self._generate_themes_by_criterion(enriched_quotes)
        
        # Generate overall assessment
        overall_assessment = self._generate_overall_assessment(themes_by_criterion)
        
        return {
            'themes_by_criterion': themes_by_criterion,
            'overall_assessment': overall_assessment,
            'data_summary': {
                'stage1_quotes': len(stage1_quotes),
                'stage2_analyses': len(stage2_data),
                'enriched_quotes': len(enriched_quotes),
                'criteria_analyzed': len(themes_by_criterion)
            }
        }
    
    def _merge_stage1_stage2_data(self, stage1_quotes: pd.DataFrame, stage2_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Merge Stage 1 quotes with Stage 2 enriched analysis
        """
        enriched_quotes = []
        
        for _, quote in stage1_quotes.iterrows():
            quote_dict = quote.to_dict()
            
            # Find corresponding Stage 2 analysis
            stage2_analysis = stage2_data[stage2_data['quote_id'] == quote['response_id']]
            
            if not stage2_analysis.empty:
                # Merge Stage 2 data
                analysis = stage2_analysis.iloc[0]
                quote_dict.update({
                    'sentiment_score': self._convert_sentiment_to_score(analysis.get('sentiment', 'neutral')),
                    'business_impact': analysis.get('priority', 'medium'),
                    'relevance_score': analysis.get('relevance_score', 0.5) or 0.5,
                    'criterion': analysis.get('criterion', 'unknown'),
                    'priority_score': self._calculate_priority_score(analysis),
                    'stage2_enriched': True,
                    'deal_weighted_score': analysis.get('deal_weighted_score', 2.0),
                    'confidence': analysis.get('confidence', 'medium')
                })
            else:
                # No Stage 2 data available
                quote_dict.update({
                    'sentiment_score': 0.5,
                    'business_impact': 'medium',
                    'relevance_score': 0.5,
                    'criterion': 'unknown',
                    'priority_score': 1.0,
                    'stage2_enriched': False,
                    'deal_weighted_score': 2.0,
                    'confidence': 'medium'
                })
            
            enriched_quotes.append(quote_dict)
        
        return enriched_quotes
    
    def _convert_sentiment_to_score(self, sentiment: str) -> float:
        """
        Convert sentiment text to numeric score
        """
        sentiment_mapping = {
            'positive': 0.8,
            'negative': 0.2,
            'neutral': 0.5,
            'very_positive': 0.9,
            'very_negative': 0.1
        }
        return sentiment_mapping.get(sentiment.lower(), 0.5)
    
    def _calculate_priority_score(self, stage2_analysis: pd.Series) -> float:
        """
        Calculate priority score based on Stage 2 data
        """
        sentiment_score = self._convert_sentiment_to_score(stage2_analysis.get('sentiment', 'neutral'))
        business_impact = stage2_analysis.get('priority', 'medium') or 'medium'
        relevance_score = stage2_analysis.get('relevance_score', 0.5) or 0.5
        deal_weighted_score = stage2_analysis.get('deal_weighted_score', 2.0) or 2.0
        
        # Business impact weighting
        impact_weights = {'high': 3.0, 'medium': 2.0, 'low': 1.0}
        impact_weight = impact_weights.get(business_impact, 2.0)
        
        # Use deal_weighted_score if relevance_score is missing
        if relevance_score == 0.5 and deal_weighted_score > 0:
            relevance_score = min(1.0, deal_weighted_score / 10.0)
        
        # Calculate priority score
        priority_score = (sentiment_score * 0.3 + relevance_score * 0.4 + impact_weight * 0.3) * 10
        
        return min(10.0, max(1.0, priority_score))
    
    def _generate_themes_by_criterion(self, enriched_quotes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate improvement-focused themes for each criterion
        """
        criteria = [
            'Product Capability & Features',
            'Commercial Terms & Pricing', 
            'Integration & Technical Fit',
            'Security & Compliance',
            'Implementation & Onboarding'
        ]
        
        themes_by_criterion = {}
        
        for criterion in criteria:
            print(f"\n🔍 Analyzing {criterion}...")
            
            # Filter quotes for this criterion
            criterion_quotes = [
                q for q in enriched_quotes 
                if q.get('criterion', '').lower() in criterion.lower() or
                self._check_criterion_keywords(q.get('verbatim_response', ''), criterion)
            ]
            
            if criterion_quotes:
                # Generate holistic evaluation for this criterion
                criterion_data = {
                    'framework': {
                        'title': criterion,
                        'business_impact': 'Directly impacts customer satisfaction',
                        'executive_description': f'Key factor in {criterion.lower()}'
                    }
                }
                
                evaluation = self.holistic_evaluator.evaluate_criterion_holistically(
                    criterion_data, criterion_quotes
                )
                
                # Extract improvement opportunities and winning factors
                improvement_opportunities = self._extract_improvement_opportunities(criterion_quotes)
                winning_factors = self._extract_winning_factors(criterion_quotes)
                
                themes_by_criterion[criterion] = {
                    'holistic_score': evaluation['holistic_score'],
                    'performance_assessment': evaluation['performance_assessment'],
                    'improvement_opportunities': improvement_opportunities,
                    'winning_factors': winning_factors,
                    'sentiment_breakdown': evaluation['sentiment_breakdown'],
                    'evidence_summary': evaluation['evidence_summary']
                }
                
                print(f"   📈 Score: {evaluation['holistic_score']}/10")
                print(f"   📉 Improvement Opportunities: {len(improvement_opportunities)}")
                print(f"   🏆 Winning Factors: {len(winning_factors)}")
        
        return themes_by_criterion
    
    def _extract_improvement_opportunities(self, quotes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract high-priority improvement opportunities
        """
        opportunities = []
        
        for quote in quotes:
            sentiment_score = quote.get('sentiment_score', 0.5) or 0.5
            priority_score = quote.get('priority_score', 1.0) or 1.0
            business_impact = quote.get('business_impact', 'medium') or 'medium'
            
            # Ensure priority_score is a float
            if isinstance(priority_score, dict):
                priority_score = priority_score.get('total_score', 1.0) or 1.0
            elif not isinstance(priority_score, (int, float)):
                priority_score = 1.0
            
            # Less strict filtering - focus on negative sentiment with reasonable priority
            if (sentiment_score < 0.5 and 
                priority_score >= 3.0 and 
                business_impact in ['high', 'medium']):
                
                opportunity = {
                    'opportunity': self._identify_improvement_type(quote['verbatim_response']),
                    'evidence': quote['verbatim_response'][:200] + "..." if len(quote['verbatim_response']) > 200 else quote['verbatim_response'],
                    'interviewee': quote.get('interviewee_name', 'Unknown'),
                    'company': quote.get('company', 'Unknown'),
                    'priority_score': priority_score,
                    'business_impact': business_impact,
                    'sentiment_score': sentiment_score
                }
                opportunities.append(opportunity)
        
        # Sort by priority score and business impact
        opportunities.sort(key=lambda x: (x['business_impact'] == 'high', x['priority_score']), reverse=True)
        return opportunities[:5]  # Top 5 improvement opportunities
    
    def _extract_winning_factors(self, quotes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract high-priority winning factors
        """
        winning_factors = []
        
        for quote in quotes:
            sentiment_score = quote.get('sentiment_score', 0.5) or 0.5
            priority_score = quote.get('priority_score', 1.0) or 1.0
            business_impact = quote.get('business_impact', 'medium') or 'medium'
            
            # Ensure priority_score is a float
            if isinstance(priority_score, dict):
                priority_score = priority_score.get('total_score', 1.0) or 1.0
            elif not isinstance(priority_score, (int, float)):
                priority_score = 1.0
            
            # Less strict filtering - focus on positive sentiment with reasonable priority
            if (sentiment_score > 0.6 and 
                priority_score >= 3.0 and 
                business_impact in ['high', 'medium']):
                
                winning_factor = {
                    'factor': self._identify_winning_type(quote['verbatim_response']),
                    'evidence': quote['verbatim_response'][:200] + "..." if len(quote['verbatim_response']) > 200 else quote['verbatim_response'],
                    'interviewee': quote.get('interviewee_name', 'Unknown'),
                    'company': quote.get('company', 'Unknown'),
                    'priority_score': priority_score,
                    'business_impact': business_impact,
                    'sentiment_score': sentiment_score
                }
                winning_factors.append(winning_factor)
        
        # Sort by priority score and business impact
        winning_factors.sort(key=lambda x: (x['business_impact'] == 'high', x['priority_score']), reverse=True)
        return winning_factors[:5]  # Top 5 winning factors
    
    def _identify_improvement_type(self, quote_text: str) -> str:
        """
        Identify the type of improvement opportunity
        """
        text_lower = quote_text.lower()
        
        if any(word in text_lower for word in ['slow', 'delay', 'wait']):
            return "Speed and Performance Issues"
        elif any(word in text_lower for word in ['inaccurate', 'error', 'wrong']):
            return "Accuracy and Quality Issues"
        elif any(word in text_lower for word in ['expensive', 'cost', 'price']):
            return "Pricing and Cost Concerns"
        elif any(word in text_lower for word in ['difficult', 'hard', 'complex']):
            return "Usability and Complexity Issues"
        elif any(word in text_lower for word in ['integration', 'connect', 'sync']):
            return "Integration and Technical Issues"
        elif any(word in text_lower for word in ['frustrated', 'annoying', 'disappointing']):
            return "User Experience Issues"
        else:
            return "General Improvement Opportunity"
    
    def _identify_winning_type(self, quote_text: str) -> str:
        """
        Identify the type of winning factor
        """
        text_lower = quote_text.lower()
        
        if any(word in text_lower for word in ['fast', 'quick', 'efficient', 'saves time']):
            return "Speed and Efficiency Gains"
        elif any(word in text_lower for word in ['love', 'great', 'amazing', 'wonderful']):
            return "Positive User Experience"
        elif any(word in text_lower for word in ['helpful', 'useful', 'valuable']):
            return "Practical Utility and Value"
        elif any(word in text_lower for word in ['accurate', 'reliable', 'consistent']):
            return "Quality and Reliability"
        elif any(word in text_lower for word in ['easy', 'simple', 'smooth']):
            return "Ease of Use and Simplicity"
        elif any(word in text_lower for word in ['worth', 'investment', 'roi']):
            return "Value and Return on Investment"
        else:
            return "General Positive Experience"
    
    def _check_criterion_keywords(self, quote_text: str, criterion: str) -> bool:
        """
        Check if quote contains keywords for the criterion
        """
        text_lower = quote_text.lower()
        
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
        
        keywords = keyword_mapping.get(criterion, [])
        return any(keyword in text_lower for keyword in keywords)
    
    def _generate_overall_assessment(self, themes_by_criterion: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate overall assessment across all criteria
        """
        if not themes_by_criterion:
            return {
                'overall_score': 0.0,
                'performance_level': 'No data available',
                'description': 'Insufficient data for assessment',
                'improvement_priorities': [],
                'winning_highlights': []
            }
        
        # Calculate overall score
        scores = [theme['holistic_score'] for theme in themes_by_criterion.values()]
        overall_score = sum(scores) / len(scores)
        
        # Collect improvement opportunities
        all_improvements = []
        for criterion, theme in themes_by_criterion.items():
            for improvement in theme['improvement_opportunities']:
                improvement['criterion'] = criterion
                all_improvements.append(improvement)
        
        # Collect winning factors
        all_wins = []
        for criterion, theme in themes_by_criterion.items():
            for win in theme['winning_factors']:
                win['criterion'] = criterion
                all_wins.append(win)
        
        # Sort by priority
        all_improvements.sort(key=lambda x: (x['business_impact'] == 'high', x['priority_score']), reverse=True)
        all_wins.sort(key=lambda x: (x['business_impact'] == 'high', x['priority_score']), reverse=True)
        
        # Generate performance level
        if overall_score >= 7.0:
            performance_level = "Strong competitive advantage"
            description = "Customers consistently report positive experiences across all areas"
        elif overall_score >= 5.0:
            performance_level = "Solid performance with improvement opportunities"
            description = "Generally positive feedback with specific areas for enhancement"
        elif overall_score >= 3.0:
            performance_level = "Areas for enhancement identified"
            description = "Mixed feedback with clear improvement opportunities"
        else:
            performance_level = "Significant improvement opportunities"
            description = "Customer feedback indicates need for substantial enhancements"
        
        return {
            'overall_score': round(overall_score, 1),
            'performance_level': performance_level,
            'description': description,
            'improvement_priorities': all_improvements[:5],  # Top 5 overall
            'winning_highlights': all_wins[:5],  # Top 5 overall
            'criteria_count': len(themes_by_criterion)
        } 