#!/usr/bin/env python3
"""
Excel Win-Loss Report Exporter
Creates analyst-ready multi-tab Excel workbooks for theme curation workflow.
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import xlsxwriter
from collections import defaultdict
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExcelWinLossExporter:
    """
    Create comprehensive Excel workbooks for analyst curation workflow.
    
    Features:
    - Multiple tabs for different analysis phases
    - Pre-formatted cells for Include/Exclude decisions
    - Conditional formatting for priority themes
    - Summary dashboards for quick overview
    """
    
    def __init__(self):
        self.workbook = None
        self.formats = {}
        self.db = None
        self.client_id = None
        self.discussion_guide = None
        
    def export_analyst_workbook(self, themes_data: Dict[str, Any], output_path: str = None) -> str:
        """
        Export complete analyst curation workbook.
        
        Args:
            themes_data: Output from WinLossReportGenerator
            output_path: Optional custom output path
            
        Returns:
            Path to generated Excel file
        """
        if not themes_data.get("success"):
            raise ValueError(f"Invalid themes data: {themes_data.get('error')}")
        
        # Generate filename if not provided
        if not output_path:
            client_id = themes_data["metadata"]["client_id"]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"Win_Loss_Analyst_Workbook_{client_id}_{timestamp}.xlsx"
        
        logger.info(f"🗂️ Creating analyst workbook: {output_path}")
        
        # Initialize database connection
        from supabase_database import SupabaseDatabase
        self.db = SupabaseDatabase()
        self.client_id = themes_data["metadata"]["client_id"]
        
        # Create workbook and define formatting
        self.workbook = xlsxwriter.Workbook(output_path)
        self._define_formats()
        
        try:
            # Load discussion guide if available
            try:
                from discussion_guide_integration import DiscussionGuideIntegrator
                integrator = DiscussionGuideIntegrator()
                discussion_guide_data = integrator.parse_supio_discussion_guide('uploads/Supio_PRJ-00027 Discussion Guide v1.txt')
                self.discussion_guide = discussion_guide_data.get('questions', []) if discussion_guide_data else []
                logger.info(f"✅ Loaded discussion guide with {len(self.discussion_guide)} questions")
            except Exception as e:
                logger.warning(f"⚠️ Could not load discussion guide: {e}")
                self.discussion_guide = []
            
            # Tab 1: Executive Summary
            self._create_executive_summary_tab(themes_data)
            
            # Tab 2: Cross-Section Themes Reference
            self._create_cross_section_reference_tab(themes_data)
            
            # Tab 3: Win Drivers Section Validation
            self._create_win_drivers_validation_tab(themes_data)
            
            # Tab 3: Loss Factors Section Validation
            self._create_loss_factors_validation_tab(themes_data)
            
            # Tab 4: Competitive Intelligence Section Validation
            self._create_competitive_intelligence_validation_tab(themes_data)
            
            # Tab 5: Implementation Insights Section Validation
            self._create_implementation_insights_validation_tab(themes_data)
            
            # Tab 6: Section Planning Dashboard (Optional overview)
            self._create_section_planning_tab(themes_data)
            
            # Tab 7: Raw Data Reference
            self._create_raw_data_tab(themes_data)
            
            # Tab 6: Research Question Alignment Analysis
            if hasattr(self, 'discussion_guide') and self.discussion_guide:
                self._create_research_question_alignment_tab(themes_data)
            
            # Tab 7: Research Question Coverage Analysis
            if hasattr(self, 'discussion_guide') and self.discussion_guide:
                self._create_research_question_coverage_tab(themes_data)
            
            # Tab 8: Discussion Guide Coverage (if available)
            if hasattr(self, 'discussion_guide') and self.discussion_guide:
                self._create_discussion_guide_coverage_tab(themes_data)
            
            # Tab 9: Report Builder Template
            self._create_report_builder_tab(themes_data)
            
            self.workbook.close()
            
            logger.info(f"✅ Successfully created analyst workbook: {output_path}")
            return output_path
            
        except Exception as e:
            self.workbook.close()
            logger.error(f"❌ Error creating workbook: {e}")
            raise
    
    def _define_formats(self):
        """Define all cell formats used throughout the workbook"""
        self.formats = {
            'title': self.workbook.add_format({
                'bold': True, 'font_size': 16, 'bg_color': '#2F4F4F', 'font_color': 'white',
                'align': 'center', 'valign': 'vcenter'
            }),
            'header': self.workbook.add_format({
                'bold': True, 'font_size': 12, 'bg_color': '#4682B4', 'font_color': 'white',
                'align': 'center', 'valign': 'vcenter', 'text_wrap': True
            }),
            'subheader': self.workbook.add_format({
                'bold': True, 'font_size': 10, 'bg_color': '#B0C4DE', 
                'align': 'left', 'valign': 'vcenter'
            }),
            'strength': self.workbook.add_format({
                'bg_color': '#90EE90', 'font_color': '#006400', 'bold': True
            }),
            'weakness': self.workbook.add_format({
                'bg_color': '#FFB6C1', 'font_color': '#8B0000', 'bold': True
            }),
            'mixed_signal': self.workbook.add_format({
                'bg_color': '#FFD700', 'font_color': '#FF8C00', 'bold': True
            }),
            'high_priority': self.workbook.add_format({
                'bg_color': '#FF6347', 'font_color': 'white', 'bold': True
            }),
            'decision_cell': self.workbook.add_format({
                'bg_color': '#F0F8FF', 'align': 'center', 'border': 1
            }),
            'notes_cell': self.workbook.add_format({
                'bg_color': '#FFFACD', 'text_wrap': True, 'valign': 'top'
            }),
            'data_cell': self.workbook.add_format({
                'text_wrap': True, 'valign': 'top', 'border': 1
            }),
            'number': self.workbook.add_format({
                'num_format': '0.0', 'align': 'center'
            }),
            'percentage': self.workbook.add_format({
                'num_format': '0%', 'align': 'center'
            }),
            'validated': self.workbook.add_format({
                'bg_color': '#90EE90', 'font_color': '#006400', 'bold': True, 'align': 'center'
            })
        }
    
    def _create_executive_summary_tab(self, themes_data: Dict[str, Any]):
        """Create executive summary dashboard tab"""
        worksheet = self.workbook.add_worksheet('📊 Executive Summary')
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:F', 15)
        
        # Title
        worksheet.merge_range('A1:F1', f"Win-Loss Analysis Executive Summary - {themes_data['metadata']['client_id']}", self.formats['title'])
        
        # Metadata section
        row = 3
        worksheet.write(row, 0, "Analysis Overview", self.formats['subheader'])
        row += 1
        worksheet.write(row, 0, "Generated On:")
        worksheet.write(row, 1, themes_data['metadata']['generated_at'][:10])
        row += 1
        worksheet.write(row, 0, "Total Quotes Analyzed:")
        worksheet.write(row, 1, themes_data['metadata']['total_quotes'])
        row += 1
        worksheet.write(row, 0, "Companies Analyzed:")
        worksheet.write(row, 1, themes_data['metadata']['companies_analyzed'])
        row += 1
        worksheet.write(row, 0, "High-Quality Themes Generated:")
        worksheet.write(row, 1, themes_data['metadata']['total_themes'])
        
        # Themes summary
        row += 3
        worksheet.write(row, 0, "Theme Summary by Type", self.formats['subheader'])
        row += 1
        
        # Headers
        headers = ["Theme Type", "Count", "Avg Quality Score", "Total Quotes", "Key Insights"]
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1
        
        # Theme type summaries
        theme_summaries = self._summarize_themes_by_type(themes_data['themes'])
        for theme_type, summary in theme_summaries.items():
            theme_format = self.formats.get(theme_type, self.formats['data_cell'])
            worksheet.write(row, 0, theme_type.replace('_', ' ').title(), theme_format)
            worksheet.write(row, 1, summary['count'])
            worksheet.write(row, 2, summary['avg_quality_score'], self.formats['number'])
            worksheet.write(row, 3, summary['total_quotes'])
            worksheet.write(row, 4, summary['key_insight'], self.formats['data_cell'])
            row += 1
        
        # Discussion Guide Integration section
        row += 2
        worksheet.write(row, 0, "Discussion Guide Integration", self.formats['subheader'])
        row += 1
        
        # Check if discussion guide is available
        discussion_guide = getattr(self, 'discussion_guide', None)
        if discussion_guide and len(discussion_guide) > 0:
            worksheet.write(row, 0, "✅ Discussion Guide Connected:", self.formats['strength'])
            worksheet.write(row, 1, f"{len(discussion_guide)} research questions loaded")
            row += 1
            
            # Add research question coverage analysis
            coverage_analysis = self._analyze_theme_question_coverage(themes_data['themes'], discussion_guide)
            worksheet.write(row, 0, "📊 Research Question Coverage:", self.formats['data_cell'])
            worksheet.write(row, 1, f"{coverage_analysis['questions_with_coverage']}/{len(discussion_guide)} questions covered ({coverage_analysis['coverage_percentage']:.1f}%)")
            row += 1
            
            if coverage_analysis['uncovered_questions']:
                worksheet.write(row, 0, "⚠️ Coverage Gaps:", self.formats['data_cell'])
                worksheet.write(row, 1, f"{len(coverage_analysis['uncovered_questions'])} questions need additional analysis")
                row += 1
            
            worksheet.write(row, 0, "📋 Detailed Analysis:", self.formats['data_cell'])
            worksheet.write(row, 1, "See 'Research Question Coverage' tab for complete analysis")
            row += 1
        else:
            worksheet.write(row, 0, "⚠️ No Discussion Guide Connected", self.formats['weakness'])
            worksheet.write(row, 1, "Upload discussion guide for better research alignment")
            row += 1
        
        # Key recommendations section
        row += 2
        worksheet.write(row, 0, "Analyst Action Items", self.formats['subheader'])
        row += 1
        
        recommendations = [
            "1. Review section validation tabs - approve/reject themes for final report",
            "2. Classify quotes as FEATURED/PRIMARY/SUPPORTING/EXCLUDE in each section", 
            "3. Use Discussion Guide Coverage tab to ensure research alignment",
            "4. Build final report using Report Builder tab",
            "5. Cross-reference Raw Data for additional context when needed"
        ]
        
        for rec in recommendations:
            worksheet.write(row, 0, rec, self.formats['data_cell'])
            row += 1
    
    def _create_coverage_validation_tab(self, themes_data: Dict[str, Any]):
        """Phase 1: Discussion Guide Coverage - Map research questions to discovered themes"""
        worksheet = self.workbook.add_worksheet('Phase 1 - Coverage')
        
        # Set column widths
        worksheet.set_column('A:A', 50)  # Research Question
        worksheet.set_column('B:B', 40)  # Related Discovered Themes
        worksheet.set_column('C:C', 20)  # Coverage Assessment
        worksheet.set_column('D:D', 15)  # Theme Count
        worksheet.set_column('E:E', 15)  # Quote Count
        worksheet.set_column('F:F', 50)  # Coverage Notes
        worksheet.set_column('G:G', 20)  # Action Needed
        
        # Title and instructions
        worksheet.merge_range('A1:G1', "Phase 1: Discussion Guide Coverage Validation", self.formats['title'])
        worksheet.merge_range('A2:G2', "PURPOSE: Validate that discovered themes address your original research questions. Add your discussion guide questions below, then assess coverage.", self.formats['subheader'])
        
        # Headers
        headers = [
            "Original Research Question", "Related Discovered Themes", "Coverage Assessment",
            "Theme Count", "Quote Count", "Coverage Notes", "Action Needed"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, self.formats['header'])
        
        # Instructions for analyst to fill in research questions
        row = 4
        
        # Sample research questions with mapping to discovered themes
        sample_questions = self._generate_sample_research_questions(themes_data['themes'])
        
        for question_data in sample_questions:
            # Research Question
            worksheet.write(row, 0, question_data['question'], self.formats['data_cell'])
            
            # Related Themes (discovered)
            related_themes = "; ".join(question_data['related_themes'][:3])
            if len(question_data['related_themes']) > 3:
                related_themes += f" (+{len(question_data['related_themes']) - 3} more)"
            worksheet.write(row, 1, related_themes, self.formats['data_cell'])
            
            # Coverage Assessment dropdown
            worksheet.data_validation(row, 2, row, 2, {
                'validate': 'list',
                'source': ['STRONG - Well covered', 'ADEQUATE - Sufficient', 'WEAK - Limited coverage', 'MISSING - No themes found', 'REVIEW NEEDED']
            })
            worksheet.write(row, 2, question_data['coverage'], self.formats['decision_cell'])
            
            # Theme Count
            worksheet.write(row, 3, len(question_data['related_themes']), self.formats['number'])
            
            # Quote Count
            worksheet.write(row, 4, question_data['quote_count'], self.formats['number'])
            
            # Coverage Notes
            worksheet.write(row, 5, "", self.formats['notes_cell'])
            
            # Action Needed dropdown
            worksheet.data_validation(row, 6, row, 6, {
                'validate': 'list',
                'source': ['COMPLETE', 'FOLLOW UP NEEDED', 'SUPPLEMENTAL RESEARCH', 'REFRAME QUESTION']
            })
            worksheet.write(row, 6, "", self.formats['decision_cell'])
            
            row += 1
        
        # Add blank rows for additional research questions
        for i in range(5):
            worksheet.write(row, 0, "[ADD YOUR RESEARCH QUESTION HERE]", self.formats['notes_cell'])
            worksheet.data_validation(row, 2, row, 2, {
                'validate': 'list',
                'source': ['STRONG - Well covered', 'ADEQUATE - Sufficient', 'WEAK - Limited coverage', 'MISSING - No themes found', 'REVIEW NEEDED']
            })
            worksheet.data_validation(row, 6, row, 6, {
                'validate': 'list',
                'source': ['COMPLETE', 'FOLLOW UP NEEDED', 'SUPPLEMENTAL RESEARCH', 'REFRAME QUESTION']
            })
            row += 1
        
        # Add summary
        row += 2
        worksheet.write(row, 0, "COVERAGE SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, f"Total Discovered Themes: {len(themes_data['themes'])}")
        worksheet.write(row, 2, "Research Questions Covered: [TO BE DETERMINED]")
        worksheet.write(row, 4, "Coverage Confidence: [RATE 1-5]")

    def _generate_sample_research_questions(self, themes: List[Dict[str, Any]]) -> List[Dict]:
        """Generate sample research questions mapped to discovered themes"""
        # Group themes by subject for mapping
        themes_by_subject = {}
        for theme in themes:
            subject = theme.get('harmonized_subject', 'Unknown')
            if subject not in themes_by_subject:
                themes_by_subject[subject] = []
            themes_by_subject[subject].append(theme.get('theme_title', theme.get('theme_id', 'Unknown')))
        
        # Create sample questions based on common VOC research areas
        sample_questions = []
        
        # Map subjects to research questions
        subject_to_question = {
            'Product Capabilities': "What product features drive vendor selection decisions?",
            'Pricing and Commercial': "How do pricing models influence purchase decisions?", 
            'Implementation Process': "What implementation challenges affect vendor satisfaction?",
            'Sales Experience': "How does the sales process impact vendor perception?",
            'User Experience': "What usability factors influence user adoption?",
            'Competitive Dynamics': "How do vendors compare in the competitive landscape?",
            'Market Discovery': "What market needs are driving vendor evaluation?",
            'Support and Service': "How does ongoing support affect vendor relationships?",
            'Integration Technical': "What technical requirements drive integration decisions?",
            'Vendor Stability': "How important is vendor stability in selection decisions?"
        }
        
        for subject, question in subject_to_question.items():
            if subject in themes_by_subject:
                related_themes = themes_by_subject[subject]
                # Estimate coverage based on number of themes
                if len(related_themes) >= 3:
                    coverage = "STRONG - Well covered"
                elif len(related_themes) >= 2:
                    coverage = "ADEQUATE - Sufficient"
                else:
                    coverage = "WEAK - Limited coverage"
                
                sample_questions.append({
                    'question': question,
                    'related_themes': related_themes,
                    'coverage': coverage,
                    'quote_count': len(related_themes) * 8  # Rough estimate
                })
        
        return sample_questions[:8]  # Limit to top 8 questions

    def _create_win_drivers_validation_tab(self, themes_data: Dict[str, Any]):
        """Win Drivers Section Validation - Integrated theme and quote validation"""
        worksheet = self.workbook.add_worksheet('Win Drivers Section')
        
        # Set column widths for integrated validation
        worksheet.set_column('A:A', 15)  # Theme ID
        worksheet.set_column('B:B', 50)  # Theme Statement
        worksheet.set_column('C:C', 20)  # Report Section
        worksheet.set_column('D:D', 30)  # Research Question
        worksheet.set_column('E:E', 60)  # Quote Text
        worksheet.set_column('F:F', 15)  # Company
        worksheet.set_column('G:G', 15)  # Interviewee
        worksheet.set_column('H:H', 12)  # Sentiment
        worksheet.set_column('I:I', 12)  # Impact Score
        worksheet.set_column('J:J', 25)  # Research Alignment
        worksheet.set_column('K:K', 25)  # Quote Classification
        worksheet.set_column('L:L', 25)  # Theme Decision
        worksheet.set_column('M:M', 40)  # Analyst Notes
        
        # Title and instructions
        worksheet.merge_range('A1:M1', "Win Drivers Section Validation", self.formats['title'])
        worksheet.merge_range('A2:M2', "PURPOSE: Validate themes and quotes for the 'Why You Win' section. See how each theme contributes to the win story.", self.formats['subheader'])
        
        # Section context
        worksheet.merge_range('A3:M3', "📖 SECTION CONTEXT: This section explains why customers choose your solution over competitors. Focus on strengths, capabilities, and positive differentiators.", self.formats['data_cell'])
        
        # Research question context
        worksheet.merge_range('A4:M4', "🔍 RESEARCH FOCUS: 'What product features and capabilities drive vendor selection decisions?' 'What do customers value most about our solution?'", self.formats['data_cell'])
        
        # Headers
        headers = [
            "Theme ID", "Theme Statement", "Report Section", "Research Question", 
            "Quote Text", "Company", "Interviewee", "Sentiment", "Impact Score", "Research Alignment", "Quote Classification", "Theme Decision", "Analyst Notes"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(5, col, header, self.formats['header'])
        
        # Process win driver themes - one quote per row
        row = 6
        win_themes = self._filter_themes_by_section(themes_data['themes'], 'win')
        
        # Get cross-section map to avoid duplication
        cross_section_map = self._identify_cross_section_themes(themes_data['themes'])
        
        # Filter to only include themes where this is their primary section OR they're not cross-section
        primary_win_themes = []
        for theme in win_themes:
            theme_id = theme.get('theme_id', 'unknown')
            primary_section = self._get_primary_section_for_theme(theme, cross_section_map)
            
            if primary_section == 'win' or theme_id not in cross_section_map:
                primary_win_themes.append(theme)
        
        for theme in primary_win_themes:
            all_quotes = theme.get('all_quotes', [])
            theme_id = theme.get('theme_id', 'unknown')
            
            # Check if this is a cross-section theme
            is_cross_section = theme_id in cross_section_map
            cross_sections = cross_section_map.get(theme_id, [])
            
            # Write theme info for first quote only
            first_quote = True
            
            for quote in all_quotes:
                # Theme ID (only show for first quote of each theme)
                if first_quote:
                    worksheet.write(row, 0, theme['theme_id'], self.formats['data_cell'])
                    
                    # Add cross-reference info to theme statement if it's a cross-section theme
                    theme_statement = theme.get('theme_statement', 'No statement generated')
                    if is_cross_section:
                        other_sections = [s for s in cross_sections if s != 'win']
                        theme_statement += f" [CROSS-SECTION: Also appears in {', '.join(other_sections).title()}]"
                    
                    worksheet.write(row, 1, theme_statement, self.formats['data_cell'])
                    worksheet.write(row, 2, "Win Drivers", self.formats['data_cell'])
                    worksheet.write(row, 3, self._map_theme_to_research_question(theme), self.formats['data_cell'])
                    first_quote = False
                else:
                    # Leave theme info blank for subsequent quotes
                    worksheet.write(row, 0, "", self.formats['data_cell'])
                    worksheet.write(row, 1, "", self.formats['data_cell'])
                    worksheet.write(row, 2, "", self.formats['data_cell'])
                    worksheet.write(row, 3, "", self.formats['data_cell'])
                
                # Individual quote data
                worksheet.write(row, 4, quote.get('verbatim_response', 'No quote text'), self.formats['data_cell'])
                worksheet.write(row, 5, quote.get('company', quote.get('company_name', 'Unknown')), self.formats['data_cell'])
                worksheet.write(row, 6, quote.get('interviewee_name', 'Unknown'), self.formats['data_cell'])
                worksheet.write(row, 7, quote.get('sentiment', 'unknown').title(), self.formats['data_cell'])
                worksheet.write(row, 8, quote.get('impact_score', 0), self.formats['number'])
                
                # Research Alignment
                research_alignment = self._get_quote_research_alignment(quote)
                worksheet.write(row, 9, research_alignment, self.formats['data_cell'])
                
                # Quote Classification dropdown
                worksheet.data_validation(row, 10, row, 10, {
                    'validate': 'list',
                    'source': ['FEATURED - Executive summary', 'PRIMARY - Main evidence', 'SUPPORTING - Background', 'EXCLUDE - Do not use']
                })
                worksheet.write(row, 10, "", self.formats['decision_cell'])
                
                # Analyst Notes
                worksheet.write(row, 12, "", self.formats['notes_cell'])
                
                row += 1
            
            # Add Theme Decision Row after all quotes for this theme
            worksheet.write(row, 0, f"THEME DECISION: {theme['theme_id']}", self.formats['header'])
            worksheet.write(row, 1, "After reviewing all quotes above, make theme decision:", self.formats['subheader'])
            
            # Theme Decision dropdown
            worksheet.data_validation(row, 11, row, 11, {
                'validate': 'list',
                'source': ['VALIDATED - Use in report', 'REJECTED - Insufficient evidence', 'REVISED - Needs statement changes', 'MERGE - Combine with other theme']
            })
            worksheet.write(row, 11, "", self.formats['decision_cell'])
            
            # Theme-level analyst notes
            worksheet.write(row, 12, "", self.formats['notes_cell'])
            
            row += 1
            
            # Add a blank row between themes for visual separation
            row += 1
        
        # Add section summary
        row += 2
        worksheet.write(row, 0, "WIN DRIVERS SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, f"Total Win Themes: {len(win_themes)}")
        worksheet.write(row, 3, "Validated Themes: [Count after review]")
        worksheet.write(row, 6, "Featured Quotes: [Count]")

    def _create_loss_factors_validation_tab(self, themes_data: Dict[str, Any]):
        """Loss Factors Section Validation - Integrated theme and quote validation"""
        worksheet = self.workbook.add_worksheet('Loss Factors Section')
        
        # Set column widths for integrated validation
        worksheet.set_column('A:A', 15)  # Theme ID
        worksheet.set_column('B:B', 50)  # Theme Statement
        worksheet.set_column('C:C', 20)  # Report Section
        worksheet.set_column('D:D', 30)  # Research Question
        worksheet.set_column('E:E', 60)  # Quote Text
        worksheet.set_column('F:F', 15)  # Company
        worksheet.set_column('G:G', 15)  # Interviewee
        worksheet.set_column('H:H', 12)  # Sentiment
        worksheet.set_column('I:I', 12)  # Impact Score
        worksheet.set_column('J:J', 25)  # Research Alignment
        worksheet.set_column('K:K', 25)  # Quote Classification
        worksheet.set_column('L:L', 25)  # Theme Decision
        worksheet.set_column('M:M', 40)  # Analyst Notes
        
        # Title and instructions
        worksheet.merge_range('A1:M1', "Loss Factors Section Validation", self.formats['title'])
        worksheet.merge_range('A2:M2', "PURPOSE: Validate themes and quotes for the 'Why You Lose' section. Identify areas for improvement and competitive gaps.", self.formats['subheader'])
        
        # Section context
        worksheet.merge_range('A3:M3', "📖 SECTION CONTEXT: This section explains why customers choose competitors or don't select your solution. Focus on weaknesses, gaps, and areas for improvement.", self.formats['data_cell'])
        
        # Research question context
        worksheet.merge_range('A4:M4', "🔍 RESEARCH FOCUS: 'What factors lead to lost deals?' 'What do customers see as our weaknesses?' 'What competitive advantages do others have?'", self.formats['data_cell'])
        
        # Headers
        headers = [
            "Theme ID", "Theme Statement", "Report Section", "Research Question", 
            "Quote Text", "Company", "Interviewee", "Sentiment", "Impact Score", "Research Alignment", "Quote Classification", "Theme Decision", "Analyst Notes"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(5, col, header, self.formats['header'])
        
        # Process loss factor themes - one quote per row
        row = 6
        loss_themes = self._filter_themes_by_section(themes_data['themes'], 'loss')
        
        # Get cross-section map to avoid duplication
        cross_section_map = self._identify_cross_section_themes(themes_data['themes'])
        
        # Filter to only include themes where this is their primary section OR they're not cross-section
        primary_loss_themes = []
        for theme in loss_themes:
            theme_id = theme.get('theme_id', 'unknown')
            primary_section = self._get_primary_section_for_theme(theme, cross_section_map)
            
            if primary_section == 'loss' or theme_id not in cross_section_map:
                primary_loss_themes.append(theme)
        
        for theme in primary_loss_themes:
            all_quotes = theme.get('all_quotes', [])
            theme_id = theme.get('theme_id', 'unknown')
            
            # Check if this is a cross-section theme
            is_cross_section = theme_id in cross_section_map
            cross_sections = cross_section_map.get(theme_id, [])
            
            # Write theme info for first quote only
            first_quote = True
            
            for quote in all_quotes:
                # Theme ID (only show for first quote of each theme)
                if first_quote:
                    worksheet.write(row, 0, theme['theme_id'], self.formats['data_cell'])
                    
                    # Add cross-reference info to theme statement if it's a cross-section theme
                    theme_statement = theme.get('theme_statement', 'No statement generated')
                    if is_cross_section:
                        other_sections = [s for s in cross_sections if s != 'loss']
                        theme_statement += f" [CROSS-SECTION: Also appears in {', '.join(other_sections).title()}]"
                    
                    worksheet.write(row, 1, theme_statement, self.formats['data_cell'])
                    worksheet.write(row, 2, "Loss Factors", self.formats['data_cell'])
                    worksheet.write(row, 3, self._map_theme_to_research_question(theme), self.formats['data_cell'])
                    first_quote = False
                else:
                    # Leave theme info blank for subsequent quotes
                    worksheet.write(row, 0, "", self.formats['data_cell'])
                    worksheet.write(row, 1, "", self.formats['data_cell'])
                    worksheet.write(row, 2, "", self.formats['data_cell'])
                    worksheet.write(row, 3, "", self.formats['data_cell'])
                
                # Individual quote data
                worksheet.write(row, 4, quote.get('verbatim_response', 'No quote text'), self.formats['data_cell'])
                worksheet.write(row, 5, quote.get('company', quote.get('company_name', 'Unknown')), self.formats['data_cell'])
                worksheet.write(row, 6, quote.get('interviewee_name', 'Unknown'), self.formats['data_cell'])
                worksheet.write(row, 7, quote.get('sentiment', 'unknown').title(), self.formats['data_cell'])
                worksheet.write(row, 8, quote.get('impact_score', 0), self.formats['number'])
                
                # Research Alignment
                research_alignment = self._get_quote_research_alignment(quote)
                worksheet.write(row, 9, research_alignment, self.formats['data_cell'])
                
                # Quote Classification dropdown
                worksheet.data_validation(row, 10, row, 10, {
                    'validate': 'list',
                    'source': ['FEATURED - Executive summary', 'PRIMARY - Main evidence', 'SUPPORTING - Background', 'EXCLUDE - Do not use']
                })
                worksheet.write(row, 10, "", self.formats['decision_cell'])
                
                # Analyst Notes
                worksheet.write(row, 12, "", self.formats['notes_cell'])
                
                row += 1
            
            # Add Theme Decision Row after all quotes for this theme
            worksheet.write(row, 0, f"THEME DECISION: {theme['theme_id']}", self.formats['header'])
            worksheet.write(row, 1, "After reviewing all quotes above, make theme decision:", self.formats['subheader'])
            
            # Theme Decision dropdown
            worksheet.data_validation(row, 11, row, 11, {
                'validate': 'list',
                'source': ['VALIDATED - Use in report', 'REJECTED - Insufficient evidence', 'REVISED - Needs statement changes', 'MERGE - Combine with other theme']
            })
            worksheet.write(row, 11, "", self.formats['decision_cell'])
            
            # Theme-level analyst notes
            worksheet.write(row, 12, "", self.formats['notes_cell'])
            
            row += 1
            
            # Add a blank row between themes for visual separation
            row += 1
        
        # Add section summary
        row += 2
        worksheet.write(row, 0, "LOSS FACTORS SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, f"Total Loss Themes: {len(loss_themes)}")
        worksheet.write(row, 3, "Validated Themes: [Count after review]")
        worksheet.write(row, 6, "Featured Quotes: [Count]")

    def _create_competitive_intelligence_validation_tab(self, themes_data: Dict[str, Any]):
        """Competitive Intelligence Section Validation - Integrated theme and quote validation"""
        worksheet = self.workbook.add_worksheet('Competitive Intelligence')
        
        # Set column widths for integrated validation
        worksheet.set_column('A:A', 15)  # Theme ID
        worksheet.set_column('B:B', 50)  # Theme Statement
        worksheet.set_column('C:C', 20)  # Report Section
        worksheet.set_column('D:D', 30)  # Research Question
        worksheet.set_column('E:E', 60)  # Quote Text
        worksheet.set_column('F:F', 15)  # Company
        worksheet.set_column('G:G', 15)  # Interviewee
        worksheet.set_column('H:H', 12)  # Sentiment
        worksheet.set_column('I:I', 12)  # Impact Score
        worksheet.set_column('J:J', 25)  # Quote Classification
        worksheet.set_column('K:K', 25)  # Theme Decision
        worksheet.set_column('L:L', 40)  # Analyst Notes
        
        # Title and instructions
        worksheet.merge_range('A1:L1', "Competitive Intelligence Section Validation", self.formats['title'])
        worksheet.merge_range('A2:L2', "PURPOSE: Validate themes and quotes for competitive analysis. Understand how customers view competitors vs. your solution.", self.formats['subheader'])
        
        # Section context
        worksheet.merge_range('A3:L3', "📖 SECTION CONTEXT: This section provides insights into competitive positioning, market dynamics, and how customers compare solutions.", self.formats['data_cell'])
        
        # Research question context
        worksheet.merge_range('A4:L4', "🔍 RESEARCH FOCUS: 'How do customers compare vendors?' 'What competitive advantages do others have?' 'What market dynamics affect decisions?'", self.formats['data_cell'])
        
        # Headers
        headers = [
            "Theme ID", "Theme Statement", "Report Section", "Research Question", 
            "Quote Text", "Company", "Interviewee", "Sentiment", "Impact Score", "Quote Classification", "Theme Decision", "Analyst Notes"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(5, col, header, self.formats['header'])
        
        # Process competitive themes - one quote per row
        row = 6
        competitive_themes = self._filter_themes_by_section(themes_data['themes'], 'competitive')
        
        # Get cross-section map to avoid duplication
        cross_section_map = self._identify_cross_section_themes(themes_data['themes'])
        
        # Filter to only include themes where this is their primary section OR they're not cross-section
        primary_competitive_themes = []
        for theme in competitive_themes:
            theme_id = theme.get('theme_id', 'unknown')
            primary_section = self._get_primary_section_for_theme(theme, cross_section_map)
            
            if primary_section == 'competitive' or theme_id not in cross_section_map:
                primary_competitive_themes.append(theme)
        
        for theme in primary_competitive_themes:
            all_quotes = theme.get('all_quotes', [])
            theme_id = theme.get('theme_id', 'unknown')
            
            # Check if this is a cross-section theme
            is_cross_section = theme_id in cross_section_map
            cross_sections = cross_section_map.get(theme_id, [])
            
            # Write theme info for first quote only
            first_quote = True
            
            for quote in all_quotes:
                # Theme ID (only show for first quote of each theme)
                if first_quote:
                    worksheet.write(row, 0, theme['theme_id'], self.formats['data_cell'])
                    
                    # Add cross-reference info to theme statement if it's a cross-section theme
                    theme_statement = theme.get('theme_statement', 'No statement generated')
                    if is_cross_section:
                        other_sections = [s for s in cross_sections if s != 'competitive']
                        theme_statement += f" [CROSS-SECTION: Also appears in {', '.join(other_sections).title()}]"
                    
                    worksheet.write(row, 1, theme_statement, self.formats['data_cell'])
                    worksheet.write(row, 2, "Competitive Intelligence", self.formats['data_cell'])
                    worksheet.write(row, 3, self._map_theme_to_research_question(theme), self.formats['data_cell'])
                    first_quote = False
                else:
                    # Leave theme info blank for subsequent quotes
                    worksheet.write(row, 0, "", self.formats['data_cell'])
                    worksheet.write(row, 1, "", self.formats['data_cell'])
                    worksheet.write(row, 2, "", self.formats['data_cell'])
                    worksheet.write(row, 3, "", self.formats['data_cell'])
                
                # Individual quote data
                worksheet.write(row, 4, quote.get('verbatim_response', 'No quote text'), self.formats['data_cell'])
                worksheet.write(row, 5, quote.get('company', quote.get('company_name', 'Unknown')), self.formats['data_cell'])
                worksheet.write(row, 6, quote.get('interviewee_name', 'Unknown'), self.formats['data_cell'])
                worksheet.write(row, 7, quote.get('sentiment', 'unknown').title(), self.formats['data_cell'])
                worksheet.write(row, 8, quote.get('impact_score', 0), self.formats['number'])
                
                # Quote Classification dropdown
                worksheet.data_validation(row, 9, row, 9, {
                    'validate': 'list',
                    'source': ['FEATURED - Key competitive insight', 'PRIMARY - Main competitive evidence', 'SUPPORTING - Background competitive context', 'EXCLUDE - Do not use']
                })
                worksheet.write(row, 9, "", self.formats['decision_cell'])
                
                # Theme Decision (only for first quote of each theme)
                if first_quote or row == 6:  # First quote of first theme
                    worksheet.data_validation(row, 10, row, 10, {
                        'validate': 'list',
                        'source': ['VALIDATED - Use in report', 'REJECTED - Insufficient evidence', 'REVISED - Needs statement changes', 'MERGE - Combine with other theme']
                    })
                    worksheet.write(row, 10, "", self.formats['decision_cell'])
                else:
                    worksheet.write(row, 10, "", self.formats['data_cell'])
                
                # Analyst Notes
                worksheet.write(row, 11, "", self.formats['notes_cell'])
                
                row += 1
            
            # Add a blank row between themes for visual separation
            row += 1
        
        # Add section summary
        row += 2
        worksheet.write(row, 0, "COMPETITIVE INTELLIGENCE SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, f"Total Competitive Themes: {len(competitive_themes)}")
        worksheet.write(row, 3, "Validated Themes: [Count after review]")
        worksheet.write(row, 6, "Featured Quotes: [Count]")

    def _create_implementation_insights_validation_tab(self, themes_data: Dict[str, Any]):
        """Implementation Insights Section Validation - Integrated theme and quote validation"""
        worksheet = self.workbook.add_worksheet('Implementation Insights')
        
        # Set column widths for integrated validation
        worksheet.set_column('A:A', 15)  # Theme ID
        worksheet.set_column('B:B', 50)  # Theme Statement
        worksheet.set_column('C:C', 20)  # Report Section
        worksheet.set_column('D:D', 30)  # Research Question
        worksheet.set_column('E:E', 60)  # Quote Text
        worksheet.set_column('F:F', 15)  # Company
        worksheet.set_column('G:G', 15)  # Interviewee
        worksheet.set_column('H:H', 12)  # Sentiment
        worksheet.set_column('I:I', 12)  # Impact Score
        worksheet.set_column('J:J', 25)  # Quote Classification
        worksheet.set_column('K:K', 25)  # Theme Decision
        worksheet.set_column('L:L', 40)  # Analyst Notes
        
        # Title and instructions
        worksheet.merge_range('A1:L1', "Implementation Insights Section Validation", self.formats['title'])
        worksheet.merge_range('A2:L2', "PURPOSE: Validate themes and quotes for implementation insights. Understand deployment challenges and success factors.", self.formats['subheader'])
        
        # Section context
        worksheet.merge_range('A3:L3', "📖 SECTION CONTEXT: This section covers implementation experiences, deployment challenges, and factors that affect successful adoption.", self.formats['data_cell'])
        
        # Research question context
        worksheet.merge_range('A4:L4', "🔍 RESEARCH FOCUS: 'What implementation challenges do customers face?' 'What factors drive successful deployment?' 'How does implementation affect satisfaction?'", self.formats['data_cell'])
        
        # Headers
        headers = [
            "Theme ID", "Theme Statement", "Report Section", "Research Question", 
            "Quote Text", "Company", "Interviewee", "Sentiment", "Impact Score", "Quote Classification", "Theme Decision", "Analyst Notes"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(5, col, header, self.formats['header'])
        
        # Process implementation themes - one quote per row
        row = 6
        implementation_themes = self._filter_themes_by_section(themes_data['themes'], 'implementation')
        
        # Get cross-section map to avoid duplication
        cross_section_map = self._identify_cross_section_themes(themes_data['themes'])
        
        # Filter to only include themes where this is their primary section OR they're not cross-section
        primary_implementation_themes = []
        for theme in implementation_themes:
            theme_id = theme.get('theme_id', 'unknown')
            primary_section = self._get_primary_section_for_theme(theme, cross_section_map)
            
            if primary_section == 'implementation' or theme_id not in cross_section_map:
                primary_implementation_themes.append(theme)
        
        for theme in primary_implementation_themes:
            all_quotes = theme.get('all_quotes', [])
            theme_id = theme.get('theme_id', 'unknown')
            
            # Check if this is a cross-section theme
            is_cross_section = theme_id in cross_section_map
            cross_sections = cross_section_map.get(theme_id, [])
            
            # Write theme info for first quote only
            first_quote = True
            
            for quote in all_quotes:
                # Theme ID (only show for first quote of each theme)
                if first_quote:
                    worksheet.write(row, 0, theme['theme_id'], self.formats['data_cell'])
                    
                    # Add cross-reference info to theme statement if it's a cross-section theme
                    theme_statement = theme.get('theme_statement', 'No statement generated')
                    if is_cross_section:
                        other_sections = [s for s in cross_sections if s != 'implementation']
                        theme_statement += f" [CROSS-SECTION: Also appears in {', '.join(other_sections).title()}]"
                    
                    worksheet.write(row, 1, theme_statement, self.formats['data_cell'])
                    worksheet.write(row, 2, "Implementation Insights", self.formats['data_cell'])
                    worksheet.write(row, 3, self._map_theme_to_research_question(theme), self.formats['data_cell'])
                    first_quote = False
                else:
                    # Leave theme info blank for subsequent quotes
                    worksheet.write(row, 0, "", self.formats['data_cell'])
                    worksheet.write(row, 1, "", self.formats['data_cell'])
                    worksheet.write(row, 2, "", self.formats['data_cell'])
                    worksheet.write(row, 3, "", self.formats['data_cell'])
                
                # Individual quote data
                worksheet.write(row, 4, quote.get('verbatim_response', 'No quote text'), self.formats['data_cell'])
                worksheet.write(row, 5, quote.get('company', quote.get('company_name', 'Unknown')), self.formats['data_cell'])
                worksheet.write(row, 6, quote.get('interviewee_name', 'Unknown'), self.formats['data_cell'])
                worksheet.write(row, 7, quote.get('sentiment', 'unknown').title(), self.formats['data_cell'])
                worksheet.write(row, 8, quote.get('impact_score', 0), self.formats['number'])
                
                # Quote Classification dropdown
                worksheet.data_validation(row, 9, row, 9, {
                    'validate': 'list',
                    'source': ['FEATURED - Key implementation insight', 'PRIMARY - Main implementation evidence', 'SUPPORTING - Background implementation context', 'EXCLUDE - Do not use']
                })
                worksheet.write(row, 9, "", self.formats['decision_cell'])
                
                # Theme Decision (only for first quote of each theme)
                if first_quote or row == 6:  # First quote of first theme
                    worksheet.data_validation(row, 10, row, 10, {
                        'validate': 'list',
                        'source': ['VALIDATED - Use in report', 'REJECTED - Insufficient evidence', 'REVISED - Needs statement changes', 'MERGE - Combine with other theme']
                    })
                    worksheet.write(row, 10, "", self.formats['decision_cell'])
                else:
                    worksheet.write(row, 10, "", self.formats['data_cell'])
                
                # Analyst Notes
                worksheet.write(row, 11, "", self.formats['notes_cell'])
                
                row += 1
            
            # Add a blank row between themes for visual separation
            row += 1
        
        # Add section summary
        row += 2
        worksheet.write(row, 0, "IMPLEMENTATION INSIGHTS SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, f"Total Implementation Themes: {len(implementation_themes)}")
        worksheet.write(row, 3, "Validated Themes: [Count after review]")
        worksheet.write(row, 6, "Featured Quotes: [Count]")

    def _filter_themes_by_section(self, themes: List[Dict[str, Any]], section_type: str) -> List[Dict[str, Any]]:
        """Filter themes by report section type"""
        filtered_themes = []
        
        for theme in themes:
            theme_type = theme.get('theme_type', '').lower()
            subject = theme.get('harmonized_subject', '').lower()
            theme_statement = theme.get('theme_statement', '').lower()
            all_quotes = theme.get('all_quotes', [])
            
            if section_type == 'win':
                # Win drivers: strength themes, positive sentiment, high impact
                is_strength = theme_type == 'strength'
                is_positive_subject = subject in ['product capabilities', 'user experience', 'sales experience']
                has_positive_quotes = any(q.get('sentiment', '').lower() in ['positive', 'mixed'] for q in all_quotes)
                
                if is_strength or (is_positive_subject and has_positive_quotes):
                    filtered_themes.append(theme)
                    
            elif section_type == 'loss':
                # Loss factors: weakness themes, negative sentiment, competitive gaps
                is_weakness = theme_type == 'weakness'
                is_negative_subject = subject in ['pricing and commercial', 'competitive dynamics']
                has_negative_quotes = any(q.get('sentiment', '').lower() in ['negative', 'mixed'] for q in all_quotes)
                
                if is_weakness or (is_negative_subject and has_negative_quotes):
                    filtered_themes.append(theme)
                    
            elif section_type == 'competitive':
                # Competitive intelligence: competitive themes, market dynamics
                is_competitive_subject = subject in ['competitive dynamics', 'market discovery']
                has_competitive_keyword = 'competitive' in theme_statement
                
                if is_competitive_subject or has_competitive_keyword:
                    filtered_themes.append(theme)
                    
            elif section_type == 'implementation':
                # Implementation insights: implementation, integration, technical themes
                is_implementation_subject = subject in ['implementation process', 'integration technical', 'support and service']
                has_implementation_keyword = 'implementation' in theme_statement or 'integration' in theme_statement
                
                if is_implementation_subject or has_implementation_keyword:
                    filtered_themes.append(theme)
        
        return filtered_themes

    def _map_theme_to_research_question(self, theme: Dict[str, Any]) -> str:
        """Map theme to specific research question using actual alignment data"""
        # Check if theme has research alignment data
        research_alignment = theme.get('research_alignment', {})
        if research_alignment and research_alignment.get('primary_question'):
            return research_alignment['primary_question']
        
        # Fallback to discussion guide if no alignment data
        discussion_guide = getattr(self, 'discussion_guide', None)
        if discussion_guide and len(discussion_guide) > 0:
            questions = discussion_guide
            
            # Use LLM or keyword matching to find the most relevant question
            subject = theme.get('harmonized_subject', '').lower()
            theme_statement = theme.get('theme_statement', '').lower()
            
            # Simple keyword matching to find relevant question
            for question in questions:
                question_lower = question.lower()
                # Check if theme subject or statement contains keywords from question
                if any(word in subject or word in theme_statement 
                      for word in question_lower.split()[:5]):
                    return question
            
            # If no match found, return the first question as default
            return questions[0] if questions else "Research question not specified"
        
        # Final fallback to hardcoded questions
        subject = theme.get('harmonized_subject', '').lower()
        theme_type = theme.get('theme_type', '').lower()
        
        # Map to specific research questions
        if 'product' in subject or 'capabilities' in subject:
            return "What product features drive vendor selection decisions?"
        elif 'pricing' in subject or 'commercial' in subject:
            return "How do pricing models influence purchase decisions?"
        elif 'implementation' in subject:
            return "What implementation challenges affect vendor satisfaction?"
        elif 'sales' in subject:
            return "How does the sales process impact vendor perception?"
        elif 'competitive' in subject:
            return "How do vendors compare in the competitive landscape?"
        elif 'user' in subject or 'experience' in subject:
            return "What usability factors influence user adoption?"
        elif 'market' in subject:
            return "What market needs are driving vendor evaluation?"
        elif 'support' in subject or 'service' in subject:
            return "How does ongoing support affect vendor relationships?"
        elif 'integration' in subject or 'technical' in subject:
            return "What technical requirements drive integration decisions?"
        else:
            return "What factors influence vendor selection and satisfaction?"

    def _create_evidence_validation_tab(self, themes_data: Dict[str, Any]):
        """Phase 2: Evidence-First Theme Validation - Show theme with ALL evidence for validation"""
        worksheet = self.workbook.add_worksheet('Phase 2 - Theme Validation')
        
        # Set column widths for evidence validation
        worksheet.set_column('A:A', 12)  # Theme ID
        worksheet.set_column('B:B', 50)  # Auto-Generated Theme Statement
        worksheet.set_column('C:C', 80)  # ALL Supporting Evidence
        worksheet.set_column('D:D', 20)  # Evidence Strength
        worksheet.set_column('E:E', 20)  # Statement Accuracy
        worksheet.set_column('F:F', 50)  # Analyst-Revised Statement
        worksheet.set_column('G:G', 20)  # Theme Status
        worksheet.set_column('H:H', 30)  # Research Connection
        worksheet.set_column('I:I', 40)  # Validation Notes
        
        # Title and instructions
        worksheet.merge_range('A1:I1', "Phase 2: Evidence-First Theme Validation", self.formats['title'])
        worksheet.merge_range('A2:I2', "PURPOSE: For each discovered theme, review ALL evidence to determine if it's real and accurately stated. Only validated themes advance to quote curation.", self.formats['subheader'])
        
        # Headers
        headers = [
            "Theme ID", "Auto-Generated Theme Statement", "ALL Supporting Evidence", "Evidence Strength",
            "Statement Accuracy", "Analyst-Revised Statement", "Theme Status", "Research Connection", "Validation Notes"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, self.formats['header'])
        
        # Process each theme for validation
        row = 4
        for theme in themes_data['themes']:
            all_quotes = theme.get('all_quotes', [])
            
            # Theme ID
            worksheet.write(row, 0, theme['theme_id'], self.formats['data_cell'])
            
            # Auto-Generated Theme Statement
            theme_statement = theme.get('theme_statement', 'No statement generated')
            worksheet.write(row, 1, theme_statement, self.formats['data_cell'])
            
            # ALL Supporting Evidence - comprehensive view
            evidence_text = self._create_comprehensive_evidence_view(theme, all_quotes)
            worksheet.write(row, 2, evidence_text, self.formats['data_cell'])
            
            # Evidence Strength Assessment
            worksheet.data_validation(row, 3, row, 3, {
                'validate': 'list',
                'source': ['SUFFICIENT - Strong evidence', 'MODERATE - Some gaps', 'INSUFFICIENT - Weak evidence', 'CONTRADICTORY - Mixed signals']
            })
            worksheet.write(row, 3, "", self.formats['decision_cell'])
            
            # Statement Accuracy Assessment
            worksheet.data_validation(row, 4, row, 4, {
                'validate': 'list',
                'source': ['ACCURATE - Reflects evidence', 'NEEDS REVISION - Close but off', 'INACCURATE - Does not match', 'TOO BROAD - Overstated', 'TOO NARROW - Understated']
            })
            worksheet.write(row, 4, "", self.formats['decision_cell'])
            
            # Analyst-Revised Statement
            worksheet.write(row, 5, "", self.formats['notes_cell'])
            
            # Theme Status (Final Decision)
            worksheet.data_validation(row, 6, row, 6, {
                'validate': 'list',
                'source': ['VALIDATED - Advance to curation', 'REJECTED - Insufficient evidence', 'MERGED - Combine with other theme', 'PENDING - Needs more review']
            })
            worksheet.write(row, 6, "", self.formats['decision_cell'])
            
            # Research Connection
            research_connection = self._map_theme_to_research_area(theme)
            worksheet.write(row, 7, research_connection, self.formats['data_cell'])
            
            # Validation Notes
            worksheet.write(row, 8, "", self.formats['notes_cell'])
            
            row += 1
        
        # Add validation summary
        row += 2
        worksheet.write(row, 0, "VALIDATION SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, f"Total Themes for Validation: {len(themes_data['themes'])}")
        worksheet.write(row, 3, "Validated Themes: [Count after review]")
        worksheet.write(row, 6, "Validation Complete: [Yes/No]")

    def _create_comprehensive_evidence_view(self, theme: Dict[str, Any], all_quotes: List[Dict]) -> str:
        """Create comprehensive evidence view for validation (more detailed than previous)"""
        if not all_quotes:
            return "❌ NO EVIDENCE FOUND - This theme has no supporting quotes"
        
        evidence_parts = []
        
        # Theme context
        evidence_parts.append(f"🎯 THEME: {theme.get('theme_statement', 'No statement')}")
        evidence_parts.append(f"📊 EVIDENCE SCOPE: {len(all_quotes)} quotes across {len(set(q.get('company', q.get('company_name', 'Unknown')) for q in all_quotes))} companies")
        evidence_parts.append("=" * 60)
        
        # Group by company and show ALL quotes (not just top 3)
        quotes_by_company = {}
        for quote in all_quotes:
            company = quote.get('company', quote.get('company_name', 'Unknown'))
            if company not in quotes_by_company:
                quotes_by_company[company] = []
            quotes_by_company[company].append(quote)
        
        # Show comprehensive evidence by company
        for company, company_quotes in quotes_by_company.items():
            evidence_parts.append(f"\n🏢 {company.upper()} ({len(company_quotes)} quotes):")
            
            for i, quote in enumerate(company_quotes, 1):
                sentiment = quote.get('sentiment', 'unknown').upper()
                impact = quote.get('impact_score', 0)
                interviewee = quote.get('interviewee_name', 'Unknown')
                
                # Full quote text for validation (not truncated)
                quote_text = quote.get('verbatim_response', 'No quote text')
                
                evidence_parts.append(f"\n  {i}. [{sentiment}, Impact: {impact}] {interviewee}:")
                evidence_parts.append(f"     \"{quote_text}\"")
        
        # Evidence quality indicators
        evidence_parts.append(f"\n📈 EVIDENCE ANALYSIS:")
        sentiments = [q.get('sentiment', 'unknown') for q in all_quotes]
        avg_impact = sum(q.get('impact_score', 0) for q in all_quotes) / len(all_quotes) if all_quotes else 0
        
        evidence_parts.append(f"• Average Impact Score: {avg_impact:.1f}/5")
        evidence_parts.append(f"• Sentiment Distribution: {dict(zip(*zip(*[(s, sentiments.count(s)) for s in set(sentiments)])))}") 
        evidence_parts.append(f"• Cross-Company Validation: {len(quotes_by_company)} companies represented")
        evidence_parts.append(f"• Evidence Depth: {len(all_quotes)} total quotes")
        
        return "\n".join(evidence_parts)

    def _map_theme_to_research_area(self, theme: Dict[str, Any]) -> str:
        """Map theme to likely research question area"""
        subject = theme.get('harmonized_subject', '').lower()
        theme_type = theme.get('theme_type', '').lower()
        
        # Simple mapping based on subject and theme type
        if 'product' in subject or 'capabilities' in subject:
            return "Product feature evaluation"
        elif 'pricing' in subject or 'commercial' in subject:
            return "Pricing model assessment"
        elif 'implementation' in subject:
            return "Implementation challenges"
        elif 'sales' in subject:
            return "Sales process evaluation"
        elif 'competitive' in subject:
            return "Competitive positioning"
        elif 'user' in subject or 'experience' in subject:
            return "User experience factors"
        else:
            return "General market insights"

    def _create_quote_curation_tab(self, themes_data: Dict[str, Any]):
        """Phase 3: Quote-by-Quote Curation for validated themes only"""
        worksheet = self.workbook.add_worksheet('Phase 3 - Quote Curation')
        
        # Set column widths
        worksheet.set_column('A:A', 12)  # Theme ID
        worksheet.set_column('B:B', 40)  # Validated Theme Statement
        worksheet.set_column('C:C', 50)  # Individual Quote
        worksheet.set_column('D:D', 15)  # Company
        worksheet.set_column('E:E', 15)  # Interviewee
        worksheet.set_column('F:F', 12)  # Impact Score
        worksheet.set_column('G:G', 12)  # Sentiment
        worksheet.set_column('H:H', 20)  # Evidence Quality
        worksheet.set_column('I:I', 18)  # Usage Level
        worksheet.set_column('J:J', 25)  # Research Question
        worksheet.set_column('K:K', 30)  # Quote Notes
        
        # Title and instructions
        worksheet.merge_range('A1:K1', "Phase 3: Quote-by-Quote Evidence Curation", self.formats['title'])
        worksheet.merge_range('A2:K2', "PURPOSE: For validated themes only, curate individual quotes by evidence strength and usage level. Build evidence hierarchy for report writing.", self.formats['subheader'])
        
        # Headers
        headers = [
            "Theme ID", "Validated Theme Statement", "Individual Quote", "Company", "Interviewee",
            "Impact Score", "Sentiment", "Evidence Quality", "Usage Level", "Research Question", "Quote Notes"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, self.formats['header'])
        
        # Instructions for analyst
        row = 4
        worksheet.write(row, 0, "INSTRUCTIONS:", self.formats['header'])
        worksheet.write(row, 1, "1. Only themes marked 'VALIDATED' in Phase 2 should appear here", self.formats['data_cell'])
        row += 1
        worksheet.write(row, 1, "2. Rate each quote's evidence quality for the specific theme", self.formats['data_cell'])
        row += 1
        worksheet.write(row, 1, "3. Assign usage level based on quote strength and relevance", self.formats['data_cell'])
        row += 1
        worksheet.write(row, 1, "4. Featured quotes should be your strongest evidence for executive summary", self.formats['data_cell'])
        row += 2
        
        # Create quote curation rows for each theme
        # Note: In real implementation, this would only show validated themes
        for theme in themes_data['themes']:
            all_quotes = theme.get('all_quotes', [])
            
            for quote in all_quotes:
                # Theme ID
                worksheet.write(row, 0, theme['theme_id'], self.formats['data_cell'])
                
                # Validated Theme Statement (placeholder - would come from Phase 2)
                theme_statement = f"[VALIDATED VERSION FROM PHASE 2: {theme.get('theme_statement', '')[:50]}...]"
                worksheet.write(row, 1, theme_statement, self.formats['data_cell'])
                
                # Individual Quote
                quote_text = quote.get('verbatim_response', 'No quote')
                worksheet.write(row, 2, quote_text, self.formats['data_cell'])
                
                # Company & Interviewee
                company = quote.get('company', quote.get('company_name', 'Unknown'))
                worksheet.write(row, 3, company, self.formats['data_cell'])
                worksheet.write(row, 4, quote.get('interviewee_name', 'Unknown'), self.formats['data_cell'])
                
                # Impact Score & Sentiment
                worksheet.write(row, 5, quote.get('impact_score', 0), self.formats['number'])
                worksheet.write(row, 6, quote.get('sentiment', 'unknown').title(), self.formats['data_cell'])
                
                # Evidence Quality Assessment
                worksheet.data_validation(row, 7, row, 7, {
                    'validate': 'list',
                    'source': ['STRONG PROOF - Perfect example', 'SUPPORTING - Good evidence', 'WEAK - Tangential', 'IRRELEVANT - Does not support']
                })
                worksheet.write(row, 7, "", self.formats['decision_cell'])
                
                # Usage Level Assignment  
                worksheet.data_validation(row, 8, row, 8, {
                    'validate': 'list',
                    'source': ['FEATURED - Executive summary', 'PRIMARY - Main evidence', 'SUPPORTING - Background', 'EXCLUDE - Do not use']
                })
                worksheet.write(row, 8, "", self.formats['decision_cell'])
                
                # Research Question Connection
                research_connection = self._map_theme_to_research_area(theme)
                worksheet.write(row, 9, research_connection, self.formats['data_cell'])
                
                # Quote Notes
                worksheet.write(row, 10, "", self.formats['notes_cell'])
                
                row += 1
                
                # Limit quotes per theme for readability
                if row > 50:  # Practical limit for Excel usability
                    break
            
            if row > 50:
                break
        
        # Add curation summary
        row += 2
        worksheet.write(row, 0, "CURATION SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, "Featured Quotes: [Count]")
        worksheet.write(row, 3, "Primary Evidence: [Count]") 
        worksheet.write(row, 6, "Supporting Quotes: [Count]")
        worksheet.write(row, 9, "Total Curated: [Count]")

    def _create_integrated_review_tab(self, themes_data: Dict[str, Any]):
        """Create integrated theme-evidence review tab where analysts see themes with all supporting quotes"""
        worksheet = self.workbook.add_worksheet('🔍 Theme-Evidence Review')
        
        # Set column widths for integrated view
        worksheet.set_column('A:A', 12)  # Theme ID
        worksheet.set_column('B:B', 45)  # Theme Title
        worksheet.set_column('C:C', 18)  # Win-Loss Category  
        worksheet.set_column('D:D', 18)  # Report Section
        worksheet.set_column('E:E', 12)  # Quality Score
        worksheet.set_column('F:F', 18)  # Theme Rating
        worksheet.set_column('G:G', 80)  # Supporting Evidence (All Quotes)
        worksheet.set_column('H:H', 25)  # Evidence Strength
        worksheet.set_column('I:I', 15)  # Company Coverage
        worksheet.set_column('J:J', 40)  # Analyst Notes
        worksheet.set_column('K:K', 15)  # Priority
        
        # Title and instructions
        worksheet.merge_range('A1:K1', "Integrated Theme-Evidence Review - Make Decisions with Full Context", self.formats['title'])
        worksheet.merge_range('A2:K2', "WORKFLOW: For each theme, review ALL supporting quotes (Column G) → Assess evidence strength (Column H) → Set theme rating (Column F) → Assign to report section (Column D)", self.formats['subheader'])
        
        # Headers
        headers = [
            "Theme ID", "Theme Title", "Win-Loss Category", "Report Section", "Quality Score",
            "Theme Rating", "Supporting Evidence (All Quotes)", "Evidence Strength", 
            "Company Coverage", "Analyst Notes", "Priority"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, self.formats['header'])
        
        # Process each theme with all its evidence
        row = 4
        for theme in themes_data['themes']:
            # Get all quotes for this theme
            all_quotes = theme.get('all_quotes', [])
            supporting_quotes = theme.get('supporting_quotes', [])
            
            # Theme basic info
            worksheet.write(row, 0, theme['theme_id'], self.formats['data_cell'])
            
            theme_title = theme.get('theme_title', f"Theme {theme['theme_id']}")
            worksheet.write(row, 1, theme_title, self.formats['data_cell'])
            
            # Win-Loss Category with dropdown
            win_loss_category = self._determine_win_loss_category(theme)
            worksheet.data_validation(row, 2, row, 2, {
                'validate': 'list',
                'source': ['Strength', 'Weakness', 'Opportunity', 'Competitive', 'Process']
            })
            worksheet.write(row, 2, win_loss_category, self.formats['data_cell'])
            
            # Report Section with dropdown
            report_section = self._determine_report_section(win_loss_category)
            worksheet.data_validation(row, 3, row, 3, {
                'validate': 'list',
                'source': ['Section 2: Why You Win', 'Section 3: Why You Lose', 'Section 4: Market Opportunities', 'Section 5: Competitive Intelligence', 'Section 6: Implementation Insights']
            })
            worksheet.write(row, 3, report_section, self.formats['data_cell'])
            
            # Quality Score
            worksheet.write(row, 4, theme['validation_metrics']['quality_score'], self.formats['number'])
            
            # Theme Rating dropdown (Featured/Include/Exclude)
            worksheet.data_validation(row, 5, row, 5, {
                'validate': 'list',
                'source': ['FEATURED', 'INCLUDE', 'EXCLUDE']
            })
            worksheet.write(row, 5, "", self.formats['decision_cell'])
            
            # Supporting Evidence - ALL quotes with context
            evidence_text = self._create_integrated_evidence_view(theme, all_quotes, supporting_quotes)
            worksheet.write(row, 6, evidence_text, self.formats['data_cell'])
            
            # Evidence Strength Assessment dropdown
            worksheet.data_validation(row, 7, row, 7, {
                'validate': 'list',
                'source': ['STRONG - Multiple companies, clear pattern', 'MODERATE - Some validation needed', 'WEAK - Limited evidence', 'INSUFFICIENT - Needs more quotes']
            })
            worksheet.write(row, 7, "", self.formats['decision_cell'])
            
            # Company Coverage
            company_dist = theme['validation_metrics'].get('company_distribution', {})
            dist_summary = company_dist.get('distribution_summary', f"{theme['validation_metrics']['companies_count']} companies")
            worksheet.write(row, 8, dist_summary, self.formats['data_cell'])
            
            # Analyst Notes
            worksheet.write(row, 9, "", self.formats['notes_cell'])
            
            # Priority dropdown
            worksheet.data_validation(row, 10, row, 10, {
                'validate': 'list',
                'source': ['HIGH', 'MEDIUM', 'LOW']
            })
            worksheet.write(row, 10, "", self.formats['decision_cell'])
            
            row += 1
        
        # Add summary section
        row += 2
        worksheet.write(row, 0, "INTEGRATION SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, f"Total Themes for Review: {len(themes_data['themes'])}")
        worksheet.write(row, 3, f"Total Supporting Quotes: {sum(len(theme.get('all_quotes', [])) for theme in themes_data['themes'])}")
        worksheet.write(row, 6, "Complete evidence review before making theme decisions")

    def _create_integrated_evidence_view(self, theme: Dict[str, Any], all_quotes: List[Dict], supporting_quotes: List[Dict]) -> str:
        """Create integrated view of all evidence for a theme"""
        if not all_quotes:
            return "No quotes available"
        
        evidence_parts = []
        
        # Add theme statement for context
        evidence_parts.append(f"THEME: {theme.get('theme_statement', 'No statement')}")
        evidence_parts.append("=" * 50)
        
        # Group quotes by company for better organization
        quotes_by_company = {}
        for quote in all_quotes:
            company = quote.get('company', quote.get('company_name', 'Unknown'))
            if company not in quotes_by_company:
                quotes_by_company[company] = []
            quotes_by_company[company].append(quote)
        
        # Display quotes organized by company
        for company, company_quotes in quotes_by_company.items():
            evidence_parts.append(f"\n📍 {company} ({len(company_quotes)} quotes):")
            
            for i, quote in enumerate(company_quotes[:3], 1):  # Limit to top 3 per company
                sentiment = quote.get('sentiment', 'unknown').upper()
                impact = quote.get('impact_score', 0)
                interviewee = quote.get('interviewee_name', 'Unknown')
                
                # Mark if this is a supporting quote
                is_supporting = any(sq.get('response_id') == quote.get('response_id') for sq in supporting_quotes)
                support_marker = "⭐ " if is_supporting else "• "
                
                quote_text = quote.get('verbatim_response', '')[:200] + "..." if len(quote.get('verbatim_response', '')) > 200 else quote.get('verbatim_response', '')
                
                evidence_parts.append(f"  {support_marker}[{sentiment}, Impact: {impact}] {interviewee}: \"{quote_text}\"")
            
            if len(company_quotes) > 3:
                evidence_parts.append(f"  ... and {len(company_quotes) - 3} more quotes from {company}")
        
        # Add summary stats
        evidence_parts.append(f"\n📊 EVIDENCE SUMMARY:")
        evidence_parts.append(f"• Total Quotes: {len(all_quotes)} across {len(quotes_by_company)} companies")
        evidence_parts.append(f"• Top Supporting: {len(supporting_quotes)} quotes (marked with ⭐)")
        evidence_parts.append(f"• Avg Impact: {sum(q.get('impact_score', 0) for q in all_quotes) / len(all_quotes):.1f}")
        
        return "\n".join(evidence_parts)
    
    def _create_theme_curation_tab(self, themes_data: Dict[str, Any]):
        """Create the main theme curation workspace"""
        worksheet = self.workbook.add_worksheet('🎯 Theme Curation')
        
        # Set column widths
        worksheet.set_column('A:A', 12)  # Theme ID
        worksheet.set_column('B:B', 50)  # Theme Title
        worksheet.set_column('C:C', 60)  # Theme Statement  
        worksheet.set_column('D:D', 15)  # Theme Type
        worksheet.set_column('E:E', 20)  # Subject
        worksheet.set_column('F:F', 18)  # Win-Loss Category
        worksheet.set_column('G:G', 18)  # Report Section
        worksheet.set_column('H:H', 12)  # Quality Score
        worksheet.set_column('I:I', 20)  # Company Distribution
        worksheet.set_column('J:J', 50)  # Evidence Preview
        worksheet.set_column('K:K', 15)  # Quality Flags
        worksheet.set_column('L:L', 18)  # Theme Rating (Featured/Include/Exclude)
        worksheet.set_column('M:M', 40)  # Analyst Notes
        worksheet.set_column('N:N', 15)  # Priority Level
        
        # Title
        worksheet.merge_range('A1:N1', "Theme Curation & Section Assignment Workspace", self.formats['title'])
        
        # Instructions
        worksheet.merge_range('A2:N2', "INSTRUCTIONS: 1) Review evidence preview (Column J) 2) Assign win-loss category (Column F) 3) Set theme rating (Column L) 4) Assign to report section (Column G). This organizes themes for structured win-loss reporting.", self.formats['subheader'])
        
        # Headers
        headers = [
            "Theme ID", "Theme Title", "Theme Statement", "Type", "Subject Category",
            "Win-Loss Category", "Report Section", "Quality Score", "Company Distribution", 
            "Evidence Preview", "Quality Flags", "Theme Rating", "Analyst Notes", "Priority Level"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, self.formats['header'])
        
        # Theme data
        row = 4
        for theme in themes_data['themes']:
            # Theme ID
            worksheet.write(row, 0, theme['theme_id'])
            
            # Theme Title (new column)
            theme_title = theme.get('theme_title', f"Theme {theme['theme_id']}")
            worksheet.write(row, 1, theme_title, self.formats['data_cell'])
            
            # Theme Statement
            worksheet.write(row, 2, theme['theme_statement'], self.formats['data_cell'])
            
            # Theme Type with formatting
            theme_type = theme['theme_type']
            theme_format = self.formats.get(theme_type, self.formats['data_cell'])
            worksheet.write(row, 3, theme_type.replace('_', ' ').title(), theme_format)
            
            # Subject Category
            worksheet.write(row, 4, theme['harmonized_subject'])
            
            # Win-Loss Category (new column)
            win_loss_category = self._determine_win_loss_category(theme)
            worksheet.data_validation(row, 5, row, 5, {
                'validate': 'list',
                'source': ['Strength', 'Weakness', 'Opportunity', 'Competitive', 'Process']
            })
            worksheet.write(row, 5, win_loss_category, self.formats['data_cell'])
            
            # Report Section (new column) 
            report_section = self._determine_report_section(win_loss_category)
            worksheet.data_validation(row, 6, row, 6, {
                'validate': 'list',
                'source': ['Section 2: Why You Win', 'Section 3: Why You Lose', 'Section 4: Market Opportunities', 'Section 5: Competitive Intelligence', 'Section 6: Implementation Insights']
            })
            worksheet.write(row, 6, report_section, self.formats['data_cell'])
            
            # Quality Score
            worksheet.write(row, 7, theme['validation_metrics']['quality_score'], self.formats['number'])
            
            # Company Distribution
            company_dist = theme['validation_metrics'].get('company_distribution', {})
            dist_summary = company_dist.get('distribution_summary', f"{theme['validation_metrics']['companies_count']} companies")
            worksheet.write(row, 8, dist_summary, self.formats['data_cell'])
            
            # Evidence Preview (Top 2 supporting quotes)
            evidence_preview = self._create_evidence_preview(theme)
            worksheet.write(row, 9, evidence_preview, self.formats['data_cell'])
            
            # Quality Flags
            quality_flags = self._assign_quality_flags(theme)
            worksheet.write(row, 10, ", ".join(quality_flags), self.formats['data_cell'])
            
            # Theme Rating Cell (dropdown) - Featured/Include/Exclude
            worksheet.data_validation(row, 11, row, 11, {
                'validate': 'list',
                'source': ['FEATURED', 'INCLUDE', 'EXCLUDE']
            })
            worksheet.write(row, 11, "", self.formats['decision_cell'])
            
            # Notes Cell
            worksheet.write(row, 12, "", self.formats['notes_cell'])
            
            # Priority Cell (dropdown)
            worksheet.data_validation(row, 13, row, 13, {
                'validate': 'list', 
                'source': ['HIGH', 'MEDIUM', 'LOW']
            })
            worksheet.write(row, 13, "", self.formats['decision_cell'])
            
            row += 1
        
        # Add conditional formatting for theme types
        worksheet.conditional_format(f'C4:C{row}', {
            'type': 'text',
            'criteria': 'containing',
            'value': 'Strength',
            'format': self.formats['strength']
        })
        
        worksheet.conditional_format(f'C4:C{row}', {
            'type': 'text', 
            'criteria': 'containing',
            'value': 'Weakness',
            'format': self.formats['weakness']
        })
    
    def _create_quote_analysis_tab(self, themes_data: Dict[str, Any]):
        """Create detailed quote analysis and selection tab"""
        worksheet = self.workbook.add_worksheet('💬 Quote Analysis')
        
        # Set column widths
        worksheet.set_column('A:A', 12)  # Response ID
        worksheet.set_column('B:B', 40)  # Original Question
        worksheet.set_column('C:C', 12)  # Theme ID
        worksheet.set_column('D:D', 40)  # Theme Title
        worksheet.set_column('E:E', 18)  # Report Section
        worksheet.set_column('F:F', 50)  # Full Theme Statement
        worksheet.set_column('G:G', 50)  # Verbatim Quote
        worksheet.set_column('H:H', 12)  # Sentiment
        worksheet.set_column('I:I', 12)  # Impact Score
        worksheet.set_column('J:J', 15)  # Company
        worksheet.set_column('K:K', 15)  # Interviewee
        worksheet.set_column('L:L', 18)  # Quote Rating
        worksheet.set_column('M:M', 30)  # Quote Notes
        
        # Title
        worksheet.merge_range('A1:M1', "Quote Analysis & Selection for Final Report", self.formats['title'])
        
        # Headers
        headers = [
            "Response ID", "Original Question", "Theme ID", "Theme Title", "Report Section", "Full Theme Statement",
            "Verbatim Quote", "Sentiment", "Impact Score", "Company", "Interviewee", 
            "Quote Rating", "Quote Notes"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, self.formats['header'])
        
        # Quote data
        row = 3
        for theme in themes_data['themes']:
            for quote in theme['all_quotes']:
                # Response ID
                worksheet.write(row, 0, quote.get('response_id', ''))
                
                # Original Question
                worksheet.write(row, 1, quote.get('question', 'Question not available'), self.formats['data_cell'])
                
                # Theme ID
                worksheet.write(row, 2, theme['theme_id'])
                
                # Theme Title
                theme_title = theme.get('theme_title', f"Theme {theme['theme_id']}")
                worksheet.write(row, 3, theme_title, self.formats['data_cell'])
                
                # Report Section
                win_loss_category = self._determine_win_loss_category(theme)
                report_section = self._determine_report_section(win_loss_category)
                worksheet.write(row, 4, report_section, self.formats['data_cell'])
                
                # Full Theme Statement
                worksheet.write(row, 5, theme['theme_statement'], self.formats['data_cell'])
                
                # Verbatim Quote
                worksheet.write(row, 6, quote['verbatim_response'], self.formats['data_cell'])
                
                # Sentiment
                sentiment = quote.get('sentiment', 'unknown').title()
                worksheet.write(row, 7, sentiment)
                
                # Impact Score
                worksheet.write(row, 8, quote.get('impact_score', 0), self.formats['number'])
                
                # Company (handle both column names)
                company = quote.get('company', quote.get('company_name', 'Unknown'))
                worksheet.write(row, 9, company)
                
                # Interviewee
                worksheet.write(row, 10, quote.get('interviewee_name', ''))
                
                # Quote Rating dropdown (Featured/Include/Exclude)
                worksheet.data_validation(row, 11, row, 11, {
                    'validate': 'list',
                    'source': ['FEATURED', 'INCLUDE', 'EXCLUDE']
                })
                worksheet.write(row, 11, "", self.formats['decision_cell'])
                
                # Quote Notes
                worksheet.write(row, 12, "", self.formats['notes_cell'])
                
                row += 1

    def _create_section_planning_tab(self, themes_data: Dict[str, Any]):
        """Create section planning dashboard for report structure"""
        worksheet = self.workbook.add_worksheet('Section Planning')
        
        # Set column widths
        worksheet.set_column('A:A', 25)  # Section Name
        worksheet.set_column('B:B', 15)  # Featured Count
        worksheet.set_column('C:C', 15)  # Include Count
        worksheet.set_column('D:D', 15)  # Total Themes
        worksheet.set_column('E:E', 20)  # Question Coverage
        worksheet.set_column('F:F', 60)  # Key Themes Preview
        worksheet.set_column('G:G', 20)  # Strength Assessment
        
        # Title
        worksheet.merge_range('A1:G1', "Win-Loss Report Section Planning Dashboard", self.formats['title'])
        
        # Instructions
        worksheet.merge_range('A2:G2', "OVERVIEW: This dashboard shows how themes will be distributed across report sections. Use this to ensure balanced coverage and strong narratives for each section.", self.formats['subheader'])
        
        # Section summary
        section_summary = self._analyze_section_distribution(themes_data['themes'])
        
        # Headers
        headers = [
            "Report Section", "Featured Themes", "Include Themes", "Total Themes",
            "Question Coverage", "Key Themes Preview", "Strength Assessment"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, self.formats['header'])
        
        # Section data
        row = 4
        sections = [
            "Section 2: Why You Win",
            "Section 3: Why You Lose", 
            "Section 4: Market Opportunities",
            "Section 5: Competitive Intelligence",
            "Section 6: Implementation Insights"
        ]
        
        for section in sections:
            section_data = section_summary.get(section, {})
            
            # Section Name
            worksheet.write(row, 0, section, self.formats['data_cell'])
            
            # Featured Count
            featured_count = section_data.get('featured_count', 0)
            worksheet.write(row, 1, featured_count, self.formats['number'])
            
            # Include Count  
            include_count = section_data.get('include_count', 0)
            worksheet.write(row, 2, include_count, self.formats['number'])
            
            # Total Themes
            total_count = featured_count + include_count
            worksheet.write(row, 3, total_count, self.formats['number'])
            
            # Question Coverage (placeholder)
            worksheet.write(row, 4, "To Be Determined", self.formats['data_cell'])
            
            # Key Themes Preview
            key_themes = section_data.get('key_themes', [])
            themes_preview = "; ".join(key_themes[:2]) if key_themes else "No themes assigned"
            worksheet.write(row, 5, themes_preview, self.formats['data_cell'])
            
            # Strength Assessment
            strength = self._assess_section_strength(featured_count, include_count, total_count)
            worksheet.write(row, 6, strength, self.formats['data_cell'])
            
            row += 1
        
        # Add summary statistics
        row += 2
        worksheet.write(row, 0, "REPORT SUMMARY:", self.formats['header'])
        row += 1
        
        total_featured = sum(section_summary.get(s, {}).get('featured_count', 0) for s in sections)
        total_include = sum(section_summary.get(s, {}).get('include_count', 0) for s in sections)
        
        worksheet.write(row, 0, f"Total Featured Themes: {total_featured}")
        worksheet.write(row, 3, f"Total Include Themes: {total_include}")
        worksheet.write(row, 6, f"Grand Total: {total_featured + total_include}")

    def _analyze_section_distribution(self, themes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how themes are distributed across report sections"""
        section_analysis = {}
        
        for theme in themes:
            # Determine section for this theme
            win_loss_category = self._determine_win_loss_category(theme)
            report_section = self._determine_report_section(win_loss_category)
            
            if report_section not in section_analysis:
                section_analysis[report_section] = {
                    'featured_count': 0,
                    'include_count': 0,
                    'key_themes': []
                }
            
            # For now, assume all themes are "Include" level
            # In reality, this would come from analyst decisions
            section_analysis[report_section]['include_count'] += 1
            
            # Add theme title to key themes
            theme_title = theme.get('theme_title', f"Theme {theme.get('theme_id', '')}")
            section_analysis[report_section]['key_themes'].append(theme_title)
        
        return section_analysis
    
    def _assess_section_strength(self, featured_count: int, include_count: int, total_count: int) -> str:
        """Assess the strength of evidence for a report section"""
        if featured_count >= 2:
            return "STRONG - Executive Ready"
        elif featured_count >= 1:
            return "GOOD - Solid Evidence" 
        elif include_count >= 3:
            return "MODERATE - Needs Curation"
        elif total_count >= 1:
            return "WEAK - Limited Evidence"
        else:
            return "MISSING - No Themes"

    def _create_competitive_tab(self, themes_data: Dict[str, Any]):
        """Create competitive intelligence deep dive tab"""
        worksheet = self.workbook.add_worksheet('🏆 Competitive Intel')
        
        # Set column widths
        worksheet.set_column('A:A', 15)  # Theme Type
        worksheet.set_column('B:B', 50)  # Theme Statement
        worksheet.set_column('C:C', 40)  # Verbatim Quote
        worksheet.set_column('D:D', 20)  # Competitive Insight
        worksheet.set_column('E:E', 15)  # Company
        worksheet.set_column('F:F', 12)  # Impact Score
        worksheet.set_column('G:G', 30)  # Strategic Implication
        
        # Title
        worksheet.merge_range('A1:G1', "Competitive Intelligence & Market Positioning Analysis", self.formats['title'])
        
        # Headers
        headers = [
            "Theme Type", "Theme Statement", "Key Quote", "Competitive Insight", 
            "Company", "Impact Score", "Strategic Implication"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, self.formats['header'])
        
        # Competitive data - focus on themes flagged as competitive
        row = 3
        for theme in themes_data['themes']:
            if theme.get('competitive_flag', False):
                # Show top quotes for competitive themes
                for quote in theme['supporting_quotes'][:3]:  # Top 3 quotes
                    worksheet.write(row, 0, theme['theme_type'].replace('_', ' ').title())
                    worksheet.write(row, 1, theme['theme_statement'], self.formats['data_cell'])
                    worksheet.write(row, 2, quote['quote_text'], self.formats['data_cell'])
                    worksheet.write(row, 3, self._extract_competitive_insight(quote['quote_text']), self.formats['data_cell'])
                    worksheet.write(row, 4, quote['company'])
                    worksheet.write(row, 5, quote['impact_score'], self.formats['number'])
                    worksheet.write(row, 6, "", self.formats['notes_cell'])  # For analyst to fill
                    row += 1
    
    def _create_raw_data_tab(self, themes_data: Dict[str, Any]):
        """Create raw data reference tab"""
        worksheet = self.workbook.add_worksheet('📋 Raw Data')
        
        # Set column widths
        worksheet.set_column('A:A', 15)  # Response ID
        worksheet.set_column('B:B', 20)  # Company
        worksheet.set_column('C:C', 15)  # Interviewee
        worksheet.set_column('D:D', 20)  # Subject
        worksheet.set_column('E:E', 50)  # Question
        worksheet.set_column('F:F', 60)  # Response
        worksheet.set_column('G:G', 12)  # Sentiment
        worksheet.set_column('H:H', 12)  # Impact Score
        
        # Title
        worksheet.merge_range('A1:H1', "Raw Interview Data Reference", self.formats['title'])
        
        # Headers
        headers = [
            "Response ID", "Company", "Interviewee", "Subject", 
            "Original Question", "Verbatim Response", "Sentiment", "Impact Score"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, self.formats['header'])
        
        # Raw data from all themes
        row = 3
        all_quotes = []
        for theme in themes_data['themes']:
            all_quotes.extend(theme['all_quotes'])
        
        # Remove duplicates by response_id
        seen_ids = set()
        unique_quotes = []
        for quote in all_quotes:
            if quote['response_id'] not in seen_ids:
                unique_quotes.append(quote)
                seen_ids.add(quote['response_id'])
        
        for quote in unique_quotes:
            worksheet.write(row, 0, quote['response_id'])
            company = quote.get('company', quote.get('company_name', 'Unknown'))
            worksheet.write(row, 1, company)
            worksheet.write(row, 2, quote.get('interviewee_name', ''))
            worksheet.write(row, 3, quote.get('subject', ''))
            worksheet.write(row, 4, quote.get('question', ''), self.formats['data_cell'])
            worksheet.write(row, 5, quote['verbatim_response'], self.formats['data_cell'])
            worksheet.write(row, 6, quote.get('sentiment', 'unknown').title())
            worksheet.write(row, 7, quote.get('impact_score', 0), self.formats['number'])
            row += 1
    
    def _create_report_builder_tab(self, themes_data: Dict[str, Any]):
        """Create enhanced report builder that respects analyst decisions and quote classifications"""
        worksheet = self.workbook.add_worksheet('Report Builder (Final Output)')
        
        # Set column widths
        worksheet.set_column('A:A', 25)  # Section
        worksheet.set_column('B:B', 60)  # Theme Statement
        worksheet.set_column('C:C', 40)  # Featured Quotes
        worksheet.set_column('D:D', 40)  # Supporting Quotes
        worksheet.set_column('E:E', 20)  # Decision Status
        
        # Title and instructions
        worksheet.merge_range('A1:E1', "Executive Report Builder - Based on Analyst Decisions", self.formats['title'])
        worksheet.merge_range('A2:E2', "This report is built from VALIDATED themes and FEATURED quotes only. Review section tabs for full analysis.", self.formats['subheader'])
        
        row = 4
        
        # Executive Summary Section
        worksheet.write(row, 0, "📊 EXECUTIVE SUMMARY", self.formats['header'])
        worksheet.merge_range('A4:E4', "Key insights for executive audience - Featured quotes only", self.formats['data_cell'])
        row += 1
        
        # Get featured quotes from validated themes
        featured_quotes = self._get_featured_quotes_from_validated_themes(themes_data)
        if featured_quotes:
            for quote in featured_quotes[:5]:  # Top 5 featured quotes
                worksheet.write(row, 0, "• Featured Insight")
                worksheet.write(row, 1, quote.get('theme_statement', 'No theme statement'), self.formats['data_cell'])
                worksheet.write(row, 2, f"\"{quote.get('verbatim_response', '')[:100]}...\"", self.formats['data_cell'])
                worksheet.write(row, 3, f"{quote.get('company', 'Unknown')} - {quote.get('interviewee_name', 'Unknown')}", self.formats['data_cell'])
                worksheet.write(row, 4, "VALIDATED", self.formats['validated'])
                row += 1
        else:
            worksheet.write(row, 1, "No featured quotes identified. Review section tabs to classify quotes as 'FEATURED'.", self.formats['data_cell'])
            row += 1
        
        row += 2
        
        # Win Drivers Section
        worksheet.write(row, 0, "🟢 WHY YOU WIN", self.formats['strength'])
        worksheet.merge_range(f'A{row}:E{row}', "Validated win driver themes with primary evidence", self.formats['data_cell'])
        row += 1
        
        win_themes = self._get_validated_themes_by_section(themes_data, 'win')
        if win_themes:
            for theme in win_themes:
                worksheet.write(row, 0, f"• {theme['theme_id']}")
                worksheet.write(row, 1, theme.get('theme_statement', 'No statement'), self.formats['data_cell'])
                
                # Show primary quotes for this theme
                primary_quotes = self._get_primary_quotes_for_theme(theme)
                if primary_quotes:
                    quote_text = f"\"{primary_quotes[0].get('verbatim_response', '')[:80]}...\""
                    worksheet.write(row, 2, quote_text, self.formats['data_cell'])
                    worksheet.write(row, 3, f"{len(primary_quotes)} supporting quotes", self.formats['data_cell'])
                else:
                    worksheet.write(row, 2, "No primary quotes classified", self.formats['data_cell'])
                    worksheet.write(row, 3, "Review quote classifications", self.formats['data_cell'])
                
                worksheet.write(row, 4, "VALIDATED", self.formats['validated'])
                row += 1
        else:
            worksheet.write(row, 1, "No validated win themes. Review 'Win Drivers Section' tab.", self.formats['data_cell'])
            row += 1
        
        row += 2
        
        # Loss Factors Section
        worksheet.write(row, 0, "🔴 WHY YOU LOSE", self.formats['weakness'])
        worksheet.merge_range(f'A{row}:E{row}', "Validated loss factor themes with primary evidence", self.formats['data_cell'])
        row += 1
        
        loss_themes = self._get_validated_themes_by_section(themes_data, 'loss')
        if loss_themes:
            for theme in loss_themes:
                worksheet.write(row, 0, f"• {theme['theme_id']}")
                worksheet.write(row, 1, theme.get('theme_statement', 'No statement'), self.formats['data_cell'])
                
                # Show primary quotes for this theme
                primary_quotes = self._get_primary_quotes_for_theme(theme)
                if primary_quotes:
                    quote_text = f"\"{primary_quotes[0].get('verbatim_response', '')[:80]}...\""
                    worksheet.write(row, 2, quote_text, self.formats['data_cell'])
                    worksheet.write(row, 3, f"{len(primary_quotes)} supporting quotes", self.formats['data_cell'])
                else:
                    worksheet.write(row, 2, "No primary quotes classified", self.formats['data_cell'])
                    worksheet.write(row, 3, "Review quote classifications", self.formats['data_cell'])
                
                worksheet.write(row, 4, "VALIDATED", self.formats['validated'])
                row += 1
        else:
            worksheet.write(row, 1, "No validated loss themes. Review 'Loss Factors Section' tab.", self.formats['data_cell'])
            row += 1
        
        row += 2
        
        # Competitive Intelligence Section
        worksheet.write(row, 0, "🟡 COMPETITIVE INTELLIGENCE", self.formats['mixed_signal'])
        worksheet.merge_range(f'A{row}:E{row}', "Validated competitive insights with primary evidence", self.formats['data_cell'])
        row += 1
        
        competitive_themes = self._get_validated_themes_by_section(themes_data, 'competitive')
        if competitive_themes:
            for theme in competitive_themes:
                worksheet.write(row, 0, f"• {theme['theme_id']}")
                worksheet.write(row, 1, theme.get('theme_statement', 'No statement'), self.formats['data_cell'])
                
                # Show primary quotes for this theme
                primary_quotes = self._get_primary_quotes_for_theme(theme)
                if primary_quotes:
                    quote_text = f"\"{primary_quotes[0].get('verbatim_response', '')[:80]}...\""
                    worksheet.write(row, 2, quote_text, self.formats['data_cell'])
                    worksheet.write(row, 3, f"{len(primary_quotes)} supporting quotes", self.formats['data_cell'])
                else:
                    worksheet.write(row, 2, "No primary quotes classified", self.formats['data_cell'])
                    worksheet.write(row, 3, "Review quote classifications", self.formats['data_cell'])
                
                worksheet.write(row, 4, "VALIDATED", self.formats['validated'])
                row += 1
        else:
            worksheet.write(row, 1, "No validated competitive themes. Review 'Competitive Intelligence' tab.", self.formats['data_cell'])
            row += 1
        
        row += 2
        
        # Implementation Insights Section
        worksheet.write(row, 0, "🔧 IMPLEMENTATION INSIGHTS", self.formats['data_cell'])
        worksheet.merge_range(f'A{row}:E{row}', "Validated implementation themes with primary evidence", self.formats['data_cell'])
        row += 1
        
        implementation_themes = self._get_validated_themes_by_section(themes_data, 'implementation')
        if implementation_themes:
            for theme in implementation_themes:
                worksheet.write(row, 0, f"• {theme['theme_id']}")
                worksheet.write(row, 1, theme.get('theme_statement', 'No statement'), self.formats['data_cell'])
                
                # Show primary quotes for this theme
                primary_quotes = self._get_primary_quotes_for_theme(theme)
                if primary_quotes:
                    quote_text = f"\"{primary_quotes[0].get('verbatim_response', '')[:80]}...\""
                    worksheet.write(row, 2, quote_text, self.formats['data_cell'])
                    worksheet.write(row, 3, f"{len(primary_quotes)} supporting quotes", self.formats['data_cell'])
                else:
                    worksheet.write(row, 2, "No primary quotes classified", self.formats['data_cell'])
                    worksheet.write(row, 3, "Review quote classifications", self.formats['data_cell'])
                
                worksheet.write(row, 4, "VALIDATED", self.formats['validated'])
                row += 1
        else:
            worksheet.write(row, 1, "No validated implementation themes. Review 'Implementation Insights' tab.", self.formats['data_cell'])
            row += 1
        
        row += 2
        
        # Decision Summary
        worksheet.write(row, 0, "📋 ANALYST DECISION SUMMARY", self.formats['header'])
        worksheet.merge_range(f'A{row}:E{row}', "Overview of analyst decisions across all sections", self.formats['data_cell'])
        row += 1
        
        decision_summary = self._generate_decision_summary(themes_data)
        for section, stats in decision_summary.items():
            worksheet.write(row, 0, f"• {section}")
            worksheet.write(row, 1, f"Validated: {stats['validated']}, Rejected: {stats['rejected']}, Revised: {stats['revised']}", self.formats['data_cell'])
            worksheet.write(row, 2, f"Featured Quotes: {stats['featured_quotes']}", self.formats['data_cell'])
            worksheet.write(row, 3, f"Primary Quotes: {stats['primary_quotes']}", self.formats['data_cell'])
            worksheet.write(row, 4, f"Coverage: {stats['coverage']}%", self.formats['data_cell'])
            row += 1
    
    def _get_featured_quotes_from_validated_themes(self, themes_data: Dict[str, Any]) -> List[Dict]:
        """Get featured quotes from validated themes for executive summary"""
        featured_quotes = []
        
        for theme in themes_data['themes']:
            # For now, we'll simulate validated themes (in real implementation, this would read analyst decisions)
            # In a real system, this would check if theme was marked as 'VALIDATED' in section tabs
            if theme.get('theme_type') in ['strength', 'opportunity']:  # Simulate validated win themes
                all_quotes = theme.get('all_quotes', [])
                for quote in all_quotes:
                    # Simulate featured quote classification (in real implementation, this would read from section tabs)
                    if quote.get('impact_score', 0) >= 4:  # High impact quotes as featured
                        quote_with_theme = quote.copy()
                        quote_with_theme['theme_statement'] = theme.get('theme_statement', 'No statement')
                        featured_quotes.append(quote_with_theme)
        
        return featured_quotes[:10]  # Return top 10 featured quotes
    
    def _get_validated_themes_by_section(self, themes_data: Dict[str, Any], section_type: str) -> List[Dict]:
        """Get validated themes for a specific report section"""
        # For now, simulate validated themes based on theme type
        # In real implementation, this would read analyst decisions from section tabs
        section_themes = self._filter_themes_by_section(themes_data['themes'], section_type)
        
        # Simulate validation - in real system, this would check analyst decisions
        validated_themes = []
        for theme in section_themes:
            # Simulate validation based on quality score
            if theme.get('validation_metrics', {}).get('quality_score', 0) >= 7.0:
                validated_themes.append(theme)
        
        return validated_themes
    
    def _get_primary_quotes_for_theme(self, theme: Dict[str, Any]) -> List[Dict]:
        """Get primary quotes for a specific theme"""
        all_quotes = theme.get('all_quotes', [])
        primary_quotes = []
        
        for quote in all_quotes:
            # Simulate primary quote classification (in real implementation, this would read from section tabs)
            if quote.get('impact_score', 0) >= 3:  # Medium-high impact quotes as primary
                primary_quotes.append(quote)
        
        return primary_quotes[:3]  # Return top 3 primary quotes
    
    def _generate_decision_summary(self, themes_data: Dict[str, Any]) -> Dict[str, Dict]:
        """Generate summary of analyst decisions across all sections"""
        sections = {
            'Win Drivers': 'win',
            'Loss Factors': 'loss', 
            'Competitive Intelligence': 'competitive',
            'Implementation Insights': 'implementation'
        }
        
        summary = {}
        for section_name, section_type in sections.items():
            themes = self._filter_themes_by_section(themes_data['themes'], section_type)
            
            # Simulate decision counts (in real implementation, this would read analyst decisions)
            validated = len([t for t in themes if t.get('validation_metrics', {}).get('quality_score', 0) >= 7.0])
            rejected = len([t for t in themes if t.get('validation_metrics', {}).get('quality_score', 0) < 5.0])
            revised = len([t for t in themes if 5.0 <= t.get('validation_metrics', {}).get('quality_score', 0) < 7.0])
            
            # Count featured and primary quotes
            featured_quotes = 0
            primary_quotes = 0
            for theme in themes:
                all_quotes = theme.get('all_quotes', [])
                for quote in all_quotes:
                    if quote.get('impact_score', 0) >= 4:
                        featured_quotes += 1
                    elif quote.get('impact_score', 0) >= 3:
                        primary_quotes += 1
            
            total_themes = len(themes)
            coverage = round((validated / total_themes * 100) if total_themes > 0 else 0, 1)
            
            summary[section_name] = {
                'validated': validated,
                'rejected': rejected,
                'revised': revised,
                'featured_quotes': featured_quotes,
                'primary_quotes': primary_quotes,
                'coverage': coverage
            }
        
        return summary
    
    def _get_quote_research_alignment(self, quote: Dict[str, Any]) -> str:
        """Get research alignment summary for a quote"""
        try:
            # Check if quote has research question alignment data
            if 'research_question_alignment' in quote and quote['research_question_alignment']:
                alignments = quote['research_question_alignment']
                
                if isinstance(alignments, str):
                    try:
                        alignments = json.loads(alignments)
                    except:
                        return "No alignment data"
                
                if alignments:
                    # Create summary of alignments
                    alignment_summaries = []
                    for alignment in alignments[:2]:  # Show first 2 alignments
                        question_text = alignment.get('question_text', '')[:30] + "..." if len(alignment.get('question_text', '')) > 30 else alignment.get('question_text', '')
                        score = alignment.get('alignment_score', 0)
                        priority = alignment.get('coverage_priority', 'medium')
                        alignment_summaries.append(f"{question_text} ({score}/5, {priority})")
                    
                    return "; ".join(alignment_summaries)
            
            return "No alignment data"
            
        except Exception as e:
            return "Error parsing alignment"
    
    def _create_research_question_alignment_tab(self, themes_data: Dict[str, Any]):
        """Create research question alignment analysis tab"""
        worksheet = self.workbook.add_worksheet('Research Question Alignment')
        
        # Set column widths
        worksheet.set_column('A:A', 15)  # Response ID
        worksheet.set_column('B:B', 50)  # Response Text
        worksheet.set_column('C:C', 20)  # Sentiment
        worksheet.set_column('D:D', 15)  # Impact Score
        worksheet.set_column('E:E', 20)  # Harmonized Subject
        worksheet.set_column('F:F', 50)  # Research Questions Addressed
        worksheet.set_column('G:G', 15)  # Questions Count
        worksheet.set_column('H:H', 30)  # Coverage Summary
        worksheet.set_column('I:I', 20)  # Company
        worksheet.set_column('J:J', 20)  # Interviewee
        
        # Title
        worksheet.merge_range('A1:J1', "Research Question Alignment Analysis", self.formats['title'])
        worksheet.merge_range('A2:J2', "How well do individual responses address research questions?", self.formats['subheader'])
        
        # Headers
        headers = [
            "Response ID", "Response Text", "Sentiment", "Impact Score", "Harmonized Subject",
            "Research Questions Addressed", "Questions Count", "Coverage Summary", "Company", "Interviewee"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, self.formats['header'])
        
        # Get responses with research question alignment
        responses = self._get_responses_with_research_alignment()
        
        # Populate data
        row = 4
        for response in responses:
            # Response ID
            worksheet.write(row, 0, response.get('response_id', ''), self.formats['data_cell'])
            
            # Response Text (truncated)
            response_text = response.get('verbatim_response', '')[:100] + "..." if len(response.get('verbatim_response', '')) > 100 else response.get('verbatim_response', '')
            worksheet.write(row, 1, response_text, self.formats['data_cell'])
            
            # Sentiment
            sentiment = response.get('sentiment', 'unknown').title()
            worksheet.write(row, 2, sentiment, self.formats['data_cell'])
            
            # Impact Score
            impact_score = response.get('impact_score', 0)
            worksheet.write(row, 3, impact_score, self.formats['number'])
            
            # Harmonized Subject
            worksheet.write(row, 4, response.get('harmonized_subject', ''), self.formats['data_cell'])
            
            # Research Questions Addressed
            alignments = response.get('research_question_alignment', [])
            if alignments:
                question_texts = []
                for alignment in alignments:
                    question_text = alignment.get('question_text', '')[:40] + "..." if len(alignment.get('question_text', '')) > 40 else alignment.get('question_text', '')
                    score = alignment.get('alignment_score', 0)
                    priority = alignment.get('coverage_priority', 'medium')
                    question_texts.append(f"{question_text} ({score}/5, {priority})")
                questions_text = "; ".join(question_texts)
            else:
                questions_text = "No alignments found"
            worksheet.write(row, 5, questions_text, self.formats['data_cell'])
            
            # Questions Count
            worksheet.write(row, 6, len(alignments), self.formats['number'])
            
            # Coverage Summary
            worksheet.write(row, 7, response.get('coverage_summary', ''), self.formats['data_cell'])
            
            # Company
            worksheet.write(row, 8, response.get('company', ''), self.formats['data_cell'])
            
            # Interviewee
            worksheet.write(row, 9, response.get('interviewee_name', ''), self.formats['data_cell'])
            
            row += 1
        
        # Add summary statistics
        row += 2
        worksheet.write(row, 0, "Alignment Summary", self.formats['header'])
        row += 1
        
        total_responses = len(responses)
        responses_with_alignments = len([r for r in responses if r.get('research_question_alignment')])
        avg_questions_addressed = sum(len(r.get('research_question_alignment', [])) for r in responses) / max(1, total_responses)
        
        worksheet.write(row, 0, "Total Responses:")
        worksheet.write(row, 1, total_responses, self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "Responses with Alignments:")
        worksheet.write(row, 1, responses_with_alignments, self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "Average Questions Addressed:")
        worksheet.write(row, 1, f"{avg_questions_addressed:.1f}", self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "Alignment Rate:")
        worksheet.write(row, 1, f"{(responses_with_alignments / max(1, total_responses)) * 100:.1f}%", self.formats['data_cell'])
    
    def _get_responses_with_research_alignment(self) -> List[Dict]:
        """Get responses that have research question alignment data"""
        try:
            # Get responses from database
            df = self.db.get_stage1_data_responses(client_id=self.client_id)
            
            if df.empty:
                return []
            
            # Filter for responses with research question alignment
            responses_with_alignment = []
            
            for _, row in df.iterrows():
                response_data = row.to_dict()
                
                # Check if response has research question alignment
                if 'research_question_alignment' in response_data and response_data['research_question_alignment']:
                    try:
                        # Parse JSON alignment data
                        if isinstance(response_data['research_question_alignment'], str):
                            alignments = json.loads(response_data['research_question_alignment'])
                        else:
                            alignments = response_data['research_question_alignment']
                        
                        response_data['research_question_alignment'] = alignments
                        responses_with_alignment.append(response_data)
                    except:
                        # Skip if JSON parsing fails
                        continue
            
            return responses_with_alignment
            
        except Exception as e:
            logger.error(f"❌ Failed to get responses with research alignment: {e}")
            return []
    
    def _create_research_question_coverage_tab(self, themes_data: Dict[str, Any]):
        """Create research question coverage analysis tab"""
        worksheet = self.workbook.add_worksheet('Research Question Coverage')
        
        # Set column widths
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 60)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 15)
        
        # Title
        worksheet.merge_range('A1:D1', "Research Question Coverage Analysis", self.formats['title'])
        worksheet.merge_range('A2:D2', "How well do discovered themes address original research questions?", self.formats['subheader'])
        
        # Get research questions
        research_questions = self.discussion_guide
        
        # Analyze coverage
        coverage_analysis = self._analyze_theme_question_coverage(themes_data['themes'], research_questions)
        
        # Coverage Summary
        row = 4
        worksheet.write(row, 0, "Coverage Summary", self.formats['header'])
        row += 1
        worksheet.write(row, 0, "Total Research Questions:")
        worksheet.write(row, 1, len(research_questions), self.formats['data_cell'])
        row += 1
        worksheet.write(row, 0, "Questions with Theme Coverage:")
        worksheet.write(row, 1, coverage_analysis['questions_with_coverage'], self.formats['data_cell'])
        row += 1
        worksheet.write(row, 0, "Coverage Percentage:")
        worksheet.write(row, 1, f"{coverage_analysis['coverage_percentage']:.1f}%", self.formats['data_cell'])
        
        # Question Coverage Details
        row += 2
        worksheet.write(row, 0, "Research Question", self.formats['header'])
        worksheet.write(row, 1, "Covering Themes", self.formats['header'])
        worksheet.write(row, 2, "Evidence Strength", self.formats['header'])
        worksheet.write(row, 3, "Coverage Status", self.formats['header'])
        row += 1
        
        for question, coverage in coverage_analysis['question_coverage'].items():
            # Research Question
            worksheet.write(row, 0, question, self.formats['data_cell'])
            
            # Covering Themes
            if coverage['themes']:
                theme_list = ", ".join([f"T{theme['theme_id']}" for theme in coverage['themes']])
                worksheet.write(row, 1, theme_list, self.formats['data_cell'])
            else:
                worksheet.write(row, 1, "No themes found", self.formats['data_cell'])
            
            # Evidence Strength
            if coverage['themes']:
                avg_evidence = sum(theme.get('validation_metrics', {}).get('quality_score', 0) for theme in coverage['themes']) / len(coverage['themes'])
                worksheet.write(row, 2, f"{avg_evidence:.1f}/5.0", self.formats['data_cell'])
            else:
                worksheet.write(row, 2, "N/A", self.formats['data_cell'])
            
            # Coverage Status
            if coverage['themes']:
                worksheet.write(row, 3, "✅ COVERED", self.formats['validated'])
            else:
                worksheet.write(row, 3, "❌ UNCOVERED", self.formats['data_cell'])
            
            row += 1
        
        # Coverage Gaps
        if coverage_analysis['uncovered_questions']:
            row += 2
            worksheet.write(row, 0, "Coverage Gaps - Research Questions Without Themes", self.formats['header'])
            row += 1
            
            for question in coverage_analysis['uncovered_questions']:
                worksheet.write(row, 0, f"• {question}", self.formats['data_cell'])
                row += 1
        
        # Analyst Recommendations
        row += 2
        worksheet.write(row, 0, "Analyst Recommendations", self.formats['header'])
        row += 1
        
        recommendations = [
            "1. Review uncovered questions - consider additional data collection",
            "2. Validate theme accuracy for covered questions",
            "3. Assess evidence strength for each research question",
            "4. Consider combining themes to improve coverage",
            "5. Prioritize high-impact research questions for additional analysis"
        ]
        
        for rec in recommendations:
            worksheet.write(row, 0, rec, self.formats['data_cell'])
            row += 1
    
    def _analyze_theme_question_coverage(self, themes: List[Dict], research_questions: List[str]) -> Dict[str, Any]:
        """Analyze how well themes cover research questions"""
        
        coverage_analysis = {
            'question_coverage': {},
            'uncovered_questions': [],
            'questions_with_coverage': 0,
            'coverage_percentage': 0
        }
        
        # Initialize question coverage
        for question in research_questions:
            coverage_analysis['question_coverage'][question] = {
                'themes': [],
                'evidence_strength': 0,
                'coverage_score': 0
            }
        
        # Analyze each theme against research questions
        for theme in themes:
            theme_text = f"{theme.get('theme_statement', '')} {theme.get('harmonized_subject', '')}".lower()
            
            # Check alignment with each research question
            for question in research_questions:
                question_lower = question.lower()
                
                # Simple keyword matching (could be enhanced with LLM)
                keywords = self._extract_question_keywords(question_lower)
                matches = []
                
                for keyword in keywords:
                    if keyword in theme_text:
                        matches.append(keyword)
                
                if matches:
                    alignment_score = len(matches) / len(keywords)
                    if alignment_score > 0.3:  # 30% keyword match threshold
                        coverage_analysis['question_coverage'][question]['themes'].append(theme)
                        coverage_analysis['question_coverage'][question]['coverage_score'] = max(
                            coverage_analysis['question_coverage'][question]['coverage_score'],
                            alignment_score
                        )
        
        # Calculate coverage statistics
        for question, coverage in coverage_analysis['question_coverage'].items():
            if coverage['themes']:
                coverage_analysis['questions_with_coverage'] += 1
            else:
                coverage_analysis['uncovered_questions'].append(question)
        
        coverage_analysis['coverage_percentage'] = (
            coverage_analysis['questions_with_coverage'] / len(research_questions)
        ) * 100
        
        return coverage_analysis
    
    def _extract_question_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from research question"""
        # Remove common words and extract keywords
        stop_words = {'what', 'how', 'why', 'when', 'where', 'who', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
        
        words = text.split()
        keywords = [word.lower() for word in words if word.lower() not in stop_words and len(word) > 3]
        return list(set(keywords))  # Remove duplicates
    
    def _create_discussion_guide_coverage_tab(self, themes_data: Dict[str, Any]):
        """Create discussion guide coverage analysis tab"""
        worksheet = self.workbook.add_worksheet('Discussion Guide Coverage')
        
        # Set column widths
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 60)
        worksheet.set_column('C:C', 20)
        
        # Title
        worksheet.merge_range('A1:C1', "Discussion Guide Coverage Analysis", self.formats['title'])
        worksheet.merge_range('A2:C2', "Analysis of how well themes address original research questions", self.formats['subheader'])
        
        # Import discussion guide integrator
        from discussion_guide_integration import DiscussionGuideIntegrator
        integrator = DiscussionGuideIntegrator()
        
        # Get Supio discussion guide
        if not hasattr(self, 'discussion_guide'):
            from discussion_guide_integration import DiscussionGuideIntegrator
            integrator = DiscussionGuideIntegrator()
            self.discussion_guide = integrator.parse_supio_discussion_guide('uploads/Supio_PRJ-00027 Discussion Guide v1.txt')
        
        discussion_guide = self.discussion_guide
        
        # Analyze coverage
        coverage_analysis = integrator.analyze_coverage(
            self.discussion_guide,
            themes_data['themes']
        )
        
        # Map questions to themes
        question_mappings = integrator.map_questions_to_themes(self.discussion_guide, themes_data['themes'])
        
        # Coverage Summary
        row = 4
        worksheet.write(row, 0, "Coverage Summary", self.formats['header'])
        row += 1
        worksheet.write(row, 0, "Total Questions:")
        worksheet.write(row, 1, coverage_analysis['total_questions'], self.formats['data_cell'])
        row += 1
        worksheet.write(row, 0, "Covered Questions:")
        worksheet.write(row, 1, coverage_analysis['covered_questions'], self.formats['data_cell'])
        row += 1
        worksheet.write(row, 0, "Coverage Percentage:")
        worksheet.write(row, 1, f"{coverage_analysis['coverage_percentage']:.1f}%", self.formats['data_cell'])
        
        # Question Coverage Details
        row += 2
        worksheet.write(row, 0, "Question Coverage Details", self.formats['header'])
        row += 1
        
        for coverage_item in coverage_analysis['coverage_data']:
            question = coverage_item['question']
            theme_count = coverage_item['theme_count']
            status = coverage_item['coverage_status']
            
            if status == 'Covered':
                worksheet.write(row, 0, f"✅ {question}", self.formats['data_cell'])
                worksheet.write(row, 1, f"Addressed by {theme_count} themes", self.formats['data_cell'])
            else:
                worksheet.write(row, 0, f"❌ {question}", self.formats['high_priority'])
                worksheet.write(row, 1, "No themes address this question", self.formats['high_priority'])
            row += 1
        
        # Theme-Question Mapping
        row += 2
        worksheet.write(row, 0, "Theme-Question Mapping", self.formats['header'])
        row += 1
        
        for theme_id, questions in question_mappings.items():
            if questions:
                worksheet.write(row, 0, f"✅ {theme_id}", self.formats['validated'])
                worksheet.write(row, 1, f"Addresses {len(questions)} questions", self.formats['data_cell'])
                row += 1
    
    def _summarize_themes_by_type(self, themes: List[Dict]) -> Dict[str, Dict]:
        """Summarize themes by type for executive overview"""
        summaries = defaultdict(lambda: {
            'count': 0, 
            'total_quotes': 0, 
            'quality_scores': [], 
            'avg_quality_score': 0,
            'key_insight': ''
        })
        
        for theme in themes:
            theme_type = theme.get('theme_type', 'unknown')
            if theme_type not in summaries:
                summaries[theme_type] = {
                    'count': 0,
                    'total_quotes': 0,
                    'avg_quality': 0.0,
                    'companies': set()
                }
            
            summaries[theme_type]['count'] += 1
            summaries[theme_type]['total_quotes'] += theme['validation_metrics'].get('quotes_count', 0)
            summaries[theme_type]['avg_quality'] += theme['validation_metrics'].get('confidence_score', 0.0)
            
            # Add companies
            company_distribution = theme.get('company_distribution', {})
            if 'companies' in company_distribution:
                for company in company_distribution['companies']:
                    summaries[theme_type]['companies'].add(company)
        
        # Calculate averages and insights
        for theme_type, summary in summaries.items():
            if summary['count'] > 0:
                summary['avg_quality_score'] = summary['avg_quality'] / summary['count']
            
            # Generate key insight
            if theme_type == 'strength':
                summary['key_insight'] = f"Identified {summary['count']} competitive advantages"
            elif theme_type == 'weakness':
                summary['key_insight'] = f"Found {summary['count']} areas requiring immediate attention"
            elif theme_type == 'investigation_needed':
                summary['key_insight'] = f"Discovered {summary['count']} complex patterns needing investigation"
            else:
                summary['key_insight'] = f"Identified {summary['count']} {theme_type} themes"
        
        return dict(summaries)
    
    def _extract_competitive_insight(self, quote_text: str) -> str:
        """Extract competitive insight from quote text"""
        text_lower = quote_text.lower()
        
        if 'competitor' in text_lower:
            return "Direct competitive comparison mentioned"
        elif 'alternative' in text_lower:
            return "Alternative solution discussed"  
        elif 'versus' in text_lower or 'vs' in text_lower:
            return "Head-to-head comparison"
        elif 'switch' in text_lower:
            return "Switching consideration mentioned"
        else:
            return "Market positioning insight"
    
    def _create_evidence_preview(self, theme: Dict[str, Any]) -> str:
        """Create evidence preview for theme curation tab"""
        supporting_quotes = theme.get('supporting_quotes', [])
        if not supporting_quotes:
            return "No supporting quotes available"
        
        # Show top 2 quotes with company attribution
        preview_parts = []
        for i, quote in enumerate(supporting_quotes[:2], 1):
            quote_text = quote['quote_text']
            # Truncate long quotes
            if len(quote_text) > 100:
                quote_text = quote_text[:100] + "..."
            
            company = quote.get('company', 'Unknown')
            preview_parts.append(f"{i}. \"{quote_text}\" - {company}")
        
        return "\n\n".join(preview_parts)
    
    def _assign_quality_flags(self, theme: Dict[str, Any]) -> List[str]:
        """Assign quality flags based on theme characteristics"""
        flags = []
        
        metrics = theme.get('validation_metrics', {})
        quality_score = metrics.get('quality_score', 0)
        company_dist = metrics.get('company_distribution', {})
        
        # Quality confidence flags
        if quality_score >= 8.0:
            flags.append("HIGH_CONFIDENCE")
        elif quality_score >= 6.0:
            flags.append("MEDIUM_CONFIDENCE")
        else:
            flags.append("REVIEW_REQUIRED")
        
        # Company distribution flags
        if company_dist.get('total_companies', 0) == 1:
            flags.append("SINGLE_COMPANY")
        elif company_dist.get('bias_warning', False):
            flags.append("COMPANY_BIAS")
        elif company_dist.get('company_balance_score', 0) < 0.3:
            flags.append("UNBALANCED")
        
        # Competitive intelligence flag
        if theme.get('competitive_flag', False):
            flags.append("COMPETITIVE")
        
        return flags
    
    def _determine_win_loss_category(self, theme: Dict[str, Any]) -> str:
        """Determine win-loss category based on theme type and characteristics"""
        theme_type = theme.get('theme_type', '').lower()
        competitive_flag = theme.get('competitive_flag', False)
        harmonized_subject = theme.get('harmonized_subject', '').lower()
        
        # Map theme types to win-loss categories
        if theme_type == 'strength':
            if competitive_flag or 'competitive' in harmonized_subject:
                return 'Competitive'
            else:
                return 'Strength'
        elif theme_type == 'weakness':
            return 'Weakness'
        elif theme_type in ['opportunity', 'investigation_needed']:
            if 'sales' in harmonized_subject or 'implementation' in harmonized_subject:
                return 'Process'
            elif competitive_flag or 'competitive' in harmonized_subject:
                return 'Competitive'
            else:
                return 'Opportunity'
        else:
            # Default categorization for mixed/other themes
            if competitive_flag or 'competitive' in harmonized_subject:
                return 'Competitive'
            elif 'sales' in harmonized_subject or 'implementation' in harmonized_subject:
                return 'Process'
            else:
                return 'Opportunity'
    
    def _determine_report_section(self, win_loss_category: str) -> str:
        """Map win-loss category to report section"""
        section_mapping = {
            'Strength': 'Section 2: Why You Win',
            'Weakness': 'Section 3: Why You Lose', 
            'Opportunity': 'Section 4: Market Opportunities',
            'Competitive': 'Section 5: Competitive Intelligence',
            'Process': 'Section 6: Implementation Insights'
        }
        return section_mapping.get(win_loss_category, 'Section 4: Market Opportunities')
    
    def _get_research_questions_for_section(self, section_name: str) -> List[str]:
        """Get research questions from the actual discussion guide file"""
        try:
            # Path to the discussion guide
            discussion_guide_path = 'uploads/Supio_PRJ-00027 Discussion Guide v1.txt'
            
            with open(discussion_guide_path, 'r') as f:
                content = f.read()
            
            # Parse the discussion guide to extract questions by section
            questions = self._parse_discussion_guide_for_section(content, section_name)
            
            return questions
            
        except FileNotFoundError:
            print(f"Warning: Discussion guide not found at {discussion_guide_path}")
            # Return empty or default questions as fallback
            return []
        except Exception as e:
            print(f"Error reading discussion guide: {e}")
            return []
    
    def _parse_discussion_guide_for_section(self, content: str, section_name: str) -> List[str]:
        """Parse discussion guide content to extract questions for a specific section"""
        
        questions = []
        lines = content.split('\n')
        in_section = False
        
        # Map section names to discussion guide sections
        section_markers = {
            'Win Drivers': ['Win/Loss Outcome', 'WIN:', 'Why did you ultimately choose Supio'],
            'Loss Factors': ['Win/Loss Outcome', 'LOSS:', 'Why did you ultimately choose'],
            'Competitive Intelligence': ['Supio Perceptions vs Competitors', 'Competitors'],
            'Implementation Insights': ['Implementation Experience', 'Implementation']
        }
        
        target_markers = section_markers.get(section_name, [])
        
        for line in lines:
            line = line.strip()
            
            # Check if we're entering the target section
            for marker in target_markers:
                if marker in line:
                    in_section = True
                    break
            
            # Check if we're leaving the section (entering a new numbered section)
            if in_section and line.startswith(('8.', '9.', '10.', '11.', '12.', '13.', '14.', '15.', '16.')):
                # We've moved to a new section
                break
            
            # Extract questions from the current section
            if in_section and line:
                # Look for question patterns
                if '?' in line and not line.startswith('*') and not line.startswith('CONTEXT:'):
                    # Clean up the question
                    question = line.strip()
                    if question and len(question) > 10:  # Avoid very short lines
                        questions.append(question)
        
        return questions
    
    def _count_evidence_for_research_question(self, question: str) -> int:
        """Count how many responses provide evidence for a specific research question"""
        try:
            df = self.db.get_stage1_data_responses(client_id=self.client_id)
            if df.empty:
                return 0
            
            # Count responses that have research alignment data for this question
            count = 0
            for _, row in df.iterrows():
                if pd.notna(row.get('research_question_alignment')):
                    try:
                        alignments = json.loads(row['research_question_alignment']) if isinstance(row['research_question_alignment'], str) else row['research_question_alignment']
                        for alignment in alignments:
                            if question.lower() in alignment.get('question_text', '').lower():
                                count += 1
                                break
                    except:
                        continue
            
            return count
        except Exception as e:
            logger.error(f"Error counting evidence for question: {e}")
            return 0
    
    def _get_discovered_themes_for_section(self, section_name: str) -> List[Dict]:
        """Get discovered themes for a specific report section"""
        # For now, return sample themes - this would be populated from actual theme analysis
        sample_themes = {
            'Win Drivers': [
                {
                    'theme_id': 'WD001',
                    'theme_statement': 'Product features and capabilities drive vendor selection',
                    'validation_metrics': {'confidence_score': 0.85, 'quotes_count': 15},
                    'research_alignment': 'Strong alignment with product evaluation criteria'
                },
                {
                    'theme_id': 'WD002', 
                    'theme_statement': 'Customer service and support quality',
                    'validation_metrics': {'confidence_score': 0.78, 'quotes_count': 8},
                    'research_alignment': 'Addresses implementation and support concerns'
                }
            ],
            'Loss Factors': [
                {
                    'theme_id': 'LF001',
                    'theme_statement': 'Pricing concerns and budget constraints',
                    'validation_metrics': {'confidence_score': 0.72, 'quotes_count': 12},
                    'research_alignment': 'Directly addresses pricing comparison questions'
                }
            ],
            'Competitive Intelligence': [
                {
                    'theme_id': 'CI001',
                    'theme_statement': 'Competitive positioning and differentiation',
                    'validation_metrics': {'confidence_score': 0.81, 'quotes_count': 10},
                    'research_alignment': 'Covers competitive evaluation and vendor comparison'
                }
            ],
            'Implementation Insights': [
                {
                    'theme_id': 'II001',
                    'theme_statement': 'Implementation process and timeline',
                    'validation_metrics': {'confidence_score': 0.75, 'quotes_count': 6},
                    'research_alignment': 'Addresses implementation experience questions'
                }
            ]
        }
        
        return sample_themes.get(section_name, [])
    
    def _get_theme_research_alignment(self, theme: Dict) -> str:
        """Get research alignment summary for a theme"""
        alignment = theme.get('research_alignment', 'No alignment data')
        return alignment[:50] + "..." if len(alignment) > 50 else alignment
    
    def _get_quotes_for_section(self, section_name: str) -> List[Dict]:
        """Get quotes relevant to a specific report section"""
        try:
            df = self.db.get_stage1_data_responses(client_id=self.client_id)
            if df.empty:
                return []
            
            # Filter quotes based on section relevance
            section_keywords = {
                'Win Drivers': ['strength', 'positive', 'good', 'great', 'excellent', 'value', 'feature', 'capability'],
                'Loss Factors': ['weakness', 'negative', 'bad', 'poor', 'issue', 'problem', 'concern', 'disappointing'],
                'Competitive Intelligence': ['competitor', 'compare', 'versus', 'alternative', 'other', 'different'],
                'Implementation Insights': ['implementation', 'setup', 'process', 'timeline', 'experience', 'support']
            }
            
            keywords = section_keywords.get(section_name, [])
            relevant_quotes = []
            
            for _, row in df.iterrows():
                quote_text = row.get('verbatim_response', '').lower()
                if any(keyword in quote_text for keyword in keywords):
                    relevant_quotes.append(row.to_dict())
            
            return relevant_quotes[:20]  # Limit to 20 most relevant quotes
            
        except Exception as e:
            logger.error(f"Error getting quotes for section: {e}")
            return []

    def _identify_cross_section_themes(self, themes: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Identify themes that appear in multiple sections and map their locations"""
        theme_sections = {}
        
        # Check each theme against all section types
        for theme in themes:
            theme_id = theme.get('theme_id', 'unknown')
            theme_sections[theme_id] = []
            
            # Test against each section type
            for section_type in ['win', 'loss', 'competitive', 'implementation']:
                filtered = self._filter_themes_by_section([theme], section_type)
                if filtered:
                    theme_sections[theme_id].append(section_type)
        
        # Return only themes that appear in multiple sections
        cross_section_themes = {
            theme_id: sections 
            for theme_id, sections in theme_sections.items() 
            if len(sections) > 1
        }
        
        return cross_section_themes
    
    def _get_primary_section_for_theme(self, theme: Dict[str, Any], cross_section_map: Dict[str, List[str]]) -> str:
        """Determine the primary section for a theme to avoid duplication"""
        theme_id = theme.get('theme_id', 'unknown')
        
        if theme_id not in cross_section_map:
            # Single-section theme - use its natural section
            return self._determine_primary_section(theme)
        
        # Cross-section theme - determine primary based on priority
        sections = cross_section_map[theme_id]
        
        # Priority order: win > loss > competitive > implementation
        priority_order = ['win', 'loss', 'competitive', 'implementation']
        
        for section in priority_order:
            if section in sections:
                return section
        
        return sections[0]  # Fallback
    
    def _determine_primary_section(self, theme: Dict[str, Any]) -> str:
        """Determine the primary section for a single-section theme"""
        theme_type = theme.get('theme_type', '').lower()
        subject = theme.get('harmonized_subject', '').lower()
        
        if theme_type == 'strength':
            return 'win'
        elif theme_type == 'weakness':
            return 'loss'
        elif 'competitive' in subject or 'market' in subject:
            return 'competitive'
        elif 'implementation' in subject or 'integration' in subject:
            return 'implementation'
        else:
            # Default based on theme type
            return 'win' if theme_type == 'strength' else 'loss'
    
    def _create_cross_section_reference_tab(self, themes_data: Dict[str, Any]):
        """Create a reference tab showing cross-section themes and their locations"""
        worksheet = self.workbook.add_worksheet('🔄 Cross-Section Themes')
        
        # Set column widths
        worksheet.set_column('A:A', 15)  # Theme ID
        worksheet.set_column('B:B', 50)  # Theme Statement
        worksheet.set_column('C:C', 20)  # Primary Section
        worksheet.set_column('D:D', 30)  # All Sections
        worksheet.set_column('E:E', 40)  # Cross-Reference Notes
        worksheet.set_column('F:F', 25)  # Processing Status
        
        # Title and instructions
        worksheet.merge_range('A1:F1', "🔄 Cross-Section Themes Reference", self.formats['title'])
        worksheet.merge_range('A2:F2', "IMPORTANT: These themes appear in multiple sections. Process them ONCE in their primary section, then reference here.", self.formats['subheader'])
        
        # Instructions
        worksheet.merge_range('A3:F3', "📋 WORKFLOW: 1) Process theme in Primary Section 2) Mark as 'Processed' here 3) Reference in other sections without re-processing", self.formats['data_cell'])
        
        # Headers
        headers = [
            "Theme ID", "Theme Statement", "Primary Section", "All Sections", 
            "Cross-Reference Notes", "Processing Status"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(4, col, header, self.formats['header'])
        
        # Get cross-section themes
        cross_section_map = self._identify_cross_section_themes(themes_data['themes'])
        
        row = 5
        for theme in themes_data['themes']:
            theme_id = theme.get('theme_id', 'unknown')
            
            if theme_id in cross_section_map:
                sections = cross_section_map[theme_id]
                primary_section = self._get_primary_section_for_theme(theme, cross_section_map)
                
                # Theme ID
                worksheet.write(row, 0, theme_id, self.formats['data_cell'])
                
                # Theme Statement
                worksheet.write(row, 1, theme.get('theme_statement', 'No statement'), self.formats['data_cell'])
                
                # Primary Section
                worksheet.write(row, 2, primary_section.title(), self.formats['data_cell'])
                
                # All Sections
                all_sections = ', '.join([s.title() for s in sections])
                worksheet.write(row, 3, all_sections, self.formats['data_cell'])
                
                # Cross-Reference Notes
                worksheet.write(row, 4, f"Process in {primary_section.title()} section, then reference in: {', '.join([s.title() for s in sections if s != primary_section])}", self.formats['data_cell'])
                
                # Processing Status dropdown
                worksheet.data_validation(row, 5, row, 5, {
                    'validate': 'list',
                    'source': ['PENDING - Not yet processed', 'PROCESSED - Complete in primary section', 'REFERENCED - Added to other sections']
                })
                worksheet.write(row, 5, "PENDING - Not yet processed", self.formats['decision_cell'])
                
                row += 1
        
        # Add summary
        if cross_section_map:
            worksheet.write(row, 0, f"SUMMARY: {len(cross_section_map)} cross-section themes identified", self.formats['header'])
            worksheet.write(row, 1, "Efficiency gain: Process once, reference multiple times", self.formats['data_cell'])
        else:
            worksheet.write(row, 0, "No cross-section themes found", self.formats['data_cell'])

# Test function
def test_excel_export():
    """Test the Excel exporter with sample data"""
    from win_loss_report_generator import WinLossReportGenerator
    
    # Generate sample report data
    generator = WinLossReportGenerator(client_id="Supio")
    themes_data = generator.generate_analyst_report()
    
    if themes_data["success"]:
        # Export to Excel
        exporter = ExcelWinLossExporter()
        output_file = exporter.export_analyst_workbook(themes_data)
        print(f"✅ Excel workbook created: {output_file}")
        return output_file
    else:
        print(f"❌ Error generating themes: {themes_data['error']}")
        return None

if __name__ == "__main__":
    test_excel_export() 