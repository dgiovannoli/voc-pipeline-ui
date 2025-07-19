#!/usr/bin/env python3
"""
Rev Theme-Story Scorecard Report
Themes tell the story, findings/quotes provide evidence, scorecard anchors the framework
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from official_scripts.database.supabase_database import SupabaseDatabase

class RevThemeStoryScorecard:
    """Generate theme-driven story anchored by scorecard framework"""
    
    def __init__(self):
        self.client_id = 'Rev'
        self.db = SupabaseDatabase()
        
    def generate_theme_story_report(self):
        """Generate theme-driven story with scorecard framework"""
        
        print("🎯 GENERATING REV THEME-STORY SCORECARD REPORT")
        print("Themes Tell the Story, Evidence Supports, Scorecard Anchors")
        print("=" * 70)
        
        # Get all data
        themes = self.db.get_themes(self.client_id)
        findings = self.db.get_stage3_findings(self.client_id)
        stage1_data = self.db.get_all_stage1_data_responses()
        rev_data = stage1_data[stage1_data['client_id'] == self.client_id]
        
        print(f"📊 Data Sources:")
        print(f"   Themes: {len(themes)}")
        print(f"   Findings: {len(findings)}")
        print(f"   Quotes: {len(rev_data)}")
        
        # Build scorecard framework with theme stories
        scorecard = self._build_theme_story_scorecard(themes, findings, rev_data)
        
        return scorecard
    
    def _build_theme_story_scorecard(self, themes: pd.DataFrame, findings: pd.DataFrame, quotes: pd.DataFrame) -> dict:
        """Build scorecard framework with theme-driven stories"""
        
        # Scorecard criteria as the anchoring framework
        scorecard_framework = {
            'product_capability': {
                'title': 'Product Capability & Features',
                'weight': 0.35,
                'description': 'Core transcription functionality and user experience',
                'story_theme': 'How Rev\'s product capabilities impact user success and satisfaction',
                'win_narrative': 'Rev\'s product strengths that drive competitive advantage',
                'loss_narrative': 'Product gaps that create competitive vulnerabilities'
            },
            'commercial_terms': {
                'title': 'Commercial Terms & Pricing',
                'weight': 0.25,
                'description': 'Pricing strategy and value proposition',
                'story_theme': 'How pricing transparency and value perception influence decisions',
                'win_narrative': 'Commercial advantages that support customer acquisition',
                'loss_narrative': 'Pricing and commercial factors that hinder adoption'
            },
            'integration_technical_fit': {
                'title': 'Integration & Technical Fit',
                'weight': 0.25,
                'description': 'Workflow integration and technical compatibility',
                'story_theme': 'How integration capabilities affect workflow efficiency',
                'win_narrative': 'Integration strengths that enhance user workflows',
                'loss_narrative': 'Integration gaps that disrupt user processes'
            },
            'security_compliance': {
                'title': 'Security & Compliance',
                'weight': 0.10,
                'description': 'Data security and compliance standards',
                'story_theme': 'How security and compliance build or erode trust',
                'win_narrative': 'Security measures that build customer confidence',
                'loss_narrative': 'Security concerns that create adoption barriers'
            },
            'implementation_onboarding': {
                'title': 'Implementation & Onboarding',
                'weight': 0.05,
                'description': 'Setup process and user adoption',
                'story_theme': 'How implementation ease affects user success',
                'win_narrative': 'Implementation strengths that drive quick adoption',
                'loss_narrative': 'Implementation challenges that slow adoption'
            }
        }
        
        scorecard = {}
        
        for criterion, framework in scorecard_framework.items():
            # Find themes that tell the story for this criterion
            story_themes = self._find_story_themes(criterion, themes, framework)
            
            # Build evidence matrix for each theme
            theme_evidence = self._build_theme_evidence(story_themes, findings, quotes)
            
            # Create narrative analysis
            narrative_analysis = self._create_narrative_analysis(story_themes, theme_evidence, framework)
            
            # Calculate scorecard metrics
            scorecard_metrics = self._calculate_scorecard_metrics(story_themes, theme_evidence, framework['weight'])
            
            scorecard[criterion] = {
                'framework': framework,
                'story_themes': story_themes,
                'theme_evidence': theme_evidence,
                'narrative_analysis': narrative_analysis,
                'scorecard_metrics': scorecard_metrics
            }
        
        return scorecard
    
    def _find_story_themes(self, criterion: str, themes: pd.DataFrame, framework: dict) -> list:
        """Find themes that tell the story for this criterion"""
        
        criterion_keywords = self._get_criterion_keywords(criterion)
        story_themes = []
        
        for _, theme in themes.iterrows():
            theme_text = f"{theme['theme_title']} {theme['theme_statement']}".lower()
            
            # Check relevance to criterion
            keyword_matches = sum(1 for keyword in criterion_keywords if keyword in theme_text)
            relevance_score = keyword_matches / len(criterion_keywords) if criterion_keywords else 0
            
            if relevance_score > 0.2:  # Threshold for story relevance
                # Determine story direction
                story_direction = self._determine_story_direction(theme, criterion)
                
                story_themes.append({
                    'theme_id': theme['theme_id'],
                    'title': theme['theme_title'],
                    'statement': theme['theme_statement'],
                    'classification': theme['classification'],
                    'relevance_score': relevance_score,
                    'story_direction': story_direction,
                    'narrative_role': self._determine_narrative_role(theme, story_direction, framework)
                })
        
        # Sort by relevance and story impact
        story_themes.sort(key=lambda x: (x['relevance_score'], x['story_direction']['impact_score']), reverse=True)
        
        return story_themes
    
    def _get_criterion_keywords(self, criterion: str) -> list:
        """Get keywords for criterion"""
        keyword_mapping = {
            'product_capability': ['efficiency', 'accuracy', 'speed', 'feature', 'transcription', 'delay', 'inaccuracy', 'correction'],
            'commercial_terms': ['pricing', 'cost', 'revenue', 'transparency', 'allocation', 'strategy', 'value'],
            'integration_technical_fit': ['integration', 'workflow', 'clio', 'software', 'system', 'efficiency', 'manual'],
            'security_compliance': ['security', 'compliance', 'confidential', 'data', 'risk', 'trust'],
            'implementation_onboarding': ['implementation', 'onboarding', 'training', 'adoption', 'setup', 'record']
        }
        return keyword_mapping.get(criterion, [])
    
    def _determine_story_direction(self, theme: pd.Series, criterion: str) -> dict:
        """Determine the story direction for the theme"""
        
        theme_text = f"{theme['theme_title']} {theme['theme_statement']}".lower()
        
        # Analyze theme sentiment and impact
        positive_indicators = ['efficiency', 'improve', 'enhance', 'benefit', 'advantage', 'success']
        negative_indicators = ['risk', 'decline', 'suffer', 'complicate', 'fail', 'threat']
        
        positive_count = sum(1 for indicator in positive_indicators if indicator in theme_text)
        negative_count = sum(1 for indicator in negative_indicators if indicator in theme_text)
        
        if positive_count > negative_count:
            direction = 'positive'
            impact_score = 7
            story_type = 'success_story'
        elif negative_count > positive_count:
            direction = 'negative'
            impact_score = 3
            story_type = 'challenge_story'
        else:
            direction = 'neutral'
            impact_score = 5
            story_type = 'observation_story'
        
        return {
            'direction': direction,
            'impact_score': impact_score,
            'story_type': story_type,
            'positive_indicators': positive_count,
            'negative_indicators': negative_count
        }
    
    def _determine_narrative_role(self, theme: pd.Series, story_direction: dict, framework: dict) -> str:
        """Determine the narrative role of the theme"""
        
        if story_direction['direction'] == 'positive':
            return framework['win_narrative']
        elif story_direction['direction'] == 'negative':
            return framework['loss_narrative']
        else:
            return 'neutral_observation'
    
    def _build_theme_evidence(self, story_themes: list, findings: pd.DataFrame, quotes: pd.DataFrame) -> dict:
        """Build evidence matrix for each theme"""
        
        theme_evidence = {}
        
        for theme in story_themes:
            theme_id = theme['theme_id']
            
            # Find supporting findings
            supporting_findings = self._find_supporting_findings(theme, findings)
            
            # Find supporting quotes
            supporting_quotes = self._find_supporting_quotes(theme, quotes)
            
            theme_evidence[theme_id] = {
                'theme': theme,
                'findings': supporting_findings,
                'quotes': supporting_quotes,
                'evidence_summary': self._create_evidence_summary(supporting_findings, supporting_quotes)
            }
        
        return theme_evidence
    
    def _find_supporting_findings(self, theme: dict, findings: pd.DataFrame) -> list:
        """Find findings that support the theme story"""
        
        theme_keywords = self._extract_theme_keywords(theme)
        supporting = []
        
        for _, finding in findings.iterrows():
            finding_text = finding['finding_statement'].lower()
            keyword_matches = sum(1 for keyword in theme_keywords if keyword in finding_text)
            
            if keyword_matches > 0:
                supporting.append({
                    'id': finding['finding_id'],
                    'statement': finding['finding_statement'],
                    'company': finding['interview_company'],
                    'interviewee': finding['interviewee_name'],
                    'primary_quote': finding['primary_quote'],
                    'relevance_score': keyword_matches / len(theme_keywords) if theme_keywords else 0,
                    'evidence_type': 'quantitative_impact' if any(word in finding_text for word in ['significantly', 'dramatically', 'substantially']) else 'qualitative_insight'
                })
        
        # Sort by relevance
        supporting.sort(key=lambda x: x['relevance_score'], reverse=True)
        return supporting
    
    def _find_supporting_quotes(self, theme: dict, quotes: pd.DataFrame) -> list:
        """Find quotes that support the theme story"""
        
        theme_keywords = self._extract_theme_keywords(theme)
        supporting = []
        
        for _, quote in quotes.iterrows():
            quote_text = quote['verbatim_response'].lower()
            keyword_matches = sum(1 for keyword in theme_keywords if keyword in quote_text)
            
            if keyword_matches > 0:
                # Analyze quote sentiment and impact
                sentiment_analysis = self._analyze_quote_sentiment(quote_text)
                impact_analysis = self._analyze_quote_impact(quote_text)
                
                supporting.append({
                    'company': quote['company'],
                    'interviewee': quote['interviewee_name'],
                    'quote': quote['verbatim_response'],
                    'relevance_score': keyword_matches / len(theme_keywords) if theme_keywords else 0,
                    'sentiment': sentiment_analysis,
                    'impact': impact_analysis,
                    'story_role': self._determine_quote_story_role(sentiment_analysis, impact_analysis, theme['story_direction']['direction'])
                })
        
        # Sort by relevance and impact
        supporting.sort(key=lambda x: (x['relevance_score'], x['impact']['level']), reverse=True)
        return supporting
    
    def _extract_theme_keywords(self, theme: dict) -> list:
        """Extract keywords from theme"""
        
        theme_text = f"{theme['title']} {theme['statement']}".lower()
        
        # Extract key concepts based on theme content
        keywords = []
        
        # Efficiency-related
        if any(word in theme_text for word in ['efficiency', 'efficient', 'time', 'speed', 'fast', 'delay']):
            keywords.extend(['efficiency', 'time', 'speed', 'fast', 'delay'])
        
        # Cost-related
        if any(word in theme_text for word in ['cost', 'pricing', 'revenue', 'expensive', 'budget', 'strategy']):
            keywords.extend(['cost', 'pricing', 'revenue', 'expensive', 'budget', 'strategy'])
        
        # Integration-related
        if any(word in theme_text for word in ['integration', 'workflow', 'clio', 'software', 'system']):
            keywords.extend(['integration', 'workflow', 'clio', 'software', 'system'])
        
        # Security-related
        if any(word in theme_text for word in ['security', 'compliance', 'confidential', 'data', 'risk']):
            keywords.extend(['security', 'compliance', 'confidential', 'data', 'risk'])
        
        # Implementation-related
        if any(word in theme_text for word in ['implementation', 'onboarding', 'training', 'adoption', 'setup']):
            keywords.extend(['implementation', 'onboarding', 'training', 'adoption', 'setup'])
        
        # Transcription-related
        if any(word in theme_text for word in ['transcription', 'accuracy', 'inaccuracy', 'correction']):
            keywords.extend(['transcription', 'accuracy', 'inaccuracy', 'correction'])
        
        return list(set(keywords))  # Remove duplicates
    
    def _analyze_quote_sentiment(self, quote_text: str) -> dict:
        """Analyze quote sentiment"""
        
        positive_words = ['good', 'great', 'excellent', 'love', 'like', 'easy', 'fast', 'helpful', 'saved', 'stress', 'appreciate']
        negative_words = ['bad', 'terrible', 'hate', 'difficult', 'slow', 'expensive', 'problem', 'issue', 'concern', 'frustrated']
        
        positive_count = sum(1 for word in positive_words if word in quote_text)
        negative_count = sum(1 for word in negative_words if word in quote_text)
        
        if positive_count > negative_count:
            sentiment = 'positive'
            score = 8
        elif negative_count > positive_count:
            sentiment = 'negative'
            score = 2
        else:
            sentiment = 'neutral'
            score = 5
        
        return {
            'sentiment': sentiment,
            'score': score,
            'positive_count': positive_count,
            'negative_count': negative_count
        }
    
    def _analyze_quote_impact(self, quote_text: str) -> dict:
        """Analyze quote impact"""
        
        impact_indicators = ['important', 'critical', 'essential', 'need', 'must', 'should', 'would', 'could']
        impact_count = sum(1 for indicator in impact_indicators if indicator in quote_text)
        
        if impact_count >= 3:
            level = 'high'
        elif impact_count >= 1:
            level = 'medium'
        else:
            level = 'low'
        
        return {
            'level': level,
            'indicators': impact_count
        }
    
    def _determine_quote_story_role(self, sentiment: dict, impact: dict, theme_direction: str) -> str:
        """Determine the role of the quote in the story"""
        
        if theme_direction == 'positive' and sentiment['sentiment'] == 'positive':
            return 'success_validation'
        elif theme_direction == 'negative' and sentiment['sentiment'] == 'negative':
            return 'challenge_confirmation'
        elif impact['level'] == 'high':
            return 'key_insight'
        else:
            return 'supporting_detail'
    
    def _create_evidence_summary(self, findings: list, quotes: list) -> dict:
        """Create evidence summary for theme"""
        
        total_evidence = len(findings) + len(quotes)
        
        if total_evidence == 0:
            return {'strength': 'none', 'confidence': 'low', 'story_support': 'minimal'}
        
        # Calculate evidence strength
        finding_relevance = sum(f['relevance_score'] for f in findings) / len(findings) if findings else 0
        quote_relevance = sum(q['relevance_score'] for q in quotes) / len(quotes) if quotes else 0
        overall_relevance = (finding_relevance + quote_relevance) / 2
        
        # Analyze sentiment balance
        positive_quotes = sum(1 for q in quotes if q['sentiment']['sentiment'] == 'positive')
        negative_quotes = sum(1 for q in quotes if q['sentiment']['sentiment'] == 'negative')
        
        # Determine evidence strength
        if overall_relevance >= 0.6 and total_evidence >= 5:
            strength = 'strong'
            confidence = 'high'
        elif overall_relevance >= 0.4 and total_evidence >= 3:
            strength = 'moderate'
            confidence = 'medium'
        else:
            strength = 'weak'
            confidence = 'low'
        
        # Determine story support
        if total_evidence >= 10 and overall_relevance >= 0.5:
            story_support = 'comprehensive'
        elif total_evidence >= 5 and overall_relevance >= 0.4:
            story_support = 'substantial'
        else:
            story_support = 'limited'
        
        return {
            'strength': strength,
            'confidence': confidence,
            'story_support': story_support,
            'total_evidence': total_evidence,
            'finding_count': len(findings),
            'quote_count': len(quotes),
            'overall_relevance': overall_relevance,
            'sentiment_balance': {
                'positive': positive_quotes,
                'negative': negative_quotes,
                'neutral': len(quotes) - positive_quotes - negative_quotes
            }
        }
    
    def _create_narrative_analysis(self, story_themes: list, theme_evidence: dict, framework: dict) -> dict:
        """Create narrative analysis for the criterion"""
        
        # Analyze story themes
        win_themes = [t for t in story_themes if t['story_direction']['direction'] == 'positive']
        loss_themes = [t for t in story_themes if t['story_direction']['direction'] == 'negative']
        neutral_themes = [t for t in story_themes if t['story_direction']['direction'] == 'neutral']
        
        # Create narrative summary
        narrative_summary = {
            'story_theme': framework['story_theme'],
            'win_narrative': self._create_win_narrative(win_themes, theme_evidence),
            'loss_narrative': self._create_loss_narrative(loss_themes, theme_evidence),
            'overall_story': self._create_overall_story(story_themes, theme_evidence),
            'theme_distribution': {
                'win_themes': len(win_themes),
                'loss_themes': len(loss_themes),
                'neutral_themes': len(neutral_themes),
                'total_themes': len(story_themes)
            }
        }
        
        return narrative_summary
    
    def _create_win_narrative(self, win_themes: list, theme_evidence: dict) -> str:
        """Create win narrative from positive themes"""
        
        if not win_themes:
            return "No clear winning themes identified in this area."
        
        # Get top win theme
        top_theme = win_themes[0]
        evidence = theme_evidence.get(top_theme['theme_id'], {})
        
        narrative = f"Rev demonstrates strength in {top_theme['title'].lower()}, "
        
        if evidence.get('quotes'):
            positive_quotes = [q for q in evidence['quotes'] if q['sentiment']['sentiment'] == 'positive']
            if positive_quotes:
                narrative += f"with customers expressing satisfaction about {positive_quotes[0]['quote'][:100]}... "
        
        if evidence.get('findings'):
            narrative += f"This is supported by {len(evidence['findings'])} findings showing positive impact. "
        
        return narrative
    
    def _create_loss_narrative(self, loss_themes: list, theme_evidence: dict) -> str:
        """Create loss narrative from negative themes"""
        
        if not loss_themes:
            return "No significant challenges identified in this area."
        
        # Get top loss theme
        top_theme = loss_themes[0]
        evidence = theme_evidence.get(top_theme['theme_id'], {})
        
        narrative = f"Rev faces challenges with {top_theme['title'].lower()}, "
        
        if evidence.get('quotes'):
            negative_quotes = [q for q in evidence['quotes'] if q['sentiment']['sentiment'] == 'negative']
            if negative_quotes:
                narrative += f"with customers expressing concerns about {negative_quotes[0]['quote'][:100]}... "
        
        if evidence.get('findings'):
            narrative += f"This is supported by {len(evidence['findings'])} findings showing negative impact. "
        
        return narrative
    
    def _create_overall_story(self, story_themes: list, theme_evidence: dict) -> str:
        """Create overall story for the criterion"""
        
        if not story_themes:
            return "Limited theme coverage in this area."
        
        # Calculate overall sentiment
        total_evidence = sum(len(evidence.get('quotes', [])) for evidence in theme_evidence.values())
        positive_evidence = sum(
            sum(1 for q in evidence.get('quotes', []) if q['sentiment']['sentiment'] == 'positive')
            for evidence in theme_evidence.values()
        )
        
        if total_evidence > 0:
            positive_ratio = positive_evidence / total_evidence
            if positive_ratio > 0.6:
                sentiment = "positive"
            elif positive_ratio < 0.4:
                sentiment = "negative"
            else:
                sentiment = "mixed"
        else:
            sentiment = "neutral"
        
        # Create story
        story = f"The overall narrative for this area is {sentiment}, "
        story += f"with {len(story_themes)} themes telling the story through {total_evidence} pieces of evidence. "
        
        if story_themes:
            top_theme = story_themes[0]
            story += f"The most prominent theme is '{top_theme['title']}' which {top_theme['story_direction']['direction']}ly impacts user experience."
        
        return story
    
    def _calculate_scorecard_metrics(self, story_themes: list, theme_evidence: dict, weight: float) -> dict:
        """Calculate scorecard metrics"""
        
        if not story_themes:
            return {
                'score': 5.0,
                'performance': 'neutral',
                'weight': weight,
                'weighted_score': 5.0 * weight,
                'evidence_coverage': 'none'
            }
        
        # Calculate theme scores
        theme_scores = []
        total_evidence = 0
        
        for theme in story_themes:
            evidence = theme_evidence.get(theme['theme_id'], {})
            evidence_summary = evidence.get('evidence_summary', {})
            
            # Base score from story direction
            base_score = theme['story_direction']['impact_score']
            
            # Adjust for evidence strength
            if evidence_summary.get('strength') == 'strong':
                evidence_multiplier = 1.2
            elif evidence_summary.get('strength') == 'moderate':
                evidence_multiplier = 1.0
            else:
                evidence_multiplier = 0.8
            
            theme_score = base_score * evidence_multiplier
            theme_scores.append(theme_score)
            
            total_evidence += evidence_summary.get('total_evidence', 0)
        
        # Calculate overall score
        overall_score = sum(theme_scores) / len(theme_scores) if theme_scores else 5.0
        
        # Determine performance level
        if overall_score >= 7.5:
            performance = 'excellent'
        elif overall_score >= 6.0:
            performance = 'good'
        elif overall_score >= 4.5:
            performance = 'fair'
        elif overall_score >= 3.0:
            performance = 'poor'
        else:
            performance = 'critical'
        
        # Determine evidence coverage
        if total_evidence >= 20:
            coverage = 'comprehensive'
        elif total_evidence >= 10:
            coverage = 'substantial'
        elif total_evidence >= 5:
            coverage = 'moderate'
        else:
            coverage = 'limited'
        
        return {
            'score': overall_score,
            'performance': performance,
            'weight': weight,
            'weighted_score': overall_score * weight,
            'evidence_coverage': coverage,
            'total_evidence': total_evidence,
            'theme_count': len(story_themes)
        }
    
    def print_theme_story_report(self, scorecard: dict):
        """Print theme-driven story report"""
        
        print("\n" + "="*80)
        print("🎯 REV THEME-STORY SCORECARD REPORT")
        print("Themes Tell the Story, Evidence Supports, Scorecard Anchors")
        print("="*80)
        
        # Executive Summary
        print(f"\n📋 EXECUTIVE SUMMARY")
        total_weighted_score = sum(data['scorecard_metrics']['weighted_score'] for data in scorecard.values())
        total_weight = sum(data['scorecard_metrics']['weight'] for data in scorecard.values())
        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
        
        print(f"   Overall Score: {overall_score:.1f}/10")
        print(f"   Performance Level: {self._get_performance_level(overall_score)}")
        
        print(f"\n   📊 SCORECARD FRAMEWORK:")
        for criterion, data in scorecard.items():
            metrics = data['scorecard_metrics']
            print(f"     • {data['framework']['title']} (Weight: {metrics['weight']*100:.0f}%)")
            print(f"       Score: {metrics['score']:.1f}/10, Performance: {metrics['performance']}")
            print(f"       Evidence: {metrics.get('total_evidence', 0)} items, Coverage: {metrics.get('evidence_coverage', 'none')}")
        
        # Theme-Driven Stories by Criterion
        print(f"\n🎯 THEME-DRIVEN STORIES BY CRITERION")
        for criterion, data in scorecard.items():
            print(f"\n   📋 {data['framework']['title']}")
            print(f"     Weight: {data['scorecard_metrics']['weight']*100:.0f}%")
            print(f"     Score: {data['scorecard_metrics']['score']:.1f}/10")
            print(f"     Performance: {data['scorecard_metrics']['performance']}")
            
            # Story Theme
            narrative = data['narrative_analysis']
            print(f"     🎭 Story Theme: {narrative['story_theme']}")
            
            # Win Narrative
            print(f"     🏆 Win Narrative: {narrative['win_narrative']}")
            
            # Loss Narrative
            print(f"     ❌ Loss Narrative: {narrative['loss_narrative']}")
            
            # Overall Story
            print(f"     📖 Overall Story: {narrative['overall_story']}")
            
            # Theme Distribution
            dist = narrative['theme_distribution']
            print(f"     📊 Theme Distribution: {dist['win_themes']} wins, {dist['loss_themes']} losses, {dist['neutral_themes']} neutral")
            
            # Key Themes with Evidence
            print(f"     🎯 Key Themes:")
            for theme in data['story_themes'][:3]:  # Top 3 themes
                evidence = data['theme_evidence'].get(theme['theme_id'], {})
                evidence_summary = evidence.get('evidence_summary', {})
                
                print(f"       • {theme['title']}")
                print(f"         Direction: {theme['story_direction']['direction']}")
                print(f"         Story Type: {theme['story_direction']['story_type']}")
                print(f"         Evidence: {evidence_summary.get('total_evidence', 0)} items")
                print(f"         Strength: {evidence_summary.get('strength', 'none')}")
                
                # Top supporting evidence
                if evidence.get('quotes'):
                    top_quote = evidence['quotes'][0]
                    print(f"         Key Quote: {top_quote['quote'][:100]}...")
                    print(f"           Source: {top_quote['company']} - {top_quote['interviewee']}")
                    print(f"           Sentiment: {top_quote['sentiment']['sentiment']}")
                
                if evidence.get('findings'):
                    top_finding = evidence['findings'][0]
                    print(f"         Key Finding: {top_finding['statement'][:100]}...")
                    print(f"           Source: {top_finding['company']} - {top_finding['interviewee']}")
        
        # Strategic Implications
        print(f"\n📈 STRATEGIC IMPLICATIONS")
        print(f"   🎯 Theme-Driven Insights:")
        
        for criterion, data in scorecard.items():
            narrative = data['narrative_analysis']
            metrics = data['scorecard_metrics']
            
            if metrics['performance'] in ['excellent', 'good']:
                print(f"     • {data['framework']['title']}: Strong theme support for positive performance")
            elif metrics['performance'] in ['poor', 'critical']:
                print(f"     • {data['framework']['title']}: Theme analysis reveals significant challenges")
            else:
                print(f"     • {data['framework']['title']}: Mixed theme signals suggest opportunity for improvement")
        
        print(f"\n🎯 THEME-STORY SCORECARD REPORT GENERATION COMPLETE")
        print("="*80)
    
    def _get_performance_level(self, score: float) -> str:
        """Get performance level description"""
        if score >= 7.5:
            return 'Excellent - Strong theme-driven competitive advantages'
        elif score >= 6.0:
            return 'Good - Theme-supported competitive positioning'
        elif score >= 4.5:
            return 'Fair - Mixed theme impact on competitive position'
        elif score >= 3.0:
            return 'Poor - Theme-identified competitive disadvantages'
        else:
            return 'Critical - Major theme-driven competitive vulnerabilities'
    
    def save_theme_story_report(self, scorecard: dict, filename: str = "REV_THEME_STORY_REPORT.txt"):
        """Save theme story report to file"""
        
        with open(filename, 'w') as f:
            f.write("🎯 REV THEME-STORY SCORECARD REPORT\n")
            f.write("Themes Tell the Story, Evidence Supports, Scorecard Anchors\n")
            f.write("="*80 + "\n\n")
            
            # Executive Summary
            total_weighted_score = sum(data['scorecard_metrics']['weighted_score'] for data in scorecard.values())
            total_weight = sum(data['scorecard_metrics']['weight'] for data in scorecard.values())
            overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
            
            f.write("📋 EXECUTIVE SUMMARY\n")
            f.write(f"   Overall Score: {overall_score:.1f}/10\n")
            f.write(f"   Performance Level: {self._get_performance_level(overall_score)}\n\n")
            
            f.write("   📊 SCORECARD FRAMEWORK:\n")
            for criterion, data in scorecard.items():
                metrics = data['scorecard_metrics']
                f.write(f"     • {data['framework']['title']} (Weight: {metrics['weight']*100:.0f}%)\n")
                f.write(f"       Score: {metrics['score']:.1f}/10, Performance: {metrics['performance']}\n")
                f.write(f"       Evidence: {metrics.get('total_evidence', 0)} items, Coverage: {metrics.get('evidence_coverage', 'none')}\n\n")
            
            # Theme-Driven Stories
            f.write("🎯 THEME-DRIVEN STORIES BY CRITERION\n")
            for criterion, data in scorecard.items():
                f.write(f"\n   📋 {data['framework']['title']}\n")
                f.write(f"     Weight: {data['scorecard_metrics']['weight']*100:.0f}%\n")
                f.write(f"     Score: {data['scorecard_metrics']['score']:.1f}/10\n")
                f.write(f"     Performance: {data['scorecard_metrics']['performance']}\n\n")
                
                # Story Theme
                narrative = data['narrative_analysis']
                f.write(f"     🎭 Story Theme: {narrative['story_theme']}\n")
                f.write(f"     🏆 Win Narrative: {narrative['win_narrative']}\n")
                f.write(f"     ❌ Loss Narrative: {narrative['loss_narrative']}\n")
                f.write(f"     📖 Overall Story: {narrative['overall_story']}\n\n")
                
                # Key Themes with Evidence
                f.write(f"     🎯 Key Themes:\n")
                for theme in data['story_themes'][:3]:
                    evidence = data['theme_evidence'].get(theme['theme_id'], {})
                    evidence_summary = evidence.get('evidence_summary', {})
                    
                    f.write(f"       • {theme['title']}\n")
                    f.write(f"         Direction: {theme['story_direction']['direction']}\n")
                    f.write(f"         Story Type: {theme['story_direction']['story_type']}\n")
                    f.write(f"         Evidence: {evidence_summary.get('total_evidence', 0)} items\n")
                    f.write(f"         Strength: {evidence_summary.get('strength', 'none')}\n")
                    
                    # Top supporting evidence
                    if evidence.get('quotes'):
                        top_quote = evidence['quotes'][0]
                        f.write(f"         Key Quote: {top_quote['quote']}\n")
                        f.write(f"           Source: {top_quote['company']} - {top_quote['interviewee']}\n")
                        f.write(f"           Sentiment: {top_quote['sentiment']['sentiment']}\n\n")
                    
                    if evidence.get('findings'):
                        top_finding = evidence['findings'][0]
                        f.write(f"         Key Finding: {top_finding['statement']}\n")
                        f.write(f"           Source: {top_finding['company']} - {top_finding['interviewee']}\n\n")
        
        print(f"📄 Theme story report saved to: {filename}")

def main():
    """Generate theme-driven story report for Rev"""
    
    generator = RevThemeStoryScorecard()
    scorecard = generator.generate_theme_story_report()
    generator.print_theme_story_report(scorecard)
    generator.save_theme_story_report(scorecard)
    
    return scorecard

if __name__ == "__main__":
    scorecard = main() 