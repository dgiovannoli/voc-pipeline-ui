#!/usr/bin/env python3
"""
Enhanced Theme-Story Scorecard Report for B2B SaaS Executives
Addresses critical gaps: theme visibility, client credibility, score context, and executive presentation
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from official_scripts.database.supabase_database import SupabaseDatabase

class EnhancedThemeStoryScorecard:
    """Generate executive-ready theme-driven story with enhanced credibility and clarity"""
    
    def __init__(self):
        self.client_id = 'Rev'
        self.db = SupabaseDatabase()
        
    def generate_enhanced_report(self):
        """Generate enhanced theme-driven story with executive focus"""
        
        print("🎯 GENERATING ENHANCED THEME-STORY SCORECARD REPORT")
        print("Executive-Ready: Themes, Evidence, Credibility, Actionable Insights")
        print("=" * 80)
        
        # Get all data
        themes = self.db.get_themes(self.client_id)
        findings = self.db.get_stage3_findings(self.client_id)
        stage1_data = self.db.get_all_stage1_data_responses()
        rev_data = stage1_data[stage1_data['client_id'] == self.client_id]
        
        print(f"📊 Data Sources:")
        print(f"   Themes: {len(themes)}")
        print(f"   Findings: {len(findings)}")
        print(f"   Quotes: {len(rev_data)}")
        
        # Build enhanced scorecard framework
        scorecard = self._build_enhanced_scorecard(themes, findings, rev_data)
        
        return scorecard
    
    def _build_enhanced_scorecard(self, themes: pd.DataFrame, findings: pd.DataFrame, quotes: pd.DataFrame) -> dict:
        """Build enhanced scorecard framework with executive focus"""
        
        # Executive-focused scorecard criteria
        scorecard_framework = {
            'product_capability': {
                'title': 'Product Capability & Features',
                'weight': 0.35,
                'executive_description': 'Core product functionality that drives user satisfaction and competitive differentiation',
                'strength_definition': 'Features that customers love and competitors struggle to match',
                'weakness_definition': 'Product gaps that create competitive vulnerabilities or user frustration',
                'business_impact': 'Directly impacts customer retention, expansion, and competitive positioning'
            },
            'commercial_terms': {
                'title': 'Commercial Terms & Pricing',
                'weight': 0.25,
                'executive_description': 'Pricing strategy and value proposition that influences purchase decisions',
                'strength_definition': 'Pricing that customers perceive as fair value and supports business growth',
                'weakness_definition': 'Pricing concerns that create barriers to adoption or expansion',
                'business_impact': 'Affects revenue growth, customer acquisition cost, and market penetration'
            },
            'integration_technical_fit': {
                'title': 'Integration & Technical Fit',
                'weight': 0.25,
                'executive_description': 'How well the solution fits into customer workflows and technical environments',
                'strength_definition': 'Seamless integration that enhances user productivity and reduces friction',
                'weakness_definition': 'Integration challenges that create workflow disruption or technical debt',
                'business_impact': 'Influences implementation success, user adoption, and long-term customer satisfaction'
            },
            'security_compliance': {
                'title': 'Security & Compliance',
                'weight': 0.10,
                'executive_description': 'Data security and compliance measures that build or erode customer trust',
                'strength_definition': 'Security practices that exceed customer expectations and industry standards',
                'weakness_definition': 'Security concerns that create risk or compliance barriers',
                'business_impact': 'Critical for enterprise sales, customer trust, and risk mitigation'
            },
            'implementation_onboarding': {
                'title': 'Implementation & Onboarding',
                'weight': 0.05,
                'executive_description': 'Ease of getting customers successfully up and running',
                'strength_definition': 'Smooth onboarding that drives quick time-to-value and user adoption',
                'weakness_definition': 'Implementation challenges that delay value realization or create friction',
                'business_impact': 'Affects customer success, expansion opportunities, and implementation costs'
            }
        }
        
        scorecard = {}
        
        for criterion, framework in scorecard_framework.items():
            # Find all themes for this criterion (not just story themes)
            all_themes = self._find_all_themes(criterion, themes, framework)
            
            # Build comprehensive evidence matrix
            theme_evidence = self._build_comprehensive_evidence(all_themes, findings, quotes)
            
            # Create executive narrative analysis
            narrative_analysis = self._create_executive_narrative(all_themes, theme_evidence, framework)
            
            # Calculate executive-focused metrics
            scorecard_metrics = self._calculate_executive_metrics(all_themes, theme_evidence, framework)
            
            scorecard[criterion] = {
                'framework': framework,
                'all_themes': all_themes,
                'theme_evidence': theme_evidence,
                'narrative_analysis': narrative_analysis,
                'scorecard_metrics': scorecard_metrics
            }
        
        return scorecard
    
    def _find_all_themes(self, criterion: str, themes: pd.DataFrame, framework: dict) -> list:
        """Find ALL themes for this criterion, not just story themes"""
        
        criterion_keywords = self._get_criterion_keywords(criterion)
        all_themes = []
        
        for _, theme in themes.iterrows():
            theme_text = f"{theme['theme_title']} {theme['theme_statement']}".lower()
            
            # Check relevance to criterion
            keyword_matches = sum(1 for keyword in criterion_keywords if keyword in theme_text)
            relevance_score = keyword_matches / len(criterion_keywords) if criterion_keywords else 0
            
            if relevance_score > 0.1:  # Lower threshold to include more themes
                # Determine theme direction and business impact
                theme_analysis = self._analyze_theme_for_executives(theme, criterion, framework)
                
                all_themes.append({
                    'theme_id': theme['theme_id'],
                    'title': theme['theme_title'],
                    'statement': theme['theme_statement'],
                    'classification': theme['classification'],
                    'relevance_score': relevance_score,
                    'direction': theme_analysis['direction'],
                    'business_impact': theme_analysis['business_impact'],
                    'executive_summary': theme_analysis['executive_summary'],
                    'customer_voice': theme_analysis['customer_voice']
                })
        
        # Sort by business impact and relevance
        all_themes.sort(key=lambda x: (x['business_impact']['score'], x['relevance_score']), reverse=True)
        
        return all_themes
    
    def _analyze_theme_for_executives(self, theme: pd.Series, criterion: str, framework: dict) -> dict:
        """Analyze theme from executive perspective"""
        
        theme_text = f"{theme['theme_title']} {theme['theme_statement']}".lower()
        
        # Determine direction with business context
        direction = self._determine_executive_direction(theme_text, criterion)
        
        # Assess business impact
        business_impact = self._assess_business_impact(theme_text, direction, framework)
        
        # Create executive summary
        executive_summary = self._create_executive_summary(theme, direction, business_impact)
        
        # Extract customer voice
        customer_voice = self._extract_customer_voice(theme)
        
        return {
            'direction': direction,
            'business_impact': business_impact,
            'executive_summary': executive_summary,
            'customer_voice': customer_voice
        }
    
    def _determine_executive_direction(self, theme_text: str, criterion: str) -> dict:
        """Determine theme direction with executive context"""
        
        # Enhanced positive indicators for B2B context
        positive_indicators = [
            'improve', 'improves', 'improved', 'improvement', 'improvements',
            'enhance', 'enhances', 'enhanced', 'enhancement', 'enhancements',
            'benefit', 'benefits', 'beneficial', 'advantage', 'advantages', 'advantageous',
            'success', 'successful', 'succeed', 'succeeds', 'succeeding',
            'excellent', 'excellence', 'outstanding', 'superior', 'best',
            'easy', 'easier', 'easiest', 'simple', 'simpler', 'simplest',
            'fast', 'faster', 'fastest', 'quick', 'quicker', 'quickest',
            'efficient', 'efficiency', 'effective', 'effectiveness',
            'love', 'loves', 'loved', 'like', 'likes', 'liked',
            'great', 'good', 'better', 'best', 'amazing', 'wonderful',
            'seamless', 'smooth', 'reliable', 'consistent', 'accurate',
            'valuable', 'worth', 'worthwhile', 'productive', 'time-saving'
        ]
        
        # Enhanced negative indicators for B2B context
        negative_indicators = [
            'inaccuracies', 'inaccuracy', 'error', 'errors', 'mistake', 'mistakes',
            'fail', 'fails', 'failure', 'failures', 'broken', 'break', 'breaks',
            'problem', 'problems', 'issue', 'issues', 'bug', 'bugs',
            'risk', 'risks', 'threat', 'threats', 'danger', 'dangers',
            'suffer', 'suffers', 'suffering', 'decline', 'declines', 'declining',
            'lose', 'loses', 'loss', 'losses', 'losing',
            'complicate', 'complicates', 'complicated', 'complex', 'complexity',
            'difficult', 'difficulty', 'difficulties', 'hard', 'challenging',
            'slow', 'slower', 'slowly', 'delay', 'delays', 'delayed',
            'expensive', 'costly', 'overpriced', 'unaffordable',
            'frustrated', 'frustrating', 'annoyed', 'annoying', 'irritated',
            'disappointing', 'disappointed', 'unreliable', 'inconsistent',
            'waste', 'wastes', 'wasting', 'inefficient', 'ineffective'
        ]
        
        # Count indicators
        positive_count = sum(1 for indicator in positive_indicators if indicator in theme_text)
        negative_count = sum(1 for indicator in negative_indicators if indicator in theme_text)
        
        # Determine direction with confidence
        if positive_count > negative_count:
            direction = 'positive'
            confidence = min(1.0, positive_count / max(negative_count, 1))
        elif negative_count > positive_count:
            direction = 'negative'
            confidence = min(1.0, negative_count / max(positive_count, 1))
        else:
            direction = 'neutral'
            confidence = 0.5
        
        return {
            'direction': direction,
            'confidence': confidence,
            'positive_indicators': positive_count,
            'negative_indicators': negative_count
        }
    
    def _assess_business_impact(self, theme_text: str, direction: dict, framework: dict) -> dict:
        """Assess business impact of theme"""
        
        # Impact scoring based on direction and strength
        base_impact = direction['confidence']
        
        # Adjust for business criticality
        if any(word in theme_text for word in ['revenue', 'cost', 'efficiency', 'productivity']):
            business_multiplier = 1.5
        elif any(word in theme_text for word in ['customer', 'user', 'satisfaction']):
            business_multiplier = 1.3
        else:
            business_multiplier = 1.0
        
        impact_score = base_impact * business_multiplier
        
        # Categorize impact
        if impact_score >= 1.2:
            impact_level = 'high'
            description = 'Significant business impact requiring executive attention'
        elif impact_score >= 0.8:
            impact_level = 'medium'
            description = 'Moderate business impact affecting operational decisions'
        else:
            impact_level = 'low'
            description = 'Limited business impact, operational consideration'
        
        return {
            'score': impact_score,
            'level': impact_level,
            'description': description,
            'multiplier': business_multiplier
        }
    
    def _create_executive_summary(self, theme: pd.Series, direction: dict, business_impact: dict) -> str:
        """Create executive summary of theme"""
        
        theme_title = theme['theme_title']
        direction_type = direction['direction']
        impact_level = business_impact['level']
        
        if direction_type == 'positive':
            if impact_level == 'high':
                return f"Strong competitive advantage: {theme_title}"
            elif impact_level == 'medium':
                return f"Positive differentiator: {theme_title}"
            else:
                return f"Minor strength: {theme_title}"
        elif direction_type == 'negative':
            if impact_level == 'high':
                return f"Critical business risk: {theme_title}"
            elif impact_level == 'medium':
                return f"Competitive vulnerability: {theme_title}"
            else:
                return f"Minor concern: {theme_title}"
        else:
            return f"Neutral factor: {theme_title}"
    
    def _extract_customer_voice(self, theme: pd.Series) -> str:
        """Extract customer voice from theme"""
        
        # This would ideally extract actual customer quotes
        # For now, return the theme statement as customer voice
        return theme['theme_statement']
    
    def _get_criterion_keywords(self, criterion: str) -> list:
        """Get keywords for criterion"""
        keyword_mapping = {
            'product_capability': ['efficiency', 'accuracy', 'speed', 'feature', 'transcription', 'delay', 'inaccuracy', 'correction', 'quality', 'performance'],
            'commercial_terms': ['pricing', 'cost', 'revenue', 'transparency', 'allocation', 'strategy', 'value', 'investment', 'roi', 'budget'],
            'integration_technical_fit': ['integration', 'workflow', 'clio', 'software', 'system', 'efficiency', 'manual', 'automation', 'api', 'technical'],
            'security_compliance': ['security', 'compliance', 'confidential', 'data', 'risk', 'trust', 'privacy', 'protection', 'audit'],
            'implementation_onboarding': ['implementation', 'onboarding', 'training', 'adoption', 'setup', 'record', 'deployment', 'migration']
        }
        return keyword_mapping.get(criterion, [])
    
    def _build_comprehensive_evidence(self, themes: list, findings: pd.DataFrame, quotes: pd.DataFrame) -> dict:
        """Build comprehensive evidence matrix with client names and roles"""
        
        evidence_matrix = {}
        
        for theme in themes:
            theme_id = theme['theme_id']
            
            # Find supporting findings with client context
            supporting_findings = self._find_supporting_findings_with_context(theme, findings)
            
            # Find supporting quotes with client context
            supporting_quotes = self._find_supporting_quotes_with_context(theme, quotes)
            
            # Create evidence summary
            evidence_summary = self._create_evidence_summary_with_context(supporting_findings, supporting_quotes)
            
            evidence_matrix[theme_id] = {
                'findings': supporting_findings,
                'quotes': supporting_quotes,
                'evidence_summary': evidence_summary
            }
        
        return evidence_matrix
    
    def _find_supporting_findings_with_context(self, theme: dict, findings: pd.DataFrame) -> list:
        """Find supporting findings with full client context"""
        
        theme_keywords = self._extract_theme_keywords(theme)
        supporting_findings = []
        
        for _, finding in findings.iterrows():
            finding_text = f"{finding['finding_statement']}".lower()
            
            # Check keyword relevance
            keyword_matches = sum(1 for keyword in theme_keywords if keyword in finding_text)
            if keyword_matches > 0:
                # Add full client context
                supporting_findings.append({
                    'finding_id': finding['finding_id'],
                    'statement': finding['finding_statement'],
                    'confidence': finding.get('enhanced_confidence', 0.5),
                    'company': finding.get('interview_company', 'Unknown Company'),
                    'interviewee_name': finding.get('interviewee_name', 'Unknown'),
                    'interviewee_role': finding.get('interviewee_role', 'Unknown Role'),
                    'industry': finding.get('industry', 'Unknown Industry'),
                    'relevance_score': keyword_matches / len(theme_keywords) if theme_keywords else 0
                })
        
        # Sort by relevance and confidence
        supporting_findings.sort(key=lambda x: (x['relevance_score'], x['confidence']), reverse=True)
        
        return supporting_findings[:10]  # Top 10 findings
    
    def _find_supporting_quotes_with_context(self, theme: dict, quotes: pd.DataFrame) -> list:
        """Find supporting quotes with full client context"""
        
        theme_keywords = self._extract_theme_keywords(theme)
        supporting_quotes = []
        
        for _, quote in quotes.iterrows():
            quote_text = f"{quote['verbatim_response']}".lower()
            
            # Check keyword relevance
            keyword_matches = sum(1 for keyword in theme_keywords if keyword in quote_text)
            if keyword_matches > 0:
                # Analyze quote sentiment and impact
                sentiment = self._analyze_quote_sentiment(quote['verbatim_response'])
                impact = self._analyze_quote_impact(quote['verbatim_response'])
                
                # Add full client context
                supporting_quotes.append({
                    'quote_id': quote['response_id'],
                    'quote': quote['verbatim_response'],
                    'company': quote.get('company', 'Unknown Company'),
                    'interviewee_name': quote.get('interviewee_name', 'Unknown'),
                    'interviewee_role': quote.get('interviewee_role', 'Unknown Role'),
                    'industry': quote.get('industry', 'Unknown Industry'),
                    'sentiment': sentiment,
                    'impact': impact,
                    'relevance_score': keyword_matches / len(theme_keywords) if theme_keywords else 0
                })
        
        # Sort by relevance and impact
        supporting_quotes.sort(key=lambda x: (x['relevance_score'], x['impact']['score']), reverse=True)
        
        return supporting_quotes[:15]  # Top 15 quotes
    
    def _extract_theme_keywords(self, theme: dict) -> list:
        """Extract keywords from theme"""
        
        theme_text = f"{theme['title']} {theme['statement']}".lower()
        
        # Extract meaningful keywords
        keywords = []
        words = theme_text.split()
        
        for word in words:
            # Remove common words and keep meaningful terms
            if len(word) > 3 and word not in ['the', 'and', 'for', 'with', 'that', 'this', 'they', 'have', 'been', 'from', 'their']:
                keywords.append(word)
        
        return keywords[:10]  # Top 10 keywords
    
    def _analyze_quote_sentiment(self, quote_text: str) -> dict:
        """Analyze quote sentiment"""
        
        quote_lower = quote_text.lower()
        
        # Simple sentiment analysis
        positive_words = ['love', 'great', 'good', 'excellent', 'amazing', 'wonderful', 'perfect', 'best', 'easy', 'fast', 'efficient']
        negative_words = ['hate', 'terrible', 'bad', 'awful', 'worst', 'difficult', 'slow', 'inefficient', 'problem', 'issue', 'frustrated']
        
        positive_count = sum(1 for word in positive_words if word in quote_lower)
        negative_count = sum(1 for word in negative_words if word in quote_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
            confidence = min(1.0, positive_count / max(negative_count, 1))
        elif negative_count > positive_count:
            sentiment = 'negative'
            confidence = min(1.0, negative_count / max(positive_count, 1))
        else:
            sentiment = 'neutral'
            confidence = 0.5
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'positive_words': positive_count,
            'negative_words': negative_count
        }
    
    def _analyze_quote_impact(self, quote_text: str) -> dict:
        """Analyze quote business impact"""
        
        quote_lower = quote_text.lower()
        
        # Impact indicators
        high_impact_words = ['revenue', 'cost', 'efficiency', 'productivity', 'critical', 'essential', 'vital']
        medium_impact_words = ['important', 'significant', 'valuable', 'helpful', 'useful']
        
        high_impact_count = sum(1 for word in high_impact_words if word in quote_lower)
        medium_impact_count = sum(1 for word in medium_impact_words if word in quote_lower)
        
        if high_impact_count > 0:
            impact_level = 'high'
            impact_score = 1.0 + (high_impact_count * 0.2)
        elif medium_impact_count > 0:
            impact_level = 'medium'
            impact_score = 0.7 + (medium_impact_count * 0.1)
        else:
            impact_level = 'low'
            impact_score = 0.5
        
        return {
            'level': impact_level,
            'score': min(2.0, impact_score),
            'high_impact_words': high_impact_count,
            'medium_impact_words': medium_impact_count
        }
    
    def _create_evidence_summary_with_context(self, findings: list, quotes: list) -> dict:
        """Create evidence summary with client context"""
        
        total_evidence = len(findings) + len(quotes)
        
        if total_evidence == 0:
            return {
                'total_evidence': 0,
                'strength': 'none',
                'client_coverage': 'none',
                'top_clients': [],
                'evidence_quality': 'none'
            }
        
        # Analyze client coverage
        clients = set()
        for finding in findings:
            clients.add(finding['company'])
        for quote in quotes:
            clients.add(quote['company'])
        
        # Get top clients by evidence volume
        client_evidence = {}
        for finding in findings:
            client = finding['company']
            client_evidence[client] = client_evidence.get(client, 0) + 1
        for quote in quotes:
            client = quote['company']
            client_evidence[client] = client_evidence.get(client, 0) + 1
        
        top_clients = sorted(client_evidence.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Determine evidence strength
        if total_evidence >= 20:
            strength = 'strong'
        elif total_evidence >= 10:
            strength = 'moderate'
        else:
            strength = 'weak'
        
        # Determine client coverage
        if len(clients) >= 5:
            coverage = 'broad'
        elif len(clients) >= 3:
            coverage = 'moderate'
        else:
            coverage = 'limited'
        
        # Determine evidence quality
        high_quality_evidence = sum(1 for finding in findings if finding['confidence'] >= 0.7)
        high_quality_evidence += sum(1 for quote in quotes if quote['impact']['score'] >= 1.0)
        
        quality_ratio = high_quality_evidence / total_evidence if total_evidence > 0 else 0
        
        if quality_ratio >= 0.7:
            quality = 'high'
        elif quality_ratio >= 0.4:
            quality = 'moderate'
        else:
            quality = 'low'
        
        return {
            'total_evidence': total_evidence,
            'strength': strength,
            'client_coverage': coverage,
            'top_clients': top_clients,
            'evidence_quality': quality,
            'unique_clients': len(clients),
            'high_quality_ratio': quality_ratio
        }
    
    def _create_executive_narrative(self, themes: list, theme_evidence: dict, framework: dict) -> dict:
        """Create executive-focused narrative analysis"""
        
        # Separate themes by direction
        positive_themes = [t for t in themes if t['direction']['direction'] == 'positive']
        negative_themes = [t for t in themes if t['direction']['direction'] == 'negative']
        neutral_themes = [t for t in themes if t['direction']['direction'] == 'neutral']
        
        # Create executive narratives
        strengths_narrative = self._create_strengths_narrative(positive_themes, theme_evidence, framework)
        weaknesses_narrative = self._create_weaknesses_narrative(negative_themes, theme_evidence, framework)
        opportunities_narrative = self._create_opportunities_narrative(neutral_themes, theme_evidence, framework)
        
        # Overall business story
        overall_story = self._create_overall_business_story(themes, theme_evidence, framework)
        
        return {
            'strengths_narrative': strengths_narrative,
            'weaknesses_narrative': weaknesses_narrative,
            'opportunities_narrative': opportunities_narrative,
            'overall_story': overall_story,
            'theme_distribution': {
                'positive_themes': len(positive_themes),
                'negative_themes': len(negative_themes),
                'neutral_themes': len(neutral_themes),
                'total_themes': len(themes)
            }
        }
    
    def _create_strengths_narrative(self, positive_themes: list, theme_evidence: dict, framework: dict) -> str:
        """Create strengths narrative for executives"""
        
        if not positive_themes:
            return "No significant strengths identified in this area."
        
        # Get top 3 strengths by business impact
        top_strengths = sorted(positive_themes, key=lambda x: x['business_impact']['score'], reverse=True)[:3]
        
        strength_descriptions = []
        for strength in top_strengths:
            evidence = theme_evidence.get(strength['theme_id'], {})
            evidence_summary = evidence.get('evidence_summary', {})
            
            strength_desc = f"{strength['title']} - {strength['executive_summary']}"
            if evidence_summary.get('total_evidence', 0) > 0:
                strength_desc += f" (Supported by {evidence_summary['total_evidence']} evidence items from {evidence_summary['unique_clients']} clients)"
            
            strength_descriptions.append(strength_desc)
        
        return f"Key strengths include: {'; '.join(strength_descriptions)}"
    
    def _create_weaknesses_narrative(self, negative_themes: list, theme_evidence: dict, framework: dict) -> str:
        """Create weaknesses narrative for executives"""
        
        if not negative_themes:
            return "No significant weaknesses identified in this area."
        
        # Get top 3 weaknesses by business impact
        top_weaknesses = sorted(negative_themes, key=lambda x: x['business_impact']['score'], reverse=True)[:3]
        
        weakness_descriptions = []
        for weakness in top_weaknesses:
            evidence = theme_evidence.get(weakness['theme_id'], {})
            evidence_summary = evidence.get('evidence_summary', {})
            
            weakness_desc = f"{weakness['title']} - {weakness['executive_summary']}"
            if evidence_summary.get('total_evidence', 0) > 0:
                weakness_desc += f" (Supported by {evidence_summary['total_evidence']} evidence items from {evidence_summary['unique_clients']} clients)"
            
            weakness_descriptions.append(weakness_desc)
        
        return f"Key areas for improvement include: {'; '.join(weakness_descriptions)}"
    
    def _create_opportunities_narrative(self, neutral_themes: list, theme_evidence: dict, framework: dict) -> str:
        """Create opportunities narrative for executives"""
        
        if not neutral_themes:
            return "No significant opportunities identified in this area."
        
        # Get top 3 opportunities by business impact
        top_opportunities = sorted(neutral_themes, key=lambda x: x['business_impact']['score'], reverse=True)[:3]
        
        opportunity_descriptions = []
        for opportunity in top_opportunities:
            evidence = theme_evidence.get(opportunity['theme_id'], {})
            evidence_summary = evidence.get('evidence_summary', {})
            
            opportunity_desc = f"{opportunity['title']} - {opportunity['executive_summary']}"
            if evidence_summary.get('total_evidence', 0) > 0:
                opportunity_desc += f" (Supported by {evidence_summary['total_evidence']} evidence items from {evidence_summary['unique_clients']} clients)"
            
            opportunity_descriptions.append(opportunity_desc)
        
        return f"Potential opportunities include: {'; '.join(opportunity_descriptions)}"
    
    def _create_overall_business_story(self, themes: list, theme_evidence: dict, framework: dict) -> str:
        """Create overall business story for executives"""
        
        if not themes:
            return f"No themes identified for {framework['title']}."
        
        # Calculate overall sentiment
        positive_count = len([t for t in themes if t['direction']['direction'] == 'positive'])
        negative_count = len([t for t in themes if t['direction']['direction'] == 'negative'])
        neutral_count = len([t for t in themes if t['direction']['direction'] == 'neutral'])
        
        total_themes = len(themes)
        
        if positive_count > negative_count:
            sentiment = "positive"
            story_type = "competitive advantage"
        elif negative_count > positive_count:
            sentiment = "negative"
            story_type = "competitive vulnerability"
        else:
            sentiment = "mixed"
            story_type = "competitive opportunity"
        
        # Get total evidence
        total_evidence = sum(
            theme_evidence.get(theme['theme_id'], {}).get('evidence_summary', {}).get('total_evidence', 0)
            for theme in themes
        )
        
        return f"Overall {sentiment} sentiment with {total_themes} themes ({positive_count} positive, {negative_count} negative, {neutral_count} neutral) supported by {total_evidence} evidence items, indicating {story_type} in {framework['title'].lower()}."
    
    def _calculate_executive_metrics(self, themes: list, theme_evidence: dict, framework: dict) -> dict:
        """Calculate executive-focused metrics"""
        
        if not themes:
            return {
                'score': 5.0,
                'performance': 'neutral',
                'weight': framework['weight'],
                'weighted_score': 5.0 * framework['weight'],
                'evidence_coverage': 'none',
                'strength_count': 0,
                'weakness_count': 0,
                'opportunity_count': 0,
                'total_evidence': 0,
                'client_coverage': 'none'
            }
        
        # Calculate theme scores
        positive_themes = [t for t in themes if t['direction']['direction'] == 'positive']
        negative_themes = [t for t in themes if t['direction']['direction'] == 'negative']
        neutral_themes = [t for t in themes if t['direction']['direction'] == 'neutral']
        
        # Calculate overall score based on theme distribution and business impact
        positive_score = sum(t['business_impact']['score'] for t in positive_themes)
        negative_score = sum(t['business_impact']['score'] for t in negative_themes)
        neutral_score = sum(t['business_impact']['score'] for t in neutral_themes) * 0.5  # Neutral themes count half
        
        total_impact = positive_score + negative_score + neutral_score
        
        if total_impact > 0:
            # Normalize to 0-10 scale
            overall_score = min(10.0, (positive_score / total_impact) * 10)
        else:
            overall_score = 5.0
        
        # Determine performance level
        if overall_score >= 7.5:
            performance = 'excellent'
            performance_description = 'Strong competitive advantages with clear market differentiation'
        elif overall_score >= 6.0:
            performance = 'good'
            performance_description = 'Competitive positioning with some areas for improvement'
        elif overall_score >= 4.5:
            performance = 'fair'
            performance_description = 'Mixed competitive position with significant improvement opportunities'
        elif overall_score >= 3.0:
            performance = 'poor'
            performance_description = 'Competitive vulnerabilities requiring immediate attention'
        else:
            performance = 'critical'
            performance_description = 'Major competitive disadvantages requiring urgent strategic intervention'
        
        # Calculate evidence metrics
        total_evidence = sum(
            theme_evidence.get(theme['theme_id'], {}).get('evidence_summary', {}).get('total_evidence', 0)
            for theme in themes
        )
        
        # Determine evidence coverage
        if total_evidence >= 50:
            coverage = 'comprehensive'
        elif total_evidence >= 25:
            coverage = 'substantial'
        elif total_evidence >= 10:
            coverage = 'moderate'
        else:
            coverage = 'limited'
        
        # Calculate client coverage
        all_clients = set()
        for theme in themes:
            evidence = theme_evidence.get(theme['theme_id'], {})
            evidence_summary = evidence.get('evidence_summary', {})
            if evidence_summary.get('unique_clients'):
                all_clients.update(range(evidence_summary['unique_clients']))
        
        if len(all_clients) >= 10:
            client_coverage = 'broad'
        elif len(all_clients) >= 5:
            client_coverage = 'moderate'
        else:
            client_coverage = 'limited'
        
        return {
            'score': overall_score,
            'performance': performance,
            'performance_description': performance_description,
            'weight': framework['weight'],
            'weighted_score': overall_score * framework['weight'],
            'evidence_coverage': coverage,
            'strength_count': len(positive_themes),
            'weakness_count': len(negative_themes),
            'opportunity_count': len(neutral_themes),
            'total_evidence': total_evidence,
            'client_coverage': client_coverage,
            'unique_clients': len(all_clients),
            'theme_count': len(themes)
        }
    
    def print_enhanced_report(self, scorecard: dict):
        """Print enhanced executive report"""
        
        print("\n" + "="*100)
        print("🎯 ENHANCED THEME-STORY SCORECARD REPORT FOR B2B SAAS EXECUTIVES")
        print("Executive-Ready: Themes, Evidence, Credibility, Actionable Insights")
        print("="*100)
        
        # Executive Summary with Strengths & Weaknesses
        self._print_executive_summary(scorecard)
        
        # Detailed Scorecard Framework
        self._print_detailed_scorecard(scorecard)
        
        # Theme-Driven Analysis by Criterion
        self._print_theme_analysis(scorecard)
        
        # Strategic Implications
        self._print_strategic_implications(scorecard)
        
        print("\n🎯 ENHANCED THEME-STORY SCORECARD REPORT COMPLETE")
        print("="*100)
    
    def _print_executive_summary(self, scorecard: dict):
        """Print executive summary with strengths and weaknesses"""
        
        print(f"\n📋 EXECUTIVE SUMMARY")
        
        # Calculate overall metrics
        total_weighted_score = sum(data['scorecard_metrics']['weighted_score'] for data in scorecard.values())
        total_weight = sum(data['scorecard_metrics']['weight'] for data in scorecard.values())
        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
        
        # Count strengths and weaknesses
        total_strengths = sum(data['scorecard_metrics']['strength_count'] for data in scorecard.values())
        total_weaknesses = sum(data['scorecard_metrics']['weakness_count'] for data in scorecard.values())
        total_opportunities = sum(data['scorecard_metrics']['opportunity_count'] for data in scorecard.values())
        
        print(f"   Overall Score: {overall_score:.1f}/10")
        print(f"   Performance Level: {self._get_enhanced_performance_level(overall_score)}")
        print(f"   Theme Distribution: {total_strengths} strengths, {total_weaknesses} weaknesses, {total_opportunities} opportunities")
        
        # Top Strengths
        print(f"\n   🏆 TOP STRENGTHS:")
        strengths_by_criterion = []
        for criterion, data in scorecard.items():
            if data['scorecard_metrics']['strength_count'] > 0:
                strengths_by_criterion.append({
                    'criterion': data['framework']['title'],
                    'strength_count': data['scorecard_metrics']['strength_count'],
                    'score': data['scorecard_metrics']['score']
                })
        
        strengths_by_criterion.sort(key=lambda x: x['strength_count'], reverse=True)
        for strength in strengths_by_criterion[:3]:
            print(f"     • {strength['criterion']}: {strength['strength_count']} strengths (Score: {strength['score']:.1f}/10)")
        
        # Top Areas for Improvement
        print(f"\n   🔧 TOP AREAS FOR IMPROVEMENT:")
        weaknesses_by_criterion = []
        for criterion, data in scorecard.items():
            if data['scorecard_metrics']['weakness_count'] > 0:
                weaknesses_by_criterion.append({
                    'criterion': data['framework']['title'],
                    'weakness_count': data['scorecard_metrics']['weakness_count'],
                    'score': data['scorecard_metrics']['score']
                })
        
        weaknesses_by_criterion.sort(key=lambda x: x['weakness_count'], reverse=True)
        for weakness in weaknesses_by_criterion[:3]:
            print(f"     • {weakness['criterion']}: {weakness['weakness_count']} weaknesses (Score: {weakness['score']:.1f}/10)")
    
    def _print_detailed_scorecard(self, scorecard: dict):
        """Print detailed scorecard framework"""
        
        print(f"\n📊 DETAILED SCORECARD FRAMEWORK")
        print(f"   Understanding the Framework:")
        print(f"   • Score (0-10): Overall performance in this area based on theme analysis")
        print(f"   • Weight (%): Relative importance of this area to overall business success")
        print(f"   • Evidence: Number of supporting quotes and findings from customer interviews")
        print(f"   • Performance: Executive assessment of competitive position")
        
        for criterion, data in scorecard.items():
            metrics = data['scorecard_metrics']
            framework = data['framework']
            
            print(f"\n   📋 {framework['title']}")
            print(f"     Weight: {metrics['weight']*100:.0f}% - {framework['business_impact']}")
            print(f"     Score: {metrics['score']:.1f}/10 - {metrics['performance_description']}")
            print(f"     Evidence: {metrics['total_evidence']} items from {metrics['unique_clients']} clients")
            print(f"     Coverage: {metrics['evidence_coverage']} evidence, {metrics['client_coverage']} client coverage")
            print(f"     Themes: {metrics['strength_count']} strengths, {metrics['weakness_count']} weaknesses, {metrics['opportunity_count']} opportunities")
    
    def _print_theme_analysis(self, scorecard: dict):
        """Print detailed theme analysis by criterion"""
        
        print(f"\n🎯 THEME-DRIVEN ANALYSIS BY CRITERION")
        
        for criterion, data in scorecard.items():
            print(f"\n   📋 {data['framework']['title']}")
            print(f"     {data['framework']['executive_description']}")
            
            # Strengths
            positive_themes = [t for t in data['all_themes'] if t['direction']['direction'] == 'positive']
            if positive_themes:
                print(f"\n     🏆 STRENGTHS:")
                for theme in positive_themes[:3]:  # Top 3 strengths
                    evidence = data['theme_evidence'].get(theme['theme_id'], {})
                    evidence_summary = evidence.get('evidence_summary', {})
                    
                    print(f"       • {theme['title']}")
                    print(f"         {theme['statement']}")
                    print(f"         Business Impact: {theme['business_impact']['description']}")
                    print(f"         Evidence: {evidence_summary.get('total_evidence', 0)} items from {evidence_summary.get('unique_clients', 0)} clients")
                    
                    # Show top supporting quote
                    if evidence.get('quotes'):
                        top_quote = evidence['quotes'][0]
                        print(f"         Key Quote: \"{top_quote['quote'][:150]}...\"")
                        print(f"           - {top_quote['interviewee_name']}, {top_quote['interviewee_role']} at {top_quote['company']}")
            
            # Weaknesses
            negative_themes = [t for t in data['all_themes'] if t['direction']['direction'] == 'negative']
            if negative_themes:
                print(f"\n     🔧 AREAS FOR IMPROVEMENT:")
                for theme in negative_themes[:3]:  # Top 3 weaknesses
                    evidence = data['theme_evidence'].get(theme['theme_id'], {})
                    evidence_summary = evidence.get('evidence_summary', {})
                    
                    print(f"       • {theme['title']}")
                    print(f"         {theme['statement']}")
                    print(f"         Business Impact: {theme['business_impact']['description']}")
                    print(f"         Evidence: {evidence_summary.get('total_evidence', 0)} items from {evidence_summary.get('unique_clients', 0)} clients")
                    
                    # Show top supporting quote
                    if evidence.get('quotes'):
                        top_quote = evidence['quotes'][0]
                        print(f"         Key Quote: \"{top_quote['quote'][:150]}...\"")
                        print(f"           - {top_quote['interviewee_name']}, {top_quote['interviewee_role']} at {top_quote['company']}")
    
    def _print_strategic_implications(self, scorecard: dict):
        """Print strategic implications"""
        
        print(f"\n📈 STRATEGIC IMPLICATIONS")
        print(f"   🎯 Executive Recommendations:")
        
        for criterion, data in scorecard.items():
            metrics = data['scorecard_metrics']
            framework = data['framework']
            
            if metrics['performance'] in ['excellent', 'good']:
                print(f"     • {framework['title']}: Leverage existing strengths for competitive advantage")
            elif metrics['performance'] in ['poor', 'critical']:
                print(f"     • {framework['title']}: Prioritize improvements to address competitive vulnerabilities")
            else:
                print(f"     • {framework['title']}: Focus on opportunities to enhance competitive positioning")
    
    def _get_enhanced_performance_level(self, score: float) -> str:
        """Get enhanced performance level description"""
        if score >= 7.5:
            return 'Excellent - Strong competitive advantages with clear market differentiation'
        elif score >= 6.0:
            return 'Good - Competitive positioning with some areas for improvement'
        elif score >= 4.5:
            return 'Fair - Mixed competitive position with significant improvement opportunities'
        elif score >= 3.0:
            return 'Poor - Competitive vulnerabilities requiring immediate attention'
        else:
            return 'Critical - Major competitive disadvantages requiring urgent strategic intervention'

def main():
    """Main function to generate enhanced report"""
    generator = EnhancedThemeStoryScorecard()
    scorecard = generator.generate_enhanced_report()
    generator.print_enhanced_report(scorecard)

if __name__ == "__main__":
    main() 