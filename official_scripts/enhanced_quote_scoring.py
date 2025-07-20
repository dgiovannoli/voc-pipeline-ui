#!/usr/bin/env python3
"""
Enhanced Quote Scoring and Competitive Intelligence
World-class quote prioritization and competitive analysis
"""

import re
from typing import Dict, List, Any
import pandas as pd

class EnhancedQuoteScoring:
    """Advanced quote scoring and competitive intelligence system"""
    
    def __init__(self):
        self.executive_titles = [
            'CEO', 'CTO', 'CFO', 'COO', 'VP', 'Vice President', 'President',
            'Chief', 'Executive', 'Director', 'Senior Director'
        ]
        
        self.business_impact_words = [
            'revenue', 'cost', 'efficiency', 'productivity', 'budget', 'roi', 'profit',
            'savings', 'investment', 'return', 'value', 'benefit', 'advantage',
            'competitive', 'market', 'growth', 'scale', 'performance'
        ]
        
        self.emotional_intensity_words = [
            'frustrated', 'delighted', 'amazed', 'disappointed', 'love', 'hate',
            'critical', 'essential', 'vital', 'crucial', 'terrible', 'excellent',
            'outstanding', 'awful', 'fantastic', 'horrible', 'brilliant'
        ]
        
        self.competitive_context_words = [
            'competitor', 'alternative', 'other solution', 'compared to', 'instead of',
            'versus', 'vs', 'better than', 'worse than', 'different from',
            'similar to', 'like', 'unlike', 'prefer', 'choose', 'selected'
        ]
        
        self.specific_metrics_patterns = [
            r'\$\d+',  # Dollar amounts
            r'\d+%',   # Percentages
            r'\d+ hours?',  # Time periods
            r'\d+ days?',
            r'\d+ weeks?',
            r'\d+ months?',
            r'\d+ years?',
            r'\d+ times?',  # Frequency
            r'\d+ people?',  # Headcount
            r'\d+ users?',
            r'\d+ customers?'
        ]

    def calculate_quote_priority_score(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive priority score for a quote
        
        Returns:
            Dict with score, breakdown, and reasoning
        """
        score = 0
        breakdown = {}
        reasoning = []
        
        # 1. Executive Level (0-3 points)
        executive_score = self._score_executive_level(quote)
        score += executive_score['score']
        breakdown['executive_level'] = executive_score
        if executive_score['score'] > 0:
            reasoning.append(f"Executive level: {executive_score['reasoning']}")
        
        # 2. Business Impact Language (0-3 points)
        impact_score = self._score_business_impact(quote)
        score += impact_score['score']
        breakdown['business_impact'] = impact_score
        if impact_score['score'] > 0:
            reasoning.append(f"Business impact: {impact_score['reasoning']}")
        
        # 3. Specific Metrics (0-2 points)
        metrics_score = self._score_specific_metrics(quote)
        score += metrics_score['score']
        breakdown['specific_metrics'] = metrics_score
        if metrics_score['score'] > 0:
            reasoning.append(f"Specific metrics: {metrics_score['reasoning']}")
        
        # 4. Emotional Intensity (0-2 points)
        emotion_score = self._score_emotional_intensity(quote)
        score += emotion_score['score']
        breakdown['emotional_intensity'] = emotion_score
        if emotion_score['score'] > 0:
            reasoning.append(f"Emotional intensity: {emotion_score['reasoning']}")
        
        # 5. Competitive Context (0-2 points)
        competitive_score = self._score_competitive_context(quote)
        score += competitive_score['score']
        breakdown['competitive_context'] = competitive_score
        if competitive_score['score'] > 0:
            reasoning.append(f"Competitive context: {competitive_score['reasoning']}")
        
        # 6. Quote Length and Completeness (0-1 point)
        completeness_score = self._score_completeness(quote)
        score += completeness_score['score']
        breakdown['completeness'] = completeness_score
        if completeness_score['score'] > 0:
            reasoning.append(f"Completeness: {completeness_score['reasoning']}")
        
        # Determine priority level
        priority_level = self._determine_priority_level(score)
        
        return {
            'total_score': score,
            'priority_level': priority_level,
            'breakdown': breakdown,
            'reasoning': reasoning,
            'max_possible_score': 13
        }

    def _score_executive_level(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """Score based on executive level of speaker"""
        role = quote.get('interviewee_role', '').lower()
        
        # Check for executive titles
        for title in self.executive_titles:
            if title.lower() in role:
                if any(exec_title in title for exec_title in ['CEO', 'CTO', 'CFO', 'COO', 'VP', 'President']):
                    return {
                        'score': 3,
                        'reasoning': f"Senior executive ({title})",
                        'details': f"Role: {quote.get('interviewee_role', 'Unknown')}"
                    }
                elif 'Director' in title:
                    return {
                        'score': 2,
                        'reasoning': f"Director level ({title})",
                        'details': f"Role: {quote.get('interviewee_role', 'Unknown')}"
                    }
                else:
                    return {
                        'score': 1,
                        'reasoning': f"Management level ({title})",
                        'details': f"Role: {quote.get('interviewee_role', 'Unknown')}"
                    }
        
        return {
            'score': 0,
            'reasoning': "Non-executive role",
            'details': f"Role: {quote.get('interviewee_role', 'Unknown')}"
        }

    def _score_business_impact(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """Score based on business impact language"""
        text = quote.get('quote', '').lower()
        impact_words_found = []
        
        for word in self.business_impact_words:
            if word in text:
                impact_words_found.append(word)
        
        if len(impact_words_found) >= 3:
            return {
                'score': 3,
                'reasoning': f"High business impact language ({len(impact_words_found)} terms)",
                'details': f"Terms: {', '.join(impact_words_found[:3])}"
            }
        elif len(impact_words_found) >= 2:
            return {
                'score': 2,
                'reasoning': f"Moderate business impact language ({len(impact_words_found)} terms)",
                'details': f"Terms: {', '.join(impact_words_found)}"
            }
        elif len(impact_words_found) >= 1:
            return {
                'score': 1,
                'reasoning': f"Some business impact language ({len(impact_words_found)} term)",
                'details': f"Terms: {', '.join(impact_words_found)}"
            }
        
        return {
            'score': 0,
            'reasoning': "No business impact language detected",
            'details': "No business terms found"
        }

    def _score_specific_metrics(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """Score based on specific metrics mentioned"""
        text = quote.get('quote', '')
        metrics_found = []
        
        for pattern in self.specific_metrics_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            metrics_found.extend(matches)
        
        if len(metrics_found) >= 3:
            return {
                'score': 2,
                'reasoning': f"Multiple specific metrics ({len(metrics_found)} found)",
                'details': f"Metrics: {', '.join(metrics_found[:3])}"
            }
        elif len(metrics_found) >= 1:
            return {
                'score': 1,
                'reasoning': f"Some specific metrics ({len(metrics_found)} found)",
                'details': f"Metrics: {', '.join(metrics_found)}"
            }
        
        return {
            'score': 0,
            'reasoning': "No specific metrics detected",
            'details': "No metrics found"
        }

    def _score_emotional_intensity(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """Score based on emotional intensity"""
        text = quote.get('quote', '').lower()
        emotions_found = []
        
        for word in self.emotional_intensity_words:
            if word in text:
                emotions_found.append(word)
        
        if len(emotions_found) >= 2:
            return {
                'score': 2,
                'reasoning': f"High emotional intensity ({len(emotions_found)} emotions)",
                'details': f"Emotions: {', '.join(emotions_found)}"
            }
        elif len(emotions_found) >= 1:
            return {
                'score': 1,
                'reasoning': f"Some emotional intensity ({len(emotions_found)} emotion)",
                'details': f"Emotions: {', '.join(emotions_found)}"
            }
        
        return {
            'score': 0,
            'reasoning': "No emotional intensity detected",
            'details': "No emotional language found"
        }

    def _score_competitive_context(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """Score based on competitive context"""
        text = quote.get('quote', '').lower()
        competitive_terms_found = []
        
        for word in self.competitive_context_words:
            if word in text:
                competitive_terms_found.append(word)
        
        if len(competitive_terms_found) >= 2:
            return {
                'score': 2,
                'reasoning': f"Strong competitive context ({len(competitive_terms_found)} terms)",
                'details': f"Terms: {', '.join(competitive_terms_found)}"
            }
        elif len(competitive_terms_found) >= 1:
            return {
                'score': 1,
                'reasoning': f"Some competitive context ({len(competitive_terms_found)} term)",
                'details': f"Terms: {', '.join(competitive_terms_found)}"
            }
        
        return {
            'score': 0,
            'reasoning': "No competitive context detected",
            'details': "No competitive terms found"
        }

    def _score_completeness(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """Score based on quote completeness and quality"""
        text = quote.get('quote', '')
        
        # Check for complete sentences and meaningful content
        if len(text.split()) >= 20 and text.count('.') >= 2:
            return {
                'score': 1,
                'reasoning': "Complete, detailed quote",
                'details': f"Length: {len(text.split())} words, {text.count('.')} sentences"
            }
        elif len(text.split()) >= 10:
            return {
                'score': 0.5,
                'reasoning': "Moderate quote length",
                'details': f"Length: {len(text.split())} words"
            }
        
        return {
            'score': 0,
            'reasoning': "Short or incomplete quote",
            'details': f"Length: {len(text.split())} words"
        }

    def _determine_priority_level(self, score: int) -> str:
        """Determine priority level based on total score"""
        if score >= 10:
            return "CRITICAL"
        elif score >= 7:
            return "HIGH"
        elif score >= 4:
            return "MEDIUM"
        elif score >= 2:
            return "LOW"
        else:
            return "BASIC"

    def extract_competitive_intelligence(self, quotes: List[Dict[str, Any]], themes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract competitive intelligence from quotes and themes
        Uses quote priority scoring to select the highest-rated competitive insights
        """
        # Score all quotes for priority
        scored_quotes = []
        for quote in quotes:
            priority_score = self.calculate_quote_priority_score(quote)
            scored_quotes.append({
                'quote': quote,
                'priority_score': priority_score['total_score'],
                'priority_details': priority_score
            })
        
        # Sort by priority score (highest first)
        scored_quotes.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Extract competitive signals from highest-rated quotes
        competitor_mentions = self._extract_competitor_mentions_from_scored(scored_quotes)
        pricing_insights = self._extract_pricing_context_from_scored(scored_quotes)
        feature_gaps = self._extract_feature_comparisons_from_scored(scored_quotes)
        decision_factors = self._extract_decision_criteria_from_scored(scored_quotes)
        
        # Prioritize by interview diversity and priority score
        competitor_mentions_prioritized = self._prioritize_by_diversity_and_score(competitor_mentions, max_instances=5)
        pricing_insights_prioritized = self._prioritize_by_diversity_and_score(pricing_insights, max_instances=5)
        feature_gaps_prioritized = self._prioritize_by_diversity_and_score(feature_gaps, max_instances=5)
        decision_factors_prioritized = self._prioritize_by_diversity_and_score(decision_factors, max_instances=5)
        
        return {
            'competitor_mentions': competitor_mentions_prioritized,
            'pricing_insights': pricing_insights_prioritized,
            'feature_gaps': feature_gaps_prioritized,
            'decision_factors': decision_factors_prioritized,
            'competitive_prompt': self._generate_competitive_prompt(quotes, themes, competitor_mentions_prioritized, pricing_insights_prioritized, feature_gaps_prioritized, decision_factors_prioritized)
        }

    def _prioritize_by_diversity_and_score(self, data: List[Dict[str, Any]], max_instances: int = 5) -> List[Dict[str, Any]]:
        """
        Prioritize competitive intelligence by interview diversity and quote priority score
        """
        if not data:
            return []
        
        # Group by company to ensure diversity
        company_groups = {}
        for item in data:
            company = item.get('company', 'Unknown')
            if company not in company_groups:
                company_groups[company] = []
            company_groups[company].append(item)
        
        # Select best from each company based on priority score
        prioritized_items = []
        
        for company, items in company_groups.items():
            # Sort by priority score and take the best from this company
            items.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
            if items:
                prioritized_items.append(items[0])
        
        # Sort by priority score across all companies and take top max_instances
        prioritized_items.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        
        # Return the top items with diversity info
        result = []
        for i, item in enumerate(prioritized_items[:max_instances]):
            item['diversity_rank'] = i + 1
            result.append(item)
        
        return result

    def _extract_competitor_mentions_from_scored(self, scored_quotes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract competitor mentions from highest-rated quotes"""
        competitor_mentions = []
        
        for scored_quote in scored_quotes:
            quote = scored_quote['quote']
            text = quote.get('quote', '').lower()
            
            # Look for competitor names and references
            competitor_indicators = [
                'competitor', 'alternative', 'other solution', 'different company',
                'another vendor', 'other provider', 'similar product', 'clio', 'westlaw',
                'co-counsel', 'different platform', 'other software'
            ]
            
            for indicator in competitor_indicators:
                if indicator in text:
                    competitor_mentions.append({
                        'quote_id': quote.get('quote_id'),
                        'quote': quote.get('quote'),
                        'interviewee': quote.get('interviewee_name'),
                        'company': quote.get('company'),
                        'priority_score': scored_quote['priority_score'],
                        'indicator': indicator,
                        'context': self._extract_context(text, indicator)
                    })
                    break  # Only count each quote once for competitors
        
        return competitor_mentions

    def _extract_pricing_context_from_scored(self, scored_quotes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract pricing insights from highest-rated quotes"""
        pricing_quotes = []
        
        pricing_keywords = ['price', 'cost', 'expensive', 'cheaper', 'budget', 'pricing', 'afford', 'worth', 'value']
        
        for scored_quote in scored_quotes:
            quote = scored_quote['quote']
            text = quote.get('quote', '').lower()
            
            for keyword in pricing_keywords:
                if keyword in text:
                    pricing_quotes.append({
                        'quote_id': quote.get('quote_id'),
                        'quote': quote.get('quote'),
                        'interviewee': quote.get('interviewee_name'),
                        'company': quote.get('company'),
                        'priority_score': scored_quote['priority_score'],
                        'keyword': keyword,
                        'context': self._extract_context(text, keyword)
                    })
                    break  # Only count each quote once for pricing
        
        return pricing_quotes

    def _extract_feature_comparisons_from_scored(self, scored_quotes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract feature comparison insights from highest-rated quotes"""
        feature_quotes = []
        
        feature_keywords = ['feature', 'capability', 'doesn\'t have', 'missing', 'better', 'worse', 'different', 'accuracy', 'quality', 'transcription', 'audio']
        
        for scored_quote in scored_quotes:
            quote = scored_quote['quote']
            text = quote.get('quote', '').lower()
            
            for keyword in feature_keywords:
                if keyword in text:
                    feature_quotes.append({
                        'quote_id': quote.get('quote_id'),
                        'quote': quote.get('quote'),
                        'interviewee': quote.get('interviewee_name'),
                        'company': quote.get('company'),
                        'priority_score': scored_quote['priority_score'],
                        'keyword': keyword,
                        'context': self._extract_context(text, keyword)
                    })
                    break  # Only count each quote once for features
        
        return feature_quotes

    def _extract_decision_criteria_from_scored(self, scored_quotes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract decision-making criteria from highest-rated quotes"""
        decision_quotes = []
        
        decision_keywords = ['decided', 'chose', 'selected', 'because', 'reason', 'why', 'factor', 'efficiency', 'time', 'speed', 'quality']
        
        for scored_quote in scored_quotes:
            quote = scored_quote['quote']
            text = quote.get('quote', '').lower()
            
            for keyword in decision_keywords:
                if keyword in text:
                    decision_quotes.append({
                        'quote_id': quote.get('quote_id'),
                        'quote': quote.get('quote'),
                        'interviewee': quote.get('interviewee_name'),
                        'company': quote.get('company'),
                        'priority_score': scored_quote['priority_score'],
                        'keyword': keyword,
                        'context': self._extract_context(text, keyword)
                    })
                    break  # Only count each quote once for decisions
        
        return decision_quotes

    def _extract_competitor_mentions(self, quotes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and analyze competitor mentions from quotes"""
        competitor_mentions = []
        
        for quote in quotes:
            text = quote.get('quote', '').lower()
            
            # Look for competitor names and references
            competitor_indicators = [
                'competitor', 'alternative', 'other solution', 'different company',
                'another vendor', 'other provider', 'similar product'
            ]
            
            for indicator in competitor_indicators:
                if indicator in text:
                    competitor_mentions.append({
                        'quote_id': quote.get('quote_id'),
                        'quote': quote.get('quote'),
                        'interviewee': quote.get('interviewee_name'),
                        'company': quote.get('company'),
                        'indicator': indicator,
                        'context': self._extract_context(text, indicator)
                    })
        
        return competitor_mentions

    def _extract_pricing_context(self, quotes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract pricing-related insights"""
        pricing_quotes = []
        
        pricing_keywords = ['price', 'cost', 'expensive', 'cheaper', 'budget', 'pricing', 'afford']
        
        for quote in quotes:
            text = quote.get('quote', '').lower()
            
            for keyword in pricing_keywords:
                if keyword in text:
                    pricing_quotes.append({
                        'quote_id': quote.get('quote_id'),
                        'quote': quote.get('quote'),
                        'interviewee': quote.get('interviewee_name'),
                        'company': quote.get('company'),
                        'keyword': keyword,
                        'context': self._extract_context(text, keyword)
                    })
                    break
        
        return pricing_quotes

    def _extract_feature_comparisons(self, quotes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract feature comparison insights"""
        feature_quotes = []
        
        feature_keywords = ['feature', 'capability', 'doesn\'t have', 'missing', 'better', 'worse', 'different']
        
        for quote in quotes:
            text = quote.get('quote', '').lower()
            
            for keyword in feature_keywords:
                if keyword in text:
                    feature_quotes.append({
                        'quote_id': quote.get('quote_id'),
                        'quote': quote.get('quote'),
                        'interviewee': quote.get('interviewee_name'),
                        'company': quote.get('company'),
                        'keyword': keyword,
                        'context': self._extract_context(text, keyword)
                    })
                    break
        
        return feature_quotes

    def _extract_decision_criteria(self, quotes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract decision-making criteria"""
        decision_quotes = []
        
        decision_keywords = ['decided', 'chose', 'selected', 'because', 'reason', 'why', 'factor']
        
        for quote in quotes:
            text = quote.get('quote', '').lower()
            
            for keyword in decision_keywords:
                if keyword in text:
                    decision_quotes.append({
                        'quote_id': quote.get('quote_id'),
                        'quote': quote.get('quote'),
                        'interviewee': quote.get('interviewee_name'),
                        'company': quote.get('company'),
                        'keyword': keyword,
                        'context': self._extract_context(text, keyword)
                    })
                    break
        
        return decision_quotes

    def _extract_context(self, text: str, keyword: str) -> str:
        """Extract context around a keyword"""
        words = text.split()
        try:
            keyword_index = words.index(keyword.lower())
            start = max(0, keyword_index - 5)
            end = min(len(words), keyword_index + 6)
            return ' '.join(words[start:end])
        except ValueError:
            return text[:100] + "..."

    def _generate_competitive_prompt(self, quotes: List[Dict[str, Any]], themes: List[Dict[str, Any]], 
                                   competitor_mentions: List[Dict[str, Any]], pricing_insights: List[Dict[str, Any]], 
                                   feature_gaps: List[Dict[str, Any]], decision_factors: List[Dict[str, Any]]) -> str:
        """Generate world-class competitive intelligence prompt"""
        
        prompt = f"""
You are a world-class competitive intelligence analyst specializing in B2B SaaS. 

CONTEXT: We are conducting customer research and have identified critical competitive vulnerabilities. 
Your mission is to provide actionable competitive intelligence that will inform strategic decisions.

CUSTOMER INSIGHTS (from {len(quotes)} interviews):

COMPETITOR MENTIONS ({len(competitor_mentions)} instances):
{self._format_competitive_data(competitor_mentions)}

PRICING PRESSURE POINTS ({len(pricing_insights)} instances):
{self._format_competitive_data(pricing_insights)}

FEATURE COMPARISON GAPS ({len(feature_gaps)} instances):
{self._format_competitive_data(feature_gaps)}

DECISION CRITERIA ({len(decision_factors)} instances):
{self._format_competitive_data(decision_factors)}

CORE THEMES IDENTIFIED:
{self._format_themes(themes)}

YOUR TASK:

1. COMPETITIVE LANDSCAPE ANALYSIS
   - Identify the top 3-5 competitors mentioned or implied in our data
   - Map their positioning against our identified themes
   - Analyze their pricing strategies based on customer feedback
   - Assess their feature strengths/weaknesses relative to our gaps

2. STRATEGIC VULNERABILITY ASSESSMENT
   - Which competitors are most effectively exploiting our weaknesses?
   - What specific messaging are they using against us?
   - How are they positioning themselves in deals we're losing?
   - What competitive advantages are they claiming?

3. OPPORTUNITY IDENTIFICATION
   - Where are competitors weak that we can exploit?
   - What market gaps are they not addressing?
   - What customer pain points are they missing?
   - What pricing strategies are leaving money on the table?

4. ACTIONABLE INTELLIGENCE
   - Specific messaging recommendations to counter competitive threats
   - Pricing strategy adjustments based on competitive pressure
   - Feature development priorities based on competitive gaps
   - Sales enablement content to address competitive objections

5. MARKET POSITIONING RECOMMENDATIONS
   - How should we reposition to neutralize competitive threats?
   - What unique value propositions should we emphasize?
   - What competitive weaknesses should we highlight?
   - How should we adjust our go-to-market strategy?

DELIVERABLE FORMAT:

For each major competitor identified:
- Company: [Name]
- Market Position: [Brief description]
- Key Strengths: [Based on our customer feedback]
- Key Weaknesses: [Opportunities for us]
- Pricing Strategy: [What customers are saying]
- Competitive Messaging: [How they position against us]
- Threat Level: [High/Medium/Low with reasoning]
- Counter-Strategy: [Specific actions we should take]

ADDITIONAL REQUIREMENTS:
- Include specific quotes from our customer data when relevant
- Provide confidence levels for each assessment
- Identify any data gaps that need further research
- Prioritize recommendations by potential business impact
- Include timeline recommendations for implementation

Remember: This intelligence will directly inform strategic decisions worth millions in potential revenue. 
Be thorough, specific, and actionable.
"""
        return prompt

    def _format_competitive_data(self, data: List[Dict[str, Any]]) -> str:
        """Format competitive data for prompt"""
        if not data:
            return "None identified"
        
        formatted = []
        for item in data[:5]:  # Limit to top 5
            priority_info = f" (Priority Score: {item.get('priority_score', 'N/A')})"
            formatted.append(f"- {item['interviewee']} ({item['company']}){priority_info}: \"{item['quote']}\"")
        
        if len(data) > 5:
            formatted.append(f"... and {len(data) - 5} more instances")
        
        return '\n'.join(formatted)

    def _format_themes(self, themes: List[Dict[str, Any]]) -> str:
        """Format themes for prompt"""
        formatted = []
        for theme in themes:
            formatted.append(f"- {theme.get('title', 'Unknown')}: {theme.get('statement', 'No description')}")
        return '\n'.join(formatted) 